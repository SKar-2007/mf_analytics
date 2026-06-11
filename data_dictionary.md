# Structural Mapping & Project Data Dictionary

## 1. dim_fund (Fund Master Coordinates)
| Column Name | Data Type | Core Definition Context |
|---|---|---|
| amfi_code | INT (PK) | Unique Association Key Assigned by AMFI |
| fund_house | VARCHAR | Asset Management Company Name |
| scheme_name | VARCHAR | Registered Legal Investment Title |
| category | VARCHAR | Broad asset classification (e.g., Equity) |

## 2. fact_nav (Historical Valuation Appraisals Log)
| Column Name | Data Type | Core Definition Context |
|---|---|---|
| nav_id | SERIAL (PK) | Auto-incrementing record identifier |
| amfi_code | INT (FK) | Target Fund Identification Code |
| date_id | DATE (FK) | Associated calendar day |
| nav | NUMERIC | Continuous Asset Valuation Metric |