import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import requests

from app.config import BACKEND_BASE_URL

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Cached filenames
BQ5_RAW_JSON = DATA_DIR / "bq5_reorders_by_category.json"
BQ5_CATEGORIES_CSV = DATA_DIR / "bq5_categories.csv"
BQ5_HOURLY_CSV = DATA_DIR / "bq5_hourly_distribution.csv"


def _request_reorders_by_category(start_iso: str, end_iso: str, timezone_offset_minutes: int) -> Dict[str, Any]:
    url = BACKEND_BASE_URL.rstrip("/") + "/analytics/reorders-by-category"
    params = {
        "start": start_iso,
        "end": end_iso,
        "timezone_offset_minutes": timezone_offset_minutes,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _save_raw_json(payload: Dict[str, Any]) -> None:
    with open(BQ5_RAW_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _load_raw_json() -> Optional[Dict[str, Any]]:
    if not BQ5_RAW_JSON.exists():
        return None
    with open(BQ5_RAW_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_payload_to_frames(payload: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    categories = payload.get("categories", [])
    # Categories summary
    cat_rows = []
    hourly_rows = []
    for c in categories:
        cat_rows.append({
            "categoria_id": c.get("categoria_id"),
            "categoria_nombre": c.get("categoria_nombre"),
            "reorder_count": c.get("reorder_count", 0),
        })
        for h in c.get("hour_distribution", []) or []:
            hourly_rows.append({
                "categoria_id": c.get("categoria_id"),
                "categoria_nombre": c.get("categoria_nombre"),
                "hour": h.get("hour"),
                "count": h.get("count", 0),
            })

    df_categories = pd.DataFrame(cat_rows)
    df_hourly = pd.DataFrame(hourly_rows)
    if not df_categories.empty:
        df_categories = df_categories.sort_values(["reorder_count", "categoria_nombre"], ascending=[False, True])
    if not df_hourly.empty:
        df_hourly = df_hourly.sort_values(["categoria_id", "hour"]) 

    return {
        "categories": df_categories,
        "hourly": df_hourly,
    }


def _save_frames(frames: Dict[str, pd.DataFrame]) -> None:
    frames["categories"].to_csv(BQ5_CATEGORIES_CSV, index=False)
    frames["hourly"].to_csv(BQ5_HOURLY_CSV, index=False)


def run_bq5_etl(start: Optional[datetime] = None,
                 end: Optional[datetime] = None,
                 timezone_offset_minutes: int = 0,
                 force_refresh: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Execute BQ5 ETL: fetch from backend (if cache not present or force_refresh),
    normalize and save CSVs under data/.

    Returns dataframes dict: {"categories": df, "hourly": df}
    """
    # Default window: last 30 days
    if end is None:
        end = datetime.utcnow()
    if start is None:
        start = end - timedelta(days=30)

    # If cached CSVs exist and not forcing refresh, reuse
    if not force_refresh and BQ5_CATEGORIES_CSV.exists() and BQ5_HOURLY_CSV.exists():
        return {
            "categories": pd.read_csv(BQ5_CATEGORIES_CSV),
            "hourly": pd.read_csv(BQ5_HOURLY_CSV),
        }

    # If raw cached JSON exists and not forcing refresh, reuse it
    payload: Optional[Dict[str, Any]] = None
    if not force_refresh and BQ5_RAW_JSON.exists():
        try:
            payload = _load_raw_json()
        except Exception:
            payload = None

    # Else fetch from backend
    if payload is None:
        start_iso = start.replace(microsecond=0).isoformat() + "Z"
        end_iso = end.replace(microsecond=0).isoformat() + "Z"
        payload = _request_reorders_by_category(start_iso, end_iso, timezone_offset_minutes)
        _save_raw_json(payload)

    frames = _normalize_payload_to_frames(payload)
    _save_frames(frames)
    return frames
