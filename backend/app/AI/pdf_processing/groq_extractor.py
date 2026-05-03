import re
import json
import logging
from typing import List, Dict
from .vital_definitions import VITAL_DEFS
from .utils import classify_status
from .models import VitalResult
from .learned_vitals import resolve_vital_name, register_vital, save_learned_vital

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# GROQ FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

LLM_PROMPT_TEMPLATE = """You are a medical data extraction assistant. Extract ALL vital signs and lab values from the following medical report text.

Return ONLY a valid JSON array. Each element must be an object with these exact keys:
  "name"            : canonical vital/test name (string)
  "value"           : extracted numeric value (string)
  "unit"            : measurement unit (string)
  "reference_range" : reference range as given in the document (string, empty if not found)
  "status"          : "Normal", "High", "Low", or "Unknown"
  "category"        : one of: "cardiovascular", "diabetes_metabolic", "blood_cbc", "liver_hepatic", "kidney_renal", "electrolytes", "thyroid", "nutritional", "respiratory", "hormonal", "general_wellness"

Do NOT include any explanation or markdown. Only the JSON array.

Medical report text:
\"\"\"
{text}
\"\"\"
"""


class GroqFallback:
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key
        self.model = model
        self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def extract(self, text: str) -> List[VitalResult]:
        safe_text = text[:5500].encode("ascii", errors="ignore").decode("ascii")
        logger.info(f"[Groq] Text length being sent: {len(safe_text)} chars")

        from groq import Groq
        import json

        # Sanitize API key — strip any non-ASCII chars (e.g. accidentally pasted emoji)
        clean_key = self.api_key.encode("ascii", errors="ignore").decode("ascii").strip()
        if not clean_key:
            raise RuntimeError("Groq API key is empty or contains only non-ASCII characters. Please paste a valid gsk_... key.")
        client = Groq(api_key=clean_key)
        # Sanitize text — strip non-ASCII chars that Groq/LLM APIs reject
        safe_text = text[:5500].encode("ascii", errors="ignore").decode("ascii")
        prompt = LLM_PROMPT_TEMPLATE.format(text=safe_text)
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,   # low temp for consistent structured output
                max_tokens=4096,
            )
            raw = response.choices[0].message.content.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"```\s*$", "", raw).strip()
            items = json.loads(raw)
        except Exception as e:
            logger.error(f"Groq extraction failed: {e}")
            raise RuntimeError(f"Groq API error: {e}") from e

        # Capture token usage from Groq response
        usage = response.usage
        self.last_usage = {
            "prompt_tokens":     usage.prompt_tokens     if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens":      usage.total_tokens      if usage else 0,
        }

        results: List[VitalResult] = []
        for item in items:
            if not isinstance(item, dict):
                continue

            raw_vital_name = item.get("name", "Unknown").strip()
            vital_name     = resolve_vital_name(raw_vital_name)   # map to canonical key
            unit           = item.get("unit", "").strip()
            category       = item.get("category", "Other").strip()

            try:
                fv = float(str(item.get("value", "")).replace(",", "."))
                status, ref = classify_status(vital_name, fv)
                if not status or status == "Unknown":
                    status = item.get("status", "Unknown")
                if not ref:
                    ref = item.get("reference_range", "")
            except (ValueError, TypeError):
                fv     = None
                status = item.get("status", "Unknown")
                ref    = item.get("reference_range", "")

            # ── SELF-LEARNING: if Gemini found a vital we don't know, learn it ──
            if vital_name and vital_name not in VITAL_DEFS:
                # Build a minimal definition using what Gemini told us
                # Try to parse a numeric normal range from the reference_range string
                learned_normal = None
                if ref:
                    range_m = re.search(
                        r"(\d{1,5}(?:\.\d{1,3})?)\s*[-–—]\s*(\d{1,5}(?:\.\d{1,3})?)",
                        ref
                    )
                    if range_m:
                        try:
                            learned_normal = (float(range_m.group(1)), float(range_m.group(2)))
                        except ValueError:
                            pass

                # ── Build rich aliases from the vital name automatically ──────────
                # e.g. "T3 - Triiodothyronine" → ["T3 - Triiodothyronine", "T3", "Triiodothyronine"]
                # e.g. "Fasting Blood Sugar"    → ["Fasting Blood Sugar", "FBS"]
                aliases = [vital_name]

                # Split on " - ", " / ", comma to get sub-parts as aliases
                import re as _re
                parts = _re.split(r"\s*[-–/,]\s*", vital_name)
                for p in parts:
                    p = p.strip()
                    if len(p) >= 3 and p not in aliases:
                        aliases.append(p)

                # Add common abbreviations for well-known patterns
                _ABBREV = {
                    "Fasting Blood Sugar":           "FBS",
                    "Random Blood Sugar":            "RBS",
                    "Blood Urea Nitrogen":           "BUN",
                    "Thyroid Stimulating Hormone":   "TSH",
                    "Triiodothyronine":              "T3",
                    "Thyroxine":                     "T4",
                    "Platelet Count":                "PLT",
                    "White Blood Cell":              "WBC",
                    "Red Blood Cell":                "RBC",
                    "Mean Corpuscular Volume":       "MCV",
                    "Mean Corpuscular Hemoglobin":   "MCH",
                    "Erythrocyte Sedimentation Rate":"ESR",
                    "C-Reactive Protein":            "CRP",
                    "Alanine Aminotransferase":      "ALT",
                    "Aspartate Aminotransferase":    "AST",
                    "Alkaline Phosphatase":          "ALP",
                    "Total Iron Binding Capacity":   "TIBC",
                    "Prostate Specific Antigen":     "PSA",
                }
                for full, abbr in _ABBREV.items():
                    if full.lower() in vital_name.lower() and abbr not in aliases:
                        aliases.append(abbr)

                # Determine type — qualitative if no numeric value was found
                vital_type = "numeric" if fv is not None else "qualitative"

                new_defn: Dict = {
                    "aliases":  aliases,
                    "unit":     unit or "?",
                    "category": category,
                    "type":     vital_type,
                }
                if learned_normal and vital_type == "numeric":
                    new_defn["normal"] = learned_normal

                # Register in memory → regex works for rest of this session
                register_vital(vital_name, new_defn)
                # Persist to disk → regex works from next run onward
                save_learned_vital(vital_name, new_defn)

            results.append(VitalResult(
                name=vital_name,
                value=str(item.get("value", "")),
                unit=unit,
                category=category,
                reference_range=ref,
                status=status,
                confidence=0.88,
                method="gemini",
            ))
        return results
