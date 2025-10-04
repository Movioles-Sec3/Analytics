"""
BQ13 Analysis Script
====================
Pregunta: ¿Cuál es el tiempo P95 de carga de la app (desde apertura hasta menú usable) 
por clase de dispositivo y condiciones de red, y cómo cambia después de optimizaciones?

Usage:
    python scripts/analyze_bq13.py "data/analytics_events.csv"
    python scripts/analyze_bq13.py "path/to/data.csv" --cutoff "2025-10-05"
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import sys
from pathlib import Path

def calculate_p95(series):
    """Calcula percentil 95"""
    return np.percentile(series.dropna(), 95) if len(series.dropna()) > 0 else 0

def format_duration(ms):
    """Formatea milisegundos a formato legible"""
    if ms < 1000:
        return f"{ms:.0f}ms"
    else:
        return f"{ms/1000:.2f}s"

def analyze_bq13(csv_path, cutoff_date=None):
    """Analiza BQ13: P95 app loading time por device class y network"""
    
    print("=" * 80)
    print("BQ13: P95 APP LOADING TIME ANALYSIS")
    print("=" * 80)
    
    # Cargar datos
    try:
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        print(f"✅ Cargados {len(df)} eventos desde {csv_path}")
    except Exception as e:
        print(f"❌ Error cargando CSV: {e}")
        sys.exit(1)
    
    # Filtrar eventos app_launch_to_menu
    launch_df = df[df['event_name'] == 'app_launch_to_menu'].copy()
    
    if len(launch_df) == 0:
        print("❌ No se encontraron eventos 'app_launch_to_menu'!")
        sys.exit(1)
    
    print(f"📱 Total eventos de carga: {len(launch_df)}")
    print(f"📅 Rango de fechas: {launch_df['timestamp'].min()} a {launch_df['timestamp'].max()}")
    print()
    
    # Análisis P95 general
    print("-" * 80)
    print("P95 POR DEVICE CLASS & NETWORK TYPE")
    print("-" * 80)
    
    p95_overall = launch_df.groupby(['device_tier', 'network_type'])['duration_ms'].agg([
        ('count', 'count'),
        ('mean', 'mean'),
        ('median', 'median'),
        ('p95', calculate_p95),
        ('max', 'max')
    ]).reset_index()
    
    print(p95_overall.to_string(index=False))
    print()
    
    # Resumen por device tier
    print("-" * 80)
    print("P95 POR DEVICE TIER")
    print("-" * 80)
    by_tier = launch_df.groupby('device_tier')['duration_ms'].agg([
        ('count', 'count'),
        ('p95', calculate_p95)
    ]).reset_index()
    for _, row in by_tier.iterrows():
        print(f"  {row['device_tier']:>6}: {format_duration(row['p95']):>8} (n={row['count']})")
    print()
    
    # Resumen por network type
    print("-" * 80)
    print("P95 POR NETWORK TYPE")
    print("-" * 80)
    by_network = launch_df.groupby('network_type')['duration_ms'].agg([
        ('count', 'count'),
        ('p95', calculate_p95)
    ]).reset_index()
    for _, row in by_network.iterrows():
        print(f"  {row['network_type']:>10}: {format_duration(row['p95']):>8} (n={row['count']})")
    print()
    
    # Comparación antes/después si hay fecha de corte
    if cutoff_date:
        cutoff_dt = pd.Timestamp(cutoff_date)
        before_df = launch_df[launch_df['timestamp'] < cutoff_dt]
        after_df = launch_df[launch_df['timestamp'] >= cutoff_dt]
        
        print("-" * 80)
        print(f"COMPARACIÓN ANTES/DESPUÉS DE OPTIMIZACIÓN (Corte: {cutoff_date})")
        print("-" * 80)
        print(f"Antes: {len(before_df)} eventos | Después: {len(after_df)} eventos")
        print()
        
        if len(before_df) > 0 and len(after_df) > 0:
            p95_before = before_df.groupby(['device_tier', 'network_type'])['duration_ms'].apply(calculate_p95).reset_index()
            p95_before.columns = ['device_tier', 'network_type', 'p95_before']
            
            p95_after = after_df.groupby(['device_tier', 'network_type'])['duration_ms'].apply(calculate_p95).reset_index()
            p95_after.columns = ['device_tier', 'network_type', 'p95_after']
            
            comparison = p95_before.merge(p95_after, on=['device_tier', 'network_type'], how='outer')
            comparison['improvement_ms'] = comparison['p95_before'] - comparison['p95_after']
            comparison['improvement_pct'] = (comparison['improvement_ms'] / comparison['p95_before'] * 100).round(2)
            
            print(comparison.to_string(index=False))
            print()
            
            # Mejora general
            overall_p95_before = calculate_p95(before_df['duration_ms'])
            overall_p95_after = calculate_p95(after_df['duration_ms'])
            improvement = ((overall_p95_before - overall_p95_after) / overall_p95_before * 100)
            
            print(f"📊 Mejora general en P95: {improvement:.2f}%")
            print(f"   Antes:   {format_duration(overall_p95_before)}")
            print(f"   Después: {format_duration(overall_p95_after)}")
            print()
    
    # Generar visualizaciones
    print("-" * 80)
    print("GENERANDO VISUALIZACIONES...")
    print("-" * 80)
    
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('BQ13: P95 App Loading Time Analysis', fontsize=16, fontweight='bold')
    
    # Plot 1: Barras por device tier y network
    ax1 = axes[0, 0]
    pivot_data = p95_overall.pivot(index='device_tier', columns='network_type', values='p95')
    pivot_data = pivot_data.reindex(['low', 'mid', 'high'])
    pivot_data.plot(kind='bar', ax=ax1, rot=0)
    ax1.set_title('P95 Loading Time por Device Tier y Network', fontweight='bold')
    ax1.set_xlabel('Device Tier')
    ax1.set_ylabel('P95 Duration (ms)')
    ax1.legend(title='Network Type')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Heatmap
    ax2 = axes[0, 1]
    pivot_heatmap = p95_overall.pivot(index='device_tier', columns='network_type', values='p95')
    pivot_heatmap = pivot_heatmap.reindex(['low', 'mid', 'high'])
    sns.heatmap(pivot_heatmap, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax2, cbar_kws={'label': 'P95 (ms)'})
    ax2.set_title('P95 Loading Time Heatmap', fontweight='bold')
    ax2.set_xlabel('Network Type')
    ax2.set_ylabel('Device Tier')
    
    # Plot 3: Distribución por device tier
    ax3 = axes[1, 0]
    for tier in ['low', 'mid', 'high']:
        data = launch_df[launch_df['device_tier'] == tier]['duration_ms']
        if len(data) > 0:
            ax3.hist(data, bins=30, alpha=0.5, label=tier)
    ax3.set_title('Distribución de Loading Time por Device Tier', fontweight='bold')
    ax3.set_xlabel('Duration (ms)')
    ax3.set_ylabel('Frequency')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Box plot
    ax4 = axes[1, 1]
    launch_df_sorted = launch_df.copy()
    launch_df_sorted['device_tier'] = pd.Categorical(
        launch_df_sorted['device_tier'],
        categories=['low', 'mid', 'high'],
        ordered=True
    )
    sns.boxplot(data=launch_df_sorted, x='device_tier', y='duration_ms', hue='network_type', ax=ax4)
    ax4.set_title('Loading Time Distribution (Box Plot)', fontweight='bold')
    ax4.set_xlabel('Device Tier')
    ax4.set_ylabel('Duration (ms)')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar figura
    output_file = 'bq13_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Visualización guardada en: {output_file}")
    
    # Guardar resultados en CSV
    output_csv = 'bq13_results.csv'
    p95_overall.to_csv(output_csv, index=False)
    print(f"✅ Resultados guardados en: {output_csv}")
    
    print()
    print("=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description='BQ13: Analizar P95 app loading time')
    parser.add_argument('csv_file', help='Ruta al archivo CSV de analytics')
    parser.add_argument('--cutoff', help='Fecha de corte para comparación antes/después (YYYY-MM-DD)', default=None)
    
    args = parser.parse_args()
    
    if not Path(args.csv_file).exists():
        print(f"❌ Error: El archivo '{args.csv_file}' no existe")
        sys.exit(1)
    
    analyze_bq13(args.csv_file, args.cutoff)

if __name__ == "__main__":
    main()

