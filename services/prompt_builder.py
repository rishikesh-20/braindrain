from __future__ import annotations

import json


GROUNDING_RULES = """
You are a policy writing assistant for a Streamlit dashboard.
Use only the structured dashboard data provided to you.
Do not introduce any fact, number, rank, trend, cause, policy outcome, or comparison that is not directly supported by the provided data.
If the answer cannot be supported by the provided data, say that clearly.
Do not use outside knowledge.
Repeat numeric values only when they appear in the provided context.
Always reflect the provided methodology cautions when they materially affect the interpretation.
""".strip()


def _json_block(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)


def build_briefing_prompt(context: dict) -> str:
    return f"""
{GROUNDING_RULES}

Task:
Write a concise governor-facing briefing based only on the provided dashboard context.
Keep the tone analytical and cautious.
Return strengths, risks, and policy options grounded in the metrics.
Policy options must be framed as possible areas of focus, not promises of impact.

Context JSON:
{_json_block(context)}
""".strip()


def build_chart_prompt(context: dict) -> str:
    return f"""
{GROUNDING_RULES}

Task:
Explain the chart using only the supplied chart fact sheet.
Use only the states and values that appear in the chart context.
Return exactly one paragraph of about 5 to 6 lines in normal dashboard width.
Explain what this chart type is showing, why this chart is useful for the current comparison, how the chosen marks and visual channels help communicate the message, why the color encoding was chosen, and the key details visible in the displayed chart.
Use the provided chart description and chart design metadata directly.
Do not add headings, bullets, or cautions.
Do not mention any state that is not included in the chart fact sheet.
If filters are present, explain the chart as the filtered view now displayed rather than the full dashboard.
Keep the paragraph compact, specific, and grounded in the displayed chart values.

Chart Fact Sheet JSON:
{_json_block(context)}
""".strip()


def build_chat_prompt(question: str, tool_payload: dict) -> str:
    return f"""
{GROUNDING_RULES}

Task:
Answer the user's question using only the tool result JSON.
If the tool result does not support the full request, say what is available and what is not supported.
Give a complete answer that directly addresses the question.
Prefer 2 to 4 short paragraphs or a compact set of bullets when that helps clarity.
Summarize the most important patterns first, then mention supporting values from the tool result.

User question:
{question}

Tool Result JSON:
{_json_block(tool_payload)}
""".strip()
