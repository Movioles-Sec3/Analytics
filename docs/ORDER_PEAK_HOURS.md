# Order Peak Hours Analysis

## Overview

This module analyzes order patterns to answer the question: **"At what hours is the peak of orders?"**

The analysis identifies:
- Order volume distribution throughout the day (24 hours)
- Peak hours with highest order concentration
- Revenue patterns by hour
- Insights for operational optimization

## Features

### 1. Backend Pipeline (`app/pipelines/order_peak_hours.py`)

The ETL pipeline processes order data and provides:

- **Hourly Distribution**: Order count, revenue, and average order value per hour
- **Peak Hour Identification**: Automatically identifies hours with highest volume (top 25%)
- **Summary Statistics**: Total orders, busiest hours, slowest hours
- **Caching**: Results are cached to avoid repeated processing
- **Fallback Mode**: Analyzes local CSV files when backend is unavailable

#### Key Functions

```python
run_order_peak_hours_etl(
    start=None,              # Start datetime (default: today)
    end=None,                # End datetime (default: today)
    timezone_offset_minutes=0,  # Timezone offset
    force_refresh=False,     # Force reload from backend
    fallback_to_local=True,  # Use local data if backend fails
    local_data_path=None     # Custom path to local CSV
)
```

### 2. Dashboard View (`app/views/order_peak_hours.py`)

Interactive visualization component featuring:

- **Summary Metrics**: Total orders, busiest hour, peak coverage
- **Hourly Bar Chart**: Visual representation of order volume by hour
- **Color Coding**: Peak hours highlighted in red, normal hours in blue
- **Revenue Analysis**: Revenue distribution throughout the day
- **Pie Chart**: Percentage distribution of orders
- **Heatmap**: Order volume intensity visualization
- **Insights Section**: Actionable recommendations based on data
- **Data Export**: Download analysis results as CSV

### 3. Dashboard Integration

The new tab "🕐 Order Peak Hours" is integrated into the main dashboard (`app/dashboard.py`).

## Data Sources

### Backend Endpoint (Primary)

Expected endpoint: `/analytics/order-peak-hours`

**Request Parameters:**
- `start`: ISO 8601 datetime string (e.g., "2025-10-31T00:00:00Z")
- `end`: ISO 8601 datetime string
- `timezone_offset_minutes`: Integer offset (e.g., -300 for UTC-5)

**Expected Response:**
```json
{
  "hourly_distribution": [
    {
      "hour": 0,
      "order_count": 10,
      "total_revenue": 150000.0,
      "avg_order_value": 15000.0,
      "percentage": 2.5,
      "is_peak": false
    },
    ...
  ],
  "peak_hours": [12, 13, 19, 20],
  "summary": {
    "Total Orders": 400,
    "Peak Hours": "12:00, 13:00, 19:00, 20:00",
    "Busiest Hour": 19,
    "Busiest Hour Orders": 85
  }
}
```

### Local CSV (Fallback)

The pipeline can analyze local CSV files with the following structure:

**Required Columns:**
- `id_compra`: Unique order ID
- `fecha_creacion`: Order creation timestamp (YYYY-MM-DD HH:MM:SS)
- `total_cop`: Order total in COP (optional, for revenue analysis)

**Default File:** `data/compras_completadas_20251004_172958.csv`

## Usage

### Running the Dashboard

```bash
streamlit run app/dashboard.py
```

Then navigate to the "🕐 Order Peak Hours" tab.

### Using the Pipeline Directly

```python
from app.pipelines.order_peak_hours import run_order_peak_hours_etl
from datetime import datetime

# Analyze today's orders
frames = run_order_peak_hours_etl()

# Access results
df_hourly = frames["hourly"]
df_summary = frames["summary"]

# Analyze custom date range
frames = run_order_peak_hours_etl(
    start=datetime(2025, 10, 1),
    end=datetime(2025, 10, 31),
    timezone_offset_minutes=-300  # UTC-5 (Colombia)
)
```

## Visualizations

### 1. Hourly Bar Chart
Shows order count for each hour (0-23), with peak hours highlighted in red.

### 2. Order Distribution Pie Chart
Displays percentage of total orders for each hour.

### 3. Revenue by Hour
Bar chart showing total revenue (COP) per hour, with color gradient.

### 4. Order Volume Heatmap
Heat intensity map showing order concentration throughout the day.

### 5. Peak Hours Table
Detailed table with hour, order count, percentage, and revenue for peak periods.

## Insights & Recommendations

The dashboard automatically generates insights:

### High Demand Periods
- Identifies busiest hours
- Suggests staff scheduling
- Inventory preparation recommendations
- Kitchen workflow optimization

### Optimization Opportunities
- Identifies low-demand periods
- Promotion timing suggestions
- Maintenance scheduling
- Staff schedule adjustments

## Configuration

### Timezone Settings

The analysis supports timezone offsets. Common values:
- **UTC-5 (Colombia)**: -300 minutes
- **UTC-4**: -240 minutes
- **UTC-3**: -180 minutes
- **UTC**: 0 minutes

### Backend URL

Configure in `app/config.py`:

```python
BACKEND_BASE_URL = "http://localhost:8000/"
```

Or set environment variable:
```bash
export BACKEND_BASE_URL="https://api.example.com/"
```

## Data Caching

The pipeline caches data in the `data/` directory:

- `order_peak_hours_raw.json`: Raw backend response
- `order_peak_hours_hourly.csv`: Processed hourly data
- `order_peak_hours_summary.csv`: Summary statistics

To force refresh:
1. Check "Force refresh" in the dashboard
2. Or delete cache files manually
3. Or use `force_refresh=True` in code

## Example Output

### Summary Metrics
- **Total Orders**: 450
- **Busiest Hour**: 19:00
- **Peak Hour Orders**: 85
- **Peak Hours Coverage**: 42.3%

### Peak Hours Identified
- 12:00 - 13:00 (Lunch)
- 19:00 - 21:00 (Dinner)

### Insights
- 42.3% of all orders occur during peak hours
- Consider increasing kitchen staff during 19:00-21:00
- Run promotions during 15:00-17:00 (slow period)

## Error Handling

The pipeline includes robust error handling:

1. **Backend Unavailable**: Automatically falls back to local data analysis
2. **Missing Cache**: Regenerates from source
3. **Invalid Dates**: Displays warning and prevents execution
4. **Empty Data**: Shows informative message to user

## Performance

- **Caching**: Significantly reduces load times for repeated queries
- **Efficient Processing**: Pandas-based analysis for fast computation
- **Incremental Loading**: Only fetches new data when needed

## Future Enhancements

Potential improvements:
- Day-of-week analysis (weekday vs weekend patterns)
- Seasonal trends (monthly/quarterly patterns)
- Category-specific peak hours
- Predictive modeling for demand forecasting
- Real-time monitoring mode
- Alert system for unusual patterns

## Support

For issues or questions, refer to the main project documentation or contact the development team.
