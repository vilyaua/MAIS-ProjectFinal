# AI Dev Team — Final Project Presentation

## Slide 1: Title

**AI Dev Team — Multi-Agent Software Development System**

Vitalii Perminov | MAIS Final Project | May 2026

Multi-agent system that takes a user story and autonomously produces
production-quality code with tests, QA review, and a GitHub PR.

---

## Slide 2: Problem & Goal

**Problem:** Writing code from a user story requires multiple skills —
requirements analysis, implementation, testing, code review.

**Goal:** Automate this with a team of AI agents that collaborate:
- Business Analyst → analyzes requirements
- Developer → writes code
- QA Engineer → reviews and tests

**Pattern:** Evaluator-Optimizer (Dev ↔ QA loop) + Prompt Chaining + HITL

---

## Slide 3: Architecture

> Use the mermaid diagram from README or a screenshot

```
User Story → BA Agent → [HITL Gate] → Developer → QA Engineer → GitHub PR
                ↑                         ↑            |
                |                         |   REVISION  |
                |                         +←←←←←←←←←←←←+
                |
             feedback
```

**Key decisions:**
- LangGraph StateGraph with conditional edges
- `interrupt()` for Human-in-the-Loop spec approval
- Max 5 QA→Dev revision iterations
- GitHub node after QA approval

---

## Slide 4: Agents & Models

| Agent | Model | Role | Why this model |
|-------|-------|------|----------------|
| BA | gpt-4.1-mini | Spec generation | Cheap, 1 call is enough |
| Developer | gpt-5.5 | Code writing | Best code quality, fewer calls, no revisions |
| QA | gpt-5.4 | Code review | Thorough analysis, approves first try |

**Key insight:** Cheaper models (gpt-4.1-mini) produce worse code →
QA rejects → revision loops → MORE total cost.
gpt-5.5 costs 3x per token but uses 70% fewer calls.

---

## Slide 5: Tools (8 total)

| Tool | Agent | What it does |
|------|-------|-------------|
| knowledge_search | BA | RAG — FAISS + BM25 + cross-encoder (23 docs) |
| read_notion_page | BA | Read user stories from Notion |
| web_search | Dev | DuckDuckGo search |
| docs_search | Dev | Context7 MCP — live library documentation |
| python_repl | Dev, QA | Sandboxed code execution |
| run_command | Dev, QA | Terminal commands (python, pytest, ls) |
| file_write | Dev | Create files in workspace |
| file_read | Dev, QA | Read files from workspace |

**Integrations:** Context7 via MCP Protocol, GitHub via PyGithub (Git Trees API)

---

## Slide 6: Demo — Pipeline in Action

> Screenshots from the 5 demo runs (use 2-3 best screenshots)

1. **Input** → User types a story
2. **Spec Review** → BA produces spec, user approves (HITL)
3. **Code Generated** → Dev writes files, clickable tabs to view each
4. **QA Review** → Score 0.95+, APPROVED
5. **PR Created** → Link to GitHub PR
6. **Results Saved** → Output package with README

> Or show the live demo video here

---

## Slide 7: Token Optimization Journey

| Metric | v0.1 (start) | v2.6 (final) | Change |
|--------|-------------|-------------|--------|
| BA tokens | 5–9k (5-6 calls) | 800 (1 call) | **-90%** |
| Dev calls | 10–13 | 3–4 | **-70%** |
| QA calls | 8 | 3 | **-63%** |
| Revisions per run | 1–2+ | 0 | **-100%** |
| Success rate | ~30% | 100% | **+70pp** |
| Cost per run | $0.12–crash | $0.10–0.25 | **predictable** |

**What worked:**
- Model upgrade (gpt-5.5 for Dev)
- Remove unnecessary tools from BA
- Strict QA prompt: "read → test → verdict"
- `run_command` instead of inline code pasting

---

## Slide 8: The SummarizationMiddleware Trap

> This is the most interesting technical story

**What:** LangChain middleware that compresses conversation history.

**Expected:** 19% token savings (measured by our tracker).

**Reality:** Middleware makes its own LLM calls — invisible to our callback.
Our tracker showed 8,600 tokens. OpenAI reported **200,000 tokens**.

