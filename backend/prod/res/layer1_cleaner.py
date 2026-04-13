"""
FLUX — Layer 1: Data Ingestion & Cleaning
Accepts raw CSV, returns clean standardized DataFrame
"""

import pandas as pd
import numpy as np
from io import BytesIO
from typing import Tuple


REQUIRED_COLUMNS = ["date", "product_name", "units_sold", "current_stock"]
OPTIONAL_COLUMNS = ["product_id", "category", "price", "supplier_id"]


def clean_csv(file_bytes: bytes) -> Tuple[pd.DataFrame, dict]:
    """
    Main entry point. Takes raw CSV bytes, returns clean DataFrame + report.
    """
    report = {"warnings": [], "rows_removed": 0, "columns_detected": []}

    # --- 1. Load ---
    try:
        df = pd.read_csv(BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Could not parse CSV: {e}")

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    report["columns_detected"] = list(df.columns)

    # --- 2. Map common column name variants ---
    column_aliases = {
        "sale_date": "date", "sales_date": "date", "transaction_date": "date",
        "item": "product_name", "product": "product_name", "name": "product_name",
        "qty_sold": "units_sold", "quantity": "units_sold", "sales": "units_sold",
        "stock": "current_stock", "inventory": "current_stock", "on_hand": "current_stock",
    }
    df.rename(columns=column_aliases, inplace=True)

    # --- 3. Validate required columns ---
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Found: {list(df.columns)}")

    # --- 4. Parse dates ---
    df["date"] = pd.to_datetime(df["date"], infer_format=True, dayfirst=True, errors="coerce")
    bad_dates = df["date"].isna().sum()
    if bad_dates > 0:
        report["warnings"].append(f"{bad_dates} rows had unparseable dates — removed")
        df = df.dropna(subset=["date"])

    df = df.sort_values("date").reset_index(drop=True)

    # --- 5. Remove duplicates ---
    before = len(df)
    df = df.drop_duplicates(subset=["date", "product_name"])
    report["rows_removed"] += before - len(df)

    # --- 6. Remove negative/zero values ---
    before = len(df)
    df = df[df["units_sold"] >= 0]
    df = df[df["current_stock"] >= 0]
    report["rows_removed"] += before - len(df)

    # --- 7. Fill missing values ---
    if "category" in df.columns:
        df["category"] = df["category"].fillna("general")
    else:
        df["category"] = "general"

    if "product_id" not in df.columns:
        # Generate stable product IDs from product names
        unique_products = df["product_name"].unique()
        id_map = {name: f"SKU_{str(i+1).zfill(3)}" for i, name in enumerate(unique_products)}
        df["product_id"] = df["product_name"].map(id_map)

    # Fill missing stock with forward fill per product
    df["current_stock"] = (
        df.groupby("product_name")["current_stock"]
        .transform(lambda x: x.ffill().bfill())
    )

    # Fill missing units_sold with category median
    df["units_sold"] = df.groupby("category")["units_sold"].transform(
        lambda x: x.fillna(x.median())
    )
    df["units_sold"] = df["units_sold"].fillna(0)

    # --- 8. Add derived columns ---
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.dayofweek  # 0=Monday

    report["final_rows"] = len(df)
    report["products_found"] = df["product_name"].nunique()
    report["date_range"] = f"{df['date'].min().date()} → {df['date'].max().date()}"

    return df, report
