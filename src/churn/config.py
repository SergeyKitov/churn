from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
RAW_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
RAW_XLSX = RAW_DIR / "online_retail_II.xlsx"
TRANSACTIONS_PATH = INTERIM_DIR / "transactions.parquet"
