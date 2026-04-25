"""REPL with HITL interrupt/resume loop + Langfuse tracing.

Usage: python main.py
"""

import logging
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path

from langfuse import propagate_attributes
from langfuse.langchain import CallbackHandler
from langgraph.types import Command, Interrupt

from config import APP_VERSION, Settings
from graph import build_graph

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler("logs/dev-team.log", maxBytes=5_000_000, backupCount=3),
    ],
)
logger = logging.getLogger("dev-team")

settings = Settings()

USER_ID = "cli-user"
SESSION_ID = str(uuid.uuid4())


def _create_langfuse_handler() -> CallbackHandler:
    """Create a Langfuse CallbackHandler (v4 — attributes set via propagate_attributes)."""
    return CallbackHandler()


def _print_header():
    print(f"\nAI Dev Team v{APP_VERSION}")
    print(f"Model: {settings.model_powerful}")
    print(f"Session: {SESSION_ID[:8]} | Max QA iterations: {settings.max_qa_iterations}")
    print("Enter a user story to start. Type 'exit' to quit.")
    print("-" * 60)


def _print_spec(spec_data: dict):
    """Pretty-print a SpecOutput for HITL review."""
    print("\n" + "=" * 60)
    print("  SPECIFICATION FOR REVIEW")
    print("=" * 60)
    print(f"\n  Title: {spec_data.get('title', '?')}")
    print(f"  Complexity: {spec_data.get('estimated_complexity', '?')}")
    print("\n  Requirements:")
    for i, req in enumerate(spec_data.get("requirements", []), 1):
        print(f"    {i}. {req}")
    print("\n  Acceptance Criteria:")
    for i, ac in enumerate(spec_data.get("acceptance_criteria", []), 1):
        print(f"    {i}. {ac}")
    print("\n" + "=" * 60)


def _handle_interrupt(
    interrupts: list[Interrupt],
    thread_id: str,
    graph,
    langfuse_handler: CallbackHandler,
) -> dict | None:
    """Handle HITL interrupt — spec review."""
    for intr in interrupts:
        payload = intr.value

        if payload.get("type") == "spec_review":
            _print_spec(payload)

            while True:
                choice = input("\n  approve / reject (with feedback): ").strip().lower()
                if choice == "approve":
                    resume_data = {"approved": True, "feedback": ""}
                    break
                elif choice.startswith("reject"):
                    feedback = input("  Your feedback: ").strip()
                    resume_data = {"approved": False, "feedback": feedback}
                    break
                else:
                    print("  Please enter 'approve' or 'reject'")

            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 100,
                "callbacks": [langfuse_handler],
            }

            result = graph.invoke(
                Command(resume=resume_data),
                config=config,
            )
            return result

    return None


def _run_pipeline(user_story: str, graph, langfuse_handler: CallbackHandler):
    """Run the full Dev Team pipeline with HITL support."""
    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 100,
        "callbacks": [langfuse_handler],
    }

    initial_state = {
        "user_story": user_story,
        "spec": None,
        "spec_approved": False,
        "spec_feedback": "",
        "code": None,
        "review": None,
        "iteration": 0,
        "review_history": [],
    }

    print("\n  Starting pipeline...")
    print("  [1/3] Business Analyst analyzing user story...")

    with propagate_attributes(
        session_id=SESSION_ID,
        user_id=USER_ID,
        tags=["dev-team", "cli"],
    ):
        result = graph.invoke(initial_state, config=config)

        # Handle HITL interrupts
        while True:
            interrupts = result.get("__interrupt__", [])
            if not interrupts:
                break

            result = _handle_interrupt(interrupts, thread_id, graph, langfuse_handler)
            if result is None:
                break

    # Print final results
    _print_results(result)


def _print_results(result: dict):
    """Print the final pipeline results."""
    spec = result.get("spec")
    code = result.get("code")
    review = result.get("review")
    iteration = result.get("iteration", 0)

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)

    if spec:
        print(f"\n  Spec: {spec.title} ({spec.estimated_complexity})")

    if code:
        print(f"\n  Code: {code.description}")
        print(f"  Files: {', '.join(code.files_created)}")

    if review:
        print(f"\n  QA Verdict: {review.verdict}")
        print(f"  QA Score: {review.score:.2f}")
        print(f"  Iterations: {iteration}")

        if review.issues:
            print("\n  Issues:")
            for issue in review.issues:
                print(f"    - {issue}")

        if review.suggestions:
            print("\n  Suggestions:")
            for sug in review.suggestions:
                print(f"    - {sug}")

    print("\n" + "=" * 60)


def main():
    _print_header()
    graph = build_graph()

    while True:
        try:
            user_input = input("\nUser Story: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        langfuse_handler = _create_langfuse_handler()

        try:
            _run_pipeline(user_input, graph, langfuse_handler)
        except Exception as e:
            logger.exception("Pipeline error")
            print(f"\n  Error: {e}")


if __name__ == "__main__":
    main()
