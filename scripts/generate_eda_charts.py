import os
import sqlite3
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"
CHARTS_DIR = BASE_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 300, "figure.figsize": (12, 6)})

def get_conn():
    return sqlite3.connect(DB_PATH)

# --- Chart 1: Daily NAV trend — all schemes ---
def chart_nav_trend():
    conn = get_conn()
    df = pd.read_sql("SELECT date_id, amfi_code, nav FROM fact_nav ORDER BY date_id", conn)
    conn.close()
    pivot = df.pivot(index="date_id", columns="amfi_code", values="nav").ffill()
    fig = px.line(pivot, x=pivot.index, y=pivot.columns[:40],
                  title="Daily NAV Trends — All Schemes (2022–2026)",
                  labels={"date_id": "Date", "value": "NAV (INR)"})
    fig.add_vrect(x0="2023-03-01", x1="2023-12-31", fillcolor="green", opacity=0.08,
                  annotation_text="2023 Bull Run", annotation_position="top left")
    fig.add_vrect(x0="2024-05-01", x1="2024-06-15", fillcolor="red", opacity=0.12,
                  annotation_text="2024 Correction", annotation_position="bottom left")
    fig.update_layout(template="plotly_white", showlegend=False)
    fig.write_image(str(CHARTS_DIR / "01_nav_trend.png"), width=1400, height=700, scale=2)
    print("Chart 1: NAV trends saved")

# --- Chart 2: AUM grouped bar by fund house ---
def chart_aum_bar():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT d.calendar_year, a.fund_house, a.aum_lakh_crore
        FROM fact_aum a
        JOIN dim_date d ON a.date_id = d.date_id
        WHERE strftime('%m', a.date_id) = '12' OR strftime('%m', a.date_id) = '03'
    """, conn)
    conn.close()
    df = df[df["fund_house"].isin(df["fund_house"].value_counts().nlargest(8).index)]
    plt.figure()
    sns.barplot(data=df, x="calendar_year", y="aum_lakh_crore", hue="fund_house", palette="viridis")
    plt.title("AUM by Fund House (2022–2025)", weight="bold")
    plt.xlabel("Year")
    plt.ylabel("AUM (₹ Lakh Crore)")
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    max_row = df.loc[df["aum_lakh_crore"].idxmax()]
    plt.annotate(f"SBI: {max_row['aum_lakh_crore']}L Cr",
                 xy=(max_row["calendar_year"], max_row["aum_lakh_crore"]),
                 xytext=(max_row["calendar_year"] - 0.5, max_row["aum_lakh_crore"] + 0.5),
                 arrowprops=dict(facecolor="black", shrink=0.05))
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "02_aum_bar.png")
    plt.close()
    print("Chart 2: AUM bar saved")

# --- Chart 3: SIP monthly inflow time-series ---
def chart_sip_inflow():
    conn = get_conn()
    df = pd.read_sql("SELECT sip_inflow_crore, month FROM fact_sip ORDER BY month", conn)
    conn.close()
    df["month_dt"] = pd.to_datetime(df["month"])
    fig = px.line(df, x="month", y="sip_inflow_crore",
                  title="Monthly SIP Inflows (2022–2025)",
                  labels={"month": "Date", "sip_inflow_crore": "SIP Inflow (₹ Crore)"})
    peak = df.loc[df["sip_inflow_crore"].idxmax()]
    fig.add_annotation(x=peak["month"], y=peak["sip_inflow_crore"],
                       text=f"ATH: ₹{int(peak['sip_inflow_crore']):,} Cr",
                       showarrow=True, arrowhead=2, ax=-80, ay=-40,
                       font=dict(color="white", size=11),
                       bgcolor="darkblue")
    fig.update_layout(template="plotly_white")
    fig.write_image(str(CHARTS_DIR / "03_sip_inflow.png"), width=1400, height=700, scale=2)
    print("Chart 3: SIP inflow saved")

# --- Chart 4: Category inflow heatmap ---
def chart_category_heatmap():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT month, category, net_inflow_crore
        FROM fact_category_inflow ORDER BY month
    """, conn)
    conn.close()
    df["month_short"] = pd.to_datetime(df["month"]).dt.strftime("%Y-%m")
    pivot = df.pivot(index="category", columns="month_short", values="net_inflow_crore").fillna(0)
    plt.figure(figsize=(14, 6))
    sns.heatmap(pivot, cmap="RdYlGn", center=0, cbar_kws={"label": "₹ Crore"}, linewidths=0.2)
    plt.title("Category-wise Net Inflow Heatmap", weight="bold")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "04_category_heatmap.png")
    plt.close()
    print("Chart 4: Category heatmap saved")

