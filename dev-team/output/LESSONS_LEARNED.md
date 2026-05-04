# Lessons Learned — Building a Multi-Agent AI Dev Team

> A practical guide from building, optimizing, and debugging a multi-agent system
> that takes a user story and produces production-quality code with tests, QA review,
> and a GitHub PR — all autonomously.

## The Project

Three AI agents — Business Analyst, Developer, QA Engineer — collaborate in a
LangGraph pipeline. The BA analyzes a user story and produces a spec. The user
approves it (Human-in-the-Loop). The Developer writes code. QA reviews and either
approves or sends it back for revision. Approved code gets pushed to GitHub as a PR.

**Final result:** 5 demo runs completing reliably at $0.10–0.25 each, with QA
scoring 0.95–0.98 and zero revision loops.

Getting there took many iterations. Here's what we learned.

---

## 1. Model Selection Matters More Than Prompt Engineering

### What we tried

| Version | BA | Developer | QA | Result |
|---------|-----|-----------|-----|--------|
| v0.1 | gpt-4.1-mini | gpt-4.1 | gpt-4.1-mini | Rate limited (30k TPM) |
| v1.0 | gpt-4.1-mini | gpt-4.1-mini | gpt-4.1-mini | Cheap per-token but terrible code, QA scored 0.30, constant revisions |
| v2.0 | gpt-5.4-mini | gpt-5.5 | gpt-5.4 | BA over-researched, QA over-analyzed |
| **v2.2** | **gpt-4.1-mini** | **gpt-5.5** | **gpt-5.4** | **Best: 3-4 Dev calls, QA approves first try** |

### The lesson

**Cheaper models cost more in total.** gpt-4.1-mini produced code that QA rejected
at 0.30, triggering revision loops that consumed 100k+ tokens. gpt-5.5 wrote
correct code in 3–4 calls that QA approved at 0.95+ on the first try.

A single gpt-5.5 call costs ~3x more than gpt-4.1-mini, but the pipeline uses
3 calls instead of 13, and eliminates 30–60k tokens of revision loops.

**Per-token cost is irrelevant. Per-pipeline cost is what matters.**

### The surprise

gpt-4.1 seemed like a good middle ground but had the worst TPM limit (30k at Tier 1).
The pipeline couldn't even finish a single run without hitting rate limits.
Meanwhile, gpt-5.5 had 500k TPM — 16x more headroom.

---

## 2. Rate Limits Are an Architecture Constraint, Not a Bug

### OpenAI Tier 1 limits

| Model | TPM Limit | Impact |
|-------|-----------|--------|
| gpt-4.1 | 30,000 | Unusable — single Dev run exceeds it |
| gpt-4.1-mini | 200,000 | Tight — one pipeline run uses 30–100k |
| gpt-5.5 / gpt-5.4 | 500,000 | Comfortable — no rate limit issues |

### What we learned

- **TPM is per-minute, not per-request.** A fast agent making 10 calls in 30 seconds
  can exhaust the budget before completing.
- **Retries consume tokens too.** OpenAI counts tokens even on 429 responses.
  With `max_retries=8`, the system burned tokens retrying failures.
- **Different models have separate TPM pools.** Using gpt-4.1-mini for BA/QA and
  gpt-5.5 for Dev spreads the load across two pools.
- We reduced `max_retries` from 8 to 4 to fail faster on quota errors instead of
  burning money on retries.

---

## 3. The SummarizationMiddleware Disaster

### What happened

LangChain's `SummarizationMiddleware` promises to compress conversation history,
reducing token usage. We added it to the QA agent with `trigger=4000, keep=6`.

**Initial measurement showed 19% token savings.** We celebrated.

### The reality

The middleware makes its own LLM calls to summarize — and those calls are invisible
to our token tracking callback. When we added verbose per-call logging, we discovered:

- Our tracker showed QA using 8,600 tokens
- OpenAI reported **200,000 tokens consumed** in the same period
- The middleware was silently burning **190k+ tokens** for summarization calls

**The "19% savings" was an illusion.** The middleware saved visible tokens but
consumed 20x more invisible ones.

### The fix

Removed `SummarizationMiddleware` entirely. The QA agent now uses a strict 3-step
prompt ("read → test → verdict") that naturally limits tool calls to 3–4.

### The lesson

**Never trust a metric you can't fully observe.** Any middleware or abstraction that
makes LLM calls needs to be visible in your token tracking. We added `on_llm_start`,
`on_llm_end`, and `on_llm_error` logging to catch every call.

---

## 4. Prompt Engineering: Less Is More

