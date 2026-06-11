-- Q1: Top 5 funds by latest AUM
SELECT f.scheme_name, f.fund_house, a.aum_cr
FROM fact_aum a JOIN dim_fund f ON a.amfi_code = f.amfi_code
WHERE a.date_id = (SELECT MAX(date_id) FROM fact_aum)
ORDER BY a.aum_cr DESC LIMIT 5;

-- Q2: Average NAV per month (all funds)
SELECT d.year, d.month_name, ROUND(AVG(n.nav), 2) AS avg_nav
FROM fact_nav n JOIN dim_date d ON n.date_id = d.date_id
GROUP BY d.year, d.month ORDER BY d.year, d.month;

-- Q3: SIP inflow YoY growth
SELECT d.year,
       ROUND(SUM(t.amount) / 1e7, 2) AS total_sip_cr,
       ROUND((SUM(t.amount) - LAG(SUM(t.amount)) OVER (ORDER BY d.year))
             / LAG(SUM(t.amount)) OVER (ORDER BY d.year) * 100, 2) AS yoy_pct
FROM fact_transactions t JOIN dim_date d ON t.date_id = d.date_id
WHERE t.transaction_type = 'SIP'
GROUP BY d.year;

-- Q4: Total transaction amount by state (top 10)
SELECT t.state, ROUND(SUM(t.amount) / 1e7, 2) AS total_cr
FROM fact_transactions t
GROUP BY t.state ORDER BY total_cr DESC LIMIT 10;

-- Q5: Funds with expense_ratio < 1%
SELECT f.scheme_name, f.fund_house, f.category, p.expense_ratio
FROM fact_performance p JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio < 1.0
ORDER BY p.expense_ratio ASC;

-- Q6: Category-wise net inflow in FY2025
SELECT f.category,
       ROUND(SUM(CASE WHEN t.transaction_type IN ('SIP','Lumpsum') THEN t.amount ELSE 0 END) / 1e7, 2) AS inflow_cr,
       ROUND(SUM(CASE WHEN t.transaction_type = 'Redemption' THEN t.amount ELSE 0 END) / 1e7, 2) AS outflow_cr,
       ROUND((SUM(CASE WHEN t.transaction_type != 'Redemption' THEN t.amount ELSE 0 END)
             - SUM(CASE WHEN t.transaction_type = 'Redemption' THEN t.amount ELSE 0 END)) / 1e7, 2) AS net_inflow_cr
FROM fact_transactions t JOIN dim_fund f ON t.amfi_code = f.amfi_code
     JOIN dim_date d ON t.date_id = d.date_id
WHERE d.year = 2025
GROUP BY f.category ORDER BY net_inflow_cr DESC;

-- Q7: Top 5 fund houses by total transaction volume
SELECT f.fund_house, COUNT(*) AS txn_count,
       ROUND(SUM(t.amount) / 1e7, 2) AS volume_cr
FROM fact_transactions t JOIN dim_fund f ON t.amfi_code = f.amfi_code
GROUP BY f.fund_house ORDER BY volume_cr DESC LIMIT 5;

-- Q8: Month-over-month NAV change for SBI Bluechip (119551)
SELECT d.year, d.month_name,
       ROUND(AVG(n.nav), 4) AS avg_monthly_nav,
       ROUND(AVG(n.nav) - LAG(AVG(n.nav)) OVER (ORDER BY d.year, d.month), 4) AS mom_change
FROM fact_nav n JOIN dim_date d ON n.date_id = d.date_id
WHERE n.amfi_code = 119551
GROUP BY d.year, d.month ORDER BY d.year, d.month;

-- Q9: Investor count by city tier and KYC status
SELECT t.city_tier, t.kyc_status, COUNT(DISTINCT t.investor_id) AS investor_count
FROM fact_transactions t
GROUP BY t.city_tier, t.kyc_status ORDER BY investor_count DESC;

-- Q10: Funds with highest 3-year returns in each category
SELECT f.category, f.scheme_name, f.fund_house, p.return_3yr,
       RANK() OVER (PARTITION BY f.category ORDER BY p.return_3yr DESC) AS rank_in_category
FROM fact_performance p JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY f.category, rank_in_category;
