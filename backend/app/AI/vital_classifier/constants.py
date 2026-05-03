BUCKETS = ["cardiovascular", "diabetes_metabolic", "blood_cbc", "liver_hepatic", "kidney_renal", "electrolytes", "thyroid", "nutritional", "respiratory", "hormonal", "general_wellness"]


#not correct yet
BUCKET_TO_FIELDS = {
    "cardio": ["bp_systolic", "bp_diastolic", "heart_rate", "ldl", "hdl", "triglycerides"],
    "diabetes": ["glucose", "hba1c"],
    "blood": ["hemoglobin", "wbc", "rbc", "platelets"],
    "liver": ["alt", "ast", "bilirubin"],
    "kidney": ["creatinine", "urea", "egfr"],
    "electrolytes": ["sodium", "potassium", "calcium"],
    "thyroid": ["tsh", "t3", "t4"],
    "vitamins": ["vitamin_d", "vitamin_b12", "iron"],
    "respiratory": ["spo2"],
    "general": []
}