# --- Chart 5: Age group distribution pie ---
def chart_age_pie():
    conn = get_conn()
    df = pd.read_sql("SELECT age_group, SUM(amount) as total FROM fact_transactions GROUP BY age_group", conn)
    conn.close()
    plt.figure()
    plt.pie(df["total"], labels=df["age_group"], autopct="%1.1f%%",
            colors=sns.color_palette("pastel"), startangle=140)
    plt.title("Transaction Volume by Age Group", weight="bold")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "05_age_pie.png")
    plt.close()
    print("Chart 5: Age pie saved")

# --- Chart 6: SIP box plot by age group ---
def chart_sip_box():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT age_group, amount FROM fact_transactions
        WHERE transaction_type = 'SIP' AND amount IS NOT NULL
    """, conn)
    conn.close()
    plt.figure()
    sns.boxplot(data=df, x="age_group", y="amount", palette="Set2", showfliers=False)
    plt.title("SIP Amount Distribution by Age Group", weight="bold")
    plt.ylabel("Amount (₹)")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "06_sip_box.png")
    plt.close()
    print("Chart 6: SIP box saved")

# --- Chart 7: Gender split donut ---
def chart_gender_donut():
    conn = get_conn()
    df = pd.read_sql("SELECT gender, COUNT(DISTINCT investor_id) as cnt FROM fact_transactions GROUP BY gender", conn)
    conn.close()
    fig = go.Figure(data=[go.Pie(labels=df["gender"], values=df["cnt"], hole=0.4)])
    fig.update_layout(title="Investor Gender Distribution", template="plotly_white")
    fig.write_image(str(CHARTS_DIR / "07_gender_donut.png"), width=800, height=600, scale=2)
    print("Chart 7: Gender donut saved")

# --- Chart 8: SIP by state — horizontal bar ---
def chart_state_bar():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT state, SUM(amount) as total FROM fact_transactions
        WHERE transaction_type = 'SIP' GROUP BY state ORDER BY total DESC LIMIT 15
    """, conn)
    conn.close()
    plt.figure()
    sns.barplot(data=df, x="total", y="state", palette="flare")
    plt.title("Top 15 States by SIP Volume", weight="bold")
    plt.xlabel("Total SIP Amount (₹)")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "08_state_bar.png")
    plt.close()
    print("Chart 8: State bar saved")

# --- Chart 9: T30 vs B30 city tier pie ---
def chart_tier_pie():
    conn = get_conn()
    df = pd.read_sql("SELECT city_tier, SUM(amount) as total FROM fact_transactions GROUP BY city_tier", conn)
    conn.close()
    fig = go.Figure(data=[go.Pie(labels=df["city_tier"], values=df["total"], hole=0.3)])
    fig.update_layout(title="T30 vs B30 City Tier Transaction Share", template="plotly_white")
    fig.write_image(str(CHARTS_DIR / "09_tier_pie.png"), width=800, height=600, scale=2)
    print("Chart 9: Tier pie saved")

# --- Chart 10: Folio count growth line ---
def chart_folio_growth():
    conn = get_conn()
    df = pd.read_sql("SELECT month, total_folios_crore FROM fact_folio ORDER BY month", conn)
    conn.close()
    df["month_dt"] = pd.to_datetime(df["month"])
    plt.figure()
    plt.plot(df["month_dt"], df["total_folios_crore"], marker="o", markersize=4, color="darkgreen", linewidth=2)
    plt.title("Folio Count Growth (2022–2025)", weight="bold")
    plt.xlabel("Date")
    plt.ylabel("Total Folios (Crore)")
    for _, row in df.iterrows():
        if row["total_folios_crore"] in [df["total_folios_crore"].min(), df["total_folios_crore"].max()]:
            plt.annotate(f"{row['total_folios_crore']} Cr", xy=(row["month_dt"], row["total_folios_crore"]))
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "10_folio_growth.png")
    plt.close()
    print("Chart 10: Folio growth saved")

