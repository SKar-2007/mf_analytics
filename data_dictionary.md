# Data Dictionary — Bluestock MF Capstone

## dim_fund
| Column | Data Type | Business Definition | Source |
|--------|-----------|---------------------|--------|
| amfi_code | INTEGER | AMFI-assigned 6-digit scheme identifier | fund_master.csv |
| fund_house | TEXT | Asset Management Company name | fund_master.csv |
| scheme_name | TEXT | Full scheme name with plan suffix | fund_master.csv |
| category | TEXT | Broad asset class (Equity, Debt, Hybrid, Solution-Oriented) | fund_master.csv |
| sub_category | TEXT | Market cap / strategy type (Large Cap, Mid Cap, etc.) | fund_master.csv |
| plan_type | TEXT | Direct or Regular plan | fund_master.csv |
| risk_grade | TEXT | Risk assessment (Low, Moderate, High, Very High) | fund_master.csv |
| launch_date | TEXT | Scheme launch date | fund_master.csv |
| benchmark | TEXT | Benchmark index name | fund_master.csv |
| expense_ratio_pct | REAL | Annual expense ratio as percentage | fund_master.csv |
| fund_manager | TEXT | Name of fund manager | fund_master.csv |

## dim_date
| Column | Data Type | Business Definition | Source |
|--------|-----------|---------------------|--------|
| date_id | TEXT | Calendar date in YYYY-MM-DD format | Generated |
| calendar_year | INTEGER | Year component | Generated |
| calendar_month | INTEGER | Month number (1-12) | Generated |
| month_name | TEXT | Full month name | Generated |
| day_of_week | INTEGER | Day of week (0=Monday, 6=Sunday) | Generated |
| is_weekend | INTEGER | Flag: 1 if Saturday/Sunday, else 0 | Generated |

## fact_nav
| Column | Data Type | Business Definition | Source |
|--------|-----------|---------------------|--------|
| nav_id | INTEGER | Surrogate primary key | Auto-generated |
| amfi_code | INTEGER | Scheme identifier (FK to dim_fund) | nav_history.csv |
| date_id | TEXT | Valuation date (FK to dim_date) | nav_history.csv |
| nav | REAL | Net Asset Value in INR per unit | nav_history.csv |

## fact_transactions
| Column | Data Type | Business Definition | Source |
|--------|-----------|---------------------|--------|
| txn_id | INTEGER | Surrogate primary key | Auto-generated |
| investor_id | TEXT | Anonymized investor identifier | investor_transactions.csv |
| amfi_code | INTEGER | Scheme identifier (FK to dim_fund) | investor_transactions.csv |
| date_id | TEXT | Transaction date (FK to dim_date) | investor_transactions.csv |
| transaction_type | TEXT | SIP, LUMPSUM, or REDEMPTION | investor_transactions.csv |
| amount | REAL | Transaction amount in INR | investor_transactions.csv |
| state | TEXT | Investor state | investor_transactions.csv |
| city | TEXT | Investor city | investor_transactions.csv |
| city_tier | TEXT | T30 (top 30 cities) or B30 (beyond 30) | investor_transactions.csv |
| age_group | TEXT | Age bracket of investor | investor_transactions.csv |
| gender | TEXT | Male / Female / Other | investor_transactions.csv |
| kyc_status | TEXT | VERIFIED, PENDING, or FAILED | investor_transactions.csv |

