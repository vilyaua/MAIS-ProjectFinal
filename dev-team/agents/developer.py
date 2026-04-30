"""Developer Agent — receives spec, writes code, creates project files."""

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from config import Settings
from langfuse_prompts import get_system_prompt
from schemas import CodeOutput, ReviewOutput, SpecOutput
from tools import DEVELOPER_TOOLS

settings = Settings()


def create_developer_agent():
    """Create the Developer agent with structured CodeOutput."""
    system_prompt = get_system_prompt("developer-prompt")

    agent = create_agent(
        model=settings.model_powerful,
        tools=DEVELOPER_TOOLS,
        system_prompt=system_prompt,
        response_format=ToolStrategy(CodeOutput),
        name="developer",
        model_kwargs={"max_retries": 8},
    )
    return agent


def run_developer(
    spec: SpecOutput,
    review: ReviewOutput | None = None,
    iteration: int = 0,
    callbacks=None,
) -> CodeOutput:
    """Run the Developer agent. Returns structured CodeOutput."""
    agent = create_developer_agent()

    prompt_parts = [
        "## Specification",
        f"**Title:** {spec.title}",
        f"**Complexity:** {spec.estimated_complexity}",
        "",
        "**Requirements:**",
    ]
    for i, req in enumerate(spec.requirements, 1):
        prompt_parts.append(f"{i}. {req}")

    prompt_parts.extend(["", "**Acceptance Criteria:**"])
    for i, ac in enumerate(spec.acceptance_criteria, 1):
        prompt_parts.append(f"{i}. {ac}")

    if review and review.verdict == "REVISION_NEEDED":
        prompt_parts.extend([
            "",
            f"## QA Feedback (iteration {iteration})",
            f"**Score:** {review.score:.1f}",
            "",
            "**Issues to fix:**",
        ])
        for issue in review.issues:
            prompt_parts.append(f"- {issue}")
        if review.suggestions:
            prompt_parts.extend(["", "**Suggestions:**"])
            for sug in review.suggestions:
                prompt_parts.append(f"- {sug}")

    prompt = "\n".join(prompt_parts)

    config = {}
    if callbacks:
        config["callbacks"] = callbacks

    result = agent.invoke(
        {"messages": [("user", prompt)]},
        config=config,
    )
    return result["structured_response"]
