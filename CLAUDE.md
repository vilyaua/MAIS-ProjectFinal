# CLAUDE.md — Final Project: Software Development Team (Multi-Agent System)

## Goal

Multi-agent system simulating an AI software development team: **Business Analyst → Developer → QA Engineer**. Takes a user story as input, analyzes requirements, writes code, and verifies quality through automated review and testing.

**Deadline:** 2026-04-27, 22:59

## Architecture Pattern

**Primary:** Evaluator-Optimizer (Anthropic) — Developer generates code, QA evaluates with structured output. If quality insufficient → return to Developer with feedback. Max 5 iterations.

**Linear part:** Prompt Chaining with HITL gate — User → BA → (user approves spec) → Developer.

**Interaction type:** Cooperative — all agents share a common goal (quality code).

```
User Story
    │
    ▼
┌─────────┐    SpecOutput     ┌──────────┐
│   BA    │──────────────────►│  HITL    │
│ Agent   │◄─── feedback ─────│  Gate    │
└─────────┘                   └────┬─────┘
    │ (DuckDuckGo, RAG)            │ approved
    │                              ▼
    │                        ┌──────────┐
    │                        │Developer │
    │                        │ Agent    │
    │                        └────┬─────┘
    │                   (REPL,    │ CodeOutput
    │                    Files)   ▼
    │                        ┌──────────┐
    │                  ┌────►│  QA      │
    │                  │     │ Agent    │
    │                  │     └────┬─────┘
    │                  │  (REPL,  │ ReviewOutput
    │                  │   Files) │
    │                  │          ▼
    │              REVISION   ┌────────┐
    │              NEEDED     │verdict?│
    │              (iter<5)   └───┬────┘
    │                  │          │ APPROVED
    │                  └──────────┼──────────►  END (final code + review)
    │                             │
```

## Project Layout

```
MAIS-ProjectFinal/
├── CLAUDE.md
├── README.md
├── pyproject.toml                    # ruff config
├── .pre-commit-config.yaml
├── .gitignore
├── course-project/                   # assignment specs (read-only)
└── dev-team/                         # implementation
    ├── main.py                       # REPL + HITL interrupt/resume + Langfuse
    ├── graph.py                      # LangGraph StateGraph + conditional edges
    ├── state.py                      # TypedDict state definition
    ├── nodes.py                      # Node functions: ba_node, dev_node, qa_node
    ├── agents/
    │   ├── __init__.py
    │   ├── ba.py                     # Business Analyst agent
    │   ├── developer.py              # Developer agent
    │   └── qa.py                     # QA Engineer agent
    ├── schemas.py                    # Pydantic: SpecOutput, CodeOutput, ReviewOutput
    ├── tools.py                      # @tool: web_search, knowledge_search, python_repl, file_write, file_read
    ├── config.py                     # Settings (pydantic-settings) — NO hardcoded prompts
    ├── langfuse_prompts.py           # Load all prompts from Langfuse Prompt Management
    ├── retriever.py                  # Hybrid retrieval: FAISS + BM25 + cross-encoder
    ├── ingest.py                     # PDF/MD ingestion → FAISS index
    ├── tests/
    │   ├── __init__.py
    │   ├── conftest.py               # Shared fixtures, LLM judge helper
    │   ├── test_ba.py                # BA spec quality (LLM-as-a-Judge)
    │   ├── test_developer.py         # Developer code correctness
    │   ├── test_qa.py                # QA review quality (intentionally bad code)
    │   └── test_e2e.py               # End-to-end pipeline test
    ├── requirements.txt
    ├── Dockerfile
    ├── docker-compose.yml
    ├── VERSION
    ├── DEVLOG.md
    ├── .env.example
    ├── .env                          # NEVER commit
    ├── data/                         # Docs for RAG (Python stdlib, style guides)
    ├── index/                        # Persisted FAISS + BM25 (gitignored)
    ├── workspace/                    # Developer-generated project files (gitignored)
    ├── output/                       # Final approved code packages
    ├── screenshots/                  # Langfuse UI screenshots
    └── logs/                         # Agent logs
```

## Agents

### Business Analyst (BA)
- **Role:** Receives user story, researches context, produces structured specification
- **Tools:** `web_search`, `knowledge_search` (RAG)
- **Output:** `SpecOutput` (structured)
- **Prompt name in Langfuse:** `ba-prompt`

