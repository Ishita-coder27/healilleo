"""
app.py — Vital Extractor Gradio Application (Gradio 6.0 compatible)

Pipeline:
  PDF upload → multi-layer extraction → interactive table + downloadable PDF + JSON + backend save
"""

import os
import json
import tempfile
import traceback
import logging
from datetime import datetime
from typing import Optional

import gradio as gr
import pandas as pd
import requests

from vitals_extractor import VitalsExtractor
from report_generator import generate_report

# Auto-load .env if present (GEMINI_API_KEY pre-fills the UI key field)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — key must be pasted manually
_ENV_GEMINI_KEY = os.environ.get("GROQ_API_KEY", "")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Backend URL ────────────────────────────────────────────────────────────────
BACKEND_BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/api")

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

STATUS_EMOJI = {
    "Normal":   "✅ Normal",
    "High":     "🔺 High",
    "Low":      "🔻 Low",
    "Elevated": "⚠️ Elevated",
    "Unknown":  "❓ Unknown",
}
METHOD_LABEL = {
    "table":  "📊 Table",
    "regex":  "🔍 Regex",
    "gemini": "🤖 Gemini",
    "ocr":    "📷 OCR",
}


def vitals_to_dataframe(vitals) -> pd.DataFrame:
    rows = []
    for v in vitals:
        rows.append({
            "Test Name":       v.name,
            "Value":           v.value,
            "Unit":            v.unit,
            "Reference Range": v.reference_range or "—",
            "Status":          STATUS_EMOJI.get(v.status, v.status),
            "Category":        v.category,
            "Source":          METHOD_LABEL.get(v.method, v.method),
            "Confidence":      f"{int(v.confidence * 100)}%",
        })
    return pd.DataFrame(rows)


def vitals_to_json_payload(result: dict) -> dict:
    vitals       = result["vitals"]
    patient_info = result["patient_info"]
    stats        = result["stats"]

    return {
        "patient_info": {
            "patient_name": patient_info.get("Patient Name"),
            "age":          patient_info.get("Age"),
            "gender":       patient_info.get("Gender"),
            "report_date":  patient_info.get("Report Date"),
            "doctor":       patient_info.get("Doctor"),
        },
        "vitals": [
            {
                "name":            v.name,
                "value":           v.value,
                "unit":            v.unit,
                "reference_range": v.reference_range or "",
                "status":          v.status,
                "category":        v.category,
                "method":          v.method,
                "confidence":      round(v.confidence, 4),
            }
            for v in vitals
        ],
        "stats": {
            "total":     stats["total"],
            "by_table":       stats["by_table"],
            "by_regex":       stats["by_regex"],
            "by_qualitative": stats.get("by_qualitative", 0),
            "by_gemini":      stats["by_gemini"],
            "normal":    stats["normal"],
            "abnormal":  stats["abnormal"],
        },
        "pdf_filename": result.get("pdf_filename", ""),
        "pdf_method":   result["pdf_method"],
        "used_gemini":  result["used_gemini"],
    }


def build_summary_md(stats: dict, patient_info: dict,
                     pdf_method: str, used_gemini: bool) -> str:
    name  = patient_info.get("Patient Name", "N/A")
    age   = patient_info.get("Age", "N/A")
    sex   = patient_info.get("Gender", "N/A")
    date  = patient_info.get("Report Date", "N/A")
    doc   = patient_info.get("Doctor", "N/A")
    badge = " · 🤖 Groq used" if used_gemini else ""

    return f"""
### 👤 Patient Info
| Field | Value |
|---|---|
| Name | **{name}** |
| Age | {age} |
| Gender | {sex} |
| Report Date | {date} |
| Doctor | {doc} |

### 📊 Extraction Summary
| Metric | Count |
|---|---|
| ✅ Total Vitals Extracted | **{stats['total']}** |
| 🟢 Normal | {stats['normal']} |
| 🔴 Abnormal | {stats['abnormal']} |
| 📊 From Tables | {stats['by_table']} |
| 🔍 From Regex | {stats['by_regex']} |
| 🔤 From Qualitative | {stats['by_qualitative']} |
| 🤖 From Groq | {stats['by_gemini']} |
| 📄 PDF Reader | `{pdf_method}`{badge} |
"""


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STATE
# ─────────────────────────────────────────────────────────────────────────────

