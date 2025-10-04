"""
Generador de Datos Sintéticos de Compras para BQ4
==================================================
Genera datos realistas de compras completadas para testing y demos.

Usage:
    python scripts/generate_synthetic_orders.py --orders 100 --output data/synthetic_compras.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import random

def generate_synthetic_orders(num_orders=100, output_file='data/synthetic_compras.csv', days_back=7):
    """Genera datos sintéticos de compras"""
    
    print(f"🔧 Generando {num_orders} pedidos sintéticos...")
    
    # Configuración
    usuarios = ['andres', 'maria', 'carlos', 'lucia', 'pedro']
    items_menu = {
        'Hamburguesa': 7000,
        'Pizza': 9000,
        'Pasta': 14000,
        'Ensalada': 7000,
        'Sandwich': 7000,
        'Sushi': 22000,
        'Tacos': 15000,
        'Burrito': 13000,
        'Pollo': 18000,
        'Pescado': 25000
    }
    
    orders = []
    start_date = datetime.now() - timedelta(days=days_back)
    
    for i in range(1, num_orders + 1):
        # Timestamp aleatorio en los últimos N días
        days_offset = random.randint(0, days_back)
        # Más actividad en horas de comida
        hour_weights = {
            0: 0.1, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.2, 5: 0.5,
            6: 1.0, 7: 1.5, 8: 2.0, 9: 1.5, 10: 1.0, 11: 3.0,
            12: 5.0, 13: 4.0, 14: 2.0, 15: 1.5, 16: 1.5, 17: 2.0,
            18: 3.0, 19: 5.0, 20: 4.0, 21: 2.0, 22: 1.0, 23: 0.5
        }
        hour = random.choices(list(hour_weights.keys()), weights=list(hour_weights.values()))[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        fecha_creacion = start_date + timedelta(
            days=days_offset,
            hours=hour,
            minutes=minute,
            seconds=second
        )
        
        # Simular tiempos de preparación y espera
        # Tiempo hasta que empieza preparación (muy rápido, 5-30 seg)
        tiempo_hasta_prep = random.uniform(5, 30)
        fecha_en_preparacion = fecha_creacion + timedelta(seconds=tiempo_hasta_prep)
        
        # Tiempo de preparación (1-10 minutos, más en horas pico)
        is_peak = (12 <= hora <= 14) or (19 <= hour <= 21)
        if is_peak:
            tiempo_preparacion = random.uniform(120, 600)  # 2-10 min en peak
        else:
            tiempo_preparacion = random.uniform(60, 300)  # 1-5 min en off-peak
        
        fecha_listo = fecha_en_preparacion + timedelta(seconds=tiempo_preparacion)
        
        # Tiempo de espera para pickup (ESTE ES EL IMPORTANTE PARA BQ4)
        # En peak hours, tiende a ser más largo
        if is_peak:
            # Peak: más congestionado, tiempos más variados
            tiempo_espera_base = random.uniform(1, 120)  # 1 seg - 2 min
            # Algunos outliers por congestión
            if random.random() < 0.1:  # 10% outliers
                tiempo_espera_base = random.uniform(180, 600)  # 3-10 min
        else:
            # Off-peak: más rápido y consistente
            tiempo_espera_base = random.uniform(1, 60)  # 1-60 seg
            # Pocos outliers
            if random.random() < 0.05:  # 5% outliers
                tiempo_espera_base = random.uniform(120, 300)  # 2-5 min
        
        fecha_entregado = fecha_listo + timedelta(seconds=tiempo_espera_base)
        
        # Calcular totales
        total_cop = random.choice(list(items_menu.values()))
        # Pedidos múltiples
        if random.random() < 0.3:  # 30% son pedidos múltiples
            total_cop += random.choice(list(items_menu.values()))
        
        # Crear orden
        order = {
            'id_compra': i,
            'fecha_creacion': fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            'usuario_nombre': random.choice(usuarios),
            'usuario_email': f"{random.choice(usuarios)}@gmail.com",
            'total_cop': float(total_cop),
            'fecha_en_preparacion': fecha_en_preparacion.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_listo': fecha_listo.strftime('%Y-%m-%d %H:%M:%S'),
            'fecha_entregado': fecha_entregado.strftime('%Y-%m-%d %H:%M:%S'),
            'tiempo_hasta_preparacion_seg': round(tiempo_hasta_prep, 6),
            'tiempo_hasta_preparacion_min': round(tiempo_hasta_prep / 60, 2),
            'tiempo_preparacion_seg': round(tiempo_preparacion, 6),
            'tiempo_preparacion_min': round(tiempo_preparacion / 60, 2),
            'tiempo_espera_entrega_seg': round(tiempo_espera_base, 6),
            'tiempo_espera_entrega_min': round(tiempo_espera_base / 60, 2),
            'tiempo_total_seg': round(tiempo_hasta_prep + tiempo_preparacion + tiempo_espera_base, 6),
            'tiempo_total_min': round((tiempo_hasta_prep + tiempo_preparacion + tiempo_espera_base) / 60, 2)
        }
        
        orders.append(order)
    
    # Crear DataFrame y ordenar
    df = pd.DataFrame(orders)
    df = df.sort_values('fecha_creacion')
    
    # Guardar
    df.to_csv(output_file, index=False)
    
    # Estadísticas
    print(f"\n✅ {len(df)} pedidos generados")
    print(f"✅ Guardado en: {output_file}")
    
    # Analizar peak vs off-peak
    df['fecha_listo_dt'] = pd.to_datetime(df['fecha_listo'])
    df['hora'] = df['fecha_listo_dt'].dt.hour
    df['is_peak'] = df['hora'].apply(lambda h: (12 <= h < 14) or (19 <= h < 21))
    
    print(f"\n📊 Estadísticas:")
    print(f"   Peak orders: {df['is_peak'].sum()} ({df['is_peak'].sum()/len(df)*100:.1f}%)")
    print(f"   Off-peak orders: {(~df['is_peak']).sum()} ({(~df['is_peak']).sum()/len(df)*100:.1f}%)")
    print(f"\n⏱️ Tiempos de espera (pickup):")
    print(f"   Peak median:     {df[df['is_peak']]['tiempo_espera_entrega_seg'].median():.2f}s")
    print(f"   Off-peak median: {df[~df['is_peak']]['tiempo_espera_entrega_seg'].median():.2f}s")
    print(f"   Overall median:  {df['tiempo_espera_entrega_seg'].median():.2f}s")
    print(f"\n📅 Rango de fechas: {df['fecha_creacion'].min()} a {df['fecha_creacion'].max()}")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Generar datos sintéticos de compras para BQ4')
    parser.add_argument('--orders', type=int, default=100, help='Número de pedidos a generar')
    parser.add_argument('--output', default='data/synthetic_compras.csv', help='Archivo CSV de salida')
    parser.add_argument('--days', type=int, default=7, help='Días hacia atrás para generar pedidos')
    
    args = parser.parse_args()
    
    generate_synthetic_orders(args.orders, args.output, args.days)

if __name__ == "__main__":
    main()

