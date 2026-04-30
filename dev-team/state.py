"""LangGraph state definition for the Dev Team workflow."""

from typing import TypedDict

from schemas import CodeOutput, ReviewOutput, SpecOutput


class DevTeamState(TypedDict, total=False):
    """Shared state for the Dev Team StateGraph."""

    user_story: str
    spec: SpecOutput | None
    spec_approved: bool
    spec_feedback: str
    code: CodeOutput | None
    review: ReviewOutput | None
    iteration: int
    review_history: list[ReviewOutput]
    pr_url: str | None
