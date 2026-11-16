"""Tests for baby_log.py.

    python3 test_baby_log.py            # all tests (calls the API)
    python3 test_baby_log.py --offline  # only the parse tests (free, instant)
"""

import sys

from baby_log import FeedError, extract_feed, parse_reply

# Each entry is paired with the values the model should return.
# "uncertain_includes" lists field names that must appear in "uncertain";
# other names may appear too, since that part of the reply varies run to run.
test_entries = [
    ("fed on the left side, 15 minutes", {
        "method": "breast", "first_side": "left",
        "duration_left": 15, "duration_right": None, "duration_min_total": 15,
        "oz_given": None,
    }),
    ("fed on the left for like 10 min then right, maybe 10 more", {
        "method": "breast", "first_side": "left",
        "duration_left": 10, "duration_right": 10, "duration_min_total": 20,
        "oz_given": None,
    }),
    ("nursed, not sure how long", {
        "method": "breast", "first_side": None,
        "duration_left": None, "duration_right": None, "duration_min_total": None,
        "oz_given": None,
    }),
    ("bottle of 3 oz pumped milk", {
        "method": "bottle", "first_side": None,
        "duration_left": None, "duration_right": None, "duration_min_total": None,
        "oz_given": 3,
    }),
    ("fed 15 minutes", {
        "method": "breast", "first_side": None,
        "duration_left": None, "duration_right": None, "duration_min_total": 15,
        "oz_given": None,
        "uncertain_includes": ["method"],
    }),
    ("fed left 10 min, not interested, then 2 oz bottle", {
        "method": "breast_and_bottle", "first_side": "left",
        "duration_left": 10, "duration_right": None, "duration_min_total": 10,
        "oz_given": 2,
    }),
]

# Hand-made model replies for parse_reply: (name, reply, should_parse)
parse_cases = [
    ("plain", '{"method": "bottle", "oz_given": 3}', True),
    ("fenced json", '```json\n{\n  "method": "breast"\n}\n```', True),
    ("fenced no lang", '```\n{"method": "breast"}\n```', True),
    ("whitespace around", '  \n{"method": "breast"}\n  ', True),
    ("truncated", '{"method": "breast", "first_si', False),
    ("extra text", 'Here is the JSON: {"method": "breast"}', False),
    ("a list", "[1, 2]", False),
    ("empty", "", False),
]


def check_feed(feed, expected):
    """Return a list of differences between the model's reply and what we expect."""
    problems = []
    for field, want in expected.items():
        if field == "uncertain_includes":
            missing = [name for name in want if name not in feed.get("uncertain", [])]
            if missing:
                problems.append(f"uncertain is missing {missing} (got {feed.get('uncertain')})")
        elif feed.get(field) != want:
            problems.append(f"{field}: expected {want!r}, got {feed.get(field)!r}")
    return problems


def run_parse_tests():
    failures = 0
    print("parse_reply tests")
    for name, reply, should_parse in parse_cases:
        try:
            parse_reply(reply)
            parsed = True
        except ValueError:
            parsed = False
        ok = parsed == should_parse
        failures += not ok
        expectation = "accepted" if should_parse else "rejected"
        print(f"  {'PASS' if ok else 'FAIL'}  {name} (should be {expectation})")
    return failures


def run_entry_tests():
    failures = 0
    print("model tests (calls the API)")
    for entry, expected in test_entries:
        try:
            problems = check_feed(extract_feed(entry), expected)
        except FeedError as err:
            problems = [f"{err} | raw reply: {err.raw_reply!r}"]
        failures += bool(problems)
        print(f"  {'FAIL' if problems else 'PASS'}  {entry}")
        for problem in problems:
            print(f"          {problem}")
    return failures


if __name__ == "__main__":
    failures = run_parse_tests()
    if "--offline" not in sys.argv:
        print()
        failures += run_entry_tests()
    print()
    print("all passed" if failures == 0 else f"{failures} failed")
    sys.exit(1 if failures else 0)
