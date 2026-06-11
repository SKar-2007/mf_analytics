"""
Generate Presentation.pptx (12 slides) using python-pptx.
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

BASE = Path(__file__).resolve().parent.parent
CHARTS = BASE / "charts"
REPORTS = BASE / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

DARK_BLUE = RGBColor(0x0A, 0x2F, 0x5E)
ACCENT = RGBColor(0xF5, 0xA6, 0x23)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY = RGBColor(0x66, 0x66, 0x66)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)


def add_bg(slide, color=DARK_BLUE):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_title_box(slide, text, left=0.5, top=0.3, width=12, height=1, size=36, color=WHITE):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = True
    p.font.color.rgb = color
    return txBox


def add_text_box(slide, text, left=0.5, top=1.5, width=12, height=5, size=18, color=WHITE):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, line in enumerate(text.split("\n")):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = line
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.space_after = Pt(8)
    return txBox


def add_chart_slide(slide, chart_name, left=0.5, top=1.8, width=12, height=5.2):
    path = CHARTS / chart_name
    if path.exists():
        slide.shapes.add_picture(str(path), Inches(left), Inches(top),
                                 width=Inches(width), height=Inches(height))


# Slide 1: Title
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_box(slide, "Bluestock Mutual Fund", left=1, top=2, size=44)
add_title_box(slide, "Analytics Capstone", left=1, top=2.8, size=36)
add_text_box(slide, "End-to-End Data Analytics Project\nSQLite · Python · Plotly · Power BI\nJune 2026",
             left=1, top=4, size=20, color=ACCENT)

# Slide 2: Problem & Objective
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_title_box(slide, "Problem & Objective", color=DARK_BLUE)
lines = [
    "Problem: Mutual fund data is fragmented across multiple sources with inconsistent formats,",
    "making it difficult for investors and AMCs to get a unified view of performance and risk.",
    "",
    "7 Objectives:",
    "1. Ingest and clean 10+ MF datasets + live API data",
    "2. Build a SQLite star-schema relational database",
    "3. Produce 15+ EDA charts with annotated insights",
    "4. Compute institutional-grade performance metrics (CAGR, Sharpe, Alpha, Beta, MDD)",
    "5. Deliver a 4-page interactive Power BI dashboard",
    "6. Run advanced risk analytics (VaR, CVaR, cohort, recommender)",
    "7. Package into professional report + presentation"
]
add_text_box(slide, "\n".join(lines), size=16, color=DARK_BLUE)

# Slide 3: Data Sources
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_title_box(slide, "Data Sources", color=DARK_BLUE)
lines = [
    "Dataset                    | Format  | Rows     | Period",
    "fund_master.csv            | CSV     | 40       | 2022-2026",
    "nav_history.csv            | CSV     | 64K      | 2022-2026",
    "aum_data.csv               | CSV     | 90       | 2022-2025",
    "investor_transactions.csv  | CSV     | 32K      | 2022-2025",
    "scheme_performance.csv     | CSV     | 40       | Snapshot",
    "portfolio_holdings.csv     | CSV     | 322      | Snapshot",
    "sip_data.csv               | CSV     | 48       | 2022-2025",
    "folio_data.csv             | CSV     | 21       | 2022-2025",
    "benchmark_data.csv         | CSV     | 8K       | 2022-2026",
    "live_nav (API)             | JSON    | ~20K     | Daily live",
]
add_text_box(slide, "\n".join(lines), size=14, color=DARK_BLUE)

# Slide 4: Architecture
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_title_box(slide, "Technical Architecture", color=DARK_BLUE)
lines = [
    "Raw CSVs → data_cleaning.py → Clean CSVs → load_database.py → SQLite DB",
    "",
    "                     ┌─────────────────┐",
    " 10 Raw CSVs ──────→│  Data Cleaning   │──────→ 10 Clean CSVs",
    "                     └─────────────────┘",
    "                              │",
    "                     ┌─────────────────┐",
    "                     │  SQLite Loader   │──────→ bluestock_mf.db",
    "                     └─────────────────┘",
    "                              │",
    "               ┌──────────────┼──────────────┐",
    "               ▼              ▼              ▼",
    "      EDA Notebooks   Performance    Power BI",
    "      (15+ charts)    Metrics       Dashboard",
    "                      (CAGR/Sharpe) (4 pages)",
]
add_text_box(slide, "\n".join(lines), size=14, color=DARK_BLUE)

# Slide 5: EDA Highlights I
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_title_box(slide, "EDA Highlights I", color=DARK_BLUE)
add_chart_slide(slide, "01_nav_trend.png", left=0.3, top=1.5, width=6.2, height=3.5)
add_chart_slide(slide, "02_aum_bar.png", left=6.8, top=1.5, width=6.2, height=3.5)
add_text_box(slide, "NAV Trends (left): All 40 schemes show positive drift. 2023 bull run and 2024 correction highlighted.\nAUM by Fund House (right): SBI leads with ₹12.5L Cr — highest by any single AMC.",
             left=0.5, top=5.2, size=13, color=DARK_BLUE)

# Slide 6: EDA Highlights II
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_title_box(slide, "EDA Highlights II", color=DARK_BLUE)
add_chart_slide(slide, "03_sip_inflow.png", left=0.3, top=1.5, width=6.2, height=3.5)
add_chart_slide(slide, "10_folio_growth.png", left=6.8, top=1.5, width=6.2, height=3.5)
add_text_box(slide, "SIP Inflows (left): All-time high of ₹31,002 Cr in Dec 2025.\nFolio Growth (right): Doubled from 13.26 Cr to 26.12 Cr (2022-2025).",
             left=0.5, top=5.2, size=13, color=DARK_BLUE)

# Slide 7: Performance Metrics I
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_title_box(slide, "Performance Metrics I", color=DARK_BLUE)
add_chart_slide(slide, "scorecard_bar.png", left=0.3, top=1.5, width=6.2, height=3.5)
add_text_box(slide, "Fund Scorecard: Weighted composite (30% CAGR, 25% Sharpe, 20% Alpha, 15% Expense, 10% Drawdown).\nTop funds score >80/100. Scorecard saved to reports/fund_scorecard.csv.",
             left=0.5, top=5.2, size=13, color=DARK_BLUE)

# Slide 8: Performance Metrics II
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_title_box(slide, "Performance Metrics II", color=DARK_BLUE)
add_chart_slide(slide, "alpha_beta_scatter.png", left=0.3, top=1.5, width=6.2, height=3.5)
add_chart_slide(slide, "benchmark_comparison.png", left=6.8, top=1.5, width=6.2, height=3.5)
add_text_box(slide, "Alpha-Beta Scatter (left): Bubble size = AUM, color = 3Y return.\nBenchmark Comparison (right): Top 5 scorecard funds vs Nifty 50.",
             left=0.5, top=5.2, size=13, color=DARK_BLUE)

# Slide 9: Dashboard Screenshot I
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_title_box(slide, "Dashboard — Pages 1 & 2", color=DARK_BLUE)
add_text_box(slide, "Page 1: Industry Overview — KPI cards, AUM trend, AUM by AMC\nPage 2: Fund Performance — Risk-return scatter, scorecard table, NAV vs benchmark",
             left=0.5, top=1.5, size=16, color=DARK_BLUE)

# Slide 10: Dashboard Screenshot II
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_title_box(slide, "Dashboard — Pages 3 & 4", color=DARK_BLUE)
add_text_box(slide, "Page 3: Investor Analytics — SIP by state, transaction donut, age analysis\nPage 4: SIP & Market Trends — SIP+Nifty dual-axis, category heatmap",
             left=0.5, top=1.5, size=16, color=DARK_BLUE)

# Slide 11: Key Findings
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_title_box(slide, "Key Findings", color=DARK_BLUE)
lines = [
    "1. HDFC and SBI together control 38% of industry AUM",
    "",
    "2. Monthly SIP inflows grew 180% from ₹11K Cr (2022) to ₹31K Cr (2025)",
    "",
    "3. Folio count doubled from 13.26 Cr to 26.12 Cr in 4 years",
    "",
    "4. Large Cap funds show >0.85 pairwise return correlation",
    "",
    "5. Direct plans outperform Regular plans by 1.2% annually on average",
    "",
    "6. B30 cities represent 35% of investors but only 22% of AUM",
    "",
    "7. Financial Services dominates equity sector allocation at 32%"
]
add_text_box(slide, "\n".join(lines), size=16, color=DARK_BLUE)

# Slide 12: Thank You
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_box(slide, "Thank You", left=3, top=2, size=48)
add_text_box(slide, "Bluestock Mutual Fund Analytics Capstone\n\nGitHub: github.com/<username>/bluestock_mf_capstone\n\nQuestions?", left=3, top=3.5, size=20, color=ACCENT)

prs.save(str(REPORTS / "Presentation.pptx"))
print(f"Presentation.pptx generated: {REPORTS / 'Presentation.pptx'}")
