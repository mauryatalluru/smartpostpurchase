"""
Rule engine for Smart Post-Purchase Rules demo.
Deterministic, explainable recommendations - no ML.
"""

from typing import Any
import pandas as pd
import numpy as np

# Valid window options (minutes)
VALID_WINDOWS = (10, 15, 20, 25, 30)

INDUSTRIES = ("Apparel", "Beauty", "Electronics", "Supplements")


def _clamp_window(val: float) -> int:
    """Clamp suggested window to nearest valid option (10–30)."""
    for w in sorted(VALID_WINDOWS):
        if val <= w:
            return w
    return 30


def _compute_window(
    base: int,
    customer_type: str,
    discount_used: int,
    past_edits: int,
    shipping_speed: str,
) -> int:
    """Compute suggested edit window for a single row."""
    w = float(base)
    if customer_type == "vip":
        w -= 5
    if customer_type == "first_time" and discount_used == 1:
        w += 5
    if past_edits >= 2:
        w += 5
    if shipping_speed == "express":
        w -= 5
    return _clamp_window(max(10, w))


def _compute_upsell(
    order_value: float,
    customer_type: str,
    shipping_speed: str,
    industry: str,
    enable_upsell: bool,
) -> str:
    """Determine if upsell should be shown."""
    if not enable_upsell or shipping_speed == "express":
        return "No"

    if order_value >= 80 and customer_type != "first_time":
        return "Yes"
    if industry == "Apparel" and order_value >= 60:
        return "Yes"
    if industry == "Electronics" and order_value >= 120:
        return "Yes"

    return "No"


def _compute_strict_address(
    address_change_requests: int,
    customer_type: str,
    conservative: bool,
) -> str:
    """Determine if strict address validation should be enabled."""
    if conservative and customer_type == "first_time":
        return "Yes"
    if address_change_requests >= 1 or customer_type == "first_time":
        return "Yes"
    return "No"


def _compute_lock_early(
    customer_type: str,
    discount_used: int,
    address_change_requests: int,
    past_cancels: int,
    conservative: bool,
) -> str:
    """Determine if order should be locked early."""
    if conservative:
        if past_cancels >= 2 or address_change_requests >= 2:
            return "Yes"

    if (customer_type == "first_time" and discount_used == 1 and address_change_requests >= 1):
        return "Yes"
    if past_cancels >= 2:
        return "Yes"

    return "No"


def _build_explanation(
    window: int,
    upsell: str,
    strict_addr: str,
    lock: str,
    customer_type: str,
    discount_used: int,
    past_edits: int,
    shipping_speed: str,
    order_value: float,
    industry: str,
    enable_upsell: bool,
) -> str:
    """Build short explanation (top 2 reasons) for the recommendations."""
    reasons: list[str] = []

    # Window reasons
    if customer_type == "vip":
        reasons.append("VIP: shorter window")
    if customer_type == "first_time" and discount_used == 1:
        reasons.append("First-time + discount: extended window")
    if past_edits >= 2:
        reasons.append("High past edits: extended window")
    if shipping_speed == "express":
        reasons.append("Express shipping: shorter window")

    # Upsell reasons
    if upsell == "Yes" and enable_upsell:
        if shipping_speed == "express":
            pass  # wouldn't be Yes
        elif order_value >= 80 and customer_type != "first_time":
            reasons.append("High value + returning: upsell")
        elif industry == "Apparel" and order_value >= 60:
            reasons.append("Apparel threshold: upsell")
        elif industry == "Electronics" and order_value >= 120:
            reasons.append("Electronics threshold: upsell")

    # Lock / strict reasons
    if lock == "Yes":
        reasons.append("Lock early: fraud-risk")
    if strict_addr == "Yes":
        reasons.append("Strict address: risk factors")

    return "; ".join(reasons[:2]) if reasons else "Standard rules applied"


def recommendations(
    df: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Compute recommendations for each order using deterministic rules.

    Args:
        df: DataFrame with required schema.
        config: Dict with keys:
            - base_window (int)
            - conservative (bool)
            - enable_upsell (bool)
            - industry (str)

    Returns:
        Tuple of (DataFrame with recommendations, summary dict).
    """
    base = int(config.get("base_window", 15))
    conservative = bool(config.get("conservative", False))
    enable_upsell = bool(config.get("enable_upsell", True))
    industry = str(config.get("industry", "Apparel"))

    if df is None or df.empty:
        empty_df = pd.DataFrame()
        return empty_df, {
            "total_orders": 0,
            "pct_upsell": 0.0,
            "avg_window": 0.0,
            "pct_lock_early": 0.0,
            "pct_strict_addr": 0.0,
        }

    # Safely access columns with defaults
    customer_type = df["customer_type"].fillna("first_time").astype(str).str.lower()
    order_value = pd.to_numeric(df["order_value"], errors="coerce").fillna(0)
    discount_used = pd.to_numeric(df["discount_used"], errors="coerce").fillna(0).astype(int)
    past_edits = pd.to_numeric(df["past_edits"], errors="coerce").fillna(0).astype(int)
    past_cancels = pd.to_numeric(df["past_cancels"], errors="coerce").fillna(0).astype(int)
    shipping_speed = df["shipping_speed"].fillna("standard").astype(str).str.lower()
    minutes_since = pd.to_numeric(df["minutes_since_checkout"], errors="coerce").fillna(0).astype(int)
    addr_changes = pd.to_numeric(df["address_change_requests"], errors="coerce").fillna(0).astype(int)

    # Compute per-row
    windows = []
    upsells = []
    strict_addrs = []
    lock_earlys = []
    explanations = []

    for i in range(len(df)):
        ct = customer_type.iloc[i] if i < len(customer_type) else "first_time"
        ov = float(order_value.iloc[i]) if i < len(order_value) else 0.0
        du = int(discount_used.iloc[i]) if i < len(discount_used) else 0
        pe = int(past_edits.iloc[i]) if i < len(past_edits) else 0
        pc = int(past_cancels.iloc[i]) if i < len(past_cancels) else 0
        ss = str(shipping_speed.iloc[i]) if i < len(shipping_speed) else "standard"
        ac = int(addr_changes.iloc[i]) if i < len(addr_changes) else 0

        w = _compute_window(base, ct, du, pe, ss)
        u = _compute_upsell(ov, ct, ss, industry, enable_upsell)
        sa = _compute_strict_address(ac, ct, conservative)
        le = _compute_lock_early(ct, du, ac, pc, conservative)
        exp = _build_explanation(
            w, u, sa, le, ct, du, pe, ss, ov, industry, enable_upsell
        )

        windows.append(w)
        upsells.append(u)
        strict_addrs.append(sa)
        lock_earlys.append(le)
        explanations.append(exp)

    out = df.copy()
    out["suggested_edit_window_minutes"] = windows
    out["show_upsell"] = upsells
    out["strict_address_validation"] = strict_addrs
    out["lock_order_early"] = lock_earlys
    out["explanation"] = explanations

    # Window expired
    out["window_expired"] = minutes_since > np.array(windows)

    # Summary
    n = len(out)
    summary = {
        "total_orders": n,
        "pct_upsell": (out["show_upsell"] == "Yes").sum() / n * 100 if n else 0.0,
        "avg_window": float(out["suggested_edit_window_minutes"].mean()) if n else 0.0,
        "pct_lock_early": (out["lock_order_early"] == "Yes").sum() / n * 100 if n else 0.0,
        "pct_strict_addr": (out["strict_address_validation"] == "Yes").sum() / n * 100 if n else 0.0,
    }

    return out, summary
