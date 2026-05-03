# ─────────────────────────────────────────────────────────────────────────────
# REGEX-BASED TEXT EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, List, Tuple
from .vital_definitions import VITAL_DEFS
from .models import VitalResult
from .utils import COMPILED_PATTERNS, classify_status, _looks_like_range_only

class RegexExtractor:
    def extract(self, text: str) -> List[VitalResult]:
        results: List[VitalResult] = []
        seen_vitals: set = set()

        for vital_name, patterns in COMPILED_PATTERNS.items():
            if vital_name in seen_vitals:
                continue
            defn = VITAL_DEFS[vital_name]

            for pattern in patterns:
                if vital_name in seen_vitals:
                    break
                for m in pattern.finditer(text):
                    if _looks_like_range_only(text, m.start(), m.end()):
                        continue

                    groups = m.groups()
                    if not groups:
                        continue

                    if defn["type"] == "bp":
                        if len(groups) >= 2 and groups[0] and groups[1]:
                            sys_v = float(groups[0])
                            dia_v = float(groups[1])
                            if 60 <= sys_v <= 250 and 40 <= dia_v <= 150:
                                value_str = f"{int(sys_v)}/{int(dia_v)}"
                                s_stat = "Normal" if sys_v < 120 else ("High" if sys_v > 140 else "Elevated")
                                d_stat = "Normal" if dia_v < 80 else "High"
                                status = s_stat if s_stat != "Normal" else d_stat
                                results.append(VitalResult(
                                    name=vital_name, value=value_str, unit="mmHg",
                                    category=defn["category"], reference_range="< 120 / < 80",
                                    status=status, confidence=0.85, method="regex",
                                ))
                                seen_vitals.add(vital_name)
                                break

                    elif defn["type"] == "temp":
                        val_str = groups[0]
                        temp_unit = (groups[1] or "F").upper()
                        if val_str:
                            fv = float(val_str)
                            unit_label = "°C" if temp_unit == "C" else "°F"
                            lo, hi = defn.get("normal_C", (36.5, 37.3)) if temp_unit == "C" else defn.get("normal_F", (97.8, 99.1))
                            if (unit_label == "°C" and 30 <= fv <= 45) or (unit_label == "°F" and 86 <= fv <= 113):
                                status = "Normal" if lo <= fv <= hi else ("High" if fv > hi else "Low")
                                results.append(VitalResult(
                                    name=vital_name, value=val_str, unit=unit_label,
                                    category=defn["category"],
                                    reference_range=f"{lo}–{hi} {unit_label}",
                                    status=status, confidence=0.80, method="regex",
                                ))
                                seen_vitals.add(vital_name)
                                break

                    else:
                        val_str = groups[0] if groups[0] else (groups[1] if len(groups) > 1 else None)
                        if val_str:
                            fv = float(val_str)
                            if self._plausible(vital_name, fv):
                                status, ref_range = classify_status(vital_name, fv, defn["unit"])
                                results.append(VitalResult(
                                    name=vital_name, value=val_str, unit=defn["unit"],
                                    category=defn["category"], reference_range=ref_range,
                                    status=status, confidence=0.75, method="regex",
                                ))
                                seen_vitals.add(vital_name)
                                break

        return results

    _PLAUSIBILITY: Dict[str, Tuple[float, float]] = {
        "Heart Rate": (20, 300), "Respiratory Rate": (5, 60), "SpO2": (50, 100),
        "Weight": (1, 500), "Height": (30, 300), "BMI": (5, 80),
        "Hemoglobin": (2, 25), "Hematocrit": (5, 70), "RBC Count": (1.0, 10.0),
        "WBC Count": (0.5, 100.0), "Platelets": (5, 2000),
        "MCV": (50, 130), "MCH": (10, 50), "MCHC": (20, 45),
        "Neutrophils": (0, 100), "Lymphocytes": (0, 100),
        "Monocytes": (0, 30), "Eosinophils": (0, 50),
        "Glucose": (20, 1000), "HbA1c": (3, 20), "BUN": (1, 200),
        "Creatinine": (0.1, 20), "eGFR": (1, 200),
        "Sodium": (100, 200), "Potassium": (1.0, 9.0),
        "Chloride": (70, 130), "Calcium": (4, 15), "Uric Acid": (0.5, 20),
        "Total Cholesterol": (50, 600), "LDL Cholesterol": (10, 400),
        "HDL Cholesterol": (10, 150), "Triglycerides": (20, 2000),
        "VLDL": (2, 100),
        "Cholesterol:HDL Ratio": (0.5, 20), "LDL:HDL Ratio": (0.5, 15),
        "Non-HDL Cholesterol": (20, 500),
        "ALT": (1, 3000), "AST": (1, 3000), "ALP": (10, 2000),
        "GGT": (1, 1000), "Total Bilirubin": (0.1, 30),
        "Direct Bilirubin": (0.0, 20), "Albumin": (1, 7), "Total Protein": (2, 12),
        "TSH": (0.001, 100), "Free T3": (0.5, 20), "Free T4": (0.1, 10),
        "Ferritin": (1, 5000), "Serum Iron": (10, 500),
        "Vitamin B12": (50, 5000), "Vitamin D": (1, 200),
        "PT/INR": (0.5, 10), "aPTT": (10, 200),
        "CRP": (0, 500), "ESR": (0, 200),
    }

    def _plausible(self, vital_name: str, value: float) -> bool:
        bounds = self._PLAUSIBILITY.get(vital_name)
        if not bounds:
            return True
        return bounds[0] <= value <= bounds[1]

