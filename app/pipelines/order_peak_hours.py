"""
Order Peak Hours Analysis Pipeline
===================================
Analyzes at what hours the peak of orders occurs.

This pipeline processes order data to identify:
- Order volume distribution by hour
- Peak hours identification
- Order patterns throughout the day
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import requests

from app.config import BACKEND_BASE_URL

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Cached filenames
ORDER_PEAK_RAW_JSON = DATA_DIR / "order_peak_hours_raw.json"
ORDER_PEAK_HOURLY_CSV = DATA_DIR / "order_peak_hours_hourly.csv"
ORDER_PEAK_SUMMARY_CSV = DATA_DIR / "order_peak_hours_summary.csv"


def _request_order_peak_hours(start_iso: str, end_iso: str, timezone_offset_minutes: int) -> Dict[str, Any]:
    """
    Request order peak hours data from backend.
    Expected endpoint: /analytics/order-peak-hours
    """
    url = BACKEND_BASE_URL.rstrip("/") + "/analytics/order-peak-hours"
    params = {
        "start": start_iso,
        "end": end_iso,
        "timezone_offset_minutes": timezone_offset_minutes,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _save_raw_json(payload: Dict[str, Any]) -> None:
    """Save raw JSON response from backend."""
    with open(ORDER_PEAK_RAW_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _load_raw_json() -> Optional[Dict[str, Any]]:
    """Load raw JSON from cache if it exists."""
    if not ORDER_PEAK_RAW_JSON.exists():
        return None
    with open(ORDER_PEAK_RAW_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _analyze_local_data(file_path: Path) -> Dict[str, pd.DataFrame]:
    """
    Analyze local CSV data when backend is not available.
    Fallback method that analyzes compras_completadas CSV directly.
    """
    if not file_path.exists():
        return {"hourly": pd.DataFrame(), "summary": pd.DataFrame()}
    
    # Load orders data
    df = pd.read_csv(file_path)
    df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'])
    
    # Extract hour from creation date
    df['hour'] = df['fecha_creacion'].dt.hour
    df['day_of_week'] = df['fecha_creacion'].dt.day_name()
    df['is_weekend'] = df['fecha_creacion'].dt.dayofweek >= 5
    
    # Hourly distribution
    hourly = df.groupby('hour').agg({
        'id_compra': 'count',
        'total_cop': ['sum', 'mean']
    }).reset_index()
    hourly.columns = ['hour', 'order_count', 'total_revenue', 'avg_order_value']
    hourly = hourly.sort_values('hour')
    
    # Calculate percentage of daily orders
    total_orders = hourly['order_count'].sum()
    hourly['percentage'] = (hourly['order_count'] / total_orders * 100).round(2)
    
    # Identify peak hours (top 25% by volume)
    threshold = hourly['order_count'].quantile(0.75)
    hourly['is_peak'] = hourly['order_count'] >= threshold
    
    # Summary statistics
    peak_hours = hourly[hourly['is_peak']]['hour'].tolist()
    summary_data = {
        'metric': [
            'Total Orders',
            'Peak Hours',
            'Peak Hour Range',
            'Orders in Peak Hours',
            'Percentage in Peak Hours',
            'Busiest Hour',
            'Busiest Hour Orders',
            'Slowest Hour',
            'Slowest Hour Orders'
        ],
        'value': [
            int(total_orders),
            ', '.join(map(lambda h: f"{h}:00", peak_hours)),
            f"{min(peak_hours)}:00 - {max(peak_hours)}:00" if peak_hours else "N/A",
            int(hourly[hourly['is_peak']]['order_count'].sum()),
            f"{(hourly[hourly['is_peak']]['order_count'].sum() / total_orders * 100):.1f}%",
            int(hourly.loc[hourly['order_count'].idxmax(), 'hour']),
            int(hourly['order_count'].max()),
            int(hourly.loc[hourly['order_count'].idxmin(), 'hour']),
            int(hourly['order_count'].min())
        ]
    }
    summary = pd.DataFrame(summary_data)
    
    return {
        "hourly": hourly,
        "summary": summary
    }


def _normalize_payload_to_frames(payload: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """
    Normalize backend JSON payload to DataFrames.
    Expected structure:
    {
        "hourly_distribution": [{"hour": 0, "order_count": 10, ...}, ...],
        "peak_hours": [12, 13, 19, 20],
        "summary": {...}
    }
    """
    hourly_data = payload.get("hourly_distribution", [])
    df_hourly = pd.DataFrame(hourly_data)
    
    if not df_hourly.empty:
        df_hourly = df_hourly.sort_values('hour')
    
    # Create summary DataFrame
    summary_info = payload.get("summary", {})
    summary_rows = []
    for key, value in summary_info.items():
        summary_rows.append({"metric": key, "value": str(value)})
    df_summary = pd.DataFrame(summary_rows)
    
    return {
        "hourly": df_hourly,
        "summary": df_summary
    }


def _save_frames(frames: Dict[str, pd.DataFrame]) -> None:
    """Save DataFrames to CSV files."""
    frames["hourly"].to_csv(ORDER_PEAK_HOURLY_CSV, index=False)
    frames["summary"].to_csv(ORDER_PEAK_SUMMARY_CSV, index=False)


def run_order_peak_hours_etl(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    timezone_offset_minutes: int = 0,
    force_refresh: bool = False,
    fallback_to_local: bool = True,
    local_data_path: Optional[Path] = None
) -> Dict[str, pd.DataFrame]:
    """
    Execute Order Peak Hours ETL pipeline.
    
    Args:
        start: Start datetime for analysis (default: 30 days ago)
        end: End datetime for analysis (default: now)
        timezone_offset_minutes: Timezone offset in minutes (default: 0 for UTC)
        force_refresh: Force refresh from backend (default: False)
        fallback_to_local: If backend fails, analyze local CSV (default: True)
        local_data_path: Path to local CSV file (default: data/compras_completadas_20251004_172958.csv)
    
    Returns:
        Dictionary with "hourly" and "summary" DataFrames
    """
    # Set default time window
    if end is None:
        end = datetime.utcnow()
    if start is None:
        start = end.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Check cache first
    if not force_refresh and ORDER_PEAK_HOURLY_CSV.exists() and ORDER_PEAK_SUMMARY_CSV.exists():
        return {
            "hourly": pd.read_csv(ORDER_PEAK_HOURLY_CSV),
            "summary": pd.read_csv(ORDER_PEAK_SUMMARY_CSV)
        }
    
    # Try to get data from backend
    payload: Optional[Dict[str, Any]] = None
    backend_available = False
    
    try:
        if not force_refresh and ORDER_PEAK_RAW_JSON.exists():
            payload = _load_raw_json()
            backend_available = True
        else:
            start_iso = start.replace(microsecond=0).isoformat() + "Z"
            end_iso = end.replace(microsecond=0).isoformat() + "Z"
            payload = _request_order_peak_hours(start_iso, end_iso, timezone_offset_minutes)
            _save_raw_json(payload)
            backend_available = True
        
        if payload:
            frames = _normalize_payload_to_frames(payload)
            _save_frames(frames)
            return frames
    except Exception as e:
        print(f"Backend request failed: {e}")
        backend_available = False
    
    # Fallback to local data analysis
    if fallback_to_local and not backend_available:
        if local_data_path is None:
            local_data_path = DATA_DIR / "compras_completadas_20251004_172958.csv"
        
        frames = _analyze_local_data(local_data_path)
        if not frames["hourly"].empty:
            _save_frames(frames)
            return frames
    
    # Return empty frames if everything fails
    return {
        "hourly": pd.DataFrame(),
        "summary": pd.DataFrame()
    }
