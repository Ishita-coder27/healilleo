import json
from .constants import BUCKETS

VALID_BUCKETS = set(BUCKETS)

def parse_and_validate(output: str):
    try:
        data = json.loads(output)

        if not isinstance(data, list):
            return ["general"]

        cleaned = [b for b in data if b in VALID_BUCKETS]

        return cleaned if cleaned else ["general"]

    except Exception:
        return ["general"]