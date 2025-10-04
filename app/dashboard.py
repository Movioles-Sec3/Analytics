"""
Analytics Dashboard for BQ13, BQ14, BQ4 & BQ5
==============================================
Dashboard interactivo para analizar tiempos de carga, pagos, pickup y reorders.

BQ13: P95 app loading time (open to usable menu) by device class and network
BQ14: P95 payment time (Pay tap to confirmed) by network type and device class
BQ4: Median pickup waiting time by peak vs off-peak hours
BQ5: Product categories re-order patterns by time

Usage:
    streamlit run app/dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import os
import sys
try:
    from app.pipelines.bq5 import run_bq5_etl
except ModuleNotFoundError:
    # Ensure project root is on sys.path when running as a script
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from app.pipelines.bq5 import run_bq5_etl

# Configuración de página
st.set_page_config(
    page_title="Analytics Dashboard - BQ13, BQ14, BQ4 & BQ5",
    page_icon="📊",
    layout="wide"
)

def load_data(file_path):
    """Carga y parsea el archivo CSV"""
    try:
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"❌ Error cargando archivo: {e}")
        return None

def calculate_p95(series):
    """Calcula percentil 95"""
    return np.percentile(series.dropna(), 95) if len(series.dropna()) > 0 else 0

def format_duration(ms):
    """Formatea milisegundos a formato legible"""
    if ms < 1000:
        return f"{ms:.0f}ms"
    else:
        return f"{ms/1000:.2f}s"

def load_pickup_data(file_path):
    """Carga y parsea el archivo CSV de compras"""
    try:
        df = pd.read_csv(file_path)
        df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'])
        df['fecha_listo'] = pd.to_datetime(df['fecha_listo'])
        df['fecha_entregado'] = pd.to_datetime(df['fecha_entregado'])
        return df
    except Exception as e:
        st.error(f"❌ Error cargando archivo: {e}")
        return None

def classify_peak_hours(hour):
    """Clasifica horas como pico o valle"""
    if (12 <= hour < 14) or (19 <= hour < 21):
        return 'Peak'
    else:
        return 'Off-Peak'

def get_meal_period(hour):
    """Identifica el periodo de comida"""
    if 6 <= hour < 11:
        return 'Breakfast'
    elif 11 <= hour < 15:
        return 'Lunch'
    elif 15 <= hour < 18:
        return 'Snack'
    elif 18 <= hour < 22:
        return 'Dinner'
    else:
        return 'Late Night'

def format_time(seconds):
    """Formatea segundos a formato legible"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.2f}min"
    else:
        return f"{seconds/3600:.2f}h"

