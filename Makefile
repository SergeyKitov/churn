.DELETE_ON_ERROR:

RAW := data/raw/online_retail_II.xlsx
INTERIM := data/interim/transactions.parquet

.PHONY: install lint format test data


install:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest

data: $(INTERIM)

$(RAW):
	uv run python -m churn.data download

$(INTERIM): $(RAW) src/churn/data.py src/churn/config.py
	uv run python -m churn.data build

