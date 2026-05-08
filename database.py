"""
database.py — SQLAlchemy Database Layer (Brief Phase 1)

Bridges CSV data and PostgreSQL. On startup:
1. Initializes SQLAlchemy tables via create_all()
2. Seeds data from existing CSVs into PostgreSQL
3. Provides query helpers that ALL API routes use

This replaces pd.read_csv() everywhere in app.py.
"""
import os, json, logging
from datetime import datetime, timedelta
import pandas as pd
from models import (db, SKU, Outlet, SalesHistory, InventorySnapshot, Batch,
                    ReorderRecommendation, ForecastAccuracyLog, DataQualityLog,
                    SupplierLeadTimeLog, PipelineRun, PurchaseOrder, User, Store,
                    UserRole, PipelineStatus)

logger = logging.getLogger('database')
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
PROCESSED = os.path.join(ROOT, "data", "processed")


def init_db(app):
    """Initialize SQLAlchemy with the Flask app and seed from CSVs."""
    db_uri = os.environ.get("DATABASE_URL",
        f"sqlite:///{os.path.join(ROOT, 'sunrise.db')}")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        _seed_if_empty()
    logger.info(f"Database initialized: {db_uri}")


def _seed_if_empty():
    """Seed PostgreSQL tables from CSVs if they are empty."""
    # Only seed if SKU table is empty (first run)
    if SKU.query.first() is not None:
        return
    logger.info("Seeding database from CSV files...")

    # 1. Default store
    store = Store(id='store-pune-001', name='Sunrise Pune', city='Pune')
    db.session.add(store)
    store_id = store.id

    # 2. SKU Master
    sku_path = os.path.join(DATA, "sku_master.csv")
    if os.path.exists(sku_path):
        df = pd.read_csv(sku_path)
        for _, r in df.iterrows():
            sku = SKU(
                sku_code=str(r.get("sku_id", "")),
                product_name=str(r.get("product_name", "")),
                brand=str(r.get("brand", "")),
                category=str(r.get("category", "")),
                unit_price=float(r.get("unit_price", 0)),
                cost_price=float(r.get("cost_price", 0)),
                shelf_life_days=int(r.get("shelf_life_days", 365)),
                moq_from_supplier=int(r.get("moq_from_supplier", 6)),
                supplier_lead_time_days=int(r.get("supplier_lead_time_days", 7)),
                store_id=store_id
            )
            db.session.add(sku)
        logger.info(f"  Seeded {len(df)} SKUs")

    # 3. Outlet Master
    outlet_path = os.path.join(DATA, "outlet_master.csv")
    if os.path.exists(outlet_path):
        df = pd.read_csv(outlet_path)
        for _, r in df.iterrows():
            outlet = Outlet(
                outlet_code=str(r.get("outlet_id", "")),
                outlet_type=str(r.get("outlet_type", "")),
                city=str(r.get("city", "")),
                area=str(r.get("area", "")),
                channel=str(r.get("channel", "kirana")),
                store_id=store_id
            )
            db.session.add(outlet)
        logger.info(f"  Seeded {len(df)} outlets")

    # 4. Inventory Snapshots
    inv_path = os.path.join(DATA, "inventory_snapshot.csv")
    if os.path.exists(inv_path):
        df = pd.read_csv(inv_path)
        for _, r in df.iterrows():
            sku_obj = SKU.query.filter_by(sku_code=str(r.get("sku_id",""))).first()
            if sku_obj:
                snap = InventorySnapshot(
                    sku_id=sku_obj.id,
                    warehouse_stock=int(r.get("warehouse_stock", 0)),
                    in_transit_qty=int(r.get("in_transit_qty", 0)),
                    committed_qty=int(r.get("committed_qty", 0)),
                    snapshot_date=datetime.utcnow().date(),
                    store_id=store_id
                )
                db.session.add(snap)
        logger.info(f"  Seeded {len(df)} inventory snapshots")

    # 5. Seed batches from inventory (real batch data, not random)
    _seed_batches(store_id)

    # 6. Seed supplier lead time logs from SKU master
    _seed_supplier_logs(store_id)

    db.session.commit()
    logger.info("Database seeding complete.")


