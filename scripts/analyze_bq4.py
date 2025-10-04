"""
BQ4 Analysis Script
====================
Pregunta: ¿Cuál es el tiempo de espera mediano desde "pedido listo" 
hasta "pedido recogido", segmentado por horas pico vs valle?

Usage:
    python scripts/analyze_bq4.py data/compras_completadas_20251004_172958.csv
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import sys
from pathlib import Path

def classify_peak_hours(hour):
    """Clasifica horas como pico o valle"""
    if (12 <= hour < 14) or (19 <= hour < 21):
        return 'peak'
    else:
        return 'off-peak'

def format_time(seconds):
    """Formatea segundos a formato legible"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.2f}min"
    else:
        return f"{seconds/3600:.2f}h"

def analyze_bq4(csv_path):
    """Analiza BQ4: Tiempo mediano de espera por peak/off-peak hours"""
    
    print("=" * 80)
    print("BQ4: MEDIAN PICKUP WAITING TIME ANALYSIS")
    print("=" * 80)
    
    # Cargar datos
    try:
        df = pd.read_csv(csv_path)
        df['fecha_listo'] = pd.to_datetime(df['fecha_listo'])
        print(f"✅ Cargados {len(df)} pedidos desde {csv_path}")
    except Exception as e:
        print(f"❌ Error cargando CSV: {e}")
        sys.exit(1)
    
    # Extraer hora y clasificar
    df['hora_listo'] = df['fecha_listo'].dt.hour
    df['periodo_hora'] = df['hora_listo'].apply(classify_peak_hours)
    df['dia_semana'] = df['fecha_listo'].dt.day_name()
    
    print(f"📅 Rango de fechas: {df['fecha_listo'].min()} a {df['fecha_listo'].max()}")
    print()
    
    # Análisis principal: Mediana por peak/off-peak
    print("-" * 80)
    print("TIEMPO MEDIANO DE ESPERA: PEAK VS OFF-PEAK")
    print("-" * 80)
    
    median_by_period = df.groupby('periodo_hora')['tiempo_espera_entrega_seg'].agg([
        ('count', 'count'),
        ('median', 'median'),
        ('mean', 'mean'),
        ('std', 'std'),
        ('min', 'min'),
        ('max', 'max'),
        ('p25', lambda x: np.percentile(x, 25)),
        ('p75', lambda x: np.percentile(x, 75))
    ]).reset_index()
    
    print(median_by_period.to_string(index=False))
    print()
    
    # Comparación
    peak_median = median_by_period[median_by_period['periodo_hora'] == 'peak']['median'].values[0]
    offpeak_median = median_by_period[median_by_period['periodo_hora'] == 'off-peak']['median'].values[0]
    diff = peak_median - offpeak_median
    pct_diff = (diff / offpeak_median * 100)
    
    print(f"📊 COMPARACIÓN:")
    print(f"   Peak hours:     {format_time(peak_median)} (mediana)")
    print(f"   Off-peak hours: {format_time(offpeak_median)} (mediana)")
    print(f"   Diferencia:     {format_time(diff)} ({pct_diff:+.1f}%)")
    print()
    
    # Análisis por hora del día
    print("-" * 80)
    print("TIEMPO MEDIANO POR HORA DEL DÍA")
    print("-" * 80)
    
    median_by_hour = df.groupby('hora_listo')['tiempo_espera_entrega_seg'].agg([
        ('count', 'count'),
        ('median', 'median')
    ]).reset_index()
    median_by_hour['periodo'] = median_by_hour['hora_listo'].apply(classify_peak_hours)
    
    print(median_by_hour.to_string(index=False))
    print()
    
    # Análisis por día de la semana
    print("-" * 80)
    print("TIEMPO MEDIANO POR DÍA Y PERIODO")
    print("-" * 80)
    
    median_by_day_period = df.groupby(['dia_semana', 'periodo_hora'])['tiempo_espera_entrega_seg'].agg([
        ('count', 'count'),
        ('median', 'median')
    ]).reset_index()
    
    print(median_by_day_period.to_string(index=False))
    print()
    
    # Horas pico más críticas
    print("-" * 80)
    print("TOP 5 HORAS MÁS LENTAS (por mediana)")
    print("-" * 80)
    
    slowest_hours = median_by_hour.nlargest(5, 'median')[['hora_listo', 'periodo', 'median', 'count']]
    for _, row in slowest_hours.iterrows():
        print(f"  {int(row['hora_listo']):02d}:00 ({row['periodo']:>8}): {format_time(row['median']):>10} (n={int(row['count'])})")
    print()
    
    # Distribución de tiempos
    print("-" * 80)
    print("DISTRIBUCIÓN DE TIEMPOS DE ESPERA")
    print("-" * 80)
    
    for period in ['peak', 'off-peak']:
        data = df[df['periodo_hora'] == period]['tiempo_espera_entrega_seg']
        if len(data) > 0:
            print(f"\n{period.upper()}:")
            print(f"  < 5 seg:     {(data < 5).sum():>4} ({(data < 5).sum()/len(data)*100:>5.1f}%)")
            print(f"  < 30 seg:    {(data < 30).sum():>4} ({(data < 30).sum()/len(data)*100:>5.1f}%)")
            print(f"  < 1 min:     {(data < 60).sum():>4} ({(data < 60).sum()/len(data)*100:>5.1f}%)")
            print(f"  1-5 min:     {((data >= 60) & (data < 300)).sum():>4} ({((data >= 60) & (data < 300)).sum()/len(data)*100:>5.1f}%)")
            print(f"  > 5 min:     {(data >= 300).sum():>4} ({(data >= 300).sum()/len(data)*100:>5.1f}%)")
    print()
    
    # Generar visualizaciones
    print("-" * 80)
    print("GENERANDO VISUALIZACIONES...")
    print("-" * 80)
    
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('BQ4: Pickup Waiting Time Analysis (Peak vs Off-Peak)', fontsize=16, fontweight='bold')
    
    # Plot 1: Box plot comparando peak vs off-peak
    ax1 = axes[0, 0]
    df_plot = df.copy()
    df_plot['periodo_hora'] = pd.Categorical(df_plot['periodo_hora'], categories=['off-peak', 'peak'], ordered=True)
    sns.boxplot(data=df_plot, x='periodo_hora', y='tiempo_espera_entrega_seg', ax=ax1, palette='Set2')
    ax1.set_title('Waiting Time: Peak vs Off-Peak (Box Plot)', fontweight='bold')
    ax1.set_xlabel('Period')
    ax1.set_ylabel('Waiting Time (seconds)')
    ax1.axhline(y=peak_median, color='r', linestyle='--', alpha=0.5, label=f'Peak Median: {format_time(peak_median)}')
    ax1.axhline(y=offpeak_median, color='b', linestyle='--', alpha=0.5, label=f'Off-Peak Median: {format_time(offpeak_median)}')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Mediana por hora del día
    ax2 = axes[0, 1]
    colors = ['salmon' if p == 'peak' else 'lightblue' for p in median_by_hour['periodo']]
    ax2.bar(median_by_hour['hora_listo'], median_by_hour['median'], color=colors, edgecolor='black')
    ax2.set_title('Median Waiting Time by Hour of Day', fontweight='bold')
    ax2.set_xlabel('Hour')
    ax2.set_ylabel('Median Waiting Time (seconds)')
    ax2.axhspan(12, 14, alpha=0.2, color='red', label='Lunch Peak')
    ax2.axhspan(19, 21, alpha=0.2, color='orange', label='Dinner Peak')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Histograma comparativo
    ax3 = axes[1, 0]
    peak_data = df[df['periodo_hora'] == 'peak']['tiempo_espera_entrega_seg']
    offpeak_data = df[df['periodo_hora'] == 'off-peak']['tiempo_espera_entrega_seg']
    ax3.hist([offpeak_data, peak_data], bins=30, alpha=0.7, label=['Off-Peak', 'Peak'], color=['lightblue', 'salmon'])
    ax3.set_title('Distribution of Waiting Times', fontweight='bold')
    ax3.set_xlabel('Waiting Time (seconds)')
    ax3.set_ylabel('Frequency')
    ax3.axvline(offpeak_median, color='blue', linestyle='--', linewidth=2, label=f'Off-Peak Median')
    ax3.axvline(peak_median, color='red', linestyle='--', linewidth=2, label=f'Peak Median')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Violin plot por día de la semana
    ax4 = axes[1, 1]
    df_plot2 = df.copy()
    # Ordenar días de la semana
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_plot2['dia_semana'] = pd.Categorical(df_plot2['dia_semana'], categories=day_order, ordered=True)
    sns.violinplot(data=df_plot2, x='dia_semana', y='tiempo_espera_entrega_seg', hue='periodo_hora', 
                   split=True, ax=ax4, palette='Set2')
    ax4.set_title('Waiting Time by Day of Week', fontweight='bold')
    ax4.set_xlabel('Day of Week')
    ax4.set_ylabel('Waiting Time (seconds)')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Guardar figura
    output_file = 'bq4_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Visualización guardada en: {output_file}")
    
    # Guardar resultados
    output_csv = 'bq4_results.csv'
    median_by_period.to_csv(output_csv, index=False)
    print(f"✅ Resultados guardados en: {output_csv}")
    
    output_hourly = 'bq4_results_by_hour.csv'
    median_by_hour.to_csv(output_hourly, index=False)
    print(f"✅ Resultados por hora guardados en: {output_hourly}")
    
    print()
    print("=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)
    print(f"\n🎯 CONCLUSIÓN:")
    if peak_median > offpeak_median:
        print(f"   Los tiempos de espera en horas PICO son {pct_diff:.1f}% MAYORES que en horas valle.")
    else:
        print(f"   Los tiempos de espera en horas VALLE son {abs(pct_diff):.1f}% MAYORES que en horas pico.")
    print(f"   Se recomienda {'aumentar staff' if peak_median > offpeak_median else 'redistribuir recursos'} en horas pico.")

def main():
    parser = argparse.ArgumentParser(description='BQ4: Analizar tiempo mediano de pickup')
    parser.add_argument('csv_file', help='Ruta al archivo CSV de compras')
    
    args = parser.parse_args()
    
    if not Path(args.csv_file).exists():
        print(f"❌ Error: El archivo '{args.csv_file}' no existe")
        sys.exit(1)
    
    analyze_bq4(args.csv_file)

if __name__ == "__main__":
    main()