**190k+ tokens burned silently.**

**Lesson:** Never trust a metric you can't fully observe.
Always log every LLM call: start, end, error, tokens.

---

## Slide 9: Observability — Langfuse

> Screenshots from Langfuse dashboard

- **Tracing:** Every LLM call with input/output, tokens, latency
- **Sessions:** Pipeline runs grouped by session
- **Prompt Management:** 3 prompts, version-controlled, zero hardcoded
- **Cost tracking:** Per-model, per-run, all-time statistics

**All-time stats:**
- 50+ pipeline runs
- ~$12 total project spend
- 3 Langfuse evaluators: spec-quality, code-correctness, qa-thoroughness
- 10/10 LLM-as-a-Judge pytest tests passing

---

## Slide 10: Demo Results — 10 Test Cases

**English demos:**

| # | Demo | Tokens | Cost |
|---|------|--------|------|
| 1 | ASCII Art Generator | 45k | $0.16 |
| 2 | Password Generator CLI | 29k | $0.11 |
| 3 | Markdown→HTML Library | 24k | $0.10 |
| 4 | CSV Data Analyzer | 77k | $0.27 |
| 5 | Flask REST API + SQLite | 43k | $0.16 |

**Russian/logistics demos:**

| # | Demo | Tokens | Cost |
|---|------|--------|------|
| 6 | Landed Cost Calculator | 46k | $0.17 |
| 7 | Container Loader CLI | 50k | $0.18 |
| 8 | Invoice/Packing Parser | 107k | $0.38 |
| 9 | Payment Reconciliation | 156k | $0.55 |
| 10 | Supply Chain REST API | 65k | $0.27 |

**10/10 passed. Zero revisions. Multilingual. All produced working code
with tests, READMEs, and GitHub PRs.**

---

## Slide 11: Tech Stack

- **LangChain** — `create_agent`, `ToolStrategy`, structured output
- **LangGraph** — `StateGraph`, `interrupt()`, conditional edges
- **Langfuse v4** — tracing, `propagate_attributes()`, prompt management
- **MCP** — Model Context Protocol (Context7 for library docs)
- **PyGithub** — Git Trees API for single-commit PRs
- **FastAPI** — Web UI with SSE streaming
- **FAISS + BM25** — Hybrid RAG with cross-encoder reranking
- **Playwright** — Automated UI testing & screenshots
- **Docker** — Containerized deployment
- **Ruff + pre-commit** — Code quality hooks

---

## Slide 12: Key Takeaways

1. **Per-pipeline cost > per-token cost** — a strong model making 3 calls
   beats a weak model making 13 calls

2. **Remove tools you don't need** — the model WILL use every available tool.
   Prompt instructions are suggestions; tool availability is a constraint

3. **Full observability from day one** — per-call token logging caught the
   SummarizationMiddleware disaster that "saved 19%" but actually cost 20x more

4. **Rate limits are architecture** — check TPM limits before choosing models.
   30k TPM is unusable for multi-agent systems

5. **Measure end-to-end, not components** — local optimization can hide
   global regression

---

## Video Script (3-5 min)

### Opening (30s)
"This is AI Dev Team — a multi-agent system that takes a user story and
produces production-quality code. Let me show you how it works."

### Live Demo (2-3 min)
1. Open localhost:8000, show the UI
2. Type: "Build a CLI password generator with a strength meter"
3. Show BA producing spec (point out: 1 call, ~800 tokens)
4. Approve the spec
5. Show Developer writing code (point out: gpt-5.5, 3-4 calls)
6. Show QA reviewing (point out: score 0.95+, APPROVED first try)
7. Show PR created on GitHub
8. Click a file tab to show generated code
9. Show the output directory with README

### Langfuse (30s)
Switch to Langfuse, show:
- Latest trace with the full pipeline
- Token costs per model
- Prompt management with v3 production

### Closing (30s)
"The system costs about $0.10-0.25 per run. We optimized from 43k tokens
with constant failures to 24-30k tokens with 100% success rate. The key
insight: spending more per token on a better model saves money overall
because it eliminates revision loops."
