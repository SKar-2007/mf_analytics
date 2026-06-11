"""
Bluestock MF Capstone — Fund Recommender Engine (D6 deliverable)

Recommends top N funds based on risk appetite using Sharpe ratio.

Usage:
    python scripts/recommender.py
"""

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent
PROCESSED = BASE / "data" / "processed"

RISK_MAP = {
    "Low": ["Low", "Moderately Low"],
    "Moderate": ["Moderate", "Moderately High"],
    "High": ["High", "Very High"],
}


def recommend_funds(risk_appetite: str = "Moderate", top_n: int = 3) -> pd.DataFrame:
    """
    Returns top N funds for a given risk appetite based on Sharpe ratio.

    Parameters:
        risk_appetite: "Low" | "Moderate" | "High"
        top_n: number of funds to return (default 3)

    Returns:
        DataFrame with scheme_name, fund_house, sharpe_ratio, expense_ratio, risk_grade
    """
    fund = pd.read_csv(PROCESSED / "fund_master.csv")
    perf = pd.read_csv(PROCESSED / "scheme_performance.csv")
    merged = fund.merge(perf, on="amfi_code", suffixes=("_fund", "_perf"))

    risk_col = "risk_grade_fund" if "risk_grade_fund" in merged.columns else "risk_grade"
    eligible_grades = RISK_MAP.get(risk_appetite, [])
    filtered = merged[merged[risk_col].isin(eligible_grades)]

    sharpe_col = "sharpe_ratio" if "sharpe_ratio" in filtered.columns else "return_3yr_pct"
    name_col = "scheme_name_fund" if "scheme_name_fund" in filtered.columns else "scheme_name"
    house_col = "fund_house_fund" if "fund_house_fund" in filtered.columns else "fund_house"
    exp_col = "expense_ratio_pct_fund" if "expense_ratio_pct_fund" in filtered.columns else "expense_ratio_pct"

    if sharpe_col not in filtered.columns:
        log.warning("No sharpe_ratio column; using return_3yr_pct as proxy")
        sharpe_col = "return_3yr_pct"

    return filtered.nlargest(top_n, sharpe_col)[
        [name_col, house_col, sharpe_col, exp_col, risk_col]
    ]


def main():
    for appetite in ["Low", "Moderate", "High"]:
        print(f"\n--- Top 3 funds for {appetite} risk ---")
        result = recommend_funds(appetite)
        print(result.to_string(index=False))


if __name__ == "__main__":
    main()
