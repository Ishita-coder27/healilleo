from typing import Dict
VITAL_DEFS: Dict[str, Dict] = {

    # ── Basic Vitals ──────────────────────────────────────────────────────────
    "Blood Pressure": {
        "aliases": ["BP", "Blood Pressure", "B.P", "Systolic/Diastolic", "SBP/DBP"],
        "unit": "mmHg",
        "category": "cardiovascular",
        "normal": {"systolic": (90, 120), "diastolic": (60, 80)},
        "type": "bp",
    },

    "Heart Rate": {
        "aliases": ["HR", "Heart Rate", "Pulse", "P.R", "PR", "Pulse Rate"],
        "unit": "bpm",
        "category": "cardiovascular",
        "normal": (60, 100),
        "type": "numeric",
    },

    "Temperature": {
        "aliases": ["Temp", "Temperature", "Body Temp"],
        "unit": "°F",
        "category": "general_wellness",
        "normal_F": (97.8, 99.1),
        "normal_C": (36.5, 37.3),
        "type": "temp",
    },

    "Respiratory Rate": {
        "aliases": ["RR", "Resp Rate", "Respiratory Rate", "Respirations"],
        "unit": "breaths/min",
        "category": "respiratory",
        "normal": (12, 20),
        "type": "numeric",
    },

    "SpO2": {
        "aliases": ["SpO2", "O2 Sat", "Oxygen Saturation", "Spo2", "SaO2"],
        "unit": "%",
        "category": "respiratory",
        "normal": (95, 100),
        "type": "numeric",
    },

    "Weight": {
        "aliases": ["Weight", "Body Weight"],
        "unit": "kg",
        "category": "nutritional",
        "normal": None,
        "type": "numeric",
    },

    "Height": {
        "aliases": ["Height", "Body Height"],
        "unit": "cm",
        "category": "general_wellness",
        "normal": None,
        "type": "numeric",
    },

    "BMI": {
        "aliases": ["BMI", "Body Mass Index"],
        "unit": "kg/m²",
        "category": "nutritional",
        "normal": (18.5, 24.9),
        "type": "numeric",
    },

    # ── CBC ───────────────────────────────────────────────────────────────────
    "Hemoglobin": {
        "aliases": ["Hb", "Hemoglobin", "HGB", "Haemoglobin"],
        "unit": "g/dL",
        "category": "blood_cbc",
        "normal_male": (13.0, 16.5),
        "normal_female": (12.0, 15.5),
        "type": "numeric",
    },

    "RBC Count": {
        "aliases": ["RBC", "RBC Count", "Red Blood Cells", "Red Cell Count",
                    "Erythrocytes", "Red Blood Cell Count"],
        "unit": "million/cmm",
        "category": "blood_cbc",
        "normal_male": (4.5, 5.5),
        "normal_female": (4.1, 5.1),
        "type": "numeric",
    },

    "Hematocrit": {
        "aliases": ["HCT", "Hematocrit", "Haematocrit", "PCV", "Packed Cell Volume"],
        "unit": "%",
        "category": "blood_cbc",
        "normal_male": (40.0, 49.0),
        "normal_female": (36.0, 46.0),
        "type": "numeric",
    },

    "MCV": {
        "aliases": ["MCV", "Mean Corpuscular Volume"],
        "unit": "fL",
        "category": "blood_cbc",
        "normal": (83, 101),
        "type": "numeric",
    },

    "MCH": {
        "aliases": ["MCH", "Mean Corpuscular Hemoglobin"],
        "unit": "pg",
        "category": "blood_cbc",
        "normal": (27.1, 32.5),
        "type": "numeric",
    },

    "MCHC": {
        "aliases": ["MCHC", "Mean Corpuscular Hemoglobin Concentration"],
        "unit": "g/dL",
        "category": "blood_cbc",
        "normal": (32.5, 36.7),
        "type": "numeric",
    },
    # NEW: Red Cell Distribution Width
    "RDW": {
        "aliases": ["RDW", "RDW CV", "RDW-CV", "Red Cell Distribution Width",
                    "RBC Distribution Width"],
        "unit": "%",
        "category": "blood_cbc",
        "normal": (11.6, 14.0),
        "type": "numeric",
    },

    "WBC Count": {
        "aliases": ["WBC", "WBC Count", "White Blood Cells", "White Cell Count",
                    "Leukocytes", "TLC", "Total WBC"],
        "unit": "/cmm",
        "category": "blood_cbc",
        "normal": (4000, 10000),
        "type": "numeric",
    },

    "Neutrophils": {
        "aliases": ["Neutrophils", "NEUT", "Segs", "PMN"],
        "unit": "%",
        "category": "blood_cbc",
        "normal": (40, 80),
        "type": "numeric",
    },

    "Lymphocytes": {
        "aliases": ["Lymphocytes", "LYMPH", "LYM"],
        "unit": "%",
        "category": "blood_cbc",
        "normal": (20, 40),
        "type": "numeric",
    },

    "Monocytes": {
        "aliases": ["Monocytes", "MONO"],
        "unit": "%",
        "category": "blood_cbc",
        "normal": (2, 10),
        "type": "numeric",
    },

    "Eosinophils": {
        "aliases": ["Eosinophils", "EOS"],
        "unit": "%",
        "category": "blood_cbc",
        "normal": (1, 6),
        "type": "numeric",
    },
    # NEW: Basophils
    "Basophils": {
        "aliases": ["Basophils", "BASO", "Basophil"],
        "unit": "%",
        "category": "blood_cbc",   
        "normal": (0, 2),
        "type": "numeric",
    },

    "Platelets": {
        "aliases": ["PLT", "Platelets", "Thrombocytes", "Platelet Count",
                    "Platelet Count Electrical"],
        "unit": "/cmm",
        "category": "blood_cbc",
        "normal": (150000, 410000),
        "type": "numeric",
    },
    # NEW: Mean Platelet Volume
    "MPV": {
        "aliases": ["MPV", "Mean Platelet Volume"],
        "unit": "fL",
        "category": "blood_cbc",
        "normal": (7.5, 10.3),
        "type": "numeric",
    },
    # NEW: HB Electrophoresis components
    "Hb A": {
        "aliases": ["Hb A", "HbA", "Hemoglobin A", "Haemoglobin A"],
        "unit": "%",
        "category": "blood_cbc",
        "normal": (96.8, 97.8),
        "type": "numeric",
    },

    "Hb A2": {
        "aliases": ["Hb A2", "HbA2", "Hemoglobin A2", "Haemoglobin A2"],
        "unit": "%",
        "category": "blood_cbc",
        "normal": (2.2, 3.2),
        "type": "numeric",
    },

    "Fetal Hemoglobin": {
        "aliases": ["Foetal Hb", "Fetal Hb", "HbF", "Fetal Hemoglobin",
                    "Foetal Hemoglobin", "Hemoglobin F"],
        "unit": "%",
        "category": "blood_cbc",
        "normal": (0.0, 1.0),
        "type": "numeric",
    },

    # ── Metabolic Panel ───────────────────────────────────────────────────────
    "Glucose": {
        "aliases": ["Glucose", "Blood Glucose", "FBS", "Fasting Glucose", "RBS",
                    "Blood Sugar", "Fasting Blood Sugar", "Random Blood Sugar",
                    "Fasting Blood Sugar GOD"],
        "unit": "mg/dL",
        "category": "diabetes_metabolic",
        "normal_fasting": (74, 106),
        "normal": (70, 140),
        "type": "numeric",
    },

    "HbA1c": {
        "aliases": ["HbA1c", "Hemoglobin A1c", "Glycated Hemoglobin", "A1C", "Hba1c",
                    "HbA1c Glycosylated Hemoglobin"],
        "unit": "%",
        "category": "diabetes_metabolic",
        "normal": (4.0, 5.6),
        "type": "numeric",
    },
    # NEW: Mean Blood Glucose (derived from HbA1c)
    "Mean Blood Glucose": {
        "aliases": ["Mean Blood Glucose", "eAG", "Estimated Average Glucose",
                    "Average Blood Glucose"],
        "unit": "mg/dL",
        "category": "diabetes_metabolic",
        "normal": (70, 154),
        "type": "numeric",
    },

    "BUN": {
        "aliases": ["BUN", "Blood Urea Nitrogen", "Urea Nitrogen"],
        "unit": "mg/dL",
        "category": "kidney_renal",   
        "normal": (9.0, 20.0),
        "type": "numeric",
    },
    # NEW: Serum Urea (separate from BUN — Sterling reports both)
    "Urea": {
        "aliases": ["Urea", "Serum Urea", "Blood Urea", "Urea Serum"],
        "unit": "mg/dL",
        "category": "kidney_renal",   
        "normal": (19.3, 43.0),
        "type": "numeric",
    },

    "Creatinine": {
        "aliases": ["Creatinine", "Creat", "Serum Creatinine", "Creatinine Serum",
                    "Creatinine, Serum"],
        "unit": "mg/dL",
        "category": "kidney_renal",   
        "normal_male": (0.66, 1.25),
        "normal_female": (0.59, 1.04),
        "type": "numeric",
    },

    "eGFR": {
        "aliases": ["eGFR", "GFR", "Estimated GFR", "Glomerular Filtration Rate"],
        "unit": "mL/min/1.73m²",
        "category": "kidney_renal",   
        "normal": (90, 999),
        "type": "numeric",
    },

    "Sodium": {
        "aliases": ["Sodium", "Serum Sodium", "Sodium (Na+)", "Na+", "Na"],
        "unit": "mmol/L",
        "category": "electrolytes", 
        "normal": (136, 145),
        "type": "numeric",
    },

    "Potassium": {
        "aliases": ["Potassium", "Serum Potassium", "Potassium (K+)", "K+", "K"],
        "unit": "mmol/L",
        "category": "electrolytes",    
        "normal": (3.5, 5.1),
        "type": "numeric",
    },

    "Chloride": {
        "aliases": ["Chloride", "Serum Chloride", "Chloride (Cl-)", "Cl-"],
        "unit": "mmol/L",
        "category": "electrolytes",    
        "normal": (98, 107),
        "type": "numeric",
    },

    "Calcium": {
        "aliases": ["Calcium", "Total Calcium", "Serum Calcium"],
        "unit": "mg/dL",
        "category": "electrolytes",    
        "normal": (8.4, 10.2),
        "type": "numeric",
    },

    "Uric Acid": {
        "aliases": ["Uric Acid", "Urate", "Serum Urate"],
        "unit": "mg/dL",
        "category": "kidney_renal",    
        "normal_male": (3.5, 8.5),
        "normal_female": (2.6, 6.0),
        "type": "numeric",
    },
    # NEW: Urine Microalbumin
    "Microalbumin": {
        "aliases": ["Microalbumin", "Microalbumin Urine", "Microalbumin (per urine volume)",
                    "Urine Microalbumin", "Urinary Albumin"],
        "unit": "mg/L",
        "category": "kidney_renal",    
        "normal": (0, 16.7),
        "type": "numeric",
    },

    # ── Lipid Panel ───────────────────────────────────────────────────────────
    "Total Cholesterol": {
        "aliases": ["Cholesterol - Total", "Cholesterol, Total", "Total Cholesterol",
                    "Serum Cholesterol", "Chol"],
        "unit": "mg/dL",
        "category": "diabetes_metabolic",    
        "normal": (0, 200),
        "type": "numeric",
    },

    "LDL Cholesterol": {
        "aliases": ["Cholesterol - LDL", "LDL-C", "LDL Cholesterol",
                    "Low Density Lipoprotein", "Direct LDL", "LDL"],
        "unit": "mg/dL",
        "category": "diabetes_metabolic",    
        "normal": (0, 100),
        "type": "numeric",
    },

    "HDL Cholesterol": {
        "aliases": ["Cholesterol - HDL", "HDL-C", "HDL Cholesterol",
                    "High Density Lipoprotein", "HDL"],
        "unit": "mg/dL",
        "category": "diabetes_metabolic",    
        "normal_male": (40, 999),
        "normal_female": (50, 999),
        "type": "numeric",
    },

    "Triglycerides": {
        "aliases": ["Triglycerides", "Triglyceride", "TG", "TRIG"],
        "unit": "mg/dL",
        "category": "diabetes_metabolic",    
        "normal": (0, 150),
        "type": "numeric",
    },

    "VLDL": {
        "aliases": ["Cholesterol- VLDL", "Cholesterol-VLDL", "VLDL-C",
                    "Very Low Density Lipoprotein", "VLDL"],
        "unit": "mg/dL",
        "category": "diabetes_metabolic",    
        "normal": (5, 35),
        "type": "numeric",
    },

    "Cholesterol:HDL Ratio": {
        "aliases": ["Cholesterol : HDL Cholesterol", "Cholesterol:HDL Ratio",
                    "Cholesterol:HDL", "TC/HDL", "Chol/HDL", "CHOL/HDL Ratio",
                    "CHOL/HDL"],
        "unit": "Ratio",
        "category": "diabetes_metabolic",    
        "normal": (0.0, 5.0),
        "type": "numeric",
    },

    "LDL:HDL Ratio": {
        "aliases": ["LDL : HDL Cholesterol", "LDL:HDL Ratio", "LDL:HDL",
                    "LDL/HDL", "LDL/HDL Ratio"],
        "unit": "Ratio",
        "category": "diabetes_metabolic",    
        "normal": (0.0, 3.5),
        "type": "numeric",
    },

    "Non-HDL Cholesterol": {
        "aliases": ["Non HDL Cholesterol", "Non-HDL Cholesterol", "Non-HDL-C", "NonHDL"],
        "unit": "mg/dL",
        "category": "diabetes_metabolic",    
        "normal": (0, 130),
        "type": "numeric",
    },

    # ── Liver Function ────────────────────────────────────────────────────────
    "ALT": {
        "aliases": ["ALT", "SGPT", "Alanine Aminotransferase", "Alanine Transaminase"],
        "unit": "U/L",
        "category": "liver_hepatic",    
        "normal_male": (7, 56),
        "normal_female": (7, 45),
        "type": "numeric",
    },

    "AST": {
        "aliases": ["AST", "SGOT", "Aspartate Aminotransferase", "Aspartate Transaminase"],
        "unit": "U/L",
        "category": "liver_hepatic",    
        "normal": (17, 59),
        "type": "numeric",
    },

    "ALP": {
        "aliases": ["ALP", "Alkaline Phosphatase", "Alk Phos"],
        "unit": "U/L",
        "category": "liver_hepatic",    
        "normal": (44, 147),
        "type": "numeric",
    },

    "GGT": {
        "aliases": ["GGT", "Gamma GT", "Gamma Glutamyl Transferase"],
        "unit": "U/L",
        "category": "liver_hepatic",    
        "normal_male": (8, 61),
        "normal_female": (5, 36),
        "type": "numeric",
    },

    "Total Bilirubin": {
        "aliases": ["Total Bilirubin", "T.Bili", "TBIL", "Bilirubin Total",
                    "Bilirubin Total Serum"],
        "unit": "mg/dL",
        "category": "liver_hepatic",    
        "normal": (0.2, 1.3),
        "type": "numeric",
    },

    "Direct Bilirubin": {
        "aliases": ["Direct Bilirubin", "D.Bili", "DBIL", "Conjugated Bilirubin",
                    "Bilirubin Direct"],
        "unit": "mg/dL",
        "category": "liver_hepatic",    
        "normal": (0.0, 0.3),
        "type": "numeric",
    },
    # NEW: Indirect / Unconjugated Bilirubin
    "Indirect Bilirubin": {
        "aliases": ["Indirect Bilirubin", "Unconjugated Bilirubin", "Bilirubin Indirect",
                    "Indirect Bili", "I.Bili"],
        "unit": "mg/dL",
        "category": "liver_hepatic",    
        "normal": (0.0, 1.1),
        "type": "numeric",
    },
    # NEW: Delta Bilirubin
    "Delta Bilirubin": {
        "aliases": ["Delta Bilirubin", "Bilirubin Delta", "D-Bilirubin"],
        "unit": "mg/dL",
        "category": "liver_hepatic",    
        "normal": (0.0, 0.2),
        "type": "numeric",
    },

    "Albumin": {
        "aliases": ["Albumin", "Serum Albumin"],
        "unit": "g/dL",
        "category": "liver_hepatic",    
        "normal": (3.5, 5.0),
        "type": "numeric",
    },

    "Total Protein": {
        "aliases": ["Total Protein", "Protein Total", "Total Protein Serum"],
        "unit": "g/dL",
        "category": "liver_hepatic",    
        "normal": (6.3, 8.2),
        "type": "numeric",
    },
    # NEW: Globulin
    "Globulin": {
        "aliases": ["Globulin", "Serum Globulin", "Total Globulin"],
        "unit": "g/dL",
        "category": "liver_hepatic",    
        "normal": (2.3, 3.5),
        "type": "numeric",
    },
    # NEW: Albumin/Globulin Ratio
    "A/G Ratio": {
        "aliases": ["A/G Ratio", "AG Ratio", "Albumin Globulin Ratio",
                    "Albumin/Globulin Ratio"],
        "unit": "",
        "category": "liver_hepatic",    
        "normal": (1.3, 1.7),
        "type": "numeric",
    },

    # ── Thyroid ───────────────────────────────────────────────────────────────
    "TSH": {
        "aliases": ["TSH", "Thyroid Stimulating Hormone", "Thyrotropin",
                    "TSH - Thyroid Stimulating Hormone"],
        "unit": "µIU/mL",
        "category": "thyroid",    
        "normal": (0.35, 4.94),
        "type": "numeric",
    },
    # NEW: Total T3 (distinct from Free T3)
    "T3 Total": {
        "aliases": ["T3", "T3 Total", "Total T3", "Triiodothyronine",
                    "T3 - Triiodothyronine", "T3-Triiodothyronine"],
        "unit": "ng/mL",
        "category": "thyroid",    
        "normal": (0.58, 1.59),
        "type": "numeric",
    },

    "Free T3": {
        "aliases": ["FT3", "Free T3", "fT3", "Free Triiodothyronine"],
        "unit": "pg/mL",
        "category": "thyroid",    
        "normal": (2.3, 4.2),
        "type": "numeric",
    },
    # NEW: Total T4 (distinct from Free T4)
    "T4 Total": {
        "aliases": ["T4", "T4 Total", "Total T4", "Thyroxine",
                    "T4 - Thyroxine", "T4-Thyroxine"],
        "unit": "µg/dL",
        "category": "thyroid",    
        "normal": (4.87, 11.72),
        "type": "numeric",
    },

    "Free T4": {
        "aliases": ["FT4", "Free T4", "fT4", "Free Thyroxine"],
        "unit": "ng/dL",
        "category": "thyroid",    
        "normal": (0.8, 1.8),
        "type": "numeric",
    },

    # ── Iron Studies ──────────────────────────────────────────────────────────
    "Ferritin": {
        "aliases": ["Ferritin", "Serum Ferritin"],
        "unit": "ng/mL",
        "category": "blood_cbc",    
        "normal_male": (24, 336),
        "normal_female": (11, 307),
        "type": "numeric",
    },

    "Serum Iron": {
        "aliases": ["Serum Iron", "Iron", "Iron Serum", "Fe", "S.Iron"],
        "unit": "µg/dL",
        "category": "blood_cbc",    
        "normal": (49, 181),
        "type": "numeric",
    },
    # NEW: TIBC
    "TIBC": {
        "aliases": ["TIBC", "Total Iron Binding Capacity", "Total Iron Binding Capacity (TIBC)"],
        "unit": "µg/dL",
        "category": "blood_cbc",    
        "normal": (261, 462),
        "type": "numeric",
    },
    # NEW: Transferrin Saturation
    "Transferrin Saturation": {
        "aliases": ["Transferrin Saturation", "TSAT", "Transferrin Sat",
                    "Iron Saturation", "% Transferrin Saturation"],
        "unit": "%",
        "category": "blood_cbc",    
        "normal": (20, 50),
        "type": "numeric",
    },

    # ── Vitamins ──────────────────────────────────────────────────────────────
    "Vitamin B12": {
        "aliases": ["Vitamin B12", "B12", "Cobalamin", "Cyanocobalamin"],
        "unit": "pg/mL",
        "category": "nutritional",    
        "normal": (187, 833),
        "type": "numeric",
    },

    "Vitamin D": {
        "aliases": ["Vitamin D", "25-OH Vitamin D", "25-Hydroxyvitamin D", "Vit D",
                    "25(OH) Vitamin D", "Vitamin D3", "25 OH Vitamin D"],
        "unit": "ng/mL",
        "category": "nutritional",    
        "normal": (30, 100),
        "type": "numeric",
    },

    # ── Coagulation ───────────────────────────────────────────────────────────
    "PT/INR": {
        "aliases": ["INR", "Prothrombin Time", "PT/INR"],
        "unit": "INR",
        "category": "blood_cbc",    
        "normal": (0.8, 1.2),
        "type": "numeric",
    },

    "aPTT": {
        "aliases": ["aPTT", "APTT", "Activated Partial Thromboplastin Time"],
        "unit": "sec",
        "category": "blood_cbc",    
        "normal": (25, 35),
        "type": "numeric",
    },

    # ── Inflammation ──────────────────────────────────────────────────────────
    "CRP": {
        "aliases": ["CRP", "C-Reactive Protein", "hs-CRP", "hsCRP"],
        "unit": "mg/L",
        "category": "blood_cbc",    
        "normal": (0, 5),
        "type": "numeric",
    },

    "ESR": {
        "aliases": ["ESR", "Erythrocyte Sedimentation Rate", "Sed Rate"],
        "unit": "mm/hr",
        "category": "blood_cbc",    
        "normal_male": (0, 14),
        "normal_female": (0, 20),
        "type": "numeric",
    },
    # NEW: Homocysteine
    "Homocysteine": {
        "aliases": ["Homocysteine", "Homocysteine Serum", "tHcy", "Total Homocysteine",
                    "Homocysteine, Serum"],
        "unit": "µmol/L",
        "category": "nutritional",    
        "normal": (6.0, 14.8),
        "type": "numeric",
    },

    # ── Other ─────────────────────────────────────────────────────────────────
    # NEW: PSA
    "PSA": {
        "aliases": ["PSA", "PSA Total", "Prostate Specific Antigen",
                    "PSA-Prostate Specific Antigen", "PSA-Prostate Specific Antigen, Total"],
        "unit": "ng/mL",
        "category": "general_wellness",    
        "normal": (0, 4.0),
        "type": "numeric",
    },
    # NEW: IgE
    "IgE": {
        "aliases": ["IgE", "Total IgE", "Immunoglobulin E", "Serum IgE"],
        "unit": "IU/mL",
        "category": "blood_cbc",    
        "normal": (0, 87),
        "type": "numeric",
    },

    # ── Absolute Differential Counts ──────────────────────────────────────────
    "Absolute Neutrophil Count": {
        "aliases": ["Absolute Neutrophil Count", "ANC", "Neutrophils Absolute",
                    "Neutrophil Absolute Count", "Abs Neutrophil"],
        "unit": "/cmm",
        "category": "blood_cbc",    
        "normal": (2000, 6700),
        "type": "numeric",
    },

    "Absolute Lymphocyte Count": {
        "aliases": ["Absolute Lymphocyte Count", "ALC", "Lymphocytes Absolute",
                    "Lymphocyte Absolute Count", "Abs Lymphocyte"],
        "unit": "/cmm",
        "category": "blood_cbc",    
        "normal": (1100, 3300),
        "type": "numeric",
    },

    "Absolute Eosinophil Count": {
        "aliases": ["Absolute Eosinophil Count", "AEC", "Eosinophils Absolute",
                    "Eosinophil Absolute Count", "Abs Eosinophil"],
        "unit": "/cmm",
        "category": "blood_cbc",    
        "normal": (0, 400),
        "type": "numeric",
    },

    "Absolute Monocyte Count": {
        "aliases": ["Absolute Monocyte Count", "AMC", "Monocytes Absolute",
                    "Monocyte Absolute Count", "Abs Monocyte"],
        "unit": "/cmm",
        "category": "blood_cbc",    
        "normal": (200, 700),
        "type": "numeric",
    },

    "Absolute Basophil Count": {
        "aliases": ["Absolute Basophil Count", "ABC", "Basophils Absolute",
                    "Basophil Absolute Count", "Abs Basophil"],
        "unit": "/cmm",
        "category": "blood_cbc",    
        "normal": (0, 100),
        "type": "numeric",
    },

    # ── Blood Group ───────────────────────────────────────────────────────────
    # qualitative type: value is text like "A", "B", "O", "AB", "Positive", "Negative"
    "ABO Type": {
        "aliases": ["ABO Type", "ABO Blood Group", "Blood Group ABO", "Blood Type ABO"],
        "unit": "",
        "category": "blood_cbc",    
        "normal": None,
        "type": "qualitative",
    },

    "Rh Type": {
        "aliases": ["Rh Type", "Rh (D) Type", "RhD", "Rh Factor", "Rh(D)",
                    "Rh D Type", "Rhesus Factor"],
        "unit": "",
        "category": "blood_cbc",  
        "normal": None,
        "type": "qualitative",
    },

    # ── Urine Physical / Chemical (Dipstick) ──────────────────────────────────
    "Urine pH": {
        "aliases": ["Urine pH", "pH Urine", "Urinary pH"],
        "unit": "",
        "category": "kidney_renal",
        "normal": (4.6, 8.0),
        "type": "numeric",
    },

    "Urine Specific Gravity": {
        "aliases": ["Specific Gravity", "Urine Specific Gravity", "SG Urine",
                    "Urine SG", "S.G."],
        "unit": "",
        "category": "kidney_renal",
        "normal": (1.005, 1.030),
        "type": "numeric",
    },

    "Urine Glucose": {
        "aliases": ["Urine Glucose", "Glucose Urine", "Glucosuria",
                    "Urinary Glucose"],
        "unit": "",
        "category": "diabetes_metabolic",
        "normal": None,
        "type": "qualitative",
    },

    "Urine Protein": {
        "aliases": ["Urine Protein", "Protein Urine", "Urinary Protein",
                    "Proteinuria"],
        "unit": "",
        "category": "kidney_renal",
        "normal": None,
        "type": "qualitative",
    },

    "Urine Bilirubin": {
        "aliases": ["Urine Bilirubin", "Bilirubin Urine", "Bilirubin (urine)",
                    "Urinary Bilirubin"],
        "unit": "",
        "category": "liver_hepatic",
        "normal": None,
        "type": "qualitative",
    },

    "Urobilinogen": {
        "aliases": ["Urobilinogen", "Urine Urobilinogen", "Urobilinogen Urine"],
        "unit": "",
        "category": "liver_hepatic",
        "normal": None,
        "type": "qualitative",
    },

    "Urine Ketone": {
        "aliases": ["Urine Ketone", "Ketone Urine", "Ketones Urine",
                    "Urine Ketones", "Ketonuria"],
        "unit": "",
        "category": "diabetes_metabolic",
        "normal": None,
        "type": "qualitative",
    },

    "Urine Nitrite": {
        "aliases": ["Urine Nitrite", "Nitrite Urine", "Nitrite"],
        "unit": "",
        "category": "blood_cbc",
        "normal": None,
        "type": "qualitative",
    },

    # ── Urine Microscopy ──────────────────────────────────────────────────────
    "Pus Cells": {
        "aliases": ["Pus Cells", "WBC Urine", "Urine WBC", "Leukocyte Esterase",
                    "Pus Cells Urine"],
        "unit": "/hpf",
        "category": "blood_cbc",  
        "normal": (0, 2),
        "type": "numeric",
    },

    "Urine RBC": {
        "aliases": ["Red Cells", "Urine RBC", "RBC Urine", "Red Blood Cells Urine",
                    "Urine Red Cells"],
        "unit": "/hpf",
        "category": "kidney_renal", 
        "normal": (0, 2),
        "type": "numeric",
    },

    "Epithelial Cells": {
        "aliases": ["Epithelial Cells", "Epithelial Cells Urine",
                    "Squamous Epithelial Cells"],
        "unit": "/hpf",
        "category": "kidney_renal", 
        "normal": None,
        "type": "numeric",
    },

    "Casts": {
        "aliases": ["Casts", "Urine Casts", "Urinary Casts",
                    "Hyaline Casts"],
        "unit": "/hpf",
        "category": "kidney_renal", 
        "normal": None,
        "type": "qualitative",
    },

    "Crystals": {
        "aliases": ["Crystals", "Urine Crystals", "Urinary Crystals"],
        "unit": "/hpf",
        "category": "kidney_renal",  
        "normal": None,
        "type": "qualitative",
    },

    # ── Infection / Serology ──────────────────────────────────────────────────
    "HIV Ag/Ab": {
        "aliases": ["HIV I & II Ab/Ag with P24 Ag", "HIV Ag/Ab", "HIV 1 & 2",
                    "HIV Antibody", "HIV Antigen", "HIV I II", "Anti HIV"],
        "unit": "S/Co",
        "category": "blood_cbc", 
        "normal": (0, 1.0),
        "type": "numeric",
    },

    "HBsAg": {
        "aliases": ["HBsAg", "Hepatitis B Surface Antigen", "HBs Antigen",
                    "Hepatitis B sAg", "HBs Ag"],
        "unit": "S/Co",
        "category": "blood_cbc", 
        "normal": (0, 1.0),
        "type": "numeric",
    },

    # ── HB Electrophoresis Peaks ──────────────────────────────────────────────
    "P2 Peak": {
        "aliases": ["P2 Peak", "P2", "HbP2", "Hb P2 Peak"],
        "unit": "%",
        "category": "blood_cbc",  
        "normal": (0, 10),
        "type": "numeric",
    },

    "P3 Peak": {
        "aliases": ["P3 Peak", "P3", "HbP3", "Hb P3 Peak"],
        "unit": "%",
        "category": "blood_cbc",    
        "normal": (0, 10),
        "type": "numeric",
    },
}