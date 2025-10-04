
# ⏱️ BQ4: Pickup Waiting Time Analysis

Análisis del tiempo de espera desde "pedido listo" hasta "pedido recogido", segmentado por horas pico vs valle.

## 📋 Pregunta de Negocio

> **BQ4**: ¿Cuál es el tiempo de espera mediano desde la notificación de "pedido listo" hasta el "pedido recogido", segmentado por horas pico vs horas valle?

**Métricas clave**:
- **Orden listo**: `fecha_listo`
- **Orden recogida**: `fecha_entregado`
- **Tiempo de espera**: `tiempo_espera_entrega_seg`

**Segmentación**:
- **Peak hours** (horas pico): 12:00-14:00 (almuerzo) y 19:00-21:00 (cena)
- **Off-peak hours** (horas valle): Resto del día

---

## 🚀 Uso Rápido

### 1. Dashboard Interactivo (Recomendado)

```bash
streamlit run scripts/dashboard_bq4.py
```

El dashboard abre en http://localhost:8501 y muestra:
- 📊 Comparación peak vs off-peak
- 🕐 Análisis por hora del día
- 📅 Análisis por día de semana
- 📈 Datos crudos con filtros

### 2. Script de Análisis

```bash
python scripts/analyze_bq4.py data/compras_completadas_20251004_172958.csv
```

**Salidas generadas**:
- `bq4_analysis.png` - 4 visualizaciones (box plot, por hora, histograma, violin plot)
- `bq4_results.csv` - Estadísticas por peak/off-peak
- `bq4_results_by_hour.csv` - Estadísticas por hora del día

### 3. Transformación de Datos (Opcional)

```bash
python scripts/transform_pickup_data.py data/compras_completadas_20251004_172958.csv
```

**Columnas agregadas**:
- `periodo_hora` (peak/off-peak)
- `periodo_comida` (breakfast/lunch/snack/dinner/late_night)
- `categoria_espera` (instant/very_fast/fast/normal/slow/very_slow)
- `dia_semana` + `es_fin_semana`
- `hora_listo` (hora del día)
- `es_outlier` (detección de outliers)
- Y más...

---

## 📂 Formato del CSV

El archivo debe estar en `data/` con estas columnas:

```csv
id_compra,fecha_listo,fecha_entregado,tiempo_espera_entrega_seg,tiempo_espera_entrega_min,...
1,2025-10-04 02:56:49,2025-10-04 02:56:52,2.361819,0.04,...
2,2025-10-04 04:12:25,2025-10-04 04:12:27,1.727573,0.03,...
```

### Columnas Requeridas

| Columna | Descripción | Tipo |
|---------|-------------|------|
| `id_compra` | ID único del pedido | Integer |
| `fecha_listo` | Timestamp cuando el pedido está listo | Datetime |
| `fecha_entregado` | Timestamp cuando se recoge | Datetime |
| `tiempo_espera_entrega_seg` | Tiempo de espera en segundos | Float |
| `tiempo_espera_entrega_min` | Tiempo de espera en minutos | Float |
| `fecha_creacion` | Timestamp de creación del pedido | Datetime |
| `total_cop` | Valor del pedido en COP | Float |

---

## 📊 Métricas Calculadas

### ¿Qué es la Mediana?

La **mediana** es el valor del medio cuando los datos están ordenados. Es mejor que el promedio para tiempos porque:
- ✅ No se afecta por outliers extremos
- ✅ Representa la experiencia típica del cliente
- ✅ Útil para comparar segmentos

### Definición de Horas Pico

**Peak Hours** (horas pico):
- **Almuerzo**: 12:00 - 14:00
- **Cena**: 19:00 - 21:00

**Off-Peak Hours** (horas valle):
- Resto del día (00:00-12:00, 14:00-19:00, 21:00-24:00)

### Categorías de Tiempo de Espera

| Categoría | Tiempo | Evaluación |
|-----------|--------|------------|
| Instant | < 5 segundos | Excelente |
| Very Fast | < 30 segundos | Muy bueno |
| Fast | < 1 minuto | Bueno |
| Normal | 1-5 minutos | Aceptable |
| Slow | 5-10 minutos | Mejorable |
| Very Slow | > 10 minutos | Crítico |

---

## 📈 Visualizaciones Incluidas

