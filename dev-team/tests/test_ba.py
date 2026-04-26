"""LLM-as-a-Judge tests for the Business Analyst agent.

Tests that BA produces complete, well-structured specifications
with testable acceptance criteria.
"""

import pytest

from agents.ba import run_ba
from tests.conftest import llm_judge


@pytest.mark.parametrize(
    "user_story",
    [
        "As a user, I want to register via email so that I can create an account",
        "As a user, I want to reset my password via email link",
        "As a user, I want to see a list of my orders sorted by date",
    ],
    ids=["registration", "password-reset", "order-list"],
)
def test_ba_spec_completeness(user_story: str):
    """BA should produce a spec with clear requirements and testable acceptance criteria."""
    spec = run_ba(user_story)

    spec_text = (
        f"Title: {spec.title}\n"
        f"Complexity: {spec.estimated_complexity}\n"
        f"Requirements:\n" + "\n".join(f"- {r}" for r in spec.requirements) + "\n"
        f"Acceptance Criteria:\n" + "\n".join(f"- {ac}" for ac in spec.acceptance_criteria)
    )

    result = llm_judge(
        criteria=(
            "Evaluate the specification for completeness:\n"
            "1. Are requirements clear, specific, and non-ambiguous?\n"
            "2. Do acceptance criteria cover happy path, edge cases, and error handling?\n"
            "3. Are acceptance criteria testable (can be verified with code)?\n"
            "4. Is the complexity estimate reasonable?\n"
            "5. Does the spec cover validation and security considerations?"
        ),
        input_text=user_story,
        output_text=spec_text,
        threshold=0.6,
    )

    print(f"\n  Score: {result.score:.2f} | {result.reasoning}")
    assert result.passed, f"BA spec quality too low: {result.score:.2f} — {result.reasoning}"


def test_ba_handles_vague_story():
    """BA should still produce a reasonable spec from a vague user story."""
    vague_story = "I want login"

    spec = run_ba(vague_story)

    assert spec.title, "Spec must have a title"
    assert len(spec.requirements) >= 2, "Even vague stories should yield multiple requirements"
    assert len(spec.acceptance_criteria) >= 2, "Must have acceptance criteria"

    result = llm_judge(
        criteria=(
            "The BA received a very vague user story. Evaluate whether the BA:\n"
            "1. Interpreted the vague request reasonably\n"
            "2. Added necessary details (authentication method, validation, etc.)\n"
            "3. Produced testable acceptance criteria despite vague input"
        ),
        input_text=vague_story,
        output_text=f"Requirements: {spec.requirements}\nAC: {spec.acceptance_criteria}",
        threshold=0.5,
    )

    print(f"\n  Score: {result.score:.2f} | {result.reasoning}")
    assert result.passed, f"BA failed on vague story: {result.reasoning}"
