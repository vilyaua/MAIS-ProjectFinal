# Dev Log

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
