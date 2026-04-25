"""LLM-as-a-Judge tests for the QA Engineer agent.

Tests that QA catches real issues and provides actionable feedback.
"""

import pytest

from agents.qa import run_qa
from schemas import CodeOutput, SpecOutput
from tests.conftest import llm_judge


def _make_spec() -> SpecOutput:
    return SpecOutput(
        title="User Registration",
        requirements=[
            "Validate email format before registration",
            "Password must be at least 8 characters",
            "Return clear error messages for invalid input",
        ],
        acceptance_criteria=[
            "Invalid email like 'notanemail' is rejected",
            "Password '123' is rejected with clear message",
            "Valid registration returns success",
        ],
        estimated_complexity="simple",
    )


def test_qa_catches_bad_code():
    """QA should find issues in intentionally bad code."""
    spec = _make_spec()

    bad_code = CodeOutput(
        source_code=(
            'def register(email, password):\n'
            '    # No validation at all\n'
            '    users = {}\n'
            '    users[email] = password\n'
            '    return "ok"\n'
        ),
        description="Basic registration function",
        files_created=["register.py"],
    )

    review = run_qa(spec, bad_code)

    # QA should not approve code with no validation
    assert review.verdict == "REVISION_NEEDED", (
        f"QA should reject code without validation, but got {review.verdict}"
    )
    assert len(review.issues) > 0, "QA should find issues in bad code"
    assert review.score < 0.7, f"Score too high for bad code: {review.score}"

    result = llm_judge(
        criteria=(
            "The QA reviewed code that is missing email validation and password length check.\n"
            "Evaluate QA's review quality:\n"
            "1. Did QA identify the missing email validation?\n"
            "2. Did QA identify the missing password check?\n"
            "3. Are the issues specific and actionable (not vague)?\n"
            "4. Do suggestions help the developer fix the problems?"
        ),
        input_text=f"Bad code:\n{bad_code.source_code}\nSpec requirements: {spec.requirements}",
        output_text=f"QA issues: {review.issues}\nSuggestions: {review.suggestions}",
        threshold=0.6,
    )

    print(f"\n  Score: {result.score:.2f} | {result.reasoning}")
    assert result.passed, f"QA review quality too low: {result.reasoning}"


def test_qa_approves_good_code():
    """QA should approve well-implemented code."""
    spec = _make_spec()

    good_code = CodeOutput(
        source_code=(
            'import re\n\n'
            'def register(email: str, password: str) -> dict:\n'
            '    """Register a new user with email and password."""\n'
            '    if not re.match(r"^[\\w.+-]+@[\\w-]+\\.[\\w.]+$", email):\n'
            '        return {"error": "Invalid email format"}\n'
            '    if len(password) < 8:\n'
            '        return {"error": "Password must be at least 8 characters"}\n'
            '    return {"success": True, "email": email}\n'
        ),
        description="Registration with email and password validation",
        files_created=["register.py"],
    )

    review = run_qa(spec, good_code)

    # QA should generally approve good code, but may still have minor suggestions
    assert review.score >= 0.6, f"Score too low for good code: {review.score}"

    print(f"\n  Verdict: {review.verdict}, Score: {review.score:.2f}")
    if review.suggestions:
        print(f"  Suggestions: {review.suggestions}")
