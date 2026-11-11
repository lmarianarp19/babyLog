# Baby log

A small Python script that turns a short spoken or typed feeding entry into structured JSON.

## Current state
- `baby-log.py` sends each entry in `test_entries` to the Claude API, checks the reply is valid JSON (stripping ```json fences), and prints it.
- Uses `claude-haiku-5-5` with the `anthropic` Python package.
- The API key is read from the `ANTHROPIC_API_KEY` environment variable. Never hardcode it.

## Feed fields
- method: 'breast', 'bottle', or 'breast_and_bottle' (e.g. tried nursing, then a bottle top-up)
  - If the entry states the method outright ("nursed", "breastfed", "bottle"), use that.
  - Nursing or a side AND a bottle or ounces → 'breast_and_bottle'.
  - A side → 'breast'. Ounces → 'bottle'.
  - Only minutes → 'breast', with 'method' added to uncertain.
  - For 'breast_and_bottle', the side and duration fields describe the nursing part; oz_given describes the bottle part.
- first_side: 'left', 'right', or null. If one side is mentioned, that's the first side; if both, the one mentioned first; null only if no side is mentioned.
- duration_left: minutes on the left side, or null
- duration_right: minutes on the right side, or null
- duration_min_total: total minutes, or null. When both sides are given, it is duration_left + duration_right. When only one side is given, it equals that side's duration.
- oz_given: ounces the baby drank, or null
- uncertain: list of field names the entry did not state clearly

## Rules
- Never guess a value. Use null when it isn't stated.
- Pumping is a separate event type and is out of scope for now.
- This is a tracking tool, not medical advice.

## Test entries
The test entries live in the `test_entries` list in `baby-log.py`. Add or change them there.