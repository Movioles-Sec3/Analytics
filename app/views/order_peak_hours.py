"""
Order Peak Hours Dashboard View
================================
Renders visualization and analysis of order peak hours.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path

from app.pipelines.order_peak_hours import run_order_peak_hours_etl


def render_order_peak_hours():
    """
    Render the Order Peak Hours analysis section.
    Displays order volume distribution by hour and identifies peak hours.
    """
    st.header("🕐 Order Peak Hours Analysis")
    st.markdown("**Question**: *At what hours is the peak of orders?*")
    
    # Parameter controls
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        current_date = datetime.utcnow().date()
        start_date = st.date_input("From (UTC)", value=current_date)
    
    with col2:
        end_date = st.date_input("To (UTC)", value=current_date)
    
    with col3:
        tz_str = st.text_input(
            "Timezone offset (minutes)", 
            value="-300", 
            placeholder="e.g., -300 for UTC-5",
            help="Enter timezone offset in minutes. Example: -300 for UTC-5 (Colombia)"
        )
    
    with col4:
        force_refresh = st.checkbox(
            "Force refresh", 
            value=False, 
            help="Ignore cache and reload data"
        )
    
    # Validate dates
    if end_date < start_date:
        st.warning("'To' date must be on or after 'From' date.")
        return
    
    # Parse timezone offset
    try:
        tz_offset = int(tz_str) if tz_str.strip() else 0
    except ValueError:
        st.warning("Timezone offset must be an integer (minutes). Using 0.")
        tz_offset = 0
    
    # Run ETL pipeline
    try:
        frames = run_order_peak_hours_etl(
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date, datetime.max.time()),
            timezone_offset_minutes=tz_offset,
            force_refresh=bool(force_refresh),
            fallback_to_local=True
        )
    except Exception as e:
        st.error(f"❌ Error running Order Peak Hours ETL: {e}")
        return
    
    df_hourly = frames.get("hourly")
    df_summary = frames.get("summary")
    
    if df_hourly is None or df_hourly.empty:
        st.warning("No order data available for the selected period.")
        return
    
    # Display summary metrics
    st.subheader("📊 Summary Metrics")
    
    if df_summary is not None and not df_summary.empty:
        # Create metrics from summary data
        metrics_dict = dict(zip(df_summary['metric'], df_summary['value']))
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Orders", 
                metrics_dict.get('Total Orders', 'N/A')
            )
        
        with col2:
            st.metric(
                "Busiest Hour",
                f"{metrics_dict.get('Busiest Hour', 'N/A')}:00"
            )
        
        with col3:
            st.metric(
                "Peak Hour Orders",
                metrics_dict.get('Busiest Hour Orders', 'N/A')
            )
        
        with col4:
            st.metric(
                "Peak Hours Coverage",
                metrics_dict.get('Percentage in Peak Hours', 'N/A')
            )
        
        # Display full summary table
        with st.expander("📋 Detailed Summary", expanded=False):
            st.dataframe(df_summary, use_container_width=True, hide_index=True)
    
    # Main visualization: Hourly order distribution
    st.subheader("📈 Order Volume by Hour")
    
    # Prepare data for visualization
    df_plot = df_hourly.copy()
    df_plot['hour_label'] = df_plot['hour'].apply(lambda h: f"{int(h):02d}:00")
    
    # Determine peak vs non-peak coloring
    if 'is_peak' in df_plot.columns:
        df_plot['category'] = df_plot['is_peak'].apply(lambda x: 'Peak Hour' if x else 'Normal Hour')
        color_col = 'category'
        color_map = {'Peak Hour': '#FF6B6B', 'Normal Hour': '#4ECDC4'}
    else:
        color_col = None
        color_map = None
    
    # Bar chart
    fig_hourly = px.bar(
        df_plot,
        x='hour',
        y='order_count',
        color=color_col,
        color_discrete_map=color_map,
        title='Order Distribution Throughout the Day',
        labels={
            'hour': 'Hour of Day',
            'order_count': 'Number of Orders',
            'category': 'Type'
        },
        text='order_count',
        height=500
    )
    
    fig_hourly.update_traces(textposition='outside')
    fig_hourly.update_layout(
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=1,
            title='Hour of Day (24h format)'
        ),
        yaxis_title='Number of Orders',
        showlegend=True if color_col else False,
        hovertemplate='<b>Hour</b>: %{x}:00<br><b>Orders</b>: %{y}<extra></extra>'
    )
    
    st.plotly_chart(fig_hourly, use_container_width=True)
    
    # Additional visualizations in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🥧 Order Distribution (Percentage)")
        
        if 'percentage' in df_plot.columns:
            fig_pie = px.pie(
                df_plot,
                values='order_count',
                names='hour_label',
                title='Orders by Hour (%)',
                hole=0.4
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Percentage data not available.")
    
    with col2:
        st.markdown("### 💰 Revenue by Hour")
        
        if 'total_revenue' in df_plot.columns:
            fig_revenue = px.bar(
                df_plot,
                x='hour',
                y='total_revenue',
                title='Total Revenue by Hour',
                labels={
                    'hour': 'Hour of Day',
                    'total_revenue': 'Total Revenue (COP)'
                },
                color='total_revenue',
                color_continuous_scale='Viridis'
            )
            fig_revenue.update_layout(
                xaxis=dict(tickmode='linear', tick0=0, dtick=1),
                showlegend=False
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("Revenue data not available.")
    
    # Peak hours identification
    st.subheader("🔝 Peak Hours Identification")
    
    if 'is_peak' in df_plot.columns:
        peak_hours_df = df_plot[df_plot['is_peak']].sort_values('order_count', ascending=False)
        
        if not peak_hours_df.empty:
            st.markdown(f"""
            **Peak hours** are defined as the hours with the highest order volume 
            (top 25% percentile). The following hours are identified as peak:
            """)
            
            # Display peak hours with metrics
            peak_cols = st.columns(min(len(peak_hours_df), 4))
            for idx, (_, row) in enumerate(peak_hours_df.iterrows()):
                col_idx = idx % 4
                with peak_cols[col_idx]:
                    st.metric(
                        f"Hour {int(row['hour']):02d}:00",
                        f"{int(row['order_count'])} orders",
                        f"{row.get('percentage', 0):.1f}% of total"
                    )
            
            # Detailed table
            st.markdown("#### 📊 Peak Hours Details")
            display_cols = ['hour_label', 'order_count', 'percentage']
            if 'total_revenue' in peak_hours_df.columns:
                display_cols.append('total_revenue')
            if 'avg_order_value' in peak_hours_df.columns:
                display_cols.append('avg_order_value')
            
            peak_display = peak_hours_df[display_cols].copy()
            peak_display.columns = [
                'Hour', 'Orders', 'Percentage (%)', 
                'Revenue (COP)', 'Avg Order Value (COP)'
            ][:len(display_cols)]
            
            st.dataframe(peak_display, use_container_width=True, hide_index=True)
    
    # Heatmap visualization
    st.subheader("🔥 Order Volume Heatmap")
    
    # Create a simple heatmap representation
    hourly_matrix = df_plot[['hour', 'order_count']].set_index('hour').T
    
    fig_heatmap = px.imshow(
        hourly_matrix,
        labels=dict(x="Hour of Day", y="", color="Orders"),
        x=[f"{int(h):02d}:00" for h in hourly_matrix.columns],
        color_continuous_scale='YlOrRd',
        aspect='auto',
        text_auto=True
    )
    fig_heatmap.update_layout(height=200)
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Insights and recommendations
    st.subheader("💡 Insights & Recommendations")
    
    if not df_hourly.empty:
        busiest_hour = int(df_hourly.loc[df_hourly['order_count'].idxmax(), 'hour'])
        slowest_hour = int(df_hourly.loc[df_hourly['order_count'].idxmin(), 'hour'])
        max_orders = int(df_hourly['order_count'].max())
        min_orders = int(df_hourly['order_count'].min())
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            #### ⚠️ High Demand Periods
            - **Busiest hour**: {busiest_hour}:00 with {max_orders} orders
            - Consider increasing staff during peak hours
            - Prepare inventory for high-demand items
            - Optimize kitchen workflow for faster preparation
            """)
        
        with col2:
            st.markdown(f"""
            #### 💡 Optimization Opportunities
            - **Slowest hour**: {slowest_hour}:00 with {min_orders} orders
            - Run promotions during slow periods
            - Schedule maintenance during low-demand hours
            - Adjust staff schedules to match demand
            """)
    
    # Data export
    st.subheader("📥 Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        csv_hourly = df_hourly.to_csv(index=False)
        st.download_button(
            label="📊 Download Hourly Data (CSV)",
            data=csv_hourly,
            file_name=f"order_peak_hours_hourly_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        if df_summary is not None and not df_summary.empty:
            csv_summary = df_summary.to_csv(index=False)
            st.download_button(
                label="📋 Download Summary (CSV)",
                data=csv_summary,
                file_name=f"order_peak_hours_summary_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