_last_payload: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXTRACTION FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def process_pdf(
    pdf_file,
    gemini_api_key: str,
    force_gemini: bool,
    progress=gr.Progress(track_tqdm=True),
):
    global _last_payload

    if pdf_file is None:
        return (
            None,
            gr.update(value="⚠️ Please upload a PDF file.", visible=True),
            None,
            None,
            gr.update(visible=False),
            gr.update(value="Upload a PDF first.", visible=True),
        )

    pdf_path = pdf_file.name if hasattr(pdf_file, "name") else str(pdf_file)
    pdf_filename = os.path.basename(pdf_path)

    try:
        progress(0.1, desc="Reading PDF…")
        key = gemini_api_key.strip() if gemini_api_key else ""

        extractor = VitalsExtractor(gemini_api_key=key)
        if force_gemini and key:
            extractor.GEMINI_THRESHOLD_COUNT = 9999
            extractor.GEMINI_THRESHOLD_CONF  = 999.0  # bypass confidence check too

        progress(0.35, desc="Extracting text & tables…")
        result = extractor.extract(pdf_path)
        result["pdf_filename"] = pdf_filename

        vitals       = result["vitals"]
        patient_info = result["patient_info"]
        stats        = result["stats"]
        pdf_method   = result["pdf_method"]
        used_gemini  = result["used_gemini"]

        progress(0.55, desc="Building table…")
        df = vitals_to_dataframe(vitals)
        summary_md = build_summary_md(stats, patient_info, pdf_method, used_gemini)

        progress(0.65, desc="Building JSON…")
        payload = vitals_to_json_payload(result)
        _last_payload = payload

        json_tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix="_vitals.json",
            dir=tempfile.gettempdir(), prefix="VitalExtractor_"
        )
        json_tmp.write(json.dumps(payload, indent=2).encode())
        json_tmp.close()
        json_preview = json.dumps(payload, indent=2)

        progress(0.80, desc="Generating PDF report…")
        pdf_tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix="_vital_report.pdf",
            dir=tempfile.gettempdir(), prefix="VitalExtractor_"
        )
        pdf_tmp.close()
        generate_report(
            output_path=pdf_tmp.name,
            vitals=vitals,
            patient_info=patient_info,
            stats=stats,
            used_gemini=used_gemini,
            pdf_method=pdf_method,
        )

        progress(1.0, desc="Done!")

        if len(vitals) == 0:
            warn = "⚠️ No vitals found. Try enabling Gemini for AI-assisted extraction."
        else:
            abnormal = [v for v in vitals if v.status in ("High", "Low")]
            warn = ""
            if abnormal:
                names = ", ".join(v.name for v in abnormal[:5])
                more  = f" and {len(abnormal)-5} more" if len(abnormal) > 5 else ""
                warn = f"⚠️ **Abnormal values detected:** {names}{more}. Please consult a physician."

        return (
            df,
            gr.update(value=summary_md, visible=True),
            pdf_tmp.name,
            json_tmp.name,
            gr.update(value=warn, visible=bool(warn)),
            gr.update(value=json_preview, visible=True),
        )

    except Exception as e:
        logger.error(traceback.format_exc())
        return (
            None,
            gr.update(value=f"❌ Error: {e}", visible=True),
            None, None,
            gr.update(visible=False),
            gr.update(value=f"Error: {e}", visible=True),
        )


# ─────────────────────────────────────────────────────────────────────────────
# SAVE TO BACKEND
# ─────────────────────────────────────────────────────────────────────────────

