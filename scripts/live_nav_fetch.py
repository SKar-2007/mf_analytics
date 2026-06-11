"""
Bluestock MF Capstone — Live NAV Fetcher

Fetches live NAV data from https://api.mfapi.in/mf/{amfi_code}
with:
  - Retry with exponential backoff
  - Rate limiting (configurable)
  - Response caching (in-memory + file)
  - Graceful degradation (partial success tolerated)
  - Combined output file
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import config
from utils.logging_setup import setup_logger
from utils.retry import rate_limiter, retry

logger = setup_logger("live_nav")


class LiveNAVFetcher:
    def __init__(self) -> None:
        self.base_url = config.resolve("live_nav", "base_url", "") or "https://api.mfapi.in/mf/{code}"
        self.timeout = config.resolve("live_nav", "timeout_seconds") or 15
        self.max_retries = config.resolve("live_nav", "max_retries") or 3
        self.retry_delay = config.resolve("live_nav", "retry_delay_seconds") or 2
        self.schemes: Dict[str, int] = config.schemes()
        self.raw_dir = config.raw_dir
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[int, Tuple[str, pd.DataFrame]] = {}

    @retry(max_attempts=3, delay=2.0, backoff=2.0)
    @rate_limiter(max_per_second=2.0)
    def _fetch_scheme(self, code: int) -> Optional[Dict]:
        url = self.base_url.format(code=code)
        logger.debug("Fetching %s", url)
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def fetch_one(self, name: str, code: int) -> Optional[pd.DataFrame]:
        """Fetch a single scheme's NAV history."""
        try:
            data = self._fetch_scheme(code)
            if not data or "data" not in data:
                logger.warning("%s (code %d): empty response", name, code)
                return None

            df = pd.DataFrame(data["data"])
            df["amfi_code"] = code
            df["scheme_name"] = data.get("meta", {}).get("scheme_name", name)
            df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
            df = df.dropna(subset=["date"])
            df = df[::-1].reset_index(drop=True)

            filepath = self.raw_dir / f"live_nav_{name}.csv"
            df.to_csv(filepath, index=False)
            logger.info("Saved %s (code %d): %d rows", name, code, len(df))
            return df

        except requests.exceptions.Timeout:
            logger.error("%s (code %d): timeout after %ds", name, code, self.timeout)
        except requests.exceptions.HTTPError as e:
            logger.error("%s (code %d): HTTP %s", name, code, e)
        except requests.exceptions.ConnectionError:
            logger.error("%s (code %d): connection failed", name, code)
        except Exception as e:
            logger.error("%s (code %d): %s", name, code, e)

        return None

    def fetch_all(self) -> pd.DataFrame:
        """Fetch all configured schemes. Partial success is tolerated."""
        all_dfs: List[pd.DataFrame] = []
        failures: List[str] = []
        total = len(self.schemes)

        logger.info("Fetching live NAV for %d schemes...", total)
        for i, (name, code) in enumerate(self.schemes.items(), 1):
            logger.info("[%d/%d] %s (code: %d)...", i, total, name, code)
            df = self.fetch_one(name, code)
            if df is not None:
                all_dfs.append(df)
            else:
                failures.append(name)
            time.sleep(0.5)

        if failures:
            logger.warning("Failed to fetch %d/%d schemes: %s", len(failures), total, failures)

        if all_dfs:
            combined = pd.concat(all_dfs, ignore_index=True)
            combined_path = self.raw_dir / "live_nav_combined.csv"
            combined.to_csv(combined_path, index=False)
            logger.info("Combined: %d rows saved to %s", len(combined), combined_path)
            return combined

        logger.error("No live NAV data fetched at all")
        return pd.DataFrame()

    def verify_fetched(self) -> Dict[str, int]:
        """Check what files exist and their row counts."""
        results = {}
        for name in self.schemes:
            path = self.raw_dir / f"live_nav_{name}.csv"
            if path.exists():
                try:
                    df = pd.read_csv(path)
                    results[name] = len(df)
                except Exception:
                    results[name] = -1
            else:
                results[name] = 0
        return results


def main() -> None:
    fetcher = LiveNAVFetcher()

    import argparse
    parser = argparse.ArgumentParser(description="Fetch live NAV data from MFAPI")
    parser.add_argument("--scheme", "-s", type=str, help="Fetch a specific scheme only")
    parser.add_argument("--verify", action="store_true", help="Verify existing files")
    parser.add_argument("--output", "-o", type=str, help="Custom output combined path")
    args = parser.parse_args()

    if args.verify:
        results = fetcher.verify_fetched()
        print("\n=== Fetched Files ===")
        for name, count in results.items():
            status = f"{count} rows" if count > 0 else "MISSING" if count == 0 else "CORRUPT"
            print(f"  {name:20s}: {status}")
        return

    if args.scheme:
        name = args.scheme
        code = fetcher.schemes.get(name)
        if code is None:
            valid = ", ".join(fetcher.schemes.keys())
            logger.error("Unknown scheme '%s'. Valid: %s", name, valid)
            sys.exit(1)
        fetcher.fetch_one(name, code)
    else:
        fetcher.fetch_all()


if __name__ == "__main__":
    main()
