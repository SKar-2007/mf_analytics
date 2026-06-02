# scripts/data_cleaning.py
import os
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def process_nav_history():
    print("Executing group-isolated cleaning on nav_history.csv...")
    raw_path = RAW_DIR / "nav_history.csv"
    if not raw_path.exists(): return
    
    df = pd.read_csv(raw_path)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date', 'amfi_code'])
    df = df.drop_duplicates(subset=['amfi_code', 'date'])
    df = df[df['nav'] > 0]
    
    # Isolate forward-filling within each individual fund profile
    processed_groups = []
    for amfi, group in df.groupby('amfi_code'):
        group = group.set_index('date').sort_index()
        # Reindex to a complete continuous timeline to expose holiday/weekend gaps
        full_timeline = pd.date_range(start=group.index.min(), end=group.index.max(), freq='D')
        group = group.reindex(full_timeline)
        # Safely forward fill values inside the isolated group boundaries
        group['nav'] = group['nav'].ffill()
        group['amfi_code'] = amfi
        group = group.reset_index().rename(columns={'index': 'date'})
        processed_groups.append(group)
        
    final_df = pd.concat(processed_groups, ignore_index=True)
    final_df.to_csv(PROCESSED_DIR / "nav_history.csv", index=False)
    print(f"nav_history clean pipeline complete. Shape: {final_df.shape}")

def process_transactions():
    print("Normalizing investor transactions and compliance parameters...")
    raw_path = RAW_DIR / "investor_transactions.csv"
    if not raw_path.exists(): return
    
    df = pd.read_csv(raw_path)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    df = df.dropna(subset=['transaction_date', 'amount'])
    
    # Map raw transactional variations into unified classes
    df['transaction_type'] = df['transaction_type'].astype(str).str.upper().str.strip()
    txn_map = {'SIP': 'SIP', 'SYSTEMATIC': 'SIP', 'LUMPSUM': 'LUMPSUM', 'ONETIME': 'LUMPSUM', 'REDEMPTION': 'REDEMPTION', 'WITHDRAWAL': 'REDEMPTION'}
    df['transaction_type'] = df['transaction_type'].map(txn_map).fillna('LUMPSUM')
    
    df = df[df['amount'] > 0]
    
    # Handle user compliance states
    df['kyc_status'] = df['kyc_status'].astype(str).str.upper().str.strip()
    df['kyc_status'] = df['kyc_status'].apply(lambda x: x if x in ['VERIFIED', 'PENDING', 'FAILED'] else 'FAILED')
    
    df.to_csv(PROCESSED_DIR / "investor_transactions.csv", index=False)
    print("Transaction preprocessing step finished successfully.")

def process_performance():
    print("Evaluating financial performance bounds...")
    raw_path = RAW_DIR / "scheme_performance.csv"
    if not raw_path.exists(): return
    
    df = pd.read_csv(raw_path)
    for target_col in ['return_1y', 'return_3y', 'return_5y', 'expense_ratio']:
        if target_col in df.columns:
            df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
            
    if 'expense_ratio' in df.columns:
        # Flag structural cost anomalies outside of standard limits (0.1% to 2.5%)
        df['expense_ratio_anomaly'] = ((df['expense_ratio'] < 0.1) | (df['expense_ratio'] > 2.5)).astype(int)
        
    df.to_csv(PROCESSED_DIR / "scheme_performance.csv", index=False)
    print("Performance vectors clean pipeline complete.")

if __name__ == "__main__":
    process_nav_history()
    process_transactions()
    process_performance()