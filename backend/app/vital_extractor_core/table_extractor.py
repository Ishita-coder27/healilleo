import re
from typing import List, Tuple, Optional
from .vital_definitions import VITAL_DEFS

from .utils import classify_status, normalize_label, _SKIP_ROW_RE
from .models import VitalResult

# ─────────────────────────────────────────────────────────────────────────────
# TABLE-BASED EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────




class TableExtractor:
    MIN_COLS = 2

    def extract(self, tables: List[List]) -> Tuple[List[VitalResult], int]:
        """
        Returns (results, unmatched_count).
        unmatched_count = rows that had a numeric value but no VITAL_DEFS match.
        A non-zero unmatched_count signals Gemini should be called.
        """
        results: List[VitalResult] = []
        unmatched_count = 0
        for table in tables:
            if not table:
                continue
            for row in table:
                if not row or len(row) < self.MIN_COLS:
                    continue
                result, was_unmatched = self._parse_row(row)
                if result:
                    results.append(result)
                elif was_unmatched:
                    unmatched_count += 1
        return results, unmatched_count

    def _parse_row(self, row: List) -> Tuple[Optional[VitalResult], bool]:
        """
        Returns (VitalResult | None, was_unmatched).
        was_unmatched=True means: row had a numeric value but vital name unknown.
        """
        cells = [str(c).strip() if c else "" for c in row]
        if not cells[0]:
            return None, False

        test_name_raw = cells[0]

        # Skip header rows and risk/reference table rows
        if _SKIP_ROW_RE.search(test_name_raw):
            return None, False

        value_cell = cells[1] if len(cells) > 1 else ""
        unit_cell  = cells[2] if len(cells) > 2 else ""
        ref_cell   = cells[3] if len(cells) > 3 else ""

        matched_vital = self._match_vital_name(test_name_raw)
        if not matched_vital:
            # Check if this row actually has a numeric value — if so, it is a
            # real unmatched vital (not a blank/header/section row)
            has_number = bool(re.search(r"\d", value_cell))
            return None, has_number

        num_match = re.search(r"(\d{1,5}(?:\.\d{1,3})?)", value_cell)
        if not num_match:
            return None
        value_str = num_match.group(1)

        unit = unit_cell.strip() or VITAL_DEFS[matched_vital]["unit"]
        # FIX: guard against garbage multi-line unit cells
        unit = unit.split("\n")[0].strip()

        try:
            fv = float(value_str)
            status, ref_range = classify_status(matched_vital, fv, unit)
        except ValueError:
            status, ref_range = "Unknown", ""

        # Use ref_cell from the report if it's clean (single line, not too long)
        if ref_cell:
            first_line = ref_cell.split("\n")[0].strip()
            if first_line:
                ref_range = first_line

        return VitalResult(
            name=matched_vital,
            value=value_str,
            unit=unit,
            category=VITAL_DEFS[matched_vital]["category"],
            reference_range=ref_range,
            status=status,
            confidence=0.92,
            method="table",
        ), False

    def _match_vital_name(self, raw: str) -> Optional[str]:
        raw_lower = raw.lower().strip()
        raw_normalized = normalize_label(raw)

        # FIX: skip rows that are from risk tables or headers
        if _SKIP_ROW_RE.search(raw_lower):
            return None

        best_vital = None
        best_score = 0

        for vital_name, defn in VITAL_DEFS.items():
            for alias in defn["aliases"]:
                alias_lower = alias.lower()
                alias_normalized = normalize_label(alias)
                # FIX: skip aliases shorter than 4 chars in table matching
                # Prevents "Ca" matching inside "category", "TC" inside "TATA", etc.
                if len(alias_lower) < 4:
                    continue
                # Exact match (highest priority)
                if alias_lower == raw_lower or (alias_normalized and alias_normalized == raw_normalized):
                    return vital_name
                # Word-boundary substring match
                if re.search(r'\b' + re.escape(alias_lower) + r'\b', raw_lower):
                    score = len(alias_lower)
                    if score > best_score:
                        best_score = score
                        best_vital = vital_name
                elif alias_normalized and re.search(r'(?<![a-z0-9])' + re.escape(alias_normalized) + r'(?![a-z0-9])', raw_normalized):
                    score = len(alias_normalized)
                    if score > best_score:
                        best_score = score
                        best_vital = vital_name

        return best_vital if best_score >= 4 else None
