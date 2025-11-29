"""
Most Requested Categories View
==============================
Streamlit section displaying the product categories most requested by users.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from app.pipelines.most_requested_categories import run_most_requested_categories_etl


def _summary_dict(df_summary: Optional[pd.DataFrame]) -> Dict[str, Any]:
    if df_summary is None or df_summary.empty:
        return {}
    return dict(zip(df_summary["metric"], df_summary["value"]))


def _fmt_int(value: Any) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _fmt_float(value: Any, decimals: int = 1) -> Optional[str]:
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return None


def _fmt_currency(value: Any) -> Optional[str]:
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return None


def render_most_requested_categories() -> None:
    """Render the most requested categories panel."""
    st.header("🏆 Most Requested Categories")
    st.markdown("**Question:** *What are the most requested categories by users?*")

    col1, col2, col3 = st.columns([1, 1, 1])

    default_start = datetime(2025, 1, 1).date()
    default_end = datetime(2025, 12, 31).date()

    with col1:
        start_date = st.date_input(
            "From (UTC)",
            value=default_start,
            key="most_requested_from",
        )

    with col2:
        end_date = st.date_input(
            "To (UTC)",
            value=default_end,
            key="most_requested_to",
        )

    with col3:
        limit = st.number_input(
            "Top categories",
            min_value=1,
            max_value=50,
            value=5,
            step=1,
            key="most_requested_limit",
        )

    col_refresh = st.columns([1, 3])[0]
    with col_refresh:
        force_refresh = st.checkbox(
            "Force refresh",
            value=False,
            help="Ignore cached response and query backend.",
            key="most_requested_force_refresh",
        )

    if end_date < start_date:
        st.warning("'To' date must be on or after 'From' date.")
        return

    try:
        frames = run_most_requested_categories_etl(
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date, datetime.max.time()),
            limit=int(limit),
            force_refresh=bool(force_refresh),
        )
    except Exception as exc:
        st.error(f"❌ Error fetching categories: {exc}")
        return

    df_categories = frames.get("categories")
    df_summary = frames.get("summary")

    if df_categories is None or df_categories.empty:
        st.warning("No category data available for the selected period.")
        return

    summary = _summary_dict(df_summary)

    st.subheader("📊 Summary Metrics")
    metrics_row = st.columns(4)

    with metrics_row[0]:
        total_orders = _fmt_int(summary.get("total_orders"))
        st.metric("Total orders (period)", total_orders if total_orders is not None else "N/A")

    with metrics_row[1]:
        top_category = summary.get("top_category_name") or "N/A"
        st.metric("Top category", top_category)

    with metrics_row[2]:
        top_orders = _fmt_int(summary.get("top_category_orders"))
        st.metric("Orders (top category)", top_orders if top_orders is not None else "N/A")

    with metrics_row[3]:
        top_share = _fmt_float(summary.get("top_category_share"), 1)
        st.metric("Share (top category)", f"{top_share}%" if top_share is not None else "N/A")

    with st.expander("📋 Full summary", expanded=False):
        st.dataframe(df_summary, hide_index=True, use_container_width=True)

    st.subheader("🏅 Ranking by Orders")
    plot_df = df_categories.copy()
    plot_df["orders_percentage"] = pd.to_numeric(plot_df.get("orders_percentage"), errors="coerce")

    fig_orders = px.bar(
        plot_df,
        x="total_orders",
        y="categoria_nombre",
        orientation="h",
        text="total_orders",
        title="Top categories by number of orders",
        labels={"total_orders": "Orders", "categoria_nombre": "Category"},
        color="total_orders",
        color_continuous_scale="Blues",
    )
    fig_orders.update_traces(textposition="outside")
    fig_orders.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_orders, use_container_width=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 📦 Units sold per category")
        if "total_units" in plot_df.columns:
            fig_units = px.bar(
                plot_df,
                x="categoria_nombre",
                y="total_units",
                text="total_units",
                labels={"categoria_nombre": "Category", "total_units": "Units"},
                title="Total units sold",
            )
            fig_units.update_traces(textposition="outside")
            fig_units.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig_units, use_container_width=True)
        else:
            st.info("Units data not available.")

    with col_right:
        st.markdown("### 💰 Revenue share")
        if "total_revenue" in plot_df.columns:
            revenue_df = plot_df.copy()
            revenue_df["label"] = revenue_df["categoria_nombre"].astype(str)
            revenue_df["value"] = pd.to_numeric(revenue_df["total_revenue"], errors="coerce")
            fig_revenue = px.pie(
                revenue_df,
                values="value",
                names="label",
                hole=0.35,
                title="Revenue contribution",
            )
            fig_revenue.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("Revenue data not available.")

    st.subheader("📋 Detailed table")
    display_df = df_categories.copy()
    if "total_revenue" in display_df.columns:
        display_df["total_revenue"] = display_df["total_revenue"].apply(_fmt_currency)

    st.dataframe(display_df, hide_index=True, use_container_width=True)

    st.subheader("📥 Export data")
    col_export_1, col_export_2 = st.columns(2)
    with col_export_1:
        st.download_button(
            "Download categories (CSV)",
            data=df_categories.to_csv(index=False),
            file_name=f"most_requested_categories_{datetime.utcnow():%Y%m%d}.csv",
            mime="text/csv",
        )
    with col_export_2:
        if df_summary is not None and not df_summary.empty:
            st.download_button(
                "Download summary (CSV)",
                data=df_summary.to_csv(index=False),
                file_name=f"most_requested_categories_summary_{datetime.utcnow():%Y%m%d}.csv",
                mime="text/csv",
            )