## fact_performance
| Column | Data Type | Business Definition | Source |
|--------|-----------|---------------------|--------|
| perf_id | INTEGER | Surrogate primary key | Auto-generated |
| amfi_code | INTEGER | Scheme identifier (FK to dim_fund) | scheme_performance.csv |
| return_1yr_pct | REAL | 1-year return percentage | scheme_performance.csv |
| return_3yr_pct | REAL | 3-year annualized return percentage | scheme_performance.csv |
| return_5yr_pct | REAL | 5-year annualized return percentage | scheme_performance.csv |
| expense_ratio_pct | REAL | Annual expense ratio; range 0.1-2.5% | scheme_performance.csv |
| sharpe_ratio | REAL | Risk-adjusted return metric | scheme_performance.csv |
| sortino_ratio | REAL | Downside risk-adjusted return | scheme_performance.csv |
| alpha | REAL | Excess return vs benchmark | scheme_performance.csv |
| beta | REAL | Systematic risk vs benchmark | scheme_performance.csv |
| std_dev_ann_pct | REAL | Annualized standard deviation of returns | scheme_performance.csv |
| max_drawdown_pct | REAL | Maximum peak-to-trough decline | scheme_performance.csv |
| aum_crore | REAL | AUM in INR crores | scheme_performance.csv |
| risk_grade | TEXT | Risk grade assigned by AMC | scheme_performance.csv |

## fact_aum
| Column | Data Type | Business Definition | Source |
|--------|-----------|---------------------|--------|
| aum_id | INTEGER | Surrogate primary key | Auto-generated |
| fund_house | TEXT | AMC name | aum_data.csv |
| date_id | TEXT | Month-end date (FK to dim_date) | aum_data.csv |
| aum_lakh_crore | REAL | AUM in lakh crores | aum_data.csv |
| aum_crore | REAL | AUM in crores | aum_data.csv |
| num_schemes | INTEGER | Number of schemes under AMC | aum_data.csv |

## fact_sip
| Column | Data Type | Business Definition | Source |
|--------|-----------|---------------------|--------|
| sip_id | INTEGER | Surrogate primary key | Auto-generated |
| month | TEXT | Month in YYYY-MM format | sip_data.csv |
| sip_inflow_crore | REAL | Total SIP inflow in INR crores | sip_data.csv |
| active_sip_accounts_crore | REAL | Active SIP accounts in crores | sip_data.csv |
| new_sip_accounts_lakh | REAL | New SIP accounts opened in lakhs | sip_data.csv |
| sip_aum_lakh_crore | REAL | SIP AUM in lakh crores | sip_data.csv |
| yoy_growth_pct | REAL | Year-over-year SIP growth percentage | sip_data.csv |

## fact_folio
| Column | Data Type | Business Definition | Source |
|--------|-----------|---------------------|--------|
| folio_id | INTEGER | Surrogate primary key | Auto-generated |
| month | TEXT | Month in YYYY-MM format | folio_data.csv |
| total_folios_crore | REAL | Total folio count in crores | folio_data.csv |
| equity_folios_crore | REAL | Equity folio count in crores | folio_data.csv |
| debt_folios_crore | REAL | Debt folio count in crores | folio_data.csv |
| hybrid_folios_crore | REAL | Hybrid folio count in crores | folio_data.csv |
| others_folios_crore | REAL | Other category folio count in crores | folio_data.csv |

## fact_benchmark
| Column | Data Type | Business Definition | Source |
|--------|-----------|---------------------|--------|
| bench_id | INTEGER | Surrogate primary key | Auto-generated |
| date_id | TEXT | Trading date (FK to dim_date) | benchmark_data.csv |
| index_name | TEXT | Index name (NIFTY50, NIFTY100, SENSEX) | benchmark_data.csv |
| close_value | REAL | Index closing value | benchmark_data.csv |

## fact_portfolio
| Column | Data Type | Business Definition | Source |
|--------|-----------|---------------------|--------|
| holding_id | INTEGER | Surrogate primary key | Auto-generated |
| amfi_code | INTEGER | Scheme identifier (FK to dim_fund) | portfolio_holdings.csv |
| stock_symbol | TEXT | Stock ticker symbol | portfolio_holdings.csv |
| stock_name | TEXT | Full company name | portfolio_holdings.csv |
| sector | TEXT | Industry sector | portfolio_holdings.csv |
| weight_pct | REAL | Allocation weight percentage | portfolio_holdings.csv |
| market_value_cr | REAL | Market value in INR crores | portfolio_holdings.csv |
| portfolio_date | TEXT | Portfolio snapshot date | portfolio_holdings.csv |
