"""End-to-end LLM-as-a-Judge test for the full Dev Team pipeline.

Tests the complete flow: user story -> BA -> Developer -> QA -> final code.
"""

from agents.ba import run_ba
from agents.developer import run_developer
from agents.qa import run_qa

from tests.conftest import llm_judge


def test_e2e_simple_feature():
    """Full pipeline: user story -> approved code."""
    user_story = (
        "As a user, I want a function that converts temperatures between Celsius and Fahrenheit"
    )

    # Step 1: BA
    spec = run_ba(user_story)
    assert spec.requirements, "BA must produce requirements"
    assert spec.acceptance_criteria, "BA must produce acceptance criteria"

    # Step 2: Developer
    code = run_developer(spec)
    assert code.files_created, "Developer must create files"

    # Step 3: QA
    review = run_qa(spec, code)

    # Step 4: If revision needed, do one more iteration
    if review.verdict == "REVISION_NEEDED":
        code = run_developer(spec, review=review, iteration=1)
        review = run_qa(spec, code, iteration=1)

    # Judge the final result
    result = llm_judge(
        criteria=(
            "Evaluate the complete pipeline output:\n"
            "1. Does the final code correctly implement temperature conversion?\n"
            "2. Does it handle both C->F and F->C?\n"
            "3. Is the code well-structured and readable?\n"
            "4. Does the QA review make sense given the code quality?\n"
            "5. Does the final output match the original user story?"
        ),
        input_text=f"User story: {user_story}",
        output_text=(
            f"Spec: {spec.title}\nRequirements: {spec.requirements}\n\n"
            f"Code: {code.description}\nFiles: {', '.join(code.files_created)}\n\n"
            f"QA verdict: {review.verdict}, score: {review.score}\n"
            f"QA issues: {review.issues}"
        ),
        threshold=0.6,
    )

    print(f"\n  E2E Score: {result.score:.2f}")
    print(f"  Reasoning: {result.reasoning}")
    print(f"  QA iterations: {'2' if review.verdict == 'APPROVED' else '1'}")
    assert result.passed, f"E2E quality too low: {result.reasoning}"
