"""
Products at risk of stockout
============================
Identify the most frequently ordered products so the team can plan
replenishment before inventory runs out.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import plotly.express as px
import streamlit as st


PRODUCT_NAME_CANDIDATES: Iterable[str] = (
    "product_name",
    "producto",
    "producto_nombre",
    "nombre_producto",
    "item_name",
    "item",
    "item_nombre",
)

QUANTITY_CANDIDATES: Iterable[str] = (
    "quantity",
    "qty",
    "cantidad",
    "units",
    "unit_count",
    "order_quantity",
    "order_count",
    "cantidad_unidades",
    "total_units",
    "units_sold",
    "orders",
    "total_orders",
)

CATEGORY_CANDIDATES: Iterable[str] = (
    "category",
    "categoria",
    "categoria_nombre",
    "product_category",
    "categoria_producto",
)


@dataclass
class ColumnMapping:
    product_col: str
    quantity_col: Optional[str] = None
    category_col: Optional[str] = None


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _detect_columns(df: pd.DataFrame) -> Optional[ColumnMapping]:
    """Find the best matching column names for product/quantity/category."""
    product_col = next((c for c in PRODUCT_NAME_CANDIDATES if c in df.columns), None)
    if not product_col:
        return None

    quantity_col = next((c for c in QUANTITY_CANDIDATES if c in df.columns), None)
    category_col = next((c for c in CATEGORY_CANDIDATES if c in df.columns), None)

    return ColumnMapping(product_col=product_col, quantity_col=quantity_col, category_col=category_col)


def render_stock_risk(df: Optional[pd.DataFrame]) -> None:
    """
    Render the stock risk tab.

    Expects a DataFrame with at least one product-name column. If a quantity column exists,
    it is used as weight; otherwise each row counts as a single order.
    """
    st.header("📦 Products at Risk of Stockout")
    st.markdown(
        "Surface the products with the highest demand so you can prioritize replenishment. "
        "Use the filters to focus on specific categories or events."
    )

    if df is None or df.empty:
        st.info("Load a dataset with product and order information first.")
        return

    mapping = _detect_columns(df)
    working: Optional[pd.DataFrame] = None

    if mapping is None:
        st.warning(
            "No column resembling `product_name`, `producto_nombre`, or similar was detected in the main dataset. "
            "Load a product-demand CSV below."
        )
        uploaded_products = st.file_uploader(
            "Upload product demand CSV",
            type=["csv"],
            key="stock_risk_product_uploader",
            help="Provide a file with at least product name and units ordered.",
        )

        default_candidates = list(DATA_DIR.glob("productos_populares*.csv"))
        default_path_value = str(default_candidates[0]) if default_candidates else str(DATA_DIR / "productos_populares.csv")
        custom_path = st.text_input(
            "Or read from local path",
            value=default_path_value,
            help="Point to a CSV on disk (e.g. data/productos_populares_20251031_224656.csv).",
        )

        candidate_df: Optional[pd.DataFrame] = None
        try:
            if uploaded_products is not None:
                candidate_df = pd.read_csv(uploaded_products)
            elif custom_path and Path(custom_path).exists():
                candidate_df = pd.read_csv(custom_path)
                st.caption(f"Loaded dataset from `{custom_path}`.")
        except Exception as exc:
            st.error(f"Could not read the provided CSV: {exc}")
            return

        if candidate_df is None:
            st.info("Upload a CSV or provide a valid path to analyze product demand.")
            return

        mapping = _detect_columns(candidate_df)
        if mapping is None:
            st.error(
                "The supplied CSV still lacks recognizable product or quantity columns. "
                "Ensure it contains headers like `product_name`, `quantity`, or `total_units`."
            )
            return
        working = candidate_df.copy()
    else:
        working = df.copy()

    # Remove rows without a meaningful product name
    working = working[working[mapping.product_col].astype(str).str.strip().ne("")]
    if working.empty:
        st.info("No rows with valid product names remain after cleaning the dataset.")
        return

    # Prepare quantity column
    if mapping.quantity_col:
        working["_units"] = pd.to_numeric(working[mapping.quantity_col], errors="coerce").fillna(0)
    else:
        working["_units"] = 1

    working = working[working["_units"] > 0]
    if working.empty:
        st.info("All quantity values are zero. Review the quantity column or add data.")
        return

    st.subheader("⚙️ Filters")

    # Filter by category (if present)
    if mapping.category_col and working[mapping.category_col].notnull().any():
        categories = sorted(working[mapping.category_col].dropna().astype(str).unique())
        selected_categories = st.multiselect(
            "Categories to include",
            options=categories,
            default=categories,
            help="Pick one or multiple categories to narrow the analysis.",
        )
        if selected_categories:
            working = working[working[mapping.category_col].astype(str).isin(selected_categories)]
        if working.empty:
            st.info("No data available after applying the category filter.")
            return

    # Filter by event (if a column exists)
    if "event_name" in working.columns:
        candidate_events = sorted(working["event_name"].astype(str).unique())
        default_events = [
            e
            for e in candidate_events
            if any(x in e.lower() for x in ("order", "pedido", "purchase", "reorder", "checkout"))
        ]
        if not default_events:
            default_events = candidate_events

        selected_events = st.multiselect(
            "Events to include",
            options=candidate_events,
            default=default_events,
            help="Keep only the events that correspond to orders or reorders.",
        )
        if selected_events:
            working = working[working["event_name"].astype(str).isin(selected_events)]
        if working.empty:
            st.info("No rows remain for the selected events.")
            return

    st.caption(
        "If your dataset contains a quantity column (for example `quantity` or `cantidad`), "
        "it is used to weight the ranking. Otherwise each row counts once."
    )

    aggregated = (
        working.groupby(mapping.product_col, dropna=False)["_units"]
        .sum()
        .rename("total_units")
        .reset_index()
        .sort_values("total_units", ascending=False)
    )

    total_units = aggregated["total_units"].sum()
    aggregated["share_pct"] = (aggregated["total_units"] / total_units * 100).round(2)

    max_products = int(max(aggregated.shape[0], 1))
    top_n = st.slider(
        "Number of products to highlight",
        min_value=1,
        max_value=max_products,
        value=min(10, max_products),
    )

    min_orders = st.number_input(
        "Minimum units to flag risk", value=1, min_value=1, step=1
    )
    aggregated = aggregated[aggregated["total_units"] >= min_orders]
    if aggregated.empty:
        st.info("No products meet the minimum units threshold.")
        return

    top_products = aggregated.head(top_n)

    st.subheader("🏅 Top Risk Products")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Top product",
            f"{top_products.iloc[0][mapping.product_col]}",
            f"{int(top_products.iloc[0]['total_units'])} orders",
        )
    with col2:
        st.metric("Total orders analyzed", f"{int(total_units)}")
    with col3:
        st.metric(
            "Top N cumulative share",
            f"{top_products['share_pct'].sum():.1f}%",
        )

    fig = px.bar(
        top_products,
        x="total_units",
        y=mapping.product_col,
        orientation="h",
        text="total_units",
        title="Highest-demand products",
        labels={
            mapping.product_col: "Product",
            "total_units": "Units / orders",
        },
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis=dict(autorange="reversed"))

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📋 Full detail")
    st.dataframe(top_products, hide_index=True, use_container_width=True)

    csv_bytes = aggregated.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download full ranking",
        data=csv_bytes,
        file_name="products_stock_risk.csv",
        mime="text/csv",
    )

    st.markdown(
        "💡 **Tip:** Combine this ranking with inventory on hand or supplier lead times to "
        "prioritize replenishment and avoid stockouts."
    )
