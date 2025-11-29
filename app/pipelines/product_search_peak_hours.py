"""
Product Search Peak Hours Pipeline
==================================
Fetches and normalizes analytics about when users use the product search
feature the most throughout the day.

Endpoint: GET /analytics/product-search-peak-hours
Expected JSON payload example:
{
  "start": "...",
  "end": "...",
  "timezone_offset_minutes": -300,
  "total_searches": 542,
  "peak_hours": [19, 20, 21],
  "hourly_distribution": [
    {"hour": 19, "search_count": 74, "percentage": 13.65, "is_peak": true},
    ...
  ]
}
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import requests

from app.config import BACKEND_BASE_URL

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Cache file names
SEARCH_PEAK_RAW_JSON = DATA_DIR / "product_search_peak_hours_raw.json"
SEARCH_PEAK_HOURLY_CSV = DATA_DIR / "product_search_peak_hours_hourly.csv"
SEARCH_PEAK_SUMMARY_CSV = DATA_DIR / "product_search_peak_hours_summary.csv"


def _endpoint_url() -> str:
    return BACKEND_BASE_URL.rstrip("/") + "/analytics/product-search-peak-hours"


def _request_product_search_peak_hours(
    start_iso: str,
    end_iso: str,
    timezone_offset_minutes: int,
) -> Dict[str, Any]:
    """Request product search peak hours from backend."""
    params = {
        "start": start_iso,
        "end": end_iso,
        "timezone_offset_minutes": timezone_offset_minutes,
    }
    response = requests.get(_endpoint_url(), params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _save_raw_json(payload: Dict[str, Any]) -> None:
    with open(SEARCH_PEAK_RAW_JSON, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _load_raw_json() -> Optional[Dict[str, Any]]:
    if not SEARCH_PEAK_RAW_JSON.exists():
        return None
    with open(SEARCH_PEAK_RAW_JSON, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_payload_to_frames(payload: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """Normalize backend payload to pandas DataFrames."""
    hourly = pd.DataFrame(payload.get("hourly_distribution", []) or [])
    if not hourly.empty:
        # Ensure consistent ordering and data types
        hourly = hourly.sort_values("hour").reset_index(drop=True)
        numeric_cols = ["hour", "search_count", "percentage"]
        for column in numeric_cols:
            if column in hourly.columns:
                hourly[column] = pd.to_numeric(hourly[column], errors="coerce")
        if "is_peak" in hourly.columns:
            hourly["is_peak"] = hourly["is_peak"].astype(bool)

    summary_rows = []

    def add_summary(metric: str, value: Any) -> None:
        summary_rows.append({"metric": metric, "value": value})

    add_summary("start", payload.get("start"))
    add_summary("end", payload.get("end"))
    add_summary("timezone_offset_minutes", payload.get("timezone_offset_minutes"))
    add_summary("total_searches", payload.get("total_searches"))

    peak_hours = payload.get("peak_hours") or []
    if peak_hours:
        add_summary("peak_hours", ", ".join(f"{int(h):02d}:00" for h in peak_hours))
    elif peak_hours is not None:
        add_summary("peak_hours", "")

    if not hourly.empty and "search_count" in hourly.columns:
        peak_frame = hourly[hourly.get("is_peak", False)]
        add_summary("searches_in_peak_hours", int(peak_frame["search_count"].sum()) if not peak_frame.empty else 0)
        add_summary(
            "peak_hours_percentage",
            f"{peak_frame['percentage'].sum():.2f}%" if "percentage" in peak_frame.columns and not peak_frame.empty else "",
        )

    df_summary = pd.DataFrame(summary_rows)

    return {"hourly": hourly, "summary": df_summary}


def _ensure_csv_exists(path: Path, df: pd.DataFrame) -> None:
    """Persist dataframe to CSV even when empty, preserving columns."""
    if df is None:
        df = pd.DataFrame()
    df.to_csv(path, index=False)


def _save_frames(frames: Dict[str, pd.DataFrame]) -> None:
    _ensure_csv_exists(SEARCH_PEAK_HOURLY_CSV, frames.get("hourly", pd.DataFrame()))
    _ensure_csv_exists(SEARCH_PEAK_SUMMARY_CSV, frames.get("summary", pd.DataFrame()))


def run_product_search_peak_hours_etl(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    timezone_offset_minutes: int = 0,
    force_refresh: bool = False,
) -> Dict[str, pd.DataFrame]:
    """
    Execute ETL to obtain product search peak hours analytics.

    Args:
        start: Optional start datetime (defaults to 30 days ago if omitted).
        end: Optional end datetime (defaults to now).
        timezone_offset_minutes: Client timezone offset in minutes.
        force_refresh: Skip caches and call backend directly.

    Returns:
        Dict with "hourly" and "summary" DataFrames.
    """
    if end is None:
        end = datetime.utcnow()
    if start is None:
        start = end - timedelta(days=30)

    # 1. Reuse processed CSV cache if available
    if (
        not force_refresh
        and SEARCH_PEAK_HOURLY_CSV.exists()
        and SEARCH_PEAK_SUMMARY_CSV.exists()
    ):
        hourly = pd.read_csv(SEARCH_PEAK_HOURLY_CSV)
        summary = pd.read_csv(SEARCH_PEAK_SUMMARY_CSV)
        return {"hourly": hourly, "summary": summary}

    # 2. Try raw JSON cache
    payload: Optional[Dict[str, Any]] = None
    if not force_refresh and SEARCH_PEAK_RAW_JSON.exists():
        try:
            payload = _load_raw_json()
        except Exception:
            payload = None

    # 3. Fetch from backend if needed
    if payload is None:
        start_iso = start.replace(microsecond=0).isoformat() + "Z"
        end_iso = end.replace(microsecond=0).isoformat() + "Z"
        payload = _request_product_search_peak_hours(start_iso, end_iso, timezone_offset_minutes)
        _save_raw_json(payload)

    frames = _normalize_payload_to_frames(payload or {})
    _save_frames(frames)
    return frames


