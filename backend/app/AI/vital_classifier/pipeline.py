# app/AI/vital_classifier/pipeline.py
from .classifier import classify_query
from .retriever import get_vitals_for_buckets, format_vitals
from .response_llm import generate_response
from . import session_store
from app.core.bucket_store import bucket_map
import json


def process_user_query(user_id: int, query: str, context_summary: dict = None):

    buckets = classify_query(query)
    print(f"[PIPELINE] user_id={user_id} | buckets={buckets}")

    cached_vitals = session_store.get_cached_vitals(user_id)
    seen_buckets = session_store.get_seen_buckets(user_id)

    # ── Conversational query detection ──────────────────────────
    # If classifier returned only general/general_wellness AND we have
    # cached vitals, treat it as a conversational query and use everything
    CONVERSATIONAL_BUCKETS = {"general", "general_wellness"}
    is_conversational = (
        set(buckets).issubset(CONVERSATIONAL_BUCKETS)
        and len(cached_vitals) > 0
    )

    if is_conversational:
        print(f"[PIPELINE] conversational query detected — using all cached vitals")
        session_summary = session_store.get_summary(user_id)
        effective_summary = context_summary or session_summary

        print(f"[LLM INPUT] query='{query}'")
        print(f"[LLM INPUT] vitals passed={json.dumps(cached_vitals, indent=2)}")
        print(f"[LLM INPUT] summary={json.dumps(effective_summary, indent=2)}")

        answer, summary_update = generate_response(query, cached_vitals, effective_summary)

        print(f"[LLM OUTPUT] answer={answer}")

        if summary_update:
            session_store.update_summary(user_id, summary_update)

        return {
            "buckets": buckets,
            "vitals": cached_vitals,
            "answer": answer,
            "summary": summary_update or {},
            "cached_vitals_used": list(cached_vitals.keys()),
        }
    # ────────────────────────────────────────────────────────────

    # ... rest of pipeline unchanged from here

    new_buckets = [b for b in buckets if b not in seen_buckets]
    print(f"[PIPELINE] new_buckets={new_buckets}")  # ← add

    all_required_vitals = []
    for b in buckets:
        all_required_vitals.extend(bucket_map.get(b, []))
    print(f"[PIPELINE] all_required_vitals={all_required_vitals}")  # ← add

    missing_vitals_names = [v for v in all_required_vitals if v not in cached_vitals]

    newly_fetched = {}
    if missing_vitals_names:
        raw_rows = get_vitals_for_buckets(user_id, new_buckets if new_buckets else buckets)
        all_fetched = format_vitals(raw_rows)

        # Normalize: build a lookup from lowercase → fetched value
        all_fetched_lower = {k.lower().replace(" ", "_"): v for k, v in all_fetched.items()}

        # Match bucket_map names against DB names case-insensitively
        for vital in missing_vitals_names:
            normalized = vital.lower().replace(" ", "_")
            if normalized in all_fetched_lower:
                newly_fetched[vital] = all_fetched_lower[normalized]  # store under original name

        # newly_fetched = {k: v for k, v in all_fetched.items() if k in missing_vitals_names}
        # print(f"[PIPELINE] newly_fetched={newly_fetched}")  # ← add

    # ... rest unchanged

    # 6. Merge: cached + newly fetched → only vitals relevant to this query
    merged = {**cached_vitals, **newly_fetched}
    # Merge current bucket vitals WITH all previously cached vitals
    query_vitals = {
        **cached_vitals,          # all previously fetched vitals
        **{v: merged[v] for v in all_required_vitals if v in merged}  # current query vitals
    }

    # 7. Persist new data into session
    if newly_fetched or new_buckets:
        session_store.update_session(user_id, newly_fetched, buckets)

    # 8. Build conversation context for the LLM
    session_summary = session_store.get_summary(user_id)
    effective_summary = context_summary or session_summary

    # 9. Call LLM
    print(f"[LLM INPUT] query='{query}'")
    print(f"[LLM INPUT] vitals passed={json.dumps(query_vitals, indent=2)}")
    print(f"[LLM INPUT] summary={json.dumps(effective_summary, indent=2)}")
    answer, summary_update = generate_response(query, query_vitals, effective_summary)
    print(f"[LLM OUTPUT] answer={answer}")

    # 10. Persist any new summary observations
    if summary_update:
        session_store.update_summary(user_id, summary_update)

    return {
        "buckets": buckets,
        "vitals": query_vitals,
        "answer": answer,
        "summary": summary_update or {},
        "cached_vitals_used": list(set(all_required_vitals) & set(cached_vitals.keys())),
    }