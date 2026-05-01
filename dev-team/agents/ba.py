"""Business Analyst Agent — analyzes user story, produces SpecOutput."""

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.chat_models import init_chat_model

from config import Settings
from langfuse_prompts import get_system_prompt
from schemas import SpecOutput
from tools import BA_TOOLS

settings = Settings()
_ba_agent = None


def _get_ba_agent():
    """Get or create the cached BA agent."""
    global _ba_agent
    if _ba_agent is None:
        system_prompt = get_system_prompt("ba-prompt")
        model = init_chat_model(settings.model_fast, max_retries=4)
        _ba_agent = create_agent(
            model=model,
            tools=BA_TOOLS,
            system_prompt=system_prompt,
            response_format=ToolStrategy(SpecOutput),
            name="business-analyst",
        )
    return _ba_agent


def run_ba(user_story: str, feedback: str | None = None, callbacks=None) -> SpecOutput:
    """Run the BA agent on a user story. Returns structured SpecOutput."""
    agent = _get_ba_agent()

    if feedback:
        prompt = (
            f"User story: {user_story}\n\n"
            f"Previous spec was rejected. User feedback:\n{feedback}\n\n"
            "Revise the specification based on this feedback."
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
