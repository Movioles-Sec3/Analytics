# Most Requested Categories

## Overview

Answers the question: **"What are the most requested categories by users?"**

The analysis aggregates orders, units, and revenue per product category in a given date range and returns a ranking sorted by order volume.

## Components

- **Pipeline:** `app/pipelines/most_requested_categories.py`
  - Calls `GET /analytics/most-requested-categories`
  - Caches raw JSON plus normalized category and summary CSVs under `data/`
  - Normalizes numeric fields (`total_orders`, `total_units`, `total_revenue`, `orders_percentage`)
- **Dashboard View:** `app/views/most_requested_categories.py`
  - Exposes filters for date range, top-N limit, and cache refresh
  - Shows KPIs (total orders, top category name/orders/share)
  - Renders ranking and supporting visuals (orders, units, revenue pie)
  - Provides CSV downloads for categories and summary
- **Dashboard Tab:** labelled **“🏆 Most Requested Categories”** in `app/dashboard.py`

## API Contract

`GET /analytics/most-requested-categories`

Query parameters:
- `start` (ISO-8601 UTC, optional) – inclusive lower bound, defaults to last 30 days
- `end` (ISO-8601 UTC, optional) – exclusive upper bound, defaults to now
- `limit` (int 1-50, optional, default 5) – maximum number of categories returned

Sample response:

```json
{
  "start": "2025-10-01T00:00:00Z",
  "end": "2025-10-31T23:59:59Z",
  "total_orders": 128,
  "categories": [
    {
      "categoria_id": 2,
      "categoria_nombre": "Cócteles",
      "total_orders": 56,
      "total_units": 142,
      "total_revenue": 2360000.0,
      "orders_percentage": 43.75
    }
  ]
}
```

## Usage

Launch the Streamlit dashboard:

```bash
streamlit run app/dashboard.py
```

Navigate to **🏆 Most Requested Categories**, choose date bounds and top-N value, and explore:
- Horizontal bar chart of orders per category
- Units bar chart and revenue pie split
- Download buttons for both normalized datasets

## Troubleshooting

- **Empty results:** The backend returns `total_orders = 0` with an empty list. Broaden the date range or lower the `limit`.
- **Limit errors:** The frontend enforces `1 ≤ limit ≤ 50`. Adjust if you receive a validation error from the backend.
- **Stale data:** Tick *Force refresh* or remove the cached files under `data/most_requested_categories_*`.


