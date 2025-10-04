"""
Transformación de Datos de Compras para BQ4
============================================
Agrega columnas derivadas para análisis de tiempos de recogida:
- Clasificación de horas pico vs valle
- Categorización de tiempos de espera
- Día de la semana y segmentaciones temporales

Usage:
    python scripts/transform_pickup_data.py data/compras_completadas_20251004_172958.csv
"""

import pandas as pd
import numpy as np
import argparse
import sys
from pathlib import Path

def classify_peak_hours(hour):
    """
    Clasifica las horas como pico o valle
    Peak hours: 12-14 (almuerzo) y 19-21 (cena)
    Off-peak: resto del día
    """
    if (12 <= hour < 14) or (19 <= hour < 21):
        return 'peak'
    else:
        return 'off-peak'

def get_meal_period(hour):
    """Identifica el periodo de comida"""
    if 6 <= hour < 11:
        return 'breakfast'
    elif 11 <= hour < 15:
        return 'lunch'
    elif 15 <= hour < 18:
        return 'snack'
    elif 18 <= hour < 22:
        return 'dinner'
    else:
        return 'late_night'

def categorize_waiting_time(seconds):
    """Categoriza el tiempo de espera"""
    if seconds < 5:
        return 'instant'  # < 5 segundos
    elif seconds < 30:
        return 'very_fast'  # < 30 segundos
    elif seconds < 60:
        return 'fast'  # < 1 minuto
    elif seconds < 300:
        return 'normal'  # 1-5 minutos
    elif seconds < 600:
        return 'slow'  # 5-10 minutos
    else:
        return 'very_slow'  # > 10 minutos

def categorize_order_value(value):
    """Categoriza el valor del pedido"""
    if value < 10000:
        return 'low'
    elif value < 30000:
        return 'medium'
    elif value < 60000:
        return 'high'
    else:
        return 'very_high'

