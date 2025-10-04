"""
Generador de Datos Sintéticos de Analytics
===========================================
Genera eventos de analytics realistas para testing y demos.

Usage:
    python generate_synthetic_data.py
    python generate_synthetic_data.py --events 1000 --output test_data.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import random

def generate_synthetic_data(num_events=500, output_file='synthetic_analytics.csv', days_back=30):
    """Genera datos sintéticos de analytics"""
    
    print(f"🔧 Generando {num_events} eventos sintéticos...")
    
    # Configuración
    device_tiers = ['low', 'mid', 'high']
    network_types = ['Wi-Fi', '5G', '4G', '3G', 'Cellular']
    event_types = ['app_launch_to_menu', 'payment_completed', 'menu_ready']
    payment_methods = ['wallet', 'credit_card', 'debit_card', 'paypal', 'google_pay']
    device_models = [
        'Google Pixel 7',
        'Samsung Galaxy S23',
        'OnePlus 11',
        'Xiaomi 13',
        'Google sdk_gphone64_x86_64',
        'Samsung Galaxy A54',
        'Motorola Edge 40',
        'iPhone 14 Pro',
        'Google Pixel 6a'
    ]
    screens = ['HomeActivity', 'MainActivity', 'DashboardActivity', 'MenuActivity']
    
    # Tiempos base realistas por tier y red (ms)
    base_times = {
        'app_launch_to_menu': {
            'low': {'Wi-Fi': 6000, '5G': 6500, '4G': 7000, '3G': 9000, 'Cellular': 8000},
            'mid': {'Wi-Fi': 4000, '5G': 4200, '4G': 4800, '3G': 6500, 'Cellular': 5500},
            'high': {'Wi-Fi': 2500, '5G': 2800, '4G': 3200, '3G': 4500, 'Cellular': 4000},
        },
        'payment_completed': {
            'low': {'Wi-Fi': 3000, '5G': 3200, '4G': 3800, '3G': 5000, 'Cellular': 4500},
            'mid': {'Wi-Fi': 2000, '5G': 2200, '4G': 2600, '3G': 3800, 'Cellular': 3200},
            'high': {'Wi-Fi': 1500, '5G': 1600, '4G': 1900, '3G': 2800, 'Cellular': 2400},
        },
        'menu_ready': {
            'low': {'Wi-Fi': 5000, '5G': 5200, '4G': 5800, '3G': 7500, 'Cellular': 6800},
            'mid': {'Wi-Fi': 3500, '5G': 3700, '4G': 4200, '3G': 5800, 'Cellular': 5000},
            'high': {'Wi-Fi': 2000, '5G': 2200, '4G': 2600, '3G': 3800, 'Cellular': 3200},
        }
    }
    
    events = []
    start_date = datetime.now() - timedelta(days=days_back)
    
    # Pesos para distribución más realista
    tier_weights = {'low': 0.3, 'mid': 0.5, 'high': 0.2}  # Más devices mid-tier
    network_weights = {'Wi-Fi': 0.5, '5G': 0.15, '4G': 0.25, '3G': 0.05, 'Cellular': 0.05}
    
    for i in range(num_events):
        # Timestamp aleatorio en los últimos N días
        days_offset = random.randint(0, days_back)
        hours_offset = random.randint(6, 23)  # Actividad entre 6 AM y 11 PM
        minutes_offset = random.randint(0, 59)
        seconds_offset = random.randint(0, 59)
        
        timestamp = start_date + timedelta(
            days=days_offset,
            hours=hours_offset,
            minutes=minutes_offset,
            seconds=seconds_offset
        )
        
        # Características aleatorias con pesos
        event_type = random.choice(event_types)
        device_tier = random.choices(
            list(tier_weights.keys()),
            weights=list(tier_weights.values())
        )[0]
        network_type = random.choices(
            list(network_weights.keys()),
            weights=list(network_weights.values())
        )[0]
        
        # Calcular duración con variación realista
        base_time = base_times[event_type][device_tier][network_type]
        
        # Simulación de mejoras de performance a lo largo del tiempo
        improvement_factor = 1.0 - (days_offset / days_back * 0.20)  # 20% mejora
        base_time *= improvement_factor
        
        # Variación aleatoria (±40%)
        variation = random.uniform(0.6, 1.4)
        duration = int(base_time * variation)
        
        # Algunos outliers ocasionales (5% de probabilidad)
        if random.random() < 0.05:
            duration = int(duration * random.uniform(2.0, 4.0))
        
        # Duración mínima
        duration = max(duration, 50)
        
        # Otros campos
        device_model = random.choice(device_models)
        os_api = random.choices([30, 31, 33, 34, 35, 36], weights=[0.05, 0.1, 0.2, 0.25, 0.25, 0.15])[0]
        android_version = f"Android {os_api - 21} (API {os_api})"
        app_version = "1.0"
        
        # Campos específicos por evento
        success = None
        payment_method = None
        screen = None
        
        if event_type == 'payment_completed':
            # Tasa de éxito alta en buenas redes, menor en malas
            if network_type in ['Wi-Fi', '5G']:
                success_prob = 0.98
            elif network_type == '4G':
                success_prob = 0.95
            else:
                success_prob = 0.88
            
            success = random.random() < success_prob
            payment_method = random.choice(payment_methods)
            
        elif event_type == 'menu_ready':
            screen = random.choice(screens)
        
        # Crear evento
        event = {
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'event_name': event_type,
            'duration_ms': duration,
            'network_type': network_type,
            'device_tier': device_tier,
            'os_api': os_api,
            'success': success if success is not None else '',
            'payment_method': payment_method if payment_method else '',
            'screen': screen if screen else '',
            'app_version': app_version,
            'device_model': device_model,
            'android_version': android_version
        }
        
        events.append(event)
    
    # Crear DataFrame y ordenar
    df = pd.DataFrame(events)
    df = df.sort_values('timestamp')
    
    # Guardar
    df.to_csv(output_file, index=False)
    
    # Estadísticas
    print(f"\n✅ {len(df)} eventos generados")
    print(f"✅ Guardado en: {output_file}")
    print(f"\n📊 Distribución de eventos:")
    print(df['event_name'].value_counts().to_string())
    print(f"\n📱 Device tiers:")
    print(df['device_tier'].value_counts().to_string())
    print(f"\n📡 Network types:")
    print(df['network_type'].value_counts().to_string())
    print(f"\n📅 Rango de fechas: {df['timestamp'].min()} a {df['timestamp'].max()}")
    
    if 'success' in df.columns and df['success'].notna().any():
        payment_df = df[df['event_name'] == 'payment_completed']
        if len(payment_df) > 0:
            success_rate = payment_df['success'].sum() / len(payment_df) * 100
            print(f"\n💳 Tasa de éxito de pagos: {success_rate:.1f}%")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Generar datos sintéticos de analytics')
    parser.add_argument('--events', type=int, default=500, help='Número de eventos a generar')
    parser.add_argument('--output', default='synthetic_analytics.csv', help='Archivo CSV de salida')
    parser.add_argument('--days', type=int, default=30, help='Días hacia atrás para generar eventos')
    
    args = parser.parse_args()
    
    generate_synthetic_data(args.events, args.output, args.days)

if __name__ == "__main__":
    main()

