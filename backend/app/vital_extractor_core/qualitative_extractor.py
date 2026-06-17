import re
from typing import List, Tuple, Optional
from .vital_definitions import VITAL_DEFS
from .models import VitalResult

# ─────────────────────────────────────────────────────────────────────────────
# QUALITATIVE EXTRACTOR
# Handles vitals whose values are text (Absent/Present/Positive/Reactive etc.)
# No API needed — pure regex on known value vocabularies
# ─────────────────────────────────────────────────────────────────────────────

# Each entry: (vital_name, [text patterns for name], [accepted text values], confidence)
# Values are matched case-insensitively; the first match wins.
_QUALITATIVE_DEFS = [

    # ── Blood Group ───────────────────────────────────────────────────────────
    ("ABO Type", [
        r"ABO\s+(?:Blood\s+)?(?:Group|Type)",
        r"Blood\s+Group\s+ABO",
        r"Blood\s+Type\s+ABO",
    ], [r"\bA\b", r"\bB\b", r"\bAB\b", r"\bO\b"], 0.92),

    ("Rh Type", [
        r"Rh\s*\(\s*D\s*\)\s*Type",
        r"Rh\s+Factor",
        r"Rh\s+D\s+Type",
        r"Rhesus",
        r"RhD",
    ], [r"Positive", r"Negative"], 0.92),

    # ── Urine Dipstick ────────────────────────────────────────────────────────
    ("Urine Glucose", [
        r"Urine\s+Glucose",
        r"Glucose\s+(?:Urine|\(Urine\))",
        r"Glucosuria",
    ], [r"Absent", r"Present", r"Nil", r"Trace", r"1\+", r"2\+", r"3\+", r"4\+",
        r"\+{1,4}", r"Normal", r"Negative"], 0.90),

    ("Urine Protein", [
        r"Urine\s+Protein",
        r"Protein\s+(?:Urine|\(Urine\))",
        r"Proteinuria",
        r"Albumin\s+(?:Urine|\(Urine\))",
    ], [r"Absent", r"Present", r"Nil", r"Trace", r"1\+", r"2\+", r"3\+", r"4\+",
        r"\+{1,4}", r"Normal", r"Negative"], 0.90),

    ("Urine Bilirubin", [
        r"Bilirubin\s+(?:Urine|\(Urine\))",
        r"Urine\s+Bilirubin",
    ], [r"Absent", r"Present", r"Nil", r"Trace", r"1\+", r"2\+", r"3\+",
        r"\+{1,3}", r"Normal", r"Negative"], 0.90),

    ("Urobilinogen", [
        r"Urobilinogen",
        r"Urine\s+Urobilinogen",
    ], [r"Normal", r"Absent", r"Present", r"1\+", r"2\+", r"3\+",
        r"0\.1\s*(?:mg/dL|EU)", r"0\.2\s*(?:mg/dL|EU)", r"Negative"], 0.88),

    ("Urine Ketone", [
        r"(?:Urine\s+)?Ketones?(?:\s+Urine)?",
        r"Ketonuria",
    ], [r"Absent", r"Present", r"Nil", r"Trace", r"1\+", r"2\+", r"3\+",
        r"\+{1,3}", r"Normal", r"Negative"], 0.90),

    ("Urine Nitrite", [
        r"Nitrite(?:\s+Urine)?",
        r"Urine\s+Nitrite",
    ], [r"Absent", r"Present", r"Positive", r"Negative", r"Normal"], 0.88),

    # ── Urine Microscopy ──────────────────────────────────────────────────────
    ("Casts", [
        r"(?:Urine\s+)?Casts?(?:\s+Urine)?",
        r"Hyaline\s+Casts?",
        r"Urinary\s+Casts?",
    ], [r"Absent", r"Nil", r"None", r"Not\s+Seen", r"Present",
        r"\d+[-–]\d+\s*/\s*(?:lpf|hpf)",
        r"Occasional", r"Rare", r"Few", r"Moderate", r"Many"], 0.85),

    ("Crystals", [
        r"(?:Urine\s+)?Crystals?(?:\s+Urine)?",
        r"Urinary\s+Crystals?",
    ], [r"Absent", r"Nil", r"None", r"Not\s+Seen", r"Present",
        r"Occasional", r"Rare", r"Few", r"Moderate", r"Many",
        r"Oxalate", r"Urate", r"Phosphate"], 0.85),

    # ── Serology / Infection ──────────────────────────────────────────────────
    ("HIV Ag/Ab", [
        r"HIV\s+I\s*(?:&|and|/)\s*II",
        r"HIV\s+Ag\s*/\s*Ab",
        r"Anti\s+HIV",
        r"HIV\s+Antibody",
        r"HIV\s+1\s*(?:&|and|/)\s*2",
    ], [r"Reactive", r"Non[\s-]?Reactive", r"Positive", r"Negative",
        r"Detected", r"Not\s+Detected"], 0.92),

    ("HBsAg", [
        r"HBs\s*Ag",
        r"Hepatitis\s+B\s+Surface\s+Antigen",
        r"HBs\s+Antigen",
    ], [r"Reactive", r"Non[\s-]?Reactive", r"Positive", r"Negative",
        r"Detected", r"Not\s+Detected"], 0.92),

    # ── RBC Morphology (common in CBC reports) ────────────────────────────────
    ("RBC Morphology", [
        r"RBC\s+Morphology",
        r"Red\s+(?:Blood\s+)?Cell\s+Morphology",
        r"Erythrocyte\s+Morphology",
    ], [r"Normochromic\s+Normocytic",
        r"Normochromic",
        r"Normocytic",
        r"Microcytic",
        r"Macrocytic",
        r"Hypochromic",
        r"Normal"], 0.88),

    # ── Urine Appearance ──────────────────────────────────────────────────────
    ("Urine Colour", [
        r"(?:Urine\s+)?Colou?r(?:\s+Urine)?",
        r"Urine\s+Appearance",
        r"Colour\s+of\s+Urine",
    ], [r"Pale\s+Yellow", r"Yellow", r"Dark\s+Yellow", r"Amber",
        r"Colourless", r"Colorless", r"Straw", r"Clear"], 0.80),

    ("Urine Turbidity", [
        r"(?:Urine\s+)?Turbidity",
        r"(?:Urine\s+)?Clarity",
        r"Appearance",
    ], [r"Clear", r"Slightly\s+Turbid", r"Turbid", r"Hazy",
        r"Cloudy", r"Transparent"], 0.80),
]


