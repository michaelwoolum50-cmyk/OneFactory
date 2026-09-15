# One — AI Factory
## Local Substrate Autonomous Agent System

Built for: michaelwoolum50-cmyk
Stack: Llama 3.1 70B → 405B | Triple-loop verification | MCP tool access | Agent spawning

---

## What This Is

An autonomous AI factory running entirely on your local substrate.
No cloud. No external APIs. Air-gap capable.

One reasons, plans, builds, verifies, and ships — then spawns sub-agents to parallelize work.

---

## Stack

| Layer | Component | Purpose |
|-------|-----------|---------|
| Reasoning | Llama 3.1 70B Instruct | Core brain — start here |
| Deep reasoning | Llama 3.1 405B Instruct FP8 | Scale up when substrate ready |
| Code | GPT-5.3 Coder triple-loop | Write → verify → fix until clean |
| Tools | Agentic MCP repo | File system, shell, GitHub, fetch |
| Skills | GitHub awesome skill sets | Pre-built capabilities |
| Orchestration | Agent Factory (FastAPI :8080) | Spawn and manage sub-agents |
| Safety | Llama-Guard-4-12B | Keep the system clean |

---

## Quick Start

### Step 1 — Pull the model
```bash
ollama pull llama3.1:70b-instruct
```

### Step 2 — Create the One modelfile
```bash
ollama create one-70b -f modelfiles/Modelfile.one-70b
ollama run one-70b
```

### Step 3 — Start the Agent Factory
```bash
cd agents/
cp .env.example .env
# Edit .env with your network IPs
pip install -r requirements.txt
uvicorn agent_factory:app --host 0.0.0.0 --port 8080
```

### Step 4 — Test it
```bash
curl -X POST http://localhost:8080/spawn-agent \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a Python function that reads a CSV and returns summary stats"}'
```

### Step 5 — Scale up (when ready)
```bash
ollama pull llama3.1:405b-instruct-fp8
ollama create one-405b -f modelfiles/Modelfile.one-405b
# Update DEFAULT_MODEL=one-405b in .env
```

---

## Architecture

```
[You / Trinity Frontend]
        ↓
[Agent Factory :8080]  ←── This repo
        ↓
[Ollama :11434 → one-70b or one-405b]
        ↓
[MCP Tools: filesystem, shell, github, fetch, memory]
        ↓
[Sub-agents spawned as needed]
        ↓
[Output verified via triple-loop]
        ↓
[Result returned / pushed to GitHub]
```

---

## Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Status check |
| `/spawn-agent` | POST | Spawn a task agent with verification |
| `/build-repo` | POST | Full autonomous repo builder |
| `/agents` | GET | List all active/completed agents |

---

## Environment Boundaries

- **Trinity (SovereignOne)** — SEALED. Never write to it. Read-only health check only.
- **Scout-Bot** — Separate. Market data source if needed.
- **One (Base44)** — Venture prediction engine. Separate cloud layer.
- **This factory** — Your local substrate. Builds everything else.

---

## Upgrading

When your GPU substrate is ready for 405B:
1. `ollama pull llama3.1:405b-instruct-fp8`
2. `ollama create one-405b -f modelfiles/Modelfile.one-405b`
3. Change `DEFAULT_MODEL=one-405b` in `.env`
4. Restart the factory

No other changes needed. The factory is model-agnostic.

---

## Files

```
ai_factory/
├── prompts/
│   └── ONE_SYSTEM_PROMPT.md      ← The reasoning clone prompt
├── modelfiles/
│   ├── Modelfile.one-70b         ← Start here
│   └── Modelfile.one-405b        ← Scale up when ready
├── mcp/
│   └── one_mcp_config.json       ← MCP tool wiring
├── agents/
│   ├── agent_factory.py          ← FastAPI agent spawner :8080
│   ├── requirements.txt
│   └── .env.example
└── docs/
    └── README.md                 ← This file
```
