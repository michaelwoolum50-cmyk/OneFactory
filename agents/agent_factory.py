"""
Agent Factory — One's autonomous agent spawner
Runs on the local substrate. Spawns, manages, and collects from sub-agents.
Deploy alongside Trinity backend or as a standalone service on :8080
"""

import asyncio
import httpx
import json
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI(title="One — Agent Factory", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "one-70b")
MAX_VERIFY_LOOPS = int(os.getenv("MAX_VERIFY_LOOPS", "3"))

# In-memory agent registry
active_agents: dict = {}


class AgentTask(BaseModel):
    task: str
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    context: Optional[dict] = None
    verify_loops: Optional[int] = 3


class AgentResult(BaseModel):
    agent_id: str
    task: str
    result: str
    status: str
    loops_used: int
    verified: bool


async def call_llm(prompt: str, system: str, model: str) -> str:
    """Call local Ollama LLM."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": 32768,
            }
        })
        resp.raise_for_status()
        return resp.json()["response"]


async def verify_output(output: str, task: str, model: str) -> tuple[bool, str]:
    """
    Triple-loop verification — check if output actually solves the task.
    Returns (passed: bool, feedback: str)
    """
    verify_prompt = f"""
TASK: {task}

OUTPUT TO VERIFY:
{output}

Your job: Verify this output against the task.
Answer ONLY in this JSON format:
{{
  "passed": true/false,
  "issues": "describe any issues, or 'none' if passed",
  "fix_instructions": "what to fix if failed, or 'none' if passed"
}}
"""
    result = await call_llm(
        verify_prompt,
        "You are a strict code and output verifier. Be precise. Output only valid JSON.",
        model
    )
    try:
        # Extract JSON from response
        start = result.find('{')
        end = result.rfind('}') + 1
        parsed = json.loads(result[start:end])
        return parsed.get("passed", False), parsed.get("fix_instructions", "unknown issue")
    except Exception:
        return False, "Verification parse failed"


@app.post("/spawn-agent", response_model=AgentResult)
async def spawn_agent(task: AgentTask):
    """
    Spawn an autonomous sub-agent to complete a task.
    Runs triple-loop verification before returning.
    """
    agent_id = str(uuid.uuid4())[:8]
    model = task.model or DEFAULT_MODEL
    loops = task.verify_loops or MAX_VERIFY_LOOPS

    system = task.system_prompt or """
You are One — an autonomous agent. Complete the assigned task precisely.
Think step by step. Be thorough. Return clean, complete output.
"""

    active_agents[agent_id] = {"status": "running", "task": task.task}

    current_prompt = task.task
    if task.context:
        current_prompt = f"CONTEXT:\n{json.dumps(task.context, indent=2)}\n\nTASK:\n{task.task}"

    result = ""
    verified = False
    loops_used = 0

    for loop in range(loops):
        loops_used = loop + 1
        print(f"[Agent {agent_id}] Loop {loops_used}/{loops}")

        # Generate output
        result = await call_llm(current_prompt, system, model)

        # Verify output
        passed, feedback = await verify_output(result, task.task, model)

        if passed:
            verified = True
            break
        else:
            # Feed failure back into next loop
            current_prompt = f"""
ORIGINAL TASK: {task.task}

PREVIOUS ATTEMPT (FAILED VERIFICATION):
{result}

WHAT'S WRONG:
{feedback}

Fix the issues and produce a correct, complete output.
"""

    active_agents[agent_id]["status"] = "complete" if verified else "unverified"

    return AgentResult(
        agent_id=agent_id,
        task=task.task,
        result=result,
        status="verified" if verified else "max_loops_reached",
        loops_used=loops_used,
        verified=verified
    )


@app.get("/agents")
async def list_agents():
    return {"agents": active_agents, "count": len(active_agents)}


@app.get("/health")
async def health():
    return {"status": "online", "service": "One Agent Factory", "model": DEFAULT_MODEL}


@app.post("/build-repo")
async def build_repo(request: dict):
    """
    Autonomous repo builder.
    Give it a description and it spawns agents to build each component.
    """
    description = request.get("description", "")
    repo_name = request.get("repo_name", "new-project")

    if not description:
        raise HTTPException(status_code=400, detail="Description required")

    # Phase 1 — Architecture agent
    arch_task = AgentTask(
        task=f"Design the complete file structure and architecture for: {description}. "
             f"Output a JSON file tree with descriptions for each file.",
        model=DEFAULT_MODEL
    )
    arch_result = await spawn_agent(arch_task)

    # Phase 2 — Implementation agents (spawned per component)
    impl_task = AgentTask(
        task=f"Implement the full codebase for: {description}",
        context={"architecture": arch_result.result, "repo_name": repo_name},
        model=DEFAULT_MODEL,
        verify_loops=3
    )
    impl_result = await spawn_agent(impl_task)

    return {
        "repo_name": repo_name,
        "architecture": arch_result.result,
        "implementation": impl_result.result,
        "verified": impl_result.verified,
        "loops_used": impl_result.loops_used
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