def transform_pickup_data(input_csv, output_csv=None):
    """Aplica transformaciones a los datos de compras"""
    
    print("=" * 80)
    print("TRANSFORMACIÓN DE DATOS DE PICKUP (BQ4)")
    print("=" * 80)
    print(f"Input: {input_csv}")
    
    # Cargar datos
    try:
        df = pd.read_csv(input_csv)
        print(f"✅ Cargados {len(df)} pedidos")
    except Exception as e:
        print(f"❌ Error cargando CSV: {e}")
        sys.exit(1)
    
    # Convertir fechas
    df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'])
    df['fecha_listo'] = pd.to_datetime(df['fecha_listo'])
    df['fecha_entregado'] = pd.to_datetime(df['fecha_entregado'])
    
    print("\n" + "-" * 80)
    print("APLICANDO TRANSFORMACIONES")
    print("-" * 80)
    
    # 1. Extraer información temporal de "fecha_listo" (momento de la notificación)
    print("1. Extrayendo información temporal...")
    df['hora_listo'] = df['fecha_listo'].dt.hour
    df['dia_semana'] = df['fecha_listo'].dt.day_name()
    df['es_fin_semana'] = df['fecha_listo'].dt.dayofweek >= 5
    df['fecha'] = df['fecha_listo'].dt.date
    
    # 2. Clasificar horas pico vs valle
    print("2. Clasificando peak vs off-peak hours...")
    df['periodo_hora'] = df['hora_listo'].apply(classify_peak_hours)
    
    # 3. Identificar periodo de comida
    print("3. Identificando periodo de comida...")
    df['periodo_comida'] = df['hora_listo'].apply(get_meal_period)
    
    # 4. Categorizar tiempo de espera (tiempo_espera_entrega_seg)
    print("4. Categorizando tiempos de espera...")
    df['categoria_espera'] = df['tiempo_espera_entrega_seg'].apply(categorize_waiting_time)
    
    # 5. Categorizar valor del pedido
    print("5. Categorizando valor de pedidos...")
    df['categoria_valor'] = df['total_cop'].apply(categorize_order_value)
    
    # 6. Calcular métricas adicionales
    print("6. Calculando métricas adicionales...")
    
    # Tiempo total desde creación hasta entrega (en horas)
    df['tiempo_total_horas'] = df['tiempo_total_min'] / 60
    
    # Porcentaje del tiempo total que es espera de pickup
    df['pct_espera_pickup'] = (df['tiempo_espera_entrega_seg'] / df['tiempo_total_seg'] * 100).round(2)
    
    # 7. Detección de outliers en tiempo de espera
    print("7. Detectando outliers...")
    Q1 = df['tiempo_espera_entrega_seg'].quantile(0.25)
    Q3 = df['tiempo_espera_entrega_seg'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df['es_outlier'] = (df['tiempo_espera_entrega_seg'] < lower_bound) | (df['tiempo_espera_entrega_seg'] > upper_bound)
    
    # 8. Hora exacta (con formato)
    print("8. Formateando hora de notificación...")
    df['hora_listo_str'] = df['fecha_listo'].dt.strftime('%H:%M:%S')
    
    # 9. Segmento combinado
    print("9. Creando segmentos combinados...")
    df['segmento'] = df['periodo_hora'] + '_' + df['dia_semana'].str.lower()
    
    # Estadísticas de transformación
    print("\n" + "-" * 80)
    print("RESUMEN DE TRANSFORMACIONES")
    print("-" * 80)
    print(f"Total pedidos: {len(df)}")
    print(f"Nuevas columnas agregadas: 12")
    print(f"\nDistribución Peak vs Off-Peak:")
    print(df['periodo_hora'].value_counts())
    print(f"\nPedidos por periodo de comida:")
    print(df['periodo_comida'].value_counts())
    print(f"\nCategorías de tiempo de espera:")
    print(df['categoria_espera'].value_counts())
    print(f"\nOutliers detectados: {df['es_outlier'].sum()} ({df['es_outlier'].sum()/len(df)*100:.1f}%)")
    print(f"\nTiempo mediano de espera:")
    print(f"  Peak hours:     {df[df['periodo_hora']=='peak']['tiempo_espera_entrega_seg'].median():.2f} seg")
    print(f"  Off-peak hours: {df[df['periodo_hora']=='off-peak']['tiempo_espera_entrega_seg'].median():.2f} seg")
    
    # Guardar datos transformados
    if output_csv is None:
        output_csv = input_csv.replace('.csv', '_transformed.csv')
    
    df.to_csv(output_csv, index=False)
    print(f"\n✅ Datos transformados guardados en: {output_csv}")
    
    # Mostrar muestra
    print("\n" + "-" * 80)
    print("MUESTRA DE DATOS TRANSFORMADOS (primeras 5 filas)")
    print("-" * 80)
    cols_to_show = [
        'id_compra', 'fecha_listo', 'hora_listo', 'periodo_hora', 
        'periodo_comida', 'tiempo_espera_entrega_seg', 'categoria_espera'
    ]
    print(df[cols_to_show].head().to_string(index=False))
    
    print("\n" + "=" * 80)
    print("TRANSFORMACIÓN COMPLETADA")
    print("=" * 80)
    
    return output_csv

def main():
    parser = argparse.ArgumentParser(
        description='Transformar datos de compras para análisis BQ4'
    )
    parser.add_argument(
        'input_csv',
        help='Ruta al archivo CSV de compras'
    )
    parser.add_argument(
        '--output',
        help='Ruta al archivo CSV de salida (default: input_transformed.csv)',
        default=None
    )
    
    args = parser.parse_args()
    
    if not Path(args.input_csv).exists():
        print(f"❌ Error: El archivo '{args.input_csv}' no existe")
        sys.exit(1)
    
    transform_pickup_data(args.input_csv, args.output)

if __name__ == "__main__":
    main()

