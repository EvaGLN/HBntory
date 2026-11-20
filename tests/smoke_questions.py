#!/usr/bin/python3
"""Examples to test the AI service and check the answers."""

import os
import sys
import requests

URL = os.environ.get("AI_URL", "http://localhost:5002") + "/ask"

QUESTIONS = [
    ("Give me details about product HB-LAP-1001", "HB-LAP-1001"),
    ("Which branch has stock of HB-LAP-1001?", None),
    ("What products can I find in Lyon?", "Lyon"),
    ("I want 3 of HB-LAP-1001 and 2 of HB-LAP-1002, where do I go?", None),
    ("Tell me about ZZZ", None),
    ("What is the capital of France?", None),
]

failed = 0
for question, expected in QUESTIONS:
    r = requests.post(URL, json={"question": question}, timeout=60)
    answer = r.json().get("answer", "")
    ok = r.status_code == 200 and answer.strip() != "" and (
        expected is None or expected in answer)
    print("OK " if ok else "FAIL", question, "->", answer[:80].replace(
        "\n", " "))
    failed += not ok
sys.exit(1 if failed else 0)
