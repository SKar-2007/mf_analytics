import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_DIR = BASE_DIR / "data" / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)

db_path = DB_DIR / "bluestock_mf.db"
engine = create_engine(f"sqlite:///{db_path}")

TABLE_MAP = {
    "fund_master.csv": "dim_fund",
    "nav_history.csv": "fact_nav",
    "investor_transactions.csv": "fact_transactions",
    "scheme_performance.csv": "fact_performance",
    "aum_data.csv": "fact_aum",
    "sip_data.csv": "fact_sip",
    "folio_data.csv": "fact_folio",
    "benchmark_data.csv": "fact_benchmark",
    "portfolio_holdings.csv": "fact_portfolio",
    "category_inflows.csv": "fact_category_inflow",
}

def build_date_dimension(start="2020-01-01", end="2026-12-31"):
    print("Building dim_date...")
    dates = pd.date_range(start=start, end=end, freq="D")
    df = pd.DataFrame({"date_id": dates.strftime("%Y-%m-%d")})
    dt = pd.to_datetime(df["date_id"])
    df["calendar_year"] = dt.dt.year
    df["calendar_month"] = dt.dt.month
    df["month_name"] = dt.dt.month_name()
    df["day_of_week"] = dt.dt.dayofweek
    df["is_weekend"] = (dt.dt.dayofweek >= 5).astype(int)
    df.to_sql("dim_date", engine, if_exists="replace", index=False)
    print(f"dim_date: {len(df)} rows")

def load_table(csv_name, table_name):
    csv_path = PROCESSED_DIR / csv_name
    if not csv_path.exists():
        print(f"SKIP: {csv_name} not found")
        return
    df = pd.read_csv(csv_path)
    with engine.connect() as conn:
        insp = conn.exec_driver_sql(f"SELECT * FROM {table_name} LIMIT 0")
        table_cols = set(insp.keys())
    df_cols = set(df.columns)
    common_cols = list(df_cols & table_cols)
    if not common_cols:
        print(f"SKIP: no matching columns for {table_name}")
        return
    df = df[common_cols]
    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"{table_name}: {len(df)} rows loaded")

if __name__ == "__main__":
    schema_path = BASE_DIR / "sql" / "schema.sql"
    with engine.connect() as conn:
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_nav;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_transactions;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_performance;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_aum;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_sip;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_folio;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_benchmark;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_portfolio;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_category_inflow;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS dim_fund;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS dim_date;")
        if schema_path.exists():
            with open(schema_path) as f:
                for stmt in f.read().split(";"):
                    if stmt.strip():
                        conn.exec_driver_sql(stmt)
        conn.commit()
    print("Schema applied.")
    build_date_dimension()
    for csv_name, table_name in TABLE_MAP.items():
        load_table(csv_name, table_name)
    print("\nDatabase load complete.")
