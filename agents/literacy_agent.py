"""
Agent 1 — Financial Literacy Agent
Uses RAG (ChromaDB + OpenAI embeddings) to answer finance education queries.
Falls back to direct LLM if vector store has no relevant chunks.
"""
import os
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a friendly, expert financial literacy coach named Finnie.
Your job is to explain financial concepts in clear, simple language 
suitable for Indian retail investors.

Rules:
- Use Indian context: INR, SEBI, NSE/BSE, mutual funds, SIPs, ELSS etc.
- Explain jargon in plain language
- Give practical examples with real numbers
- Keep answers concise — 3-5 paragraphs max
- Always end with one actionable tip
- Never give specific buy/sell advice
- If context is provided from RAG, use it and cite it naturally
"""


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point called by orchestrator."""
    query        = context["query"]
    user_profile = context.get("user_profile", {})
    rag_context  = _retrieve_rag_context(query)

    user_message = query
    if rag_context:
        user_message = f"""Question: {query}

Relevant knowledge base context:
{rag_context}

Please answer using the context above where relevant."""

    experience = user_profile.get("experience", "intermediate")
    system = SYSTEM_PROMPT + f"\n\nUser experience level: {experience}. Adjust complexity accordingly."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",  "content": system},
                {"role": "user",    "content": user_message},
            ],
            max_tokens=600,
            temperature=0.3,
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = _fallback_response(query)

    return {"agent": "literacy", "response": answer}


def _retrieve_rag_context(query: str) -> str:
    """
    Retrieve relevant chunks from ChromaDB vector store.
    Returns empty string if store not initialised yet.
    """
    try:
        from rag.retriever import retrieve
        chunks = retrieve(query, top_k=3)
        if chunks:
            return "\n\n".join(chunks)
    except Exception:
        pass
    return ""


def _fallback_response(query: str) -> str:
    """Static fallback if OpenAI call fails."""
    return (
        f"I understand you're asking about: '{query}'. "
        "I'm having trouble connecting to my knowledge base right now. "
        "Please try again in a moment, or check your OPENAI_API_KEY in the .env file."
    )