def save_to_backend(auth_token: str) -> str:
    global _last_payload

    if not _last_payload:
        return "❌ No extraction result found. Extract vitals from a PDF first."

    token = auth_token.strip()
    if not token:
        return "❌ Please enter your JWT auth token."

    url = f"{BACKEND_BASE_URL}/report-vitals/save-extraction"   # ← correct endpoint

    try:
        resp = requests.post(
            url,
            json=_last_payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            timeout=15,
        )
    except requests.exceptions.ConnectionError:
        return (
            f"❌ Could not connect to backend at `{BACKEND_BASE_URL}`.\n"
            "Make sure the FastAPI server is running."
        )
    except requests.exceptions.Timeout:
        return "❌ Request timed out."

    if resp.status_code == 201:
        data = resp.json()
        return (
            f"✅ **Saved successfully!**\n\n"
            f"- Record ID: `{data.get('record_id')}`\n"
            f"- Patient: `{data.get('patient_name') or 'N/A'}`\n"
            f"- {data.get('message', '')}\n"
            f"- Saved at: `{data.get('saved_at', '')}`"
        )
    if resp.status_code == 403:
        detail = resp.json().get("detail", "Access denied.")
        return (
            f"🚫 **Access Denied (403)**\n\n{detail}\n\n"
            "_The patient name on the report must match your account name._"
        )
    if resp.status_code == 401:
        return "🔐 **Unauthorized (401)** — Token is invalid or expired. Please log in again."
    if resp.status_code == 422:
        errors = resp.json().get("detail", [])
        error_text = "\n".join(
            f"- `{'.'.join(str(x) for x in e.get('loc', []))}`: {e.get('msg', '')}"
            for e in errors
        ) if isinstance(errors, list) else str(errors)
        return f"⚠️ **Validation Error (422)**\n\n{error_text}"

    try:
        detail = resp.json().get("detail", resp.text)
    except Exception:
        detail = resp.text
    return f"❌ Backend error ({resp.status_code}): {detail}"


# ─────────────────────────────────────────────────────────────────────────────
# CSS  (passed to launch() in Gradio 6.0)
# ─────────────────────────────────────────────────────────────────────────────

CSS = """
.banner-box {
    background: linear-gradient(135deg, #1A2C4E 0%, #2E5090 100%);
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 16px;
}
.banner-box h1 { color: #FFFFFF; margin: 0 0 6px; font-size: 1.9rem; }
.banner-box p  { color: #A8C4F0; margin: 0; font-size: 0.95rem; }
.warn-banner {
    background: #FFF3CD;
    border-left: 4px solid #F39C12;
    border-radius: 6px;
    padding: 10px 14px;
}
.dataframe thead th {
    background-color: #1A2C4E !important;
    color: white !important;
    font-weight: 600;
}
.upload-area {
    border: 2px dashed #2E5090 !important;
    border-radius: 10px !important;
}
.footer-note { color: #95A5A6; font-size: 0.8rem; text-align: center; padding-top: 12px; }
.json-preview { font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 0.78rem; }
.save-panel {
    border: 1.5px solid #2E5090;
    border-radius: 10px;
    padding: 16px;
    margin-top: 8px;
    background: #F7F9FF;
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# GRADIO UI  — theme/css passed to launch() in Gradio 6.0
# ─────────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="Vital Extractor") as demo:

    gr.HTML("""
    <div class="banner-box">
        <h1>🩺 Vital Extractor</h1>
        <p>Upload a medical report PDF — vitals are extracted via tables, regex, and AI fallback.
        Download a formatted PDF report, export JSON, or push directly to your backend.</p>
    </div>
    """)

    warn_banner = gr.Markdown("", visible=False, elem_classes=["warn-banner"])

    with gr.Row(equal_height=False):

        # ── LEFT COLUMN ────────────────────────────────────────────────────────
        with gr.Column(scale=1, min_width=290):
            gr.Markdown("### 📤 Upload PDF")
            pdf_input = gr.File(
                label="Medical Report PDF",
                file_types=[".pdf"],
                elem_classes=["upload-area"],
            )

            with gr.Accordion("⚙️ AI Fallback (Groq)", open=False):
                gemini_key_input = gr.Textbox(
                    label="Groq API Key",
                    placeholder="gsk_…",
                    type="password",
                    value=_ENV_GEMINI_KEY,
                    info="Auto-loaded from GROQ_API_KEY in .env if set.",
                )
                force_gemini_cb = gr.Checkbox(
                    label="Force Groq on every upload",
                    value=False,
                )

            extract_btn = gr.Button("🔬 Extract Vitals", variant="primary", size="lg")

            gr.HTML('<div class="save-panel">')
            gr.Markdown("### 💾 Save to Backend")
            auth_token_input = gr.Textbox(
                label="Your JWT Auth Token",
                placeholder="eyJhbGciOiJIUzI1NiIs…",
                type="password",
                info="Log in to your app and paste your Bearer token here.",
            )
            save_btn = gr.Button("📤 Save to Database", variant="secondary", size="lg")
            save_status = gr.Markdown("_Extract vitals first, then save._")
            gr.HTML("</div>")

            gr.Markdown("""
