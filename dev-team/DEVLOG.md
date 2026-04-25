# Dev Log

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
