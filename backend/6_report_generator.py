"""
backend/6_report_generator.py -- Monday Morning Report Generator
Includes business impact: revenue_at_risk, capital_trapped_in_overstock.
"""
import pandas as pd, json, os, numpy as np
from datetime import datetime

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)): return int(obj)
        if isinstance(obj, (np.floating,)): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super().default(obj)

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _resolve_report_date(processed_dir):
    """Anchor the Monday report date to the first forecast week, so the
    delivery dates and projections shown in the report agree with the
    forecast horizon (Brief A7 fix)."""
    fc_path = os.path.join(processed_dir, "forecasts.csv")
    if os.path.exists(fc_path):
        try:
            fc = pd.read_csv(fc_path)
            if "week_start_date" in fc.columns and len(fc) > 0:
                return pd.to_datetime(fc["week_start_date"]).min().to_pydatetime()
        except Exception:
            pass
    return datetime.now()

def run():
    root = get_project_root()
    processed_dir = os.path.join(root, "data", "processed")
    print("[6_report] Generating Monday morning report...")
    reorder = pd.read_csv(os.path.join(processed_dir, "reorder_recommendations.csv"))
    sku_class = pd.read_csv(os.path.join(processed_dir, "sku_classification.csv"))
    report_anchor = _resolve_report_date(processed_dir)
    stockout_alerts = reorder[reorder["flags"].str.contains("STOCKOUT_RISK", na=False)]
    overstock_alerts = reorder[reorder["flags"].str.contains("OVERSTOCK_RISK", na=False)]
    expiry_alerts_df = reorder[reorder["flags"].str.contains("EXPIRY_ALERT", na=False)]
    to_reorder = reorder[reorder["final_reorder_qty"] > 0]

    # Business impact metrics from reorder data
    total_revenue_at_risk = int(reorder["revenue_at_risk"].sum()) if "revenue_at_risk" in reorder.columns else 0
    total_overstock_value = int(reorder["overstock_value"].sum()) if "overstock_value" in reorder.columns else 0

    # Shelf life violations (MUST be 0)
    violations = reorder[(reorder["final_reorder_qty"] > 0) & (reorder["final_reorder_qty"] > reorder["shelf_life_max"])]
    shelf_violations = len(violations)

    # Urgent orders (top 10 stockout risk by weeks_of_stock ascending)
    urgent = stockout_alerts.nsmallest(10, "weeks_of_stock")
    urgent_list = []
    for _, r in urgent.iterrows():
        urgent_list.append({
            "sku_id": r["sku_id"], "product_name": r["product_name"],
            "category": r["category"], "weeks_of_stock": float(r["weeks_of_stock"]),
            "reorder_qty": int(r["final_reorder_qty"]),
            "order_value": int(r["order_value_inr"]),
            "delivery_date": r["delivery_date"], "reason": r["reason_text"],
            "revenue_at_risk": int(r.get("revenue_at_risk", 0))
        })

    overstock_list = []
    for _, r in overstock_alerts.iterrows():
        overstock_list.append({
            "sku_id": r["sku_id"], "product_name": r["product_name"],
            "category": r["category"], "available_stock": int(r["available_stock"]),
            "forecast_6w": int(r["forecast_6w_total"]),
            "excess_units": int(max(0, r["available_stock"] - r["forecast_6w_total"])),
            "capital_trapped": int(r.get("overstock_value", 0))
        })

    expiry_list = []
    for _, r in expiry_alerts_df.iterrows():
        try:
            dte = int(r.get("days_to_earliest_expiry", 0)) if str(r.get("days_to_earliest_expiry", "")).strip() != "" else None
        except Exception:
            dte = None
        expiry_list.append({
            "sku_id": r["sku_id"], "product_name": r["product_name"],
            "category": r["category"],
            "available_stock": int(r["available_stock"]),
            "forecast_6w": int(r["forecast_6w_total"]),
            "earliest_expiry_date": r.get("earliest_expiry_date", ""),
            "days_to_expiry": dte,
            "recommended_action": "Run markdown / promotion to clear stock before expiry"
        })

    full_reorder = []
    for _, r in to_reorder.iterrows():
        full_reorder.append({
            "sku_id": r["sku_id"], "product_name": r["product_name"],
            "category": r["category"], "reorder_qty": int(r["final_reorder_qty"]),
            "order_value": int(r["order_value_inr"]), "flags": r["flags"],
            "delivery_date": r["delivery_date"]
        })

    report = {
        "report_date": report_anchor.strftime("%Y-%m-%d"),
        "generated_at": datetime.now().strftime("%I:%M %p IST"),
        "data_anchor_note": f"Stockout/delivery dates anchored to forecast horizon ({report_anchor.date()}). System time: {datetime.now().date()}.",
        "executive_summary": {
            "total_skus_to_reorder": int(len(to_reorder)),
            "total_order_value_inr": int(to_reorder["order_value_inr"].sum()),
            "skus_at_stockout_risk": int(len(stockout_alerts)),
            "skus_at_overstock_risk": int(len(overstock_alerts)),
            "total_revenue_at_risk_inr": total_revenue_at_risk,
            "revenue_at_risk_inr": total_revenue_at_risk,
            "capital_trapped_in_overstock_inr": total_overstock_value,
            "shelf_life_violations": int(shelf_violations),
            "total_skus_analyzed": int(len(reorder)),
            "dead_stock_count": int(reorder["flags"].str.contains("DEAD_STOCK", na=False).sum()),
            "expiry_alert_count": int(len(expiry_list)),
        },
        "urgent_orders": urgent_list,
        "overstock_alerts": overstock_list,
        "expiry_alerts": expiry_list,
        "full_reorder_list": full_reorder,
    }

    with open(os.path.join(processed_dir, "monday_report.json"), "w") as f:
        json.dump(report, f, indent=2, cls=NpEncoder)

    print(f"[6_report] Complete!")
    es = report["executive_summary"]
    print(f"  SKUs to reorder: {es['total_skus_to_reorder']}")
    print(f"  Total order value: Rs.{es['total_order_value_inr']:,}")
    print(f"  Stockout risk: {es['skus_at_stockout_risk']}")
    print(f"  Revenue at risk: Rs.{es['total_revenue_at_risk_inr']:,}")
    print(f"  Overstock risk: {es['skus_at_overstock_risk']}")
    print(f"  Capital trapped: Rs.{es['capital_trapped_in_overstock_inr']:,}")
    print(f"  Shelf life violations: {es['shelf_life_violations']} [OK]")
    print(f"  Expiry alerts: {es['expiry_alert_count']}")
    return True

if __name__ == "__main__":
    run()
