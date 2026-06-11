import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from pathlib import Path
from scipy.stats import linregress

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"
CHARTS_DIR = BASE_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

RF_ANNUAL = 0.065
RF_DAILY = RF_ANNUAL / 252

def load_nav():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT date_id, amfi_code, nav FROM fact_nav ORDER BY date_id", conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date_id"])
    return df

def load_benchmark():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT date_id, index_name, close_value FROM fact_benchmark ORDER BY date_id", conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date_id"])
    return df

def load_fund_and_perf():
    conn = sqlite3.connect(DB_PATH)
    fund = pd.read_sql("SELECT * FROM dim_fund", conn)
    perf = pd.read_sql("SELECT * FROM fact_performance", conn)
    conn.close()
    return fund, perf

def make_scorecard():
    print("Building fund scorecard...")
    nav = load_nav()
    pivot = nav.pivot(index="date", columns="amfi_code", values="nav").ffill()
    daily_returns = pivot.pct_change().dropna()
    fund, perf = load_fund_and_perf()
    merged = fund.merge(perf, on="amfi_code")

    cagr = {}
    for code in daily_returns.columns:
        s = pivot[code].dropna()
        if len(s) < 2:
            continue
        years = (s.index[-1] - s.index[0]).days / 365.25
        if years > 0:
            cagr[code] = (s.iloc[-1] / s.iloc[0]) ** (1 / years) - 1
    cagr_s = pd.Series(cagr, name="cagr_3yr")

    mean_ret = daily_returns.mean()
    std_ret = daily_returns.std()
    downside = daily_returns[daily_returns < 0].std()
    sharpe = (mean_ret - RF_DAILY) / std_ret * np.sqrt(252)
    sortino = (mean_ret - RF_DAILY) / downside * np.sqrt(252)

    bench = load_benchmark()
    b = bench[bench["index_name"] == "NIFTY50"].copy().set_index("date")["close_value"]
    bench_ret = b.pct_change().dropna()

    alpha_beta = {}
    for code in daily_returns.columns:
        fr = daily_returns[code].dropna()
        aligned = fr.align(bench_ret, join="inner")
        if len(aligned[0]) < 30:
            continue
        slope, intercept, r, _, _ = linregress(aligned[1], aligned[0])
        alpha_beta[code] = {"alpha_annualised": intercept * 252, "beta": slope, "r_squared": r ** 2}
    ab_df = pd.DataFrame(alpha_beta).T

    mdd = {}
    for code in daily_returns.columns:
        cum = (1 + daily_returns[code]).cumprod()
        roll_max = cum.cummax()
        dd = (cum / roll_max - 1).min()
        mdd[code] = dd

    score = pd.DataFrame(index=daily_returns.columns)
    score["cagr_rank"] = cagr_s.rank(ascending=False)
    score["sharpe_rank"] = sharpe.rank(ascending=False)
    score["alpha_rank"] = ab_df["alpha_annualised"].rank(ascending=False)
    score["beta_rank"] = ab_df["beta"].rank(ascending=True)
    score["mdd_rank"] = pd.Series(mdd).rank(ascending=True)

    n = len(score)
    for col in score.columns:
        score[col + "_score"] = (n - score[col] + 1) / n * 100

    score["total_score"] = (
        0.30 * score["cagr_rank_score"]
        + 0.25 * score["sharpe_rank_score"]
        + 0.20 * score["alpha_rank_score"]
        + 0.15 * score["beta_rank_score"]
        + 0.10 * score["mdd_rank_score"]
    )
    score = score.sort_values("total_score", ascending=False)
    score.index.name = "amfi_code"
    score = score.reset_index()

    name_map = dict(zip(merged["amfi_code"], merged["scheme_name"]))
    house_map = dict(zip(merged["amfi_code"], merged["fund_house"]))
    score["scheme_name"] = score["amfi_code"].map(name_map)
    score["fund_house"] = score["amfi_code"].map(house_map)

    (BASE_DIR / "reports").mkdir(parents=True, exist_ok=True)
    score.to_csv(BASE_DIR / "reports" / "fund_scorecard.csv", index=False)
    print(f"Fund scorecard saved: {len(score)} funds ranked")
    return score, daily_returns, bench_ret, merged

def chart_benchmark_comparison(score, daily_returns, bench_ret, merged):
    print("Generating benchmark comparison chart...")
    top5 = score["amfi_code"].head(5).tolist()
    name_map = dict(zip(merged["amfi_code"], merged["scheme_name"]))
    cum_funds = (1 + daily_returns[top5]).cumprod()
    cum_bench = (1 + bench_ret).cumprod()

    fig = go.Figure()
    for code in top5:
        label = name_map.get(code, str(code))[:30]
        fig.add_trace(go.Scatter(x=cum_funds.index, y=cum_funds[code],
                                 mode="lines", name=label))
    fig.add_trace(go.Scatter(x=cum_bench.index, y=cum_bench,
                             mode="lines", name="NIFTY50",
                             line=dict(color="black", width=3, dash="dash")))
    fig.update_layout(title="Top 5 Scorecard Funds vs NIFTY50 (Rebased)",
                      xaxis_title="Date", yaxis_title="Cumulative Return (₹1 → ...)",
                      template="plotly_white", legend=dict(x=0.01, y=0.99))
    fig.write_image(str(CHARTS_DIR / "benchmark_comparison.png"),
                    width=1400, height=700, scale=2)
    print("Benchmark comparison chart saved")

def chart_sharpe_ranking(score, merged):
    print("Generating Sharpe ranking chart...")
    name_map = dict(zip(merged["amfi_code"], merged["scheme_name"]))
    top10_sharpe = score.head(10)
    labels = [name_map.get(c, str(c))[:25] for c in top10_sharpe["amfi_code"]]
    fig = go.Figure(go.Bar(x=top10_sharpe["total_score"], y=labels,
                           orientation="h", marker_color="darkblue"))
    fig.update_layout(title="Top 10 Funds by Scorecard Score",
                      xaxis_title="Score (0–100)", yaxis_title="",
                      template="plotly_white", height=500)
    fig.write_image(str(CHARTS_DIR / "scorecard_bar.png"),
                    width=1200, height=600, scale=2)
    print("Scorecard ranking chart saved")

def chart_alpha_beta_scatter(merged):
    print("Generating alpha-beta scatter...")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=merged["beta"], y=merged["alpha"],
        mode="markers+text",
        text=merged["scheme_name"].apply(lambda x: x[:20]),
        textposition="top center",
        marker=dict(size=merged["aum_crore"] / 1000, sizemode="area",
                    sizeref=2 * max(merged["aum_crore"]) / (40 ** 2),
                    color=merged["return_3yr_pct"], colorscale="RdYlGn",
                    showscale=True, colorbar=dict(title="3Y Return %"))
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.add_vline(x=1, line_dash="dash", line_color="gray")
    fig.update_layout(title="Alpha vs Beta (Bubble = AUM, Color = 3Y Return)",
                      xaxis_title="Beta", yaxis_title="Alpha (Annualised)",
                      template="plotly_white", height=700)
    fig.write_image(str(CHARTS_DIR / "alpha_beta_scatter.png"),
                    width=1200, height=800, scale=2)
    print("Alpha-Beta scatter saved")

if __name__ == "__main__":
    score, daily_returns, bench_ret, merged = make_scorecard()
    chart_benchmark_comparison(score, daily_returns, bench_ret, merged)
    chart_sharpe_ranking(score, merged)
    chart_alpha_beta_scatter(merged)
    print(f"\nAll performance charts saved to {CHARTS_DIR}")
