# Product Search Peak Hours

## Overview

Responds to: **"What time of day do users most frequently use the product search function?"**

The analysis aggregates every call to the product search endpoint (`GET /productos/buscar`) and builds an hourly distribution to identify peak usage windows.

## Components

- **Pipeline:** `app/pipelines/product_search_peak_hours.py`
  - Fetches `GET /analytics/product-search-peak-hours`
  - Caches raw JSON plus normalized hourly and summary CSVs under `data/`
  - Normalizes fields such as `hour`, `search_count`, `percentage`, `is_peak`, and totals
- **Dashboard View:** `app/views/product_search_peak_hours.py`
  - Allows picking date range, timezone offset, and forcing cache refresh
  - Displays KPIs (total searches, peak hours, share in peak windows)
  - Plots bar chart, pie chart, heatmap, and provides CSV exports
- **Dashboard Tab:** labelled **“🔎 Search Peak Hours”** inside `app/dashboard.py`

## API Contract

`GET /analytics/product-search-peak-hours`

Query parameters:
- `start` (optional, ISO-8601 UTC) – inclusive lower bound, defaults to last 30 days
- `end` (optional, ISO-8601 UTC) – exclusive upper bound, defaults to now
- `timezone_offset_minutes` (optional, int) – e.g. `-300` for UTC-5 to reinterpret hours locally

Sample response:

```json
{
  "start": "2025-10-01T00:00:00Z",
  "end": "2025-10-31T23:59:59Z",
  "timezone_offset_minutes": -300,
  "total_searches": 542,
  "peak_hours": [19, 20, 21],
  "hourly_distribution": [
    {"hour": 18, "search_count": 52, "percentage": 9.59, "is_peak": true},
    {"hour": 19, "search_count": 74, "percentage": 13.65, "is_peak": true}
  ]
}
```

## Usage

Launch the dashboard:

```bash
streamlit run app/dashboard.py
```

Navigate to **🔎 Search Peak Hours**, select the desired range and timezone, and explore:
- Hourly histogram highlighting peak hours
- Share of searches per hour and heatmap
- Download buttons for hourly distribution and summary CSVs

## Troubleshooting

- **No data available:** Verify backend returns data for the selected window or adjust the date range.
- **Incorrect local time interpretation:** Confirm the `timezone_offset_minutes` matches the audience’s offset.
- **Stale data:** Use the “Force refresh” checkbox or delete cached files under `data/product_search_peak_hours_*`.


