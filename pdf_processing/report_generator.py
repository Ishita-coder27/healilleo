"""
report_generator.py — Generate a polished PDF report from extracted vitals.
Uses reportlab Platypus for professional layout.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.platypus import PageBreak

from vitals_extractor import VitalResult


# ─────────────────────────────────────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────────────────────────────────────

C_HEADER_BG   = colors.HexColor("#1A2C4E")    # deep navy
C_HEADER_FG   = colors.white
C_CAT_BG      = colors.HexColor("#2E5090")    # medium blue
C_CAT_FG      = colors.white
C_ROW_ALT     = colors.HexColor("#F0F4FB")    # pale blue stripe
C_ROW_NORM    = colors.white
C_NORMAL      = colors.HexColor("#1A7A3F")    # green
C_HIGH        = colors.HexColor("#C0392B")    # red
C_LOW         = colors.HexColor("#2980B9")    # blue
C_UNKNOWN     = colors.HexColor("#7F8C8D")    # grey
C_WARN_BG     = colors.HexColor("#FFF3CD")    # yellow for abnormal rows
C_CRIT_BG     = colors.HexColor("#FDECEA")    # light red for critical
C_GRID        = colors.HexColor("#D0D8E8")
C_ACCENT      = colors.HexColor("#E8572A")    # orange accent


def _status_color(status: str) -> colors.Color:
    return {
        "Normal":  C_NORMAL,
        "High":    C_HIGH,
        "Low":     C_LOW,
        "Elevated": colors.HexColor("#E67E22"),
    }.get(status, C_UNKNOWN)


def _row_bg(status: str, row_idx: int) -> colors.Color:
    if status in ("High", "Low", "Critical"):
        return C_WARN_BG
    return C_ROW_NORM if row_idx % 2 == 0 else C_ROW_ALT


# ─────────────────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle", parent=base["Title"],
        fontSize=22, textColor=C_HEADER_FG,
        fontName="Helvetica-Bold", leading=28,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=base["Normal"],
        fontSize=10, textColor=colors.HexColor("#A8C4F0"),
        fontName="Helvetica", alignment=TA_CENTER,
    )
    section_style = ParagraphStyle(
        "Section", parent=base["Normal"],
        fontSize=11, textColor=C_CAT_FG,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT, leading=14,
    )
    body_style = ParagraphStyle(
        "Body", parent=base["Normal"],
        fontSize=9, textColor=colors.HexColor("#2C3E50"),
        fontName="Helvetica", leading=12,
    )
    value_style = ParagraphStyle(
        "Value", parent=base["Normal"],
        fontSize=9.5, fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )
    info_key_style = ParagraphStyle(
        "InfoKey", parent=base["Normal"],
        fontSize=9, textColor=colors.HexColor("#5D6D7E"),
        fontName="Helvetica-Bold",
    )
    info_val_style = ParagraphStyle(
        "InfoVal", parent=base["Normal"],
        fontSize=9, textColor=colors.HexColor("#1A2C4E"),
        fontName="Helvetica",
    )
    footer_style = ParagraphStyle(
        "Footer", parent=base["Normal"],
        fontSize=7.5, textColor=colors.HexColor("#7F8C8D"),
        fontName="Helvetica", alignment=TA_CENTER,
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "section": section_style,
        "body": body_style,
        "value": value_style,
        "info_key": info_key_style,
        "info_val": info_val_style,
        "footer": footer_style,
    }


# ─────────────────────────────────────────────────────────────────────────────
# HEADER / FOOTER CANVAS
# ─────────────────────────────────────────────────────────────────────────────

class _DocCanvas:
    """Adds running header and footer to every page."""

    def __init__(self, filename: str, patient_name: str):
        self.filename = filename
        self.patient_name = patient_name

    def __call__(self, canvas, doc):
        W, H = A4
        canvas.saveState()

        # ── Top banner ────────────────────────────────────────────────────────
        canvas.setFillColor(C_HEADER_BG)
        canvas.rect(0, H - 2.0 * cm, W, 2.0 * cm, fill=True, stroke=False)
        canvas.setFont("Helvetica-Bold", 13)
        canvas.setFillColor(colors.white)
        canvas.drawString(1.5 * cm, H - 1.3 * cm, "Vitals Extraction Report")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#A8C4F0"))
        canvas.drawRightString(W - 1.5 * cm, H - 1.3 * cm,
                               f"Patient: {self.patient_name or 'N/A'}")

        # ── Thin accent line ──────────────────────────────────────────────────
        canvas.setFillColor(C_ACCENT)
        canvas.rect(0, H - 2.1 * cm, W, 0.12 * cm, fill=True, stroke=False)

        # ── Footer ────────────────────────────────────────────────────────────
        canvas.setFillColor(colors.HexColor("#F0F4FB"))
        canvas.rect(0, 0, W, 1.1 * cm, fill=True, stroke=False)
        canvas.setFillColor(colors.HexColor("#7F8C8D"))
        canvas.setFont("Helvetica", 7.5)
        ts = datetime.now().strftime("%d %b %Y  %H:%M")
        canvas.drawString(1.5 * cm, 0.4 * cm,
                          f"Generated by Vital Extractor  •  {ts}")
        canvas.drawRightString(W - 1.5 * cm, 0.4 * cm,
                               f"Page {doc.page}")
        canvas.setStrokeColor(C_GRID)
        canvas.setLineWidth(0.5)
        canvas.line(1.0 * cm, 1.1 * cm, W - 1.0 * cm, 1.1 * cm)

        canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# HELPER BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _patient_info_table(info: Dict[str, str], styles: dict) -> Table:
    """Compact 2-column key/value table for patient info."""
    if not info:
        info = {}

    ordered_keys = ["Patient Name", "Age", "Gender", "Date of Birth", "Report Date", "Doctor"]
    rows = []
    row = []
    for i, key in enumerate(ordered_keys):
        val = info.get(key, "—")
        cell = [
            Paragraph(key, styles["info_key"]),
            Paragraph(val, styles["info_val"]),
        ]
        row.append(cell)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row + [[Paragraph("", styles["info_key"]),
                            Paragraph("", styles["info_val"])]])

    # Flatten for Table: each row = [key1, val1, key2, val2]
    flat_rows = []
    for r in rows:
        flat_rows.append([r[0][0], r[0][1], r[1][0], r[1][1]])

    col_widths = [3.5 * cm, 5.5 * cm, 3.5 * cm, 5.5 * cm]
    t = Table(flat_rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F9FC")),
        ("BOX", (0, 0), (-1, -1), 0.8, C_GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, C_GRID),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _stats_pills(stats: Dict, used_gemini: bool, pdf_method: str, styles: dict) -> Table:
    """A row of summary stat boxes."""
    pills = [
        ("Total Vitals", str(stats["total"]), colors.HexColor("#2E5090")),
        ("Normal", str(stats["normal"]), C_NORMAL),
        ("Abnormal", str(stats["abnormal"]), C_HIGH),
        ("Via Table", str(stats["by_table"]), colors.HexColor("#8E44AD")),
        ("Via Regex", str(stats["by_regex"]), colors.HexColor("#2980B9")),
        ("Via Gemini", str(stats["by_gemini"]) if used_gemini else "—", C_ACCENT),
    ]

    header = [Paragraph(f'<font color="white"><b>{p[0]}</b></font>', styles["body"]) for p in pills]
    values = [Paragraph(f'<font size="16"><b>{p[1]}</b></font>', ParagraphStyle(
        "pill", parent=styles["body"], alignment=TA_CENTER,
        textColor=p[2], fontName="Helvetica-Bold"
    )) for p in pills]

    t = Table([header, values], colWidths=[3.0 * cm] * 6)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_HEADER_BG),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F7F9FC")),
        ("BOX", (0, 0), (-1, -1), 0.8, C_GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, C_GRID),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return t


def _vitals_table(vitals: List[VitalResult], styles: dict) -> List:
    """Build per-category vital sign tables."""
    from collections import defaultdict

    by_category: Dict[str, List[VitalResult]] = defaultdict(list)
    for v in vitals:
        by_category[v.category].append(v)

    story_elements = []
    CATEGORY_ORDER = ["Basic Vitals", "CBC", "Metabolic Panel", "Lipid Panel",
                      "Liver Function", "Thyroid", "Iron Studies", "Vitamins",
                      "Coagulation", "Inflammation", "Other"]

    headers = ["Test Name", "Value", "Unit", "Reference Range", "Status", "Method"]
    col_widths = [5.5 * cm, 2.5 * cm, 3.0 * cm, 4.0 * cm, 2.5 * cm, 2.0 * cm]

    for cat in CATEGORY_ORDER:
        items = by_category.get(cat, [])
        if not items:
            continue

        # ── Category header ────────────────────────────────────────────────
        cat_cell = Paragraph(f"  {cat}", styles["section"])
        cat_table = Table([[cat_cell]], colWidths=[sum(col_widths)])
        cat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), C_CAT_BG),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))

        # ── Column headers ─────────────────────────────────────────────────
        header_cells = [
            Paragraph(f'<font color="white"><b>{h}</b></font>', styles["body"])
            for h in headers
        ]
        table_data = [header_cells]

        # ── Data rows ──────────────────────────────────────────────────────
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), C_HEADER_BG),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.4, C_GRID),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]

        for idx, v in enumerate(items):
            sc = _status_color(v.status)
            bg = _row_bg(v.status, idx)
            row_idx = idx + 1

            status_para = Paragraph(
                f'<font color="{sc.hexval()}"><b>{v.status}</b></font>',
                styles["body"]
            )

            method_label = {"table": "Table", "regex": "Regex",
                            "gemini": "Gemini", "ocr": "OCR"}.get(v.method, v.method)
            method_color = {"table": "#8E44AD", "regex": "#2980B9",
                            "gemini": "#E8572A", "ocr": "#16A085"}.get(v.method, "#7F8C8D")
            method_para = Paragraph(
                f'<font color="{method_color}">{method_label}</font>',
                ParagraphStyle("mc", parent=styles["body"], alignment=TA_CENTER)
            )

            row = [
                Paragraph(v.name, styles["body"]),
                Paragraph(f"<b>{v.value}</b>", ParagraphStyle(
                    "vb", parent=styles["body"], alignment=TA_CENTER,
                    fontName="Helvetica-Bold"
                )),
                Paragraph(v.unit, ParagraphStyle(
                    "uc", parent=styles["body"], alignment=TA_CENTER
                )),
                Paragraph(v.reference_range or "—", ParagraphStyle(
                    "rc", parent=styles["body"], alignment=TA_CENTER
                )),
                status_para,
                method_para,
            ]
            table_data.append(row)
            style_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg))

        vitals_t = Table(table_data, colWidths=col_widths, repeatRows=1)
        vitals_t.setStyle(TableStyle(style_cmds))

        story_elements.append(KeepTogether([
            cat_table,
            vitals_t,
            Spacer(1, 0.4 * cm),
        ]))

    return story_elements


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def generate_report(
    output_path: str,
    vitals: List[VitalResult],
    patient_info: Dict[str, str],
    stats: Dict,
    used_gemini: bool,
    pdf_method: str,
) -> str:
    """Create the output PDF and return the path."""

    W, H = A4
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = _build_styles()
    patient_name = patient_info.get("Patient Name", "")
    canvas_fn = _DocCanvas(output_path, patient_name)

    story = []

    # ── Space below running header ─────────────────────────────────────────
    story.append(Spacer(1, 0.6 * cm))

    # ── Report Title ───────────────────────────────────────────────────────
    story.append(Paragraph("Vital Signs Extraction Report", styles["title"]))
    story.append(Paragraph(
        f"Automatically extracted using multi-layer analysis  •  "
        f"{datetime.now().strftime('%d %B %Y')}",
        styles["subtitle"]
    ))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=C_ACCENT))
    story.append(Spacer(1, 0.4 * cm))

    # ── Patient Info ───────────────────────────────────────────────────────
    section_hdr = Paragraph("Patient Information", ParagraphStyle(
        "SH", parent=styles["section"], textColor=C_HEADER_BG, fontSize=11
    ))
    story.append(section_hdr)
    story.append(Spacer(1, 0.2 * cm))
    story.append(_patient_info_table(patient_info, styles))
    story.append(Spacer(1, 0.5 * cm))

    # ── Extraction Summary ─────────────────────────────────────────────────
    story.append(Paragraph("Extraction Summary", ParagraphStyle(
        "SH2", parent=styles["section"], textColor=C_HEADER_BG, fontSize=11
    )))
    story.append(Spacer(1, 0.2 * cm))
    story.append(_stats_pills(stats, used_gemini, pdf_method, styles))
    story.append(Spacer(1, 0.4 * cm))

    # ── Extraction method note ─────────────────────────────────────────────
    note_parts = []
    if stats["by_table"] > 0:
        note_parts.append(f"<b>{stats['by_table']}</b> from structured tables")
    if stats["by_regex"] > 0:
        note_parts.append(f"<b>{stats['by_regex']}</b> via pattern matching")
    if used_gemini and stats["by_gemini"] > 0:
        note_parts.append(f"<b>{stats['by_gemini']}</b> via Gemini AI (low-confidence fallback)")
    method_note = "  |  ".join(note_parts) if note_parts else "See individual rows for source."
    story.append(Paragraph(
        f"Extraction breakdown:  {method_note}",
        ParagraphStyle("note", parent=styles["body"],
                       textColor=colors.HexColor("#5D6D7E"), fontSize=8)
    ))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=C_GRID))
    story.append(Spacer(1, 0.4 * cm))

    # ── Vitals Tables ──────────────────────────────────────────────────────
    story.append(Paragraph("Extracted Vital Signs & Lab Values", ParagraphStyle(
        "SH3", parent=styles["section"], textColor=C_HEADER_BG, fontSize=11
    )))
    story.append(Spacer(1, 0.3 * cm))

    if vitals:
        story.extend(_vitals_table(vitals, styles))
    else:
        story.append(Paragraph(
            "No vitals could be extracted from the uploaded document. "
            "Please ensure the PDF contains readable medical data.",
            styles["body"]
        ))

    # ── Disclaimer ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_GRID))
    story.append(Spacer(1, 0.2 * cm))
    disclaimer = (
        "<b>Disclaimer:</b> This report is generated automatically and is intended "
        "for informational purposes only. Always consult a qualified healthcare "
        "professional for medical decisions. Values shown may differ from clinical "
        "lab-specific reference ranges."
    )
    story.append(Paragraph(disclaimer, ParagraphStyle(
        "disc", parent=styles["body"],
        textColor=colors.HexColor("#95A5A6"), fontSize=7.5, leading=10
    )))

    # ── Build ──────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=canvas_fn, onLaterPages=canvas_fn)
    return output_path
