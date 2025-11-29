"""
Most Requested Categories Pipeline
==================================
Fetches and normalizes product category demand analytics from the backend.

Endpoint: GET /analytics/most-requested-categories
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

MOST_REQUESTED_RAW_JSON = DATA_DIR / "most_requested_categories_raw.json"
MOST_REQUESTED_CSV = DATA_DIR / "most_requested_categories.csv"
MOST_REQUESTED_SUMMARY_CSV = DATA_DIR / "most_requested_categories_summary.csv"


def _endpoint_url() -> str:
    return BACKEND_BASE_URL.rstrip("/") + "/analytics/most-requested-categories"


def _fetch_most_requested_categories(
    start_iso: str,
    end_iso: str,
    limit: int,
) -> Dict[str, Any]:
    params = {"start": start_iso, "end": end_iso, "limit": limit}
    response = requests.get(_endpoint_url(), params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _save_raw(payload: Dict[str, Any]) -> None:
    with open(MOST_REQUESTED_RAW_JSON, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _load_raw() -> Optional[Dict[str, Any]]:
    if not MOST_REQUESTED_RAW_JSON.exists():
        return None
    with open(MOST_REQUESTED_RAW_JSON, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    categories_df = pd.DataFrame(payload.get("categories", []) or [])
    if not categories_df.empty:
        numeric_cols = ["total_orders", "total_units", "total_revenue", "orders_percentage"]
        for column in numeric_cols:
            if column in categories_df.columns:
                categories_df[column] = pd.to_numeric(categories_df[column], errors="coerce")
        categories_df = categories_df.sort_values(
            ["total_orders", "total_units"],
            ascending=[False, False],
        ).reset_index(drop=True)

    summary_rows = []

    def add_summary(metric: str, value: Any) -> None:
        summary_rows.append({"metric": metric, "value": value})

    add_summary("start", payload.get("start"))
    add_summary("end", payload.get("end"))
    add_summary("total_orders", payload.get("total_orders"))
    add_summary("categories_returned", len(categories_df))

    if not categories_df.empty:
        top_row = categories_df.iloc[0]
        add_summary("top_category_name", top_row.get("categoria_nombre"))
        add_summary("top_category_orders", top_row.get("total_orders"))
        add_summary("top_category_share", top_row.get("orders_percentage"))

    summary_df = pd.DataFrame(summary_rows)

    return {"categories": categories_df, "summary": summary_df}


def _save_frames(frames: Dict[str, pd.DataFrame]) -> None:
    frames.get("categories", pd.DataFrame()).to_csv(MOST_REQUESTED_CSV, index=False)
    frames.get("summary", pd.DataFrame()).to_csv(MOST_REQUESTED_SUMMARY_CSV, index=False)


def run_most_requested_categories_etl(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 5,
    force_refresh: bool = False,
) -> Dict[str, pd.DataFrame]:
    """
    Fetch and cache most requested categories analytics.
    """
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")

    if end is None:
        end = datetime.utcnow()
    if start is None:
        start = end - timedelta(days=30)

    if (
        not force_refresh
        and MOST_REQUESTED_CSV.exists()
        and MOST_REQUESTED_SUMMARY_CSV.exists()
    ):
        categories = pd.read_csv(MOST_REQUESTED_CSV)
        summary = pd.read_csv(MOST_REQUESTED_SUMMARY_CSV)
        return {"categories": categories, "summary": summary}

    payload: Optional[Dict[str, Any]] = None
    if not force_refresh and MOST_REQUESTED_RAW_JSON.exists():
        try:
            payload = _load_raw()
        except Exception:
            payload = None

    if payload is None:
        start_iso = start.replace(microsecond=0).isoformat() + "Z"
        end_iso = end.replace(microsecond=0).isoformat() + "Z"
        payload = _fetch_most_requested_categories(start_iso, end_iso, limit)
        _save_raw(payload)

    frames = _normalize_payload(payload or {})
    _save_frames(frames)
    return frames


