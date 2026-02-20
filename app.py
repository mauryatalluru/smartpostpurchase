"""
Smart Post-Purchase Rules - OrderEditing companion demo.
Main Streamlit application entry point.
"""

import pandas as pd
import streamlit as st

from data import (
    REQUIRED_COLUMNS,
    generate_synthetic_orders,
    validate_schema,
    normalize_uploaded_df,
    get_example_csv_content,
)
from logic import recommendations
from ui import (
    render_sidebar,
    render_title_and_description,
    render_kpis,
    render_data_preview,
    render_recommendations_table,
    render_detail_panel,
    render_export_button,
    render_self_check,
)


def _get_or_create_data() -> tuple[pd.DataFrame, str]:
    """
    Determine data source: synthetic or CSV upload.
    Returns (df, source) where source is 'synthetic' or 'upload'.
    """
    if "synthetic_df" not in st.session_state:
        st.session_state.synthetic_df = generate_synthetic_orders(200, 42)

    source = st.radio(
        "Data source",
        options=["Generate synthetic dataset", "Upload CSV"],
        index=0,
        key="data_source_radio",
        horizontal=True,
    )

    if source == "Generate synthetic dataset":
        if st.button("Generate synthetic data", key="btn_generate_synthetic"):
            st.session_state.synthetic_df = generate_synthetic_orders(200, 42)
            st.rerun()
        return st.session_state.synthetic_df, "synthetic"

    # CSV upload path
    uploaded = st.file_uploader("Upload CSV", type=["csv"], key="csv_uploader")
    if uploaded is None:
        st.info("Upload a CSV file or switch to synthetic data.")
        return pd.DataFrame(), "upload"

    try:
        raw_df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Could not parse CSV: {e}")
        return pd.DataFrame(), "upload"

    if raw_df.empty:
        st.warning("Uploaded CSV is empty.")
        return pd.DataFrame(), "upload"

    # Check if columns already match
    if all(c in raw_df.columns for c in REQUIRED_COLUMNS):
        norm_df = normalize_uploaded_df(raw_df, {c: c for c in REQUIRED_COLUMNS})
        valid, errs = validate_schema(norm_df)
        if valid:
            return norm_df, "upload"
        for err in errs:
            st.error(err)
        st.download_button(
            "Download example template",
            data=get_example_csv_content(),
            file_name="order_template.csv",
            mime="text/csv",
            key="download_template_btn",
        )
        return pd.DataFrame(), "upload"

    # Show mapping UI
    st.subheader("Column mapping")
    st.caption("Map your CSV columns to the expected schema.")
    upload_cols = ["(Skip)"] + list(raw_df.columns)
    column_map: dict[str, str] = {}

    for internal in REQUIRED_COLUMNS:
        idx = 0
        if internal in raw_df.columns:
            try:
                idx = upload_cols.index(internal)
            except ValueError:
                pass
        chosen = st.selectbox(
            f"{internal}",
            options=upload_cols,
            index=idx,
            key=f"map_{internal}",
        )
        if chosen and chosen != "(Skip)":
            column_map[internal] = chosen

    missing = [c for c in REQUIRED_COLUMNS if c not in column_map]
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        st.download_button(
            "Download example template",
            data=get_example_csv_content(),
            file_name="order_template.csv",
            mime="text/csv",
            key="download_template_btn2",
        )
        return pd.DataFrame(), "upload"

    norm_df = normalize_uploaded_df(raw_df, column_map)
    valid, errs = validate_schema(norm_df)
    if not valid:
        for err in errs:
            st.error(err)
        return pd.DataFrame(), "upload"

    return norm_df, "upload"


def _inject_icon_fix_css() -> None:
    """Hide broken Material icon text when font fails to load (e.g. corporate network)."""
    st.markdown(
        """
        <style>
        /* Hide icon names that show as text when Material font doesn't load */
        [class*="material-symbols"],
        [class*="MaterialSymbols"],
        .stMaterialSymbolsRounded {
            font-size: 0 !important;
            line-height: 0 !important;
            overflow: hidden !important;
            opacity: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Main application entry point."""
    st.set_page_config(page_title="Smart Post-Purchase Rules", layout="wide")
    _inject_icon_fix_css()

    config: dict = {
        "base_window": 15,
        "conservative": False,
        "enable_upsell": True,
        "industry": "Apparel",
    }
    config = render_sidebar(config)

    render_title_and_description()

    # Data source section - only show when not in mapping flow
    df = _get_or_create_data()[0]

    if df.empty:
        st.stop()

    # Compute recommendations
    try:
        df_rec, summary = recommendations(df, config)
    except Exception as e:
        st.error(f"Recommendation error: {e}")
        st.stop()

    if df_rec.empty:
        st.warning("No recommendations generated.")
        st.stop()

    render_kpis(summary)
    render_data_preview(df, "Data preview")

    # Filters for recommendations table
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_customer = st.selectbox(
            "Filter by customer_type",
            options=["All", "first_time", "repeat", "vip"],
            key="filter_customer_type",
        )
    with col2:
        filter_upsell = st.selectbox(
            "Filter by show_upsell",
            options=["All", "Yes", "No"],
            key="filter_upsell",
        )
    with col3:
        sort_asc = st.checkbox("Sort window ascending", value=False, key="sort_asc")

    selected_order = render_recommendations_table(
        df_rec, filter_customer, filter_upsell, sort_asc
    )
    if selected_order:
        render_detail_panel(df_rec, selected_order)

    render_export_button(df_rec)
    render_self_check(df_rec)


if __name__ == "__main__":
    main()
