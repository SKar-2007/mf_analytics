import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_DIR = BASE_DIR / "data" / "db"
DB_PATH = DB_DIR / "bluestock_mf.db"

RISK_MAP = {
    "Low": ["Low", "Moderately Low"],
    "Moderate": ["Moderate", "Moderately High"],
    "High": ["High", "Very High"],
}

def recommend_funds(risk_appetite="Moderate", top_n=3):
    fund = pd.read_csv(PROCESSED_DIR / "fund_master.csv")
    perf = pd.read_csv(PROCESSED_DIR / "scheme_performance.csv")
    merged = fund.merge(perf, on="amfi_code", suffixes=("_fund", "_perf"))
    risk_col = "risk_grade_fund" if "risk_grade_fund" in merged.columns else "risk_grade"
    eligible = RISK_MAP.get(risk_appetite, [])
    filtered = merged[merged[risk_col].isin(eligible)]
    sharpe_col = "sharpe_ratio" if "sharpe_ratio" in filtered.columns else "return_3yr_pct"
    name_col = "scheme_name_fund" if "scheme_name_fund" in filtered.columns else "scheme_name"
    house_col = "fund_house_fund" if "fund_house_fund" in filtered.columns else "fund_house"
    exp_col = "expense_ratio_pct_fund" if "expense_ratio_pct_fund" in filtered.columns else "expense_ratio_pct"
    if sharpe_col not in filtered.columns:
        print("No sharpe_ratio column available; using return_3yr_pct as proxy")
        sharpe_col = "return_3yr_pct"
    return filtered.nlargest(top_n, sharpe_col)[
        [name_col, house_col, sharpe_col, exp_col, risk_col]
    ]

if __name__ == "__main__":
    for appetite in ["Low", "Moderate", "High"]:
        print(f"\n--- Top 3 funds for {appetite} risk ---")
        result = recommend_funds(appetite)
        print(result.to_string(index=False))
