"""LangChain @tool functions for all agents.

Tools:
  - web_search      (BA, Developer)
  - knowledge_search (BA)
  - python_repl     (Developer, QA)
  - file_write      (Developer)
  - file_read       (Developer, QA)
"""

import logging
import os
import re
import subprocess
import textwrap
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import trafilatura
from ddgs import DDGS
from langchain_core.tools import tool

from config import Settings

logger = logging.getLogger("tools")
settings = Settings()

_executor = ThreadPoolExecutor(max_workers=4)

# Patterns blocked in python_repl for safety
_DANGEROUS_PATTERNS = [
    r"\bos\.system\b",
    r"\bsubprocess\b",
    r"\bshutil\.rmtree\b",
    r"\b__import__\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bopen\s*\(.*/etc/",
    r"\brm\s+-rf\b",
]


def _ddgs_search(query: str, max_results: int) -> list[dict]:
    return DDGS().text(query, max_results=max_results)


# ---------------------------------------------------------------------------
# BA + Developer tools
# ---------------------------------------------------------------------------


@tool
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo. Returns titles, URLs, and snippets."""
    try:
        future = _executor.submit(_ddgs_search, query, settings.max_search_results)
        results = future.result(timeout=30)
        if not results:
            return "No results found."
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(
                f"{i}. Title: {r.get('title', 'N/A')}\n"
                f"   URL: {r.get('href', 'N/A')}\n"
                f"   Snippet: {r.get('body', 'N/A')}"
            )
        result = "\n\n".join(formatted)
        if len(result) > settings.max_search_content_length:
            result = result[: settings.max_search_content_length] + "\n\n[... truncated]"
        return result
    except Exception as e:
        return f"Search error: {e}"


@tool
def knowledge_search(query: str) -> str:
    """Search the local knowledge base (RAG) for Python docs, style guides, and tutorials.

    Use for questions about Python stdlib, coding standards, design patterns,
    and framework documentation. Returns relevant text chunks with source refs.
    """
    try:
        from retriever import retrieve

        results = retrieve(query)
        if not results:
            return "No relevant documents found in the knowledge base."
        formatted = []
        for i, doc in enumerate(results, 1):
            source = Path(doc.metadata.get("source", "unknown")).name
            page = doc.metadata.get("page", "?")
            formatted.append(f"{i}. [Source: {source}, Page: {page}]\n{doc.page_content}")
        result = "\n\n---\n\n".join(formatted)
        if len(result) > settings.max_search_content_length:
            result = result[: settings.max_search_content_length] + "\n\n[... truncated]"
        return result
    except Exception as e:
        return f"Knowledge search error: {e}"


# ---------------------------------------------------------------------------
# Developer + QA tools
# ---------------------------------------------------------------------------


def _validate_workspace_path(filepath: str) -> Path:
    """Ensure the path is within workspace/ directory. Returns resolved Path."""
    workspace = Path(settings.workspace_dir).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    target = (workspace / filepath).resolve()
    if not str(target).startswith(str(workspace)):
        raise ValueError(f"Path escapes workspace directory: {filepath}")
    return target


@tool
def python_repl(code: str) -> str:
    """Execute Python code in a sandboxed subprocess. Returns stdout + stderr.

    Use this to test code, run scripts, or verify that implementations work.
    Code runs with a timeout and dangerous operations are blocked.
    Working directory is workspace/.
    """
    # Check for dangerous patterns
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, code):
            return f"BLOCKED: Code contains dangerous pattern matching '{pattern}'. Rewrite without it."

    workspace = Path(settings.workspace_dir).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(  # noqa: S603
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=settings.repl_timeout,
            cwd=str(workspace),
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += "\n[STDERR]\n" + result.stderr
        if not output.strip():
            output = "(no output)"
        # Truncate very long outputs
        if len(output) > 5000:
            output = output[:5000] + "\n\n[... output truncated at 5000 chars]"
        return output
    except subprocess.TimeoutExpired:
        return f"TIMEOUT: Code execution exceeded {settings.repl_timeout}s limit."
    except Exception as e:
        return f"Execution error: {e}"


@tool
def file_write(filepath: str, content: str) -> str:
    """Write a file to the workspace/ directory.

    Creates parent directories as needed. Use relative paths
    (e.g. 'src/main.py', 'tests/test_main.py', 'requirements.txt').
    """
    try:
        target = _validate_workspace_path(filepath)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"File written: {filepath} ({len(content)} chars)"
    except ValueError as e:
        return f"BLOCKED: {e}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def file_read(filepath: str) -> str:
    """Read a file from the workspace/ directory. Returns content with line numbers."""
    try:
        target = _validate_workspace_path(filepath)
        if not target.exists():
            return f"File not found: {filepath}"
        content = target.read_text(encoding="utf-8")
        # Add line numbers
        lines = content.splitlines()
        numbered = [f"{i + 1:4d} | {line}" for i, line in enumerate(lines)]
        result = "\n".join(numbered)
        if len(result) > 8000:
            result = result[:8000] + "\n\n[... truncated]"
        return result
    except ValueError as e:
        return f"BLOCKED: {e}"
    except Exception as e:
        return f"Error reading file: {e}"


# ---------------------------------------------------------------------------
# Tool groupings per agent
# ---------------------------------------------------------------------------

BA_TOOLS = [web_search, knowledge_search]
DEVELOPER_TOOLS = [web_search, python_repl, file_write, file_read]
QA_TOOLS = [python_repl, file_read]
