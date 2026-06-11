import pandas as pd
import numpy as np
from pathlib import Path
from scipy.stats import linregress

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CHARTS_DIR = BASE_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

RF_ANNUAL = 0.065
RF_DAILY = RF_ANNUAL / 252

def load_data():
    nav = pd.read_csv(PROCESSED_DIR / "nav_history.csv")
    nav["date"] = pd.to_datetime(nav["date_id"])
    perf = pd.read_csv(PROCESSED_DIR / "scheme_performance.csv")
    fund = pd.read_csv(PROCESSED_DIR / "fund_master.csv")
    bench = pd.read_csv(PROCESSED_DIR / "benchmark_data.csv")
    return nav, perf, fund, bench

def compute_daily_returns(nav):
    nav_pivot = nav.pivot(index="date", columns="amfi_code", values="nav")
    daily_returns = nav_pivot.pct_change().dropna()
    return daily_returns

def compute_cagr(nav):
    yearly = {}
    for code in nav["amfi_code"].unique():
        s = nav[nav["amfi_code"] == code].sort_values("date")
        if len(s) < 2:
            continue
        start_nav = s["nav"].iloc[0]
        end_nav = s["nav"].iloc[-1]
        days = (s["date"].iloc[-1] - s["date"].iloc[0]).days
        years = days / 365.25
        cagr_val = (end_nav / start_nav) ** (1 / years) - 1 if years > 0 else np.nan
        yearly[code] = cagr_val
    return pd.Series(yearly, name="cagr")

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
        results[code] = {"beta": slope, "alpha_annualised": intercept * 252, "r_squared": r ** 2}
    return pd.DataFrame(results).T

def max_drawdown(nav_series):
    rolling_max = nav_series.cummax()
    drawdown = nav_series / rolling_max - 1
    mdd = drawdown.min()
    end_date = drawdown.idxmin()
    start_date = nav_series[:end_date].idxmax()
    return mdd, start_date, end_date

if __name__ == "__main__":
    nav, perf, fund, bench = load_data()
    daily_returns = compute_daily_returns(nav)
    print(f"Daily returns shape: {daily_returns.shape}")
    print(daily_returns.describe())

    cagr_vals = compute_cagr(nav)
    print(f"\nCAGR:\n{cagr_vals.sort_values(ascending=False).head(10)}")

    sharpe, sortino = compute_sharpe_sortino(daily_returns)
    print(f"\nTop 5 Sharpe:\n{sharpe.sort_values(ascending=False).head()}")

    bench_nifty = bench[bench["index_name"] == "NIFTY50"].copy()
    bench_nifty["date"] = pd.to_datetime(bench_nifty["date_id"])
    bench_nifty = bench_nifty.set_index("date")["close_value"]
    bench_returns = bench_nifty.pct_change().dropna()

    ab = compute_alpha_beta(daily_returns, bench_returns)
    (BASE_DIR / "reports").mkdir(parents=True, exist_ok=True)
    ab.to_csv(BASE_DIR / "reports" / "alpha_beta.csv")
    print(f"\nAlpha/Beta saved. Shape: {ab.shape}")

    mdd_results = {}
    for code in daily_returns.columns:
        cum_nav = (1 + daily_returns[code]).cumprod()
        mdd, start, end = max_drawdown(cum_nav)
        mdd_results[code] = {"max_drawdown": mdd, "start_date": start, "end_date": end}
    mdd_df = pd.DataFrame(mdd_results).T
    print(f"\nWorst MDD:\n{mdd_df.sort_values('max_drawdown').head()}")
