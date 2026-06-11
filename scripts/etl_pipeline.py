"""
Bluestock MF Capstone — ETL Pipeline (D1 deliverable)

Run this script to execute the full ETL pipeline end-to-end:
    python scripts/etl_pipeline.py

Steps:
    1. Data ingestion  — load raw CSVs, print shape/dtypes/head
    2. Live NAV fetch  — pull from mfapi.in and save to data/raw/
    3. Data cleaning   — parse dates, ffill, validate, standardise
    4. SQLite DB load  — load all tables into data/db/bluestock_mf.db
    5. Metrics export  — CAGR, Sharpe, Beta, VaR -> CSVs

Outputs:
    data/processed/     10 cleaned CSVs
    data/db/bluestock_mf.db
    fund_scorecard.csv, alpha_beta.csv, var_cvar_report.csv

Usage:
    python scripts/etl_pipeline.py [--skip-fetch] [--skip-db]
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent
SCRIPTS = BASE

STEPS = [
    ("Data Ingestion",        "data_ingestion.py"),
    ("Data Cleaning",         "data_cleaning.py"),
    ("Database Load",         "load_database.py"),
    ("Compute Metrics",       "compute_metrics.py"),
    ("Recommender Check",     "recommender.py"),
]


def main():
    parser = argparse.ArgumentParser(description="Bluestock MF ETL Pipeline")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip live NAV fetch")
    args = parser.parse_args()

    steps = list(STEPS)
    if not args.skip_fetch:
        steps.insert(1, ("Live NAV Fetch", "live_nav_fetch.py"))

    for label, script in steps:
        script_path = SCRIPTS / script
        if not script_path.exists():
            log.warning("Script not found (skipping): %s", script_path)
            continue
        log.info("Running: %s", label)
        result = subprocess.run([sys.executable, str(script_path)], check=False)
        if result.returncode == 0:
            log.info("✓ %s complete", label)
        else:
            log.error("✗ %s failed (exit %d)", label, result.returncode)
            sys.exit(1)

    log.info("✓ Full ETL pipeline complete.")


if __name__ == "__main__":
    main()
