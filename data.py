"""
Synthetic order data generation for Smart Post-Purchase Rules demo.
Creates deterministic, realistic demo data with a fixed random seed.
"""

from typing import Any
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "order_id",
    "customer_type",
    "order_value",
    "discount_used",
    "past_edits",
    "past_cancels",
    "shipping_speed",
    "minutes_since_checkout",
    "address_change_requests",
]

# Valid values for categorical columns
CUSTOMER_TYPES = ("first_time", "repeat", "vip")
SHIPPING_SPEEDS = ("standard", "express")


def generate_synthetic_orders(n_rows: int = 200, seed: int = 42) -> pd.DataFrame:
    """
    Generate deterministic synthetic order data for demo purposes.

    Args:
        n_rows: Number of orders to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with required schema columns.
    """
    rng = np.random.default_rng(seed)

    # Order IDs: ORD-0001, ORD-0002, ...
    order_ids = [f"ORD-{i:04d}" for i in range(1, n_rows + 1)]

    # Customer types: more first_time/repeat, few vip (realistic)
    customer_type_probs = [0.45, 0.45, 0.10]  # first_time, repeat, vip
    customer_types = rng.choice(CUSTOMER_TYPES, size=n_rows, p=customer_type_probs)

    # Order value: skewed toward lower values
    order_values = np.clip(rng.exponential(scale=50, size=n_rows) + 15, 10, 500)

    # Discount used: 0 or 1
    discount_used = rng.choice([0, 1], size=n_rows, p=[0.7, 0.3])

    # Past edits: mostly 0, some 1–2, rare 3+
    past_edits = rng.choice([0, 1, 2, 3], size=n_rows, p=[0.6, 0.25, 0.12, 0.03])

    # Past cancels: mostly 0
    past_cancels = rng.choice([0, 1, 2], size=n_rows, p=[0.85, 0.12, 0.03])

    # Shipping speed: more standard than express
    shipping_speed = rng.choice(
        SHIPPING_SPEEDS, size=n_rows, p=[0.75, 0.25]
    )

    # Minutes since checkout: 0–90
    minutes_since_checkout = rng.integers(0, 91, size=n_rows)

    # Address change requests: mostly 0
    address_change_requests = rng.choice(
        [0, 1, 2], size=n_rows, p=[0.92, 0.06, 0.02]
    )

    df = pd.DataFrame(
        {
            "order_id": order_ids,
            "customer_type": customer_types,
            "order_value": np.round(order_values, 2),
            "discount_used": discount_used.astype(int),
            "past_edits": past_edits,
            "past_cancels": past_cancels,
            "shipping_speed": shipping_speed,
            "minutes_since_checkout": minutes_since_checkout,
            "address_change_requests": address_change_requests,
        }
    )

    return df


def validate_schema(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Validate that DataFrame has required columns and valid values.

    Args:
        df: DataFrame to validate.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors: list[str] = []

    if df is None or df.empty:
        return False, ["DataFrame is empty or None."]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return False, errors

    # Basic type/value checks
    if not pd.api.types.is_numeric_dtype(df["order_value"]):
        errors.append("order_value must be numeric.")

    valid_customer = set(CUSTOMER_TYPES)
    if not set(df["customer_type"].dropna().unique()).issubset(valid_customer):
        errors.append(f"customer_type must be one of: {CUSTOMER_TYPES}")

    valid_speed = set(SHIPPING_SPEEDS)
    if not set(df["shipping_speed"].dropna().unique()).issubset(valid_speed):
        errors.append(f"shipping_speed must be one of: {SHIPPING_SPEEDS}")

    if errors:
        return False, errors

    return True, []


def normalize_uploaded_df(
    df: pd.DataFrame, column_map: dict[str, str]
) -> pd.DataFrame:
    """
    Map uploaded columns to expected schema and normalize types.

    Args:
        df: Raw uploaded DataFrame.
        column_map: Mapping from internal name -> uploaded column name.

    Returns:
        Normalized DataFrame with expected schema.
    """
    result = pd.DataFrame(index=df.index)

    for internal_name, uploaded_name in column_map.items():
        if internal_name not in REQUIRED_COLUMNS or uploaded_name not in df.columns:
            continue
        result[internal_name] = df[uploaded_name].copy()

    # Coerce types
    if "order_value" in result.columns:
        result["order_value"] = pd.to_numeric(result["order_value"], errors="coerce").fillna(0)
    if "discount_used" in result.columns:
        result["discount_used"] = pd.to_numeric(result["discount_used"], errors="coerce").fillna(0).astype(int)
    if "past_edits" in result.columns:
        result["past_edits"] = pd.to_numeric(result["past_edits"], errors="coerce").fillna(0).astype(int)
    if "past_cancels" in result.columns:
        result["past_cancels"] = pd.to_numeric(result["past_cancels"], errors="coerce").fillna(0).astype(int)
    if "minutes_since_checkout" in result.columns:
        result["minutes_since_checkout"] = pd.to_numeric(result["minutes_since_checkout"], errors="coerce").fillna(0).astype(int)
    if "address_change_requests" in result.columns:
        result["address_change_requests"] = pd.to_numeric(result["address_change_requests"], errors="coerce").fillna(0).astype(int)

    if "order_id" in result.columns:
        result["order_id"] = result["order_id"].astype(str)
    if "customer_type" in result.columns:
        result["customer_type"] = result["customer_type"].astype(str).str.lower().str.strip()
    if "shipping_speed" in result.columns:
        result["shipping_speed"] = result["shipping_speed"].astype(str).str.lower().str.strip()

    return result


def get_example_csv_content() -> str:
    """Return example CSV content for template download."""
    sample = generate_synthetic_orders(n_rows=5, seed=123)
    return sample.to_csv(index=False)
