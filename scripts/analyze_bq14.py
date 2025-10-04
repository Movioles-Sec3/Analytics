"""
BQ14 Analysis Script
====================
Pregunta: ¿Cuál es el tiempo P95 desde tap en "Pay" hasta pago confirmado,
segmentado por tipo de red (Wi-Fi/4G/5G) y clase de dispositivo?

Usage:
    python scripts/analyze_bq14.py "data/analytics_events.csv"
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

def analyze_bq14(csv_path):
    """Analiza BQ14: P95 payment completion time por network y device class"""
    
    print("=" * 80)
    print("BQ14: P95 PAYMENT COMPLETION TIME ANALYSIS")
    print("=" * 80)
    
    # Cargar datos
    try:
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        print(f"✅ Cargados {len(df)} eventos desde {csv_path}")
    except Exception as e:
        print(f"❌ Error cargando CSV: {e}")
        sys.exit(1)
    
    # Filtrar eventos payment_completed
    payment_df = df[df['event_name'] == 'payment_completed'].copy()
    
    if len(payment_df) == 0:
        print("❌ No se encontraron eventos 'payment_completed'!")
        sys.exit(1)
    
    print(f"💳 Total eventos de pago: {len(payment_df)}")
    print(f"📅 Rango de fechas: {payment_df['timestamp'].min()} a {payment_df['timestamp'].max()}")
    
    # Tasa de éxito
    if 'success' in payment_df.columns:
        success_count = payment_df['success'].sum()
        success_rate = (success_count / len(payment_df) * 100) if len(payment_df) > 0 else 0
        print(f"✅ Tasa de éxito: {success_rate:.2f}% ({success_count}/{len(payment_df)})")
    print()
    
    # Análisis P95 por network type y device class
    print("-" * 80)
    print("P95 PAYMENT TIME POR NETWORK TYPE & DEVICE CLASS")
    print("-" * 80)
    
    p95_overall = payment_df.groupby(['network_type', 'device_tier'])['duration_ms'].agg([
        ('count', 'count'),
        ('mean', 'mean'),
        ('median', 'median'),
        ('p95', calculate_p95),
        ('max', 'max')
    ]).reset_index()
    
    print(p95_overall.to_string(index=False))
    print()
    
    # Resumen por network type
    print("-" * 80)
    print("P95 POR NETWORK TYPE")
    print("-" * 80)
    by_network = payment_df.groupby('network_type')['duration_ms'].agg([
        ('count', 'count'),
        ('p95', calculate_p95)
    ]).reset_index()
    for _, row in by_network.iterrows():
        print(f"  {row['network_type']:>10}: {format_duration(row['p95']):>8} (n={row['count']})")
    print()
    
    # Resumen por device tier
    print("-" * 80)
    print("P95 POR DEVICE TIER")
    print("-" * 80)
    by_tier = payment_df.groupby('device_tier')['duration_ms'].agg([
        ('count', 'count'),
        ('p95', calculate_p95)
    ]).reset_index()
    for _, row in by_tier.iterrows():
        print(f"  {row['device_tier']:>6}: {format_duration(row['p95']):>8} (n={row['count']})")
    print()
    
    # Tasa de éxito por segmento
    if 'success' in payment_df.columns:
        print("-" * 80)
        print("TASA DE ÉXITO POR SEGMENTO")
        print("-" * 80)
        success_by_segment = payment_df.groupby(['network_type', 'device_tier']).agg({
            'success': ['sum', 'count', 'mean']
        }).reset_index()
        success_by_segment.columns = ['network_type', 'device_tier', 'successful', 'total', 'rate']
        success_by_segment['rate'] = (success_by_segment['rate'] * 100).round(2)
        print(success_by_segment.to_string(index=False))
        print()
    
    # Análisis por método de pago (si existe)
    if 'payment_method' in payment_df.columns and payment_df['payment_method'].notna().any():
        print("-" * 80)
        print("P95 POR MÉTODO DE PAGO")
        print("-" * 80)
        by_method = payment_df.groupby('payment_method')['duration_ms'].agg([
            ('count', 'count'),
            ('p95', calculate_p95)
        ]).reset_index()
        print(by_method.to_string(index=False))
        print()
    
    # Escenarios más lentos
    print("-" * 80)
    print("TOP 5 ESCENARIOS MÁS LENTOS (por P95)")
    print("-" * 80)
    slowest = p95_overall.nlargest(5, 'p95')[['network_type', 'device_tier', 'p95', 'count']]
    for idx, row in slowest.iterrows():
        print(f"  {row['network_type']:>10} + {row['device_tier']:>6}: {format_duration(row['p95']):>8} (n={row['count']})")
    print()
    
    # Generar visualizaciones
    print("-" * 80)
    print("GENERANDO VISUALIZACIONES...")
    print("-" * 80)
    
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('BQ14: P95 Payment Completion Time Analysis', fontsize=16, fontweight='bold')
    
    # Plot 1: Barras por network type y device tier
    ax1 = axes[0, 0]
    pivot_data = p95_overall.pivot(index='network_type', columns='device_tier', values='p95')
    pivot_data = pivot_data.reindex(columns=['low', 'mid', 'high'])
    pivot_data.plot(kind='bar', ax=ax1, rot=45)
    ax1.set_title('P95 Payment Time por Network Type y Device Tier', fontweight='bold')
    ax1.set_xlabel('Network Type')
    ax1.set_ylabel('P95 Duration (ms)')
    ax1.legend(title='Device Tier')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Heatmap
    ax2 = axes[0, 1]
    pivot_heatmap = p95_overall.pivot(index='device_tier', columns='network_type', values='p95')
    pivot_heatmap = pivot_heatmap.reindex(['low', 'mid', 'high'])
    sns.heatmap(pivot_heatmap, annot=True, fmt='.0f', cmap='Reds', ax=ax2, cbar_kws={'label': 'P95 (ms)'})
    ax2.set_title('P95 Payment Time Heatmap', fontweight='bold')
    ax2.set_xlabel('Network Type')
    ax2.set_ylabel('Device Tier')
    
    # Plot 3: Distribución por network type
    ax3 = axes[1, 0]
    for net_type in payment_df['network_type'].unique():
        data = payment_df[payment_df['network_type'] == net_type]['duration_ms']
        if len(data) > 0:
            ax3.hist(data, bins=30, alpha=0.5, label=net_type)
    ax3.set_title('Distribución de Payment Time por Network Type', fontweight='bold')
    ax3.set_xlabel('Duration (ms)')
    ax3.set_ylabel('Frequency')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Tasa de éxito o Box plot
    ax4 = axes[1, 1]
    if 'success' in payment_df.columns:
        success_pivot = success_by_segment.pivot(index='device_tier', columns='network_type', values='rate')
        success_pivot = success_pivot.reindex(['low', 'mid', 'high'])
        sns.heatmap(success_pivot, annot=True, fmt='.1f', cmap='RdYlGn', ax=ax4, 
                    vmin=0, vmax=100, cbar_kws={'label': 'Success Rate (%)'})
        ax4.set_title('Tasa de Éxito de Pagos por Segmento', fontweight='bold')
        ax4.set_xlabel('Network Type')
        ax4.set_ylabel('Device Tier')
    else:
        payment_df_sorted = payment_df.copy()
        payment_df_sorted['device_tier'] = pd.Categorical(
            payment_df_sorted['device_tier'],
            categories=['low', 'mid', 'high'],
            ordered=True
        )
        sns.boxplot(data=payment_df_sorted, x='network_type', y='duration_ms', hue='device_tier', ax=ax4)
        ax4.set_title('Payment Time Distribution (Box Plot)', fontweight='bold')
        ax4.set_xlabel('Network Type')
        ax4.set_ylabel('Duration (ms)')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar figura
    output_file = 'bq14_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Visualización guardada en: {output_file}")
    
    # Guardar resultados en CSV
    output_csv = 'bq14_results.csv'
    p95_overall.to_csv(output_csv, index=False)
    print(f"✅ Resultados guardados en: {output_csv}")
    
    if 'success' in payment_df.columns:
        success_csv = 'bq14_success_rates.csv'
        success_by_segment.to_csv(success_csv, index=False)
        print(f"✅ Tasas de éxito guardadas en: {success_csv}")
    
    print()
    print("=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description='BQ14: Analizar P95 payment completion time')
    parser.add_argument('csv_file', help='Ruta al archivo CSV de analytics')
    
    args = parser.parse_args()
    
    if not Path(args.csv_file).exists():
        print(f"❌ Error: El archivo '{args.csv_file}' no existe")
        sys.exit(1)
    
    analyze_bq14(args.csv_file)

if __name__ == "__main__":
    main()

