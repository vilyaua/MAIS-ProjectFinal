"""QA Engineer Agent — reviews code, runs tests, returns ReviewOutput."""

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from config import Settings
from langfuse_prompts import get_system_prompt
from schemas import CodeOutput, ReviewOutput, SpecOutput
from tools import QA_TOOLS

settings = Settings()


def create_qa_agent():
    """Create the QA agent with structured ReviewOutput."""
    system_prompt = get_system_prompt(
        "qa-prompt",
        max_iterations=str(settings.max_qa_iterations),
    )

    agent = create_agent(
        model=settings.model_fast,
        tools=QA_TOOLS,
        system_prompt=system_prompt,
        response_format=ToolStrategy(ReviewOutput),
        name="qa-engineer",
        model_kwargs={"max_retries": 8},
    )
    return agent


def run_qa(
    spec: SpecOutput,
    code: CodeOutput,
    iteration: int = 0,
    callbacks=None,
) -> ReviewOutput:
    """Run the QA agent on code against spec. Returns structured ReviewOutput."""
    agent = create_qa_agent()

    prompt_parts = [
        "## Specification to verify against",
        f"**Title:** {spec.title}",
        "",
        "**Requirements:**",
    ]
    for i, req in enumerate(spec.requirements, 1):
        prompt_parts.append(f"{i}. {req}")

    prompt_parts.extend(["", "**Acceptance Criteria:**"])
    for i, ac in enumerate(spec.acceptance_criteria, 1):
        prompt_parts.append(f"{i}. {ac}")

    prompt_parts.extend([
        "",
        "## Code to review",
        f"**Description:** {code.description}",
        f"**Files created:** {', '.join(code.files_created)}",
        "",
        "```python",
        code.source_code,
        "```",
        "",
        f"This is review iteration {iteration + 1}/{settings.max_qa_iterations}.",
        "",
        "Please:",
        "1. Read the created files using file_read to verify they exist and are correct",
        "2. Run the code using python_repl to test basic functionality",
        "3. Test edge cases",
        "4. Check compliance with all requirements and acceptance criteria",
        "5. Return your ReviewOutput with verdict, issues, suggestions, and score",
    ])

    prompt = "\n".join(prompt_parts)

    config = {}
    if callbacks:
        config["callbacks"] = callbacks

    result = agent.invoke(
        {"messages": [("user", prompt)]},
        config=config,
    )
    return result["structured_response"]
