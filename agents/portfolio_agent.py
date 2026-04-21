"""
Agent 3 — Portfolio Analyst Agent
Analyses user portfolio, calculates risk score, and gives rebalancing advice.
Receives live prices from Market Agent via A2A context.
Calls Literacy Agent via A2A to explain relevant concepts.
"""
import os
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are Finnie's Portfolio Analyst Agent.
Analyse the user's portfolio data and provide:
1. Overall risk score (1-10)
2. Sector concentration analysis  
3. Diversification assessment
4. Specific rebalancing recommendations
5. One key action the user should take this month

Use Indian market context. Be specific with numbers.
Format your response clearly with sections.
Never say "buy" or "sell" specific stocks — use "consider reducing exposure to" or "consider adding".
"""


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point called by orchestrator."""
    query        = context["query"]
    portfolio    = context.get("portfolio", {})
    user_profile = context.get("user_profile", {})
    live_prices  = context.get("a2a_data", {}).get("live_prices", {})

    # Update portfolio with live prices from Market Agent (A2A)
    if live_prices:
        for ticker, price in live_prices.items():
            if ticker in portfolio and price:
                portfolio[ticker]["current_price"] = price

    portfolio_summary = _build_portfolio_summary(portfolio)
    response = _analyse_portfolio(query, portfolio_summary, user_profile)

    return {"agent": "portfolio", "response": response}


def _build_portfolio_summary(portfolio: Dict) -> str:
    """Build a text summary of the portfolio for LLM context."""
    if not portfolio:
        return "No portfolio data available."

    total_value = sum(v["qty"] * v["current_price"] for v in portfolio.values())
    lines = [f"Total portfolio value: ₹{total_value:,.0f}\n", "Holdings:"]

    for ticker, v in portfolio.items():
        cur_val  = v["qty"] * v["current_price"]
        inv_val  = v["qty"] * v["avg_price"]
        pnl      = cur_val - inv_val
        pnl_pct  = (pnl / inv_val * 100) if inv_val else 0
        alloc    = (cur_val / total_value * 100) if total_value else 0
        lines.append(
            f"  {ticker}: {v['qty']} units @ ₹{v['current_price']:,} | "
            f"Value: ₹{cur_val:,.0f} | Allocation: {alloc:.1f}% | "
            f"P&L: ₹{pnl:,.0f} ({pnl_pct:.1f}%)"
        )
    return "\n".join(lines)


def _analyse_portfolio(
    query: str,
    portfolio_summary: str,
    user_profile: Dict
) -> str:
    """Call LLM with portfolio data for analysis."""
    risk_level  = user_profile.get("risk_level", "moderate")
    experience  = user_profile.get("experience", "intermediate")
    goals       = ", ".join(user_profile.get("goals", ["wealth creation"]))

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": (
                    f"User query: {query}\n\n"
                    f"Portfolio data:\n{portfolio_summary}\n\n"
                    f"User profile: {experience} investor, {risk_level} risk appetite\n"
                    f"Financial goals: {goals}\n\n"
                    "Provide a detailed portfolio analysis and actionable recommendations."
                )},
            ],
            max_tokens=700,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return (
            f"Portfolio summary:\n{portfolio_summary}\n\n"
            f"Note: AI analysis unavailable — {str(e)}"
        )
