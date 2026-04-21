"""
Tavily Search Tool — Finnie
Used by Market Agent to fetch latest financial news and market updates.
Tavily is purpose-built for AI agents — returns clean, structured results.

Get your free API key at: https://tavily.com
Free tier: 1000 searches/month
"""
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


def search_financial_news(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search for latest financial news using Tavily.
    Returns list of {title, url, content, score} dicts.
    """
    try:
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return _fallback_response(query)

        client  = TavilyClient(api_key=api_key)
        results = client.search(
            query=f"{query} India stock market finance",
            search_depth="basic",
            max_results=max_results,
            include_domains=[
                "economictimes.indiatimes.com",
                "moneycontrol.com",
                "livemint.com",
                "ndtvprofit.com",
                "businessstandard.com",
                "reuters.com",
                "bloomberg.com",
                "upstock.com"
            ]
        )
        return results.get("results", [])

    except ImportError:
        print("Tavily not installed. Run: pip install tavily-python")
        return _fallback_response(query)
    except Exception as e:
        print(f"Tavily search error: {e}")
        return _fallback_response(query)


def search_stock_info(ticker: str) -> Dict[str, Any]:
    """
    Search for specific stock news and analysis using Tavily.
    Example: search_stock_info("INFY") returns Infosys news.
    """
    try:
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return {"error": "TAVILY_API_KEY not set", "ticker": ticker}

        client  = TavilyClient(api_key=api_key)
        results = client.search(
            query=f"{ticker} NSE stock latest news analysis 2025",
            search_depth="basic",
            max_results=3
        )
        articles = results.get("results", [])
        return {
            "ticker":   ticker,
            "articles": articles,
            "count":    len(articles)
        }

    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_market_sentiment(topic: str = "Indian stock market") -> str:
    """
    Get AI-powered market sentiment summary using Tavily's answer feature.
    Returns a concise summary string.
    """
    try:
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "Tavily API key not configured."

        client = TavilyClient(api_key=api_key)
        result = client.search(
            query=f"Latest {topic} sentiment today outlook",
            search_depth="basic",
            max_results=3,
            include_answer=True
        )
        return result.get("answer", "No summary available.")

    except Exception as e:
        return f"Search unavailable: {str(e)}"


def _fallback_response(query: str) -> List[Dict]:
    """Returns empty list when Tavily is unavailable."""
    return []


# ── LangChain Tool wrapper (for LangGraph agents) ──

def get_tavily_langchain_tool():
    """
    Returns a LangChain-compatible Tavily tool for use in LangGraph agents.
    Usage:
        tool = get_tavily_langchain_tool()
        agent = create_react_agent(llm, tools=[tool])
    """
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        return TavilySearchResults(
            max_results=5,
            api_key=os.getenv("TAVILY_API_KEY")
        )
    except ImportError:
        print("langchain_community not installed.")
        return None
