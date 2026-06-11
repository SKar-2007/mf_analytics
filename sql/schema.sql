-- sql/schema.sql
-- Ensure database drops old components cleanly before rebuilding
DROP TABLE IF EXISTS fact_transactions CASCADE;
DROP TABLE IF EXISTS fact_nav CASCADE;
DROP TABLE IF EXISTS fact_performance CASCADE;
DROP TABLE IF EXISTS fact_aum CASCADE;
DROP TABLE IF EXISTS dim_fund CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

-- Dimension Table: Fund Master Data
CREATE TABLE dim_fund (
    amfi_code INT PRIMARY KEY,
    fund_house VARCHAR(255) NOT NULL,
    scheme_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    sub_category VARCHAR(100),
    risk_grade VARCHAR(50)
);

-- Dimension Table: Dates Map (Essential for handling weekends/holidays)
CREATE TABLE dim_date (
    date_id DATE PRIMARY KEY,
    calendar_year INT NOT NULL,
    calendar_month INT NOT NULL,
    month_name VARCHAR(50) NOT NULL,
    day_of_week INT NOT NULL,
    is_weekend INT NOT NULL
);

-- Fact Table: Historical Daily Net Asset Values
CREATE TABLE fact_nav (
    nav_id SERIAL PRIMARY KEY,
    amfi_code INT REFERENCES dim_fund(amfi_code),
    date_id DATE REFERENCES dim_date(date_id),
    nav NUMERIC(12, 4) NOT NULL,
    CONSTRAINT unique_fund_date UNIQUE (amfi_code, date_id)
);

-- Fact Table: Investor Trading Log
CREATE TABLE fact_transactions (
    transaction_id INT PRIMARY KEY,
    investor_id INT NOT NULL,
    amfi_code INT REFERENCES dim_fund(amfi_code),
    transaction_date_id DATE REFERENCES dim_date(date_id),
    transaction_type VARCHAR(50) CHECK (transaction_type IN ('SIP', 'LUMPSUM', 'REDEMPTION')),
    amount NUMERIC(15, 2) NOT NULL,
    investor_state VARCHAR(100),
    kyc_status VARCHAR(50) CHECK (kyc_status IN ('VERIFIED', 'PENDING', 'FAILED'))
);

-- Fact Table: Asset Under Management (AUM) Trackers
CREATE TABLE fact_aum (
    aum_id SERIAL PRIMARY KEY,
    amfi_code INT REFERENCES dim_fund(amfi_code),
    date_id DATE REFERENCES dim_date(date_id),
    scheme_level_aum_crore NUMERIC(15, 2) NOT NULL
);

-- Fact Table: Performance Metrics & Operational Efficiency
CREATE TABLE fact_performance (
    amfi_code INT PRIMARY KEY REFERENCES dim_fund(amfi_code),
    return_1y NUMERIC(5, 2),
    return_3y NUMERIC(5, 2),
    return_5y NUMERIC(5, 2),
    expense_ratio NUMERIC(4, 2),
    expense_ratio_anomaly INT DEFAULT 0
);