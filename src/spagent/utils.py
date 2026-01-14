import json
import re
from typing import Any


def extract_first_json_block(text: str) -> str | None:
    """
    Attempts to extract the first {...} or [...] JSON block from text.
    Useful when model adds explanations or truncates output.
    """
    if not text:
        return None

    # Remove markdown fences if present
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()

    # Try object first
    obj_match = re.search(r"\{.*\}", text, re.DOTALL)
    if obj_match:
        return obj_match.group(0)

    # Try array fallback
    arr_match = re.search(r"\[.*\]", text, re.DOTALL)
    if arr_match:
        return arr_match.group(0)

    return None


def normalize_llm_json(text: str) -> dict:
    """
    Accepts:
      - valid JSON object
      - valid JSON array
      - markdown wrapped JSON
      - partial junk before/after JSON
    Returns:
      - {'events': [...]}
    Raises:
      - ValueError if unrecoverable
    """

    if not text or text.strip().lower() in ("null", ""):
        return {"events": []}

    candidate = text.strip()

    # 1️⃣ Try direct parse first (fast path)
    try:
        obj: Any = json.loads(candidate)
    except json.JSONDecodeError:
        # 2️⃣ Try extracting first JSON block
        extracted = extract_first_json_block(candidate)
        if not extracted:
            raise ValueError("No JSON block found in model output")

        try:
            obj = json.loads(extracted)
        except json.JSONDecodeError as e:
            raise ValueError("Extracted JSON still invalid") from e

    # 3️⃣ Normalize shape
    if isinstance(obj, list):
        return {"events": obj}

    if isinstance(obj, dict) and "events" in obj:
        return obj

    raise ValueError(f"Unexpected JSON shape: {type(obj)}")
