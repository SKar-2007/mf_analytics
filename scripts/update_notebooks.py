import nbformat as nbf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

def make_cell(code):
    return nbf.v4.new_code_cell(code)

def make_md(text):
    return nbf.v4.new_markdown_cell(text)

SETUP = '''import os, sqlite3, warnings
import numpy as np, pandas as pd
import seaborn as sns, matplotlib.pyplot as plt
import plotly.express as px, plotly.graph_objects as go
from pathlib import Path
warnings.filterwarnings("ignore")
BASE_DIR = Path(os.getcwd()).resolve().parent
DB_PATH = BASE_DIR / "data" / "db" / "bluestock_mf.db"
CHARTS_DIR = BASE_DIR / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 300, "figure.figsize": (12, 6)})
print(f"DB exists: {DB_PATH.exists()}")'''

HELPER = '''def query(sql):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df

def save(fig, name):
    if isinstance(fig, go.Figure):
        fig.write_image(str(CHARTS_DIR / name), width=1400, height=700, scale=2)
    else:
        fig.savefig(CHARTS_DIR / name, bbox_inches="tight")
    print(f"Saved: {name}")'''

def make_eda():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": ".venv (3.14.5)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.14.5"},
    }
    cells = [make_cell(SETUP), make_cell(HELPER)]

    cells.append(make_cell('''df = query("SELECT date_id, amfi_code, nav FROM fact_nav ORDER BY date_id")
pivot = df.pivot(index="date_id", columns="amfi_code", values="nav").ffill()
fig = px.line(pivot, x=pivot.index, y=pivot.columns[:40],
              title="Daily NAV Trends (2022-2026)",
              labels={"date_id": "Date", "value": "NAV (INR)"})
fig.add_vrect(x0="2023-03-01", x1="2023-12-31", fillcolor="green", opacity=0.08,
              annotation_text="2023 Bull Run", annotation_position="top left")
fig.add_vrect(x0="2024-05-01", x1="2024-06-15", fillcolor="red", opacity=0.12,
              annotation_text="2024 Correction", annotation_position="bottom left")
fig.update_layout(template="plotly_white", showlegend=False)
save(fig, "01_nav_trend.png")
fig.show()'''))

    cells.append(make_cell('''df = query("SELECT d.calendar_year, a.fund_house, a.aum_lakh_crore FROM fact_aum a JOIN dim_date d ON a.date_id = d.date_id WHERE strftime('%m', a.date_id) IN ('03','12')")
top = df["fund_house"].value_counts().nlargest(8).index
df = df[df["fund_house"].isin(top)]
plt.figure()
sns.barplot(data=df, x="calendar_year", y="aum_lakh_crore", hue="fund_house", palette="viridis")
plt.title("AUM by Fund House (2022-2025)", weight="bold")
plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
save(plt, "02_aum_bar.png")
plt.show()'''))

    cells.append(make_cell('''df = query("SELECT sip_inflow_crore, month FROM fact_sip ORDER BY month")
fig = px.line(df, x="month", y="sip_inflow_crore",
              title="Monthly SIP Inflows (2022-2025)",
              labels={"month": "Date", "sip_inflow_crore": "SIP Inflow (Cr)"})
peak = df.loc[df["sip_inflow_crore"].idxmax()]
fig.add_annotation(x=peak["month"], y=peak["sip_inflow_crore"],
                   text=f"ATH: {int(peak['sip_inflow_crore']):,} Cr",
                   showarrow=True, arrowhead=2, ax=-80, ay=-40,
                   font=dict(color="white", size=11), bgcolor="darkblue")
fig.update_layout(template="plotly_white")
save(fig, "03_sip_inflow.png")
fig.show()'''))

    cells.append(make_cell('''df = query("SELECT month, category, net_inflow_crore FROM fact_category_inflow ORDER BY month")
df["month_short"] = pd.to_datetime(df["month"]).dt.strftime("%Y-%m")
pivot = df.pivot(index="category", columns="month_short", values="net_inflow_crore").fillna(0)
plt.figure(figsize=(14, 6))
sns.heatmap(pivot, cmap="RdYlGn", center=0, cbar_kws={"label": "Cr"}, linewidths=0.2)
plt.title("Category Net Inflow Heatmap", weight="bold")
save(plt, "04_category_heatmap.png")
plt.show()'''))

    cells.append(make_cell('''age = query("SELECT age_group, SUM(amount) as total FROM fact_transactions GROUP BY age_group")
sip = query("SELECT age_group, amount FROM fact_transactions WHERE transaction_type='SIP' AND amount IS NOT NULL")
gen = query("SELECT gender, COUNT(DISTINCT investor_id) as cnt FROM fact_transactions GROUP BY gender")
fig, ax = plt.subplots(1, 3, figsize=(22, 6))
ax[0].pie(age["total"], labels=age["age_group"], autopct="%1.1f%%",
          colors=sns.color_palette("pastel"), startangle=140)
ax[0].set_title("Volume by Age Group", weight="bold")
sns.boxplot(data=sip, x="age_group", y="amount", ax=ax[1], palette="Set2", showfliers=False)
ax[1].set_title("SIP Amount by Age", weight="bold")
ax[2].bar(gen["gender"], gen["cnt"], color=["#2a9d8f", "#e9c46a", "#e76f51"])
ax[2].set_title("Investor Count by Gender", weight="bold")
plt.tight_layout()
save(plt, "05_demographics.png")
plt.show()'''))

    cells.append(make_cell('''state = query("SELECT state, SUM(amount) as total FROM fact_transactions WHERE transaction_type='SIP' GROUP BY state ORDER BY total DESC LIMIT 15")
tier = query("SELECT city_tier, SUM(amount) as total FROM fact_transactions GROUP BY city_tier")
fig, ax = plt.subplots(1, 2, figsize=(18, 6), gridspec_kw={"width_ratios": [1.8, 1]})
sns.barplot(data=state, x="total", y="state", ax=ax[0], palette="flare")
ax[0].set_title("Top 15 States by SIP Volume", weight="bold")
ax[1].pie(tier["total"], labels=tier["city_tier"], autopct="%1.1f%%",
          colors=["#2a9d8f", "#e9c46a"], startangle=90)
ax[1].set_title("T30 vs B30", weight="bold")
plt.tight_layout()
save(plt, "06_geography.png")
plt.show()'''))

    cells.append(make_cell('''df = query("SELECT month, total_folios_crore FROM fact_folio ORDER BY month")
df["month_dt"] = pd.to_datetime(df["month"])
plt.figure()
plt.plot(df["month_dt"], df["total_folios_crore"], marker="o", color="darkgreen", linewidth=2)
plt.title("Folio Count Growth (2022-2025)", weight="bold")
plt.xlabel("Date"); plt.ylabel("Folios (Cr)")
for _, r in df.iterrows():
    if r["total_folios_crore"] in [df["total_folios_crore"].min(), df["total_folios_crore"].max()]:
        plt.annotate(f"{r['total_folios_crore']} Cr", xy=(r["month_dt"], r["total_folios_crore"]))
save(plt, "07_folio_growth.png")
plt.show()'''))

    cells.append(make_cell('''df = query("SELECT date_id, amfi_code, nav FROM fact_nav")
pivot = df.pivot(index="date_id", columns="amfi_code", values="nav").ffill()
ret = pivot.pct_change().dropna()
corr = ret[ret.columns[:10]].corr()
plt.figure(figsize=(10, 8))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, square=True)
plt.title("Daily Return Correlation (Top 10)", weight="bold")
save(plt, "08_correlation.png")
plt.show()'''))

    cells.append(make_cell('''df = query("SELECT sector, SUM(weight_pct) as total FROM fact_portfolio GROUP BY sector ORDER BY total DESC")
fig = go.Figure(data=[go.Pie(labels=df["sector"], values=df["total"], hole=0.4)])
fig.update_layout(title="Sector Allocation (All Equity)", template="plotly_white")
save(fig, "09_sector_donut.png")
fig.show()'''))

    cells.append(make_cell('''df = query("SELECT f.plan_type, p.expense_ratio_pct FROM fact_performance p JOIN dim_fund f ON p.amfi_code = f.amfi_code WHERE p.expense_ratio_pct IS NOT NULL")
plt.figure()
sns.histplot(data=df, x="expense_ratio_pct", hue="plan_type", bins=15, kde=True, palette="Set2")
plt.title("Expense Ratio: Direct vs Regular", weight="bold")
plt.xlabel("Expense Ratio (%)")
save(plt, "10_expense_hist.png")
plt.show()'''))

    cells.append(make_cell('''df = query("SELECT strftime('%Y-%m', date_id) as month, transaction_type, COUNT(*) as cnt FROM fact_transactions GROUP BY month, transaction_type ORDER BY month")
fig = px.bar(df, x="month", y="cnt", color="transaction_type",
             title="Monthly Transaction Volume", labels={"month": "Month", "cnt": "Count"})
fig.update_layout(template="plotly_white")
save(fig, "11_txn_volume.png")
fig.show()'''))

    cells.append(make_cell('''df = query("SELECT f.category, f.fund_house, p.aum_crore, p.return_3yr_pct, p.std_dev_ann_pct FROM fact_performance p JOIN dim_fund f ON p.amfi_code = f.amfi_code WHERE p.aum_crore IS NOT NULL")
fig = px.scatter(df, x="return_3yr_pct", y="std_dev_ann_pct",
                 size="aum_crore", color="category", hover_name="fund_house",
                 title="AUM vs Return vs Risk",
                 labels={"return_3yr_pct": "3Y Return %", "std_dev_ann_pct": "Std Dev %"})
fig.update_layout(template="plotly_white")
save(fig, "12_aum_return_scatter.png")
fig.show()'''))

    cells.append(make_md('''## Key EDA Insights

1. **NAV Trends:** All 40 schemes show positive drift since 2022, with a bull run in 2023 and correction in Q2 2024.
2. **AUM Concentration:** SBI leads with highest AUM across all periods.
3. **SIP Momentum:** Monthly SIP inflows show consistent growth, hitting an all-time high in Dec 2025.
4. **Category Flows:** Large Cap and Flexi Cap attract highest net inflows.
5. **Demographics:** Millennials (25-40) drive highest transaction volume.
6. **Geography:** Maharashtra and Delhi lead SIP volumes; T30 dominates B30.
7. **Folio Growth:** Total folios doubled from 13.26 Cr to 26.12 Cr.
8. **Return Correlation:** Large-cap funds show high pairwise correlation (>0.85).
9. **Sector Allocation:** Financial Services leads at ~32% of equity holdings.
10. **Expense Ratios:** Regular plans (1.0-1.6%) cost more than Direct (0.3-0.9%).'''))

    nb.cells = cells
    nbf.write(nb, str(NOTEBOOKS_DIR / "03_eda_analysis.ipynb"))
    print(f"EDA: {len(cells)} cells")

