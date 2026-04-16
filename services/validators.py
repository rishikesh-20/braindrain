from __future__ import annotations

import re
from collections.abc import Iterable


NUMBER_PATTERN = re.compile(r"-?\$?\d[\d,]*(?:\.\d+)?%?")


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
    token = token.replace("$", "").replace("%", "").replace(",", "").strip()
    if not token:
        return token
    try:
        return str(float(token))
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
        if numeric_value is not None and any(_is_close_enough(numeric_value, candidate) for candidate in allowed_numeric):
            continue
        invalid.append(token)
    return (len(invalid) == 0, invalid)
