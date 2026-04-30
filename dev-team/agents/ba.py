"""Business Analyst Agent — analyzes user story, produces SpecOutput."""

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from config import Settings
from langfuse_prompts import get_system_prompt
from schemas import SpecOutput
from tools import BA_TOOLS

settings = Settings()


def create_ba_agent():
    """Create the BA agent with structured SpecOutput."""
    system_prompt = get_system_prompt("ba-prompt")

    agent = create_agent(
        model=settings.model_fast,
        tools=BA_TOOLS,
        system_prompt=system_prompt,
        response_format=ToolStrategy(SpecOutput),
        name="business-analyst",
        model_kwargs={"max_retries": 8},
    )
    return agent


def run_ba(user_story: str, feedback: str | None = None, callbacks=None) -> SpecOutput:
    """Run the BA agent on a user story. Returns structured SpecOutput."""
    agent = create_ba_agent()

    if feedback:
        prompt = (
            f"User story: {user_story}\n\n"
            f"Previous spec was rejected. User feedback:\n{feedback}\n\n"
            "Please revise the specification based on this feedback."
        )
    else:
        prompt = f"User story: {user_story}"

    config = {}
    if callbacks:
        config["callbacks"] = callbacks

    result = agent.invoke(
        {"messages": [("user", prompt)]},
        config=config,
    )
    return result["structured_response"]
