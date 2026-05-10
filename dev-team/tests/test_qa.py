"""LLM-as-a-Judge tests for the QA Engineer agent.

Tests that QA catches real issues and provides actionable feedback.
"""

import os
import shutil

from agents.qa import run_qa
from config import Settings
from schemas import CodeOutput, SpecOutput

from tests.conftest import llm_judge

settings = Settings()


def _write_code_to_workspace(code: CodeOutput, file_contents: dict[str, str] | None = None) -> None:
    """Write code files to workspace/ so QA can read/run them.

    Args:
        code: CodeOutput with files_created list.
        file_contents: Optional mapping of filepath -> content. If not provided,
            falls back to code.source_code for all files (single-file only).
    """
    for filepath in code.files_created:
        full_path = os.path.join(settings.workspace_dir, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        content = (file_contents or {}).get(filepath, code.source_code)
        with open(full_path, "w") as f:
            f.write(content)


def _clean_workspace() -> None:
    """Remove all files from workspace/."""
    if os.path.exists(settings.workspace_dir):
        for item in os.listdir(settings.workspace_dir):
            path = os.path.join(settings.workspace_dir, item)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)


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
            "def register(email, password):\n"
            "    # No validation at all\n"
            "    users = {}\n"
            "    users[email] = password\n"
            '    return "ok"\n'
        ),
        description="Basic registration function",
        files_created=["register.py"],
    )

    _clean_workspace()
    _write_code_to_workspace(bad_code)
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
            "import re\n\n"
            "def register(email: str, password: str) -> dict:\n"
            '    """Register a new user with email and password."""\n'
            '    if not re.match(r"^[\\w.+-]+@[\\w-]+\\.[\\w.]+$", email):\n'
            '        return {"error": "Invalid email format"}\n'
            "    if len(password) < 8:\n"
            '        return {"error": "Password must be at least 8 characters"}\n'
            '    return {"success": True, "email": email}\n'
        ),
        description="Registration with email and password validation",
        files_created=["register.py"],
    )

    _clean_workspace()
    _write_code_to_workspace(good_code)
    review = run_qa(spec, good_code)

    # QA should generally approve good code, but may still have minor suggestions
    assert review.score >= 0.6, f"Score too low for good code: {review.score}"

    print(f"\n  Verdict: {review.verdict}, Score: {review.score:.2f}")
    if review.suggestions:
        print(f"  Suggestions: {review.suggestions}")


def test_qa_catches_hardcoded_values():
    """QA should flag hardcoded magic values and missing configurability."""
    spec = SpecOutput(
        title="Temperature Converter",
        requirements=[
            "Convert Celsius to Fahrenheit and vice versa",
            "Support Kelvin conversions",
            "Handle invalid inputs gracefully",
        ],
        acceptance_criteria=[
            "celsius_to_fahrenheit(0) returns 32.0",
            "fahrenheit_to_celsius(212) returns 100.0",
            "Invalid input like 'abc' raises ValueError",
        ],
        estimated_complexity="simple",
    )

    bad_code = CodeOutput(
        source_code=(
            "def convert(value):\n"
            "    # Only C->F, no Kelvin, no error handling\n"
            "    return value * 1.8 + 32\n"
        ),
        description="Basic temperature converter",
        files_created=["converter.py"],
    )

    _clean_workspace()
    _write_code_to_workspace(bad_code)
    review = run_qa(spec, bad_code)

    assert review.verdict == "REVISION_NEEDED", (
        f"QA should reject incomplete implementation, got {review.verdict}"
    )
    assert len(review.issues) > 0, "QA should find issues in incomplete code"

    result = llm_judge(
        criteria=(
            "The code is missing Kelvin support, error handling, and reverse conversion.\n"
            "Evaluate QA's review:\n"
            "1. Did QA identify the missing Kelvin conversions?\n"
            "2. Did QA identify missing error handling?\n"
            "3. Did QA note the missing reverse (F->C) conversion?\n"
            "4. Are suggestions actionable?"
        ),
        input_text=f"Bad code:\n{bad_code.source_code}\nSpec: {spec.requirements}",
        output_text=f"QA issues: {review.issues}\nSuggestions: {review.suggestions}",
        threshold=0.6,
    )

    print(f"\n  Score: {result.score:.2f} | {result.reasoning}")
    assert result.passed, f"QA review quality too low: {result.reasoning}"


def test_qa_multi_file_review():
    """QA should review code spread across multiple files."""
    spec = SpecOutput(
        title="Key-Value Store",
        requirements=[
            "Implement get, set, delete operations",
            "Persist data to a JSON file",
            "Handle missing keys with KeyError",
        ],
        acceptance_criteria=[
            "set('key', 'value') followed by get('key') returns 'value'",
            "delete('key') removes the key",
            "get('missing') raises KeyError",
        ],
        estimated_complexity="simple",
    )

    store_code = (
        "import json\n"
        "from pathlib import Path\n\n"
        "class KVStore:\n"
        "    def __init__(self, path: str = 'store.json'):\n"
        "        self.path = Path(path)\n"
        "        self.data = {}\n"
        "        if self.path.exists():\n"
        "            self.data = json.loads(self.path.read_text())\n\n"
        "    def get(self, key: str) -> str:\n"
        "        return self.data[key]\n\n"
        "    def set(self, key: str, value: str) -> None:\n"
        "        self.data[key] = value\n"
        "        self.path.write_text(json.dumps(self.data))\n\n"
        "    def delete(self, key: str) -> None:\n"
        "        del self.data[key]\n"
        "        self.path.write_text(json.dumps(self.data))\n"
    )

    test_code = (
        "from store import KVStore\n\n"
        "def test_set_get():\n"
        "    s = KVStore('/tmp/test_store.json')\n"
        "    s.set('a', '1')\n"
        "    assert s.get('a') == '1'\n"
    )

    code = CodeOutput(
        source_code="",
        description="Key-value store with JSON persistence and tests",
        files_created=["src/store.py", "tests/test_store.py"],
    )

    _clean_workspace()
    _write_code_to_workspace(
        code,
        file_contents={"src/store.py": store_code, "tests/test_store.py": test_code},
    )
    review = run_qa(spec, code)

    assert review.score > 0, "QA must return a score"
    print(f"\n  Verdict: {review.verdict}, Score: {review.score:.2f}")
    print(f"  Issues: {review.issues}")
