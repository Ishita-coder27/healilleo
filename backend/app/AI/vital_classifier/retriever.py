from .db import run_query
from collections import defaultdict


def get_vitals_for_buckets(user_id: int, buckets: list):
    print(f"[RETRIEVER] user_id={user_id} | buckets={buckets}")
    if not buckets:
        return []

    query = """
    SELECT 
        v.key AS vital_name,
        rv.value,
        rv.unit,
        rv.reference_range,
        rv.status,
        mr.report_date
    FROM report_vitals rv
    JOIN vitals v ON rv.vital_id = v.id
    JOIN medical_reports mr ON rv.report_id = mr.id
    WHERE mr.user_id = %s
    AND v.category = ANY(%s)
    ORDER BY mr.report_date DESC
    LIMIT 50
    """

    result = run_query(query, (user_id, buckets))

    return result


def format_vitals(rows):
    """
    Converts DB rows into compact LLM-friendly format:
    glucose → 120 mg/dL | ref: 70-110 | high | 2024-01-01
    """

    formatted = {}

    for r in rows:
        name = r["vital_name"]

        value_unit = f"{r.get('value', '')} {r.get('unit', '')}".strip()
        ref = f"ref: {r.get('reference_range', 'N/A')}"
        status = r.get("status", "unknown")
        date = r.get("report_date", "unknown")

        formatted[name] = f"{value_unit} | {ref} | {status} | {date}"

    return formatted