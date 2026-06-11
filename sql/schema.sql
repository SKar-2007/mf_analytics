-- Dimension: Fund
CREATE TABLE dim_fund (
    amfi_code     INTEGER PRIMARY KEY,
    fund_house    TEXT NOT NULL,
    scheme_name   TEXT NOT NULL,
    category      TEXT,
    sub_category  TEXT,
    risk_grade    TEXT,
    plan_type     TEXT,
    benchmark     TEXT
);

-- Dimension: Date
CREATE TABLE dim_date (
    date_id       TEXT PRIMARY KEY,
    year          INTEGER,
    quarter       INTEGER,
    month         INTEGER,
    month_name    TEXT,
    week          INTEGER,
    day_of_week   TEXT,
    is_weekend    INTEGER
);

-- Fact: NAV
CREATE TABLE fact_nav (
    nav_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code     INTEGER NOT NULL,
    date_id       TEXT NOT NULL,
    nav           REAL NOT NULL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

-- Fact: Transactions
CREATE TABLE fact_transactions (
    txn_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id       TEXT NOT NULL,
    amfi_code         INTEGER NOT NULL,
    date_id           TEXT NOT NULL,
    transaction_type  TEXT NOT NULL,
    amount            REAL NOT NULL,
    state             TEXT,
    city_tier         TEXT,
    kyc_status        TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);

-- Fact: Performance
CREATE TABLE fact_performance (
    perf_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code     INTEGER NOT NULL,
    return_1yr    REAL,
    return_3yr    REAL,
    return_5yr    REAL,
    expense_ratio REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

-- Fact: AUM
CREATE TABLE fact_aum (
    aum_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code     INTEGER NOT NULL,
    date_id       TEXT NOT NULL,
    aum_cr        REAL NOT NULL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
);
