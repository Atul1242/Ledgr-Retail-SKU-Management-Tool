"""
po_pdf.py — GST-compliant Purchase Order PDF (Brief Part 6A).

Generates a single-page PDF for one PO (identified by po_number) using
reportlab. The PDF includes the buyer/supplier GSTINs, HSN per item, and
emits CGST+SGST or IGST columns depending on whether the PO is interstate.
"""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus.flowables import KeepTogether


def _money(v):
    try:
        return f"Rs. {float(v):,.2f}"
    except Exception:
        return "Rs. 0.00"


def render_po_pdf(po_number, items, store, supplier_meta, is_interstate):
    """Returns a BytesIO containing the PDF.
    items: list of dicts with sku_id, product_name, hsn_code, qty, unit_price,
           base_amount, gst_rate, cgst_amount, sgst_amount, igst_amount, total
    store: dict with name, state, gstin, city
    supplier_meta: dict with name, gstin, state
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                             topMargin=18*mm, bottomMargin=18*mm,
                             title=f"Purchase Order {po_number}")
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Heading1"],
                                 alignment=1, fontSize=16, spaceAfter=4)
    subtitle_style = ParagraphStyle("sub", parent=styles["Normal"],
                                    alignment=1, fontSize=10, textColor=colors.grey, spaceAfter=12)
    label_style = ParagraphStyle("label", parent=styles["Normal"], fontSize=8,
                                 textColor=colors.grey)
    body_style = ParagraphStyle("body", parent=styles["Normal"], fontSize=10)

    elements = []
    elements.append(Paragraph("PURCHASE ORDER", title_style))
    elements.append(Paragraph(f"Tax Invoice — {'IGST (Interstate)' if is_interstate else 'CGST + SGST (Intrastate)'}",
                              subtitle_style))

    header_data = [
        [Paragraph("<b>Buyer</b>", body_style), Paragraph("<b>Supplier</b>", body_style)],
        [Paragraph(f"{store.get('name','')}<br/>{store.get('city','')}, {store.get('state','')}<br/>"
                   f"GSTIN: {store.get('gstin','—')}", body_style),
         Paragraph(f"{supplier_meta.get('name','')}<br/>{supplier_meta.get('state','—')}<br/>"
                   f"GSTIN: {supplier_meta.get('gstin','—')}", body_style)],
    ]
    header_tbl = Table(header_data, colWidths=[88*mm, 88*mm])
    header_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(header_tbl)
    elements.append(Spacer(1, 8))

    meta_data = [[
        Paragraph(f"<b>PO Number:</b> {po_number}", body_style),
        Paragraph(f"<b>Date:</b> {datetime.utcnow().strftime('%d %b %Y')}", body_style),
    ]]
    meta_tbl = Table(meta_data, colWidths=[88*mm, 88*mm])
    meta_tbl.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    elements.append(meta_tbl)
    elements.append(Spacer(1, 6))

    if is_interstate:
        cols = ["#", "SKU", "Product", "HSN", "Qty", "Unit Rate", "Taxable", "IGST %", "IGST Amt", "Total"]
    else:
        cols = ["#", "SKU", "Product", "HSN", "Qty", "Unit Rate", "Taxable", "CGST %", "CGST Amt", "SGST %", "SGST Amt", "Total"]
    table_rows = [cols]
    sub_taxable = 0.0
    sub_tax = 0.0
    sub_total = 0.0
    for i, it in enumerate(items, 1):
        sub_taxable += float(it.get("base_amount", 0))
        sub_total += float(it.get("total", 0))
        if is_interstate:
            tax_amt = float(it.get("igst_amount", 0))
            sub_tax += tax_amt
            table_rows.append([str(i), it.get("sku_id", ""), it.get("product_name", "")[:28],
                               it.get("hsn_code", "—"), str(it.get("qty", 0)),
                               _money(it.get("unit_price", 0)),
                               _money(it.get("base_amount", 0)),
                               f"{it.get('igst_rate', 0):.1f}%",
                               _money(tax_amt),
                               _money(it.get("total", 0))])
        else:
            tax_amt = float(it.get("cgst_amount", 0)) + float(it.get("sgst_amount", 0))
            sub_tax += tax_amt
            table_rows.append([str(i), it.get("sku_id", ""), it.get("product_name", "")[:28],
                               it.get("hsn_code", "—"), str(it.get("qty", 0)),
                               _money(it.get("unit_price", 0)),
                               _money(it.get("base_amount", 0)),
                               f"{it.get('cgst_rate', 0):.1f}%",
                               _money(it.get("cgst_amount", 0)),
                               f"{it.get('sgst_rate', 0):.1f}%",
                               _money(it.get("sgst_amount", 0)),
                               _money(it.get("total", 0))])

    items_tbl = Table(table_rows, repeatRows=1)
    items_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D1B2A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (3, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(items_tbl)
    elements.append(Spacer(1, 12))

    totals_rows = [
        ["", "Subtotal (Taxable)", _money(sub_taxable)],
        ["", f"{'IGST' if is_interstate else 'CGST + SGST'} Total", _money(sub_tax)],
        ["", Paragraph("<b>Grand Total</b>", body_style),
            Paragraph(f"<b>{_money(sub_total)}</b>", body_style)],
    ]
    tot_tbl = Table(totals_rows, colWidths=[110*mm, 40*mm, 30*mm])
    tot_tbl.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("LINEABOVE", (1, -1), (-1, -1), 0.75, colors.black),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(tot_tbl)
    elements.append(Spacer(1, 24))

    elements.append(Paragraph(
        "Declaration: We declare that this invoice shows the actual price of the goods "
        "described and that all particulars are true and correct.",
        ParagraphStyle("decl", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
    ))
    elements.append(Spacer(1, 24))
    elements.append(Paragraph(
        f"Authorised signatory — {store.get('name','')}",
        ParagraphStyle("sig", parent=styles["Normal"], fontSize=9, alignment=2)
    ))

    doc.build(elements)
    buf.seek(0)
    return buf
