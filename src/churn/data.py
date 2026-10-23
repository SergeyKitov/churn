import argparse
import zipfile
from pathlib import Path

import pandas as pd
import requests

from churn import config


def download_raw() -> None:
    """Скачивает архив Online Retail II с UCI и распаковывает xlsx в data/raw.

    Идемпотентна: если xlsx уже есть, ничего не делает.

    Raises:
        requests.HTTPError: сервер ответил ошибкой (404, 500 и т.п.).
        FileNotFoundError: после распаковки нужного xlsx нет в архиве.
    """

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
    """Читает оба листа исходного xlsx и склеивает их в одну таблицу.

    Листы "Year 2009-2010" и "Year 2010-2011" пересекаются по датам
    (01.12.2010–09.12.2010). Дубли здесь не убираются, это делает clean().

    Args:
        path: путь к online_retail_II.xlsx.

    Returns:
        Сырые транзакции с исходными именами колонок.
    """

    sheets = pd.read_excel(path, sheet_name=None)
    df = pd.concat(sheets.values(), ignore_index=True)
    return df


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Приводит имена колонок к snake_case и задаёт типы.

    invoice и stock_code становятся строками (в исходнике смешаны числа
    и строки вроде "C489449"), customer_id становится nullable Int64,
    чтобы пропуски не превращали ID во float.

    Args:
        df: результат load_raw().

    Returns:
        Новая таблица; входной df не меняется.
    """

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


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Чистит транзакции и откладывает отмены отдельно.

    Правила применяются по порядку:
    1. полные дубли строк;
    2. строки без customer_id;
    3. отмены (invoice начинается с "C") уходят в returns;
    4. строки с quantity <= 0 или price <= 0.
    В покупки добавляется колонка revenue = quantity * price.

    Args:
        df: результат normalize().

    Returns:
        (purchases, returns, report), где report содержит по строке
        на шаг с колонками step, rows_left, removed.
    """

    steps = []
    df = df.copy()
    steps.append({"step": "raw", "rows_left": len(df)})

    df = df.drop_duplicates()
    steps.append({"step": "drop_duplicates", "rows_left": len(df)})

    df = df[df["customer_id"].notna()]
    steps.append({"step": "no_customer_id", "rows_left": len(df)})

    is_cancel = df["invoice"].str.startswith("C")
    returns = df[is_cancel]
    df = df[~is_cancel]
    steps.append({"step": "drop_cancel", "rows_left": len(df)})

    df = df[(df["quantity"] > 0) & (df["price"] > 0)]
    steps.append({"step": "drop_not_purch", "rows_left": len(df)})

    df["revenue"] = df["quantity"] * df["price"]
    report = pd.DataFrame(steps)
    report["removed"] = -report["rows_left"].diff().fillna(0).astype("int")
    return df, returns, report


def build() -> None:
    """Собирает interim-слой: xlsx → normalize → clean → два parquet.

    Пишет TRANSACTIONS_PATH (чистые покупки) и RETURNS_PATH (отмены),
    печатает отчёт о том, сколько строк ушло на каждом шаге чистки.
    Ожидает, что RAW_XLSX уже скачан (см. download_raw).
    """

    raw = load_raw(config.RAW_XLSX)
    purchases, returns, report = clean(normalize(raw))

    config.INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    purchases.to_parquet(config.TRANSACTIONS_PATH, index=False)
    returns.to_parquet(config.RETURNS_PATH, index=False)
    print(report.to_string(index=False))


def main() -> None:
    """Точка входа командной строки: python -m churn.data {download,build}.

    download скачивает исходник в data/raw, build собирает parquet
    в data/interim. Вызывается из Makefile.
    """
    parser = argparse.ArgumentParser(description="Online Retail II data pipeline")
    parser.add_argument("command", choices=["download", "build"])
    args = parser.parse_args()
    if args.command == "download":
        download_raw()
    else:
        build()


if __name__ == "__main__":
    main()
