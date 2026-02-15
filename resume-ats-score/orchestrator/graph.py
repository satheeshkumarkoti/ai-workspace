import os
import json
import asyncio
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END, START
from langchain_google_vertexai import ChatVertexAI
from langchain_mcp_adapters.client import MultiServerMCPClient

from state import State

load_dotenv()

# LLM
llm = ChatVertexAI(
    model_name=os.getenv('MODEL_NAME'), temperature=0
)

# MCP Tools loader


async def _init_tools():
    client = MultiServerMCPClient(
        {
            "ats_tools": {
                "transport": "http",
                "url": os.getenv('MCP_URL')
            }
        }
    )
    tools = await client.get_tools()
    return {t.name: t for t in tools}


TOOLS = asyncio.run(_init_tools())


def _tool(name: str):
    if name not in TOOLS:
        raise RuntimeError(
            f"MCP tool not found: {name}. Available tools {list(TOOLS)}")
    return TOOLS[name]

# Node 1: Resume parse


async def parse_resume_node(state: State) -> State:
    state["profile"] = await _tool("parse_resume").ainvoke(
        {"resume_text": state["resume_text"]})
    return state


# Node 2 JD Parse
async def parse_jd_node(state: State) -> State:
    state["jd_profile"] = await _tool("parse_jd").ainvoke(
        {"job_description": state["job_description"]})
    return state


# Node 3: ATS Scoring Agent (LLM)


def _parse_agent_json(text: str) -> dict:
    s = text.strip()
    if s.startswith("```"):
        s = s.strip('`')
        s = s.split("\n", 1)[-1].strip()
    return json.loads(s)


async def ats_scoring_agent_node(state: State) -> State:
    profile = state.get("profile", {})
    jd_profile = state.get("jd_profile", {})
    norm_skills = state.get("normalized_skills", [])
    must_haves = state.get("must_haves", [])
    schema = {
        "ats_score": "number between 0.0 and 1.0",
        "decision": "shortlist or reject",
        "reasons": "string (HR Friendly bullets in one string)",
        "missing_must_haves": "array of strings",
    }
    base_prompt = f"""
You are an ATS Scoring Agent.

Return only valid json (no markdown, no backticks).
JSON Schema:
{schema}

Rules:
- ats_score in [0.0, 1.0]
- Use shortlist threshold 0.70 unless clearly not fit
- missing_must_haves reduces scores strongly
- reasons must be breif and HR-Friendly

Job Description:
{state['job_description']}

JD Parsed:
{jd_profile}

Must Haves:
{must_haves}

Candidate Profile:
{profile}


Candidate Normalized Skills:
{norm_skills}
"""
    # Attempt 1
    msg1 = llm.invoke(base_prompt).content
    try:
        data = _parse_agent_json(msg1)
    except Exception:
        # Attempt 2
        msg2 = llm.invoke(
            base_prompt + f"\n\nRESPONSE 1:\n{msg1}\n\nINVALID JSON. Try again. I want response according to scheam {schema}").content
        data = _parse_agent_json(msg2)
    score = float(data.get("ats_score", 0.0))

    # validate and clamp
    if score < 0.0:
        score = 0.0
    if score > 1.0:
        score = 1.0

    decision = str(data.get("decision", "")).lower().strip()
    if decision not in ("shortlist", "reject"):
        # fallback rule
        decision = "shortlist" if score >= 0.70 else "reject"
    reasons = str(data.get("reasons", "")).strip()
    state["ats_score"] = score
    state["decision"] = decision
    state["reasons"] = reasons
    return state


# Node 4: Persist score (MCP)

async def store_score_node(state: State) -> State:
    stored = await _tool("store_score").ainvoke({
        "candidate_id": state["candidate_id"],
        "job_id": state["job_id"],
        "ats_score": state["ats_score"],
        "decision": state["decision"],
        "reasons": state["reasons"]
    })
    state["stored"] = stored
    return state

def build_graph():
    graph = StateGraph(State)
    graph.add_node("parse_resume", parse_resume_node)
    graph.add_node("parse_jd", parse_jd_node)
    graph.add_node("ats_agent", ats_scoring_agent_node)
    graph.add_node("store_score", store_score_node)

    graph.add_edge(START, "parse_resume")
    graph.add_edge("parse_resume", "parse_jd")
    graph.add_edge("parse_jd", "ats_agent")
    graph.add_edge("ats_agent", "store_score")
    graph.add_edge("store_score", END)
    return graph.compile()