### Developer
- **Role:** Receives approved spec, writes code, creates project files
- **Tools:** `web_search`, `python_repl`, `file_write`, `file_read`
- **Output:** `CodeOutput` (structured)
- **Prompt name in Langfuse:** `developer-prompt`
- **Safety:** Code execution sandboxed with timeout, restricted imports (no os.system, subprocess, shutil)

### QA Engineer
- **Role:** Reviews code, runs it, checks correctness, edge cases, spec compliance
- **Tools:** `python_repl`, `file_read`
- **Output:** `ReviewOutput` (structured, with_structured_output)
- **Prompt name in Langfuse:** `qa-prompt`

## Structured Output Contracts (Pydantic)

```python
class SpecOutput(BaseModel):
    title: str
    requirements: list[str]
    acceptance_criteria: list[str]
    estimated_complexity: Literal["simple", "medium", "complex"]

class CodeOutput(BaseModel):
    source_code: str
    description: str
    files_created: list[str]

class ReviewOutput(BaseModel):
    verdict: Literal["APPROVED", "REVISION_NEEDED"]
    issues: list[str]
    suggestions: list[str]
    score: float = Field(ge=0.0, le=1.0)
```

## LangGraph State & Workflow

### State (TypedDict)

```python
class DevTeamState(TypedDict):
    user_story: str                    # original user input
    spec: SpecOutput | None            # BA output
    spec_approved: bool                # HITL gate result
    spec_feedback: str                 # user feedback if not approved
    code: CodeOutput | None            # Developer output
    review: ReviewOutput | None        # QA output
    iteration: int                     # QA-Dev loop counter (max 5)
    review_history: list[ReviewOutput] # all QA reviews for context
    messages: list                     # LangGraph message history
```

### Graph (StateGraph)

```
START → ba_node → hitl_gate → (user approves?)
                                  ├─ NO  → ba_node (with feedback)
                                  └─ YES → dev_node → qa_node → routing
                                                                  ├─ REVISION_NEEDED & iter<5 → dev_node
                                                                  └─ APPROVED or iter>=5 → END
```

- **HITL gate:** Uses `interrupt()` from `langgraph.types`. User approves/rejects spec.
  Resume with `Command(resume={"approved": True/False, "feedback": "..."})`.
- **QA→Dev routing:** Conditional edge using `Command` API. QA returns `ReviewOutput`;
  if `verdict == "REVISION_NEEDED"` and `iteration < 5`, route back to `dev_node`
  with issues/suggestions as context.
- **Checkpointer:** `InMemorySaver` for interrupt/resume support.

## Tools Implementation

### python_repl
- Executes Python code in a subprocess with timeout (30s)
- **Security:** Block dangerous imports: `os.system`, `subprocess`, `shutil.rmtree`, `__import__`
- Captures stdout + stderr, returns combined output
- Working directory: `workspace/` (isolated from main project)

### file_write
- Writes files to `workspace/` directory only (path validation!)
- Creates subdirectories as needed
- Returns confirmation with absolute path

### file_read
- Reads files from `workspace/` directory only
- Returns file content with line numbers

### web_search
- DuckDuckGo via `ddgs` library (same pattern as L08/L12)
- Max 5 results, truncate to 3000 chars

### knowledge_search
- Hybrid RAG: FAISS + BM25 + cross-encoder reranking (same pattern as L05/L08)
- Searches Python docs, coding standards, framework tutorials

## RAG Data Preparation

Prepare 10-30 documents in `data/`:
- Python stdlib docs (key modules: typing, dataclasses, pathlib, unittest)
- Google Python Style Guide (as .md)
- FastAPI tutorial pages (if relevant to user stories)
- PEP 8 summary
- Common design patterns in Python

Run `python ingest.py` to build the index.

## Langfuse Integration

### Tracing
- `CallbackHandler` from `langfuse.langchain` on every LLM invocation (Langfuse v4)
- Trace attributes (session_id, user_id, tags) set via `propagate_attributes()` context manager
- Session ID (per conversation), User ID, tags
- Metadata: agent name, QA iteration number

### Prompt Management
- ALL system prompts loaded from Langfuse (zero hardcoded)
- Prompt names: `ba-prompt`, `developer-prompt`, `qa-prompt`
- Template vars: `{{max_iterations}}` for qa-prompt
- Label: `production`
- Module: `langfuse_prompts.py` with `get_system_prompt(name, **vars)`

