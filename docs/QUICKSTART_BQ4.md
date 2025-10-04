# 🚀 Quick Start - BQ4

Análisis rápido de tiempos de pickup en 3 pasos:

## Paso 1: Verifica los datos

```bash
ls data/compras_completadas_*.csv
```

## Paso 2: Ejecuta el Dashboard

```bash
streamlit run scripts/dashboard_bq4.py
```

O para análisis en terminal:

```bash
python scripts/analyze_bq4.py data/compras_completadas_20251004_172958.csv
```

## Paso 3: Analiza 🎉

El dashboard abre en `http://localhost:8501`

- **Tab 1**: Comparación Peak vs Off-Peak  
- **Tab 2**: Análisis por hora del día  
- **Tab 3**: Análisis por día de semana  
- **Tab 4**: Datos crudos con filtros

---

## Alternativa: Script de Análisis

Para reportes PNG sin dashboard:

```bash
python scripts/analyze_bq4.py data/compras_completadas_20251004_172958.csv
```

Genera:
- `bq4_analysis.png` (4 visualizaciones)
- `bq4_results.csv` (estadísticas)
- `bq4_results_by_hour.csv` (por hora)

---

## Transformar Datos (Opcional)

Agrega 12 columnas derivadas:

```bash
python scripts/transform_pickup_data.py data/compras_completadas_20251004_172958.csv
```

---

## Cheat Sheet

| Acción | Comando |
|--------|---------|
| Dashboard | `streamlit run scripts/dashboard_bq4.py` |
| Análisis | `python scripts/analyze_bq4.py data/compras_completadas_*.csv` |
| Transformar | `python scripts/transform_pickup_data.py data/compras_completadas_*.csv` |

---

**¡Listo en 1 minuto!** ⏱️

Para más detalles, lee [BQ4.md](BQ4.md)