### BA Agent — removing tools was better than instructions

We tried telling BA: "For standard Python tasks, produce the spec DIRECTLY.
Do NOT search." The model ignored this and searched anyway — because the tools
were available.

**What worked:** Removing `web_search` and `docs_search` from BA's tool list entirely.
With only `knowledge_search` and `read_notion_page` available, BA produces specs in
1 call, ~800 tokens. Previously: 5–6 calls, 6–9k tokens.

**The lesson:** If you don't want the model to use a tool, don't give it the tool.
Prompt instructions are suggestions; tool availability is a constraint.

### QA Agent — strict process eliminates waste

The QA prompt evolved through three versions:

**v1 (vague):** "Review code for correctness, quality, and compliance."
→ QA made 8 calls, read files multiple times, ran random tests, scored 0.30.

**v2 (detailed):** "1. Read files 2. Run tests 3. Check compliance 4. Return verdict"
→ QA made 4–5 calls, sometimes skipped files, scored 0.50–0.60.

**v3 (strict):** "Exact steps: read ALL files → run pytest → return verdict. Do NOT deviate."
→ QA makes 3 calls, scores 0.95–0.98.

**The lesson:** For tool-using agents, vague instructions cause meandering. Strict,
ordered instructions with explicit "do NOT" constraints are more effective.

### Developer Agent — revision workflow must be explicit

When QA rejected code, the Developer would rewrite everything from scratch — same
7 calls, same token cost. Adding "Files already exist. Read them. Fix ONLY the
issues" to the revision prompt reduced revision cost by ~40%.

But the most effective fix was making the Developer good enough that revisions
don't happen at all (by using gpt-5.5).

---

## 5. The ReAct Loop Context Balloon

### The problem

`create_agent` uses a ReAct loop internally. Each tool call adds the full
conversation history to the next LLM call:

```
Call 1:  system + user prompt           → 1k tokens input
Call 2:  system + user + call1 + result → 2k tokens input
Call 3:  all of above + call2 + result  → 3.5k tokens input
...
Call 10: everything                     → 12k tokens input
```

By call 10, the model is re-reading all previous tool results that it has already
processed. This is the main driver of token cost.

### What helps

- **Fewer tool calls** — gpt-5.5 makes 3–4 calls vs gpt-4.1-mini's 10–13
- **Shorter tool outputs** — `run_command("python -m pytest tests/ -v")` returns
  test results in ~100 tokens vs `python_repl` pasting entire files (~400+ tokens)
- **Don't send data twice** — we removed inline `source_code` from the QA prompt
  (QA was receiving code in the prompt AND reading it via `file_read`)

---

## 6. Token Tracking: You Need Full Visibility

### Evolution of our tracking

**v1: No tracking.** We had no idea why runs failed or how many tokens were used.
The first sign of problems was OpenAI billing alerts.

**v2: `on_llm_end` callback.** Captured tokens from successful completions.
But showed 0 for some runs because the callback path (`response.llm_output`)
didn't always have token data.

**v3: Verbose per-call logging.** Added `on_llm_start`, `on_llm_end`, `on_llm_error`
with model name, input/output tokens, running total. Every LLM call is visible:

```
LLM call #1 started (model=gpt-5.5)
LLM call #1 done: in=1271 out=2683 model=gpt-5.5 | running total: 4794
LLM call #2 started (model=gpt-5.5)
...
```

**v4: Delta logging per step.** Instead of cumulative totals, each node logs
how many tokens IT consumed:

```
BA Agent: tokens: 840 (in: 442, out: 398) | cost: $0.0041 | calls: 1
Developer: tokens: 12,208 (in: 9,382, out: 2,826) | cost: $0.0621 | calls: 3
QA: tokens: 11,458 (in: 11,266, out: 192) | cost: $0.0301 | calls: 3
Pipeline total: tokens: 24,506 | cost: $0.0962 | calls: 7
```

### The lesson

**Build observability from day one.** Token tracking, Langfuse tracing, and
per-call logging together give a complete picture. Without them, you're debugging
in the dark.

---

## 7. Changes We Reverted (And Why)

