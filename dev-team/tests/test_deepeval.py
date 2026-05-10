"""DeepEval-based offline tests with native metrics.

Supplements the custom llm_judge tests with standardized DeepEval metrics:
- GEval for spec quality and code-spec alignment
- AnswerRelevancyMetric for end-to-end pipeline relevance
"""

import pytest
from agents.ba import run_ba
from agents.developer import run_developer
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

EVAL_MODEL = "gpt-4.1-mini"

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

spec_completeness = GEval(
    name="Spec Completeness",
    evaluation_steps=[
        "Check that requirements are specific and non-ambiguous",
        "Check that acceptance criteria are testable (can be verified with code)",
        "Check that edge cases and error handling are covered",
        "Check that the complexity estimate is reasonable for the described feature",
    ],
    evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
    model=EVAL_MODEL,
    threshold=0.6,
)

code_spec_alignment = GEval(
    name="Code-Spec Alignment",
    evaluation_steps=[
        "Check that every requirement from the expected output is addressed in the actual output",
        "Check that the code description mentions the key features from the spec",
        "Penalize missing requirements proportionally",
        "Different implementation approaches are acceptable if requirements are met",
    ],
    evaluation_params=[
        SingleTurnParams.INPUT,
        SingleTurnParams.ACTUAL_OUTPUT,
        SingleTurnParams.EXPECTED_OUTPUT,
    ],
    model=EVAL_MODEL,
    threshold=0.6,
)

answer_relevancy = AnswerRelevancyMetric(threshold=0.7, model=EVAL_MODEL)

# ---------------------------------------------------------------------------
# Golden dataset
# ---------------------------------------------------------------------------

GOLDEN_BA = [
    {
        "input": "As a user, I want to register via email so I can create an account",
        "expected": (
            "Spec should cover email validation, password strength, error messages, duplicate check"
        ),
    },
    {
        "input": "As a developer, I want a CLI tool that validates JSON files",
        "expected": (
            "Spec should cover file reading, schema loading, validation errors, exit codes"
        ),
    },
    {
        "input": "As a user, I want to upload a CSV and get summary statistics",
        "expected": (
            "Spec should cover file parsing, numeric columns,"
            " statistics (mean/median/std), error handling for malformed CSV"
        ),
    },
    {
        "input": "As a user, I want to convert temperatures between C, F, and K",
        "expected": ("Spec should cover all 6 conversion directions, input validation, rounding"),
    },
    {
        "input": "As a user, I want a password generator with configurable options",
        "expected": (
            "Spec should cover length parameter, character type toggles,"
            " minimum length, cryptographic randomness"
        ),
    },
]

GOLDEN_DEV = [
    {
        "input": "Calculator: add, subtract, multiply, divide with division-by-zero handling",
        "spec_requirements": [
            "Implement add, subtract, multiply, divide functions",
            "Handle division by zero with a clear error message",
            "Support both integer and float inputs",
        ],
    },
    {
        "input": "Stack data structure with push, pop, peek, is_empty",
        "spec_requirements": [
            "Implement push to add element to top",
            "Implement pop to remove and return top element",
            "Implement peek to view top without removing",
            "Implement is_empty check",
            "Raise error on pop/peek of empty stack",
        ],
    },
    {
        "input": "FizzBuzz function for range 1..N",
        "spec_requirements": [
            "Return 'Fizz' for multiples of 3",
            "Return 'Buzz' for multiples of 5",
            "Return 'FizzBuzz' for multiples of both",
            "Return the number as string otherwise",
        ],
    },
    {
        "input": "Word frequency counter from text input",
        "spec_requirements": [
            "Count occurrences of each word in input text",
            "Ignore case (treat 'The' and 'the' as same)",
            "Return results sorted by frequency descending",
        ],
    },
    {
        "input": "Simple to-do list with add, remove, list, mark-done",
        "spec_requirements": [
            "Add a task with a description",
            "Remove a task by ID",
            "List all tasks with status",
            "Mark a task as done",
        ],
    },
]


# ---------------------------------------------------------------------------
# BA tests — GEval spec completeness
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "golden",
    GOLDEN_BA,
    ids=[g["input"][:40] for g in GOLDEN_BA],
)
def test_ba_spec_completeness_deepeval(golden):
    """BA spec quality via DeepEval GEval metric."""
    spec = run_ba(golden["input"])

    spec_text = (
        f"Title: {spec.title}\n"
        f"Complexity: {spec.estimated_complexity}\n"
        "Requirements:\n" + "\n".join(f"- {r}" for r in spec.requirements) + "\n"
        "Acceptance Criteria:\n" + "\n".join(f"- {ac}" for ac in spec.acceptance_criteria)
    )

    test_case = LLMTestCase(
        input=golden["input"],
        actual_output=spec_text,
    )
    assert_test(test_case, metrics=[spec_completeness])


# ---------------------------------------------------------------------------
# Developer tests — GEval code-spec alignment
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "golden",
    GOLDEN_DEV,
    ids=[g["input"][:40] for g in GOLDEN_DEV],
)
def test_developer_alignment_deepeval(golden):
    """Developer code-spec alignment via DeepEval GEval metric."""
    from schemas import SpecOutput

    spec = SpecOutput(
        title=golden["input"],
        requirements=golden["spec_requirements"],
        acceptance_criteria=[f"Requirement implemented: {r}" for r in golden["spec_requirements"]],
        estimated_complexity="simple",
    )
    code = run_developer(spec)

    test_case = LLMTestCase(
        input=golden["input"],
        actual_output=f"Description: {code.description}\nFiles: {', '.join(code.files_created)}",
        expected_output="Requirements:\n"
        + "\n".join(f"- {r}" for r in golden["spec_requirements"]),
    )
    assert_test(test_case, metrics=[code_spec_alignment])


# ---------------------------------------------------------------------------
# E2E test — AnswerRelevancyMetric
# ---------------------------------------------------------------------------


def test_e2e_relevancy_deepeval():
    """End-to-end pipeline relevance via DeepEval AnswerRelevancyMetric."""
    user_story = "As a user, I want a function that checks if a number is prime"

    spec = run_ba(user_story)
    code = run_developer(spec)

    output_text = (
        f"Spec: {spec.title}\n"
        f"Requirements: {spec.requirements}\n"
        f"Code: {code.description}\n"
        f"Files: {', '.join(code.files_created)}"
    )

    test_case = LLMTestCase(
        input=user_story,
        actual_output=output_text,
    )
    assert_test(test_case, metrics=[answer_relevancy])
