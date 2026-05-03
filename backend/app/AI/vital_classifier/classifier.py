from .prompts import get_classifier_prompt
from .llm_client import call_llm
from .utils import parse_and_validate

def classify_query(user_query: str):
    prompt = get_classifier_prompt(user_query)

    raw_output = call_llm(prompt)

    buckets = parse_and_validate(raw_output)

    return buckets