# One — Autonomous AI Factory

**Agents that own the job.** A local-substrate autonomous agent system that reasons, plans, builds, verifies, and ships — then spawns sub-agents to parallelize the work. No cloud. No external APIs. Air-gap capable.

Built by [Sovereign Developers](https://github.com/michaelwoolum50-cmyk).

---

## The problem

AI agents today need constant babysitting — prompts, retries, glue code. They don't own outcomes. You ask for a result; you get a draft that needs three more rounds of your time.

## The solution

One is a factory, not a chatbot. You give it a goal; it reasons about the plan, builds the solution, verifies its own work through a **triple loop** (write → verify → fix until clean), and ships the result — then spawns sub-agents to parallelize whatever comes next.

Everything runs on your own hardware: Llama 3.1 for reasoning, a FastAPI Agent Factory for orchestration, MCP tool access, and a Llama-Guard safety layer. Zero cloud bills. Zero data leaving the machine.

---

## Quick start

### Prerequisites

- [Ollama](https://ollama.com) installed
- Python 3.10+
- A GPU with enough VRAM for a 70B model (or start smaller — the factory is model-agnostic)

### 1. Pull the model and create One

```bash
ollama pull llama3.1:70b-instruct
ollama create one-70b -f modelfiles/Modelfile.one-70b
```

### 2. Configure

```bash
cd agents/
cp .env.example .env
# Edit .env — point OLLAMA_URL at your Ollama server (default http://localhost:11434)
pip install -r requirements.txt
```

### 3. Start the factory

```bash
uvicorn agent_factory:app --host 0.0.0.0 --port 8080
```

### 4. Give it a job

```bash
curl -X POST http://localhost:8080/spawn-agent \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a Python function that reads a CSV and returns summary stats"}'
```

The factory spawns an agent, runs it, verifies the output against the task, feeds failures back in, and returns only when the result passes — or tells you exactly why it couldn't.

### 5. Scale up (when your hardware is ready)

```bash
ollama pull llama3.1:405b-instruct-fp8
ollama create one-405b -f modelfiles/Modelfile.one-405b
# Set DEFAULT_MODEL=one-405b in agents/.env and restart
```

---

## How it works

```
You
 ↓
Agent Factory :8080  ← this repo
 ↓
Ollama :11434 → one-70b (or one-405b)
 ↓
Triple-loop verification (write → verify → fix)
 ↓
Verified result
```

**Triple-loop verification** is the core idea: every agent's output is checked by the model itself against the original task. If it fails, the failure feedback becomes the next attempt's input. Up to 3 loops (configurable via `MAX_VERIFY_LOOPS`). Nothing ships unverified without saying so.

**Recursive spawning:** `/build-repo` takes a plain-English description and spawns an architecture agent, then implementation agents — a whole build pipeline from one call.

## API

| Endpoint | Method | What it does |
|----------|--------|--------------|
| `/health` | GET | Status check |
| `/spawn-agent` | POST | Spawn a task agent with triple-loop verification |
| `/build-repo` | POST | Autonomous repo builder from a description |
| `/agents` | GET | List active and completed agents |

## Repo layout

```
OneFactory/
├── README.md                        ← you are here
├── agents/
│   ├── agent_factory.py             ← FastAPI factory (:8080)
│   ├── requirements.txt
│   └── .env.example                 ← copy to .env, fill in your values
├── docs/
│   └── README.md                    ← deep-dive documentation
├── mcp/
│   └── one_mcp_config.json          ← MCP tool wiring (edit hosts to match your network)
├── modelfiles/
│   ├── Modelfile.one-70b            ← start here
│   └── Modelfile.one-405b           ← scale up when ready
├── prompts/
│   └── ONE_SYSTEM_PROMPT.md         ← the agent system prompt
└── ai_co_architect_notes/
    └── 01_copilot_suggestions.md    ← design notes & roadmap
```

## Safety

- Llama-Guard-4-12B safety layer (see `mcp/one_mcp_config.json`)
- The factory never ships code it can't verify — max loops reached returns `unverified`, loudly
- Runs fully local: nothing is sent to any cloud service, ever

## License

MIT — build on it, ship with it, make it yours.
