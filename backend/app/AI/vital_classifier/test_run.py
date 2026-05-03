from .pipeline import process_user_query
import json


def run_test():
    user_id = 8
    query = "Should I be eating 5 donuts daily?"

    result = process_user_query(user_id, query)

    print("\n===== FINAL OUTPUT =====\n")

    print(json.dumps(result, indent=2))  # 👈 clean JSON output


if __name__ == "__main__":
    run_test()