| Change | Why we tried it | Why we reverted it |
|--------|----------------|-------------------|
| SummarizationMiddleware on QA | 19% visible token savings | Silently burned 190k+ tokens via hidden LLM calls |
| SummarizationMiddleware on Dev | Same as QA | Caused token explosion, exceeded 200k TPM immediately |
| gpt-5.4-mini for BA | "Smarter model won't search" | Searched MORE than gpt-4.1-mini (more curious) |
| All agents on gpt-4.1-mini | Cost reduction | Worse code → revision loops → MORE total cost |
| `model_kwargs={"max_retries": 8}` | Better rate limit handling | `create_agent` doesn't accept `model_kwargs` |
| `CallbackManager` in list | Add token tracker alongside Langfuse | `CallbackManager` is not iterable |
| `allowed_msgpack_modules` on compile | Fix serialization warning | Not a valid parameter on `compile()` or `InMemorySaver()` |
| `max_retries=8` | Survive rate limits | Too aggressive for quota errors, wasted 30s retrying |
| `.startswith(".")` skip in workspace cleanup | Keep hidden files | Left `.pytest_cache` behind, polluting workspace |

### The lesson

**Every optimization should be measured end-to-end.** Local improvements (fewer
visible tokens) can mask global regressions (invisible token explosion). Always
compare total pipeline cost, not component metrics.

---

## 8. Architecture Decisions That Worked

### Tool-per-purpose design

8 tools, each with a clear purpose. No tool does two things. The allowlist-based
`run_command` is safer than `python_repl` for file execution. Removing tools
from agents is more effective than telling them not to use tools.

### Separate models per agent role

Not all agents need the same model. BA needs speed and cheapness (gpt-4.1-mini).
Developer needs code quality (gpt-5.5). QA needs analytical depth (gpt-5.4).
This also spreads TPM load across separate rate limit pools.

### GitHub integration as a graph node

Making GitHub PR creation a node in the LangGraph (`github_node`) instead of a
post-processing hook keeps it in the observable pipeline. It gets traced in
Langfuse, errors are caught, and the PR URL flows through the state to the UI.

### Single commit via Git Trees API

Instead of one `create_file` call per file (N commits), we use `create_git_blob` +
`create_git_tree` + `create_git_commit` for a single atomic commit. Cleaner PRs,
fewer API calls.

### Langfuse for everything

Zero hardcoded prompts. All three system prompts live in Langfuse with version
control and `production` labels. Changing a prompt doesn't require a code deploy —
just update in Langfuse and restart the container.

---

## 9. Final Numbers

### Cost per demo (v2.2.0)

| Demo | Complexity | Tokens | Cost | Dev Calls | QA Score |
|------|-----------|--------|------|-----------|----------|
| ASCII Art Generator | simple | ~25k | ~$0.10 | 3 | 0.95+ |
| Password Generator | simple | 31k | $0.12 | 4 | 0.95+ |
| Markdown to HTML | medium | 59k | $0.22 | 8 | 0.97 |
| CSV Data Analyzer | medium | 42k | $0.16 | 3 | 0.95+ |
| Flask REST API | complex | 69k | $0.25 | 7 | 0.95+ |

### All-time project statistics (Langfuse)

- Total LLM calls: 1,000+
- Total tokens: 7.8M+
- Total spend: ~$4.80
- Pipeline runs completed: 50+
- Total spend: ~$12+
- Prompt versions: 3 iterations each
- Models tested: 6 (gpt-4.1, gpt-4.1-mini, gpt-5.4, gpt-5.4-mini, gpt-5.5)
- 10 demo test cases (5 English + 5 Russian/logistics)

### Optimization journey

| Metric | v0.1 | v2.6 | Improvement |
|--------|------|------|-------------|
| BA tokens | 5–9k | 800 | **-90%** |
| Dev calls | 10–13 | 3–5 | **-70%** |
| QA calls | 8 | 3–4 | **-60%** |
| Revisions per run | 1–2+ | 0 | **-100%** |
| Pipeline success rate | ~30% | 100% | **+70pp** |
| Cost (simple) | $0.12–crash | $0.10–0.17 | **predictable** |
| Cost (complex) | crash | $0.27–0.55 | **works** |

---

## 10. What We'd Do Differently

1. **Start with the best model, optimize down** — not the other way around. We wasted
   days debugging rate limits and revision loops that simply didn't exist with gpt-5.5.

2. **Add per-call token logging from day one** — not after discovering 190k invisible
   tokens. The `on_llm_start` / `on_llm_end` / `on_llm_error` pattern should be
   standard in any LLM application.

3. **Test rate limits before building** — check your OpenAI tier and model TPM limits
   before choosing models. A model with 30k TPM is unusable for multi-agent systems.

4. **Don't trust abstractions blindly** — SummarizationMiddleware, CallbackManager,
   and other LangChain internals have behaviors that aren't obvious from the docs.
   Always verify with end-to-end measurements.

5. **Fewer tools = better performance** — every tool the model sees is a potential
   unnecessary call. Give agents the minimum tool set they need.
