"""LLM-as-a-Judge tests for the Developer agent.

Tests that Developer produces code matching the specification.
"""

from agents.developer import run_developer
from schemas import SpecOutput

from tests.conftest import llm_judge


def _make_spec(
    title: str = "Calculator",
    requirements: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
) -> SpecOutput:
    return SpecOutput(
        title=title,
        requirements=requirements
        or [
            "Implement add, subtract, multiply, divide functions",
            "Handle division by zero with a clear error message",
            "Support both integer and float inputs",
        ],
        acceptance_criteria=acceptance_criteria
        or [
            "add(2, 3) returns 5",
            "divide(10, 0) raises ValueError with message",
            "multiply(2.5, 4) returns 10.0",
        ],
        estimated_complexity="simple",
    )


def test_developer_covers_all_requirements():
    """Developer code should implement all requirements from the spec."""
    spec = _make_spec()
    code = run_developer(spec)

    spec_text = "\n".join(f"- {r}" for r in spec.requirements)
    result = llm_judge(
        criteria=(
            "Evaluate whether the code implements ALL the specified requirements:\n"
            f"{spec_text}\n\n"
            "Check:\n"
            "1. Each requirement has a corresponding implementation\n"
            "2. Error handling is present where specified\n"
            "3. The code is syntactically valid Python\n"
            "4. Type support matches requirements (int, float)"
        ),
        input_text=f"Spec requirements:\n{spec_text}",
        output_text=f"Description: {code.description}\nFiles: {', '.join(code.files_created)}",
        threshold=0.6,
    )

    print(f"\n  Score: {result.score:.2f} | {result.reasoning}")
    assert result.passed, f"Developer missed requirements: {result.reasoning}"


def test_developer_creates_files():
    """Developer should actually create files in workspace/."""
    spec = _make_spec()
    code = run_developer(spec)

    assert code.files_created, "Developer must create at least one file"
    assert code.description, "Description must not be empty"


def test_developer_handles_revision():
    """Developer should incorporate QA feedback when revising."""
    from schemas import ReviewOutput

    spec = _make_spec()

    # First pass
    code_v1 = run_developer(spec)

    # Simulated QA feedback
    review = ReviewOutput(
        verdict="REVISION_NEEDED",
        issues=["Missing input validation — no check for non-numeric inputs"],
        suggestions=["Add type checking at function entry points"],
        score=0.5,
    )

    code_v2 = run_developer(spec, review=review, iteration=1)

    result = llm_judge(
        criteria=(
            "The developer received QA feedback about missing input validation.\n"
            "Evaluate whether the revised code addresses the feedback:\n"
            "1. Does it add input validation / type checking?\n"
            "2. Is the overall code quality improved?\n"
            "3. Are the original requirements still met?"
        ),
        input_text=f"QA feedback: {review.issues}\nOriginal: {code_v1.description}",
        output_text=f"Revised: {code_v2.description}\nFiles: {', '.join(code_v2.files_created)}",
        threshold=0.5,
    )

    print(f"\n  Score: {result.score:.2f} | {result.reasoning}")
    assert result.passed, f"Developer did not address feedback: {result.reasoning}"
