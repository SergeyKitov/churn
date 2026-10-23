import zipfile

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
