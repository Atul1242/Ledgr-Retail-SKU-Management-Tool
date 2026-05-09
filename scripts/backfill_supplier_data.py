"""
scripts/backfill_supplier_data.py

One-shot DB migration: every SKU in the master file should have supplier_name,
supplier_state, hsn_code, and gst_rate populated so the reorder page can show
a real supplier, the PO generator can run for any SKU, and CGST/IGST routing
is determinable.

Defaults applied (idempotent — only fills empty fields):
  - supplier_name  := brand  (vendor and brand are usually the same in FMCG)
  - supplier_state := 'Maharashtra'  (assume intrastate for the default demo)
  - supplier_gstin := generated 27-prefix placeholder
  - hsn_code       := derived from category (3401 personal_care, 3402 household, 1905 packaged_food)
  - gst_rate       := 18.0
"""
import os, sys, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Pick up SQLite DB
os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(ROOT, 'sunrise.db')}")

CATEGORY_HSN = {
    "personal_care":  "3401",  # soaps, shampoos
    "household":      "3402",  # cleaning agents
    "packaged_food":  "1905",  # bakery / packaged biscuits
}

def deterministic_gstin(brand: str) -> str:
    """Generate a stable 15-char placeholder GSTIN per brand."""
    digest = hashlib.sha1(brand.encode()).hexdigest().upper()[:13]
    return "27" + digest  # 27 = Maharashtra prefix


def main():
    from app import app
    from models import db, SKU
    with app.app_context():
        skus = SKU.query.all()
        updated = 0
        for s in skus:
            changed = False
            if not s.supplier_name and s.brand:
                s.supplier_name = s.brand
                changed = True
            if not s.supplier_state:
                s.supplier_state = "Maharashtra"
                changed = True
            if not s.supplier_gstin and s.brand:
                s.supplier_gstin = deterministic_gstin(s.brand)
                changed = True
            if not s.hsn_code:
                s.hsn_code = CATEGORY_HSN.get((s.category or "").lower(), "9999")
                changed = True
            if not s.gst_rate:
                s.gst_rate = 18.0
                changed = True
            if changed:
                updated += 1
        db.session.commit()
        print(f"Updated {updated}/{len(skus)} SKUs.")
        # Sanity check
        ready = SKU.query.filter(SKU.supplier_name.isnot(None),
                                 SKU.hsn_code.isnot(None),
                                 SKU.gst_rate.isnot(None)).count()
        print(f"PO-ready (supplier+hsn+gst all set): {ready}/{len(skus)}")


if __name__ == "__main__":
    main()
