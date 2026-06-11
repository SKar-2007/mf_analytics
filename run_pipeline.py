"""
Bluestock MF Capstone — Master Pipeline Runner

Usage:
    python run_pipeline.py                  # Full pipeline
    python run_pipeline.py --steps 1-5      # Custom step range
    python run_pipeline.py --skip 3,4       # Skip specific steps
    python run_pipeline.py --list           # List steps
    python run_pipeline.py --quality        # Also run data quality check

Features:
    - CLI argument support for step selection
    - Progress bars via tqdm
    - Audit log (tracks each run with timestamps)
    - Graceful failure (continues on non-critical errors)
    - Data quality report generation
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
from config import config
from utils.logging_setup import setup_logger

logger = setup_logger("pipeline")
AUDIT_LOG = BASE_DIR / "reports" / "pipeline_audit.json"


STEPS: List[Tuple[str, str, bool]] = [
    ("Data Ingestion",          "scripts/data_ingestion.py",        False),
    ("Live NAV Fetch",          "scripts/live_nav_fetch.py",        False),
    ("Data Cleaning",           "scripts/data_cleaning.py",         False),
    ("Database Load",           "scripts/load_database.py",         False),
    ("Performance Analytics",   "scripts/performance_analytics.py", False),
    ("EDA Charts (15)",         "scripts/generate_eda_charts.py",   False),
    ("Performance Charts",      "scripts/generate_performance_charts.py", False),
    ("Advanced Analytics",      "scripts/generate_advanced_charts.py",   False),
    ("Data Quality Report",     "scripts/data_quality_report.py",   True),
    ("Portfolio Optimizer",     "scripts/portfolio_optimizer.py",   True),
    ("Anomaly Detector",        "scripts/anomaly_detector.py",      True),
]

EXTRA_STEPS: List[Tuple[str, str, bool]] = [
    ("Portfolio Optimizer",     "scripts/portfolio_optimizer.py",   True),
    ("Anomaly Detector",        "scripts/anomaly_detector.py",      True),
]


def parse_step_range(s: str) -> List[int]:
    indices = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            indices.extend(range(int(a), int(b) + 1))
        else:
            indices.append(int(part))
    return indices


def list_steps() -> None:
    print("\nAvailable pipeline steps:")
    for i, (label, script, optional) in enumerate(STEPS, 1):
        tag = " [optional]" if optional else ""
        print(f"  {i:2d}. {label:30s} ({script}){tag}")


def run_step(
    label: str, script: str, optional: bool, desc: Optional[str] = None
) -> bool:
    script_path = BASE_DIR / script
    if not script_path.exists():
        if optional:
            logger.warning("Script not found (skipping): %s", script_path)
            return True
        logger.error("Script not found: %s", script_path)
        return False

    logger.info("─" * 50)
    logger.info("Running: %s", label)
    logger.info("─" * 50)

    start = time.time()
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=False,
        timeout=600,
    )
    elapsed = time.time() - start

    if result.returncode == 0:
        logger.info("OK (%s): %.1fs", label, elapsed)
        return True

    msg = f"FAILED: {label} (exit={result.returncode}, {elapsed:.1f}s)"
    if optional:
        logger.warning("%s — non-critical, continuing", msg)
        return True
    logger.error(msg)
    return False


def append_audit(step_results: List[dict]) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "total_steps": len(step_results),
        "passed": sum(1 for r in step_results if r["status"] == "passed"),
        "failed": sum(1 for r in step_results if r["status"] == "failed"),
        "skipped": sum(1 for r in step_results if r["status"] == "skipped"),
        "steps": step_results,
    }
    try:
        if AUDIT_LOG.exists():
            with open(AUDIT_LOG) as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        else:
            history = []
        history.append(entry)
        history = history[-50:]
        with open(AUDIT_LOG, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.warning("Could not write audit log: %s", e)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bluestock MF Capstone — Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py                    # All core steps
  python run_pipeline.py --steps 1-5        # Steps 1 through 5
  python run_pipeline.py --skip 3,4         # Skip steps 3 and 4
  python run_pipeline.py --all              # Core + optional steps
  python run_pipeline.py --quality          # Core + quality report + analytics
  python run_pipeline.py --list --all       # Show full step list
        """,
    )
    parser.add_argument("--steps", type=str, help="Step range (e.g. 1-5, 1,3,5)")
    parser.add_argument("--skip", type=str, help="Steps to skip (e.g. 2,4)")
    parser.add_argument("--list", action="store_true", help="List available steps")
    parser.add_argument("--all", action="store_true", help="Run all steps including optional")
    parser.add_argument("--quality", action="store_true", help="Include data quality check")
    args = parser.parse_args()

    if args.list:
        list_steps()
        return

    selected_steps = list(STEPS)

    if args.all or args.quality:
        pass
    elif args.steps:
        indices = parse_step_range(args.steps)
        selected_steps = [s for i, s in enumerate(STEPS, 1) if i in indices]
    elif args.skip:
        skip_indices = parse_step_range(args.skip)
        selected_steps = [s for i, s in enumerate(STEPS, 1) if i not in skip_indices]
    else:
        selected_steps = [s for s in STEPS if not s[2]]

    selected_steps = [s for s in selected_steps if s[2] is False or args.all or args.quality]

    if not selected_steps:
        logger.warning("No steps selected. Use --list to see available steps.")
        return

    logger.info("Starting pipeline: %s", config.resolve("project", "name") or "Bluestock MF")
    logger.info("Steps: %d (%s)", len(selected_steps), ", ".join(s[0] for s in selected_steps))

    step_results: List[dict] = []
    all_ok = True

    step_iter = selected_steps
    if tqdm:
        step_iter = tqdm(selected_steps, desc="Pipeline", unit="step")

    for label, script, optional in step_iter:
        if tqdm and hasattr(step_iter, "set_description"):
            step_iter.set_description(f"Running: {label[:30]}")

        ok = run_step(label, script, optional)
        step_results.append({
            "step": label,
            "script": script,
            "status": "passed" if ok else "failed",
        })
        if not ok:
            all_ok = False

    append_audit(step_results)

    passed = sum(1 for r in step_results if r["status"] == "passed")
    failed = sum(1 for r in step_results if r["status"] == "failed")

    logger.info("═" * 50)
    logger.info("Pipeline complete: %d passed, %d failed out of %d steps",
                passed, failed, len(step_results))
    logger.info("═" * 50)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
