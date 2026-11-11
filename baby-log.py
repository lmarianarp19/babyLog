import json
import re
import sys

import anthropic

client = anthropic.Anthropic(
    default_headers={"anthropic-workspace-id": "wrkspc_01HSHfFvEmQsB68Ggye1B3k3"}
)

test_entries = [
    "fed on the left side, 15 minutes",
    "fed on the left for like 10 min then right, maybe 10 more",
    "nursed, not sure how long",
    "bottle of 3 oz pumped milk",
    "fed 15 minutes",
    "fed left 10 min, not interested, then 2 oz bottle",
]


def build_prompt(entry):
    return (
        "Extract this feeding entry as JSON with these keys:\n"
        "- method: 'breast', 'bottle', or 'breast_and_bottle'. "
        "If the entry says it outright (e.g. 'nursed', 'breastfed', 'bottle'), use that. "
        "Otherwise: if it mentions nursing or a side AND a bottle or ounces, "
        "use 'breast_and_bottle'. If it mentions a side, use 'breast'. "
        "If it mentions ounces, use 'bottle'. "
        "If it mentions only minutes, use 'breast' and add 'method' to uncertain. "
        "For 'breast_and_bottle', the side and duration fields describe the nursing "
        "part and oz_given describes the bottle part.\n"
        "- first_side: the side the feed started on: 'left', 'right', or null. "
        "If the entry mentions only one side, that is the first side. "
        "If it mentions both, the first side is the one mentioned first. "
        "Use null only if no side is mentioned.\n"
        "- duration_left: minutes on the left side, or null\n"
        "- duration_right: minutes on the right side, or null\n"
        "- duration_min_total: total minutes of the feed, or null. "
        "If both duration_left and duration_right are given, "
        "this is their sum. If only one side's duration is given, "
        "this equals that side's duration.\n"
        "- oz_given: ounces the baby drank, or null\n"
        "- uncertain: list of field names the entry did not state clearly\n\n"
        "Rules: never guess a value. Use null if it isn't stated. "
        "Return only the JSON, with no extra text.\n\n"
        f"Entry: {entry}"
    )


FENCE_RE = re.compile(r"^```(?:json)?\s*\n(.*?)\n?```$", re.DOTALL)


def parse_reply(text):
    """Return the parsed JSON object from the model's reply.

    Strips a ```json ... ``` wrapper if present. Raises ValueError
    if what's left isn't a valid JSON object.
    """
    text = text.strip()
    match = FENCE_RE.match(text)
    if match:
        text = match.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"not valid JSON: {err}") from None
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object, got {type(data).__name__}")
    return data


failures = 0

for entry in test_entries:
    print("entry:", entry, file=sys.stderr)
    message = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=900,
        messages=[{
            "role": "user",
            "content": build_prompt(entry),
        }],
    )

    print("stop_reason:", message.stop_reason, file=sys.stderr)
    print("block types:", [block.type for block in message.content], file=sys.stderr)

    reply = "".join(block.text for block in message.content if block.type == "text")

    if message.stop_reason != "end_turn":
        print(f"ERROR: reply incomplete (stop_reason={message.stop_reason})", file=sys.stderr)
        print("raw reply:", reply, file=sys.stderr)
        failures += 1
        continue

    try:
        data = parse_reply(reply)
    except ValueError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        print("raw reply:", reply, file=sys.stderr)
        failures += 1
        continue

    print(json.dumps(data, indent=2), flush=True)
    print(file=sys.stderr)

if failures:
    print(f"{failures} of {len(test_entries)} entries failed", file=sys.stderr)
    sys.exit(1)
