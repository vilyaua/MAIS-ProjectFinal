"""QA Engineer Agent — reviews code, runs tests, returns ReviewOutput."""

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.chat_models import init_chat_model

from config import Settings
from langfuse_prompts import get_system_prompt
from schemas import CodeOutput, ReviewOutput, SpecOutput
from tools import QA_TOOLS

settings = Settings()
_qa_agent = None


def _get_qa_agent():
    """Get or create the cached QA agent."""
    global _qa_agent
    if _qa_agent is None:
        system_prompt = get_system_prompt(
            "qa-prompt",
            max_iterations=str(settings.max_qa_iterations),
        )
        model = init_chat_model(settings.model_mid, max_retries=4)
        _qa_agent = create_agent(
            model=model,
            tools=QA_TOOLS,
            system_prompt=system_prompt,
            response_format=ToolStrategy(ReviewOutput),
            name="qa-engineer",
        )
    return _qa_agent


def run_qa(
    spec: SpecOutput,
    code: CodeOutput,
    iteration: int = 0,
    callbacks=None,
) -> ReviewOutput:
    """Run the QA agent on code against spec. Returns structured ReviewOutput."""
    agent = _get_qa_agent()

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
        f"**Files to review:** {', '.join(code.files_created)}",
        "",
        f"Review iteration {iteration + 1}/{settings.max_qa_iterations}.",
        "Follow your review process. Read ALL files listed above.",
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