def bq13_analysis(df):
    """
    BQ13: P95 app loading time (from open to usable menu) 
    across device classes and network conditions
    """
    st.header("📱 BQ13: App Loading Time (P95)")
    st.markdown("**Pregunta**: *¿Cuál es el tiempo P95 de carga de la app (desde apertura hasta menú usable) por clase de dispositivo y condiciones de red?*")
    
    # Filtrar eventos app_launch_to_menu
    launch_df = df[df['event_name'] == 'app_launch_to_menu'].copy()
    
    if len(launch_df) == 0:
        st.warning("⚠️ No hay eventos 'app_launch_to_menu' en los datos.")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total eventos", len(launch_df))
    with col2:
        avg_time = launch_df['duration_ms'].mean()
        st.metric("Tiempo promedio", format_duration(avg_time))
    with col3:
        p95_overall = calculate_p95(launch_df['duration_ms'])
        st.metric("P95 general", format_duration(p95_overall))
    
    # Comparación antes/después
    st.subheader("🔄 Comparación de Performance")
    enable_comparison = st.checkbox("Activar comparación Antes/Después", value=False)
    
    if enable_comparison:
        cutoff_date = st.date_input(
            "Fecha de corte (despliegue de optimización)",
            value=launch_df['timestamp'].median().date()
        )
        cutoff_datetime = pd.Timestamp(cutoff_date)
        
        before_df = launch_df[launch_df['timestamp'] < cutoff_datetime]
        after_df = launch_df[launch_df['timestamp'] >= cutoff_datetime]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Antes de Optimización")
            if len(before_df) > 0:
                p95_before = before_df.groupby(['device_tier', 'network_type'])['duration_ms'].apply(calculate_p95).reset_index()
                p95_before.columns = ['Device Tier', 'Network Type', 'P95 (ms)']
                p95_before['P95'] = p95_before['P95 (ms)'].apply(format_duration)
                
                fig = px.bar(
                    p95_before,
                    x='Device Tier',
                    y='P95 (ms)',
                    color='Network Type',
                    title=f"Antes ({len(before_df)} eventos)",
                    text='P95',
                    category_orders={'Device Tier': ['low', 'mid', 'high']},
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(p95_before, use_container_width=True, hide_index=True)
            else:
                st.warning("Sin datos antes de la fecha")
        
        with col2:
            st.markdown("### 📊 Después de Optimización")
            if len(after_df) > 0:
                p95_after = after_df.groupby(['device_tier', 'network_type'])['duration_ms'].apply(calculate_p95).reset_index()
                p95_after.columns = ['Device Tier', 'Network Type', 'P95 (ms)']
                p95_after['P95'] = p95_after['P95 (ms)'].apply(format_duration)
                
                fig = px.bar(
                    p95_after,
                    x='Device Tier',
                    y='P95 (ms)',
                    color='Network Type',
                    title=f"Después ({len(after_df)} eventos)",
                    text='P95',
                    category_orders={'Device Tier': ['low', 'mid', 'high']},
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(p95_after, use_container_width=True, hide_index=True)
            else:
                st.warning("Sin datos después de la fecha")
        
        # Análisis de mejora
        if len(before_df) > 0 and len(after_df) > 0:
            st.markdown("### 📈 Análisis de Mejora")
            merged = p95_before.merge(
                p95_after,
                on=['Device Tier', 'Network Type'],
                suffixes=(' (Antes)', ' (Después)')
            )
            merged['Mejora (ms)'] = merged['P95 (ms) (Antes)'] - merged['P95 (ms) (Después)']
            merged['Mejora (%)'] = (merged['Mejora (ms)'] / merged['P95 (ms) (Antes)'] * 100).round(2)
            
            st.dataframe(merged, use_container_width=True, hide_index=True)
    else:
        # Análisis estándar sin comparación
        st.subheader("📊 P95 por Device Tier y Network Type")
        
        p95_data = launch_df.groupby(['device_tier', 'network_type'])['duration_ms'].apply(calculate_p95).reset_index()
        p95_data.columns = ['Device Tier', 'Network Type', 'P95 (ms)']
        p95_data['P95'] = p95_data['P95 (ms)'].apply(format_duration)
        
        # Gráfico de barras
        fig = px.bar(
            p95_data,
            x='Device Tier',
            y='P95 (ms)',
            color='Network Type',
            title="P95 App Loading Time por Device Tier y Network",
            text='P95',
            category_orders={'Device Tier': ['low', 'mid', 'high']},
            color_discrete_sequence=px.colors.qualitative.Set2,
            height=500
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de datos
        st.dataframe(p95_data, use_container_width=True, hide_index=True)
        
        # Heatmap
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🔥 Heatmap de P95")
            pivot = p95_data.pivot(index='Device Tier', columns='Network Type', values='P95 (ms)')
            fig_heatmap = px.imshow(
                pivot,
                text_auto='.0f',
                aspect='auto',
                color_continuous_scale='YlOrRd',
                labels=dict(color="P95 (ms)")
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Distribución de Tiempos")
            fig_box = px.box(
                launch_df,
                x='device_tier',
                y='duration_ms',
                color='network_type',
                category_orders={'device_tier': ['low', 'mid', 'high']},
                labels={'duration_ms': 'Duration (ms)', 'device_tier': 'Device Tier'}
            )
            st.plotly_chart(fig_box, use_container_width=True)
    
    # Tendencia temporal
    st.subheader("📈 Tendencia Temporal")
    launch_df_sorted = launch_df.sort_values('timestamp')
    launch_df_sorted['date'] = launch_df_sorted['timestamp'].dt.date
    
    daily_p95 = launch_df_sorted.groupby(['date', 'device_tier'])['duration_ms'].apply(calculate_p95).reset_index()
    
    fig_trend = px.line(
        daily_p95,
        x='date',
        y='duration_ms',
        color='device_tier',
        title='P95 Loading Time a lo largo del tiempo',
        labels={'duration_ms': 'P95 (ms)', 'date': 'Fecha'}
    )
    st.plotly_chart(fig_trend, use_container_width=True)

def bq14_analysis(df):
    """
    BQ14: P95 time from "Pay" tap to confirmed payment,
    segmented by network type and device class
    """
    st.header("💳 BQ14: Payment Completion Time (P95)")
    st.markdown("**Pregunta**: *¿Cuál es el tiempo P95 desde tap en 'Pay' hasta pago confirmado, segmentado por tipo de red y clase de dispositivo?*")
    
    # Filtrar eventos de pago
    payment_df = df[df['event_name'] == 'payment_completed'].copy()
    
    if len(payment_df) == 0:
        st.warning("⚠️ No hay eventos 'payment_completed' en los datos.")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Pagos", len(payment_df))
    with col2:
        if 'success' in payment_df.columns:
            success_rate = (payment_df['success'].sum() / len(payment_df) * 100)
            st.metric("Tasa de Éxito", f"{success_rate:.1f}%")
    with col3:
        avg_time = payment_df['duration_ms'].mean()
        st.metric("Tiempo Promedio", format_duration(avg_time))
    with col4:
        p95_overall = calculate_p95(payment_df['duration_ms'])
        st.metric("P95 General", format_duration(p95_overall))
    
    # P95 por segmento
    st.subheader("📊 P95 por Network Type y Device Class")
    
    p95_payment = payment_df.groupby(['network_type', 'device_tier'])['duration_ms'].apply(calculate_p95).reset_index()
    p95_payment.columns = ['Network Type', 'Device Tier', 'P95 (ms)']
    p95_payment['P95'] = p95_payment['P95 (ms)'].apply(format_duration)
    
    # Gráfico de barras
    fig = px.bar(
        p95_payment,
        x='Network Type',
        y='P95 (ms)',
        color='Device Tier',
        title="P95 Payment Time por Network Type y Device Tier",
        text='P95',
        barmode='group',
        category_orders={'Device Tier': ['low', 'mid', 'high']},
        color_discrete_sequence=px.colors.qualitative.Set1,
        height=500
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de datos
    st.dataframe(p95_payment, use_container_width=True, hide_index=True)
    
    # Visualizaciones adicionales
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔥 Heatmap de P95")
        pivot = p95_payment.pivot(index='Device Tier', columns='Network Type', values='P95 (ms)')
        fig_heatmap = px.imshow(
            pivot,
            text_auto='.0f',
            aspect='auto',
            color_continuous_scale='Reds',
            labels=dict(color="P95 (ms)")
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with col2:
        st.markdown("### ✅ Tasa de Éxito por Segmento")
        if 'success' in payment_df.columns:
            success_by_segment = payment_df.groupby(['network_type', 'device_tier']).agg({
                'success': ['sum', 'count', 'mean']
            }).reset_index()
            # Aplanar columnas MultiIndex
            success_by_segment.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                                          for col in success_by_segment.columns.values]
            success_by_segment.rename(columns={
                'network_type': 'Network Type',
                'device_tier': 'Device Tier',
                'success_sum': 'Exitosos',
                'success_count': 'Total',
                'success_mean': 'Tasa'
            }, inplace=True)
            # Convertir explícitamente a numérico antes de calcular
            success_by_segment['Tasa'] = pd.to_numeric(success_by_segment['Tasa'], errors='coerce')
            success_by_segment['Tasa'] = (success_by_segment['Tasa'] * 100).round(2)
            
            fig_success = px.bar(
                success_by_segment,
                x='Network Type',
                y='Tasa',
                color='Device Tier',
                title="Tasa de Éxito de Pagos (%)",
                barmode='group'
            )
            st.plotly_chart(fig_success, use_container_width=True)
            st.dataframe(success_by_segment, use_container_width=True, hide_index=True)
    
    # Métodos de pago
    if 'payment_method' in payment_df.columns and payment_df['payment_method'].notna().any():
        st.subheader("💰 Análisis por Método de Pago")
        method_p95 = payment_df.groupby('payment_method')['duration_ms'].apply(calculate_p95).reset_index()
        method_p95.columns = ['Método de Pago', 'P95 (ms)']
        method_p95['P95'] = method_p95['P95 (ms)'].apply(format_duration)
        
        fig_method = px.bar(
            method_p95,
            x='Método de Pago',
            y='P95 (ms)',
            title="P95 por Método de Pago",
            text='P95',
            color='Método de Pago'
        )
        fig_method.update_traces(textposition='outside')
        st.plotly_chart(fig_method, use_container_width=True)
    
    # Tendencia temporal
    st.subheader("📈 Tendencia Temporal")
    payment_df_sorted = payment_df.sort_values('timestamp')
    payment_df_sorted['date'] = payment_df_sorted['timestamp'].dt.date
    
    daily_p95_payment = payment_df_sorted.groupby(['date', 'network_type'])['duration_ms'].apply(calculate_p95).reset_index()
    
    fig_trend = px.line(
        daily_p95_payment,
        x='date',
        y='duration_ms',
        color='network_type',
        title='P95 Payment Time a lo largo del tiempo',
        labels={'duration_ms': 'P95 (ms)', 'date': 'Fecha'}
    )
    st.plotly_chart(fig_trend, use_container_width=True)

def bq5_analysis():
    """
    BQ5: Which product categories are most frequently re-ordered, and at what times?
    Fetches from backend (cached in data/) and renders visualizations.
    """
    st.header("🔁 BQ5: Reorders by Category and Time")

    # Parameter controls (calendar with defaults this year)
    current_year = datetime.utcnow().year
    default_start = datetime(current_year, 1, 1).date()
    default_end = datetime(current_year, 12, 31).date()

    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        start_date = st.date_input("From (UTC)", value=default_start)
    with col2:
        end_date = st.date_input("To (UTC)", value=default_end)
    with col3:
        tz_str = st.text_input("Timezone offset (minutes)", value="-300", placeholder="e.g., -300 for UTC-5")
    with col4:
        force_refresh = st.checkbox("Force refresh cache", value=False, help="Ignore cache and query backend")

    # Validate and parse
    if end_date < start_date:
        st.warning("'To' date must be on or after 'From' date.")
        return

    try:
        tz_offset = int(tz_str) if tz_str.strip() else 0
    except ValueError:
        st.warning("Timezone offset must be an integer (minutes). Using 0.")
        tz_offset = 0

    # Run ETL (uses cache when available unless forced)
    try:
        frames = run_bq5_etl(
            start=datetime.combine(start_date, datetime.min.time()),
            end=datetime.combine(end_date, datetime.min.time()),
            timezone_offset_minutes=tz_offset,
            force_refresh=bool(force_refresh)
        )
    except Exception as e:
        st.error(f"❌ Error running BQ5 ETL: {e}")
        return

    df_cat = frames.get("categories")
    df_hourly = frames.get("hourly")

    if df_cat is None or df_cat.empty:
        st.warning("No category data available.")
        return

    # KPIs
    total_categories = len(df_cat)
    total_reorders = int(df_cat["reorder_count"].sum()) if "reorder_count" in df_cat.columns else 0
    top_row = df_cat.iloc[0]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Categories", total_categories)
    with col2:
        st.metric("Total reorders", f"{total_reorders}")
    with col3:
        st.metric("Top category", f"{top_row.get('categoria_nombre', '-')}: {int(top_row.get('reorder_count', 0))}")

    # Ranking by category
    st.subheader("🏆 Reorders by Category (Ranking)")
    fig_rank = px.bar(
        df_cat,
        x="categoria_nombre",
        y="reorder_count",
        title="Reorders by category",
        text="reorder_count",
        color="categoria_nombre"
    )
    fig_rank.update_traces(textposition='outside')
    fig_rank.update_layout(xaxis_title="Category", yaxis_title="Reorders")
    st.plotly_chart(fig_rank, use_container_width=True)

    # Hour-of-day distribution
    st.subheader("⏰ Hour-of-day Distribution")
    if df_hourly is not None and not df_hourly.empty:
        # Category selector
        cats = df_hourly["categoria_nombre"].unique().tolist()
        selected = st.multiselect("Categories", options=cats, default=[])
        filtered_h = df_hourly[df_hourly["categoria_nombre"].isin(selected)] if selected else df_hourly

        # Bars by hour (grouped by category)
        fig_hour = px.bar(
            filtered_h,
            x="hour",
            y="count",
            color="categoria_nombre",
            barmode='group',
            title="Reorders by hour",
        )
        fig_hour.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig_hour, use_container_width=True)

        # Heatmap category vs hour
        pivot = filtered_h.pivot_table(index="categoria_nombre", columns="hour", values="count", aggfunc="sum", fill_value=0)
        fig_heat = px.imshow(pivot, aspect='auto', text_auto=True, color_continuous_scale='YlOrRd', labels=dict(color="Reorders"))
        st.plotly_chart(fig_heat, use_container_width=True)

        # Peak hours per category
        st.markdown("### 🔝 Peak hours per category")
        peak_rows = []
        for cname, grp in df_hourly.groupby("categoria_nombre"):
            if grp.empty:
                continue
            max_count = grp["count"].max()
            hours = grp[grp["count"] == max_count]["hour"].tolist()
            peak_rows.append({"Category": cname, "Peak hours": ", ".join(map(str, sorted(hours))), "Max per hour": int(max_count)})
        df_peaks = pd.DataFrame(peak_rows).sort_values(["Max per hour", "Category"], ascending=[False, True])
        st.dataframe(df_peaks, use_container_width=True, hide_index=True)
    else:
        st.info("No hourly distribution available.")

    # Downloads
    st.subheader("📥 Downloads")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download categories (CSV)", data=df_cat.to_csv(index=False), file_name="bq5_categories.csv", mime="text/csv")
    with col2:
        if df_hourly is not None and not df_hourly.empty:
            st.download_button("Download hourly distribution (CSV)", data=df_hourly.to_csv(index=False), file_name="bq5_hourly_distribution.csv", mime="text/csv")

def bq4_analysis():
    """
    BQ4: Median pickup waiting time from "order ready" to "order picked up",
    segmented by peak vs off-peak hours
    """
    st.header("⏱️ BQ4: Pickup Waiting Time (Median)")
    st.markdown("**Pregunta**: *¿Cuál es el tiempo de espera mediano desde 'pedido listo' hasta 'pedido recogido', segmentado por horas pico vs valle?*")
    
    # Sidebar para cargar datos de compras
    st.sidebar.markdown("---")
    st.sidebar.header("📦 Datos de Compras (BQ4)")
    
    uploaded_pickup_file = st.sidebar.file_uploader("Subir CSV de compras", type=['csv'], key="pickup_upload")
    
    default_pickup_path = st.sidebar.text_input(
        "O especificar ruta del CSV de compras",
        value="data/compras_completadas_20251004_172958.csv",
        key="pickup_path"
    )
    
    df_pickup = None
    
    if uploaded_pickup_file is not None:
        df_pickup = load_pickup_data(uploaded_pickup_file)
    elif Path(default_pickup_path).exists():
        df_pickup = load_pickup_data(default_pickup_path)
        st.sidebar.success(f"✅ Datos de compras cargados")
    else:
        st.info("👆 Por favor sube un archivo CSV de compras o especifica una ruta válida en el sidebar.")
        st.markdown("### Formato esperado del CSV:")
        st.code("""id_compra,fecha_listo,fecha_entregado,tiempo_espera_entrega_seg,...
1,2025-10-04 02:56:49,2025-10-04 02:56:52,2.36,...""")
        return
    
    if df_pickup is not None:
        # Procesar datos
        df_pickup['hora_listo'] = df_pickup['fecha_listo'].dt.hour
        df_pickup['periodo_hora'] = df_pickup['hora_listo'].apply(classify_peak_hours)
        df_pickup['periodo_comida'] = df_pickup['hora_listo'].apply(get_meal_period)
        df_pickup['dia_semana'] = df_pickup['fecha_listo'].dt.day_name()
        df_pickup['es_fin_semana'] = df_pickup['fecha_listo'].dt.dayofweek >= 5
        
        # Resumen general
        with st.expander("📋 Resumen de Datos", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Pedidos", len(df_pickup))
            with col2:
                peak_count = (df_pickup['periodo_hora'] == 'Peak').sum()
                st.metric("Pedidos Peak", peak_count)
            with col3:
                offpeak_count = (df_pickup['periodo_hora'] == 'Off-Peak').sum()
                st.metric("Pedidos Off-Peak", offpeak_count)
            with col4:
                st.write(f"**Rango de fechas:**")
                st.write(f"{df_pickup['fecha_listo'].min().date()} a {df_pickup['fecha_listo'].max().date()}")
        
        # Tabs para organizar análisis
        tab1, tab2, tab3 = st.tabs([
            "📊 Peak vs Off-Peak", 
            "🕐 Por Hora del Día", 
            "📅 Por Día de Semana"
        ])
        
        # TAB 1: Peak vs Off-Peak
        with tab1:
            st.subheader("📊 Análisis Peak vs Off-Peak Hours")
            
            st.info("""
            **Horas Pico**: 12:00-14:00 (almuerzo) y 19:00-21:00 (cena)  
            **Horas Valle**: Resto del día
            """)
            
            # Métricas principales
            col1, col2, col3 = st.columns(3)
            
            peak_data = df_pickup[df_pickup['periodo_hora'] == 'Peak']['tiempo_espera_entrega_seg']
            offpeak_data = df_pickup[df_pickup['periodo_hora'] == 'Off-Peak']['tiempo_espera_entrega_seg']
            
            peak_median = peak_data.median()
            offpeak_median = offpeak_data.median()
            diff = peak_median - offpeak_median
            pct_diff = (diff / offpeak_median * 100) if offpeak_median > 0 else 0
            
            with col1:
                st.metric(
                    "Mediana Peak", 
                    format_time(peak_median),
                    f"{pct_diff:+.1f}% vs Off-Peak"
                )
            with col2:
                st.metric(
                    "Mediana Off-Peak",
                    format_time(offpeak_median)
                )
            with col3:
                st.metric(
                    "Diferencia",
                    format_time(abs(diff)),
                    f"{abs(pct_diff):.1f}%"
                )
            
            # Box plot comparativo
            fig_box = px.box(
                df_pickup,
                x='periodo_hora',
                y='tiempo_espera_entrega_seg',
                color='periodo_hora',
                title="Waiting Time Distribution: Peak vs Off-Peak",
                labels={'tiempo_espera_entrega_seg': 'Waiting Time (seconds)', 'periodo_hora': 'Period'},
                color_discrete_map={'Peak': 'salmon', 'Off-Peak': 'lightblue'},
                category_orders={'periodo_hora': ['Off-Peak', 'Peak']}
            )
            fig_box.add_hline(y=peak_median, line_dash="dash", line_color="red", 
                             annotation_text=f"Peak Median: {format_time(peak_median)}")
            fig_box.add_hline(y=offpeak_median, line_dash="dash", line_color="blue",
                             annotation_text=f"Off-Peak Median: {format_time(offpeak_median)}")
            st.plotly_chart(fig_box, use_container_width=True)
            
            # Estadísticas detalladas
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Peak Hours")
                stats_peak = pd.DataFrame({
                    'Métrica': ['Count', 'Median', 'Mean', 'Std Dev', 'Min', 'Max'],
                    'Valor': [
                        len(peak_data),
                        f"{peak_data.median():.2f}s",
                        f"{peak_data.mean():.2f}s",
                        f"{peak_data.std():.2f}s",
                        f"{peak_data.min():.2f}s",
                        f"{peak_data.max():.2f}s"
                    ]
                })
                st.dataframe(stats_peak, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("### 📊 Off-Peak Hours")
                stats_offpeak = pd.DataFrame({
                    'Métrica': ['Count', 'Median', 'Mean', 'Std Dev', 'Min', 'Max'],
                    'Valor': [
                        len(offpeak_data),
                        f"{offpeak_data.median():.2f}s",
                        f"{offpeak_data.mean():.2f}s",
                        f"{offpeak_data.std():.2f}s",
                        f"{offpeak_data.min():.2f}s",
                        f"{offpeak_data.max():.2f}s"
                    ]
                })
                st.dataframe(stats_offpeak, use_container_width=True, hide_index=True)
        
        # TAB 2: Por Hora del Día
        with tab2:
            st.subheader("🕐 Análisis por Hora del Día")
            
            # Agrupar por hora
            hourly = df_pickup.groupby('hora_listo').agg({
                'tiempo_espera_entrega_seg': ['count', 'median', 'mean']
            }).reset_index()
            hourly.columns = ['Hora', 'Count', 'Median', 'Mean']
            hourly['Periodo'] = hourly['Hora'].apply(classify_peak_hours)
            
            # Gráfico de barras por hora
            fig_hourly = px.bar(
                hourly,
                x='Hora',
                y='Median',
                color='Periodo',
                title='Median Waiting Time by Hour of Day',
                labels={'Median': 'Median Waiting Time (seconds)', 'Hora': 'Hour'},
                text='Median',
                color_discrete_map={'Peak': 'salmon', 'Off-Peak': 'lightblue'}
            )
            fig_hourly.update_traces(texttemplate='%{text:.1f}s', textposition='outside')
            fig_hourly.update_layout(height=500)
            
            # Resaltar horas pico
            fig_hourly.add_vrect(x0=11.5, x1=14.5, fillcolor="red", opacity=0.1, 
                                line_width=0, annotation_text="Lunch Peak", annotation_position="top left")
            fig_hourly.add_vrect(x0=18.5, x1=21.5, fillcolor="orange", opacity=0.1,
                                line_width=0, annotation_text="Dinner Peak", annotation_position="top left")
            
            st.plotly_chart(fig_hourly, use_container_width=True)
            
            # Top 5 horas
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### ⚠️ Top 5 Horas Más Lentas")
                hourly_sorted = df_pickup.groupby('hora_listo')['tiempo_espera_entrega_seg'].median().sort_values(ascending=False).head(5)
                for hour, median in hourly_sorted.items():
                    period = classify_peak_hours(hour)
                    st.write(f"**{int(hour):02d}:00** ({period}): {format_time(median)}")
            
            with col2:
                st.markdown("### ✅ Top 5 Horas Más Rápidas")
                hourly_fastest = df_pickup.groupby('hora_listo')['tiempo_espera_entrega_seg'].median().sort_values().head(5)
                for hour, median in hourly_fastest.items():
                    period = classify_peak_hours(hour)
                    st.write(f"**{int(hour):02d}:00** ({period}): {format_time(median)}")
        
        # TAB 3: Por Día de Semana
        with tab3:
            st.subheader("📅 Análisis por Día de Semana")
            
            # Agrupar por día y periodo
            daily = df_pickup.groupby(['dia_semana', 'periodo_hora']).agg({
                'tiempo_espera_entrega_seg': ['count', 'median']
            }).reset_index()
            daily.columns = ['Día', 'Periodo', 'Count', 'Median']
            
            # Gráfico de barras agrupadas
            fig_daily = px.bar(
                daily,
                x='Día',
                y='Median',
                color='Periodo',
                barmode='group',
                title='Median Waiting Time by Day of Week',
                labels={'Median': 'Median Waiting Time (seconds)', 'Día': 'Day of Week'},
                color_discrete_map={'Peak': 'salmon', 'Off-Peak': 'lightblue'},
                category_orders={
                    'Día': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                }
            )
            st.plotly_chart(fig_daily, use_container_width=True)

def main():
    st.title("📊 Analytics Dashboard - BQ13, BQ14, BQ4 & BQ5")
    st.markdown("**Análisis de performance, pagos, pickup y reorders**")
    
    # Sidebar para cargar datos
    st.sidebar.header("📁 Cargar Datos")
    
    uploaded_file = st.sidebar.file_uploader("Subir archivo CSV", type=['csv'])
    
    default_path = st.sidebar.text_input(
        "O especificar ruta del CSV",
        value="data/analytics_events.csv"
    )
    
    df = None
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
    elif Path(default_path).exists():
        df = load_data(default_path)
        st.sidebar.success(f"✅ Datos cargados desde: {default_path}")
    else:
        st.info("👆 Por favor sube un archivo CSV o especifica una ruta válida en el sidebar.")
        st.markdown("### Formato esperado del CSV:")
        st.code("""timestamp,event_name,duration_ms,network_type,device_tier,...
2025-10-04 19:13:12.801,menu_ready,5026,Wi-Fi,low,...
2025-10-04 19:13:13.818,app_launch_to_menu,6060,Wi-Fi,low,...""")
        return
    
    if df is not None:
        # Resumen de datos
        with st.expander("📋 Resumen de Datos", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Eventos", len(df))
            with col2:
                st.write(f"**Tipos de eventos:**")
                st.write(df['event_name'].value_counts().to_dict())
            with col3:
                st.write(f"**Rango de fechas:**")
                st.write(f"{df['timestamp'].min().date()} a {df['timestamp'].max().date()}")
            
            st.dataframe(df.head(10), use_container_width=True)
        
        # Pestañas para cada análisis
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📱 BQ13: App Loading", 
            "💳 BQ14: Payment Time", 
            "⏱️ BQ4: Pickup Time",
            "🔁 BQ5: Reorders", 
            "📊 Datos Crudos"
        ])
        
        with tab1:
            bq13_analysis(df)
        
        with tab2:
            bq14_analysis(df)

        with tab3:
            bq4_analysis()

        with tab4:
            bq5_analysis()

        with tab5:
            st.subheader("📊 Explorador de Datos Crudos")
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                event_filter = st.multiselect(
                    "Tipo de Evento",
                    options=df['event_name'].unique(),
                    default=df['event_name'].unique()
                )
            with col2:
                network_filter = st.multiselect(
                    "Tipo de Red",
                    options=df['network_type'].unique(),
                    default=df['network_type'].unique()
                )
            with col3:
                tier_filter = st.multiselect(
                    "Device Tier",
                    options=df['device_tier'].unique(),
                    default=df['device_tier'].unique()
                )
            
            # Aplicar filtros
            filtered_df = df[
                (df['event_name'].isin(event_filter)) &
                (df['network_type'].isin(network_filter)) &
                (df['device_tier'].isin(tier_filter))
            ]
            
            st.write(f"**Mostrando {len(filtered_df)} eventos**")
            st.dataframe(filtered_df, use_container_width=True)
            
            # Botón de descarga
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar datos filtrados",
                data=csv,
                file_name="filtered_analytics.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()

