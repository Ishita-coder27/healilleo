# app/AI/vital_classifier/session_store.py
from threading import Lock
from collections import defaultdict

_lock = Lock()

# Keyed by user_id (int)
# Each entry: { "vitals": {name: formatted_str}, "seen_buckets": set(), "summary": {...} }
_sessions: dict[int, dict] = defaultdict(lambda: {
    "vitals": {},
    "seen_buckets": set(),
    "summary": {
        "issues": [],
        "advice_given": [],
        "observations": []
    }
})


def get_session(user_id: int) -> dict:
    with _lock:
        return _sessions[user_id]


def get_cached_vitals(user_id: int) -> dict:
    with _lock:
        return dict(_sessions[user_id]["vitals"])


def get_seen_buckets(user_id: int) -> set:
    with _lock:
        return set(_sessions[user_id]["seen_buckets"])


def update_session(user_id: int, new_vitals: dict, buckets: list, summary_update: dict = None):
    with _lock:
        _sessions[user_id]["vitals"].update(new_vitals)
        _sessions[user_id]["seen_buckets"].update(buckets)
        if summary_update:
            s = _sessions[user_id]["summary"]
            for key in ("issues", "advice_given", "observations"):
                existing = set(s.get(key, []))
                existing.update(summary_update.get(key, []))
                s[key] = list(existing)


def update_summary(user_id: int, summary_update: dict):
    with _lock:
        s = _sessions[user_id]["summary"]
        for key in ("issues", "advice_given", "observations"):
            existing = set(s.get(key, []))
            existing.update(summary_update.get(key, []))
            s[key] = list(existing)


def get_summary(user_id: int) -> dict:
    with _lock:
        return dict(_sessions[user_id]["summary"])


def clear_session(user_id: int):
    with _lock:
        _sessions[user_id] = {
            "vitals": {},
            "seen_buckets": set(),
            "summary": {"issues": [], "advice_given": [], "observations": []}
        }