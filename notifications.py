"""
notifications.py — WhatsApp, Email, and Telegram Notifications (Brief Phase 13)

Sends Monday morning pipeline reports via:
  1. Twilio WhatsApp Business API (primary)
  2. Flask-Mail email (fallback)
  3. Telegram Bot API (optional)

Also runs the outlet non-submission detector (Brief Part 5A / C5 fix)
which alerts the owner when previously-active outlets miss two consecutive
weekly uploads.
"""
import os
import json
import requests
from datetime import datetime
import pandas as pd


def load_report():
    """Load latest Monday report."""
    root = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(root, "data", "processed", "monday_report.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def format_whatsapp_message(report):
    """Format concise WhatsApp message from Monday report."""
    es = report.get("executive_summary", {})
    date = report.get("report_date", datetime.now().strftime("%Y-%m-%d"))

    msg = (
        f"📦 *Sunrise Monday Report [{date}]*\n\n"
        f"• *{es.get('total_skus_to_reorder', 0)}* SKUs need reorder\n"
        f"• *{es.get('skus_at_stockout_risk', 0)}* at stockout risk\n"
        f"• Total order value: *₹{es.get('total_order_value_inr', 0):,}*\n"
        f"• Revenue at risk: *₹{es.get('total_revenue_at_risk_inr', 0):,}*\n"
    )

    # Urgent items
    urgent = report.get("urgent_orders", [])[:3]
    if urgent:
        msg += "\n*Top Urgent:*\n"
        for u in urgent:
            msg += f"  ▸ {u['sku_id']} ({u['product_name']}): {u['weeks_of_stock']}w stock\n"

    # Expiry alerts (Brief Phase 12 / C3 fix — uses real EXPIRY_ALERT count,
    # not shelf_life_violations which counts qty-cap corrections, a different thing)
    expiry_count = es.get("expiry_alert_count", 0)
    if expiry_count > 0:
        msg += f"\n⚠ *{expiry_count} SKUs near expiry — check dashboard.*\n"

    # Dead stock
    dead = es.get("dead_stock_count", 0)
    if dead > 0:
        msg += f"\n🔴 {dead} dead stock SKUs flagged for clearance.\n"

    msg += f"\n🔗 Dashboard: http://localhost:5000/"
    return msg


def send_whatsapp(message):
    """Send via Twilio WhatsApp Business API."""
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    from_num = os.environ.get("TWILIO_WHATSAPP_FROM", "")
    to_num = os.environ.get("OWNER_WHATSAPP_TO", "")

    if not all([sid, token, from_num, to_num]):
        print("[notify] WhatsApp: Missing Twilio credentials, skipping")
        return False

    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        resp = requests.post(url, auth=(sid, token), data={
            "From": f"whatsapp:{from_num}",
            "To": f"whatsapp:{to_num}",
            "Body": message
        }, timeout=15)
        if resp.status_code in [200, 201]:
            print(f"[notify] WhatsApp sent successfully to {to_num}")
            return True
        else:
            print(f"[notify] WhatsApp failed: {resp.status_code} {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"[notify] WhatsApp error: {e}")
        return False


def send_email(report):
    """Send HTML email via Flask-Mail."""
    try:
        from flask_mail import Mail, Message as MailMessage
        from flask import Flask

        mail_server = os.environ.get("MAIL_SERVER", "")
        mail_user = os.environ.get("MAIL_USERNAME", "")
        mail_pass = os.environ.get("MAIL_PASSWORD", "")
        owner_email = os.environ.get("OWNER_EMAIL", "")

        if not all([mail_server, mail_user, owner_email]):
            print("[notify] Email: Missing mail config, skipping")
            return False

        app = Flask(__name__)
        app.config.update(
            MAIL_SERVER=mail_server,
            MAIL_PORT=int(os.environ.get("MAIL_PORT", 587)),
            MAIL_USE_TLS=True,
            MAIL_USERNAME=mail_user,
            MAIL_PASSWORD=mail_pass,
            MAIL_DEFAULT_SENDER=mail_user
        )
        mail = Mail(app)

        es = report.get("executive_summary", {})
        date = report.get("report_date", datetime.now().strftime("%Y-%m-%d"))

        html = f"""
        <html><body style="font-family:Inter,sans-serif;color:#1d273b">
        <div style="background:#1a1c2e;color:#fff;padding:20px;border-radius:8px 8px 0 0">
            <h2 style="color:#4ade80;margin:0">☀ Sunrise Monday Report</h2>
            <p style="color:rgba(255,255,255,0.5);margin:4px 0 0">{date}</p>
        </div>
        <div style="padding:20px;background:#fff;border:1px solid #e6e7e9">
            <table style="width:100%;border-collapse:collapse">
                <tr><td style="padding:8px;border-bottom:1px solid #eee"><strong>SKUs to Reorder</strong></td><td style="text-align:right;font-weight:700">{es.get('total_skus_to_reorder',0)}</td></tr>
                <tr><td style="padding:8px;border-bottom:1px solid #eee"><strong>Stockout Risk</strong></td><td style="text-align:right;color:#d63939;font-weight:700">{es.get('skus_at_stockout_risk',0)} SKUs</td></tr>
                <tr><td style="padding:8px;border-bottom:1px solid #eee"><strong>Total Order Value</strong></td><td style="text-align:right;font-weight:700">₹{es.get('total_order_value_inr',0):,}</td></tr>
                <tr><td style="padding:8px;border-bottom:1px solid #eee"><strong>Revenue at Risk</strong></td><td style="text-align:right;color:#d63939;font-weight:700">₹{es.get('total_revenue_at_risk_inr',0):,}</td></tr>
                <tr><td style="padding:8px;border-bottom:1px solid #eee"><strong>Dead Stock</strong></td><td style="text-align:right">{es.get('dead_stock_count',0)} SKUs</td></tr>
                <tr><td style="padding:8px"><strong>Shelf Life Violations</strong></td><td style="text-align:right">{es.get('shelf_life_violations',0)}</td></tr>
            </table>
        </div>
        <div style="padding:16px;text-align:center;background:#f8f9fa;border-radius:0 0 8px 8px">
            <a href="http://localhost:5000/" style="background:#206bc4;color:#fff;padding:10px 24px;text-decoration:none;border-radius:6px;font-weight:600">Open Dashboard</a>
            <div style="margin-top:12px;font-size:11px;color:#9ca3af">Generated by Ledgr · demand-forecasting AI for Sunrise Consumer Goods</div>
        </div>
        </body></html>
        """

        with app.app_context():
            msg = MailMessage(
                subject=f"📦 Sunrise Monday Report — {date}",
                recipients=[owner_email],
                html=html
            )
            mail.send(msg)
            print(f"[notify] Email sent to {owner_email}")
            return True
    except Exception as e:
        print(f"[notify] Email error: {e}")
        return False


def send_telegram(message):
    """Send via Telegram Bot API."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not all([bot_token, chat_id]):
        print("[notify] Telegram: Missing config, skipping")
        return False

    try:
        # Convert WhatsApp markdown to Telegram markdown
        text = message.replace("*", "**")
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }, timeout=15)
        if resp.ok:
            print(f"[notify] Telegram sent to chat {chat_id}")
            return True
        else:
            print(f"[notify] Telegram failed: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"[notify] Telegram error: {e}")
        return False


def detect_non_submitting_outlets():
    """Brief C5: find outlets that submitted in >=3 of the last 6 weeks but
    missed the most recent 2 consecutive weeks. Returns list of dicts."""
    root = os.path.dirname(os.path.abspath(__file__))
    sales_path = os.path.join(root, "data", "processed", "sales_classified.csv")
    outlet_master = os.path.join(root, "data", "outlet_master.csv")
    if not (os.path.exists(sales_path) and os.path.exists(outlet_master)):
        return []
    try:
        sales = pd.read_csv(sales_path)
        sales["week_start_date"] = pd.to_datetime(sales["week_start_date"])
        outlets = pd.read_csv(outlet_master)
    except Exception as e:
        print(f"[notify] Could not load data for non-submission detection: {e}")
        return []

    # An outlet "submitted" in a week iff at least one row with units_sold > 0
    # exists for that outlet/week (matches the Step 1 definition in 1_clean_data.py).
    submitted = sales[sales["units_sold"] > 0].groupby(["outlet_id", "week_start_date"]).size().reset_index()
    weeks_sorted = sorted(sales["week_start_date"].unique())
    if len(weeks_sorted) < 6:
        return []
    last6 = weeks_sorted[-6:]
    last2 = set(weeks_sorted[-2:])

    submitted_weeks_by_outlet = submitted.groupby("outlet_id")["week_start_date"].apply(set).to_dict()

    violators = []
    for _, o in outlets.iterrows():
        oid = o["outlet_id"]
        weeks_set = submitted_weeks_by_outlet.get(oid, set())
        weeks_in_last6 = sum(1 for w in last6 if w in weeks_set)
        missed_last2 = all(w not in weeks_set for w in last2)
        if weeks_in_last6 >= 3 and missed_last2:
            violators.append({
                "outlet_id": oid,
                "outlet_name": o.get("outlet_name", ""),
                "city": o.get("city", ""),
                "area": o.get("area", "")
            })
    return violators


def send_non_submission_alert(violators):
    """Send the non-submission alert via WhatsApp/Email/Telegram."""
    if not violators:
        return False
    names = ", ".join(f"{v['outlet_id']} ({v['outlet_name']})" for v in violators[:8])
    extra = "" if len(violators) <= 8 else f" (+{len(violators) - 8} more)"
    msg = (
        f"⚠ *{len(violators)} outlets have not reported this week*: {names}{extra}.\n"
        f"Check with your field team before the Monday reorder."
    )
    print(f"\n[notify] Non-submission alert: {len(violators)} outlets")
    sent_any = False
    if send_whatsapp(msg):
        sent_any = True
    if not sent_any:
        # Reuse email channel if WhatsApp failed
        try:
            from flask_mail import Mail, Message as MailMessage
            from flask import Flask
            mail_server = os.environ.get("MAIL_SERVER", "")
            mail_user = os.environ.get("MAIL_USERNAME", "")
            owner_email = os.environ.get("OWNER_EMAIL", "")
            if mail_server and mail_user and owner_email:
                app = Flask(__name__)
                app.config.update(
                    MAIL_SERVER=mail_server,
                    MAIL_PORT=int(os.environ.get("MAIL_PORT", 587)),
                    MAIL_USE_TLS=True,
                    MAIL_USERNAME=mail_user,
                    MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD", ""),
                    MAIL_DEFAULT_SENDER=mail_user
                )
                mail = Mail(app)
                with app.app_context():
                    mail.send(MailMessage(
                        subject="⚠ Sunrise — Outlets Missing Submissions",
                        recipients=[owner_email],
                        body=msg
                    ))
                    sent_any = True
        except Exception as e:
            print(f"[notify] Non-submission email failed: {e}")
    send_telegram(msg)
    return sent_any


def send_all_notifications():
    """Send notifications via all configured channels. Called after pipeline completes."""
    report = load_report()
    if not report:
        print("[notify] No report found, skipping notifications")
        return

    message = format_whatsapp_message(report)
    print(f"\n[notify] Sending notifications...")

    # Try WhatsApp first
    wa_ok = send_whatsapp(message)

    # Email fallback (or always send if configured)
    if not wa_ok:
        send_email(report)

    # Telegram (always send if configured)
    send_telegram(message)

    # Non-submission alert (separate message if any outlets are flagged)
    violators = detect_non_submitting_outlets()
    if violators:
        send_non_submission_alert(violators)

    print("[notify] Done.")


if __name__ == "__main__":
    send_all_notifications()
