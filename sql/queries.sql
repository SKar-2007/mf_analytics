-- sql/queries.sql

-- 1. Top 5 Funds Ranking by Current Total Asset Metrics Under Management (AUM Crore)
SELECT f.amfi_code, f.scheme_name, a.scheme_level_aum_crore
FROM fact_aum a
JOIN dim_fund f ON a.amfi_code = f.amfi_code
ORDER BY a.scheme_level_aum_crore DESC
LIMIT 5;

-- 2. Average Stated Asset Valuation Realized (NAV) Grouped per Month Time Boundaries
SELECT f.scheme_name, d.calendar_year, d.month_name, AVG(n.nav) as average_nav_value
FROM fact_nav n
JOIN dim_date d ON n.date_id = d.date_id
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY n.amfi_code, f.scheme_name, d.calendar_year, d.calendar_month, d.month_name
ORDER BY d.calendar_year, d.calendar_month;

-- 3. SIP Year-Over-Year Volume Ingestion Metrics Analytics
SELECT d.calendar_year, COUNT(t.transaction_id) as total_sip_count, SUM(t.amount) as aggregate_sip_capital
FROM fact_transactions t
JOIN dim_date d ON t.transaction_date_id = d.date_id
WHERE t.transaction_type = 'SIP'
GROUP BY d.calendar_year;

-- 4. Geographical Distributions Analysis of Financial Actions by Investor State Location
SELECT t.investor_state, COUNT(t.transaction_id) as trade_volume, SUM(t.amount) as transaction_liquidity
FROM fact_transactions t
GROUP BY t.investor_state
ORDER BY transaction_liquidity DESC;

-- 5. Highly Efficient Funds Operating Below Cost Limits (<1% Expense Ratio Thresholds)
SELECT f.amfi_code, f.scheme_name, p.expense_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio < 1.0 AND p.expense_ratio_anomaly = 0;