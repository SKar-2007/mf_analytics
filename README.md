# Bluestock Mutual Fund Analytics Capstone

## Overview
End-to-end data analytics project covering Indian mutual fund industry data (2022–2026). Ingests 10+ datasets, builds a SQLite star-schema warehouse, delivers 15+ EDA charts, institutional performance metrics, and a 4-page Power BI dashboard.

## Setup
```bash
git clone https://github.com/<username>/bluestock_mf_capstone.git
cd bluestock_mf_capstone
pip install -r requirements.txt
```

## Run the Full ETL Pipeline
```bash
python scripts/etl_pipeline.py
```

## Open Notebooks (in order)
```bash
jupyter notebook notebooks/
# Run: 01_data_ingestion → 02_data_cleaning → 03_eda_analysis
#      → 04_performance_analytics → 05_advanced_analytics
```

## Fund Recommender
```bash
python scripts/recommender.py
# Prompts for risk appetite: Low / Moderate / High
```

## Dataset Descriptions
| File | Description | Rows |
|------|-------------|------|
| fund_master.csv | AMFI scheme master — codes, houses, categories | ~2,000 |
| nav_history.csv | Daily NAV per scheme 2022–2026 | ~1.5M |
| aum_data.csv | Monthly AUM by fund house | ~300 |
| investor_transactions.csv | Investor SIP/Lumpsum/Redemption logs | ~32K |
| scheme_performance.csv | Returns, expense ratios, risk metrics | ~40 |
| portfolio_holdings.csv | Sector/stock weight breakdown | ~500 |
| sip_data.csv | Monthly SIP inflow aggregates | ~48 |
| folio_data.csv | Monthly folio counts | ~24 |
| benchmark_data.csv | Nifty 50, Nifty 100, Sensex daily closes | ~8K |

## Dashboard
Open `dashboard/bluestock_mf.pbix` in Power BI Desktop.

## Key Results
- Top fund by Scorecard: 
- Industry AUM Dec 2025: ₹81L Cr
- SIP ATH: ₹31,002 Cr (Dec 2025)
- Folio count: 26.12 Cr

## Project Structure
```
bluestock_mf_capstone/
├── data/raw/                  # Source CSVs + live NAV files
├── data/processed/            # Cleaned CSVs (pipeline output)
├── data/db/                   # SQLite database (gitignored)
├── notebooks/                 # 5 Jupyter notebooks (ingestion → advanced)
├── scripts/                   # Python scripts (ETL, metrics, recommender)
├── sql/                       # Schema DDL + 10 analytical queries
├── dashboard/                 # Power BI report + screenshots
├── reports/                   # Final report PDF + presentation
├── charts/                    # Exported chart PNGs (2x scale)
└── config/                    # Centralized YAML configuration
```
