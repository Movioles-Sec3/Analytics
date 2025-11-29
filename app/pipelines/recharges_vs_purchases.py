"""
Recharges vs Purchases Correlation
==================================
Compute Pearson correlation between recharge metrics and purchase metrics
from a local CSV (recargas_vs_compras*).
"""

from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_PATTERN = "recargas_vs_compras*.csv"

RECHARGE_CANDIDATES = [
    "recharge_total",
    "recargas_total",
    "recargas",
    "recharge_count",
    "recargas_count",
    "recharge_avg",
    "recargas_avg",
]

PURCHASE_CANDIDATES = [
    "purchase_total",
    "compras_total",
    "compras",
    "purchase_count",
    "compras_count",
    "purchase_avg",
    "compras_avg",
]


def get_default_dataset_path() -> Optional[Path]:
    """Return the newest matching recargas_vs_compras CSV in data/."""
    candidates = sorted(DATA_DIR.glob(DEFAULT_PATTERN), reverse=True)
    if candidates:
        return candidates[0]
    return None


def _pick_first(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    return next((c for c in candidates if c in df.columns), None)


def guess_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    """Guess recharge/purchase columns from common Spanish/English headers."""
    recharge_col = _pick_first(df, RECHARGE_CANDIDATES)
    purchase_col = _pick_first(df, PURCHASE_CANDIDATES)
    return recharge_col, purchase_col


def _prepare_numeric(df: pd.DataFrame, recharge_col: str, purchase_col: str) -> pd.DataFrame:
    """Keep rows with numeric recharge/purchase values."""
    working = df.copy()
    working[recharge_col] = pd.to_numeric(working[recharge_col], errors="coerce")
    working[purchase_col] = pd.to_numeric(working[purchase_col], errors="coerce")
    working = working.dropna(subset=[recharge_col, purchase_col])
    return working


def run_recharges_vs_purchases(
    df: Optional[pd.DataFrame] = None,
    csv_path: Optional[Path] = None,
    recharge_col: Optional[str] = None,
    purchase_col: Optional[str] = None,
) -> Dict[str, object]:
    """
    Compute Pearson correlation between recharge and purchase metrics.

    Returns a dict with:
        - correlation (float or None)
        - pairs_used (int)
        - recharge_col / purchase_col (str)
        - cleaned_df (pd.DataFrame)
        - dropped_rows (int)
    """
    if df is None:
        if csv_path is None:
            csv_path = get_default_dataset_path()
        if csv_path is None or not csv_path.exists():
            raise FileNotFoundError("No recargas_vs_compras CSV found.")
        df = pd.read_csv(csv_path)

    if recharge_col is None or purchase_col is None:
        guessed_recharge, guessed_purchase = guess_columns(df)
        recharge_col = recharge_col or guessed_recharge
        purchase_col = purchase_col or guessed_purchase

    if recharge_col is None or purchase_col is None:
        raise ValueError("Could not detect recharge/purchase columns in the dataset.")

    cleaned_df = _prepare_numeric(df, recharge_col, purchase_col)
    dropped_rows = len(df) - len(cleaned_df)

    correlation = None
    if len(cleaned_df) > 1:
        correlation = cleaned_df[[recharge_col, purchase_col]].corr(method="pearson").iloc[0, 1]

    return {
        "correlation": correlation,
        "pairs_used": len(cleaned_df),
        "recharge_col": recharge_col,
        "purchase_col": purchase_col,
        "cleaned_df": cleaned_df,
        "dropped_rows": dropped_rows,
    }
