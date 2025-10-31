"""
Example: Order Peak Hours Analysis
===================================
Demonstrates how to use the order_peak_hours pipeline directly.

Usage:
    python scripts/analyze_order_peak_hours.py [data_file]
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.pipelines.order_peak_hours import run_order_peak_hours_etl


def main():
    print("=" * 60)
    print("Order Peak Hours Analysis")
    print("=" * 60)
    print()
    
    # Get data file from arguments or use default
    if len(sys.argv) > 1:
        data_file = Path(sys.argv[1])
    else:
        data_file = Path("data/compras_completadas_20251004_172958.csv")
    
    if not data_file.exists():
        print(f"❌ Error: File not found: {data_file}")
        print(f"   Please provide a valid CSV file path.")
        sys.exit(1)
    
    print(f"📂 Analyzing data from: {data_file}")
    print()
    
    # Run the ETL pipeline
    print("🔄 Running Order Peak Hours ETL pipeline...")
    try:
        frames = run_order_peak_hours_etl(
            start=None,  # Will default to today
            end=None,
            timezone_offset_minutes=-300,  # UTC-5 (Colombia)
            force_refresh=False,
            fallback_to_local=True,
            local_data_path=data_file
        )
    except Exception as e:
        print(f"❌ Error running ETL: {e}")
        sys.exit(1)
    
    df_hourly = frames.get("hourly")
    df_summary = frames.get("summary")
    
    if df_hourly is None or df_hourly.empty:
        print("⚠️  No data available to analyze.")
        sys.exit(1)
    
    print("✅ Analysis complete!")
    print()
    
    # Display summary
    print("📊 SUMMARY")
    print("-" * 60)
    if df_summary is not None and not df_summary.empty:
        for _, row in df_summary.iterrows():
            print(f"{row['metric']:.<40} {row['value']}")
    print()
    
    # Display hourly distribution
    print("📈 HOURLY DISTRIBUTION")
    print("-" * 60)
    print(f"{'Hour':<6} {'Orders':<10} {'Percentage':<12} {'Status'}")
    print("-" * 60)
    
    for _, row in df_hourly.iterrows():
        hour = int(row['hour'])
        count = int(row['order_count'])
        percentage = row.get('percentage', 0)
        is_peak = row.get('is_peak', False)
        status = "🔴 PEAK" if is_peak else "🔵 Normal"
        
        print(f"{hour:02d}:00  {count:<10} {percentage:>6.2f}%      {status}")
    
    print()
    
    # Display peak hours specifically
    if 'is_peak' in df_hourly.columns:
        peak_hours_df = df_hourly[df_hourly['is_peak']]
        if not peak_hours_df.empty:
            print("🔝 PEAK HOURS")
            print("-" * 60)
            peak_hours = peak_hours_df['hour'].apply(lambda h: f"{int(h):02d}:00").tolist()
            print(f"Peak hours: {', '.join(peak_hours)}")
            total_peak_orders = int(peak_hours_df['order_count'].sum())
            peak_percentage = peak_hours_df['percentage'].sum()
            print(f"Orders in peak hours: {total_peak_orders} ({peak_percentage:.1f}% of total)")
            print()
    
    # Display file locations
    print("📁 OUTPUT FILES")
    print("-" * 60)
    print(f"Hourly data: data/order_peak_hours_hourly.csv")
    print(f"Summary:     data/order_peak_hours_summary.csv")
    print(f"Raw JSON:    data/order_peak_hours_raw.json")
    print()
    
    print("💡 TIP: Run 'streamlit run app/dashboard.py' for interactive visualization")
    print()


if __name__ == "__main__":
    main()
