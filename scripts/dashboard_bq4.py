"""
Dashboard BQ4: Pickup Waiting Time Analysis
============================================
Análisis interactivo del tiempo de espera de recogida por horas pico vs valle.

Pregunta: ¿Cuál es el tiempo de espera mediano desde "pedido listo" 
hasta "pedido recogido", segmentado por horas pico vs valle?

Usage:
    streamlit run scripts/dashboard_bq4.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from pathlib import Path

# Configuración de página
st.set_page_config(
    page_title="BQ4: Pickup Waiting Time",
    page_icon="⏱️",
    layout="wide"
)

def load_data(file_path):
    """Carga y parsea el archivo CSV"""
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

def main():
    st.title("⏱️ BQ4: Pickup Waiting Time Analysis")
    st.markdown("**Pregunta**: *¿Cuál es el tiempo de espera mediano desde 'pedido listo' hasta 'pedido recogido', segmentado por horas pico vs valle?*")
    
    # Sidebar para cargar datos
    st.sidebar.header("📁 Cargar Datos")
    
    uploaded_file = st.sidebar.file_uploader("Subir archivo CSV", type=['csv'])
    
    default_path = st.sidebar.text_input(
        "O especificar ruta del CSV",
        value="data/compras_completadas_20251004_172958.csv"
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
        st.code("""id_compra,fecha_listo,fecha_entregado,tiempo_espera_entrega_seg,...
