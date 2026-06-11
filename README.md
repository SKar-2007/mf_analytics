# Bluestock Mutual Fund Analytics Capstone

## Overview
End-to-end data analytics project covering Indian mutual fund industry data (2022–2026). Ingests 10+ datasets, builds a SQLite star-schema warehouse, delivers 15+ EDA charts, institutional performance metrics, and advanced risk analytics.

## Project Structure
```
├── data/
│   ├── raw/              # Source CSVs + live NAV files
│   ├── processed/        # Cleaned CSVs (pipeline output)
│   └── db/               # SQLite database (bluestock_mf.db)
├── scripts/
│   ├── data_cleaning.py        # Cleans all raw CSVs
│   ├── load_database.py        # Loads cleaned data to SQLite
│   ├── live_nav_fetch.py       # Fetches live NAV from MFAPI
│   ├── performance_analytics.py # CAGR, Sharpe, Alpha/Beta, MDD
│   ├── recommender.py          # Risk-based fund recommender
│   ├── generate_eda_charts.py       # 15 EDA charts
│   ├── generate_performance_charts.py # Scorecard + benchmark
│   └── generate_advanced_charts.py   # VaR, rolling Sharpe, cohort, HHI
├── sql/
│   ├── schema.sql        # DDL for all 11 tables
│   └── queries.sql       # 10 analytical queries
├── notebooks/
│   ├── 03_eda_analysis.ipynb
│   └── 04_performance_analytics.ipynb
├── charts/               # All exported chart PNGs (21 charts)
├── dashboard/            # Power BI report
├── reports/              # Final report + presentation
├── run_pipeline.py       # Master execution script
├── data_ingestion.py     # Dataset inspection
├── db_load.py            # Alternative DB loader
└── data_dictionary.md    # Column-level documentation
```

## Setup
```bash
git clone https://github.com/<username>/bluestock-mf-capstone.git
cd bluestock-mf-capstone
pip install -r requirements.txt
```

## Run the Full Pipeline
```bash
python run_pipeline.py
```

## Generate Charts
```bash
python scripts/generate_eda_charts.py
python scripts/generate_performance_charts.py
python scripts/generate_advanced_charts.py
```

## Open Notebooks
```bash
jupyter notebook notebooks/
```

## Database Schema
Star-schema with 11 tables:
- **Dimensions:** dim_fund (40 schemes), dim_date (2,557 days)
- **Facts:** fact_nav (64K rows), fact_transactions (32K), fact_performance (40), fact_aum (90), fact_sip (48), fact_folio (21), fact_benchmark (8K), fact_portfolio (322), fact_category_inflow (144)

## Key Results
- Top fund by Scorecard: generated in `fund_scorecard.csv`
- Industry AUM tracked across 10 fund houses (2022–2025)
- SIP ATH: ₹31,002 Cr (Dec 2025)
- VaR/CVaR computed for all 40 schemes
- Investor cohort analysis across demographic segments

## Deliverables
| Phase | Outputs |
|-------|---------|
| 1 — Ingestion | `data_ingestion.py`, `live_nav_fetch.py`, `requirements.txt` |
| 2 — Cleaning + DB | 10 clean CSVs, `bluestock_mf.db`, `sql/schema.sql`, `sql/queries.sql`, `data_dictionary.md` |
| 3 — EDA | 15 chart PNGs in `charts/` |
| 4 — Performance | `fund_scorecard.csv`, `alpha_beta.csv`, benchmark comparison chart |
| 5 — Dashboard | `dashboard/bluestock_mf_dashboard.pbix` |
| 6 — Advanced | `var_cvar_report.csv`, rolling Sharpe, cohort, HHI charts |
| 7 — Final | `run_pipeline.py`, `README.md`, full chart set |
