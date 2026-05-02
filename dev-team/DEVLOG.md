# Dev Log

## 2026-05-02, v2.3.0 — Notion API integration

- `read_notion_page` rewritten to use Notion API (was trafilatura — failed on JS-rendered pages)
- Extracts headings, paragraphs, lists, code blocks, to-dos from Notion blocks API
- Requires `NOTION_TOKEN` in .env (Notion internal integration secret)
- Added `notion_token` to Settings config
- Demo: Notion page → expense tracker CLI, 48.9k tokens, $0.18, QA approved

## 2026-05-02, v2.2.0 — model upgrade + prompt tuning + polish

- Model upgrade: BA=gpt-4.1-mini, Dev=gpt-5.5 (500k TPM), QA=gpt-5.4 (500k TPM)
  - gpt-5.5 writes code in 3-4 calls (was 10-13), QA approves 0.95-0.97 first try
  - Zero revision loops — eliminates the #1 cost driver
  - $0.10-0.12 per run, 24-30k tokens, 7-8 LLM calls
- Prompt tuning (all prompts in Langfuse, version 3):
  - BA: "Do NOT search. Produce spec directly." + removed web_search/docs_search tools
  - Dev: explicit FIRST-TIME vs REVISION workflows, source_code left empty
  - QA: strict 3-step process (read → test → verdict), no deviation
- Removed SummarizationMiddleware (was silently burning 190k+ mini tokens)
- Token tracker: verbose per-call logging (start/end/error for every LLM call)
- RAG data expanded: 18 → 23 docs (added argparse, csv, sqlite3, secrets, Flask)
- Workspace cleanup: removes ALL files including .pytest_cache
- UI: clickable file tabs in Generated Code card, colored console logs,
  flushing file handler, HITL step turns green, no duplicate PR link
- GitHub: InputGitTreeElement for single-commit PRs, skips cache dirs
- Pre-commit hooks: ruff lint+format, trailing whitespace, security checks
- Demo requests: 5 sample user stories at output/demo-requests.md

## 2026-05-01, architect-level optimizations

- Token usage optimization (calculator test: 43k → 39k tokens, QA: 25k → 15k):
  - Removed inline `source_code` from QA prompt — QA reads files via tools only
  - Added `SummarizationMiddleware` to QA agent (trigger: 4k tokens, keep: 6 messages)
  - BA prompt instructs to skip search for standard Python tasks (8k → 937 tokens)
  - Removed `SummarizationMiddleware` from Developer (caused token explosion at Tier 1)
- New tools:
  - `run_command` — run shell commands in workspace (python, pytest, ls, etc.)
    with allowlist-based validation. Saves tokens vs pasting code into python_repl
  - `read_notion_page` — fetch Notion page content as user story input for BA
- Token tracking improved:
  - Logs per-step deltas instead of cumulative totals
  - `snapshot()` + `delta_summary()` methods on `TokenUsage`
- GitHub integration improved:
  - Single commit via Git Trees API (was one commit per file)
- Other fixes:
  - `max_retries` reduced from 8 to 4 (fails faster on quota errors)
  - `CodeOutput.source_code` made optional (files in workspace are the code)
  - Removed `pip` from `run_command` allowlist (security)
  - Cached agent instances to avoid repeated Langfuse prompt fetches
  - Fixed `model_kwargs` TypeError — use `init_chat_model()` pre-built model
  - Fixed `CallbackManager` not iterable — token tracker added at app level
  - Fixed UI scrolling (flex-shrink, code block max-height)
  - Fixed GitHub PR link display in web UI

## 2026-04-30, token cost logging + UI fixes

- Added `token_tracker.py` — lightweight callback handler for cost logging
- Per-agent and pipeline total token/cost logging in nodes
- Fixed scrolling in web UI (flex layout, code block overflow)
- All agents switched to `gpt-4.1-mini` for cost efficiency
- Playwright automated screenshots for pipeline testing

## 2026-04-29, Context7 MCP + GitHub PR integration

- Added Context7 MCP integration for library documentation search:
  - New `docs_search` tool using MCP Python SDK + `@upstash/context7-mcp`
  - Available to BA (research) and Developer (implementation) agents
  - Resolves library ID, then queries up-to-date docs
  - Dockerfile updated to include Node.js 22 + context7-mcp
- Added GitHub integration for automatic PR creation:
  - New `github_integration.py` module using PyGithub
  - Creates branch `dev-team/<slug>`, commits workspace files, opens PR
  - PR body includes spec, requirements, acceptance criteria, QA review
  - New `github_node` in LangGraph StateGraph (after QA approval → GitHub → END)
  - Optional: skipped when `GITHUB_TOKEN` not configured
- Updated web UI:
  - New "GitHub PR" step in pipeline sidebar
  - PR link displayed in results card when available
- Config changes:
  - `github_token`, `github_repo`, `github_base_branch` added to Settings
  - BA and QA agents switched to `model_fast` (gpt-4.1-mini) to reduce TPM pressure
  - All agents set `max_retries=8` for better rate limit handling
- Dependencies added: `mcp>=1.9.0`, `PyGithub>=2.6.0`

## 2026-04-25, upgrade to latest libraries + RAG data

- Upgraded all dependencies to April 2026 latest versions:
  - langchain 1.2.15, langgraph 1.1.0, langchain-openai 1.2.0
  - langfuse 4.5.0 (v4 — major rewrite from v3)
  - sentence-transformers 5.4.0, ddgs 9.0, pypdf 6.10, faiss-cpu 1.13
- Migrated code for Langfuse v4 breaking changes:
  - `from langfuse.callback import CallbackHandler` → `from langfuse.langchain import CallbackHandler`
  - Constructor no longer accepts session_id/user_id/tags; now uses `propagate_attributes()` context manager
- Migrated to LangChain 1.2.x structured output pattern:
  - `response_format=Model` → `response_format=ToolStrategy(Model)` in all agents
- Populated data/ with 18 RAG documents:
  - PEP 8, Google Python Style Guide
  - Python stdlib: typing, dataclasses, pathlib, unittest, logging, collections, itertools, functools, contextlib, json, re
  - Design patterns, error handling, abc, async/await, Pydantic

## 2026-04-25, initial scaffold

- Created project structure: dev-team/
- Added config.py (pydantic-settings), schemas.py (SpecOutput, CodeOutput, ReviewOutput)
- Added langfuse_prompts.py for Langfuse Prompt Management
- Created requirements.txt, Dockerfile, docker-compose.yml
- Set up .gitignore, .env.example, VERSION (0.1.0)