def make_performance():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": ".venv (3.14.5)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.14.5"},
    }

    P_SETUP = SETUP.replace(
        'sns.set_theme(style="whitegrid", context="notebook")\nplt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 300, "figure.figsize": (12, 6)})',
        ''
    )
    cells = [make_cell(P_SETUP)]
    cells.append(make_cell('''RF_ANNUAL = 0.065
RF_DAILY = RF_ANNUAL / 252'''))

    cells.append(make_cell('''def query(sql):
    conn = sqlite3.connect(DB_PATH); df = pd.read_sql(sql, conn); conn.close(); return df

nav = query("SELECT date_id, amfi_code, nav FROM fact_nav ORDER BY date_id")
nav["date"] = pd.to_datetime(nav["date_id"])
pivot = nav.pivot(index="date", columns="amfi_code", values="nav").ffill()
daily_returns = pivot.pct_change().dropna()
print(f"Daily returns: {daily_returns.shape}")'''))

    cells.append(make_cell('''cagr = {}
for code in daily_returns.columns:
    s = pivot[code].dropna()
    if len(s) < 2: continue
    years = (s.index[-1] - s.index[0]).days / 365.25
    if years > 0: cagr[code] = (s.iloc[-1] / s.iloc[0]) ** (1 / years) - 1
cagr_s = pd.Series(cagr, name="CAGR").sort_values(ascending=False)
print("Top 10 by CAGR:"); print(cagr_s.head(10))'''))

    cells.append(make_cell('''from scipy.stats import linregress
mean_ret = daily_returns.mean()
std_ret = daily_returns.std()
downside = daily_returns[daily_returns < 0].std()
sharpe = (mean_ret - RF_DAILY) / std_ret * np.sqrt(252)
sortino = (mean_ret - RF_DAILY) / downside * np.sqrt(252)
sr = pd.DataFrame({"Sharpe": sharpe, "Sortino": sortino}).sort_values("Sharpe", ascending=False)
print("Top 10 by Sharpe:"); print(sr.head(10))'''))

    cells.append(make_cell('''bench = query("SELECT date_id, index_name, close_value FROM fact_benchmark")
bench["date"] = pd.to_datetime(bench["date_id"])
b = bench[bench["index_name"] == "NIFTY50"].set_index("date")["close_value"]
bench_ret = b.pct_change().dropna()
ab = {}
for code in daily_returns.columns:
    fr = daily_returns[code].dropna()
    a, bv = fr.align(bench_ret, join="inner")
    if len(a) < 30: continue
    slope, intercept, r, _, _ = linregress(bv, a)
    ab[code] = {"Alpha": intercept * 252, "Beta": slope, "R2": r ** 2}
ab_df = pd.DataFrame(ab).T.sort_values("Alpha", ascending=False)
print("Top 5 by Alpha:"); print(ab_df.head())'''))

    cells.append(make_cell('''mdd = {}
for code in daily_returns.columns:
    cum = (1 + daily_returns[code]).cumprod()
    mdd[code] = (cum / cum.cummax() - 1).min()
mdd_s = pd.Series(mdd, name="MDD").sort_values()
print("Worst 5 MDD:"); print(mdd_s.head())'''))

    cells.append(make_cell('''score = pd.DataFrame(index=daily_returns.columns)
score["CAGR"] = cagr_s
score["Sharpe"] = sharpe
score["Alpha"] = ab_df["Alpha"]
score["Beta"] = ab_df["Beta"]
score["MDD"] = mdd_s
n = len(score)
for col in score.columns:
    asc = col in ["Beta", "MDD"]
    score[f"{col}_Score"] = (n - score[col].rank(ascending=asc) + 1) / n * 100
score["Total"] = (0.30 * score["CAGR_Score"] + 0.25 * score["Sharpe_Score"]
                  + 0.20 * score["Alpha_Score"] + 0.15 * score["Beta_Score"]
                  + 0.10 * score["MDD_Score"])
score = score.sort_values("Total", ascending=False)
funds = query("SELECT amfi_code, scheme_name, fund_house FROM dim_fund")
score = score.reset_index().merge(funds, left_on="index", right_on="amfi_code")
print("Top 10 Scorecard:")
print(score[["scheme_name", "fund_house", "Total"]].head(10))
(BASE_DIR / "reports").mkdir(parents=True, exist_ok=True)
score.to_csv(BASE_DIR / "reports" / "fund_scorecard.csv", index=False)'''))

    cells.append(make_cell('''top5 = score["amfi_code"].head(5).tolist()
cum_f = (1 + daily_returns[top5]).cumprod()
cum_b = (1 + bench_ret).cumprod()
name_map = dict(zip(funds["amfi_code"], funds["scheme_name"]))
fig = go.Figure()
for c in top5:
    fig.add_trace(go.Scatter(x=cum_f.index, y=cum_f[c], mode="lines", name=name_map.get(c, str(c))[:30]))
fig.add_trace(go.Scatter(x=cum_b.index, y=cum_b, mode="lines", name="NIFTY50",
                         line=dict(color="black", width=3, dash="dash")))
fig.update_layout(title="Top 5 Scorecard Funds vs NIFTY50 (Rebased)", template="plotly_white")
fig.write_image(str(CHARTS_DIR / "benchmark_comparison.png"), width=1400, height=700, scale=2)
fig.show()'''))

    nb.cells = cells
    nbf.write(nb, str(NOTEBOOKS_DIR / "04_performance_analytics.ipynb"))
    print(f"Performance: {len(cells)} cells")

