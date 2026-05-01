"""Pydantic models for structured agent outputs."""

from typing import Literal

from pydantic import BaseModel, Field


class SpecOutput(BaseModel):
    """Structured output from the Business Analyst agent."""

    title: str = Field(description="Short title for the feature/task")
    requirements: list[str] = Field(description="Functional requirements derived from the user story")
    acceptance_criteria: list[str] = Field(
        description="Testable acceptance criteria (given/when/then or checklist style)"
    )
    estimated_complexity: Literal["simple", "medium", "complex"] = Field(
        description="Estimated implementation complexity"
    )


class CodeOutput(BaseModel):
    """Structured output from the Developer agent."""

    source_code: str = Field(
        default="",
        description="Optional summary or main entry point code. Full code is in workspace files.",
    )
    description: str = Field(description="Brief description of what was implemented and how")
    files_created: list[str] = Field(description="List of file paths created in workspace/")


class ReviewOutput(BaseModel):
    """Structured output from the QA Engineer agent."""

    verdict: Literal["APPROVED", "REVISION_NEEDED"] = Field(
        description="Whether the code passes quality review"
    )
    issues: list[str] = Field(description="List of issues found (empty if APPROVED)")
    suggestions: list[str] = Field(description="Improvement suggestions (optional even if APPROVED)")
    score: float = Field(ge=0.0, le=1.0, description="Quality score from 0.0 to 1.0")


class JudgeResult(BaseModel):
    """Structured output from LLM-as-a-Judge evaluations."""

    score: float = Field(ge=0.0, le=1.0, description="Evaluation score")
    reasoning: str = Field(description="Explanation of the score")
    passed: bool = Field(description="Whether the evaluation passed (score >= threshold)")
