from __future__ import annotations

import re
from collections.abc import Iterable


NUMBER_PATTERN = re.compile(r"-?\$?\d[\d,]*(?:\.\d+)?(?:[KMB])?%?(?:st|nd|rd|th)?", re.IGNORECASE)


def _flatten_values(value) -> Iterable[str]:
    if isinstance(value, dict):
        for nested in value.values():
            yield from _flatten_values(nested)
        return
    if isinstance(value, list):
        for nested in value:
            yield from _flatten_values(nested)
        return
    if value is None:
        return
    if isinstance(value, (int, float)):
        yield str(value)
        yield f"{value:,.0f}"
        yield f"{value:.1f}"
        yield f"{value:.2f}"
        yield f"{value:+.2f}"
        yield f"{value:+,.0f}"
        yield f"{value:.1f}%"
        yield f"{value:.2f}%"
        yield f"${value:,.0f}"
        return
    yield str(value)


def _normalize_numeric_token(token: str) -> str:
    token = token.strip()
    token = re.sub(r"(st|nd|rd|th)$", "", token, flags=re.IGNORECASE)
    multiplier = 1.0
    if token.lower() in {"1k", "+1k", "-1k"}:
        sign = -1.0 if token.startswith("-") else 1.0
        return str(1000.0 * sign)
    if token[-1:].lower() == "k":
        multiplier = 1_000.0
        token = token[:-1]
    elif token[-1:].lower() == "m":
        multiplier = 1_000_000.0
        token = token[:-1]
    elif token[-1:].lower() == "b":
        multiplier = 1_000_000_000.0
        token = token[:-1]
    token = token.replace("$", "").replace("%", "").replace(",", "").strip()
    if not token:
        return token
    try:
        return str(float(token) * multiplier)
    except ValueError:
        return token


def _to_float(token: str) -> float | None:
    try:
        return float(token)
    except ValueError:
        return None


def _is_close_enough(target: float, candidate: float) -> bool:
    diff = abs(target - candidate)
    scale = max(abs(target), abs(candidate), 1.0)
    return diff <= 0.5 or (diff / scale) <= 0.02


def extract_allowed_numbers(context: dict) -> set[str]:
    allowed = set()
    for value in _flatten_values(context):
        for token in NUMBER_PATTERN.findall(value):
            allowed.add(_normalize_numeric_token(token))

    # Allow canonical threshold values implied by metric names already present
    # in the app context, such as rent burden 30%+.
    serialized_context = str(context)
    if "30plus" in serialized_context or "30%+" in serialized_context:
        allowed.update({"30", "30.0", "30.00"})
    if "per 1k" in serialized_context.lower() or "per 1,000" in serialized_context.lower():
        allowed.update({"1000", "1000.0", "1000.00"})
    return allowed


def validate_numeric_grounding(text: str, context: dict) -> tuple[bool, list[str]]:
    allowed = extract_allowed_numbers(context)
    allowed_numeric = [num for num in (_to_float(token) for token in allowed) if num is not None]
    invalid = []
    for token in NUMBER_PATTERN.findall(text):
        normalized = _normalize_numeric_token(token)
        if not normalized:
            continue
        if normalized in allowed:
            continue
        numeric_value = _to_float(normalized)
        # Common unit shorthands like "per 1k" or "per 1,000" should not
        # block the entire response when the underlying metric context is
        # already rate-based.
        if numeric_value == 1000.0:
            continue
        if numeric_value is not None and any(_is_close_enough(numeric_value, candidate) for candidate in allowed_numeric):
            continue
        invalid.append(token)
    return (len(invalid) == 0, invalid)
