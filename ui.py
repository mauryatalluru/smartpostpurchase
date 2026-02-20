"""
UI components for Smart Post-Purchase Rules demo.
"""

from typing import Any, Optional
import pandas as pd
import streamlit as st


def render_sidebar(config: dict[str, Any]) -> dict[str, Any]:
    """
    Render sidebar controls and return updated config.

    Returns:
        Config dict with base_window, conservative, enable_upsell, industry.
    """
    with st.sidebar:
        st.header("Controls")
        config["base_window"] = st.slider(
            "Edit window base (minutes)",
            min_value=5,
            max_value=60,
            value=int(config.get("base_window", 15)),
            key="sidebar_base_window",
        )
        config["conservative"] = st.toggle(
            "Conservative mode",
            value=bool(config.get("conservative", False)),
            key="sidebar_conservative",
        )
        config["enable_upsell"] = st.toggle(
            "Enable upsell logic",
            value=bool(config.get("enable_upsell", True)),
            key="sidebar_enable_upsell",
        )
        industry_options = ("Apparel", "Beauty", "Electronics", "Supplements")
        idx = industry_options.index(config.get("industry", "Apparel")) if config.get("industry") in industry_options else 0
        config["industry"] = st.selectbox(
            "Industry",
            options=industry_options,
            index=idx,
            key="sidebar_industry",
        )
    return config


def render_title_and_description() -> None:
    """Render main page title and 2-line description."""
    st.title("Smart Post-Purchase Rules")
    st.markdown(
        "OrderEditing companion demo: compute explainable recommendations for edit windows, "
        "upsells, address validation, and early locking."
    )
    st.markdown(
        "Uses deterministic rules (no ML). Upload your own CSV or generate synthetic data."
    )


def render_kpis(summary: dict[str, Any]) -> None:
    """Render KPI metrics at top."""
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total orders", summary.get("total_orders", 0))
    with c2:
        st.metric("% orders recommended upsell", f"{summary.get('pct_upsell', 0):.1f}%")
    with c3:
        st.metric("Avg suggested edit window", f"{summary.get('avg_window', 0):.1f} min")
    with c4:
        st.metric("% orders flagged lock early", f"{summary.get('pct_lock_early', 0):.1f}%")
    with c5:
        st.metric("% orders strict address validation", f"{summary.get('pct_strict_addr', 0):.1f}%")


def render_data_preview(df: pd.DataFrame, title: str = "Data preview") -> None:
    """Render a compact data preview table."""
    if df is None or df.empty:
        st.info("No data to preview.")
        return
    st.subheader(title)
    display_cols = [c for c in df.columns if c not in ("explanation",)]
    st.dataframe(df[display_cols].head(10), use_container_width=True, hide_index=True)


def render_recommendations_table(
    df: pd.DataFrame,
    filter_customer: Optional[str],
    filter_upsell: Optional[str],
    sort_asc: bool,
) -> Optional[str]:
    """
    Render recommendations table with filters and sort.
    Returns selected order_id for drill-down, or None.
    """
    if df is None or df.empty:
        st.info("No recommendations to show.")
        return None

    rec_cols = [
        "order_id",
        "customer_type",
        "order_value",
        "suggested_edit_window_minutes",
        "show_upsell",
        "strict_address_validation",
        "lock_order_early",
        "window_expired",
    ]
    rec_cols = [c for c in rec_cols if c in df.columns]
    work = df[rec_cols].copy()

    if filter_customer and filter_customer != "All":
        work = work[work["customer_type"] == filter_customer]
    if filter_upsell and filter_upsell != "All":
        work = work[work["show_upsell"] == filter_upsell]

    work = work.sort_values(
        "suggested_edit_window_minutes", ascending=sort_asc
    ).reset_index(drop=True)

    st.subheader("Recommendations")
    st.dataframe(work, use_container_width=True, hide_index=True)

    order_ids = ["(Select an order)"] + list(df["order_id"].astype(str).unique())
    selected = st.selectbox(
        "Select order for details",
        options=order_ids,
        key="drill_down_order_select",
    )
    if selected and selected != "(Select an order)":
        return selected
    return None


def render_detail_panel(
    df: pd.DataFrame,
    order_id: str,
) -> None:
    """Render row-level drill-down panel for selected order."""
    if df is None or df.empty or not order_id:
        return

    row = df[df["order_id"].astype(str) == str(order_id)]
    if row.empty:
        st.warning(f"Order {order_id} not found.")
        return

    row = row.iloc[0]

    st.subheader("Order details")
    with st.expander("Raw fields", expanded=True):
        raw_cols = [
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
        for col in raw_cols:
            if col in row.index:
                st.text(f"{col}: {row[col]}")

    with st.expander("Recommended actions", expanded=True):
        for col in ["suggested_edit_window_minutes", "show_upsell", "strict_address_validation", "lock_order_early"]:
            if col in row.index:
                st.text(f"{col}: {row[col]}")
        if "window_expired" in row.index:
            st.text(f"window_expired: {row['window_expired']}")

    if "explanation" in row.index:
        st.info(f"**Explanation:** {row['explanation']}")


def render_export_button(df: pd.DataFrame) -> None:
    """Add download button for recommendations CSV."""
    if df is None or df.empty:
        return
    csv = df.to_csv(index=False)
    st.download_button(
        "Download recommendations as CSV",
        data=csv,
        file_name="recommendations.csv",
        mime="text/csv",
        key="export_csv_btn",
    )


def render_self_check(df: pd.DataFrame) -> None:
    """Run quick validations in a collapsible section."""
    with st.expander("Self-check", expanded=False):
        errors: list[str] = []
        if df is None or df.empty:
            errors.append("No data to validate.")
        else:
            required = [
                "order_id",
                "customer_type",
                "order_value",
                "suggested_edit_window_minutes",
                "show_upsell",
                "strict_address_validation",
                "lock_order_early",
            ]
            for col in required:
                if col not in df.columns:
                    errors.append(f"Missing output column: {col}")
                elif df[col].isna().any():
                    errors.append(f"Nulls in required column: {col}")

            if "suggested_edit_window_minutes" in df.columns:
                win = df["suggested_edit_window_minutes"]
                if (win < 10).any() or (win > 30).any():
                    errors.append("Suggested window outside bounds [10, 30].")

        if errors:
            for e in errors:
                st.error(e)
        else:
            st.success("All checks passed.")
