"""
Orchestrator Agent — Finnie
Routes user queries to the correct specialist agent using keyword-based
intent detection + LLM fallback. Implements A2A communication via
shared context dict passed between agents.
"""
import os
import re
from typing import Dict, Any

# ── Intent keywords for routing ──
MARKET_KEYWORDS = [
    "price", "nifty", "sensex", "stock", "trading", "market", "rupee",
    "inr", "usd", "gold", "crude", "bse", "nse", "index", "share",
    "today", "current", "live", "news", "headlines",
]
PORTFOLIO_KEYWORDS = [
    "portfolio", "holding", "analyse", "analyze", "rebalance",
    "risk", "allocation", "diversif", "my investment", "my stocks",
    "pnl", "profit", "loss", "returns", "performance",
]
LEARNING_KEYWORDS = [
    "learn", "learning", "path", "course", "teach", "explain my journey",
    "beginner", "start investing", "how to invest", "guide me",
    "curriculum", "module", "step by step",
]


def _detect_intent(query: str) -> str:
    """Rule-based intent classifier — returns agent name."""
    q = query.lower()
    market_score   = sum(1 for kw in MARKET_KEYWORDS    if kw in q)
    portfolio_score = sum(1 for kw in PORTFOLIO_KEYWORDS if kw in q)
    learning_score  = sum(1 for kw in LEARNING_KEYWORDS  if kw in q)

    # Portfolio wins if "my" + finance word — personal context
    if "my" in q and portfolio_score > 0:
        return "portfolio"

    scores = {
        "market":    market_score,
        "portfolio": portfolio_score,
        "learning":  learning_score,
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "literacy"


def route_query(
    query: str,
    user_profile: Dict[str, Any],
    portfolio: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main orchestrator entry point.
    1. Detects intent
    2. Routes to the correct specialist agent
    3. Supports A2A: market agent result can be passed to portfolio agent
    Returns: {"agent": str, "response": str}
    """
    intent = _detect_intent(query)

    # Build shared context (A2A state)
    context = {
        "query":        query,
        "user_profile": user_profile,
        "portfolio":    portfolio,
        "a2a_data":     {},   # populated by agents that call other agents
    }

    if intent == "market":
        from agents.market_agent import run as market_run
        return market_run(context)

    elif intent == "portfolio":
        # A2A: fetch live prices first, pass to portfolio agent
        from agents.market_agent import get_portfolio_prices
        from agents.portfolio_agent import run as portfolio_run
        live_prices = get_portfolio_prices(list(portfolio.keys()))
        context["a2a_data"]["live_prices"] = live_prices
        return portfolio_run(context)

    elif intent == "learning":
        from agents.learning_agent import run as learning_run
        return learning_run(context)

    else:
        from agents.literacy_agent import run as literacy_run
        return literacy_run(context)
