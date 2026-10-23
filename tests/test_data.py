import pandas as pd

from churn.data import clean


def make_transactions() -> pd.DataFrame:
    """Пять строк, каждая «плохая» нарушает ровно одно правило clean().

    0: нормальная покупка
    1: точный дубль строки 0
    2: нет клиента
    3: отмена (invoice начинается с "C")
    4: нулевая цена
    """
    return pd.DataFrame(
        {
            "invoice": ["100", "100", "101", "C102", "103"],
            "stock_code": ["A", "A", "A", "A", "A"],
            "description": ["item"] * 5,
            "quantity": [2, 2, 2, -2, 2],
            "invoice_date": [pd.Timestamp("2010-12-01")] * 5,
            "price": [3.0, 3.0, 3.0, 3.0, 0.0],
            "customer_id": pd.array([1, 1, pd.NA, 2, 3], dtype="Int64"),
            "country": ["United Kingdom"] * 5,
        }
    )


def test_clean_keeps_only_valid_purchase() -> None:
    purchases, _, _ = clean(make_transactions())

    assert len(purchases) == 1
    assert purchases["invoice"].iloc[0] == "100"
    assert purchases["revenue"].iloc[0] == 6.0


def test_clean_moves_cancellations_to_returns() -> None:
    _, returns, _ = clean(make_transactions())

    assert returns["invoice"].tolist() == ["C102"]


def test_clean_report_counts_each_rule_once() -> None:
    _, _, report = clean(make_transactions())

    assert report["step"].tolist() == [
        "raw",
        "drop_duplicates",
        "no_customer_id",
        "drop_cancel",
        "drop_not_purch",
    ]
    assert report["rows_left"].tolist() == [5, 4, 3, 2, 1]
    assert report["removed"].tolist() == [0, 1, 1, 1, 1]


def test_clean_does_not_modify_input() -> None:
    df = make_transactions()
    before = df.copy()

    clean(df)

    pd.testing.assert_frame_equal(df, before)
