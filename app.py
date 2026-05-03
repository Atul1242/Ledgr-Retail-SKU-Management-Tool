"""
app.py — Flask web application with Tabler UI dashboard
Serves API endpoints and HTML pages for the demand forecasting system.
"""
import os, sys, json, threading
import pandas as pd
import requests as http_requests
from flask import Flask, render_template, jsonify, request, send_file

app = Flask(__name__, template_folder="templates", static_folder="static")
ROOT = os.path.dirname(os.path.abspath(__file__))
PROCESSED = os.path.join(ROOT, "data", "processed")
DATA = os.path.join(ROOT, "data")

def ensure_pipeline():
    """Run pipeline if processed data doesn't exist."""
    report_path = os.path.join(PROCESSED, "monday_report.json")
    if not os.path.exists(report_path):
        sys.path.insert(0, ROOT)
        from pipeline import run_pipeline
        run_pipeline()

def load_json(name):
    path = os.path.join(PROCESSED, name)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def load_csv(name, directory=None):
    path = os.path.join(directory or PROCESSED, name)
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

# ── Pages ──
@app.route("/")
def index():
    return render_template("overview.html", page="overview")

@app.route("/retrospective")
def retrospective():
    return render_template("retrospective.html", page="retrospective")

@app.route("/forecast")
def forecast():
    return render_template("forecast.html", page="forecast")

@app.route("/reorder")
def reorder():
    return render_template("reorder.html", page="reorder")

@app.route("/classification")
def classification():
    return render_template("classification.html", page="classification")

@app.route("/accuracy")
def accuracy():
    return render_template("accuracy.html", page="accuracy")

# ── API Endpoints ──
@app.route("/api/report")
def api_report():
    return jsonify(load_json("monday_report.json"))

@app.route("/api/stockout-analysis")
def api_stockout():
    df = load_csv("diwali_stockout_analysis.csv")
    return jsonify(df.head(40).to_dict(orient="records"))

@app.route("/api/top14")
def api_top14():
    return jsonify(load_json("top_14_stockout_skus.json"))

@app.route("/api/forecasts")
def api_forecasts():
    df = load_csv("forecasts.csv")
    sku = request.args.get("sku")
    if sku:
        df = df[df["sku_id"] == sku]
    return jsonify(df.to_dict(orient="records"))

@app.route("/api/forecast-accuracy")
def api_forecast_accuracy():
    return jsonify(load_json("forecast_accuracy.json"))

@app.route("/api/reorder-recommendations")
def api_reorder_recs():
    df = load_csv("reorder_recommendations.csv")
    flag = request.args.get("flag")
    if flag and flag != "All":
        df = df[df["flags"].str.contains(flag, na=False)]
    return jsonify(df.to_dict(orient="records"))

@app.route("/api/sku-classification")
def api_sku_class():
    df = load_csv("sku_classification.csv")
    return jsonify(df.to_dict(orient="records"))

@app.route("/api/sku-list")
def api_sku_list():
    df = load_csv("sku_master.csv", DATA)
    return jsonify(df[["sku_id", "product_name", "brand", "category"]].to_dict(orient="records"))

@app.route("/api/sku-sales/<sku_id>")
def api_sku_sales(sku_id):
    sales = load_csv("sales_classified.csv")
    if len(sales) == 0:
        return jsonify([])
    sales["week_start_date"] = pd.to_datetime(sales["week_start_date"])
    sku_data = sales[sales["sku_id"] == sku_id].groupby("week_start_date").agg(
        units_sold=("units_sold", "sum")).reset_index()
    sku_data = sku_data.sort_values("week_start_date")
    sku_data["week_start_date"] = sku_data["week_start_date"].dt.strftime("%Y-%m-%d")
    return jsonify(sku_data.to_dict(orient="records"))

@app.route("/api/classification-report")
def api_class_report():
    return jsonify(load_json("classification_report.json"))

