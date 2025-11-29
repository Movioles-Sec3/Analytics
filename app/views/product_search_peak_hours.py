"""
Product Search Peak Hours View
==============================
Streamlit section that visualizes product search usage throughout the day.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from app.pipelines.product_search_peak_hours import run_product_search_peak_hours_etl


def _summary_dict(df_summary: Optional[pd.DataFrame]) -> Dict[str, Any]:
    if df_summary is None or df_summary.empty:
        return {}
    return dict(zip(df_summary["metric"], df_summary["value"]))


def _fmt_int(value: Any) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _fmt_percent(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str) and value.strip().endswith("%"):
        return value
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return None


def render_product_search_peak_hours() -> None:
    """Render the product search peak hours analysis in the dashboard."""
    st.header("🔎 Product Search Peak Hours")
    st.markdown("**Question:** *What time of day do users most frequently use the search function?*")

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    default_start = datetime(2025, 1, 1).date()
    default_end = datetime(2025, 12, 31).date()

    with col1:
        start_date = st.date_input("From (UTC)", value=default_start, key="product_search_from")

    with col2:
        end_date = st.date_input("To (UTC)", value=default_end, key="product_search_to")

    with col3:
        tz_str = st.text_input(
            "Timezone offset (minutes)",
            value="-300",
            help="Enter timezone offset in minutes. Example: -300 for UTC-5 (Bogotá).",
            key="product_search_timezone_offset",
        )

    with col4:
        force_refresh = st.checkbox(
            "Force refresh",
            value=False,
            help="Bypass cached responses.",
            key="product_search_force_refresh",
        )

    if end_date < start_date:
        st.warning("'To' date must be on or after 'From' date.")
        return

    try:
        tz_offset = int(tz_str) if tz_str.strip() else 0
    except ValueError:
        st.warning("Timezone offset must be an integer (minutes). Using 0.")
        tz_offset = 0

    try:
        frames = run_product_search_peak_hours_etl(
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date, datetime.max.time()),
            timezone_offset_minutes=tz_offset,
            force_refresh=bool(force_refresh),
        )
    except Exception as exc:
        st.error(f"❌ Error running search peak hours ETL: {exc}")
        return

    df_hourly = frames.get("hourly")
    df_summary = frames.get("summary")

    if df_hourly is None or df_hourly.empty:
        st.warning("No search data available for the selected period.")
        return

    summary = _summary_dict(df_summary)

    st.subheader("📊 Summary Metrics")
    metric_cols = st.columns(4)

    with metric_cols[0]:
        total_searches = _fmt_int(summary.get("total_searches"))
        st.metric("Total searches", total_searches if total_searches is not None else "N/A")

    with metric_cols[1]:
        peak_hours_text = summary.get("peak_hours", "")
        st.metric("Peak hours", peak_hours_text if peak_hours_text else "N/A")

    with metric_cols[2]:
        busiest_hour = None
        if "peak_hours" in summary and summary["peak_hours"]:
            try:
                busiest_hour = summary["peak_hours"].split(",")[0].strip()
            except Exception:
                busiest_hour = None
        if busiest_hour:
            st.metric("Busiest hour", busiest_hour)
        else:
            st.metric("Busiest hour", "N/A")

    with metric_cols[3]:
        peak_percent = _fmt_percent(summary.get("peak_hours_percentage"))
        st.metric("Share in peak hours", peak_percent if peak_percent else "N/A")

    with st.expander("📋 Full summary", expanded=False):
        st.dataframe(df_summary, hide_index=True, use_container_width=True)

    st.subheader("📈 Searches by Hour")

    plot_df = df_hourly.copy()
    plot_df["hour_label"] = plot_df["hour"].apply(lambda h: f"{int(h):02d}:00")
    if "is_peak" in plot_df.columns:
        plot_df["type"] = plot_df["is_peak"].apply(lambda flag: "Peak hour" if flag else "Normal hour")
    else:
        plot_df["type"] = "Normal hour"

    bar_colors = {"Peak hour": "#FF6B6B", "Normal hour": "#4ECDC4"}
    fig_hour = px.bar(
        plot_df,
        x="hour",
        y="search_count",
        color="type",
        color_discrete_map=bar_colors,
        text="search_count",
        labels={"hour": "Hour of day (24h)", "search_count": "Searches", "type": "Hour type"},
        title="Search volume distribution throughout the day",
        height=500,
    )
    fig_hour.update_traces(textposition="outside")
    fig_hour.update_layout(xaxis=dict(tickmode="linear", tick0=0, dtick=1))
    st.plotly_chart(fig_hour, use_container_width=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 🥧 Share of searches by hour")
        if "percentage" in plot_df.columns:
            fig_pie = px.pie(
                plot_df,
                values="search_count",
                names="hour_label",
                hole=0.4,
                title="Percentage of searches per hour",
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Percentage data not available.")

    with col_right:
        st.markdown("### 🔥 Heatmap")
        heat_matrix = plot_df[["hour", "search_count"]].set_index("hour").T
        fig_heatmap = px.imshow(
            heat_matrix,
            labels={"x": "Hour of day", "color": "Searches"},
            x=[f"{int(h):02d}:00" for h in heat_matrix.columns],
            color_continuous_scale="YlOrRd",
            text_auto=True,
        )
        fig_heatmap.update_layout(height=220)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    st.subheader("🔝 Peak hour details")
    peak_rows = plot_df[plot_df["type"] == "Peak hour"].copy()
    if peak_rows.empty:
        st.info("No peak hours reported for the selected period.")
    else:
        columns = ["hour_label", "search_count"]
        if "percentage" in peak_rows.columns:
            columns.append("percentage")
        peak_table = peak_rows[columns]
        renamed = {
            "hour_label": "Hour",
            "search_count": "Searches",
            "percentage": "Percentage (%)",
        }
        peak_table = peak_table.rename(columns=renamed)
        st.dataframe(peak_table, hide_index=True, use_container_width=True)

    st.subheader("📥 Export data")
    export_cols = st.columns(2)
    with export_cols[0]:
        st.download_button(
            "Download hourly distribution (CSV)",
            data=df_hourly.to_csv(index=False),
            file_name=f"product_search_peak_hours_hourly_{datetime.utcnow():%Y%m%d}.csv",
            mime="text/csv",
        )
    with export_cols[1]:
        if df_summary is not None and not df_summary.empty:
            st.download_button(
                "Download summary (CSV)",
                data=df_summary.to_csv(index=False),
                file_name=f"product_search_peak_hours_summary_{datetime.utcnow():%Y%m%d}.csv",
                mime="text/csv",
            )

