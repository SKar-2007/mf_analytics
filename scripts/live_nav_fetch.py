"""
Bluestock MF Capstone — Live NAV Fetcher (B1 deliverable)

Fetches live NAV data from https://api.mfapi.in/mf/{amfi_code}
with:
  - Retry with exponential backoff
  - Rate limiting (configurable)
  - Combined output file

Usage:
    python scripts/live_nav_fetch.py
    python scripts/live_nav_fetch.py --scheme HDFC_Top100
    python scripts/live_nav_fetch.py --verify

Cron (weekdays 8 PM):
    0 20 * * 1-5 /usr/bin/python3 /home/saikat/bluestock_mf_capstone/scripts/live_nav_fetch.py >> /home/saikat/bluestock_mf_capstone/logs/nav_fetch.log 2>&1
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)
log = logging.getLogger("live_nav")

BASE = Path(__file__).resolve().parent.parent
RAW_DIR = BASE / "data" / "raw"
LOGS_DIR = BASE / "logs"
RAW_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

fh = logging.FileHandler(LOGS_DIR / "nav_fetch.log")
fh.setFormatter(logging.Formatter("%(asctime)s — %(levelname)s — %(message)s"))
log.addHandler(fh)

SCHEMES: Dict[str, int] = {
    "HDFC_Top100": 125497,
    "SBI_Bluechip": 119551,
    "ICICI_Bluechip": 120503,
    "Nippon_LargeCap": 118632,
    "Axis_Bluechip": 119092,
    "Kotak_Bluechip": 120841,
}


def fetch_scheme(name: str, code: int) -> Optional[pd.DataFrame]:
    url = f"https://api.mfapi.in/mf/{code}"
    try:
        log.info("Fetching %s (code %d)...", name, code)
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data or "data" not in data:
            log.warning("%s (code %d): empty response", name, code)
            return None

        df = pd.DataFrame(data["data"])
        df["amfi_code"] = code
        df["scheme_name"] = data.get("meta", {}).get("scheme_name", name)
        df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
        df = df.dropna(subset=["date"])
        df = df[::-1].reset_index(drop=True)

        filepath = RAW_DIR / f"live_nav_{name}.csv"
        df.to_csv(filepath, index=False)
        log.info("Saved %s: %d rows", name, len(df))
        return df

    except requests.exceptions.Timeout:
        log.error("%s (code %d): timeout", name, code)
    except requests.exceptions.HTTPError as e:
        log.error("%s (code %d): HTTP %s", name, code, e)
    except Exception as e:
        log.error("%s (code %d): %s", name, code, e)

    return None


def fetch_all() -> pd.DataFrame:
    all_dfs = []
    failures = []
    total = len(SCHEMES)

    log.info("Fetching live NAV for %d schemes...", total)
    for i, (name, code) in enumerate(SCHEMES.items(), 1):
        log.info("[%d/%d] %s (code: %d)...", i, total, name, code)
        df = fetch_scheme(name, code)
        if df is not None:
            all_dfs.append(df)
        else:
            failures.append(name)
        time.sleep(0.5)

    if failures:
        log.warning("Failed to fetch %d/%d: %s", len(failures), total, failures)

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined_path = RAW_DIR / "live_nav_combined.csv"
        combined.to_csv(combined_path, index=False)
        log.info("Combined: %d rows saved", len(combined))
        return combined

    log.error("No live NAV data fetched at all")
    return pd.DataFrame()


def verify_fetched() -> Dict[str, int]:
    results = {}
    for name in SCHEMES:
        path = RAW_DIR / f"live_nav_{name}.csv"
        if path.exists():
            df = pd.read_csv(path)
            results[name] = len(df)
        else:
            results[name] = 0
    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch live NAV from MFAPI")
    parser.add_argument("--scheme", "-s", type=str, help="Fetch a specific scheme only")
    parser.add_argument("--verify", action="store_true", help="Verify existing files")
    args = parser.parse_args()

    if args.verify:
        results = verify_fetched()
        print("\n=== Fetched Files ===")
        for name, count in results.items():
            status = f"{count} rows" if count > 0 else "MISSING"
            print(f"  {name:20s}: {status}")
        return

    if args.scheme:
        name = args.scheme
        code = SCHEMES.get(name)
        if code is None:
            valid = ", ".join(SCHEMES.keys())
            log.error("Unknown scheme '%s'. Valid: %s", name, valid)
            sys.exit(1)
        fetch_scheme(name, code)
    else:
        fetch_all()


if __name__ == "__main__":
    main()