@app.route("/api/run-pipeline", methods=["POST"])
def api_run_pipeline():
    try:
        sys.path.insert(0, ROOT)
        from pipeline import run_pipeline
        results = run_pipeline()
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/download-reorder")
def download_reorder():
    path = os.path.join(PROCESSED, "reorder_recommendations.csv")
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name="reorder_plan.csv")
    return "File not found", 404

def get_data_cache():
    """Load all pipeline data once per request."""
    return {
        "report": load_json("monday_report.json"),
        "classification": load_json("classification_report.json"),
        "accuracy": load_json("forecast_accuracy.json"),
        "retro": load_json("top_14_stockout_skus.json"),
        "reorder": load_csv("reorder_recommendations.csv"),
        "sku_class": load_csv("sku_classification.csv"),
        "forecasts": load_csv("forecasts.csv"),
    }

def answer_query(msg, data):
    """Smart local chatbot that answers from pipeline data."""
    q = msg.lower().strip()
    report = data["report"]
    es = report.get("executive_summary", {}) if report else {}
    reorder = data["reorder"]
    sku_cls = data["sku_class"]
    acc = data["accuracy"] or {}
    retro = data["retro"] or {}
    cls_rpt = data["classification"] or {}
    forecasts = data["forecasts"]

    # Check for specific SKU query
    import re
    sku_match = re.search(r'sku[-\s]?(\d{2,3})', q)
    if sku_match:
        sku_num = sku_match.group(1).zfill(3)
        sku_id = f"SKU-{sku_num}"
        parts = [f"**{sku_id} Details:**\n"]
        # Reorder info
        if len(reorder) > 0:
            row = reorder[reorder["sku_id"] == sku_id]
            if len(row) > 0:
                r = row.iloc[0]
                parts.append(f"- **Product:** {r.get('product_name','N/A')} ({r.get('brand','')}, {r.get('category','')})")
                parts.append(f"- **Available Stock:** {int(r.get('available_stock',0))} units ({r.get('weeks_of_stock',0)} weeks cover)")
                parts.append(f"- **6-Week Forecast:** {int(r.get('forecast_6w_total',0))} units")
                parts.append(f"- **Reorder Qty:** {int(r.get('final_reorder_qty',0))} units (Rs.{int(r.get('order_value_inr',0)):,})")
                parts.append(f"- **Flags:** {r.get('flags','OK')}")
                if r.get('revenue_at_risk',0) > 0:
                    parts.append(f"- **Revenue at Risk:** Rs.{int(r['revenue_at_risk']):,}")
                parts.append(f"- **Reasoning:** {r.get('reason_text','')}")
        # Classification
        if len(sku_cls) > 0:
            row = sku_cls[sku_cls["sku_id"] == sku_id]
            if len(row) > 0:
                s = row.iloc[0]
                parts.append(f"- **Movement:** {s.get('movement_class','N/A')}, **ABC Class:** {s.get('abc_class','N/A')}")
                parts.append(f"- **Avg Weekly Sales:** {s.get('avg_weekly_sales',0):.0f} units")
                parts.append(f"- **Total Revenue:** Rs.{s.get('total_revenue',0):,.0f}")
        # Accuracy
        per_sku = acc.get("per_sku_mape", {})
        if sku_id in per_sku:
            info = per_sku[sku_id]
            parts.append(f"- **Forecast MAPE:** {info['mape']}% ({info['model_used']})")
        # Retro
        for s in retro.get("predicted_stockout_skus", []):
            if s["sku_id"] == sku_id:
                parts.append(f"- **Diwali Stockout Score:** {s['stockout_score']}/9 ({s['signals_triggered']})")
                parts.append(f"- **Reasoning:** {s['reasoning']}")
        return "\n".join(parts) if len(parts) > 1 else f"No data found for {sku_id}."

    # Summary / overview
    if any(w in q for w in ["summary", "overview", "report", "brief", "overall", "status", "dashboard", "hello", "hi"]):
        return f"""**Executive Summary**

- **SKUs Analyzed:** {es.get('total_skus_analyzed',0)}
- **SKUs to Reorder:** {es.get('total_skus_to_reorder',0)}
- **Total Order Value:** Rs.{es.get('total_order_value_inr',0):,}
- **Stockout Risk:** {es.get('skus_at_stockout_risk',0)} SKUs
- **Revenue at Risk:** Rs.{es.get('total_revenue_at_risk_inr', es.get('revenue_at_risk_inr',0)):,}
- **Overstock Risk:** {es.get('skus_at_overstock_risk',0)} SKUs
- **Capital Trapped:** Rs.{es.get('capital_trapped_in_overstock_inr',0):,}
- **Overall MAPE:** {acc.get('overall_mape',0)}%
- **Shelf Life Violations:** {es.get('shelf_life_violations',0)}
- **Dead Stock:** {es.get('dead_stock_count',0)} SKUs"""

    # Urgent / stockout / reorder
    if any(w in q for w in ["urgent", "stockout", "reorder", "order", "critical", "risk", "buy"]):
        urgent = report.get("urgent_orders", []) if report else []
        if not urgent and len(reorder) > 0:
            stockout_df = reorder[reorder["flags"].str.contains("STOCKOUT_RISK", na=False)].nsmallest(10, "weeks_of_stock")
            lines = ["**Urgent Reorder — Top Stockout Risk SKUs:**\n"]
            for _, r in stockout_df.iterrows():
                lines.append(f"- **{r['sku_id']}** ({r.get('product_name','')}): {r.get('weeks_of_stock',0)}w stock left, reorder **{int(r['final_reorder_qty'])}** units (Rs.{int(r.get('order_value_inr',0)):,})")
            return "\n".join(lines)
        lines = ["**Urgent Reorder — Top Stockout Risk SKUs:**\n"]
        for u in urgent[:10]:
            lines.append(f"- **{u['sku_id']}** ({u['product_name']}): {u['weeks_of_stock']}w stock, reorder **{u['reorder_qty']}** units (Rs.{u['order_value']:,})")
        lines.append(f"\n**Total Order Value:** Rs.{es.get('total_order_value_inr',0):,}")
        return "\n".join(lines)

    # Forecast / accuracy / MAPE
    if any(w in q for w in ["forecast", "accuracy", "mape", "predict", "model"]):
        per_sku = acc.get("per_sku_mape", {})
        sorted_skus = sorted(per_sku.items(), key=lambda x: x[1].get('mape',999))
        lines = [f"""**Forecast Accuracy Report**

- **Overall MAPE:** {acc.get('overall_mape',0)}%
- **LightGBM Models:** {acc.get('lgbm_count',0)}
- **Rolling Avg Fallback:** {acc.get('rolling_avg_count',0)}
- **Low Confidence SKUs:** {len(acc.get('low_confidence_skus',[]))}

**Top 5 Most Accurate:**"""]
        for sku, info in sorted_skus[:5]:
            lines.append(f"- {sku}: MAPE {info['mape']}% ({info['model_used']})")
        lines.append("\n**Bottom 5 (Least Accurate):**")
        for sku, info in sorted_skus[-5:]:
            lines.append(f"- {sku}: MAPE {info['mape']}% ({info['model_used']})")
        return "\n".join(lines)

    # Diwali / retrospective
    if any(w in q for w in ["diwali", "retro", "stockout detection", "festival"]):
        racc = retro.get("accuracy", {})
        lines = [f"""**Diwali 2023 Retrospective Analysis**

- **Correctly Identified:** {racc.get('correctly_identified',0)}/14 known stockout SKUs
- **Detection Cutoff:** Nov 7, 2023 (no lookahead bias)

**Top Predicted Stockout SKUs:**"""]
        for s in retro.get("predicted_stockout_skus", [])[:10]:
            lines.append(f"- #{s['rank']} **{s['sku_id']}** ({s['product_name']}): Score {s['stockout_score']}/9 — {s['signals_triggered']}")
        return "\n".join(lines)

    # Classification
    if any(w in q for w in ["class", "abc", "fast", "slow", "dead", "movement", "category"]):
        if len(sku_cls) > 0:
            counts = sku_cls["movement_class"].value_counts().to_dict() if "movement_class" in sku_cls.columns else {}
            abc_counts = sku_cls["abc_class"].value_counts().to_dict() if "abc_class" in sku_cls.columns else {}
            lines = ["**SKU Classification:**\n"]
            lines.append("**Movement:**")
            for k, v in counts.items():
                lines.append(f"- {k}: {v} SKUs")
            lines.append("\n**ABC Analysis:**")
            for k, v in abc_counts.items():
                lines.append(f"- {k}-class: {v} SKUs")
            return "\n".join(lines)

    # Data / classification / true zero
    if any(w in q for w in ["data", "true zero", "missing", "grid", "reconstruct", "classification report"]):
        cc = cls_rpt.get("classification_counts", {})
        return f"""**Data Classification Report**

- **Full Grid Size:** {cls_rpt.get('total_rows',0):,} rows (week x SKU x outlet)
- **Original Observed:** {cls_rpt.get('original_observed_rows',0):,}
- **Reconstructed Missing:** {cls_rpt.get('reconstructed_rows',0):,}
- **Observed:** {cc.get('observed',0):,}
- **True Zero:** {cc.get('true_zero',0):,}
- **Missing Data:** {cc.get('missing_data',0):,}
- **Stockout Gap:** {cc.get('stockout_gap',0):,}
- **Uncertain:** {cc.get('uncertain',0):,}"""

    # Overstock
    if any(w in q for w in ["overstock", "excess", "trapped", "capital"]):
        overstock = report.get("overstock_alerts", []) if report else []
        if overstock:
            lines = ["**Overstock Alerts:**\n"]
            for o in overstock:
                lines.append(f"- **{o['sku_id']}** ({o['product_name']}): {o['excess_units']} excess units, Rs.{o.get('capital_trapped',0):,} trapped")
            return "\n".join(lines)
        return f"No overstock alerts. Capital trapped in overstock: Rs.{es.get('capital_trapped_in_overstock_inr',0):,}"

    # Shelf life
    if any(w in q for w in ["shelf", "perishable", "expiry", "violation"]):
        return f"**Shelf Life Compliance:** {es.get('shelf_life_violations',0)} violations (guaranteed 0 by design). All reorder quantities are validated against shelf-life constraints before finalizing."

    # Help / what can you do
    if any(w in q for w in ["help", "what can", "how", "explain", "capability"]):
        return """**I can help you with:**

- **"Give me a summary"** — Executive overview of all KPIs
- **"Which SKUs need urgent reorder?"** — Top stockout-risk items
- **"Tell me about SKU-008"** — Full details on any specific SKU
- **"How is our forecast accuracy?"** — MAPE breakdown
- **"Show me the Diwali analysis"** — Retrospective stockout detection
- **"What's the SKU classification?"** — Movement + ABC analysis
- **"Data classification report"** — True zero vs missing data stats
- **"Any overstock risk?"** — Excess inventory alerts
- **"Shelf life violations?"** — Compliance check"""

    # Default fallback
    return """I can answer questions about your inventory data. Try asking:

- **"Summary"** — Quick overview
- **"Urgent reorders"** — Stockout risk SKUs
- **"SKU-008"** — Details on a specific SKU
- **"Forecast accuracy"** — Model performance
- **"Diwali analysis"** — Retrospective report
# OpenRouter API Key (Set this in your environment or .env file)
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "")

def build_data_context():
    """Build full data context string for the LLM."""
    d = get_data_cache()
    ctx = []
    report = d["report"] or {}
    es = report.get("executive_summary", {})
    ctx.append(f"EXECUTIVE SUMMARY: {json.dumps(es)}")
    for u in report.get("urgent_orders", [])[:10]:
        ctx.append(f"URGENT: {u['sku_id']} ({u['product_name']}): {u['weeks_of_stock']}w stock, reorder {u['reorder_qty']}, Rs.{u['order_value']:,}, {u.get('reason','')}")
    cls_rpt = d["classification"] or {}
    ctx.append(f"CLASSIFICATION: {json.dumps(cls_rpt.get('classification_counts', {}))}, total_rows={cls_rpt.get('total_rows',0)}, observed={cls_rpt.get('original_observed_rows',0)}, reconstructed={cls_rpt.get('reconstructed_rows',0)}")
    acc = d["accuracy"] or {}
    ctx.append(f"ACCURACY: overall_mape={acc.get('overall_mape',0)}%, lgbm={acc.get('lgbm_count',0)}, rolling={acc.get('rolling_avg_count',0)}")
    for sku, info in (acc.get("per_sku_mape", {})).items():
        ctx.append(f"  {sku}: MAPE={info['mape']}% ({info['model_used']})")
    reorder = d["reorder"]
    if len(reorder) > 0:
        for _, r in reorder.iterrows():
            ctx.append(f"REORDER {r['sku_id']} ({r.get('product_name','')}): stock={r.get('available_stock',0)}, {r.get('weeks_of_stock',0)}w, forecast_6w={r.get('forecast_6w_total',0)}, qty={r.get('final_reorder_qty',0)}, Rs.{r.get('order_value_inr',0):,.0f}, flags={r.get('flags','')}, rev_risk={r.get('revenue_at_risk',0)}, reason:{r.get('reason_text','')}")
    sku_cls = d["sku_class"]
    if len(sku_cls) > 0:
        for _, s in sku_cls.iterrows():
            ctx.append(f"SKU_CLASS {s['sku_id']} ({s.get('product_name','')}): {s.get('movement_class','')}, ABC={s.get('abc_class','')}, avg_weekly={s.get('avg_weekly_sales',0):.0f}, revenue=Rs.{s.get('total_revenue',0):,.0f}")
    retro = d["retro"] or {}
    racc = retro.get("accuracy", {})
    ctx.append(f"DIWALI RETRO: correct={racc.get('correctly_identified',0)}/14, missed={racc.get('missed_skus',[])}")
    for s in retro.get("predicted_stockout_skus", []):
        ctx.append(f"  #{s['rank']} {s['sku_id']} ({s['product_name']}): score={s['stockout_score']}/9, signals={s['signals_triggered']}, {s['reasoning']}")
    return "\n".join(ctx)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data_req = request.get_json()
    user_msg = data_req.get("message", "")
    history = data_req.get("history", [])
    if not user_msg:
        return jsonify({"error": "No message"}), 400

    # Try OpenRouter AI first
    try:
        context = build_data_context()
        system_prompt = f"""You are the Sunrise Demand AI Assistant for Sunrise Consumer Goods (FMCG distributor, Pune & Nashik, 320 outlets, 40 SKUs).

You have COMPLETE access to all pipeline data below. Answer accurately using this data. Be concise, use bullet points and bold for key numbers. Format currency as Rs. with commas. When asked about a specific SKU, provide ALL available details.

=== PIPELINE DATA ===
{context}
=== END DATA ==="""

        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_msg})

        resp = http_requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
            json={"model": "google/gemini-2.0-flash-001", "messages": messages, "max_tokens": 1500, "temperature": 0.3},
            timeout=30
        )
        result = resp.json()
        reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        if reply:
            return jsonify({"reply": reply})
    except Exception:
        pass

    # Fallback to local engine
    pipeline_data = get_data_cache()
    reply = answer_query(user_msg, pipeline_data)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    ensure_pipeline()
    app.run(debug=True, host="0.0.0.0", port=5000)


