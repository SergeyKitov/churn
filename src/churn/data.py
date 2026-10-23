import zipfile
from pathlib import Path

import pandas as pd
import requests

from churn import config


def download_raw() -> None:
    if config.RAW_XLSX.exists():
        print(f"{config.RAW_XLSX} XLSX already exists")
        return

    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = config.RAW_DIR / "online_retail_ii.zip"

    print(f"Downloading {config.RAW_URL}")
    with requests.get(config.RAW_URL, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(config.RAW_DIR)
    zip_path.unlink()

    if not config.RAW_XLSX.exists():
        raise FileNotFoundError(f"{config.RAW_XLSX} not found after unzip")


def load_raw(path: Path) -> pd.DataFrame:
    sheets = pd.read_excel(path, sheet_name=None)
    df = pd.concat(sheets.values(), ignore_index=True)
    return df


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.rename(
        columns={
            "Invoice": "invoice",
            "StockCode": "stock_code",
            "Description": "description",
            "Quantity": "quantity",
            "InvoiceDate": "invoice_date",
            "Price": "price",
            "Customer ID": "customer_id",
            "Country": "country",
        }
    )
    df["invoice"] = df["invoice"].astype("str")
    df["stock_code"] = df["stock_code"].astype("str")
    df["customer_id"] = df["customer_id"].astype("Int64")

    return df