1,2025-10-04 02:56:49,2025-10-04 02:56:52,2.36,...""")
        return
    
    if df is not None:
        # Procesar datos
        df['hora_listo'] = df['fecha_listo'].dt.hour
        df['periodo_hora'] = df['hora_listo'].apply(classify_peak_hours)
        df['periodo_comida'] = df['hora_listo'].apply(get_meal_period)
        df['dia_semana'] = df['fecha_listo'].dt.day_name()
        df['es_fin_semana'] = df['fecha_listo'].dt.dayofweek >= 5
        
        # Resumen general
        with st.expander("📋 Resumen de Datos", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Pedidos", len(df))
            with col2:
                peak_count = (df['periodo_hora'] == 'Peak').sum()
                st.metric("Pedidos Peak", peak_count)
            with col3:
                offpeak_count = (df['periodo_hora'] == 'Off-Peak').sum()
                st.metric("Pedidos Off-Peak", offpeak_count)
            with col4:
                st.write(f"**Rango de fechas:**")
                st.write(f"{df['fecha_listo'].min().date()} a {df['fecha_listo'].max().date()}")
        
        # Tabs para organizar análisis
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Peak vs Off-Peak", 
            "🕐 Por Hora del Día", 
            "📅 Por Día de Semana",
            "📈 Datos Crudos"
        ])
        
        # TAB 1: Peak vs Off-Peak
        with tab1:
            st.header("📊 Análisis Peak vs Off-Peak Hours")
            
            st.info("""
            **Horas Pico**: 12:00-14:00 (almuerzo) y 19:00-21:00 (cena)  
            **Horas Valle**: Resto del día
            """)
            
            # Métricas principales
            col1, col2, col3 = st.columns(3)
            
            peak_data = df[df['periodo_hora'] == 'Peak']['tiempo_espera_entrega_seg']
            offpeak_data = df[df['periodo_hora'] == 'Off-Peak']['tiempo_espera_entrega_seg']
            
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
            st.subheader("📦 Distribución de Tiempos")
            fig_box = px.box(
                df,
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
                    'Métrica': ['Count', 'Median', 'Mean', 'Std Dev', 'Min', 'Max', 'P25', 'P75'],
                    'Valor': [
                        len(peak_data),
                        f"{peak_data.median():.2f}s",
                        f"{peak_data.mean():.2f}s",
                        f"{peak_data.std():.2f}s",
                        f"{peak_data.min():.2f}s",
                        f"{peak_data.max():.2f}s",
                        f"{peak_data.quantile(0.25):.2f}s",
                        f"{peak_data.quantile(0.75):.2f}s"
                    ]
                })
                st.dataframe(stats_peak, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("### 📊 Off-Peak Hours")
                stats_offpeak = pd.DataFrame({
                    'Métrica': ['Count', 'Median', 'Mean', 'Std Dev', 'Min', 'Max', 'P25', 'P75'],
                    'Valor': [
                        len(offpeak_data),
                        f"{offpeak_data.median():.2f}s",
                        f"{offpeak_data.mean():.2f}s",
                        f"{offpeak_data.std():.2f}s",
                        f"{offpeak_data.min():.2f}s",
                        f"{offpeak_data.max():.2f}s",
                        f"{offpeak_data.quantile(0.25):.2f}s",
                        f"{offpeak_data.quantile(0.75):.2f}s"
                    ]
                })
                st.dataframe(stats_offpeak, use_container_width=True, hide_index=True)
            
            # Histograma comparativo
            st.subheader("📊 Histograma Comparativo")
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=offpeak_data,
                name='Off-Peak',
                opacity=0.7,
                marker_color='lightblue',
                nbinsx=30
            ))
            fig_hist.add_trace(go.Histogram(
                x=peak_data,
                name='Peak',
                opacity=0.7,
                marker_color='salmon',
                nbinsx=30
            ))
            fig_hist.update_layout(
                barmode='overlay',
                title='Distribution of Waiting Times',
                xaxis_title='Waiting Time (seconds)',
                yaxis_title='Frequency',
                height=500
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        # TAB 2: Por Hora del Día
        with tab2:
            st.header("🕐 Análisis por Hora del Día")
            
            # Agrupar por hora
            hourly = df.groupby('hora_listo').agg({
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
            
            # Tabla detallada por hora
            st.subheader("📋 Detalle por Hora")
            hourly['Median'] = hourly['Median'].apply(lambda x: format_time(x))
            hourly['Mean'] = hourly['Mean'].apply(lambda x: format_time(x))
            st.dataframe(hourly, use_container_width=True, hide_index=True)
            
            # Top 5 horas más lentas
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### ⚠️ Top 5 Horas Más Lentas")
                hourly_sorted = df.groupby('hora_listo')['tiempo_espera_entrega_seg'].median().sort_values(ascending=False).head(5)
                for hour, median in hourly_sorted.items():
                    period = classify_peak_hours(hour)
                    st.write(f"**{int(hour):02d}:00** ({period}): {format_time(median)}")
            
            with col2:
                st.markdown("### ✅ Top 5 Horas Más Rápidas")
                hourly_fastest = df.groupby('hora_listo')['tiempo_espera_entrega_seg'].median().sort_values().head(5)
                for hour, median in hourly_fastest.items():
                    period = classify_peak_hours(hour)
                    st.write(f"**{int(hour):02d}:00** ({period}): {format_time(median)}")
        
        # TAB 3: Por Día de Semana
        with tab3:
            st.header("📅 Análisis por Día de Semana")
            
            # Agrupar por día y periodo
            daily = df.groupby(['dia_semana', 'periodo_hora']).agg({
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
            
            # Tabla detallada
            st.subheader("📋 Detalle por Día y Periodo")
            daily['Median'] = daily['Median'].apply(lambda x: format_time(x))
            st.dataframe(daily, use_container_width=True, hide_index=True)
            
            # Violin plot por día
            st.subheader("🎻 Distribución por Día de Semana")
            fig_violin = px.violin(
                df,
                x='dia_semana',
                y='tiempo_espera_entrega_seg',
                color='periodo_hora',
                box=True,
                title='Waiting Time Distribution by Day of Week',
                labels={'tiempo_espera_entrega_seg': 'Waiting Time (seconds)', 'dia_semana': 'Day of Week'},
                color_discrete_map={'Peak': 'salmon', 'Off-Peak': 'lightblue'},
                category_orders={
                    'dia_semana': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                }
            )
            st.plotly_chart(fig_violin, use_container_width=True)
        
        # TAB 4: Datos Crudos
        with tab4:
            st.subheader("📊 Explorador de Datos Crudos")
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                periodo_filter = st.multiselect(
                    "Periodo",
                    options=df['periodo_hora'].unique(),
                    default=df['periodo_hora'].unique()
                )
            with col2:
                dia_filter = st.multiselect(
                    "Día de Semana",
                    options=df['dia_semana'].unique(),
                    default=df['dia_semana'].unique()
                )
            with col3:
                comida_filter = st.multiselect(
                    "Periodo de Comida",
                    options=df['periodo_comida'].unique(),
                    default=df['periodo_comida'].unique()
                )
            
            # Aplicar filtros
            filtered_df = df[
                (df['periodo_hora'].isin(periodo_filter)) &
                (df['dia_semana'].isin(dia_filter)) &
                (df['periodo_comida'].isin(comida_filter))
            ]
            
            st.write(f"**Mostrando {len(filtered_df)} pedidos**")
            
            # Mostrar datos
            cols_to_show = [
                'id_compra', 'fecha_listo', 'fecha_entregado', 'hora_listo',
                'periodo_hora', 'periodo_comida', 'dia_semana',
                'tiempo_espera_entrega_seg', 'tiempo_espera_entrega_min'
            ]
            st.dataframe(filtered_df[cols_to_show], use_container_width=True)
            
            # Botón de descarga
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar datos filtrados",
                data=csv,
                file_name="compras_filtradas.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()

