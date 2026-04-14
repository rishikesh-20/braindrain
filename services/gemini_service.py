from __future__ import annotations

from google import genai
from google.genai import types

from services.prompt_builder import (
    build_briefing_prompt,
    build_chart_prompt,
    build_chat_prompt,
)
from services.response_schemas import (
    BriefingResponse,
    ChartExplanationResponse,
    ChatResponse,
)
from services.validators import validate_numeric_grounding


DEFAULT_MODEL = "gemini-2.5-flash"


class GroundingValidationError(ValueError):
    """Raised when model output is not fully grounded in the provided context."""


def _client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def _generate_structured(api_key: str, prompt: str, schema: type, model: str = DEFAULT_MODEL):
    client = _client(api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    parsed = response.parsed
    if parsed is None:
        raise ValueError("Gemini returned no structured response.")
    if isinstance(parsed, schema):
        return parsed
    return schema.model_validate(parsed)


def _validate_briefing_result(result: BriefingResponse, context: dict) -> BriefingResponse:
    for field in [
        result.headline,
        result.executive_summary,
        *result.strengths,
        *result.risks,
        *result.policy_options,
        *result.cautions,
    ]:
        is_valid, invalid_numbers = validate_numeric_grounding(field, context)
        if not is_valid:
            raise GroundingValidationError(f"Ungrounded numbers in briefing output: {invalid_numbers}")
    return result


def generate_briefing(api_key: str, context: dict, model: str = DEFAULT_MODEL) -> BriefingResponse:
    primary_prompt = build_briefing_prompt(context)
    result = _generate_structured(api_key, primary_prompt, BriefingResponse, model=model)
    try:
        return _validate_briefing_result(result, context)
    except GroundingValidationError:
        retry_prompt = (
            primary_prompt
            + "\n\nExtra rule:\nIf you are unsure whether a number appears in the context, omit the number and keep the statement qualitative."
        )
        retry_result = _generate_structured(api_key, retry_prompt, BriefingResponse, model=model)
        return _validate_briefing_result(retry_result, context)


def explain_chart(api_key: str, context: dict, model: str = DEFAULT_MODEL) -> ChartExplanationResponse:
    client = _client(api_key)
    response = client.models.generate_content(
        model=model,
        contents=build_chart_prompt(context),
        config=types.GenerateContentConfig(
            temperature=0.4,
            top_p=0.9,
            response_mime_type="application/json",
            response_schema=ChartExplanationResponse,
        ),
    )
    parsed = response.parsed
    if parsed is None:
        raise ValueError("Gemini returned no structured response.")
    result = parsed if isinstance(parsed, ChartExplanationResponse) else ChartExplanationResponse.model_validate(parsed)
    paragraph = " ".join(result.paragraph.split())
    result.paragraph = paragraph
    is_valid, invalid_numbers = validate_numeric_grounding(result.paragraph, context)
    if not is_valid:
        raise GroundingValidationError(f"Ungrounded numbers in chart explanation: {invalid_numbers}")
    return result


def answer_chat_question(api_key: str, question: str, tool_payload: dict, model: str = DEFAULT_MODEL) -> ChatResponse:
    result = _generate_structured(api_key, build_chat_prompt(question, tool_payload), ChatResponse, model=model)
    for field in [result.answer, *result.cautions]:
        is_valid, invalid_numbers = validate_numeric_grounding(field, tool_payload)
        if not is_valid:
            raise GroundingValidationError(f"Ungrounded numbers in chat output: {invalid_numbers}")
    return result