### LLM-as-a-Judge Evaluators (Langfuse UI)
1. **Spec Completeness** (numeric 0-1): Does the spec have clear requirements and testable acceptance criteria?
2. **Code Quality** (numeric 0-1): Does the code follow best practices, handle errors, match the spec?

## LLM-as-a-Judge Tests (pytest)

| Test File | What | Scenario |
|-----------|------|----------|
| `test_ba.py` | BA produces complete spec | User story "email registration" → judge checks: requirements cover validation, edge cases, error handling |
| `test_developer.py` | Code matches spec | Spec with 3 requirements → judge checks each requirement is implemented |
| `test_qa.py` | QA catches real bugs | Submit intentionally bad code (hardcoded values, no error handling) → judge checks QA found issues |
| `test_e2e.py` | Full pipeline works | User story → approved code → judge evaluates quality, spec compliance |

### Judge Pattern
```python
def llm_judge(criteria: str, input_text: str, output_text: str) -> dict:
    """Call LLM to evaluate output against criteria. Returns {score: float, reasoning: str}."""
    # Uses the same model as agents
    # Returns structured JudgeResult(score, reasoning, passed)
```

## Dependencies

```
langchain>=1.2.15
langgraph>=1.1.0
langchain-openai>=1.2.0
langchain-community>=0.4.0
langchain-text-splitters>=1.1.0
langfuse>=4.5.0
pydantic>=2.0
pydantic-settings>=2.0
faiss-cpu>=1.13.0
rank_bm25>=0.2.2
sentence-transformers>=5.4.0
ddgs>=9.0.0
trafilatura>=2.0.0
pypdf>=6.10.0
httpx>=0.28.0
pytest>=8.0.0
```

## Environment Variables

```
OPENAI_API_KEY=sk-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
MODEL_POWERFUL=openai:gpt-4.1
MODEL_FAST=openai:gpt-4.1-mini
```

## Docker

```bash
cd dev-team
docker compose build
docker compose --profile tools run --rm ingest   # ingest docs for RAG
docker compose up                                 # interactive CLI
```

## Conventions

- Python 3.12+
- Ruff for linting/formatting (line-length=100)
- DEVLOG.md — update after every significant change
- VERSION file — single source of truth
- Use `create_agent` from `langchain.agents` for individual agents
- Use `StateGraph` from `langgraph` for the main workflow orchestration
- Structured output via `response_format=ToolStrategy(PydanticModel)` → access via `result["structured_response"]`
- All prompts from Langfuse (zero hardcoded in Python)

## Key Differences from Previous Homeworks

| Aspect | L08/L12 (Research) | Final Project (Dev Team) |
|--------|---------------------|--------------------------|
| Domain | Research & reports | Code generation & review |
| Agents | Planner, Researcher, Critic | BA, Developer, QA |
| Orchestration | Supervisor (create_agent) calling sub-agents as tools | StateGraph with nodes + conditional edges |
| Loop | Critic → Researcher (max 2) | QA → Developer (max 5) |
| HITL | save_report approval | Spec approval gate |
| New tools | — | python_repl, file_write, file_read |
| Output artifacts | Markdown reports | Project files in workspace/ |

## Grading Criteria (50 points total)

| Category | Points | What to demonstrate |
|----------|--------|---------------------|
| Architecture & code quality | 15 | Clean StateGraph, structured output, proper agent separation |
| Observability — Langfuse | 5 | Full tracing, session tracking, prompt management |
| Evaluation | 10 | 4 LLM-as-a-Judge tests with meaningful results |
| Complexity & depth | 15 | RAG, HITL, QA loop, REPL tool, file system tool |
| Demo & documentation | 5 | README with diagram, demo video/GIF, Langfuse screenshots |

## Deliverables

- [ ] Source code in Git repository
- [ ] Recorded demo (video or GIF)
- [ ] README with architecture diagram, setup instructions, usage examples
- [ ] Langfuse screenshots/links (traces, sessions, evaluators, prompts)
- [ ] LLM-as-a-Judge tests with results

## Do NOT

- Commit `.env` or API keys
- Hardcode system prompts in Python files (use Langfuse)
- Skip structured output for any agent
- Allow code execution without timeout/sandboxing
- Let QA loop exceed 5 iterations
- Write files outside `workspace/` directory from tools
