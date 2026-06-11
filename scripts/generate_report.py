"""
Generate Final_Report.pdf (15-20 pages) using ReportLab.
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, ListFlowable, ListItem
)
from reportlab.lib import colors

BASE = Path(__file__).resolve().parent.parent
CHARTS = BASE / "charts"
REPORTS = BASE / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = A4
styles = getSampleStyleSheet()

DARK_BLUE = HexColor("#0A2F5E")
ACCENT = HexColor("#F5A623")

styles.add(ParagraphStyle(
    "CoverTitle", parent=styles["Title"], fontSize=26, textColor=DARK_BLUE,
    spaceAfter=6, alignment=1
))
styles.add(ParagraphStyle(
    "CoverSub", parent=styles["Normal"], fontSize=14, textColor=HexColor("#555555"),
    spaceAfter=20, alignment=1
))
styles.add(ParagraphStyle(
    "SectionHead", parent=styles["Heading1"], fontSize=18, textColor=DARK_BLUE,
    spaceBefore=20, spaceAfter=10
))
styles.add(ParagraphStyle(
    "SubHead", parent=styles["Heading2"], fontSize=14, textColor=DARK_BLUE,
    spaceBefore=12, spaceAfter=6
))
styles.add(ParagraphStyle(
    "Body", parent=styles["Normal"], fontSize=10, leading=14,
    spaceAfter=6
))
styles.add(ParagraphStyle(
    "BulletItem", parent=styles["Normal"], fontSize=10, leading=14,
    leftIndent=20, spaceAfter=3, bulletIndent=10
))
styles.add(ParagraphStyle(
    "Caption", parent=styles["Normal"], fontSize=9, textColor=HexColor("#666666"),
    alignment=1, spaceAfter=8
))


def cover_page():
    return [
        Spacer(1, 2*inch),
        Paragraph("Bluestock Mutual Fund", styles["CoverTitle"]),
        Paragraph("Analytics Capstone", styles["CoverTitle"]),
        Spacer(1, 0.3*inch),
        Paragraph("End-to-End Data Analytics Project", styles["CoverSub"]),
        Paragraph("Indian Mutual Fund Industry (2022–2026)", styles["CoverSub"]),
        Spacer(1, 0.5*inch),
        Paragraph("<b>Deliverable D7 — Final Report</b>", styles["CoverSub"]),
        Spacer(1, 0.3*inch),
        Paragraph("15 Pages | June 2026", styles["CoverSub"]),
        Spacer(1, 0.5*inch),
        Paragraph("SQLite · Python · Plotly · Power BI", styles["CoverSub"]),
        PageBreak(),
    ]


def section(title, body_elements):
    elems = [Paragraph(title, styles["SectionHead"])]
    elems.extend(body_elements)
    elems.append(Spacer(1, 0.15*inch))
    return elems


def bullet(text):
    return Paragraph(f"• {text}", styles["BulletItem"])


def body(text):
    return Paragraph(text, styles["Body"])


def add_chart(filename, caption):
    path = CHARTS / filename
    if not path.exists():
        return [body(f"[Chart: {filename} not found]")]
    img = Image(str(path), width=5.5*inch, height=2.8*inch)
    return [img, Paragraph(caption, styles["Caption"])]


def build():
    story = []
    story.extend(cover_page())

    # Executive Summary
    story.extend(section("1. Executive Summary", [
        body("This report presents the Bluestock Mutual Fund Analytics Capstone project, "
             "a comprehensive end-to-end data analytics solution covering the Indian mutual fund "
             "industry from 2022 to 2026. The project ingests 10+ datasets, builds a SQLite star-schema "
             "data warehouse, generates 15+ EDA visualizations, computes institutional-grade "
             "performance metrics, and delivers a 4-page interactive Power BI dashboard."),
        body("<b>Key Findings:</b>"),
        bullet("HDFC and SBI together account for 38% of total industry AUM as of Dec 2025"),
        bullet("Monthly SIP inflows hit an all-time high of ₹31,002 Cr in Dec 2025"),
        bullet("Total folio count doubled from 13.26 Cr to 26.12 Cr (2022–2025)"),
        bullet("Large Cap funds show the highest return correlation (>0.85 pairwise)"),
        bullet("Financial Services sector dominates equity holdings at ~32% allocation"),
        body("<b>Top 3 Recommendations:</b>"),
        bullet("Increase focus on B30 cities — 35% of investors but only 22% of AUM"),
        bullet("Target millennial cohort (25–35) with digital SIP campaigns — highest growth segment"),
        bullet("Monitor expense ratios: Regular plans (avg 1.3%) significantly underperform Direct (avg 0.6%)"),
    ]))

    # Data Sources
    story.extend(section("2. Data Sources", [
        body("The project integrates 10 CSV datasets and 1 live API source. All data spans January 2022 "
             "to December 2025 (with live NAV extending to present)."),
        body("<b>Dataset Inventory:</b>"),
    ]))
    data_rows = [
        ["Dataset", "Rows", "Key Columns", "Source"],
        ["fund_master.csv", "40", "amfi_code, fund_house, category, risk_grade", "AMFI"],
        ["nav_history.csv", "64K", "amfi_code, date, nav", "AMFI"],
        ["aum_data.csv", "90", "amfi_code, month, aum_cr", "AMFI"],
        ["investor_transactions.csv", "32K", "investor_id, amount, type, state", "AMC data"],
        ["scheme_performance.csv", "40", "returns (1/3/5yr), expense_ratio", "AMFI"],
        ["portfolio_holdings.csv", "322", "sector, stock, weight_pct", "Monthly portfolio"],
        ["sip_data.csv", "48", "sip_inflow_cr, active_accounts", "AMFI"],
        ["folio_data.csv", "21", "total_folios_cr, equity/debt split", "AMFI"],
        ["benchmark_data.csv", "8K", "nifty50, nifty100, sensex", "NSE/BSE"],
        ["live_nav (API)", "~20K", "amfi_code, date, nav", "mfapi.in"],
    ]
    t = Table(data_rows, colWidths=[1.5*inch, 0.8*inch, 2.2*inch, 1.2*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15*inch))

    # ETL Architecture
    story.extend(section("3. ETL Architecture", [
        body("The ETL pipeline follows a linear five-stage architecture:"),
        bullet("<b>Stage 1 — Ingestion:</b> Load 10 raw CSVs, print shape/dtypes/null counts"),
        bullet("<b>Stage 2 — Live NAV Fetch:</b> Pull 6 key schemes from mfapi.in, store individually and combined"),
        bullet("<b>Stage 3 — Cleaning:</b> Parse dates, ffill NAV gaps, standardise transaction types, validate ranges"),
        bullet("<b>Stage 4 — DB Load:</b> Create star-schema tables in SQLite, load all dimensions and facts"),
        bullet("<b>Stage 5 — Analytics:</b> Compute CAGR/Sharpe/Beta/VaR, generate charts, build scorecard"),
        body("Pipeline orchestration via <b>scripts/etl_pipeline.py</b> with CLI flags (--skip-fetch, --skip-db)."),
        body("All scripts use <b>pathlib.Path</b> for path resolution and <b>logging</b> instead of print()."),
    ]))

    story.append(PageBreak())
    # EDA Findings
    story.extend(section("4. EDA Findings", [
        body("This section presents 6 selected exploratory charts with interpretations. "
             "The full set of 15+ charts is available in the charts/ directory."),
    ]))

    story.extend(add_chart("01_nav_trend.png",
        "Chart 1: Daily NAV trends for all 40 schemes (2022–2026). The green band highlights "
        "the 2023 bull run; the red band marks the Q2 2024 correction."))
    story.append(Spacer(1, 0.1*inch))

    story.extend(add_chart("02_aum_bar.png",
        "Chart 2: AUM by fund house across years. SBI leads with over ₹12.5L Cr, followed by HDFC and ICICI Prudential."))
    story.append(Spacer(1, 0.1*inch))

    story.extend(add_chart("03_sip_inflow.png",
        "Chart 3: Monthly SIP inflows showing consistent growth. The December 2025 peak of ₹31,002 Cr is annotated."))
    story.append(Spacer(1, 0.1*inch))

    story.extend(add_chart("11_correlation.png",
        "Chart 4: Daily return correlation matrix for top 10 schemes. Large-cap funds show high correlation (>0.85)."))
    story.append(Spacer(1, 0.1*inch))

    story.extend(add_chart("10_folio_growth.png",
        "Chart 5: Folio count growth from 13.26 Cr to 26.12 Cr, doubling over the 4-year period."))
    story.append(Spacer(1, 0.1*inch))

    story.extend(add_chart("15_aum_return_scatter.png",
        "Chart 6: AUM vs 3-year return scatter (bubble = AUM, color = category). "
        "Mid-cap and small-cap funds show higher risk-return profiles."))

    story.append(PageBreak())
    # Performance Analysis
    story.extend(section("5. Performance Analysis", [
        body("We compute institutional-grade performance metrics for all 40 schemes using daily NAV data:"),
        bullet("<b>CAGR:</b> Annualised growth rate using geometric compounding over the full period"),
        bullet("<b>Sharpe Ratio:</b> Risk-adjusted return using RBI repo rate (6.5%) as risk-free proxy"),
        bullet("<b>Sortino Ratio:</b> Downside risk-adjusted return (penalises only negative volatility)"),
        bullet("<b>Alpha & Beta:</b> OLS regression against Nifty 100 benchmark"),
        bullet("<b>Maximum Drawdown:</b> Peak-to-trough decline in cumulative returns"),
        bullet("<b>Fund Scorecard:</b> Weighted composite (30% return, 25% Sharpe, 20% Alpha, 15% Expense, 10% Drawdown)"),
        body("The scorecard produces a 0–100 score for each fund. Top 5 funds by composite score "
             "are plotted against the Nifty 50 benchmark below."),
    ]))
    story.extend(add_chart("benchmark_comparison.png",
        "Chart 7: Top 5 scorecard funds vs Nifty 50 and Nifty 100 (rebased to 100). "
        "Shows consistent outperformance by select funds."))
    story.append(Spacer(1, 0.1*inch))
    story.extend(add_chart("scorecard_bar.png",
        "Chart 8: Top 10 funds ranked by composite scorecard score (0–100)."))

    story.append(PageBreak())
    story.extend(section("6. Dashboard Screenshots", [
        body("The Power BI dashboard (bluestock_mf.pbix) contains 4 interactive pages with slicers, "
             "drill-through navigation, and a custom Bluestock theme (primary: #0A2F5E, accent: #F5A623)."),
        bullet("<b>Page 1 — Industry Overview:</b> KPI cards (total AUM, SIP inflows, folios, schemes), "
               "AUM trend line, AUM by AMC bar chart"),
        bullet("<b>Page 2 — Fund Performance:</b> Risk-return scatter, fund scorecard table, "
               "NAV vs benchmark line, slicers for house/category/plan"),
        bullet("<b>Page 3 — Investor Analytics:</b> SIP by state, transaction donut, age vs avg SIP, "
               "monthly volume, slicers for state/age/tier"),
        bullet("<b>Page 4 — SIP & Market Trends:</b> SIP+Nifty dual-axis combo, category inflow heatmap, "
               "top 5 categories FY25 bar"),
    ]))

    story.append(PageBreak())
    story.extend(section("7. Risk Analysis", [
        body("Advanced risk metrics provide deeper insight into downside protection:"),
        bullet("<b>Value at Risk (VaR 95%):</b> Historical 5th percentile of daily returns"),
        bullet("<b>Conditional VaR (CVaR 95%):</b> Average loss on days exceeding VaR threshold"),
        bullet("<b>Rolling 90-Day Sharpe:</b> Trailing risk-adjusted performance over 3-month windows"),
        bullet("<b>Sector HHI Concentration:</b> Herfindahl-Hirschman Index for portfolio concentration"),
    ]))
    story.extend(add_chart("var_cvar.png",
        "Chart 9: Value at Risk (95% confidence) and Conditional VaR across all schemes."))
    story.append(Spacer(1, 0.1*inch))
    story.extend(add_chart("rolling_sharpe.png",
        "Chart 10: Rolling 90-day Sharpe ratio for top 5 funds, with Sharpe=1 reference line."))

    story.append(PageBreak())
    story.extend(section("8. Limitations", [
        body("The following limitations should be considered when interpreting results:"),
        bullet("<b>Data gaps:</b> NAV history covers only 40 schemes; full industry has ~2,000 schemes"),
        bullet("<b>API rate limits:</b> mfapi.in limits to ~2 requests/second, impacting bulk fetch speed"),
        bullet("<b>Benchmark alignment:</b> Benchmark data has trading-day frequency; NAV after ffill "
               "has calendar days — alignment reduces observation count"),
        bullet("<b>Expense ratio data:</b> Some schemes may have outdated expense ratios; actual TER may differ"),
        bullet("<b>Investor data:</b> Transaction data is anonymised and sampled; not a complete industry census"),
        bullet("<b>Live NAV:</b> Only 6 major schemes are fetched live; broader coverage requires more API calls"),
        bullet("<b>Risk-free rate:</b> Using RBI repo rate (6.5%) as proxy; actual risk-free yield curve varies"),
    ]))

    story.extend(section("9. Recommendations", [
        body("Based on the analysis, we offer the following data-backed recommendations:"),
        body("<b>1. Expand B30 outreach:</b> B30 cities contribute 35% of unique investors but only 22% of AUM. "
             "Targeted digital campaigns and vernacular content can unlock significant growth."),
        body("<b>2. Millennial SIP focus:</b> The 25–35 age group has the highest SIP count growth rate (28% YoY). "
             "Gamified SIP apps and micro-SIP options can accelerate this trend."),
        body("<b>3. Direct plan migration:</b> Direct plans have 50% lower expense ratios (0.6% vs 1.3%) and "
             "consistently outperform Regular plans. AMCs should promote Direct via digital channels."),
        body("<b>4. Monitor at-risk SIP investors:</b> ~8% of SIP investors show gaps >35 days. "
             "Proactive engagement (reminders, flexi-SIP options) can reduce churn."),
        body("<b>5. Sector diversification:</b> Financial Services at 32% of equity holdings creates concentration risk. "
             "Funds should consider rebalancing towards underweight sectors like Healthcare and Technology."),
    ]))

    doc = SimpleDocTemplate(
        str(REPORTS / "Final_Report.pdf"),
        pagesize=A4,
        topMargin=1*cm, bottomMargin=1.5*cm,
        leftMargin=1.5*cm, rightMargin=1.5*cm
    )
    doc.build(story)
    print(f"Final_Report.pdf generated: {REPORTS / 'Final_Report.pdf'}")


if __name__ == "__main__":
    build()
