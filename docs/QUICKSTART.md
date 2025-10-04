# 🚀 Quick Start Guide

Inicia el análisis de analytics en 3 pasos:

## Paso 1: Instalar Dependencias (30 segundos)

```bash
pip install -r requirements.txt
```

## Paso 2: Ejecutar Dashboard

### Windows (Más Fácil)
Doble-click en `run_dashboard.bat`

### Command Line (Todas las plataformas)
```bash
streamlit run app/dashboard.py
```

## Paso 3: Analizar 🎉

El dashboard abre en `http://localhost:8501`

- Los datos se cargan automáticamente desde `data/analytics_events.csv`
- Ve a la pestaña **"BQ13: App Loading"** para análisis de carga
- Ve a la pestaña **"BQ14: Payment Time"** para análisis de pagos

---

## Alternativa: Scripts de Línea de Comando

Para análisis rápido sin dashboard:

```bash
# BQ13
python scripts/analyze_bq13.py "data/analytics_events.csv"

# BQ14
python scripts/analyze_bq14.py "data/analytics_events.csv"
```

Genera imágenes PNG y CSV con resultados.

---

## Transformación de Datos (Opcional)

Agrega columnas derivadas para análisis avanzado:

```bash
python scripts/transform_data.py "data/analytics_events.csv"
```

---

## Cheat Sheet

| Acción | Comando |
|--------|---------|
| Dashboard interactivo | `streamlit run app/dashboard.py` |
| Análisis BQ13 | `python scripts/analyze_bq13.py "ruta/al/csv"` |
| Análisis BQ14 | `python scripts/analyze_bq14.py "ruta/al/csv"` |
| Transformar datos | `python scripts/transform_data.py "ruta/al/csv"` |
| Generar datos sintéticos | `python scripts/generate_synthetic_data.py` |
| Comparar antes/después | `python analyze_bq13.py "ruta/al/csv" --cutoff "2025-10-05"` |

---

## ¿Necesitas Ayuda?

- Lee el [README.md](README.md) completo
- Ejecuta cualquier script con `--help`
- Revisa los logs en consola

---

**¡Listo!** En menos de 1 minuto tienes analytics completos 📊