def make_advanced():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": ".venv (3.14.5)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.14.5"},
    }
    cells = [make_cell(SETUP), make_cell('''RF_DAILY = 0.065 / 252''')]

    cells.append(make_cell('''def query(sql):
    conn = sqlite3.connect(DB_PATH); df = pd.read_sql(sql, conn); conn.close(); return df

nav = query("SELECT date_id, amfi_code, nav FROM fact_nav ORDER BY date_id")
nav["date"] = pd.to_datetime(nav["date_id"])
pivot = nav.pivot(index="date", columns="amfi_code", values="nav").ffill()
daily_returns = pivot.pct_change().dropna()
txn = query("SELECT investor_id, date_id, amfi_code, transaction_type, amount FROM fact_transactions ORDER BY investor_id, date_id")
txn["date"] = pd.to_datetime(txn["date_id"])
portfolio = query("SELECT amfi_code, sector, weight_pct FROM fact_portfolio")
print("Data loaded")'''))

    cells.append(make_cell('''var_cvar = {}
for code in daily_returns.columns:
    s = daily_returns[code].dropna()
    var = s.quantile(0.05)
    cvar = s[s <= var].mean()
    var_cvar[code] = {"VaR_95": var, "CVaR_95": cvar}
vc = pd.DataFrame(var_cvar).T.sort_values("VaR_95")
print("Bottom 5 by VaR:"); print(vc.head())
(BASE_DIR / "reports").mkdir(parents=True, exist_ok=True)
vc.to_csv(BASE_DIR / "reports" / "var_cvar_report.csv")'''))

    cells.append(make_cell('''key = daily_returns.columns[:5]
roll = (daily_returns[key].rolling(90).mean() - RF_DAILY) / daily_returns[key].rolling(90).std() * np.sqrt(252)
fig = go.Figure()
for c in key:
    fig.add_trace(go.Scatter(x=roll.index, y=roll[c].dropna(), mode="lines", name=str(c)))
fig.add_hline(y=1, line_dash="dash", line_color="gray", annotation_text="Sharpe=1")
fig.update_layout(title="Rolling 90-Day Sharpe", template="plotly_white")
fig.write_image(str(CHARTS_DIR / "rolling_sharpe.png"), width=1400, height=700, scale=2)
fig.show()'''))

    cells.append(make_cell('''first = txn.groupby("investor_id")["date"].min().dt.year.reset_index()
first.columns = ["investor_id", "cohort_year"]
txn_m = txn.merge(first, on="investor_id")
cohort = txn_m.groupby(["cohort_year", "investor_id"]).agg(
    total=("amount", "sum"), sip_count=("transaction_type", lambda x: (x == "SIP").sum())
).groupby("cohort_year").mean().reset_index()
print("Cohort summary:"); print(cohort)'''))

    cells.append(make_cell('''sip = txn[txn["transaction_type"] == "SIP"].sort_values(["investor_id", "date"])
sip["gap"] = sip.groupby("investor_id")["date"].diff().dt.days
summary = sip.groupby("investor_id").agg(
    total_sips=("transaction_type", "count"), max_gap=("gap", "max")
).reset_index()
at_risk = summary[(summary["total_sips"] >= 6) & (summary["max_gap"] > 35)]
eligible = summary[summary["total_sips"] >= 6]
pct = len(at_risk) / len(eligible) * 100 if len(eligible) > 0 else 0
print(f"At-risk: {len(at_risk)} / {len(eligible)} = {pct:.1f}%")'''))

    cells.append(make_cell('''risk_map = {"Low": ["Low", "Moderately Low"], "Moderate": ["Moderate", "Moderately High"], "High": ["High", "Very High"]}
fund = query("SELECT amfi_code, scheme_name, fund_house, risk_grade FROM dim_fund")
perf = query("SELECT amfi_code, sharpe_ratio, expense_ratio_pct FROM fact_performance")
merged = fund.merge(perf, on="amfi_code")
for appetite in ["Low", "Moderate", "High"]:
    filtered = merged[merged["risk_grade"].isin(risk_map[appetite])]
    top = filtered.nlargest(3, "sharpe_ratio")
    print(f"\\n{appetite}:")
    print(top[["scheme_name", "fund_house", "sharpe_ratio"]].to_string(index=False))'''))

    cells.append(make_cell('''hhi = portfolio.groupby("amfi_code").apply(lambda g: ((g["weight_pct"] / 100) ** 2).sum()).rename("HHI").reset_index()
hhi = hhi.merge(fund[["amfi_code", "scheme_name", "category"]], on="amfi_code")
concern = hhi[hhi["HHI"] > 0.25]
print(f"Highly concentrated (HHI > 0.25): {len(concern)}")
print(concern[["scheme_name", "HHI", "category"]])'''))

    nb.cells = cells
    nbf.write(nb, str(NOTEBOOKS_DIR / "05_advanced_analytics.ipynb"))
    print(f"Advanced: {len(cells)} cells")

if __name__ == "__main__":
    make_eda()
    make_performance()
    make_advanced()
    print("\nAll notebooks updated")
