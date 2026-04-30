"""LangChain @tool functions for all agents.

Tools:
  - web_search      (BA, Developer)
  - knowledge_search (BA)
  - docs_search     (BA, Developer) — Context7 MCP
  - python_repl     (Developer, QA)
  - file_write      (Developer)
  - file_read       (Developer, QA)
"""

import asyncio
import logging
import os
import re
import shutil
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
# Context7 MCP — library documentation search
# ---------------------------------------------------------------------------


async def _context7_query(library_name: str, query: str) -> str:
    """Call Context7 MCP server to resolve library and query docs."""
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from mcp.types import TextContent

    # Find context7-mcp binary
    c7_bin = shutil.which("context7-mcp")
    if not c7_bin:
        return "Context7 MCP server not installed (context7-mcp not found)."

    server_params = StdioServerParameters(command=c7_bin, args=[])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Step 1: resolve library ID
            resolve_result = await session.call_tool(
                "resolve-library-id",
                {"libraryName": library_name, "query": query},
            )
            resolve_text = ""
            for block in resolve_result.content:
                if isinstance(block, TextContent):
                    resolve_text += block.text

            if not resolve_text.strip():
                return f"No library found for '{library_name}'."

            # Extract library ID (format: /org/project)
            library_id = None
            for line in resolve_text.splitlines():
                stripped = line.strip()
                if stripped.startswith("/") and "/" in stripped[1:]:
                    # Take first token that looks like /org/project
                    candidate = stripped.split()[0] if stripped.split() else stripped
                    if candidate.startswith("/"):
                        library_id = candidate
                        break

            if not library_id:
                return f"Could not resolve library ID from: {resolve_text[:500]}"

            # Step 2: query documentation
            docs_result = await session.call_tool(
                "query-docs",
                {"libraryId": library_id, "query": query},
            )
            docs_text = ""
            for block in docs_result.content:
                if isinstance(block, TextContent):
                    docs_text += block.text

            if len(docs_text) > settings.max_url_content_length:
                docs_text = docs_text[: settings.max_url_content_length] + "\n\n[... truncated]"

            return docs_text if docs_text.strip() else "No documentation found."


@tool
def docs_search(library_name: str, query: str) -> str:
    """Search up-to-date library documentation via Context7 MCP.

    Use this to look up current API signatures, configuration options,
    and usage examples for any library or framework (e.g. Flask, FastAPI,
    pytest, SQLAlchemy, Pydantic, etc.).

    Args:
        library_name: Name of the library (e.g. 'Flask', 'FastAPI', 'pytest')
        query: What to search for (e.g. 'how to create routes', 'middleware setup')
    """
    try:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_context7_query(library_name, query))
        finally:
            loop.close()
    except Exception as e:
        logger.warning("docs_search failed: %s", e)
        return f"Docs search error: {e}"


# ---------------------------------------------------------------------------
# Terminal — run shell commands in workspace
# ---------------------------------------------------------------------------

# Allowed command prefixes for the terminal tool
_ALLOWED_COMMANDS = [
    "python", "python3", "pip", "pytest", "ls", "cat", "head", "tail",
    "wc", "diff", "find", "echo", "mkdir", "touch", "tree",
]


@tool
def run_command(command: str) -> str:
    """Run a shell command in the workspace/ directory. Returns stdout + stderr.

    Use this to run files, execute tests, install packages, or inspect the workspace.
    Prefer this over python_repl when running existing files:
      - run_command("python src/main.py")
      - run_command("python -m pytest tests/ -v")
      - run_command("pip install -r requirements.txt")
      - run_command("ls -la src/")

    Only safe commands are allowed (python, pytest, pip, ls, cat, etc.).
    """
    if not command.strip():
        return "Error: empty command."

    first_word = command.strip().split()[0]
    if first_word not in _ALLOWED_COMMANDS:
        return f"BLOCKED: Command '{first_word}' is not allowed. Allowed: {', '.join(_ALLOWED_COMMANDS)}"

    # Block dangerous patterns
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, command):
            return f"BLOCKED: Command contains dangerous pattern matching '{pattern}'."

    workspace = Path(settings.workspace_dir).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(  # noqa: S603
            command,
            shell=True,
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
        if len(output) > 5000:
            output = output[:5000] + "\n\n[... output truncated at 5000 chars]"
        return output
    except subprocess.TimeoutExpired:
        return f"TIMEOUT: Command exceeded {settings.repl_timeout}s limit."
    except Exception as e:
        return f"Execution error: {e}"


# ---------------------------------------------------------------------------
# Notion — read pages as user stories
# ---------------------------------------------------------------------------


@tool
def read_notion_page(page_url: str) -> str:
    """Read a Notion page and return its text content.

    Use this to fetch user stories or requirements from Notion.
    Accepts a Notion page URL (e.g. https://www.notion.so/My-Page-abc123).
    """
    try:
        content = trafilatura.fetch_url(page_url)
        if not content:
            return f"Could not fetch Notion page: {page_url}"
        text = trafilatura.extract(content, include_comments=False, include_tables=True)
        if not text:
            return f"Could not extract text from Notion page: {page_url}"
        if len(text) > settings.max_url_content_length:
            text = text[: settings.max_url_content_length] + "\n\n[... truncated]"
        return text
    except Exception as e:
        return f"Notion page error: {e}"


# ---------------------------------------------------------------------------
# Tool groupings per agent
# ---------------------------------------------------------------------------

BA_TOOLS = [web_search, knowledge_search, docs_search, read_notion_page]
DEVELOPER_TOOLS = [web_search, docs_search, python_repl, run_command, file_write, file_read]
QA_TOOLS = [python_repl, run_command, file_read]
