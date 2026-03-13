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
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

import pdfplumber

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# LEARNED VITALS — path to persistent JSON file (same folder as this script)
# ─────────────────────────────────────────────────────────────────────────────
LEARNED_VITALS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "learned_vitals.json"
)

# ─────────────────────────────────────────────────────────────────────────────
# DATA MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VitalResult:
    name: str
    value: str
    unit: str
    category: str
    reference_range: str = ""
    status: str = "Unknown"
    confidence: float = 0.0
    method: str = "regex"
    note: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# VITAL SIGN DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

VITAL_DEFS: Dict[str, Dict] = {

    # ── Basic Vitals ──────────────────────────────────────────────────────────
    "Blood Pressure": {
        "aliases": ["BP", "Blood Pressure", "B.P", "Systolic/Diastolic", "SBP/DBP"],
        "unit": "mmHg", "category": "Basic Vitals",
        "normal": {"systolic": (90, 120), "diastolic": (60, 80)},
        "type": "bp",
    },
    "Heart Rate": {
        "aliases": ["HR", "Heart Rate", "Pulse", "P.R", "PR", "Pulse Rate"],
        "unit": "bpm", "category": "Basic Vitals",
        "normal": (60, 100), "type": "numeric",
    },
    "Temperature": {
        "aliases": ["Temp", "Temperature", "Body Temp"],
        "unit": "°F", "category": "Basic Vitals",
        "normal_F": (97.8, 99.1), "normal_C": (36.5, 37.3), "type": "temp",
    },
    "Respiratory Rate": {
        "aliases": ["RR", "Resp Rate", "Respiratory Rate", "Respirations"],
        "unit": "breaths/min", "category": "Basic Vitals",
        "normal": (12, 20), "type": "numeric",
    },
    "SpO2": {
        "aliases": ["SpO2", "O2 Sat", "Oxygen Saturation", "Spo2", "SaO2"],
        "unit": "%", "category": "Basic Vitals",
        "normal": (95, 100), "type": "numeric",
    },
    "Weight": {
        "aliases": ["Weight", "Body Weight"],
        "unit": "kg", "category": "Basic Vitals",
        "normal": None, "type": "numeric",
    },
    "Height": {
        "aliases": ["Height", "Body Height"],
        "unit": "cm", "category": "Basic Vitals",
        "normal": None, "type": "numeric",
    },
    "BMI": {
        "aliases": ["BMI", "Body Mass Index"],
        "unit": "kg/m²", "category": "Basic Vitals",
        "normal": (18.5, 24.9), "type": "numeric",
    },

    # ── CBC ───────────────────────────────────────────────────────────────────
    "Hemoglobin": {
        "aliases": ["Hb", "Hemoglobin", "HGB", "Haemoglobin"],
        "unit": "g/dL", "category": "CBC",
        "normal_male": (13.0, 16.5), "normal_female": (12.0, 15.5), "type": "numeric",
    },
    "RBC Count": {
        "aliases": ["RBC", "RBC Count", "Red Blood Cells", "Red Cell Count",
                    "Erythrocytes", "Red Blood Cell Count"],
        "unit": "million/cmm", "category": "CBC",
        "normal_male": (4.5, 5.5), "normal_female": (4.1, 5.1), "type": "numeric",
    },
    "Hematocrit": {
        "aliases": ["HCT", "Hematocrit", "Haematocrit", "PCV", "Packed Cell Volume"],
        "unit": "%", "category": "CBC",
        "normal_male": (40.0, 49.0), "normal_female": (36.0, 46.0), "type": "numeric",
    },
    "MCV": {
        "aliases": ["MCV", "Mean Corpuscular Volume"],
        "unit": "fL", "category": "CBC",
        "normal": (83, 101), "type": "numeric",
    },
    "MCH": {
        "aliases": ["MCH", "Mean Corpuscular Hemoglobin"],
        "unit": "pg", "category": "CBC",
        "normal": (27.1, 32.5), "type": "numeric",
    },
    "MCHC": {
        "aliases": ["MCHC", "Mean Corpuscular Hemoglobin Concentration"],
        "unit": "g/dL", "category": "CBC",
        "normal": (32.5, 36.7), "type": "numeric",
    },
    # NEW: Red Cell Distribution Width
    "RDW": {
        "aliases": ["RDW", "RDW CV", "RDW-CV", "Red Cell Distribution Width",
                    "RBC Distribution Width"],
        "unit": "%", "category": "CBC",
        "normal": (11.6, 14.0), "type": "numeric",
    },
    "WBC Count": {
        "aliases": ["WBC", "WBC Count", "White Blood Cells", "White Cell Count",
                    "Leukocytes", "TLC", "Total WBC"],
        "unit": "/cmm", "category": "CBC",
        "normal": (4000, 10000), "type": "numeric",
    },
    "Neutrophils": {
        "aliases": ["Neutrophils", "NEUT", "Segs", "PMN"],
        "unit": "%", "category": "CBC",
        "normal": (40, 80), "type": "numeric",
    },
    "Lymphocytes": {
        "aliases": ["Lymphocytes", "LYMPH", "LYM"],
        "unit": "%", "category": "CBC",
        "normal": (20, 40), "type": "numeric",
    },
    "Monocytes": {
        "aliases": ["Monocytes", "MONO"],
        "unit": "%", "category": "CBC",
        "normal": (2, 10), "type": "numeric",
    },
    "Eosinophils": {
        "aliases": ["Eosinophils", "EOS"],
        "unit": "%", "category": "CBC",
        "normal": (1, 6), "type": "numeric",
    },
    # NEW: Basophils
    "Basophils": {
        "aliases": ["Basophils", "BASO", "Basophil"],
        "unit": "%", "category": "CBC",
        "normal": (0, 2), "type": "numeric",
    },
    "Platelets": {
        "aliases": ["PLT", "Platelets", "Thrombocytes", "Platelet Count",
                    "Platelet Count Electrical"],
        "unit": "/cmm", "category": "CBC",
        "normal": (150000, 410000), "type": "numeric",
    },
    # NEW: Mean Platelet Volume
    "MPV": {
        "aliases": ["MPV", "Mean Platelet Volume"],
        "unit": "fL", "category": "CBC",
        "normal": (7.5, 10.3), "type": "numeric",
    },
    # NEW: HB Electrophoresis components
    "Hb A": {
        "aliases": ["Hb A", "HbA", "Hemoglobin A", "Haemoglobin A"],
        "unit": "%", "category": "CBC",
        "normal": (96.8, 97.8), "type": "numeric",
    },
    "Hb A2": {
        "aliases": ["Hb A2", "HbA2", "Hemoglobin A2", "Haemoglobin A2"],
        "unit": "%", "category": "CBC",
        "normal": (2.2, 3.2), "type": "numeric",
    },
    "Fetal Hemoglobin": {
        "aliases": ["Foetal Hb", "Fetal Hb", "HbF", "Fetal Hemoglobin",
                    "Foetal Hemoglobin", "Hemoglobin F"],
        "unit": "%", "category": "CBC",
        "normal": (0.0, 1.0), "type": "numeric",
    },

    # ── Metabolic Panel ───────────────────────────────────────────────────────
    "Glucose": {
        "aliases": ["Glucose", "Blood Glucose", "FBS", "Fasting Glucose", "RBS",
                    "Blood Sugar", "Fasting Blood Sugar", "Random Blood Sugar",
                    "Fasting Blood Sugar GOD"],
        "unit": "mg/dL", "category": "Metabolic Panel",
        "normal_fasting": (74, 106), "normal": (70, 140), "type": "numeric",
    },
    "HbA1c": {
        "aliases": ["HbA1c", "Hemoglobin A1c", "Glycated Hemoglobin", "A1C", "Hba1c",
                    "HbA1c Glycosylated Hemoglobin"],
        "unit": "%", "category": "Metabolic Panel",
        "normal": (4.0, 5.6), "type": "numeric",
    },
    # NEW: Mean Blood Glucose (derived from HbA1c)
    "Mean Blood Glucose": {
        "aliases": ["Mean Blood Glucose", "eAG", "Estimated Average Glucose",
                    "Average Blood Glucose"],
        "unit": "mg/dL", "category": "Metabolic Panel",
        "normal": (70, 154), "type": "numeric",
    },
    "BUN": {
        "aliases": ["BUN", "Blood Urea Nitrogen", "Urea Nitrogen"],
        "unit": "mg/dL", "category": "Metabolic Panel",
        "normal": (9.0, 20.0), "type": "numeric",
    },
    # NEW: Serum Urea (separate from BUN — Sterling reports both)
    "Urea": {
        "aliases": ["Urea", "Serum Urea", "Blood Urea", "Urea Serum"],
        "unit": "mg/dL", "category": "Metabolic Panel",
        "normal": (19.3, 43.0), "type": "numeric",
    },
    "Creatinine": {
        "aliases": ["Creatinine", "Creat", "Serum Creatinine", "Creatinine Serum",
                    "Creatinine, Serum"],
        "unit": "mg/dL", "category": "Metabolic Panel",
        "normal_male": (0.66, 1.25), "normal_female": (0.59, 1.04), "type": "numeric",
    },
    "eGFR": {
        "aliases": ["eGFR", "GFR", "Estimated GFR", "Glomerular Filtration Rate"],
        "unit": "mL/min/1.73m²", "category": "Metabolic Panel",
        "normal": (90, 999), "type": "numeric",
    },
    "Sodium": {
        "aliases": ["Sodium", "Serum Sodium", "Sodium (Na+)", "Na+", "Na"],
        "unit": "mmol/L", "category": "Metabolic Panel",
        "normal": (136, 145), "type": "numeric",
    },
    "Potassium": {
        "aliases": ["Potassium", "Serum Potassium", "Potassium (K+)", "K+", "K"],
        "unit": "mmol/L", "category": "Metabolic Panel",
        "normal": (3.5, 5.1), "type": "numeric",
    },
    "Chloride": {
        "aliases": ["Chloride", "Serum Chloride", "Chloride (Cl-)", "Cl-"],
        "unit": "mmol/L", "category": "Metabolic Panel",
        "normal": (98, 107), "type": "numeric",
    },
    "Calcium": {
        # Short alias "Ca" removed — prevents false match against "category" in risk tables
        "aliases": ["Calcium", "Total Calcium", "Serum Calcium"],
        "unit": "mg/dL", "category": "Metabolic Panel",
        "normal": (8.4, 10.2), "type": "numeric",
    },
    "Uric Acid": {
        "aliases": ["Uric Acid", "Urate", "Serum Urate"],
        "unit": "mg/dL", "category": "Metabolic Panel",
        "normal_male": (3.5, 8.5), "normal_female": (2.6, 6.0), "type": "numeric",
    },
    # NEW: Urine Microalbumin
    "Microalbumin": {
        "aliases": ["Microalbumin", "Microalbumin Urine", "Microalbumin (per urine volume)",
                    "Urine Microalbumin", "Urinary Albumin"],
        "unit": "mg/L", "category": "Metabolic Panel",
        "normal": (0, 16.7), "type": "numeric",
    },

    # ── Lipid Panel ───────────────────────────────────────────────────────────
    "Total Cholesterol": {
        "aliases": ["Cholesterol - Total", "Cholesterol, Total", "Total Cholesterol",
                    "Serum Cholesterol", "Chol"],
        # NOTE: bare "Cholesterol" removed — matches "Cholesterol:HDL Ratio" lines causing value=3.4
        "unit": "mg/dL", "category": "Lipid Panel",
        "normal": (0, 200), "type": "numeric",
    },
    "LDL Cholesterol": {
        "aliases": ["Cholesterol - LDL", "LDL-C", "LDL Cholesterol",
                    "Low Density Lipoprotein", "Direct LDL", "LDL"],
        "unit": "mg/dL", "category": "Lipid Panel",
        "normal": (0, 100), "type": "numeric",
    },
    "HDL Cholesterol": {
        "aliases": ["Cholesterol - HDL", "HDL-C", "HDL Cholesterol",
                    "High Density Lipoprotein", "HDL"],
        "unit": "mg/dL", "category": "Lipid Panel",
        "normal_male": (40, 999), "normal_female": (50, 999), "type": "numeric",
    },
    "Triglycerides": {
        "aliases": ["Triglycerides", "Triglyceride", "TG", "TRIG"],
        "unit": "mg/dL", "category": "Lipid Panel",
        "normal": (0, 150), "type": "numeric",
    },
    "VLDL": {
        "aliases": ["Cholesterol- VLDL", "Cholesterol-VLDL", "VLDL-C",
                    "Very Low Density Lipoprotein", "VLDL"],
        "unit": "mg/dL", "category": "Lipid Panel",
        "normal": (5, 35), "type": "numeric",
    },
    "Cholesterol:HDL Ratio": {
        "aliases": ["Cholesterol : HDL Cholesterol", "Cholesterol:HDL Ratio",
                    "Cholesterol:HDL", "TC/HDL", "Chol/HDL", "CHOL/HDL Ratio",
                    "CHOL/HDL"],
        "unit": "Ratio", "category": "Lipid Panel",
        "normal": (0.0, 5.0), "type": "numeric",
    },
    "LDL:HDL Ratio": {
        "aliases": ["LDL : HDL Cholesterol", "LDL:HDL Ratio", "LDL:HDL",
                    "LDL/HDL", "LDL/HDL Ratio"],
        "unit": "Ratio", "category": "Lipid Panel",
        "normal": (0.0, 3.5), "type": "numeric",
    },
    "Non-HDL Cholesterol": {
        "aliases": ["Non HDL Cholesterol", "Non-HDL Cholesterol", "Non-HDL-C", "NonHDL"],
        "unit": "mg/dL", "category": "Lipid Panel",
        "normal": (0, 130), "type": "numeric",
    },

    # ── Liver Function ────────────────────────────────────────────────────────
    "ALT": {
        "aliases": ["ALT", "SGPT", "Alanine Aminotransferase", "Alanine Transaminase"],
        "unit": "U/L", "category": "Liver Function",
        "normal_male": (7, 56), "normal_female": (7, 45), "type": "numeric",
    },
    "AST": {
        "aliases": ["AST", "SGOT", "Aspartate Aminotransferase", "Aspartate Transaminase"],
        "unit": "U/L", "category": "Liver Function",
        "normal": (17, 59), "type": "numeric",
    },
    "ALP": {
        "aliases": ["ALP", "Alkaline Phosphatase", "Alk Phos"],
        "unit": "U/L", "category": "Liver Function",
        "normal": (44, 147), "type": "numeric",
    },
    "GGT": {
        "aliases": ["GGT", "Gamma GT", "Gamma Glutamyl Transferase"],
        "unit": "U/L", "category": "Liver Function",
        "normal_male": (8, 61), "normal_female": (5, 36), "type": "numeric",
    },
    "Total Bilirubin": {
        "aliases": ["Total Bilirubin", "T.Bili", "TBIL", "Bilirubin Total",
                    "Bilirubin Total Serum"],
        "unit": "mg/dL", "category": "Liver Function",
        "normal": (0.2, 1.3), "type": "numeric",
    },
    "Direct Bilirubin": {
        "aliases": ["Direct Bilirubin", "D.Bili", "DBIL", "Conjugated Bilirubin",
                    "Bilirubin Direct"],
        "unit": "mg/dL", "category": "Liver Function",
        "normal": (0.0, 0.3), "type": "numeric",
    },
    # NEW: Indirect / Unconjugated Bilirubin
    "Indirect Bilirubin": {
        "aliases": ["Indirect Bilirubin", "Unconjugated Bilirubin", "Bilirubin Indirect",
                    "Indirect Bili", "I.Bili"],
        "unit": "mg/dL", "category": "Liver Function",
        "normal": (0.0, 1.1), "type": "numeric",
    },
    # NEW: Delta Bilirubin
    "Delta Bilirubin": {
        "aliases": ["Delta Bilirubin", "Bilirubin Delta", "D-Bilirubin"],
        "unit": "mg/dL", "category": "Liver Function",
        "normal": (0.0, 0.2), "type": "numeric",
    },
    "Albumin": {
        "aliases": ["Albumin", "Serum Albumin"],
        "unit": "g/dL", "category": "Liver Function",
        "normal": (3.5, 5.0), "type": "numeric",
    },
    "Total Protein": {
        "aliases": ["Total Protein", "Protein Total", "Total Protein Serum"],
        "unit": "g/dL", "category": "Liver Function",
        "normal": (6.3, 8.2), "type": "numeric",
    },
    # NEW: Globulin
    "Globulin": {
        "aliases": ["Globulin", "Serum Globulin", "Total Globulin"],
        "unit": "g/dL", "category": "Liver Function",
        "normal": (2.3, 3.5), "type": "numeric",
    },
    # NEW: Albumin/Globulin Ratio
    "A/G Ratio": {
        "aliases": ["A/G Ratio", "AG Ratio", "Albumin Globulin Ratio",
                    "Albumin/Globulin Ratio"],
        "unit": "", "category": "Liver Function",
        "normal": (1.3, 1.7), "type": "numeric",
    },

    # ── Thyroid ───────────────────────────────────────────────────────────────
    "TSH": {
        "aliases": ["TSH", "Thyroid Stimulating Hormone", "Thyrotropin",
                    "TSH - Thyroid Stimulating Hormone"],
        "unit": "µIU/mL", "category": "Thyroid",
        "normal": (0.35, 4.94), "type": "numeric",
    },
    # NEW: Total T3 (distinct from Free T3)
    "T3 Total": {
        "aliases": ["T3", "T3 Total", "Total T3", "Triiodothyronine",
                    "T3 - Triiodothyronine", "T3-Triiodothyronine"],
        "unit": "ng/mL", "category": "Thyroid",
        "normal": (0.58, 1.59), "type": "numeric",
    },
    "Free T3": {
        "aliases": ["FT3", "Free T3", "fT3", "Free Triiodothyronine"],
        "unit": "pg/mL", "category": "Thyroid",
        "normal": (2.3, 4.2), "type": "numeric",
    },
    # NEW: Total T4 (distinct from Free T4)
    "T4 Total": {
        "aliases": ["T4", "T4 Total", "Total T4", "Thyroxine",
                    "T4 - Thyroxine", "T4-Thyroxine"],
        "unit": "µg/dL", "category": "Thyroid",
        "normal": (4.87, 11.72), "type": "numeric",
    },
    "Free T4": {
        "aliases": ["FT4", "Free T4", "fT4", "Free Thyroxine"],
        "unit": "ng/dL", "category": "Thyroid",
        "normal": (0.8, 1.8), "type": "numeric",
    },

    # ── Iron Studies ──────────────────────────────────────────────────────────
    "Ferritin": {
        "aliases": ["Ferritin", "Serum Ferritin"],
        "unit": "ng/mL", "category": "Iron Studies",
        "normal_male": (24, 336), "normal_female": (11, 307), "type": "numeric",
    },
    "Serum Iron": {
        "aliases": ["Serum Iron", "Iron", "Iron Serum", "Fe", "S.Iron"],
        "unit": "µg/dL", "category": "Iron Studies",
        "normal": (49, 181), "type": "numeric",
    },
    # NEW: TIBC
    "TIBC": {
        "aliases": ["TIBC", "Total Iron Binding Capacity", "Total Iron Binding Capacity (TIBC)"],
        "unit": "µg/dL", "category": "Iron Studies",
        "normal": (261, 462), "type": "numeric",
    },
    # NEW: Transferrin Saturation
    "Transferrin Saturation": {
        "aliases": ["Transferrin Saturation", "TSAT", "Transferrin Sat",
                    "Iron Saturation", "% Transferrin Saturation"],
        "unit": "%", "category": "Iron Studies",
        "normal": (20, 50), "type": "numeric",
    },

    # ── Vitamins ──────────────────────────────────────────────────────────────
    "Vitamin B12": {
        "aliases": ["Vitamin B12", "B12", "Cobalamin", "Cyanocobalamin"],
        "unit": "pg/mL", "category": "Vitamins",
        "normal": (187, 833), "type": "numeric",
    },
    "Vitamin D": {
        "aliases": ["Vitamin D", "25-OH Vitamin D", "25-Hydroxyvitamin D", "Vit D",
                    "25(OH) Vitamin D", "Vitamin D3", "25 OH Vitamin D"],
        "unit": "ng/mL", "category": "Vitamins",
        "normal": (30, 100), "type": "numeric",
    },

    # ── Coagulation ───────────────────────────────────────────────────────────
    "PT/INR": {
        "aliases": ["INR", "Prothrombin Time", "PT/INR"],
        "unit": "INR", "category": "Coagulation",
        "normal": (0.8, 1.2), "type": "numeric",
    },
    "aPTT": {
        "aliases": ["aPTT", "APTT", "Activated Partial Thromboplastin Time"],
        "unit": "sec", "category": "Coagulation",
        "normal": (25, 35), "type": "numeric",
    },

    # ── Inflammation ──────────────────────────────────────────────────────────
    "CRP": {
        "aliases": ["CRP", "C-Reactive Protein", "hs-CRP", "hsCRP"],
        "unit": "mg/L", "category": "Inflammation",
        "normal": (0, 5), "type": "numeric",
    },
    "ESR": {
        "aliases": ["ESR", "Erythrocyte Sedimentation Rate", "Sed Rate"],
        "unit": "mm/hr", "category": "Inflammation",
        "normal_male": (0, 14), "normal_female": (0, 20), "type": "numeric",
    },
    # NEW: Homocysteine
    "Homocysteine": {
        "aliases": ["Homocysteine", "Homocysteine Serum", "tHcy", "Total Homocysteine",
                    "Homocysteine, Serum"],
        "unit": "µmol/L", "category": "Inflammation",
        "normal": (6.0, 14.8), "type": "numeric",
    },

    # ── Other ─────────────────────────────────────────────────────────────────
    # NEW: PSA
    "PSA": {
        "aliases": ["PSA", "PSA Total", "Prostate Specific Antigen",
                    "PSA-Prostate Specific Antigen", "PSA-Prostate Specific Antigen, Total"],
        "unit": "ng/mL", "category": "Other",
        "normal": (0, 4.0), "type": "numeric",
    },
    # NEW: IgE
    "IgE": {
        "aliases": ["IgE", "Total IgE", "Immunoglobulin E", "Serum IgE"],
        "unit": "IU/mL", "category": "Other",
        "normal": (0, 87), "type": "numeric",
    },

    # ── Absolute Differential Counts ──────────────────────────────────────────
    "Absolute Neutrophil Count": {
        "aliases": ["Absolute Neutrophil Count", "ANC", "Neutrophils Absolute",
                    "Neutrophil Absolute Count", "Abs Neutrophil"],
        "unit": "/cmm", "category": "CBC",
        "normal": (2000, 6700), "type": "numeric",
    },
    "Absolute Lymphocyte Count": {
        "aliases": ["Absolute Lymphocyte Count", "ALC", "Lymphocytes Absolute",
                    "Lymphocyte Absolute Count", "Abs Lymphocyte"],
        "unit": "/cmm", "category": "CBC",
        "normal": (1100, 3300), "type": "numeric",
    },
    "Absolute Eosinophil Count": {
        "aliases": ["Absolute Eosinophil Count", "AEC", "Eosinophils Absolute",
                    "Eosinophil Absolute Count", "Abs Eosinophil"],
        "unit": "/cmm", "category": "CBC",
        "normal": (0, 400), "type": "numeric",
    },
    "Absolute Monocyte Count": {
        "aliases": ["Absolute Monocyte Count", "AMC", "Monocytes Absolute",
                    "Monocyte Absolute Count", "Abs Monocyte"],
        "unit": "/cmm", "category": "CBC",
        "normal": (200, 700), "type": "numeric",
    },
    "Absolute Basophil Count": {
        "aliases": ["Absolute Basophil Count", "ABC", "Basophils Absolute",
                    "Basophil Absolute Count", "Abs Basophil"],
        "unit": "/cmm", "category": "CBC",
        "normal": (0, 100), "type": "numeric",
    },

    # ── Blood Group ───────────────────────────────────────────────────────────
    # qualitative type: value is text like "A", "B", "O", "AB", "Positive", "Negative"
    "ABO Type": {
        "aliases": ["ABO Type", "ABO Blood Group", "Blood Group ABO", "Blood Type ABO"],
        "unit": "", "category": "Other",
        "normal": None, "type": "qualitative",
    },
    "Rh Type": {
        "aliases": ["Rh Type", "Rh (D) Type", "RhD", "Rh Factor", "Rh(D)",
                    "Rh D Type", "Rhesus Factor"],
        "unit": "", "category": "Other",
        "normal": None, "type": "qualitative",
    },

    # ── Urine Physical / Chemical (Dipstick) ──────────────────────────────────
    "Urine pH": {
        "aliases": ["Urine pH", "pH Urine", "Urinary pH"],
        "unit": "", "category": "Urinalysis",
        "normal": (4.6, 8.0), "type": "numeric",
    },
    "Urine Specific Gravity": {
        "aliases": ["Specific Gravity", "Urine Specific Gravity", "SG Urine",
                    "Urine SG", "S.G."],
        "unit": "", "category": "Urinalysis",
        "normal": (1.005, 1.030), "type": "numeric",
    },
    "Urine Glucose": {
        "aliases": ["Urine Glucose", "Glucose Urine", "Glucosuria",
                    "Urinary Glucose"],
        "unit": "", "category": "Urinalysis",
        "normal": None, "type": "qualitative",
    },
    "Urine Protein": {
        "aliases": ["Urine Protein", "Protein Urine", "Urinary Protein",
                    "Proteinuria"],
        "unit": "", "category": "Urinalysis",
        "normal": None, "type": "qualitative",
    },
    "Urine Bilirubin": {
        "aliases": ["Urine Bilirubin", "Bilirubin Urine", "Bilirubin (urine)",
                    "Urinary Bilirubin"],
        "unit": "", "category": "Urinalysis",
        "normal": None, "type": "qualitative",
    },
    "Urobilinogen": {
        "aliases": ["Urobilinogen", "Urine Urobilinogen", "Urobilinogen Urine"],
        "unit": "", "category": "Urinalysis",
        "normal": None, "type": "qualitative",
    },
    "Urine Ketone": {
        "aliases": ["Urine Ketone", "Ketone Urine", "Ketones Urine",
                    "Urine Ketones", "Ketonuria"],
        "unit": "", "category": "Urinalysis",
        "normal": None, "type": "qualitative",
    },
    "Urine Nitrite": {
        "aliases": ["Urine Nitrite", "Nitrite Urine", "Nitrite"],
        "unit": "", "category": "Urinalysis",
        "normal": None, "type": "qualitative",
    },

    # ── Urine Microscopy ──────────────────────────────────────────────────────
    "Pus Cells": {
        "aliases": ["Pus Cells", "WBC Urine", "Urine WBC", "Leukocyte Esterase",
                    "Pus Cells Urine"],
        "unit": "/hpf", "category": "Urinalysis",
        "normal": (0, 2), "type": "numeric",
    },
    "Urine RBC": {
        "aliases": ["Red Cells", "Urine RBC", "RBC Urine", "Red Blood Cells Urine",
                    "Urine Red Cells"],
        "unit": "/hpf", "category": "Urinalysis",
        "normal": (0, 2), "type": "numeric",
    },
    "Epithelial Cells": {
        "aliases": ["Epithelial Cells", "Epithelial Cells Urine",
                    "Squamous Epithelial Cells"],
        "unit": "/hpf", "category": "Urinalysis",
        "normal": None, "type": "numeric",
    },
    "Casts": {
        "aliases": ["Casts", "Urine Casts", "Urinary Casts",
                    "Hyaline Casts"],
        "unit": "/hpf", "category": "Urinalysis",
        "normal": None, "type": "qualitative",
    },
    "Crystals": {
        "aliases": ["Crystals", "Urine Crystals", "Urinary Crystals"],
        "unit": "/hpf", "category": "Urinalysis",
        "normal": None, "type": "qualitative",
    },

    # ── Infection / Serology ──────────────────────────────────────────────────
    "HIV Ag/Ab": {
        "aliases": ["HIV I & II Ab/Ag with P24 Ag", "HIV Ag/Ab", "HIV 1 & 2",
                    "HIV Antibody", "HIV Antigen", "HIV I II", "Anti HIV"],
        "unit": "S/Co", "category": "Other",
        "normal": (0, 1.0), "type": "numeric",   # <1.0 = Non Reactive
    },
    "HBsAg": {
        "aliases": ["HBsAg", "Hepatitis B Surface Antigen", "HBs Antigen",
                    "Hepatitis B sAg", "HBs Ag"],
        "unit": "S/Co", "category": "Other",
        "normal": (0, 1.0), "type": "numeric",   # <1.0 = Non Reactive
    },

    # ── HB Electrophoresis Peaks ──────────────────────────────────────────────
    "P2 Peak": {
        "aliases": ["P2 Peak", "P2", "HbP2", "Hb P2 Peak"],
        "unit": "%", "category": "CBC",
        "normal": (0, 10), "type": "numeric",   # >10% may indicate glycated Hb / variant
    },
    "P3 Peak": {
        "aliases": ["P3 Peak", "P3", "HbP3", "Hb P3 Peak"],
        "unit": "%", "category": "CBC",
        "normal": (0, 10), "type": "numeric",   # >10% may indicate abnormal variant
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# REGEX PATTERN BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _alias_pattern(aliases: List[str]) -> str:
    escaped = sorted([re.escape(a) for a in aliases], key=len, reverse=True)
    bounded = [r"\b" + e + r"\b" for e in escaped]
    return "(?:" + "|".join(bounded) + ")"


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


# ─────────────────────────────────────────────────────────────────────────────
# REFERENCE-RANGE PARSER
# ─────────────────────────────────────────────────────────────────────────────

_REF_RANGE_PAT = re.compile(
    r"\b(\d{1,5}(?:\.\d{1,3})?)\s*[-–—]\s*(\d{1,5}(?:\.\d{1,3})?)\b"
)


def _looks_like_range_only(text: str, match_start: int, match_end: int) -> bool:
    surrounding = text[max(0, match_start - 30): match_end + 30]
    return len(list(_REF_RANGE_PAT.finditer(surrounding))) >= 2


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


# ─────────────────────────────────────────────────────────────────────────────
# TABLE-BASED EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

# FIX: Rows whose test_name matches these patterns are reference/risk table rows — skip them
_SKIP_ROW_RE = re.compile(
    r"risk\s*group|treatment\s*target|primary\s*target|secondary\s*target"
    r"|extreme.{0,5}risk|very\s*high.{0,5}risk|moderate.{0,5}risk"
    r"|category\s*[abc]\b|apo.?b|ascvd|test\s*name|bio\.?\s*ref",
    re.IGNORECASE
)


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

        # FIX: skip rows that are from risk tables or headers
        if _SKIP_ROW_RE.search(raw_lower):
            return None

        best_vital = None
        best_score = 0

        for vital_name, defn in VITAL_DEFS.items():
            for alias in defn["aliases"]:
                alias_lower = alias.lower()
                # FIX: skip aliases shorter than 4 chars in table matching
                # Prevents "Ca" matching inside "category", "TC" inside "TATA", etc.
                if len(alias_lower) < 4:
                    continue
                # Exact match (highest priority)
                if alias_lower == raw_lower:
                    return vital_name
                # Word-boundary substring match
                if re.search(r'\b' + re.escape(alias_lower) + r'\b', raw_lower):
                    score = len(alias_lower)
                    if score > best_score:
                        best_score = score
                        best_vital = vital_name

        return best_vital if best_score >= 4 else None


# ─────────────────────────────────────────────────────────────────────────────
# REGEX-BASED TEXT EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# PDF TEXT + TABLE EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

class PDFReader:
    def read(self, pdf_path: str) -> Tuple[str, List[List], str]:
        text, tables = self._try_pdfplumber(pdf_path)
        method = "pdfplumber"

        if len(text.strip()) < 50:
            text2 = self._try_pymupdf(pdf_path)
            if len(text2.strip()) > len(text.strip()):
                text = text2
                method = "pymupdf"

        if len(text.strip()) < 50:
            text = self._try_ocr(pdf_path)
            method = "ocr"

        return text, tables, method

    def _try_pdfplumber(self, path: str) -> Tuple[str, List[List]]:
        full_text = ""
        all_tables: List[List] = []
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"
                    try:
                        tables = page.extract_tables()
                        if tables:
                            all_tables.extend(tables)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")
        return full_text, all_tables

    def _try_pymupdf(self, path: str) -> str:
        try:
            import fitz
            doc = fitz.open(path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"PyMuPDF failed: {e}")
        return ""

    def _try_ocr(self, path: str) -> str:
        try:
            from pdf2image import convert_from_path
            import pytesseract
            images = convert_from_path(path, dpi=300)
            return "".join(pytesseract.image_to_string(img) + "\n" for img in images)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# PATIENT INFO EXTRACTOR
# FIX: All patterns updated for TATA 1MG format
# ─────────────────────────────────────────────────────────────────────────────

_PATIENT_PATTERNS = {
    "Patient Name": [
        # TATA 1MG: "Customer Name : Mr.PRIYANK GUPTA   Collected Via : ..."
        re.compile(
            r"Customer\s*Name\s*[:\-]\s*(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*([A-Za-z][A-Za-z\s\.]{2,40}?)(?=\s{2,}|\s*Collected|\s*\n|$)",
            re.IGNORECASE
        ),
        # "Patient Name : John Doe" / "Patient Name: Mrs. Priya Singh"
        re.compile(
            r"Patient\s*Name\s*[:\-]?\s*(?:(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+)?([A-Za-z][A-Za-z\s\.]{1,40}?)(?=\s{2,}|\s*\n|\s*Age|\s*DOB|\s*Lab|\s*Reg|\s*Client|$)",
            re.IGNORECASE
        ),
        # "PATIENT NAME: AMIT VERMA" (all caps, SRL style)
        re.compile(
            r"^PATIENT\s+NAME\s*[:\-]\s*([A-Z][A-Z\s\.]{2,40}?)(?=\s{2,}|\s*\n|$)",
            re.MULTILINE
        ),
        # "Name : Lyubochka Svetka Lab Id : ..." / "Name: RAHUL KUMAR"
        re.compile(
            r"^\s*Name\s*[:\-]\s*(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*([A-Za-z][A-Za-z\s\.]{2,40}?)(?:\s{2,}|\s*\n|\s*Age|\s*Lab|\s*Reg|\s*Client|\s*$)",
            re.IGNORECASE | re.MULTILINE
        ),
    ],
    "Age": [
        # "Age/Gender : 51/Male" or "Age/Sex : 25 Yrs / Male"  (slash-separated)
        re.compile(r"Age\s*/\s*(?:Gender|Sex)\s*[:\-]\s*(\d{1,3})(?:\s*Yrs?)?\s*/", re.IGNORECASE),
        # "Age / Sex       : 45 Yrs / Male"  (spaces around slash)
        re.compile(r"Age\s*\/\s*Sex\s*[:\-]\s*(\d{1,3})", re.IGNORECASE),
        # "Sex/Age : Male / 41 Y 01-Feb-1982"  (Sterling Accuris — reversed order)
        re.compile(r"Sex\s*/\s*Age\s*[:\-]\s*(?:Male|Female)\s*/\s*(\d{1,3})\s*Y", re.IGNORECASE),
        # "AGE: 32 YEARS" or "Age: 34 Years" or "Age : 25 Yrs" (inline or on its own line)
        re.compile(r"(?:^|\s)Age\s*[:\-]\s*(\d{1,3})\s*(?:years?|yrs?|Y)?\b", re.IGNORECASE | re.MULTILINE),
        # "45 Yrs" standalone (Metropolis / Thyrocare inline age without label)
        re.compile(r"\b(\d{1,3})\s*(?:Yrs?|Years?)\b", re.IGNORECASE),
    ],
    "Gender": [
        # "Age/Gender : 51/Male" or "Age/Sex : 25 Yrs / Male"
        re.compile(r"Age\s*/\s*(?:Gender|Sex)\s*[:\-]\s*\d+(?:\s*Yrs?)?\s*/\s*(Male|Female|M\b|F\b)", re.IGNORECASE),
        # "Age / Sex  : 45 Yrs / Male"
        re.compile(r"\d+\s*Yrs?\s*/\s*(Male|Female)\b", re.IGNORECASE),
        # "Sex/Age : Male / 41 Y"  (Sterling Accuris — reversed order)
        re.compile(r"Sex\s*/\s*Age\s*[:\-]\s*(Male|Female)\s*/", re.IGNORECASE),
        # "Sex: Male" / "Gender: Female" / "SEX: MALE" / standalone "MALE"/"FEMALE" after AGE
        re.compile(r"^\s*(?:Sex|Gender)\s*[:\-]\s*(Male|Female|M\b|F\b)", re.IGNORECASE | re.MULTILINE),
        re.compile(r"\bSex\s*[:\-]\s*(Male|Female)\b", re.IGNORECASE),
    ],
    "Date of Birth": [
        re.compile(r"(?:DOB|Date\s*of\s*Birth)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", re.IGNORECASE),
    ],
    "Report Date": [
        # "05/Jan/2026" or "10-Mar-2026" mixed alphanumeric
        re.compile(
            r"(?:Report\s*Date|Reported\s*On|Report\s*On)\s*[:\-]?\s*(\d{1,2}[\/-](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\/-]\d{4})",
            re.IGNORECASE
        ),
        # "Report Date : 10/03/2026" numeric
        re.compile(
            r"(?:Report\s*Date|Reported\s*On|Report\s*On)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            re.IGNORECASE
        ),
        # "Collection Date / Sample Collected / Collected On"
        re.compile(
            r"(?:Collection\s*Date|Sample\s*Collected|Collected\s*On|Collection\s*On)\s*[:\-]?\s*(\d{1,2}[\/\-\.](?:\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*)[\/\-\.]\d{2,4})",
            re.IGNORECASE
        ),
        # "Date: 12-02-2026" bare label (may be mid-line or start of line)
        re.compile(
            r"\bDate\s*[:\-]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            re.IGNORECASE
        ),
        # "13 March 2026" written out
        re.compile(
            r"(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})",
            re.IGNORECASE
        ),
    ],
    "Doctor": [
        # "Referred by / Ref. By : Dr. XYZ" — requires Dr. prefix, min 3 chars after it
        re.compile(
            r"(?:Referred?\s*[Bb]y|Ref\.?\s*[Bb]y|Consulting\s*(?:Dr\.?|Doctor)?)\s*[:\-]?\s*Dr\.?\s*([A-Za-z][A-Za-z\s\.]{2,35}?)(?=\s{2,}|\s*\n|\s*$)",
            re.IGNORECASE | re.MULTILINE
        ),
        # Same without "Dr." prefix (some reports write just the name)
        re.compile(
            r"(?:Referred?\s*[Bb]y|Ref\.?\s*[Bb]y)\s*[:\-]?\s*(?!Dr\.?\s*$)([A-Za-z][A-Za-z\s\.]{3,35}?)(?=\s{2,}|\s*\n|\s*$)",
            re.IGNORECASE | re.MULTILINE
        ),
        # "Consulting Doctor: Dr. Kapoor" / "CONSULTING DOCTOR: DR. KAPOOR"
        re.compile(
            r"(?:Consulting\s*Doctor|Attending\s*(?:Physician|Doctor))\s*[:\-]?\s*(?:Dr\.?\s*)?([A-Za-z][A-Za-z\s\.]{2,35}?)(?=\s{2,}|\s*\n|\s*$)",
            re.IGNORECASE | re.MULTILINE
        ),
        # "Doctor: Dr. Sharma" / "Doctor : Smith" (bare label)
        re.compile(
            r"^\s*Doctor\s*[:\-]\s*(?:Dr\.?\s*)?([A-Za-z][A-Za-z\s\.]{2,35}?)(?=\s{2,}|\s*\n|\s*$)",
            re.IGNORECASE | re.MULTILINE
        ),
    ],
}


def extract_patient_info(text: str) -> Dict[str, str]:
    info: Dict[str, str] = {}
    for field_name, patterns in _PATIENT_PATTERNS.items():
        for pat in patterns:
            m = pat.search(text)
            if m:
                val = m.group(1).strip()
                val = re.sub(r"\s+", " ", val).strip(" .,:").rstrip(".")
                if val and len(val) >= 2:
                    info[field_name] = val
                    break

    # Derive Age from DOB if Age was not found directly
    if "Age" not in info and "Date of Birth" in info:
        try:
            from datetime import datetime
            dob_str = info["Date of Birth"]
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
                try:
                    dob = datetime.strptime(dob_str, fmt)
                    age = (datetime.today() - dob).days // 365
                    if 0 < age < 130:
                        info["Age"] = str(age)
                    break
                except ValueError:
                    continue
        except Exception:
            pass

    return info


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

LLM_PROMPT_TEMPLATE = """You are a medical data extraction assistant. Extract ALL vital signs and lab values from the following medical report text.

Return ONLY a valid JSON array. Each element must be an object with these exact keys:
  "name"            : canonical vital/test name (string)
  "value"           : extracted numeric value (string)
  "unit"            : measurement unit (string)
  "reference_range" : reference range as given in the document (string, empty if not found)
  "status"          : "Normal", "High", "Low", or "Unknown"
  "category"        : one of: Basic Vitals, CBC, Metabolic Panel, Lipid Panel, Liver Function, Thyroid, Iron Studies, Vitamins, Coagulation, Inflammation, Other

Do NOT include any explanation or markdown. Only the JSON array.

Medical report text:
\"\"\"
{text}
\"\"\"
"""


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



class GroqFallback:
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key
        self.model = model

    def extract(self, text: str) -> List[VitalResult]:
        from groq import Groq
        import json

        # Sanitize API key — strip any non-ASCII chars (e.g. accidentally pasted emoji)
        clean_key = self.api_key.encode("ascii", errors="ignore").decode("ascii").strip()
        if not clean_key:
            raise RuntimeError("Groq API key is empty or contains only non-ASCII characters. Please paste a valid gsk_... key.")
        client = Groq(api_key=clean_key)
        # Sanitize text — strip non-ASCII chars that Groq/LLM APIs reject
        safe_text = text[:12000].encode("ascii", errors="ignore").decode("ascii")
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

        used_gemini = False
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

        category_order = ["Basic Vitals", "CBC", "Metabolic Panel", "Lipid Panel",
                          "Liver Function", "Thyroid", "Iron Studies", "Vitamins",
                          "Coagulation", "Inflammation", "Other"]
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
            "vitals":      combined,
            "patient_info": patient_info,
            "text_length":  len(text),
            "pdf_method":   pdf_method,
            "used_gemini":  used_gemini,  # key kept as-is for UI compatibility
            "stats":        stats,
        }


# ─────────────────────────────────────────────────────────────────────────────
# MODULE STARTUP — load previously learned vitals into regex engine
# ─────────────────────────────────────────────────────────────────────────────
_n = load_learned_vitals()
if _n:
    logger.info(f"[LearnedVitals] {_n} previously learned vital(s) ready in regex engine.")
