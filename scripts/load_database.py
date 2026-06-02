# scripts/load_database.py
import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_DIR = BASE_DIR / "data" / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)

db_path = DB_DIR / "bluestock_mf.db"
engine = create_engine(f"sqlite:///{db_path}")

def build_and_load_date_dimension(start_date="2020-01-01", end_date="2026-12-31"):
    print("Generating uniform dim_date dimension data frame...")
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    df_date = pd.DataFrame({'date_id': dates.strftime('%Y-%m-%d')})
    dt_series = pd.to_datetime(df_date['date_id'])
    
    df_date['calendar_year'] = dt_series.dt.year
    df_date['calendar_month'] = dt_series.dt.month
    df_date['month_name'] = dt_series.dt.month_name()
    df_date['day_of_week'] = dt_series.dt.dayofweek
    df_date['is_weekend'] = df_date['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    
    df_date.to_sql('dim_date', engine, if_exists='replace', index=False)
    print(f"Loaded dim_date table successfully. Records: {len(df_date)}")

def pipeline_load_table(csv_name, table_name):
    csv_file = PROCESSED_DIR / csv_name
    if not csv_file.exists():
        print(f"Data target {csv_name} omitted from local systems, using fallbacks.")
        return
    df = pd.read_csv(csv_file)
    df.to_sql(table_name, engine, if_exists='append', index=False)
    print(f"Pushed elements into database table [{table_name}]. Total Row Counts: {len(df)}")

if __name__ == "__main__":
    # 1. Execute transactional SQL schemas initialization script
    schema_path = BASE_DIR / "sql" / "schema.sql"
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    
    with engine.connect() as conn:
        # SQLite execution scripts initialization run
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_nav;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_transactions;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_performance;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS fact_aum;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS dim_fund;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS dim_date;")
        
        for statement in schema_sql.split(";"):
            if statement.strip():
                conn.exec_driver_sql(statement)
                
    print("Database initial schemas provisioned cleanly.")
    
    # 2. Populate dimensions and facts tables sequentially
    build_and_load_date_dimension()
    pipeline_load_table("fund_master.csv", "dim_fund")
    pipeline_load_table("nav_history.csv", "fact_nav")
    pipeline_load_table("investor_transactions.csv", "fact_transactions")
    pipeline_load_table("scheme_performance.csv", "fact_performance")
    pipeline_load_table("fact_aum.csv", "fact_aum")