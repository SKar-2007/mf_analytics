import sqlite3
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"
CHARTS_DIR = BASE_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

RF_DAILY = 0.065 / 252

def load_daily_returns():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT date_id, amfi_code, nav FROM fact_nav ORDER BY date_id", conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date_id"])
    pivot = df.pivot(index="date", columns="amfi_code", values="nav").ffill()
    return pivot.pct_change().dropna()

def load_transactions():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT t.investor_id, t.date_id, t.amfi_code, t.transaction_type, t.amount
        FROM fact_transactions t
        ORDER BY t.investor_id, t.date_id
    """, conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date_id"])
    return df

def load_portfolio():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT amfi_code, sector, weight_pct FROM fact_portfolio", conn)
    conn.close()
    return df

# --- 6.1: Historical VaR (95%) & CVaR ---
def compute_var_cvar(daily_returns):
    print("Computing VaR and CVaR...")
    results = {}
    for code in daily_returns.columns:
        s = daily_returns[code].dropna()
        var = s.quantile(0.05)
        cvar = s[s <= var].mean()
        results[code] = {"VaR_95": var, "CVaR_95": cvar}
    df = pd.DataFrame(results).T.sort_values("VaR_95")
    (BASE_DIR / "reports").mkdir(parents=True, exist_ok=True)
    df.to_csv(BASE_DIR / "reports" / "var_cvar_report.csv")
    print(f"VaR/CVaR report saved: {len(df)} funds")
    return df

def chart_var_cvar(var_df):
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("Historical VaR (95%)", "Conditional VaR (95%)"))
    fig.add_trace(go.Bar(x=var_df.index.astype(str), y=var_df["VaR_95"],
                         marker_color="crimson"), row=1, col=1)
    fig.add_trace(go.Bar(x=var_df.index.astype(str), y=var_df["CVaR_95"],
                         marker_color="darkorange"), row=1, col=2)
    fig.update_layout(title="Value at Risk & Conditional VaR (95% Confidence)",
                      xaxis_title="Fund Code", yaxis_title="Daily Return",
                      template="plotly_white", showlegend=False, height=500)
    fig.write_image(str(CHARTS_DIR / "var_cvar.png"), width=1400, height=600, scale=2)
    print("VaR/CVaR chart saved")

# --- 6.2: Rolling 90-Day Sharpe ---
def chart_rolling_sharpe(daily_returns):
    print("Computing rolling 90-day Sharpe...")
    key_codes = daily_returns.columns[:5]
    window = 90
    rolling = (
        daily_returns[key_codes].rolling(window).mean() - RF_DAILY
    ) / daily_returns[key_codes].rolling(window).std() * np.sqrt(252)

    fig = go.Figure()
    for code in key_codes:
        fig.add_trace(go.Scatter(x=rolling.index, y=rolling[code].dropna(),
                                 mode="lines", name=str(code)))
    fig.add_hline(y=1, line_dash="dash", line_color="gray",
                  annotation_text="Sharpe = 1")
    fig.update_layout(title="Rolling 90-Day Sharpe Ratio (Top 5 Funds)",
                      xaxis_title="Date", yaxis_title="Sharpe Ratio",
                      template="plotly_white", height=600)
    fig.write_image(str(CHARTS_DIR / "rolling_sharpe.png"),
                    width=1400, height=700, scale=2)
    print("Rolling Sharpe chart saved")

# --- 6.3: Investor Cohort Analysis ---
def chart_cohort_analysis(txn):
    print("Computing investor cohorts...")
    first_txn = txn.groupby("investor_id")["date"].min().dt.year.reset_index()
    first_txn.columns = ["investor_id", "cohort_year"]
    txn = txn.merge(first_txn, on="investor_id")
    cohort = txn.groupby(["cohort_year", "investor_id"]).agg(
        total_invested=("amount", "sum"),
        sip_count=("transaction_type", lambda x: (x == "SIP").sum()),
    ).groupby("cohort_year").mean().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=cohort["cohort_year"], y=cohort["total_invested"],
                         name="Avg Invested (₹)", marker_color="steelblue"))
    fig.add_trace(go.Scatter(x=cohort["cohort_year"], y=cohort["sip_count"],
                             name="Avg SIP Count", yaxis="y2",
                             mode="lines+markers", marker_color="coral"))
    fig.update_layout(title="Investor Cohort Analysis (by First Investment Year)",
                      xaxis_title="Cohort Year",
                      yaxis=dict(title="Avg Total Invested (₹)"),
                      yaxis2=dict(title="Avg SIP Count", overlaying="y", side="right"),
                      template="plotly_white", height=500)
    fig.write_image(str(CHARTS_DIR / "cohort_analysis.png"),
                    width=1200, height=600, scale=2)
    print("Cohort analysis chart saved")

# --- 6.4: SIP Continuity Analysis ---
def sip_continuity(txn):
    print("Analyzing SIP continuity...")
    sip = txn[txn["transaction_type"] == "SIP"].sort_values(["investor_id", "date"])
    sip["gap_days"] = sip.groupby("investor_id")["date"].diff().dt.days
    summary = sip.groupby("investor_id").agg(
        total_sips=("transaction_type", "count"),
        max_gap=("gap_days", "max"),
        avg_gap=("gap_days", "mean"),
    ).reset_index()
    at_risk = summary[(summary["total_sips"] >= 6) & (summary["max_gap"] > 35)]
    pct = len(at_risk) / len(summary[summary["total_sips"] >= 6]) * 100 if len(summary[summary["total_sips"] >= 6]) > 0 else 0
    print(f"At-risk investors (gap > 35 days): {len(at_risk)} ({pct:.1f}%)")
    return summary, at_risk, pct

# --- 6.5: Fund Recommender (already exists in scripts/recommender.py) ---

# --- 6.6: Sector HHI Concentration ---
def chart_hhi_concentration(portfolio):
    print("Computing HHI concentration...")
    hhi = (
        portfolio.groupby("amfi_code")
        .apply(lambda g: ((g["weight_pct"] / 100) ** 2).sum())
        .rename("HHI")
        .reset_index()
    )
    conn = sqlite3.connect(DB_PATH)
    fund = pd.read_sql("SELECT amfi_code, scheme_name, category FROM dim_fund", conn)
    conn.close()
    hhi = hhi.merge(fund, on="amfi_code")
    hhi["label"] = hhi["scheme_name"].apply(lambda x: x[:25])

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("HHI by Fund", "Avg HHI by Category"))
    fig.add_trace(go.Bar(x=hhi["label"], y=hhi["HHI"],
                         marker_color=["red" if v > 0.25 else "green" for v in hhi["HHI"]],
                         name="HHI"), row=1, col=1)
    cat_hhi = hhi.groupby("category")["HHI"].mean().reset_index()
    fig.add_trace(go.Bar(x=cat_hhi["category"], y=cat_hhi["HHI"],
                         marker_color="steelblue", name="Avg HHI"), row=1, col=2)
    fig.add_hline(y=0.25, line_dash="dash", line_color="red",
                  annotation_text="High Concentration Threshold")
    fig.update_layout(title="Sector Concentration (HHI) Analysis",
                      template="plotly_white", showlegend=False, height=600)
    fig.write_image(str(CHARTS_DIR / "hhi_concentration.png"),
                    width=1400, height=700, scale=2)
    print("HHI concentration chart saved")

if __name__ == "__main__":
    daily_returns = load_daily_returns()
    txn = load_transactions()
    portfolio = load_portfolio()

    var_df = compute_var_cvar(daily_returns)
    chart_var_cvar(var_df)

    chart_rolling_sharpe(daily_returns)

    chart_cohort_analysis(txn)

    sip_continuity(txn)

    chart_hhi_concentration(portfolio)

    print(f"\nAll advanced charts saved to {CHARTS_DIR}")
