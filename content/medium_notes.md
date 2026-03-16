# Medium Article Notes — strands-multi-engineer-agent

> Working notes for the article. Not published content.

---

## Working title

**"Building a Multi-Model Engineering Agent with AWS Strands: One Workflow, Three Providers"**

---

## Core narrative

The article walks through building a portable CLI engineering agent where the
**exact same workflow** runs against Anthropic Claude, OpenAI GPT-4o, and a
local Ollama model — and you compare the results.

The interesting story is not "which model is smarter" but:
- How AWS Strands makes provider-swapping trivial
- What portability actually means in practice (env vars, Docker, no assumptions)
- Where models differ in *behaviour* — tool-calling patterns, verbosity, confidence

---

## Sections (draft outline)

### 1. The problem
- Running a real engineering task (inspect repo → plan → code → review)
- Usually you pick one model and commit
- What if the workflow was the constant, not the model?

### 2. AWS Strands in 2 minutes
- What it is: open-source Python agent framework from AWS
- Key idea: `Agent(model=..., tools=[...])` — model is just a config
- Comparison to LangChain / LlamaIndex: simpler, more explicit

### 3. Architecture walkthrough
- `agent/workflow.py` — the 4-phase loop
- `providers/base_provider.py` — the factory pattern
- `agent/config.py` — env-var-first config with Pydantic
- Tools: repo_reader, search, patch_writer, test_runner

### 4. Portability principles
- Why env vars are non-negotiable
- Docker Compose as the Ollama baseline
- No host assumptions

### 5. Running the comparison
- `agent run --provider anthropic --task fastapi-missing-validation`
- `agent run --provider openai --task fastapi-missing-validation`
- `agent run --provider ollama --task fastapi-missing-validation`
- Show the results JSON

### 6. What I observed
- [ ] Fill in after running actual comparisons
- Token counts, latency, tool-use patterns
- Which provider needed the most iterations?
- Self-review confidence scores

### 7. What's next
- Kubernetes deployment notes
- Adding more providers (Bedrock, Gemini)
- Evaluation scoring beyond self-review

---

## Code snippets to highlight

- `get_strands_model()` factory — 20 lines, adds a provider
- `AgentConfig.doctor_report()` — zero-secret health check
- The `@tool` decorator pattern
- `WorkflowResult` Pydantic schema

---

## Things to benchmark per task

| Metric | Anthropic | OpenAI | Ollama |
|---|---|---|---|
| Total time (s) | | | |
| Input tokens | | | |
| Output tokens | | | |
| Tool calls made | | | |
| Confidence score | | | |
| Code correct? (manual) | | | |

---

## Tone notes

- Practical, not theoretical
- Show real code, real output
- Honest about what worked and what didn't
- Accessible to engineers who haven't used Strands before
