# scripts/etl_pipeline.py
import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
SQL_SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"

# Configure connection parameters to point to your local pgAdmin PostgreSQL instance
# Format: postgresql://username:password@localhost:5432/database_name
DB_URL = "postgresql://postgres:password@localhost:5432/bluestock_mf"
engine = create_engine(DB_URL)

def run_database_initialization():
    print("Rebuilding PostgreSQL database environments...")
    with open(SQL_SCHEMA_PATH, "r") as schema_file:
        raw_sql_script = schema_file.read()
        
    with engine.begin() as DB_connection:
        # Split sql actions safely by command delimiters
        for operational_query in raw_sql_script.split(";"):
            if operational_query.strip():
                DB_connection.execute(text(operational_query))
    print("Target definitions successfully initialized.")

def load_date_dimension_matrix():
    print("Generating consistent core master calendar coordinates...")
    date_series = pd.date_range(start="2020-01-01", end="2026-12-31", freq='D')
    dim_date_df = pd.DataFrame({'date_id': date_series})
    
    dim_date_df['calendar_year'] = dim_date_df['date_id'].dt.year
    dim_date_df['calendar_month'] = dim_date_df['date_id'].dt.month
    dim_date_df['month_name'] = dim_date_df['date_id'].dt.month_name()
    dim_date_df['day_of_week'] = dim_date_df['date_id'].dt.dayofweek
    dim_date_df['is_weekend'] = dim_date_df['day_of_week'].apply(lambda day: 1 if day >= 5 else 0)
    
    dim_date_df.to_sql('dim_date', engine, if_exists='append', index=False)
    print("Master calendar matrix populated.")

def stream_processed_csv_to_db(csv_file_name, target_table_name):
    target_path = PROCESSED_DIR / csv_file_name
    if not target_path.exists():
        print(f"Skipping empty or missing track asset target: {csv_file_name}")
        return
    df = pd.read_csv(target_path)
    df.to_sql(target_table_name, engine, if_exists='append', index=False)
    print(f"Loaded database table [{target_table_name}]. Total Row Counts: {len(df)}")

if __name__ == "__main__":
    run_database_initialization()
    load_date_dimension_matrix()
    
    # Map processed assets directly down to structured relational layers
    stream_processed_csv_to_db("fund_master.csv", "dim_fund")
    stream_processed_csv_to_db("nav_history.csv", "fact_nav")
    stream_processed_csv_to_db("investor_transactions.csv", "fact_transactions")
    stream_processed_csv_to_db("scheme_performance.csv", "fact_performance")