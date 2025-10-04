"""
Data Transformation Pipeline
=============================
Transforma los datos crudos de analytics agregando columnas derivadas
y métricas calculadas para facilitar el análisis.

Transformaciones aplicadas:
1. Categorización de performance (fast/medium/slow)
2. Hora del día (morning/afternoon/evening/night)
3. Performance score (0-100)
4. Detección de outliers
5. Día de la semana
6. Flags de calidad de red

Usage:
    python transform_data.py "Pipelines Kotlin/Datos Kotlin/analytics_events.csv"
"""

import pandas as pd
import numpy as np
import argparse
from datetime import datetime
import sys

def categorize_performance(row):
    """Categoriza el performance según el tipo de evento y duración"""
    event_type = row['event_name']
    duration = row['duration_ms']
    
    # Umbrales por tipo de evento
    thresholds = {
        'app_launch_to_menu': {'fast': 3000, 'medium': 6000},
        'payment_completed': {'fast': 1500, 'medium': 3000},
        'menu_ready': {'fast': 2500, 'medium': 5000}
    }
    
    if event_type not in thresholds:
        return 'unknown'
    
    t = thresholds[event_type]
    if duration < t['fast']:
        return 'fast'
    elif duration < t['medium']:
        return 'medium'
    else:
        return 'slow'

def calculate_performance_score(row):
    """
    Calcula un score de performance (0-100)
    100 = excelente, 0 = muy malo
    """
    event_type = row['event_name']
    duration = row['duration_ms']
    
    # Tiempos ideales y máximos aceptables (ms)
    benchmarks = {
        'app_launch_to_menu': {'ideal': 2000, 'max': 10000},
        'payment_completed': {'ideal': 1000, 'max': 5000},
        'menu_ready': {'ideal': 1500, 'max': 8000}
    }
    
    if event_type not in benchmarks:
        return 50
    
    ideal = benchmarks[event_type]['ideal']
    max_time = benchmarks[event_type]['max']
    
    # Calcular score inversamente proporcional a la duración
    if duration <= ideal:
        return 100
    elif duration >= max_time:
        return 0
    else:
        # Interpolación lineal entre ideal y max
        score = 100 * (1 - (duration - ideal) / (max_time - ideal))
        return max(0, min(100, score))

def get_time_of_day(timestamp):
    """Determina la hora del día"""
    hour = timestamp.hour
    if 5 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 18:
        return 'afternoon'
    elif 18 <= hour < 22:
        return 'evening'
    else:
        return 'night'

def is_outlier(series, value):
    """Detecta si un valor es outlier usando IQR method"""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return value < lower_bound or value > upper_bound

def categorize_network_quality(network_type):
    """Categoriza la calidad de la red"""
    quality_map = {
        'Wi-Fi': 'excellent',
        '5G': 'excellent',
        '4G': 'good',
        '3G': 'poor',
        'Cellular': 'fair',
        'Offline': 'none'
    }
    return quality_map.get(network_type, 'unknown')

def transform_analytics_data(input_csv, output_csv=None):
    """Aplica todas las transformaciones a los datos"""
    
    print("=" * 80)
    print("DATA TRANSFORMATION PIPELINE")
    print("=" * 80)
    print(f"Input: {input_csv}")
    
    # Cargar datos
    try:
        df = pd.read_csv(input_csv)
        print(f"✅ Loaded {len(df)} events")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        sys.exit(1)
    
    # Convertir timestamp a datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print("\n" + "-" * 80)
    print("APPLYING TRANSFORMATIONS")
    print("-" * 80)
    
    # 1. Categorización de performance
    print("1. Categorizing performance (fast/medium/slow)...")
    df['performance_category'] = df.apply(categorize_performance, axis=1)
    
    # 2. Performance score
    print("2. Calculating performance score (0-100)...")
    df['performance_score'] = df.apply(calculate_performance_score, axis=1).round(2)
    
    # 3. Hora del día
    print("3. Extracting time of day...")
    df['time_of_day'] = df['timestamp'].apply(get_time_of_day)
    
    # 4. Día de la semana
    print("4. Extracting day of week...")
    df['day_of_week'] = df['timestamp'].dt.day_name()
    df['is_weekend'] = df['timestamp'].dt.dayofweek >= 5
    
    # 5. Detección de outliers (por tipo de evento)
    print("5. Detecting outliers...")
    df['is_outlier'] = False
    for event_type in df['event_name'].unique():
        mask = df['event_name'] == event_type
        event_durations = df[mask]['duration_ms']
        df.loc[mask, 'is_outlier'] = event_durations.apply(
            lambda x: is_outlier(event_durations, x)
        )
    
    # 6. Calidad de red
    print("6. Categorizing network quality...")
    df['network_quality'] = df['network_type'].apply(categorize_network_quality)
    
    # 7. Duración en segundos (más legible)
    print("7. Adding duration in seconds...")
    df['duration_sec'] = (df['duration_ms'] / 1000).round(3)
    
    # 8. Device tier como numérico (para correlaciones)
    print("8. Converting device tier to numeric...")
    tier_map = {'low': 1, 'mid': 2, 'high': 3}
    df['device_tier_numeric'] = df['device_tier'].map(tier_map)
    
    # 9. Combinación de factores (para segmentación avanzada)
    print("9. Creating combined segments...")
    df['segment'] = df['device_tier'] + '_' + df['network_type']
    
    # 10. Fecha sin hora (para agregaciones diarias)
    print("10. Extracting date...")
    df['date'] = df['timestamp'].dt.date
    
    # Estadísticas de transformación
    print("\n" + "-" * 80)
    print("TRANSFORMATION SUMMARY")
    print("-" * 80)
    print(f"Total events: {len(df)}")
    print(f"New columns added: 11")
    print(f"\nPerformance distribution:")
    print(df['performance_category'].value_counts())
    print(f"\nAverage performance score: {df['performance_score'].mean():.2f}/100")
    print(f"\nOutliers detected: {df['is_outlier'].sum()} ({df['is_outlier'].sum()/len(df)*100:.1f}%)")
    print(f"\nTime of day distribution:")
    print(df['time_of_day'].value_counts())
    
    # Guardar datos transformados
    if output_csv is None:
        output_csv = input_csv.replace('.csv', '_transformed.csv')
    
    df.to_csv(output_csv, index=False)
    print(f"\n✅ Transformed data saved to: {output_csv}")
    
    # Mostrar muestra de datos transformados
    print("\n" + "-" * 80)
    print("SAMPLE OF TRANSFORMED DATA (first 5 rows)")
    print("-" * 80)
    
    # Mostrar solo las columnas nuevas
    new_columns = [
        'event_name', 'duration_ms', 'performance_category', 
        'performance_score', 'time_of_day', 'day_of_week',
        'is_outlier', 'network_quality', 'segment'
    ]
    print(df[new_columns].head().to_string())
    
    print("\n" + "=" * 80)
    print("TRANSFORMATION COMPLETE")
    print("=" * 80)
    
    return output_csv

def main():
    parser = argparse.ArgumentParser(
        description='Transform analytics data with derived columns'
    )
    parser.add_argument(
        'input_csv',
        help='Path to input CSV file'
    )
    parser.add_argument(
        '--output',
        help='Path to output CSV file (default: input_transformed.csv)',
        default=None
    )
    
    args = parser.parse_args()
    
    transform_analytics_data(args.input_csv, args.output)

if __name__ == "__main__":
    main()

