import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
import requests

from app.config import BACKEND_BASE_URL

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RECHARGES_RAW_JSON = DATA_DIR / "recharges_raw.json"
RECHARGES_CSV = DATA_DIR / "recharges.csv"
RECHARGES_WEEKLY_CSV = DATA_DIR / "recharges_weekly_unique_users.csv"


def _fetch_recharges(start_iso: Optional[str], end_iso: Optional[str], limit: int = 1000) -> List[Dict[str, Any]]:
    """Fetch recharges with pagination until an empty page is returned."""
    assert 1 <= limit <= 1000, "limit must be between 1 and 1000"
    base_url = BACKEND_BASE_URL.rstrip("/") + "/analytics/recharges"
    all_rows: List[Dict[str, Any]] = []
    offset = 0

    while True:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if start_iso:
            params["start"] = start_iso
        if end_iso:
            params["end"] = end_iso
        resp = requests.get(base_url, params=params, timeout=30)
        resp.raise_for_status()
        rows = resp.json()
        if not isinstance(rows, list):
            raise ValueError("Unexpected response format: expected a JSON array")
        if len(rows) == 0:
            break
        all_rows.extend(rows)
        if len(rows) < limit:
            break
        offset += limit
        # Safety guard to avoid runaway loops
        if offset > 1_000_000:
            break

    return all_rows


def _save_raw(rows: List[Dict[str, Any]]) -> None:
    with open(RECHARGES_RAW_JSON, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def _load_raw() -> Optional[List[Dict[str, Any]]]:
    if not RECHARGES_RAW_JSON.exists():
        return None
    with open(RECHARGES_RAW_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _rows_to_frames(rows: List[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
    df = pd.DataFrame(rows)
    if df.empty:
        # Ensure stable schema even when no data to avoid read_csv errors later
        empty_cols = [
            "id", "usuario_id", "usuario_nombre", "usuario_email",
            "monto", "fecha_hora", "user_id", "user_name", "user_email", "amount"
        ]
        df = pd.DataFrame(columns=empty_cols)
        weekly_empty = pd.DataFrame(columns=["week_start", "unique_users", "recharge_count"])
        return {"recharges": df, "weekly": weekly_empty}

    # Normalize columns and parse datetime
    if "fecha_hora" in df.columns:
        df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], utc=True, errors="coerce")
    # Rename to English-friendly columns (keep originals as well)
    if "usuario_id" in df.columns:
        df["user_id"] = df["usuario_id"]
    if "usuario_nombre" in df.columns:
        df["user_name"] = df["usuario_nombre"]
    if "usuario_email" in df.columns:
        df["user_email"] = df["usuario_email"]
    if "monto" in df.columns:
        df["amount"] = df["monto"]

    # Weekly aggregation (UTC weeks, Monday-start)
    if "fecha_hora" in df.columns:
        week_period = df["fecha_hora"].dt.tz_convert("UTC").dt.to_period("W-MON")
        week_start = week_period.apply(lambda p: p.start_time.date())
        weekly = pd.DataFrame({
            "week_start": week_start,
            "user_id": df.get("usuario_id", df.get("user_id"))
        })
        weekly_grouped = weekly.groupby("week_start").agg(unique_users=("user_id", "nunique"), recharge_count=("user_id", "count")).reset_index()
    else:
        weekly_grouped = pd.DataFrame(columns=["week_start", "unique_users", "recharge_count"])

    return {"recharges": df, "weekly": weekly_grouped}


def _save_frames(frames: Dict[str, pd.DataFrame]) -> None:
    frames["recharges"].to_csv(RECHARGES_CSV, index=False)
    frames["weekly"].to_csv(RECHARGES_WEEKLY_CSV, index=False)


def run_recharges_etl(start: Optional[datetime] = None,
                      end: Optional[datetime] = None,
                      limit: int = 1000,
                      force_refresh: bool = False) -> Dict[str, pd.DataFrame]:
    """ETL for recharges: fetch (with paging), cache, normalize, and save CSVs.
    Returns dict with keys: recharges, weekly
    """
    # Default window: last 30 days
    if end is None:
        end = datetime.utcnow()
    if start is None:
        start = end - timedelta(days=30)

    # Use existing CSVs if present and not forcing
    if not force_refresh and RECHARGES_CSV.exists() and RECHARGES_WEEKLY_CSV.exists():
        try:
            rec = pd.read_csv(RECHARGES_CSV)
            if "fecha_hora" in rec.columns:
                rec["fecha_hora"] = pd.to_datetime(rec["fecha_hora"], errors="coerce", utc=True)
            weekly = pd.read_csv(RECHARGES_WEEKLY_CSV)
            return {"recharges": rec, "weekly": weekly}
        except Exception:
            # Corrupted or empty cache; fall through to rebuild
            pass

    # Try raw cache
    rows: Optional[List[Dict[str, Any]]] = None
    if not force_refresh and RECHARGES_RAW_JSON.exists():
        try:
            rows = _load_raw()
        except Exception:
            rows = None

    # Fetch if needed
    if rows is None:
        start_iso = start.replace(microsecond=0).isoformat() + "Z"
        end_iso = end.replace(microsecond=0).isoformat() + "Z"
        rows = _fetch_recharges(start_iso=start_iso, end_iso=end_iso, limit=limit)
        _save_raw(rows)

    frames = _rows_to_frames(rows)
    _save_frames(frames)
    return frames