### Dashboard (Streamlit)
1. **Box Plot**: Compara distribuciones peak vs off-peak
2. **Gráfico por Hora**: Mediana de tiempo por cada hora del día
3. **Histograma**: Distribución de frecuencias
4. **Violin Plot**: Distribución por día de semana
5. **Tablas Interactivas**: Estadísticas detalladas
6. **Filtros**: Por periodo, día, hora

### Scripts (Matplotlib)
1. **Box Plot Comparativo**: Peak vs off-peak con medianas marcadas
2. **Barras por Hora**: Con zonas pico resaltadas
3. **Histograma Sobrepuesto**: Comparación visual de distribuciones
4. **Violin Plot**: Por día de semana y periodo

---

## 🎯 Casos de Uso

### Caso 1: Análisis Rápido
```bash
streamlit run scripts/dashboard_bq4.py
# Explora visualmente los datos
```

### Caso 2: Reporte para Presentación
```bash
python scripts/analyze_bq4.py data/compras_completadas_20251004_172958.csv
# Genera PNG de alta calidad (300 DPI)
```

### Caso 3: Pipeline de Datos
```bash
python scripts/transform_pickup_data.py data/compras_completadas_20251004_172958.csv
# Crea archivo transformado con columnas derivadas
```

### Caso 4: Análisis Detallado
```bash
# Primero transformar
python scripts/transform_pickup_data.py data/compras_completadas_20251004_172958.csv

# Luego analizar con datos enriquecidos
python scripts/analyze_bq4.py data/compras_completadas_20251004_172958_transformed.csv
```

---

## 💡 Insights y Recomendaciones

### ¿Qué significa si Peak > Off-Peak?

Si las horas pico tienen tiempos de espera **mayores**:
- ⚠️ Hay congestión en horas de alta demanda
- 💡 **Acción**: Aumentar personal en ventanilla de recogida
- 💡 **Acción**: Implementar sistema de pre-ordenar para pickup
- 💡 **Acción**: Mejorar señalización y flujo de clientes

### ¿Qué significa si Peak < Off-Peak?

Si las horas pico tienen tiempos de espera **menores**:
- ✅ El sistema está manejando bien la demanda pico
- 💡 **Acción**: Redistribuir recursos de horas pico a valle
- 💡 **Acción**: Investigar por qué las horas valle son más lentas

### Benchmarks Recomendados

- **Excelente**: Mediana < 30 segundos
- **Bueno**: Mediana < 1 minuto
- **Aceptable**: Mediana < 3 minutos
- **Mejorable**: Mediana > 3 minutos

---

## 🔧 Troubleshooting

### Error: "No such file or directory"
```bash
# Asegúrate de estar en el directorio correcto
ls data/  # Verifica que el CSV existe
```

### Error: "KeyError: 'tiempo_espera_entrega_seg'"
Verifica que tu CSV tiene todas las columnas requeridas.

### Dashboard no abre
```bash
# Abre manualmente
start http://localhost:8501  # Windows
open http://localhost:8501   # Mac
```

### Puerto ocupado
```bash
streamlit run scripts/dashboard_bq4.py --server.port 8502
```

---

## 📁 Archivos del Proyecto

```
Analytics/
├── scripts/
│   ├── analyze_bq4.py              # Script de análisis
│   ├── dashboard_bq4.py            # Dashboard interactivo
│   └── transform_pickup_data.py    # Transformación de datos
├── data/
│   └── compras_completadas_*.csv   # Datos de compras
└── docs/
    ├── BQ4.md                      # Este archivo
    └── QUICKSTART_BQ4.md           # Guía rápida
```

---

## 📊 Ejemplo de Resultados

```
BQ4: MEDIAN PICKUP WAITING TIME ANALYSIS
================================================================================

TIEMPO MEDIANO DE ESPERA: PEAK VS OFF-PEAK
--------------------------------------------------------------------------------
  periodo_hora  count  median   mean    std     min      max      p25     p75
      peak        8    2.40    5.50   4.20    1.80    15.38    2.10    2.80
   off-peak      10    2.50    6.80   8.50    1.73    21.47    2.20    3.10

📊 COMPARACIÓN:
   Peak hours:     2.40s (mediana)
   Off-peak hours: 2.50s (mediana)
   Diferencia:     0.10s (-4.0%)

🎯 CONCLUSIÓN:
   Los tiempos de espera en horas VALLE son 4.0% MAYORES que en horas pico.
   Se recomienda redistribuir recursos en horas pico.
```

---

**Última actualización**: Octubre 2025  
**Versión**: 1.0  
**Python**: 3.8+

