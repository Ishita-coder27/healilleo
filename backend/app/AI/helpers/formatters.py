
import json
import pandas as pd
from typing import List, Dict

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

def build_token_footer_html(stats: dict, token_usage: dict, used_groq: bool) -> str:
    """Renders a token usage footer bar comparing Regex-only vs Groq modes."""
    by_regex = stats.get("by_regex", 0) + stats.get("by_table", 0) + stats.get("by_qualitative", 0)
    by_groq  = stats.get("by_gemini", 0)
    total    = stats.get("total", 0)

    pt  = token_usage.get("prompt_tokens",     0)
    ct  = token_usage.get("completion_tokens", 0)
    tt  = token_usage.get("total_tokens",      0)

    groq_badge = f"""
        <div class="tf-card tf-groq">
            <div class="tf-icon">🤖</div>
            <div class="tf-body">
                <div class="tf-title">Groq LLM <span class="tf-model">llama-3.1-8b-instant</span></div>
                <div class="tf-vitals">+{by_groq} vitals found</div>
                <div class="tf-tokens">
                    <span class="tf-chip tf-prompt">📥 {pt:,} prompt</span>
                    <span class="tf-chip tf-completion">📤 {ct:,} completion</span>
                    <span class="tf-chip tf-total">🔢 {tt:,} total</span>
                </div>
            </div>
        </div>""" if used_groq else """
        <div class="tf-card tf-groq tf-disabled">
            <div class="tf-icon">🤖</div>
            <div class="tf-body">
                <div class="tf-title">Groq LLM <span class="tf-model">not used</span></div>
                <div class="tf-vitals">0 vitals from Groq</div>
                <div class="tf-tokens">
                    <span class="tf-chip tf-zero">0 tokens consumed</span>
                </div>
            </div>
        </div>"""

    return f"""
<div class="token-footer">
    <div class="tf-header">⚡ Extraction Performance</div>
    <div class="tf-cards">
        <div class="tf-card tf-regex">
            <div class="tf-icon">🔍</div>
            <div class="tf-body">
                <div class="tf-title">Regex + Rules <span class="tf-model">no API</span></div>
                <div class="tf-vitals">{by_regex} vitals found</div>
                <div class="tf-tokens">
                    <span class="tf-chip tf-zero">0 tokens — offline</span>
                </div>
            </div>
        </div>
        {groq_badge}
        <div class="tf-card tf-total-card">
            <div class="tf-icon">✅</div>
            <div class="tf-body">
                <div class="tf-title">Combined Result</div>
                <div class="tf-vitals"><strong>{total} vitals</strong> extracted total</div>
                <div class="tf-tokens">
                    <span class="tf-chip tf-total">🔢 {tt:,} tokens used this run</span>
                </div>
            </div>
        </div>
    </div>
</div>
<style>
.token-footer {{
    background: linear-gradient(135deg, #f0f4ff 0%, #f8f0ff 100%);
    border: 1.5px solid #d0d8f0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-top: 16px;
}}
.tf-header {{
    font-weight: 700;
    font-size: 0.95rem;
    color: #2E5090;
    margin-bottom: 12px;
    letter-spacing: 0.3px;
}}
.tf-cards {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}}
.tf-card {{
    flex: 1;
    min-width: 180px;
    border-radius: 10px;
    padding: 12px 14px;
    display: flex;
    gap: 10px;
    align-items: flex-start;
    background: white;
    border: 1.5px solid #e0e8ff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}}
.tf-regex  {{ border-left: 4px solid #27ae60; }}
.tf-groq   {{ border-left: 4px solid #8e44ad; }}
.tf-total-card {{ border-left: 4px solid #2E5090; }}
.tf-disabled {{ opacity: 0.5; }}
.tf-icon {{ font-size: 1.4rem; line-height: 1; }}
.tf-body {{ display: flex; flex-direction: column; gap: 3px; }}
.tf-title {{ font-weight: 600; font-size: 0.82rem; color: #333; }}
.tf-model {{ font-weight: 400; color: #888; font-size: 0.75rem; margin-left: 4px; }}
.tf-vitals {{ font-size: 0.85rem; color: #555; }}
.tf-tokens {{ display: flex; gap: 5px; flex-wrap: wrap; margin-top: 4px; }}
.tf-chip {{
    font-size: 0.72rem;
    padding: 2px 7px;
    border-radius: 20px;
    font-weight: 500;
}}
.tf-prompt     {{ background: #eef2ff; color: #3730a3; }}
.tf-completion {{ background: #fef3ff; color: #7e22ce; }}
.tf-total      {{ background: #eff6ff; color: #1d4ed8; }}
.tf-zero       {{ background: #f0fdf4; color: #166534; }}
</style>
"""


def build_summary_md(stats: dict, patient_info: dict,
                     pdf_method: str, used_gemini: bool,
                     token_usage: dict = None) -> str:
    name  = patient_info.get("Patient Name", "N/A")
    age   = patient_info.get("Age", "N/A")
    sex   = patient_info.get("Gender", "N/A")
    date  = patient_info.get("Report Date", "N/A")
    doc   = patient_info.get("Doctor", "N/A")
    badge = " · 🤖 Groq used" if used_gemini else ""

    token_section = ""
    if used_gemini and token_usage and token_usage.get("total_tokens", 0) > 0:
        pt  = token_usage.get("prompt_tokens", 0)
        ct  = token_usage.get("completion_tokens", 0)
        tt  = token_usage.get("total_tokens", 0)
        token_section = f"""
### 🔢 Groq Token Usage
| Token Type | Count |
|---|---|
| 📥 Prompt Tokens | {pt:,} |
| 📤 Completion Tokens | {ct:,} |
| **🔢 Total Tokens** | **{tt:,}** |

> _llama-3.1-8b-instant · Free tier: 6,000 tokens/min · 500,000 tokens/day_
"""

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
{token_section}"""

