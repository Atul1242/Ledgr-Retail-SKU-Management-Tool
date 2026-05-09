"""
scripts/install_product_images.py

Copy hand-picked images from ../products_transparent/ into
static/images/products/SKU-XXX.png based on what each image actually depicts.

The mapping was hand-built by viewing every source image and matching it to
the closest SKU product name in data/sku_master.csv.
"""
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.abspath(os.path.join(ROOT, "..", "..", "products_transparent"))
DST_DIR = os.path.join(ROOT, "static", "images", "products")

# SKU code -> source filename (relative to SRC_DIR).
# Match logic: prefer an exact product type match (e.g. Soya Sauce → soya
# sauce bottle); reuse the closest visual category for SKUs with no obvious
# match (e.g. Lip Balm → small face-cream jar from the talc set).
MAPPING = {
    # ── Personal Care ──
    "SKU-001": "product_02_r2c2.png",  # Shampoo 200ml — Dove bottle
    "SKU-002": "product_03_r2c3.png",  # Shampoo 400ml — Dove bottle (larger angle)
    "SKU-003": "product_04_r2c4.png",  # Conditioner 200ml — Dove slimmer bottle
    "SKU-004": "product_06_r2c6.png",  # Body Wash 250ml — Amul tall green bottle
    "SKU-005": "product_05_r2c5.png",  # Face Wash 100ml — Amul green tube
    "SKU-006": "product_07_r2c7.png",  # Moisturiser 100g — cream tube + Nivea jar
    "SKU-007": "product_07_r2c7.png",  # Sunscreen 50g — reuse cream tube (closest)
    "SKU-008": "product_09_r3c3.png",  # Hair Oil 100ml — purple oil-shaped bottle
    "SKU-009": "product_13_r3c7.png",  # Talc Powder — Dabur talc (exact match)
    "SKU-010": "product_13_r3c7.png",  # Lip Balm — small jar from same set

    # ── Household ──
    "SKU-011": "product_08_r3c2.png",  # Dish Wash 500ml — Vim green dish soap
    "SKU-012": "product_14_r4c2.png",  # Floor Cleaner 1L — green cleaner variant
    "SKU-013": "product_10_r3c4.png",  # Toilet Cleaner 500ml — blue cleaner red cap (exact)
    "SKU-014": "product_11_r3c5.png",  # Glass Cleaner 500ml — Lazar trigger spray (exact)
    "SKU-015": "product_12_r3c6.png",  # Fabric Softener 1L — Comfort blue squat
    "SKU-016": "product_18_r4c6.png",  # Air Freshener 300ml — purple aerosol
    "SKU-017": "product_15_r4c3.png",  # Mosquito Repellent — purple bottle variant
    "SKU-018": "product_19_r4c7.png",  # Dishwasher Tabs 20 — Finish box (exact match)
    "SKU-019": "product_16_r4c4.png",  # Laundry Bar 250g — Comfort/Surf variant
    "SKU-020": "product_17_r4c5.png",  # Surface Spray 500ml — spray bottle variant

    # ── Packaged Food ──
    "SKU-021": "product_20_r5c2.png",  # Biscuits 200g — Oreo (exact match)
    "SKU-022": "product_21_r5c3.png",  # Chips 50g — yellow chips packet (exact match)
    "SKU-023": "product_22_r5c4.png",  # Namkeen 150g — Carnaval snacks pouch
    "SKU-024": "product_31_r6c7.png",  # Instant Noodles — Amol noodles pouch
    "SKU-025": "product_23_r5c5.png",  # Ketchup 500g — red sauce jar
    "SKU-026": "product_23_r5c5.png",  # Jam 500g — red jar (same shape)
    "SKU-027": "product_24_r5c6.png",  # Honey 500g — Dabur honey jar (exact match)
    "SKU-028": "product_25_r5c7.png",  # Coffee 200g — coffee jar + flour
    "SKU-029": "product_25_r5c7.png",  # Tea 250g — coffee/tea jar (closest)
    "SKU-030": "product_27_r6c3.png",  # Atta 5kg — Tata yellow grain packet
    "SKU-031": "product_26_r6c2.png",  # Rice 5kg — blue rice pouch
    "SKU-032": "product_26_r6c2.png",  # Dal 1kg — pouch (same shape)
    "SKU-033": "product_28_r6c4.png",  # Cooking Oil 1L — yellow tall jar
    "SKU-034": "product_28_r6c4.png",  # Ghee 500g — yellow jar (same)
    "SKU-035": "product_29_r6c5.png",  # Vinegar 500ml — green bottle
    "SKU-036": "product_30_r6c6.png",  # Soya Sauce 200ml — soya sauce bottle (exact match)
    "SKU-037": "product_22_r5c4.png",  # Protein Bar — snacks pouch (closest)
    "SKU-038": "product_27_r6c3.png",  # Oats 500g — grain packet
    "SKU-039": "product_27_r6c3.png",  # Cornflakes 500g — grain packet
    "SKU-040": "product_27_r6c3.png",  # Muesli 500g — grain packet
}


def main():
    if not os.path.isdir(SRC_DIR):
        print(f"Source not found: {SRC_DIR}", file=sys.stderr)
        sys.exit(1)
    os.makedirs(DST_DIR, exist_ok=True)
    ok, missing = 0, []
    for sku, fname in MAPPING.items():
        src = os.path.join(SRC_DIR, fname)
        dst = os.path.join(DST_DIR, f"{sku}.png")
        if not os.path.exists(src):
            missing.append((sku, fname))
            continue
        shutil.copy2(src, dst)
        ok += 1
    print(f"Installed {ok}/{len(MAPPING)} SKU images into {DST_DIR}")
    if missing:
        print("Missing source files:")
        for sku, f in missing:
            print(f"  {sku} -> {f}")
    # List unique source files used
    unique = sorted(set(MAPPING.values()))
    print(f"\nUnique source files used: {len(unique)}")


if __name__ == "__main__":
    main()
