# 📊 Analytics Dashboard - BQ13, BQ14, BQ4 & BQ5

Dashboard y scripts de análisis para responder preguntas de negocio sobre performance de app, pagos, tiempos de pickup, reorders y picos de pedidos.

## 📋 Preguntas de Negocio

### BQ13: App Loading Time
> ¿Cuál es el tiempo P95 de carga de la app (desde apertura hasta menú usable) por clase de dispositivo y condiciones de red, y cómo cambia después de optimizaciones de performance?

**Eventos analizados**: `app_launch_to_menu`  
**Scripts**: `scripts/analyze_bq13.py`

### BQ14: Payment Completion Time
> ¿Cuál es el tiempo P95 desde tap en "Pay" hasta pago confirmado, segmentado por tipo de red (Wi-Fi/4G/5G) y clase de dispositivo?

**Eventos analizados**: `payment_completed`  
**Scripts**: `scripts/analyze_bq14.py`

### BQ4: Pickup Waiting Time ⏱️
> ¿Cuál es el tiempo de espera mediano desde "pedido listo" hasta "pedido recogido", segmentado por horas pico vs valle?

**Datos analizados**: Compras completadas  
**Scripts**: `scripts/analyze_bq4.py`, `scripts/dashboard_bq4.py`  
**Documentación**: [docs/BQ4.md](docs/BQ4.md) | [Quick Start](docs/QUICKSTART_BQ4.md)

### BQ5: Reorders by Category and Time 🔁
> ¿Qué categorías de productos se reordenan más frecuentemente y en qué horarios?

**Datos analizados**: Reorders por categoría  
**Pipeline**: `app/pipelines/bq5.py`  
**Backend**: `/analytics/reorders-by-category`

### Most Requested Categories 🏆 (NEW)
> ¿Cuáles son las categorías más solicitadas por los usuarios?

**Datos analizados**: Órdenes agregadas por categoría  
**Pipeline**: `app/pipelines/most_requested_categories.py`  
**View**: `app/views/most_requested_categories.py`  
**Backend**: `/analytics/most-requested-categories`  
**Documentación**: [docs/MOST_REQUESTED_CATEGORIES.md](docs/MOST_REQUESTED_CATEGORIES.md)

### Order Peak Hours 🕐 (NEW)
> ¿En qué horas está el pico de pedidos?

**Datos analizados**: Órdenes por hora  
**Pipeline**: `app/pipelines/order_peak_hours.py`  
**View**: `app/views/order_peak_hours.py`  
**Backend**: `/analytics/order-peak-hours`  
**Documentación**: [docs/ORDER_PEAK_HOURS.md](docs/ORDER_PEAK_HOURS.md)

### Product Search Peak Hours 🔎 (NEW)
> ¿En qué horas del día los usuarios usan con mayor frecuencia el buscador de productos?

**Eventos analizados**: `GET /productos/buscar` registrados  
**Pipeline**: `app/pipelines/product_search_peak_hours.py`  
**View**: `app/views/product_search_peak_hours.py`  
**Backend**: `/analytics/product-search-peak-hours`  
**Documentación**: [docs/PRODUCT_SEARCH_PEAK_HOURS.md](docs/PRODUCT_SEARCH_PEAK_HOURS.md)

---

## 🚀 Instalación Rápida

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Verificar instalación

```bash
python -c "import streamlit; import pandas; print('✅ Todo instalado')"
```

---

## 📊 Uso

### 🎯 Opción 1: Dashboard Interactivo (Recomendado)

```bash
streamlit run app/dashboard.py
```

El dashboard se abre en http://localhost:8501 y permite:
- 📁 Cargar CSV drag & drop
- 📱 Analizar BQ13 con comparación antes/después
- 💳 Analizar BQ14 con tasas de éxito
- ⏱️ Analizar BQ4 con tiempos de pickup
- 🔁 Analizar BQ5 con reorders por categoría
- 🏆 **Analizar Most Requested Categories** - ranking de categorías más vendidas
- 🕐 **Analizar Order Peak Hours** - identificar horas pico de pedidos
- 🔎 **Analizar Product Search Peak Hours** - descubrir horas pico de búsquedas
- ⭐ Ver productos recomendados
- 📈 Gráficos interactivos (zoom, pan, export)
- 🔍 Explorar datos crudos con filtros