# --- Chart 11: NAV return correlation matrix ---
def chart_correlation():
    conn = get_conn()
    df = pd.read_sql("SELECT date_id, amfi_code, nav FROM fact_nav", conn)
    conn.close()
    pivot = df.pivot(index="date_id", columns="amfi_code", values="nav").ffill()
    returns = pivot.pct_change().dropna()
    top10 = returns.columns[:10]
    corr = returns[top10].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, square=True)
    plt.title("Daily Return Correlation — Top 10 Schemes", weight="bold")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "11_correlation.png")
    plt.close()
    print("Chart 11: Correlation saved")

# --- Chart 12: Sector allocation donut ---
def chart_sector_donut():
    conn = get_conn()
    df = pd.read_sql("SELECT sector, SUM(weight_pct) as total FROM fact_portfolio GROUP BY sector ORDER BY total DESC", conn)
    conn.close()
    fig = go.Figure(data=[go.Pie(labels=df["sector"], values=df["total"], hole=0.4)])
    fig.update_layout(title="Sector Allocation (All Equity Schemes)", template="plotly_white")
    fig.write_image(str(CHARTS_DIR / "12_sector_donut.png"), width=900, height=700, scale=2)
    print("Chart 12: Sector donut saved")

# --- Chart 13: Expense ratio distribution ---
def chart_expense_hist():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT f.plan_type, p.expense_ratio_pct
        FROM fact_performance p
        JOIN dim_fund f ON p.amfi_code = f.amfi_code
        WHERE p.expense_ratio_pct IS NOT NULL
    """, conn)
    conn.close()
    plt.figure()
    sns.histplot(data=df, x="expense_ratio_pct", hue="plan_type", bins=15, kde=True, palette="Set2")
    plt.title("Expense Ratio Distribution — Direct vs Regular", weight="bold")
    plt.xlabel("Expense Ratio (%)")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "13_expense_hist.png")
    plt.close()
    print("Chart 13: Expense hist saved")

# --- Chart 14: Monthly transaction volume bar ---
def chart_txn_volume():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT strftime('%Y-%m', date_id) as month, transaction_type, COUNT(*) as cnt
        FROM fact_transactions
        GROUP BY month, transaction_type ORDER BY month
    """, conn)
    conn.close()
    fig = px.bar(df, x="month", y="cnt", color="transaction_type",
                 title="Monthly Transaction Volume by Type",
                 labels={"month": "Month", "cnt": "Transaction Count", "transaction_type": "Type"})
    fig.update_layout(template="plotly_white")
    fig.write_image(str(CHARTS_DIR / "14_txn_volume.png"), width=1400, height=700, scale=2)
    print("Chart 14: Txn volume saved")

# --- Chart 15: AUM vs Return scatter ---
def chart_aum_return_scatter():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT f.category, f.fund_house, p.aum_crore, p.return_3yr_pct,
               p.std_dev_ann_pct, p.sharpe_ratio
        FROM fact_performance p
        JOIN dim_fund f ON p.amfi_code = f.amfi_code
        WHERE p.aum_crore IS NOT NULL
    """, conn)
    conn.close()
    fig = px.scatter(df, x="return_3yr_pct", y="std_dev_ann_pct",
                     size="aum_crore", color="category",
                     hover_name="fund_house",
                     title="AUM vs Return vs Risk (Bubble = AUM)",
                     labels={"return_3yr_pct": "3-Year Return (%)",
                             "std_dev_ann_pct": "Annualised Std Dev (%)"})
    fig.update_layout(template="plotly_white")
    fig.write_image(str(CHARTS_DIR / "15_aum_return_scatter.png"), width=1400, height=800, scale=2)
    print("Chart 15: AUM-return scatter saved")

if __name__ == "__main__":
    chart_nav_trend()
    chart_aum_bar()
    chart_sip_inflow()
    chart_category_heatmap()
    chart_age_pie()
    chart_sip_box()
    chart_gender_donut()
    chart_state_bar()
    chart_tier_pie()
    chart_folio_growth()
    chart_correlation()
    chart_sector_donut()
    chart_expense_hist()
    chart_txn_volume()
    chart_aum_return_scatter()
    print(f"\nAll 15 charts saved to {CHARTS_DIR}")
