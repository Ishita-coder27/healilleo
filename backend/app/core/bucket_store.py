# app/core/bucket_store.py

from threading import Lock

lock = Lock()

# Static bucket structure
bucket_map = {
  "cardiovascular": [
    "Blood Pressure",
    "Heart Rate"
  ],

  "general_wellness": [
    "Temperature",
    "Height",
    "PSA"
  ],

  "respiratory": [
    "Respiratory Rate",
    "SpO2"
  ],

  "nutritional": [
    "Weight",
    "BMI",
    "Vitamin B12",
    "Vitamin D",
    "Homocysteine"
  ],

  "blood_cbc": [
    "Hemoglobin",
    "RBC Count",
    "Hematocrit",
    "MCV",
    "MCH",
    "MCHC",
    "RDW",
    "RDW CV",
    "WBC Count",
    "TLC (Total Leucocyte Count)",
    "Neutrophils",
    "Lymphocytes",
    "Monocytes",
    "Eosinophils",
    "Basophils",
    "Platelets",
    "Platelet Count",
    "MPV",
    "Hb A",
    "Hb A2",
    "Fetal Hemoglobin",
    "Ferritin",
    "Serum Iron",
    "TIBC",
    "Transferrin Saturation",
    "PT/INR",
    "aPTT",
    "CRP",
    "ESR",
    "IgE",
    "Absolute Neutrophil Count",
    "Absolute Lymphocyte Count",
    "Absolute Eosinophil Count",
    "Absolute Monocyte Count",
    "Absolute Basophil Count",
    "ABO Type",
    "Rh Type",
    "Urine Nitrite",
    "Pus Cells",
    "HIV Ag/Ab",
    "HBsAg",
    "P2 Peak",
    "P3 Peak",
    "Total Erythrocyte Count (TRBC)"
  ],

  "diabetes_metabolic": [
    "Glucose",
    "Fasting Blood Sugar",
    "HbA1c",
    "Mean Blood Glucose",
    "Total Cholesterol",
    "Cholesterol",
    "LDL Cholesterol",
    "Direct LDL",
    "HDL Cholesterol",
    "Triglycerides",
    "Triglyceride",
    "VLDL",
    "Cholesterol:HDL Ratio",
    "CHOL/HDL Ratio",
    "LDL:HDL Ratio",
    "LDL/HDL Ratio",
    "LDL to HDL Ratio",
    "Non-HDL Cholesterol",
    "Urine Glucose",
    "Urine Ketone"
  ],

  "kidney_renal": [
    "BUN",
    "Urea",
    "Creatinine",
    "eGFR",
    "Uric Acid",
    "Microalbumin",
    "Urine pH",
    "Urine Specific Gravity",
    "Urine Protein",
    "Urine RBC",
    "Epithelial Cells",
    "Casts",
    "Crystals"
  ],

  "electrolytes": [
    "Sodium",
    "Potassium",
    "Chloride",
    "Calcium",
    "SERUM PHOSPHORUS",
    "S.Calciium"
  ],

  "liver_hepatic": [
    "ALT",
    "AST",
    "ALP",
    "GGT",
    "Total Bilirubin",
    "Direct Bilirubin",
    "Conjugated Bilirubin",
    "Indirect Bilirubin",
    "Unconjugated Bilirubin",
    "Delta Bilirubin",
    "Albumin",
    "Total Protein",
    "Globulin",
    "A/G Ratio",
    "Urine Bilirubin",
    "Urobilinogen"
  ],

  "thyroid": [
    "TSH",
    "TSH - Thyroid Stimulating Hormone",
    "T3 Total",
    "T3 - Triiodothyronine",
    "Free T3",
    "T4 Total",
    "T4 - Thyroxine",
    "Free T4"
  ]
}