### 📈 Opción 2: Scripts de Análisis

#### BQ13 (App Loading)

```bash
# Análisis básico
python scripts/analyze_bq13.py "data/analytics_events.csv"

# Con comparación antes/después
python scripts/analyze_bq13.py "data/analytics_events.csv" --cutoff "2025-10-05"
```

**Salidas**:
- `bq13_analysis.png` - 4 visualizaciones
- `bq13_results.csv` - Tabla de P95

#### BQ14 (Payment Time)

```bash
python scripts/analyze_bq14.py "data/analytics_events.csv"
```

**Salidas**:
- `bq14_analysis.png` - 4 visualizaciones
- `bq14_results.csv` - Tabla de P95
- `bq14_success_rates.csv` - Tasas de éxito

---

## 🔧 Transformación de Datos

Transforma los datos crudos agregando columnas derivadas (performance category, time of day, outlier detection, etc.):

```bash
python scripts/transform_data.py "data/analytics_events.csv"
```

**Columnas agregadas**:
- `performance_category` (fast/medium/slow)
- `performance_score` (0-100)
- `time_of_day` (morning/afternoon/evening/night)
- `day_of_week` + `is_weekend`
- `is_outlier` (detección de valores atípicos)
- `network_quality` (excellent/good/fair/poor)
- `duration_sec` (duración en segundos)
- `device_tier_numeric` (1/2/3)
- `segment` (combinación tier + network)
- `date` (fecha sin hora)

**Salida**: `analytics_events_transformed.csv`

---

## 🧪 Generar Datos Sintéticos

Para testing o demos:

```bash
python scripts/generate_synthetic_data.py --events 500 --days 30
```

---

## 📂 Formato del CSV

```csv
timestamp,event_name,duration_ms,network_type,device_tier,os_api,success,payment_method,screen,app_version,device_model,android_version
2025-10-04 19:13:12.801,menu_ready,5026,Wi-Fi,low,36,,,HomeActivity,1.0,Google sdk_gphone64_x86_64,Android 16 (API 36)
2025-10-04 19:13:13.818,app_launch_to_menu,6060,Wi-Fi,low,36,,,,1.0,Google sdk_gphone64_x86_64,Android 16 (API 36)
2025-10-04 19:13:59.660,payment_completed,159,Wi-Fi,low,36,true,wallet,,,Google sdk_gphone64_x86_64,Android 16 (API 36)
```

### Columnas Requeridas

| Columna | Descripción | Valores |
|---------|-------------|---------|
| `timestamp` | Fecha y hora | `YYYY-MM-DD HH:MM:SS.mmm` |
| `event_name` | Tipo de evento | `app_launch_to_menu`, `payment_completed`, `menu_ready` |
| `duration_ms` | Duración en milisegundos | Número entero |
| `network_type` | Tipo de red | `Wi-Fi`, `5G`, `4G`, `3G`, `Cellular`, `Offline` |
| `device_tier` | Clase de dispositivo | `low`, `mid`, `high` |
| `os_api` | API Level de Android | 30, 31, 33, 34, 35, 36 |
| `success` | Éxito del pago | `true`/`false` (solo para `payment_completed`) |
| `payment_method` | Método de pago | `wallet`, `credit_card`, etc. |
| `device_model` | Modelo del dispositivo | String |
| `android_version` | Versión de Android | `Android X (API Y)` |

---

## 📊 Métricas Clave

### ¿Qué es P95?

El **percentil 95** significa que el 95% de los eventos tienen un tiempo ≤ ese valor.

**¿Por qué P95 y no promedio?**
- ✅ Ignora outliers extremos (top 5%)
- ✅ Representa la experiencia de la mayoría
- ✅ Útil para SLAs y objetivos de performance

