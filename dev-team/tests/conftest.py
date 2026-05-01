"""Shared fixtures and LLM-as-a-Judge helper for tests."""

import json

import pytest
from config import Settings
from langchain_openai import ChatOpenAI
from schemas import JudgeResult

settings = Settings()


def llm_judge(
    criteria: str, input_text: str, output_text: str, threshold: float = 0.6
) -> JudgeResult:
    """Call LLM to evaluate output against criteria.

    Returns JudgeResult with score, reasoning, and pass/fail.
    """
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        api_key=settings.openai_api_key.get_secret_value(),
        temperature=0,
    )

    prompt = f"""You are an expert evaluator. Score the OUTPUT based on the CRITERIA below.

CRITERIA:
{criteria}

INPUT:
{input_text}

OUTPUT:
{output_text}

Respond with a JSON object:
{{
    "score": <float 0.0 to 1.0>,
    "reasoning": "<brief explanation of the score>",
    "passed": <true if score >= {threshold}, false otherwise>
}}

Return ONLY valid JSON, no markdown fences."""

    response = llm.invoke(prompt)
    data = json.loads(response.content)

    return JudgeResult(
        score=data["score"],
        reasoning=data["reasoning"],
        passed=data["passed"],
    )


@pytest.fixture
def judge():
    """Provide the llm_judge function as a fixture."""
    return llm_judge
