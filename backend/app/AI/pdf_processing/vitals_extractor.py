"""
VitalsExtractor — Multi-layer vital signs extraction engine.

Priority chain:
  1. pdfplumber table extraction  (structured lab reports)
  2. pdfplumber/PyMuPDF text + rich regex patterns  (narrative / mixed PDFs)
  3. pytesseract OCR  (scanned PDFs)
  4. Gemini 1.5 Flash fallback  (when confidence is too low)
"""

from __future__ import annotations

import re
import os
import json
import logging
import pdfplumber
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from .vital_definitions import VITAL_DEFS
from .regex_extractor import RegexExtractor
from .table_extractor import TableExtractor
from .qualitative_extractor import QualitativeExtractor
from .learned_vitals import (
    resolve_vital_name,
    register_vital,
    save_learned_vital,
    load_learned_vitals,
    _ALIAS_TO_CANONICAL,
)
from .groq_extractor import GroqFallback, LLM_PROMPT_TEMPLATE
from .pdf_reader import PDFReader
from .patient_extractor import extract_patient_info
from .models import VitalResult
from .utils import COMPILED_PATTERNS, classify_status, build_regex_for_vital, _looks_like_range_only, _REF_RANGE_PAT

logger = logging.getLogger(__name__)



# ─────────────────────────────────────────────────────────────────────────────
# DEDUPLICATION
# ─────────────────────────────────────────────────────────────────────────────

def deduplicate(results: List[VitalResult]) -> List[VitalResult]:
    seen: Dict[str, VitalResult] = {}
    for r in results:
        key = r.name.lower()
        if key not in seen or r.confidence > seen[key].confidence:
            seen[key] = r
    return list(seen.values())


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

class VitalsExtractor:
    GEMINI_THRESHOLD_COUNT = 3
    GEMINI_THRESHOLD_CONF  = 0.50

    def __init__(self, gemini_api_key: str = ""):
        self.pdf_reader          = PDFReader()
        self.table_extractor     = TableExtractor()
        self.regex_extractor     = RegexExtractor()
        self.qualitative_extractor = QualitativeExtractor()
        self.gemini_key          = gemini_api_key

    def extract(self, pdf_path: str) -> Dict[str, Any]:
        text, tables, pdf_method = self.pdf_reader.read(pdf_path)
        patient_info  = extract_patient_info(text)
        table_results, unmatched_rows = self.table_extractor.extract(tables)
        regex_results = self.regex_extractor.extract(text)
        qual_results  = self.qualitative_extractor.extract(text)
        combined      = deduplicate(table_results + regex_results + qual_results)

        used_gemini  = False
        token_usage  = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if self.gemini_key:
            avg_conf = (sum(r.confidence for r in combined) / len(combined)) if combined else 0

            # Gemini is called if ANY of these are true:
            # 1. Too few vitals extracted (report probably has unknown vitals)
            # 2. Average confidence is low (extraction quality is poor)
            # 3. Table had rows with numeric values that regex/table couldn't identify
            needs_gemini = (
                len(combined) < self.GEMINI_THRESHOLD_COUNT
                or avg_conf < self.GEMINI_THRESHOLD_CONF
                or unmatched_rows > 0          # ← KEY FIX: unknown vitals in table
            )

            if needs_gemini:
                reason = (
                    f"low count ({len(combined)})" if len(combined) < self.GEMINI_THRESHOLD_COUNT
                    else f"low confidence ({avg_conf:.2f})" if avg_conf < self.GEMINI_THRESHOLD_CONF
                    else f"{unmatched_rows} unmatched table row(s)"
                )
                logger.info(f"[Groq] Triggered — reason: {reason}")
                gemini = GroqFallback(self.gemini_key)
                gemini_results = gemini.extract(text)
                if gemini_results:
                    combined = deduplicate(combined + gemini_results)
                    used_gemini = True
                # Accumulate token usage for this call
                _u = gemini.last_usage
                token_usage["prompt_tokens"]     += _u["prompt_tokens"]
                token_usage["completion_tokens"] += _u["completion_tokens"]
                token_usage["total_tokens"]      += _u["total_tokens"]

        category_order = ["cardiovascular", "diabetes_metabolic", "blood_cbc", "liver_hepatic", "kidney_renal", "electrolytes", "thyroid", "nutritional", "respiratory", "hormonal", "general_wellness"]
        combined.sort(key=lambda r: (
            category_order.index(r.category) if r.category in category_order else 99,
            r.name
        ))

        methods = [r.method for r in combined]
        stats = {
            "total":          len(combined),
            "by_table":       methods.count("table"),
            "by_regex":       methods.count("regex"),
            "by_qualitative": methods.count("qualitative"),
            "by_gemini":      methods.count("gemini"),
            "normal":         sum(1 for r in combined if r.status == "Normal"),
            "abnormal":       sum(1 for r in combined if r.status in ("High", "Low", "Critical")),
        }

        return {
            "vitals":       combined,
            "patient_info": patient_info,
            "text_length":  len(text),
            "pdf_method":   pdf_method,
            "used_gemini":  used_gemini,
            "token_usage":  token_usage,
            "stats":        stats,
        }


# ─────────────────────────────────────────────────────────────────────────────
# MODULE STARTUP — load previously learned vitals into regex engine
# ─────────────────────────────────────────────────────────────────────────────
_n = load_learned_vitals()
if _n:
    logger.info(f"[LearnedVitals] {_n} previously learned vital(s) ready in regex engine.")