### Segmentaciones

**Device Tier** (por RAM):
- `low`: < 2GB RAM
- `mid`: 2-4GB RAM
- `high`: > 4GB RAM

**Network Type**:
- Wi-Fi, 5G, 4G, 3G, Cellular, Offline

---

## 🎯 Casos de Uso

### Caso 1: Exploración Rápida
```bash
streamlit run app/dashboard.py
# Carga tu CSV y explora visualmente
```

### Caso 2: Reportes para Presentaciones
```bash
python scripts/analyze_bq13.py "data/analytics_events.csv"
python scripts/analyze_bq14.py "data/analytics_events.csv"
# Genera PNGs de alta calidad para slides
```

### Caso 3: Análisis de A/B Testing
```bash
python analyze_bq13.py data.csv --cutoff "2025-10-05"
# Compara performance antes/después de un cambio
```

### Caso 4: Data Engineering Pipeline
```bash
python scripts/transform_data.py raw_data.csv --output processed_data.csv
python scripts/analyze_bq13.py processed_data.csv
# Pipeline automatizado
```

---

## 📈 Visualizaciones Generadas

### Dashboard (Streamlit)
- Bar charts interactivos por segmento
- Heatmaps de performance
- Box plots con outliers
- Time series de tendencias
- Tablas filtrables
- Export a CSV

### Scripts (Matplotlib)
- 4 gráficos por análisis en PNG (300 DPI)
- Tablas de resultados en CSV
- Output detallado en consola

---

## 🔧 Troubleshooting

### Error: "No module named 'streamlit'"
```bash
pip install streamlit
```

### Error: "No 'app_launch_to_menu' events found"
Verifica que tu CSV tenga eventos con ese `event_name`.

### Dashboard no abre en navegador
Abre manualmente: http://localhost:8501

### Puerto 8501 ocupado
```bash
streamlit run app/dashboard.py --server.port 8502
```

### Error al cargar CSV
- Verifica que el archivo existe
- Revisa que tenga todas las columnas requeridas
- Asegúrate de usar la ruta correcta (con comillas si tiene espacios)

---

## 📁 Estructura del Proyecto

```
Analytics/
├── app/
│   └── dashboard.py                      # Dashboard interactivo
├── scripts/
│   ├── analyze_bq13.py                   # Script BQ13
│   ├── analyze_bq14.py                   # Script BQ14
│   ├── transform_data.py                 # Transformación de datos
│   └── generate_synthetic_data.py        # Generador de datos sintéticos
├── data/
│   └── analytics_events.csv              # Datos de ejemplo
├── docs/
│   └── QUICKSTART.md                     # Guía rápida
├── requirements.txt                      # Dependencias Python
├── README.md                             # Este archivo
└── .gitignore                            # Ignorar archivos locales
```

---

## 💡 Tips y Mejores Prácticas

1. **Usa el dashboard** para exploración rápida y análisis ad-hoc
2. **Usa los scripts** para reportes automatizados y CI/CD
3. **Transforma los datos primero** si necesitas análisis avanzados
4. **Genera datos sintéticos** para testing antes de producción
5. **Exporta los datos filtrados** del dashboard para análisis custom

---

## 🔗 Integración con Android App

Para obtener el CSV desde tu app Android:

```kotlin
// Obtener ruta del CSV
val csvPath = AnalyticsLogger.getCSVFilePath(context)
Log.d("Analytics", "CSV path: $csvPath")

// Compartir CSV
val file = File(csvPath)
val uri = FileProvider.getUriForFile(
    context,
    "${context.packageName}.provider",
    file
)
// ... compartir con Intent
```

---

## 📧 Soporte

Para problemas:
1. Revisa este README
2. Ejecuta los scripts con `--help`
3. Verifica los logs en consola (muy verbosos)

---

**Última actualización**: Octubre 2025  
**Versión**: 2.0  
**Python**: 3.8+

