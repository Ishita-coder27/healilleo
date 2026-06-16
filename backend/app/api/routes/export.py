from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.user import User
from app.models.medical_reports import MedicalReport
from app.models.report_vitals import ReportVital
from app.models.vitals import Vital
from app.core.auth import get_current_user
from app.crud import medications as crud_meds
from io import BytesIO
import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT

router = APIRouter(prefix="/export", tags=["Export"])

TEAL       = colors.HexColor("#0D9488")
LIGHT_GRAY = colors.HexColor("#F8FAFC")
DARK       = colors.HexColor("#1E293B")
GRAY       = colors.HexColor("#64748B")
WHITE      = colors.white


@router.get("/health-report")
def export_health_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Fetch latest report vitals for this user (via medical_reports → report_vitals → vital)
    rows = (
        db.query(ReportVital, Vital, MedicalReport)
        .join(MedicalReport, ReportVital.report_id == MedicalReport.id)
        .join(Vital, ReportVital.vital_id == Vital.id)
        .filter(MedicalReport.user_id == current_user.id)
        .order_by(MedicalReport.uploaded_at.desc())
        .limit(50)
        .all()
    )

    # Deduplicate by vital key — keep most recent value per vital
    seen = {}
    for rv, v, mr in rows:
        if v.key not in seen:
            seen[v.key] = (rv, v, mr)
    vitals_data = list(seen.values())

    meds = crud_meds.get_medications_by_user(db, current_user.id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_s   = ParagraphStyle("T", fontSize=22, textColor=TEAL, spaceAfter=2, fontName="Helvetica-Bold")
    sub_s     = ParagraphStyle("S", fontSize=11, textColor=GRAY, spaceAfter=2, fontName="Helvetica")
    sect_s    = ParagraphStyle("Se", fontSize=13, textColor=DARK, spaceBefore=14, spaceAfter=8, fontName="Helvetica-Bold")
    body_s    = ParagraphStyle("B", fontSize=10, textColor=GRAY, fontName="Helvetica")
    disc_s    = ParagraphStyle("D", fontSize=8, textColor=GRAY, alignment=TA_CENTER, fontName="Helvetica-Oblique")

    now = datetime.datetime.now().strftime("%d %B %Y, %I:%M %p")
    user_name = (
        getattr(current_user, "full_name", None)
        or getattr(current_user, "name", None)
        or current_user.email
    )

    story = []

    # ── Header ──────────────────────────────────────────────────
    story.append(Paragraph("Heallio", title_s))
    story.append(Paragraph("Personal Health Report", sub_s))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(f"Prepared for: <b>{user_name}</b>", body_s))
    story.append(Paragraph(f"Generated: {now}", body_s))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceAfter=8))

    # ── Vitals ───────────────────────────────────────────────────
    story.append(Paragraph("Extracted Health Vitals", sect_s))

    if vitals_data:
        tbl = [["Vital", "Value", "Unit", "Reference Range", "Status", "From Report"]]
        for rv, v, mr in vitals_data:
            tbl.append([
                str(v.display_name or v.key),
                str(rv.value or "—"),
                str(rv.unit or "—"),
                str(rv.reference_range or "—"),
                str(rv.status or "—"),
                str(mr.report_date or str(mr.uploaded_at)[:10]),
            ])
        t = Table(tbl, colWidths=[3.8*cm, 2.2*cm, 1.8*cm, 4.2*cm, 2.5*cm, 2.5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), TEAL),
            ("TEXTCOLOR",     (0,0),(-1,0), WHITE),
            ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0),(-1,-1), 9),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT_GRAY]),
            ("GRID",          (0,0),(-1,-1), 0.3, colors.HexColor("#E2E8F0")),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No vitals extracted yet. Upload a medical report PDF to get started.", body_s))

    story.append(Spacer(1, 0.5 * cm))

    # ── Medications ───────────────────────────────────────────────
    story.append(Paragraph("Current Medications", sect_s))

    if meds:
        mtbl = [["Medication", "Dosage", "Frequency", "Start Date", "End Date"]]
        for m in meds:
            mtbl.append([
                str(m.medication_name or "—"),
                str(m.dosage or "—"),
                str(m.frequency or "—"),
                str(m.start_date or "—")[:10],
                str(m.end_date or "Ongoing")[:10],
            ])
        t2 = Table(mtbl, colWidths=[4.5*cm, 3*cm, 3.5*cm, 3*cm, 3*cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), TEAL),
            ("TEXTCOLOR",     (0,0),(-1,0), WHITE),
            ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0),(-1,-1), 9),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT_GRAY]),
            ("GRID",          (0,0),(-1,-1), 0.3, colors.HexColor("#E2E8F0")),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ]))
        story.append(t2)
    else:
        story.append(Paragraph("No medications recorded yet.", body_s))

    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=6))
    story.append(Paragraph(
        "This report is generated by Heallio for personal reference only and does not constitute medical advice. "
        "Always consult a qualified healthcare professional for diagnosis and treatment.",
        disc_s,
    ))

    doc.build(story)
    buffer.seek(0)

    fname = f"heallio-health-report-{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