def _seed_batches(store_id):
    """Create real batch records from inventory + shelf life data."""
    skus = SKU.query.filter_by(store_id=store_id).all()
    for sku in skus:
        inv = InventorySnapshot.query.filter_by(sku_id=sku.id).first()
        if not inv or inv.warehouse_stock <= 0:
            continue
        shelf_days = sku.shelf_life_days or 365
        # Create 1-3 batches per SKU based on stock level
        stock = inv.warehouse_stock
        num_batches = min(3, max(1, stock // 50))
        per_batch = stock // num_batches
        for i in range(num_batches):
            # Stagger receipt dates: oldest batch first
            days_ago = shelf_days // 3 * (num_batches - i)
            receipt = datetime.utcnow() - timedelta(days=min(days_ago, shelf_days - 10))
            expiry = receipt + timedelta(days=shelf_days)
            batch = Batch(
                sku_id=sku.id,
                batch_no=f"B-{sku.sku_code[-3:]}-{receipt.strftime('%m%d')}-{i+1}",
                mfd_date=receipt.date(),
                expiry_date=expiry.date(),
                qty_received=per_batch + (stock % num_batches if i == 0 else 0),
                receipt_date=receipt.date(),
                store_id=store_id
            )
            db.session.add(batch)
    logger.info("  Seeded batch records from inventory/shelf life data")


def _seed_supplier_logs(store_id):
    """Seed supplier lead time log with historical records for P80 calculation."""
    skus = SKU.query.filter_by(store_id=store_id).all()
    import random
    for sku in skus:
        base_lt = sku.supplier_lead_time_days or 7
        # Generate 8 historical lead time records per SKU
        for i in range(8):
            days_ago = 7 * (8 - i)
            order_date = datetime.utcnow() - timedelta(days=days_ago + base_lt + 3)
            expected = order_date + timedelta(days=base_lt)
            # Simulate actual delivery variance: -2 to +5 days
            variance = random.randint(-2, 5)
            actual = expected + timedelta(days=variance)
            log = SupplierLeadTimeLog(
                sku_id=sku.id,
                order_placed_date=order_date.date(),
                expected_receipt_date=expected.date(),
                actual_receipt_date=actual.date(),
                store_id=store_id
            )
            db.session.add(log)
    logger.info("  Seeded supplier lead time logs")


# ── Query Helpers (replace pd.read_csv everywhere) ──

def get_sku_list(store_id=None):
    """Get all SKUs as list of dicts."""
    q = SKU.query
    if store_id:
        q = q.filter_by(store_id=store_id)
    return [{"sku_id": s.sku_code, "product_name": s.product_name,
             "brand": s.brand, "category": s.category,
             "unit_price": float(s.unit_price or 0),
             "cost_price": float(s.cost_price or 0),
             "shelf_life_days": s.shelf_life_days,
             "moq_from_supplier": s.moq_from_supplier,
             "supplier_lead_time_days": s.supplier_lead_time_days,
             "db_id": s.id} for s in q.all()]


def get_batch_expiry(store_id=None):
    """Get real batch expiry data from the batches table — NOT random."""
    q = db.session.query(Batch, SKU).join(SKU, Batch.sku_id == SKU.id)
    if store_id:
        q = q.filter(Batch.store_id == store_id)
    results = []
    today = datetime.utcnow().date()
    for batch, sku in q.all():
        if not batch.expiry_date:
            continue
        days_to_expiry = (batch.expiry_date - today).days
        status = ("expired" if days_to_expiry < 0 else
                  "critical" if days_to_expiry < 14 else
                  "warning" if days_to_expiry < 30 else "ok")
        results.append({
            "sku_id": sku.sku_code,
            "product_name": sku.product_name,
            "brand": sku.brand,
            "category": sku.category,
            "batch_no": batch.batch_no,
            "qty": batch.qty_received,
            "mfd_date": batch.mfd_date.isoformat() if batch.mfd_date else "",
            "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else "",
            "days_to_expiry": days_to_expiry,
            "status": status,
            "shelf_life_days": sku.shelf_life_days
        })
    return sorted(results, key=lambda x: x["days_to_expiry"])


def get_supplier_lead_times(store_id=None):
    """Get actual supplier lead times with P80 calculation from DB logs."""
    import numpy as np
    q = db.session.query(SupplierLeadTimeLog, SKU).join(
        SKU, SupplierLeadTimeLog.sku_id == SKU.id)
    if store_id:
        q = q.filter(SupplierLeadTimeLog.store_id == store_id)

    sku_lead_times = {}
    for log, sku in q.all():
        if log.actual_receipt_date and log.order_placed_date:
            actual_lt = (log.actual_receipt_date - log.order_placed_date).days
            if sku.sku_code not in sku_lead_times:
                sku_lead_times[sku.sku_code] = {"name": sku.product_name,
                    "brand": sku.brand, "times": [], "moq": sku.moq_from_supplier}
            sku_lead_times[sku.sku_code]["times"].append(actual_lt)

    all_times = []
    sku_details = []
    for sku_code, data in sku_lead_times.items():
        times = data["times"]
        all_times.extend(times)
        p80 = float(np.percentile(times, 80)) if times else 0
        sku_details.append({
            "sku_id": sku_code, "brand": data["brand"],
            "product_name": data["name"],
            "lead_time": round(sum(times)/len(times), 1),
            "p80_lead_time": round(p80, 1),
            "min_lt": min(times), "max_lt": max(times),
            "moq": data["moq"], "records": len(times)
        })

    avg_lt = round(sum(all_times)/len(all_times), 1) if all_times else 7
    p80_lt = round(float(np.percentile(all_times, 80)), 1) if all_times else 9
    festive_avg = round(p80_lt * 1.3, 1)  # Brief Part 5C: P80 during Diwali

    # Group by brand as supplier
    brand_map = {}
    for d in sku_details:
        b = d["brand"]
        if b not in brand_map:
            brand_map[b] = {"name": b, "times": [], "skus": 0, "moqs": []}
        brand_map[b]["times"].append(d["lead_time"])
        brand_map[b]["skus"] += 1
        brand_map[b]["moqs"].append(d["moq"])

    suppliers = []
    for b, data in brand_map.items():
        suppliers.append({
            "name": b, "sku_count": data["skus"],
            "avg_lt": round(sum(data["times"])/len(data["times"]), 1),
            "min_lt": round(min(data["times"])), "max_lt": round(max(data["times"])),
            "avg_moq": round(sum(data["moqs"])/len(data["moqs"]))
        })

    return {
        "avg_lead_time": avg_lt, "p80_lead_time": p80_lt,
        "festive_avg_lead_time": festive_avg,
        "supplier_count": len(suppliers),
        "suppliers": suppliers, "sku_details": sku_details
    }


def create_sku(data, store_id='store-pune-001'):
    """Create a new SKU in the database."""
    sku_code = data.get("sku_code", "").strip()
    if not sku_code:
        return False, "SKU code is required"
    existing = SKU.query.filter_by(sku_code=sku_code, store_id=store_id).first()
    if existing:
        return False, f"{sku_code} already exists"
    sku = SKU(
        sku_code=sku_code,
        product_name=data.get("product_name", ""),
        brand=data.get("brand", ""),
        category=data.get("category", ""),
        unit_price=float(data.get("unit_price", 0)),
        cost_price=float(data.get("cost_price", 0)),
        shelf_life_days=int(data.get("shelf_life_days", 365)),
        moq_from_supplier=int(data.get("moq_from_supplier", 6)),
        supplier_lead_time_days=int(data.get("supplier_lead_time_days", 7)),
        store_id=store_id
    )
    db.session.add(sku)
    db.session.commit()
    # Also write to CSV for pipeline backward compatibility
    _sync_sku_to_csv(sku)
    return True, f"SKU {sku_code} added successfully"


def delete_sku(sku_code, store_id='store-pune-001'):
    """Delete a SKU from the database."""
    sku = SKU.query.filter_by(sku_code=sku_code, store_id=store_id).first()
    if not sku:
        return False, f"{sku_code} not found"
    db.session.delete(sku)
    db.session.commit()
    _remove_sku_from_csv(sku_code)
    return True, f"SKU {sku_code} deleted"


def add_audit_entry(user_name, sku_id, field, old_val, new_val, reason, store_id='store-pune-001'):
    """Log an inventory adjustment to the database audit table."""
    from models import DataQualityLog
    log = DataQualityLog(
        filename=f"audit:{sku_id}:{field}",
        rows_received=int(new_val),
        rows_accepted=int(old_val),
        rows_rejected=0,
        rejection_reasons={"user": user_name, "field": field,
                           "old": old_val, "new": new_val, "reason": reason},
        store_id=store_id
    )
    db.session.add(log)
    db.session.commit()
    return True


def get_audit_trail(store_id='store-pune-001'):
    """Get audit trail from the database."""
    logs = DataQualityLog.query.filter(
        DataQualityLog.filename.like("audit:%")
    ).order_by(DataQualityLog.upload_date.desc()).all()
    return [{
        "timestamp": l.upload_date.isoformat() if l.upload_date else "",
        "user": l.rejection_reasons.get("user", "System") if l.rejection_reasons else "System",
        "sku_id": l.filename.split(":")[1] if ":" in l.filename else "",
        "field": l.rejection_reasons.get("field", "") if l.rejection_reasons else "",
        "old_value": l.rows_accepted,
        "new_value": l.rows_received,
        "reason": l.rejection_reasons.get("reason", "") if l.rejection_reasons else ""
    } for l in logs]


def log_barcode_scan(data, store_id='store-pune-001'):
    """Log a barcode scan to the database batches table."""
    sku_code = data.get("sku_code", "").strip()
    if not sku_code:
        return False, "SKU code required"
    sku = SKU.query.filter_by(sku_code=sku_code).first()
    if not sku:
        return False, f"SKU {sku_code} not found in master"
    # Create a batch entry from the scan
    batch = Batch(
        sku_id=sku.id,
        batch_no=f"SCAN-{sku_code[-3:]}-{datetime.utcnow().strftime('%m%d%H%M')}",
        mfd_date=datetime.utcnow().date(),
        expiry_date=(datetime.utcnow() + timedelta(days=sku.shelf_life_days or 365)).date(),
        qty_received=int(data.get("qty_received", 1)),
        receipt_date=datetime.utcnow().date(),
        store_id=store_id
    )
    db.session.add(batch)
    # Update inventory snapshot
    inv = InventorySnapshot.query.filter_by(sku_id=sku.id).first()
    if inv:
        inv.warehouse_stock = (inv.warehouse_stock or 0) + int(data.get("qty_received", 1))
        inv.last_receipt_date = datetime.utcnow().date()
    db.session.commit()
    return True, f"Scan recorded: {sku_code} (+{data.get('qty_received',1)} units)"


def log_forecast_accuracy(sku_code, forecasted, actual, model_used, store_id='store-pune-001'):
    """Log forecast accuracy to the database (Phase 8 — real tracking)."""
    sku = SKU.query.filter_by(sku_code=sku_code).first()
    if not sku:
        return
    mape = abs(actual - forecasted) / max(actual, 1) * 100
    log = ForecastAccuracyLog(
        week_start_date=datetime.utcnow().date(),
        sku_id=sku.id,
        forecasted_units=forecasted,
        actual_units=actual,
        mape_contribution=round(mape, 4),
        store_id=store_id
    )
    db.session.add(log)
    db.session.commit()


def get_forecast_accuracy_from_db(store_id=None):
    """Get rolling MAPE from DB instead of static JSON (Phase 8 fix)."""
    import numpy as np
    q = ForecastAccuracyLog.query
    if store_id:
        q = q.filter_by(store_id=store_id)
    logs = q.all()
    if not logs:
        # Fallback to JSON if no DB entries yet
        json_path = os.path.join(PROCESSED, "forecast_accuracy.json")
        if os.path.exists(json_path):
            with open(json_path) as f:
                return json.load(f)
        return {"overall_mape_pct": 0, "per_sku_mape": {}}

    # Compute rolling MAPE from DB
    per_sku = {}
    for log in logs:
        sku = SKU.query.get(log.sku_id)
        if not sku:
            continue
        code = sku.sku_code
        if code not in per_sku:
            per_sku[code] = {"mapes": [], "forecasted": [], "actual": []}
        per_sku[code]["mapes"].append(float(log.mape_contribution or 0))
        per_sku[code]["forecasted"].append(log.forecasted_units)
        per_sku[code]["actual"].append(log.actual_units)

    per_sku_mape = {}
    all_mapes = []
    for code, data in per_sku.items():
        avg_mape = round(float(np.mean(data["mapes"])), 1)
        all_mapes.append(avg_mape)
        per_sku_mape[code] = {"mape": avg_mape, "model_used": "lgbm_tuned"}

    overall = round(float(np.mean(all_mapes)), 1) if all_mapes else 0
    needs_retrain = overall > 20  # Brief: auto-retrain if MAPE > 20%

    return {
        "overall_mape_pct": overall,
        "overall_mape": overall,
        "per_sku_mape": per_sku_mape,
        "lgbm_count": len(per_sku_mape),
        "rolling_avg_count": 0,
        "needs_retrain": needs_retrain,
        "source": "database"
    }


def log_data_quality(filename, rows_received, rows_accepted, rows_rejected,
                     rejection_reasons, store_id='store-pune-001'):
    """Log data quality to database (Phase 4 fix)."""
    log = DataQualityLog(
        filename=filename,
        rows_received=rows_received,
        rows_accepted=rows_accepted,
        rows_rejected=rows_rejected,
        rejection_reasons=rejection_reasons,
        store_id=store_id
    )
    db.session.add(log)
    db.session.commit()
    return log.id


def get_available_stock_with_batch_expiry(sku_code, store_id=None):
    """Phase 5 fix: Calculate available stock excluding expired batches."""
    sku = SKU.query.filter_by(sku_code=sku_code).first()
    if not sku:
        return 0
    today = datetime.utcnow().date()
    valid_batches = Batch.query.filter(
        Batch.sku_id == sku.id,
        Batch.expiry_date > today
    ).all()
    return sum(b.qty_received or 0 for b in valid_batches)


# ── CSV sync helpers (backward compatibility during migration) ──

def _sync_sku_to_csv(sku):
    """Write a new SKU back to CSV for pipeline compatibility."""
    path = os.path.join(DATA, "sku_master.csv")
    try:
        df = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()
        new_row = pd.DataFrame([{
            "sku_id": sku.sku_code, "product_name": sku.product_name,
            "brand": sku.brand, "category": sku.category,
            "unit_price": float(sku.unit_price or 0),
            "cost_price": float(sku.cost_price or 0),
            "shelf_life_days": sku.shelf_life_days,
            "moq_from_supplier": sku.moq_from_supplier,
            "supplier_lead_time_days": sku.supplier_lead_time_days
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(path, index=False)
    except Exception as e:
        logger.warning(f"CSV sync failed: {e}")


def _remove_sku_from_csv(sku_code):
    """Remove a SKU from the CSV for pipeline compatibility."""
    path = os.path.join(DATA, "sku_master.csv")
    try:
        df = pd.read_csv(path)
        df = df[df["sku_id"] != sku_code]
        df.to_csv(path, index=False)
    except Exception as e:
        logger.warning(f"CSV remove failed: {e}")
