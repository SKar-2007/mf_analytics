"""
Bluestock MF Capstone — Performance Metrics (D4 deliverable)

Computes CAGR, Sharpe Ratio, Sortino Ratio, Alpha/Beta,
Maximum Drawdown, and Fund Scorecard across all schemes.

Usage:
    python scripts/compute_metrics.py

Outputs:
    reports/fund_scorecard.csv
    reports/alpha_beta.csv
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import linregress

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent
PROCESSED = BASE / "data" / "processed"
REPORTS = BASE / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

RF_ANNUAL = 0.065
RF_DAILY = RF_ANNUAL / 252


def load_data():
    nav = pd.read_csv(PROCESSED / "nav_history.csv")
    nav["date"] = pd.to_datetime(nav["date_id"])
    fund = pd.read_csv(PROCESSED / "fund_master.csv")
    bench = pd.read_csv(PROCESSED / "benchmark_data.csv")
    bench["date"] = pd.to_datetime(bench["date_id"])
    return nav, fund, bench


def compute_daily_returns(nav):
    pivot = nav.pivot(index="date", columns="amfi_code", values="nav").ffill()
    return pivot.pct_change().dropna()


def cagr(nav_start, nav_end, years):
    return (nav_end / nav_start) ** (1 / years) - 1


def compute_cagr_all(pivot):
    results = {}
    for code in pivot.columns:
        s = pivot[code].dropna()
        if len(s) < 2:
            continue
        years = (s.index[-1] - s.index[0]).days / 365.25
        if years > 0:
            results[code] = (s.iloc[-1] / s.iloc[0]) ** (1 / years) - 1
    return pd.Series(results, name="cagr_3yr")


def compute_sharpe_sortino(daily_returns):
    mean_ret = daily_returns.mean()
    std_ret = daily_returns.std()
    downside = daily_returns[daily_returns < 0].std()
    sharpe = (mean_ret - RF_DAILY) / std_ret * np.sqrt(252)
    sortino = (mean_ret - RF_DAILY) / downside * np.sqrt(252)
    return sharpe, sortino


def compute_alpha_beta(daily_returns, bench_returns):
    results = {}
    for code in daily_returns.columns:
        fund_ret = daily_returns[code].dropna()
        aligned = fund_ret.align(bench_returns, join="inner")
        if len(aligned[0]) < 30:
            continue
        slope, intercept, r, p, se = linregress(aligned[1], aligned[0])
        results[code] = {
            "beta": slope,
            "alpha_annualised": intercept * 252,
            "r_squared": r ** 2,
        }
    return pd.DataFrame(results).T


def max_drawdown(nav_series):
    rolling_max = nav_series.cummax()
    drawdown = nav_series / rolling_max - 1
    mdd = drawdown.min()
    end_date = drawdown.idxmin()
    start_date = nav_series[:end_date].idxmax()
    return mdd, start_date, end_date


def build_scorecard(daily_returns, cagr_s, sharpe, alpha_beta, expense_ratio):
    score = pd.DataFrame(index=daily_returns.columns)
    score["return_rank"] = cagr_s.rank(ascending=False)
    score["sharpe_rank"] = sharpe.rank(ascending=False)
    score["alpha_rank"] = alpha_beta["alpha_annualised"].rank(ascending=False)
    score["expense_rank"] = expense_ratio.rank(ascending=True)
    mdd_vals = {}
    for code in daily_returns.columns:
        cum = (1 + daily_returns[code]).cumprod()
        mdd_vals[code], _, _ = max_drawdown(cum)
    score["drawdown_rank"] = pd.Series(mdd_vals).rank(ascending=True)
    n = len(score)
    for col in score.columns:
        score[col.replace("_rank", "_score")] = (n - score[col] + 1) / n * 100
    score["total_score"] = (
        0.30 * score["return_score"]
        + 0.25 * score["sharpe_score"]
        + 0.20 * score["alpha_score"]
        + 0.15 * score["expense_score"]
        + 0.10 * score["drawdown_score"]
    )
    return score.sort_values("total_score", ascending=False)


def main():
    log.info("Loading data...")
    nav, fund, bench = load_data()
    pivot = nav.pivot(index="date", columns="amfi_code", values="nav").ffill()
    daily_returns = compute_daily_returns(nav)
    log.info("Daily returns: %s", daily_returns.shape)

    log.info("Computing CAGR...")
    cagr_s = compute_cagr_all(pivot)
    log.info("Top 5 CAGR:\n%s", cagr_s.sort_values(ascending=False).head().to_string())

    log.info("Computing Sharpe & Sortino...")
    sharpe, sortino = compute_sharpe_sortino(daily_returns)
    log.info("Top 5 Sharpe:\n%s", sharpe.sort_values(ascending=False).head().to_string())

    log.info("Computing Alpha & Beta...")
    b = bench[bench["index_name"] == "NIFTY50"].copy().set_index("date")["close_value"]
    bench_ret = b.pct_change().dropna()
    alpha_beta = compute_alpha_beta(daily_returns, bench_ret)
    alpha_beta.to_csv(REPORTS / "alpha_beta.csv")
    log.info("Alpha/Beta saved: %d funds", len(alpha_beta))

    log.info("Building scorecard...")
    fund_map = pd.read_csv(PROCESSED / "scheme_performance.csv")
    exp_col = "expense_ratio_pct" if "expense_ratio_pct" in fund_map.columns else "expense_ratio"
    expense_ratio = fund_map.set_index("amfi_code")[exp_col] if exp_col in fund_map.columns else pd.Series(0, index=daily_returns.columns)
    scorecard = build_scorecard(daily_returns, cagr_s, sharpe, alpha_beta, expense_ratio)
    fund_names = pd.read_csv(PROCESSED / "fund_master.csv")[["amfi_code", "scheme_name", "fund_house"]]
    scorecard = scorecard.reset_index().merge(fund_names, left_on="index", right_on="amfi_code", how="left")
    scorecard.to_csv(REPORTS / "fund_scorecard.csv", index=False)
    log.info("Scorecard saved: %d funds ranked", len(scorecard))
    log.info("Top 5:\n%s", scorecard[["scheme_name", "fund_house", "total_score"]].head().to_string())

    log.info("All metrics complete.")


if __name__ == "__main__":
    main()
