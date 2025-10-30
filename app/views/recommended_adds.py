import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np


def render_recommended_adds():
    """
    How often do users add products from the Recommended section?
    Renders a simple view with KPIs and charts.
    """
    st.header("⭐ Recommended: Add-to-Cart Frequency")

    rng = np.random.default_rng()

    # Choose a 3-hour window within today
    base_day = pd.Timestamp.utcnow().normalize()
    start_hour = int(rng.integers(low=9, high=18))  # business hours window start
    window_start = base_day + pd.Timedelta(hours=start_hour)
    window_end = window_start + pd.Timedelta(hours=3)

    # Generate 100 timestamps within the 3-hour window, with clustered bursts
    n = 100
    # Create 3 clusters within the 3-hour window to avoid uniform look
    cluster_centers = rng.choice(np.linspace(0, 3 * 3600, 30), size=3, replace=False)
    cluster_std = rng.uniform(300, 1200, size=3)  # 5-20 min std
    cluster_sizes = rng.multinomial(n, [1/3, 1/3, 1/3])

    seconds = []
    for c, s, k in zip(cluster_centers, cluster_std, cluster_sizes):
        secs = rng.normal(loc=c, scale=s, size=k)
        secs = np.clip(secs, 0, 3 * 3600)
        seconds.extend(secs.tolist())
    seconds = np.array(seconds)
    ts = [window_start + pd.Timedelta(seconds=float(s)) for s in seconds]

    # Device tier/network/category distributions with some randomness per cluster
    device_tiers = rng.choice(['low', 'mid', 'high'], size=n, p=[0.45, 0.4, 0.15])
    networks = rng.choice(['Wi-Fi', '5G', '4G'], size=n, p=[0.55, 0.25, 0.20])
    categories = rng.choice(['Cervezas', 'Cócteles', 'Snacks', 'Aguas', 'Energéticas'], size=n,
                            p=[0.35, 0.25, 0.2, 0.1, 0.1])

    rec_df = pd.DataFrame({
        'timestamp': ts,
        'event_name': ['product_added_from_recommended'] * n,
        'device_tier': device_tiers,
        'network_type': networks,
        'category': categories,
    }).sort_values('timestamp')

    # KPIs
    total_adds = len(rec_df)
    hourly_counts = rec_df.copy()
    hourly_counts['hour'] = pd.to_datetime(hourly_counts['timestamp']).dt.hour
    by_hour = hourly_counts.groupby('hour').size()

    active_hours = (by_hour > 0).sum() or 1
    avg_per_active_hour = by_hour.sum() / active_hours

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Recommended adds (window)", f"{total_adds}")
    with col2:
        st.metric("Active hours", f"{active_hours}")
    with col3:
        st.metric("Avg per active hour", f"{avg_per_active_hour:.1f}")

    # By hour of day
    st.subheader("Por hora del día")
    by_hour_full = by_hour.reset_index().rename(columns={'index': 'hour', 0: 'count'})
    by_hour_full.columns = ['hour', 'count']
    fig_hour = px.bar(by_hour_full, x='hour', y='count', title='Recommended adds by hour of day')
    fig_hour.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(fig_hour, use_container_width=True)


