"""
Agent 4 — Learning Path Agent
Generates personalized financial education paths based on user profile.
Uses Redis to store and retrieve learning progress (A2A shared memory).
"""
import os
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are Finnie's Learning Path Agent — a personalized financial education coach.
Create structured, practical learning paths for Indian retail investors.

For each learning path:
1. Start with the user's current level and goals
2. List 5-6 modules in logical learning order
3. For each module: name, key topics, estimated time, why it matters for their goals
4. Recommend specific free Indian resources (SEBI investor education, NSE Academy, AMFI etc.)
5. End with a 30-day action plan

Keep language encouraging and jargon-free.
Use Indian financial products: mutual funds, SIPs, PPF, NPS, ELSS, FDs etc.
"""


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point called by orchestrator."""
    query        = context["query"]
    user_profile = context.get("user_profile", {})

    # Load progress from Redis (A2A shared memory)
    progress = _load_progress(user_profile.get("name", "user"))

    response = _generate_learning_path(query, user_profile, progress)

    # Save updated interaction to Redis
    _save_interaction(user_profile.get("name", "user"), query)

    return {"agent": "learning", "response": response}


def _generate_learning_path(
    query: str,
    user_profile: Dict,
    progress: Dict
) -> str:
    """Generate personalized learning path via LLM."""
    experience = user_profile.get("experience", "intermediate")
    risk       = user_profile.get("risk_level", "moderate")
    goals      = ", ".join(user_profile.get("goals", ["wealth creation"]))

    completed_modules = progress.get("completed_modules", [])
    completed_str = (
        f"Already completed: {', '.join(completed_modules)}"
        if completed_modules else "No modules completed yet — this is a fresh start."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": (
                    f"User request: {query}\n\n"
                    f"User profile:\n"
                    f"  Experience: {experience}\n"
                    f"  Risk appetite: {risk}\n"
                    f"  Financial goals: {goals}\n"
                    f"  {completed_str}\n\n"
                    "Create a personalized learning path tailored to this profile."
                )},
            ],
            max_tokens=800,
            temperature=0.4,
        )
        return response.choices[0].message.content
    except Exception as e:
        return (
            f"Learning path generation unavailable right now ({str(e)}). "
            "Please check your OPENAI_API_KEY in .env and try again."
        )


def _load_progress(user_id: str) -> Dict:
    """Load learning progress from Redis shared memory."""
    try:
        from memory.redis_store import RedisStore
        store = RedisStore()
        return store.get_learning_progress(user_id) or {}
    except Exception:
        return {}


def _save_interaction(user_id: str, query: str) -> None:
    """Save interaction to Redis for continuity across sessions."""
    try:
        from memory.redis_store import RedisStore
        store = RedisStore()
        store.log_interaction(user_id, "learning_agent", query)
    except Exception:
        pass
