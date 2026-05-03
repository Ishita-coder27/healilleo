import os
import re
import json
import logging
from typing import Dict
from .vital_definitions import VITAL_DEFS
from .utils import COMPILED_PATTERNS, build_regex_for_vital, LEARNED_VITALS_PATH

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# SELF-LEARNING REGISTRY
# Vitals discovered by Gemini are saved to learned_vitals.json and immediately
# registered into VITAL_DEFS + COMPILED_PATTERNS so regex handles them next time.
# ─────────────────────────────────────────────────────────────────────────────

# ── Reverse alias lookup: alias_lower → canonical VITAL_DEFS key ─────────────
_ALIAS_TO_CANONICAL: Dict[str, str] = {}

def _rebuild_alias_lookup() -> None:
    _ALIAS_TO_CANONICAL.clear()
    for canonical, defn in VITAL_DEFS.items():
        _ALIAS_TO_CANONICAL[canonical.lower()] = canonical
        for alias in defn.get("aliases", []):
            _ALIAS_TO_CANONICAL[alias.lower()] = canonical

_rebuild_alias_lookup()

# ── Resolve-only aliases ──────────────────────────────────────────────────────
# These map Groq/LLM bare names → canonical VITAL_DEFS keys for name resolution
# and status classification, WITHOUT being added to regex patterns.
# (Bare single-word aliases like "Cholesterol" cause regex to match ratio lines)
_ALIAS_TO_CANONICAL.update({
    "cholesterol":            "Total Cholesterol",
    "triglyceride":           "Triglycerides",
    "platelet count":         "Platelets",
    "fasting blood sugar":    "Glucose",
    "fasting glucose":        "Glucose",
    "random blood sugar":     "Glucose",
    "blood glucose":          "Glucose",
    "t3 - triiodothyronine":  "T3 Total",
    "t4 - thyroxine":         "T4 Total",
    "tsh - thyroid stimulating hormone": "TSH",
    "conjugated bilirubin":   "Direct Bilirubin",
    "unconjugated bilirubin": "Indirect Bilirubin",
    "rdw cv":                 "RDW",
    "direct ldl":             "LDL Cholesterol",
    "chol/hdl ratio":         "Cholesterol:HDL Ratio",
    "ldl/hdl ratio":          "LDL:HDL Ratio",
    "serum creatinine":       "Creatinine",
    "serum uric acid":        "Uric Acid",
    "serum calcium":          "Calcium",
    "serum sodium":           "Sodium",
    "serum potassium":        "Potassium",
    "serum chloride":         "Chloride",
    "sgpt (alt)":             "ALT",
    "sgot (ast)":             "AST",
    "alt (sgpt)":             "ALT",
    "ast (sgot)":             "AST",
})


def resolve_vital_name(raw_name: str) -> str:
    """
    Map a raw LLM-returned name to the canonical VITAL_DEFS key via alias lookup.
    Falls back to raw_name if unknown (triggers self-learning).
    """
    raw_lower = raw_name.strip().lower()

    # 1. Exact alias match
    if raw_lower in _ALIAS_TO_CANONICAL:
        return _ALIAS_TO_CANONICAL[raw_lower]

    # 2. Substring match — find longest alias that fits inside raw_name or vice versa
    best_canonical = None
    best_len = 0
    for alias_lower, canonical in _ALIAS_TO_CANONICAL.items():
        if len(alias_lower) < 4:
            continue
        if alias_lower in raw_lower or raw_lower in alias_lower:
            if len(alias_lower) > best_len:
                best_len = len(alias_lower)
                best_canonical = canonical

    if best_canonical:
        return best_canonical

    return raw_name.strip()


def register_vital(name: str, defn: Dict) -> None:
    """Add a vital to VITAL_DEFS and COMPILED_PATTERNS in memory."""
    if name in VITAL_DEFS:
        return   # already known, skip
    VITAL_DEFS[name] = defn
    COMPILED_PATTERNS[name] = build_regex_for_vital(name, defn)
    # Update alias lookup so resolve_vital_name() catches it immediately
    _ALIAS_TO_CANONICAL[name.lower()] = name
    for alias in defn.get("aliases", []):
        _ALIAS_TO_CANONICAL[alias.lower()] = name
    logger.info(f"[LearnedVitals] Registered new vital in memory: {name!r}")


def save_learned_vital(name: str, defn: Dict) -> None:
    """Persist a newly learned vital to learned_vitals.json."""
    # Load existing
    if os.path.exists(LEARNED_VITALS_PATH):
        try:
            with open(LEARNED_VITALS_PATH, "r", encoding="utf-8") as f:
                learned = json.load(f)
        except Exception:
            learned = {}
    else:
        learned = {}

    if name in learned:
        return   # already saved

    learned[name] = defn
    try:
        with open(LEARNED_VITALS_PATH, "w", encoding="utf-8") as f:
            json.dump(learned, f, indent=2)
        logger.info(f"[LearnedVitals] Saved to disk: {name!r} → {LEARNED_VITALS_PATH}")
    except Exception as e:
        logger.warning(f"[LearnedVitals] Could not save {name!r}: {e}")


def load_learned_vitals() -> int:
    """
    Called once at module load time.
    Reads learned_vitals.json and registers every entry into
    VITAL_DEFS + COMPILED_PATTERNS so regex picks them up immediately.
    Returns the count of vitals loaded.
    """
    if not os.path.exists(LEARNED_VITALS_PATH):
        return 0
    try:
        with open(LEARNED_VITALS_PATH, "r", encoding="utf-8") as f:
            learned = json.load(f)
        for name, defn in learned.items():
            register_vital(name, defn)
        if learned:
            logger.info(f"[LearnedVitals] Loaded {len(learned)} learned vital(s) from disk.")
        return len(learned)
    except Exception as e:
        logger.warning(f"[LearnedVitals] Failed to load learned vitals: {e}")
        return 0








