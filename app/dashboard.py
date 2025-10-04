"""
Analytics Dashboard for BQ13 and BQ14
=====================================
Dashboard interactivo para analizar tiempos de carga y pagos.

BQ13: P95 app loading time (open to usable menu) by device class and network
BQ14: P95 payment time (Pay tap to confirmed) by network type and device class

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

# Configuración de página
st.set_page_config(
    page_title="Analytics Dashboard - BQ13 & BQ14",
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

def main():
    st.title("📊 Analytics Dashboard - BQ13 & BQ14")
    st.markdown("**Análisis de performance: tiempos de carga y pagos**")
    
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
        tab1, tab2, tab3 = st.tabs(["📱 BQ13: App Loading", "💳 BQ14: Payment Time", "📊 Datos Crudos"])
        
        with tab1:
            bq13_analysis(df)
        
        with tab2:
            bq14_analysis(df)
        
        with tab3:
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

