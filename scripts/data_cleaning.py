import os
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def process_nav_history():
    print("Cleaning nav_history.csv...")
    raw_path = RAW_DIR / "nav_history.csv"
    if not raw_path.exists():
        print("SKIP: nav_history.csv not found")
        return
    df = pd.read_csv(raw_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "amfi_code"])
    df = df.drop_duplicates(subset=["amfi_code", "date"])
    df = df[df["nav"] > 0]
    processed_groups = []
    for amfi, group in df.groupby("amfi_code"):
        group = group.set_index("date").sort_index()
        full_range = pd.date_range(start=group.index.min(), end=group.index.max(), freq="D")
        group = group.reindex(full_range)
        group["nav"] = group["nav"].ffill()
        group["amfi_code"] = amfi
        group = group.reset_index().rename(columns={"index": "date"})
        processed_groups.append(group)
    final = pd.concat(processed_groups, ignore_index=True)
    final = final.rename(columns={"date": "date_id"})
    final.to_csv(PROCESSED_DIR / "nav_history.csv", index=False)
    print(f"nav_history cleaned: {final.shape}")

def process_transactions():
    print("Cleaning investor_transactions.csv...")
    raw_path = RAW_DIR / "investor_transactions.csv"
    if not raw_path.exists():
        print("SKIP: investor_transactions.csv not found")
        return
    df = pd.read_csv(raw_path)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df = df.dropna(subset=["transaction_date", "amount_inr"])
    txn_map = {"SIP": "SIP", "LUMPSUM": "LUMPSUM", "REDEMPTION": "REDEMPTION"}
    df["transaction_type"] = df["transaction_type"].astype(str).str.strip()
    df["transaction_type"] = df["transaction_type"].map(
        lambda x: txn_map.get(x, x.upper())
    )
    df = df[df["amount_inr"] > 0]
    df["kyc_status"] = df["kyc_status"].astype(str).str.upper().str.strip()
    df["kyc_status"] = df["kyc_status"].apply(
        lambda x: x if x in ["VERIFIED", "PENDING", "FAILED"] else "FAILED"
    )
    df = df.rename(columns={
        "transaction_date": "date_id",
        "amount_inr": "amount",
    })
    df.to_csv(PROCESSED_DIR / "investor_transactions.csv", index=False)
    print(f"investor_transactions cleaned: {df.shape}")

def process_performance():
    print("Cleaning scheme_performance.csv...")
    raw_path = RAW_DIR / "scheme_performance.csv"
    if not raw_path.exists():
        print("SKIP: scheme_performance.csv not found")
        return
    df = pd.read_csv(raw_path)
    for col in ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "expense_ratio_pct"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "expense_ratio_pct" in df.columns:
        df["expense_anomaly"] = (
            (df["expense_ratio_pct"] < 0.1) | (df["expense_ratio_pct"] > 2.5)
        ).astype(int)
    df.to_csv(PROCESSED_DIR / "scheme_performance.csv", index=False)
    print(f"scheme_performance cleaned: {df.shape}")

def process_fund_master():
    print("Processing fund_master.csv...")
    raw_path = RAW_DIR / "fund_master.csv"
    if not raw_path.exists():
        print("SKIP: fund_master.csv not found")
        return
    df = pd.read_csv(raw_path)
    df = df.rename(columns={
        "plan": "plan_type",
        "risk_category": "risk_grade",
    })
    df.to_csv(PROCESSED_DIR / "fund_master.csv", index=False)
    print(f"fund_master processed: {df.shape}")

def process_aum():
    print("Processing aum_data.csv...")
    raw_path = RAW_DIR / "aum_data.csv"
    if not raw_path.exists():
        print("SKIP: aum_data.csv not found")
        return
    df = pd.read_csv(raw_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.rename(columns={"date": "date_id"})
    df.to_csv(PROCESSED_DIR / "aum_data.csv", index=False)
    print(f"aum_data processed: {df.shape}")

def process_sip():
    print("Processing sip_data.csv...")
    raw_path = RAW_DIR / "sip_data.csv"
    if not raw_path.exists():
        print("SKIP: sip_data.csv not found")
        return
    df = pd.read_csv(raw_path)
    df.to_csv(PROCESSED_DIR / "sip_data.csv", index=False)
    print(f"sip_data processed: {df.shape}")

def process_folio():
    print("Processing folio_data.csv...")
    raw_path = RAW_DIR / "folio_data.csv"
    if not raw_path.exists():
        print("SKIP: folio_data.csv not found")
        return
    df = pd.read_csv(raw_path)
    df.to_csv(PROCESSED_DIR / "folio_data.csv", index=False)
    print(f"folio_data processed: {df.shape}")

def process_benchmark():
    print("Processing benchmark_data.csv...")
    raw_path = RAW_DIR / "benchmark_data.csv"
    if not raw_path.exists():
        print("SKIP: benchmark_data.csv not found")
        return
    df = pd.read_csv(raw_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.rename(columns={"date": "date_id"})
    df.to_csv(PROCESSED_DIR / "benchmark_data.csv", index=False)
    print(f"benchmark_data processed: {df.shape}")

def process_portfolio():
    print("Processing portfolio_holdings.csv...")
    raw_path = RAW_DIR / "portfolio_holdings.csv"
    if not raw_path.exists():
        print("SKIP: portfolio_holdings.csv not found")
        return
    df = pd.read_csv(raw_path)
    df.to_csv(PROCESSED_DIR / "portfolio_holdings.csv", index=False)
    print(f"portfolio_holdings processed: {df.shape}")

def process_category_inflows():
    print("Processing category_inflows.csv...")
    raw_path = RAW_DIR / "category_inflows.csv"
    if not raw_path.exists():
        print("SKIP: category_inflows.csv not found")
        return
    df = pd.read_csv(raw_path)
    df.to_csv(PROCESSED_DIR / "category_inflows.csv", index=False)
    print(f"category_inflows processed: {df.shape}")

if __name__ == "__main__":
    process_nav_history()
    process_transactions()
    process_performance()
    process_fund_master()
    process_aum()
    process_sip()
    process_folio()
    process_benchmark()
    process_portfolio()
    process_category_inflows()
    print("\nAll cleaning complete.")
