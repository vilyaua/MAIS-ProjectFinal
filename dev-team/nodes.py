"""Node functions for the Dev Team LangGraph StateGraph."""

import logging

from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from agents.ba import run_ba
from agents.developer import run_developer
from agents.qa import run_qa
from github_integration import create_pr
from state import DevTeamState

logger = logging.getLogger("nodes")


def ba_node(state: DevTeamState, config: RunnableConfig | None = None) -> dict:
    """Business Analyst: analyze user story and produce SpecOutput."""
    logger.info("BA Agent: analyzing user story")
    callbacks = config.get("callbacks", []) if config else []

    spec = run_ba(
        user_story=state["user_story"],
        feedback=state.get("spec_feedback"),
        callbacks=callbacks,
    )

    logger.info("BA Agent: produced spec '%s' (%s)", spec.title, spec.estimated_complexity)
    return {"spec": spec, "spec_approved": False, "spec_feedback": ""}


def hitl_gate(state: DevTeamState) -> dict:
    """Human-in-the-Loop gate: user approves or rejects the spec."""
    spec = state["spec"]

    # Present spec to user and wait for approval
    result = interrupt({
        "type": "spec_review",
        "title": spec.title,
        "requirements": spec.requirements,
        "acceptance_criteria": spec.acceptance_criteria,
        "estimated_complexity": spec.estimated_complexity,
    })

    # result comes from Command(resume={"approved": bool, "feedback": str})
    approved = result.get("approved", False)
    feedback = result.get("feedback", "")

    logger.info("HITL gate: %s", "APPROVED" if approved else f"REJECTED ({feedback})")
    return {"spec_approved": approved, "spec_feedback": feedback}


def dev_node(state: DevTeamState, config: RunnableConfig | None = None) -> dict:
    """Developer: write code based on spec (and QA feedback if revision)."""
    iteration = state.get("iteration", 0)
    callbacks = config.get("callbacks", []) if config else []

    logger.info("Developer Agent: writing code (iteration %d)", iteration)

    code = run_developer(
        spec=state["spec"],
        review=state.get("review"),
        iteration=iteration,
        callbacks=callbacks,
    )

    logger.info("Developer Agent: created %d files", len(code.files_created))
    return {"code": code}


def qa_node(state: DevTeamState, config: RunnableConfig | None = None) -> dict:
    """QA Engineer: review code, run tests, return ReviewOutput."""
    iteration = state.get("iteration", 0)
    callbacks = config.get("callbacks", []) if config else []

    logger.info("QA Agent: reviewing code (iteration %d)", iteration)

    review = run_qa(
        spec=state["spec"],
        code=state["code"],
        iteration=iteration,
        callbacks=callbacks,
    )

    review_history = state.get("review_history", [])
    review_history = [*review_history, review]

    logger.info("QA Agent: verdict=%s, score=%.2f", review.verdict, review.score)
    return {
        "review": review,
        "iteration": iteration + 1,
        "review_history": review_history,
    }


def github_node(state: DevTeamState) -> dict:
    """Push approved code to GitHub and open a PR."""
    logger.info("GitHub: creating PR")
    try:
        pr_url = create_pr(
            spec=state["spec"],
            code=state["code"],
            review=state.get("review"),
            iteration=state.get("iteration", 0),
        )
        if pr_url:
            logger.info("GitHub: PR created — %s", pr_url)
        else:
            logger.info("GitHub: skipped (not configured)")
        return {"pr_url": pr_url}
    except Exception as e:
        logger.error("GitHub: PR creation failed — %s", e)
        return {"pr_url": None}