class QualitativeExtractor:
    """
    Extracts vitals whose values are text (Absent/Present/Positive/Reactive etc.)
    Runs after numeric RegexExtractor and before Groq, adding coverage for
    blood group, urine dipstick, serology, and morphology results.
    """

    def __init__(self):
        # Pre-compile all patterns
        self._compiled: List[Tuple] = []
        for vital_name, name_pats, val_pats, conf in _QUALITATIVE_DEFS:
            name_re = [re.compile(p, re.IGNORECASE) for p in name_pats]
            val_re  = [re.compile(p, re.IGNORECASE) for p in val_pats]
            self._compiled.append((vital_name, name_re, val_re, conf))

    def extract(self, text: str) -> List[VitalResult]:
        results: List[VitalResult] = []
        lines = text.splitlines()

        for vital_name, name_res, val_res, conf in self._compiled:
            value = self._find_value(lines, name_res, val_res)
            if value is None:
                continue

            defn    = VITAL_DEFS.get(vital_name, {})
            unit    = defn.get("unit", "")
            cat     = defn.get("category", "Other")

            results.append(VitalResult(
                name=vital_name,
                value=value,
                unit=unit,
                reference_range="",
                status="info",      # qualitative — no numeric normal range
                confidence=conf,
                method="qualitative",
                category=cat,
            ))

        return results

    def _find_value(self, lines: List[str], name_res, val_res) -> Optional[str]:
        """
        Scan each line; if a name pattern matches, look for a value pattern
        on the same line or the next 2 lines.
        """
        for i, line in enumerate(lines):
            # Check if any name pattern matches this line
            name_hit = any(nr.search(line) for nr in name_res)
            if not name_hit:
                continue

            # Search window: same line + next 2 lines
            window = " ".join(lines[i : i + 3])

            for vr in val_res:
                m = vr.search(window)
                if m:
                    return m.group(0).strip()

        return None
