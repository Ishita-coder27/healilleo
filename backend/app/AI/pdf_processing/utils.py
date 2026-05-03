import os
import re
from typing import Dict, List, Tuple
from .vital_definitions import VITAL_DEFS

# ─────────────────────────────────────────────────────────────────────────────
# REGEX PATTERN BUILDER
# ─────────────────────────────────────────────────────────────────────────────

_ALIAS_TOKEN_RE = re.compile(r"[A-Za-z0-9+%]+")
_ALIAS_SEP_RE = r"[\s._:/,\-()]*"


def normalize_label(text: str) -> str:
    return " ".join(_ALIAS_TOKEN_RE.findall(text.lower()))


def _alias_to_regex(alias: str) -> str:
    tokens = _ALIAS_TOKEN_RE.findall(alias)
    if not tokens:
        return r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])"
    return (
        r"(?<![A-Za-z0-9])"
        + _ALIAS_SEP_RE.join(re.escape(tok) for tok in tokens)
        + r"(?![A-Za-z0-9])"
    )


def _alias_pattern(aliases: List[str]) -> str:
    flexible = sorted((_alias_to_regex(alias) for alias in aliases), key=len, reverse=True)
    return "(?:" + "|".join(flexible) + ")"


_NUM = r"(\d{1,6}(?:\.\d{1,3})?)"  # 6 digits covers Platelet Count (150000), WBC (10570)
_NUM_NC = r"\d{1,6}(?:\.\d{1,3})?"
_SEP = r"[\s:=\-\–\—]?\s*"
_UNIT_OPT = r"(?:\s*[\w/µ%°\.]+)?"


def build_regex_for_vital(vital_name: str, defn: Dict) -> List[re.Pattern]:
    patterns = []
    alias_pat = _alias_pattern(defn["aliases"])

    if defn["type"] == "bp":
        patterns.append(re.compile(
            alias_pat + r"[\s:=\-\–]?\s*" + _NUM + r"\s*/\s*" + _NUM + r"(?:\s*(?:mmHg|mm\s*Hg))?",
            re.IGNORECASE
        ))
        patterns.append(re.compile(
            r"\b(\d{2,3})\s*/\s*(\d{2,3})\s*(?:mmHg|mm\s*Hg)",
            re.IGNORECASE
        ))
    elif defn["type"] == "temp":
        patterns.append(re.compile(
            alias_pat + _SEP + _NUM + r"\s*(?:°?\s*([FCfc]))?",
            re.IGNORECASE
        ))
    else:
        patterns.append(re.compile(
            alias_pat + _SEP + _NUM + _UNIT_OPT,
            re.IGNORECASE
        ))
        patterns.append(re.compile(
            alias_pat + r"[^\n\d]{0,40}" + _NUM + _UNIT_OPT,
            re.IGNORECASE
        ))
        patterns.append(re.compile(
            r"\b" + _NUM + r"[^\S\n]+" + alias_pat,
            re.IGNORECASE
        ))

    return patterns


COMPILED_PATTERNS: Dict[str, List[re.Pattern]] = {
    name: build_regex_for_vital(name, defn)
    for name, defn in VITAL_DEFS.items()
}

# ─────────────────────────────────────────────────────────────────────────────
# STATUS CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────────

def classify_status(vital_name: str, value: float, unit: str = "") -> Tuple[str, str]:
    defn = VITAL_DEFS.get(vital_name)
    # If direct lookup fails, try resolving via alias→canonical map
    if not defn:
        canonical = _ALIAS_TO_CANONICAL.get(vital_name.lower())
        if canonical:
            defn = VITAL_DEFS.get(canonical)
    if not defn:
        return "Unknown", ""

    def _check(v, lo, hi):
        if v < lo: return "Low"
        if v > hi: return "High"
        return "Normal"

    def _fmt(lo, hi):
        if hi >= 999: return f"> {lo}"
        return f"{lo} – {hi}"

    t = defn.get("type", "numeric")

    if t == "bp":
        return "Normal", "< 120 / < 80"
    if t == "temp":
        lo, hi = defn.get("normal_F", (97.8, 99.1))
        return _check(value, lo, hi), f"{lo}–{hi} °F"

    for key in ("normal", "normal_male", "normal_fasting"):
        r = defn.get(key)
        if r:
            lo, hi = r
            return _check(value, lo, hi), _fmt(lo, hi)

    return "Unknown", ""

def _looks_like_range_only(text: str, match_start: int, match_end: int) -> bool:
    surrounding = text[max(0, match_start - 30): match_end + 30]
    return len(list(_REF_RANGE_PAT.finditer(surrounding))) >= 2

# FIX: Rows whose test_name matches these patterns are reference/risk table rows — skip them
_SKIP_ROW_RE = re.compile(
    r"risk\s*group|treatment\s*target|primary\s*target|secondary\s*target"
    r"|extreme.{0,5}risk|very\s*high.{0,5}risk|moderate.{0,5}risk"
    r"|category\s*[abc]\b|apo.?b|ascvd|test\s*name|bio\.?\s*ref",
    re.IGNORECASE
)

# ─────────────────────────────────────────────────────────────────────────────
# LEARNED VITALS — path to persistent JSON file (same folder as this script)
# ─────────────────────────────────────────────────────────────────────────────
LEARNED_VITALS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "learned_vitals.json"
)

# ─────────────────────────────────────────────────────────────────────────────
# REFERENCE-RANGE PARSER
# ─────────────────────────────────────────────────────────────────────────────

_REF_RANGE_PAT = re.compile(
    r"\b(\d{1,5}(?:\.\d{1,3})?)\s*[-–—]\s*(\d{1,5}(?:\.\d{1,3})?)\b"
)
