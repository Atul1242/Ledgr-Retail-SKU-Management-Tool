"""
scripts/reconcile_outlet_channel.py

Brief A5/A6 fix. The supplied outlet_master.csv has `outlet_type` and
`channel` disagreeing on ~200/320 rows. The classifier (1_clean_data.py)
keys off `channel`, so the column needs a single source of truth.

Policy adopted (in absence of data-owner input): outlet_type is canonical.
We overwrite channel := outlet_type so the channel-aware rules in Brief
Part 4 Bug 2 actually fire on consistent labels.

Run once: python scripts/reconcile_outlet_channel.py
"""
import os, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "outlet_master.csv")

def main():
    if not os.path.exists(PATH):
        print(f"outlet_master.csv not found at {PATH}", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(PATH)
    if "channel" not in df.columns or "outlet_type" not in df.columns:
        print("Required columns missing", file=sys.stderr)
        sys.exit(1)
    mismatches = (df["channel"] != df["outlet_type"]).sum()
    print(f"Mismatches found: {mismatches} / {len(df)}")
    if mismatches == 0:
        print("Already reconciled. Nothing to do.")
        return
    backup = PATH + ".bak"
    df.to_csv(backup, index=False)
    print(f"Backup written: {backup}")
    df["channel"] = df["outlet_type"]
    df.to_csv(PATH, index=False)
    print(f"Reconciled outlet_master.csv: channel <- outlet_type for {mismatches} rows.")

if __name__ == "__main__":
    main()