<div class="footer-note">

**Extraction chain:**
1. 📊 `pdfplumber` — structured tables
2. 🔍 Regex patterns — 35+ vital types
3. 📷 OCR — scanned PDFs
4. 🤖 Gemini — AI fallback

**Ownership rule:** Your account `name` must match the patient name on the report.
</div>
""")

        # ── RIGHT COLUMN ───────────────────────────────────────────────────────
        with gr.Column(scale=3):

            with gr.Tabs():

                with gr.Tab("📋 Vitals Table"):
                    vitals_table = gr.Dataframe(
                        headers=["Test Name", "Value", "Unit",
                                 "Reference Range", "Status",
                                 "Category", "Source", "Confidence"],
                        datatype=["str"] * 8,
                        interactive=False,
                        wrap=True,
                        label="Extracted Vitals",
                        show_label=False,
                    )

                with gr.Tab("📝 Summary & Patient Info"):
                    summary_md = gr.Markdown(
                        "Upload a PDF and click **Extract Vitals** to see results.",
                    )

                with gr.Tab("📥 PDF Report"):
                    gr.Markdown("### Download Formatted PDF Report")
                    report_file = gr.File(
                        label="Formatted PDF Report",
                        interactive=False,
                    )
                    gr.Markdown("""
The PDF report includes:
- Patient information header
- Color-coded vitals table (🟢 Normal · 🔴 High · 🔵 Low)
- Extraction source (Table / Regex / Gemini)
- Reference ranges for all values
- Timestamp and disclaimer
""")

                with gr.Tab("{ } JSON Export"):
                    gr.Markdown("### Download / Preview JSON")
                    json_file = gr.File(
                        label="Download JSON",
                        interactive=False,
                    )
                    json_preview = gr.Code(
                        label="JSON Preview",
                        language="json",
                        interactive=False,
                        lines=30,
                        elem_classes=["json-preview"],
                    )
                    gr.Markdown("""
This JSON matches the exact schema accepted by:
```
POST /api/report-vitals/save-extraction
```
""")

    with gr.Accordion("ℹ️ How it works & supported vitals", open=False):
        gr.Markdown("""
### Extraction layers (applied in priority order)

| Layer | Tool | Best for |
|---|---|---|
| 1️⃣ Table parser | `pdfplumber` | Structured lab reports with tabular data |
| 2️⃣ Regex engine | Custom patterns | Any readable PDF — 35+ vital types |
| 3️⃣ OCR | `pytesseract` + `pdf2image` | Scanned / image-based PDFs |
| 4️⃣ Gemini fallback | `google-generativeai` | Low-confidence or complex reports |

### Supported vital categories
`Basic Vitals` · `CBC` · `Metabolic Panel` · `Lipid Panel` · `Liver Function` ·
`Thyroid` · `Iron Studies` · `Vitamins` · `Coagulation` · `Inflammation`

### Backend ownership rule
The `patient_name` extracted from the PDF must match your account's `name` in the database.
If they don't match → **403 Forbidden**.
""")

    # ── Wire up ────────────────────────────────────────────────────────────────
    extract_btn.click(
        fn=process_pdf,
        inputs=[pdf_input, gemini_key_input, force_gemini_cb],
        outputs=[vitals_table, summary_md, report_file, json_file, warn_banner, json_preview],
        api_name="extract",
    )

    save_btn.click(
        fn=save_to_backend,
        inputs=[auth_token_input],
        outputs=[save_status],
        api_name="save",
    )


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo.queue(max_size=10).launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        share=False,
        show_error=True,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="indigo",
            neutral_hue="slate",
            font=[gr.themes.GoogleFont("Inter"), "sans-serif"],
        ),
        css=CSS,
    )
