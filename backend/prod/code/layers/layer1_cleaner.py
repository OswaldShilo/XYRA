"""
FLUX — Layer 1: Data Ingestion & Cleaning
Auto-detect columns, normalize formats, handle nulls, remove duplicates
"""

import pandas as pd
import numpy as np
from io import BytesIO
from typing import Tuple, Dict, Any
from datetime import datetime


def _detect_columns(df: pd.DataFrame) -> Dict[str, str]:
    """
    Auto-detect expected columns by checking common patterns.
    Returns: dict of {expected_col: actual_col}
    """
    expected = {}
    cols_lower = {col.lower(): col for col in df.columns}

    # Helper function to find column by pattern (substring match)
    def find_col(patterns):
        for pattern in patterns:
            for col_lower, col_original in cols_lower.items():
                if pattern in col_lower:
                    return col_original
        return None

    # Date column
    found = find_col(['date', 'timestamp', 'datetime', 'trans_date', 'order_date'])
    if found:
        expected['date'] = found

    # Product name/ID
    found = find_col(['product', 'sku', 'code'])
    if found:
        expected['product_id'] = found

    # Category
    found = find_col(['category', 'type'])
    if found:
        expected['category'] = found

    # Units sold
    found = find_col(['units_sold', 'quantity_sold', 'qty_sold', 'sales_qty', 'units', 'sold'])
    if found:
        expected['units_sold'] = found

    # Inventory/current stock
    found = find_col(['inventory', 'current_stock', 'stock', 'stock_level', 'level'])
    if found:
        expected['current_stock'] = found

    # Price
    found = find_col(['price', 'unit_price', 'selling_price'])
    if found:
        expected['price'] = found

    # Region
    found = find_col(['region', 'store_region', 'area'])
    if found:
        expected['region'] = found

    return expected


def _normalize_date(date_str: str) -> datetime:
    """Try multiple date formats and return normalized datetime."""
    formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%m-%d-%Y',
        '%d.%m.%Y',
    ]
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except:
            continue
    # If all fail, use pd.to_datetime's intelligent parsing
    return pd.to_datetime(date_str)


def clean_csv(file_bytes: bytes, expected_cols: Dict[str, str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main cleaning function.
    
    Input: file_bytes (CSV file)
    Output: (cleaned DataFrame, cleaning report)
    """
    report = {
        "original_rows": 0,
        "final_rows": 0,
        "duplicates_removed": 0,
        "nulls_handled": 0,
        "negatives_removed": 0,
        "date_conversion_errors": 0,
        "detected_columns": {},
        "errors": [],
    }

    try:
        # Read CSV
        df = pd.read_csv(BytesIO(file_bytes))
        report["original_rows"] = len(df)

        # Auto-detect columns if not provided
        if expected_cols is None:
            expected_cols = _detect_columns(df)
        
        report["detected_columns"] = expected_cols

        # Keep only detected columns
        cols_to_keep = list(expected_cols.values())
        missing = [col for col in cols_to_keep if col not in df.columns]
        if missing:
            report["errors"].append(f"Missing columns: {missing}")
            # Fill with defaults if possible
            for orig_col, mapped_col in expected_cols.items():
                if mapped_col not in df.columns:
                    if orig_col == 'price':
                        df[mapped_col] = 0.0
                    elif orig_col == 'region':
                        df[mapped_col] = 'Unknown'
                    else:
                        continue

        # Rename columns to standard names
        rename_map = {v: k for k, v in expected_cols.items()}
        df = df.rename(columns=rename_map)

        # Keep only standardized columns
        std_cols = ['date', 'product_id', 'category', 'units_sold', 'current_stock', 'price', 'region']
        actual_cols = [col for col in std_cols if col in df.columns]
        df = df[actual_cols]

        # Normalize date column
        try:
            df['date'] = df['date'].apply(_normalize_date)
        except Exception as e:
            report["date_conversion_errors"] = len(df)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Handle nulls
        null_counts = df.isnull().sum()
        report["nulls_handled"] = int(null_counts.sum())

        # Forward-fill date-dependent nulls
        df = df.sort_values('date')
        if 'units_sold' in df.columns:
            df['units_sold'] = df.groupby('product_id')['units_sold'].transform(lambda x: x.ffill()).fillna(0)
        if 'current_stock' in df.columns:
            df['current_stock'] = df.groupby('product_id')['current_stock'].transform(lambda x: x.ffill()).fillna(0)

        # Fill remaining nulls with category median or 0
        for col in ['units_sold', 'current_stock', 'price']:
            if col in df.columns:
                if 'category' in df.columns:
                    df[col] = df.groupby('category')[col].transform(lambda x: x.fillna(x.median()))
                df[col] = df[col].fillna(0)

        # Remove duplicates
        initial_len = len(df)
        df = df.drop_duplicates(
            subset=['date', 'product_id', 'category'] if 'category' in df.columns else ['date', 'product_id'],
            keep='first'
        )
        report["duplicates_removed"] = initial_len - len(df)

        # Remove negative values in numeric columns
        for col in ['units_sold', 'current_stock', 'price']:
            if col in df.columns:
                neg_mask = df[col] < 0
                report["negatives_removed"] += neg_mask.sum()
                df = df[~neg_mask]

        # Sort by date and product
        df = df.sort_values(['date', 'product_id']).reset_index(drop=True)
        report["final_rows"] = len(df)

        return df, report

    except Exception as e:
        report["errors"].append(str(e))
        return pd.DataFrame(), report