# Dynamic availability
vital_exists = {
  "Blood Pressure": False,
  "Heart Rate": False,
  "Temperature": False,
  "Height": False,
  "PSA": False,
  "Respiratory Rate": False,
  "SpO2": False,
  "Weight": False,
  "BMI": False,
  "Vitamin B12": False,
  "Vitamin D": False,
  "Homocysteine": False,
  "Hemoglobin": False,
  "RBC Count": False,
  "Hematocrit": False,
  "MCV": False,
  "MCH": False,
  "MCHC": False,
  "RDW": False,
  "RDW CV": False,
  "WBC Count": False,
  "TLC (Total Leucocyte Count)": False,
  "Neutrophils": False,
  "Lymphocytes": False,
  "Monocytes": False,
  "Eosinophils": False,
  "Basophils": False,
  "Platelets": False,
  "Platelet Count": False,
  "MPV": False,
  "Hb A": False,
  "Hb A2": False,
  "Fetal Hemoglobin": False,
  "Ferritin": False,
  "Serum Iron": False,
  "TIBC": False,
  "Transferrin Saturation": False,
  "PT/INR": False,
  "aPTT": False,
  "CRP": False,
  "ESR": False,
  "IgE": False,
  "Absolute Neutrophil Count": False,
  "Absolute Lymphocyte Count": False,
  "Absolute Eosinophil Count": False,
  "Absolute Monocyte Count": False,
  "Absolute Basophil Count": False,
  "ABO Type": False,
  "Rh Type": False,
  "Urine Nitrite": False,
  "Pus Cells": False,
  "HIV Ag/Ab": False,
  "HBsAg": False,
  "P2 Peak": False,
  "P3 Peak": False,
  "Total Erythrocyte Count (TRBC)": False,
  "Glucose": False,
  "Fasting Blood Sugar": False,
  "HbA1c": False,
  "Mean Blood Glucose": False,
  "Total Cholesterol": False,
  "Cholesterol": False,
  "LDL Cholesterol": False,
  "Direct LDL": False,
  "HDL Cholesterol": False,
  "Triglycerides": False,
  "Triglyceride": False,
  "VLDL": False,
  "Cholesterol:HDL Ratio": False,
  "CHOL/HDL Ratio": False,
  "LDL:HDL Ratio": False,
  "LDL/HDL Ratio": False,
  "LDL to HDL Ratio": False,
  "Non-HDL Cholesterol": False,
  "Urine Glucose": False,
  "Urine Ketone": False,
  "BUN": False,
  "Urea": False,
  "Creatinine": False,
  "eGFR": False,
  "Uric Acid": False,
  "Microalbumin": False,
  "Urine pH": False,
  "Urine Specific Gravity": False,
  "Urine Protein": False,
  "Urine RBC": False,
  "Epithelial Cells": False,
  "Casts": False,
  "Crystals": False,
  "Sodium": False,
  "Potassium": False,
  "Chloride": False,
  "Calcium": False,
  "SERUM PHOSPHORUS": False,
  "S.Calciium": False,
  "ALT": False,
  "AST": False,
  "ALP": False,
  "GGT": False,
  "Total Bilirubin": False,
  "Direct Bilirubin": False,
  "Conjugated Bilirubin": False,
  "Indirect Bilirubin": False,
  "Unconjugated Bilirubin": False,
  "Delta Bilirubin": False,
  "Albumin": False,
  "Total Protein": False,
  "Globulin": False,
  "A/G Ratio": False,
  "Urine Bilirubin": False,
  "Urobilinogen": False,
  "TSH": False,
  "TSH - Thyroid Stimulating Hormone": False,
  "T3 Total": False,
  "T3 - Triiodothyronine": False,
  "Free T3": False,
  "T4 Total": False,
  "T4 - Thyroxine": False,
  "Free T4": False
}


def get_bucket_vitals(bucket_name: str):
    if bucket_name not in bucket_map:
        return None

    return {
        vital: vital_exists.get(vital, False)
        for vital in bucket_map[bucket_name]
    }


def mark_vital_present(vital_name: str):
    with lock:
        if vital_name in vital_exists:
            vital_exists[vital_name] = True


def mark_vital_absent(vital_name: str):
    with lock:
        if vital_name in vital_exists:
            vital_exists[vital_name] = False


def initialize_vitals(existing_vitals: list):
    with lock:
        for vital in vital_exists:
            vital_exists[vital] = False

        for vital in existing_vitals:
            if vital in vital_exists:
                vital_exists[vital] = True