import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "data" / "raw"

FILES = [
    "fund_master.csv",
    "nav_history.csv",
    "aum_data.csv",
    "sip_data.csv",
    "category_inflows.csv",
    "folio_data.csv",
    "scheme_performance.csv",
    "investor_transactions.csv",
    "portfolio_holdings.csv",
    "benchmark_data.csv",
]

def inspect_dataset(filepath):
    df = pd.read_csv(filepath)
    print(f"\n{'='*60}")
    print(f"File: {filepath.name}")
    print(f"Shape: {df.shape}")
    print(f"\nColumn dtypes:\n{df.dtypes}")
    print(f"\nFirst 5 rows:\n{df.head()}")
    print(f"\nNull counts:\n{df.isnull().sum()}")

if __name__ == "__main__":
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for fname in FILES:
        fpath = RAW_DIR / fname
        if fpath.exists():
            inspect_dataset(fpath)
        else:
            print(f"\n{'='*60}\nFile not found: {fname}")
