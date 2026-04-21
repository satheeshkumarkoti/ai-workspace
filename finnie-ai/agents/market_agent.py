"""
Agent 2 — Market Data Agent
Fetches live stock prices via yFinance AND latest news via Tavily.
Called directly by orchestrator AND by portfolio agent via A2A.
"""
import os
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are Finnie's Market Data Agent.
You have access to real-time market data AND latest financial news from Tavily.
Present prices clearly, add brief context about what the numbers mean,
and summarize relevant news headlines with Bullish / Bearish / Neutral sentiment tags.
Focus on Indian markets (NSE/BSE) but cover global context where relevant.
Keep responses concise and factual. Never give specific buy/sell advice.
Format: Live prices first, then news highlights, then one key takeaway.
"""

# NSE symbols to yFinance format
NSE_TICKER_MAP = {
    "INFY":     "INFY.NS",
    "TCS":      "TCS.NS",
    "HDFC":     "HDFCBANK.NS",
    "WIPRO":    "WIPRO.NS",
    "RELIANCE": "RELIANCE.NS",
    "ICICI":    "ICICIBANK.NS",
    "HCLTECH":  "HCLTECH.NS",
    "NIFTY_MF": "^NSEI",
    "SENSEX":   "^BSESN",
}

# Queries that should trigger Tavily news search
NEWS_KEYWORDS = [
    "news", "latest", "today", "update", "headline",
    "suggest", "trend", "sentiment", "outlook", "analysis",
    "invest", "should i", "recommend", "what do you think"
]


def get_portfolio_prices(tickers: List[str]) -> Dict[str, float]:
    """
    A2A helper — called by orchestrator before routing to portfolio agent.
    Returns {ticker: current_price} dict.
    """
    prices = {}
    try:
        import yfinance as yf
        for ticker in tickers:
            yf_symbol = NSE_TICKER_MAP.get(ticker, ticker + ".NS")
            try:
                data  = yf.Ticker(yf_symbol)
                info  = data.fast_info
                prices[ticker] = round(float(info.last_price), 2)
            except Exception:
                prices[ticker] = None
    except ImportError:
        pass
    return prices


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point called by orchestrator."""
    query     = context["query"]
    portfolio = context.get("portfolio", {})

    market_data = _fetch_market_data(query, portfolio)
    news_data   = _fetch_tavily_news(query) if _needs_news(query) else ""
    response    = _generate_response(query, market_data, news_data)

    return {"agent": "market", "response": response}


def _needs_news(query: str) -> bool:
    """Decide if Tavily news search is needed for this query."""
    return any(kw in query.lower() for kw in NEWS_KEYWORDS)


def _fetch_tavily_news(query: str) -> str:
    """
    Fetch latest financial news using Tavily Search API.
    Returns formatted news string or empty string if unavailable.
    """
    try:
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return ""

        tavily  = TavilyClient(api_key=api_key)
        results = tavily.search(
            query=f"{query} India stock market finance",
            search_depth="basic",
            max_results=4,
            include_domains=[
                "economictimes.indiatimes.com",
                "moneycontrol.com",
                "livemint.com",
                "ndtvprofit.com",
                "businessstandard.com",
                "reuters.com",
            ]
        )

        articles = results.get("results", [])
        if not articles:
            return ""

        lines = ["Latest News (via Tavily):"]
        for article in articles[:4]:
            title   = article.get("title",   "No title")
            content = article.get("content", "")[:180].strip()
            lines.append(f"• {title} — {content}...")

        return "\n".join(lines)

    except ImportError:
        return ""
    except Exception:
        return ""


def _fetch_market_data(query: str, portfolio: Dict) -> str:
    """Fetch live prices from NSE/BSE using yFinance."""
    try:
        import yfinance as yf
        results = []
        q_lower = query.lower()

        # Fetch indices when query is market-level
        if any(kw in q_lower for kw in [
            "nifty", "market", "sensex", "index",
            "overview", "trend", "today", "suggest", "invest"
        ]):
            for name, symbol in [("NIFTY 50", "^NSEI"), ("SENSEX", "^BSESN")]:
                try:
                    t     = yf.Ticker(symbol)
                    price = round(t.fast_info.last_price, 2)
                    prev  = round(t.fast_info.previous_close, 2)
                    chg   = round(((price - prev) / prev) * 100, 2) if prev else 0
                    results.append(f"{name}: {price:,.2f} ({chg:+.2f}%)")
                except Exception:
                    pass

        # Fetch individual stocks mentioned in query or portfolio
        stocks_to_fetch = [
            t for t in list(NSE_TICKER_MAP.keys()) + list(portfolio.keys())
            if t.lower() in q_lower or "portfolio" in q_lower
        ]
        for ticker in set(stocks_to_fetch[:5]):
            yf_symbol = NSE_TICKER_MAP.get(ticker, ticker + ".NS")
            try:
                t     = yf.Ticker(yf_symbol)
                price = round(t.fast_info.last_price, 2)
                prev  = round(t.fast_info.previous_close, 2)
                chg   = round(((price - prev) / prev) * 100, 2) if prev else 0
                results.append(f"{ticker}: ₹{price:,.2f} ({chg:+.2f}%)")
            except Exception:
                pass

        return "\n".join(results) if results else "Live data temporarily unavailable."

    except ImportError:
        return "yfinance not installed. Run: pip install yfinance"
    except Exception as e:
        return f"Market data fetch error: {str(e)}"


def _generate_response(query: str, market_data: str, news_data: str = "") -> str:
    """Combine live prices + Tavily news into a clear LLM response."""
    combined = f"Live market data:\n{market_data}"
    if news_data:
        combined += f"\n\n{news_data}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": (
                    f"User asked: {query}\n\n"
                    f"{combined}\n\n"
                    "Present the data clearly. Tag each news item as "
                    "Bullish, Bearish, or Neutral. "
                    "End with one concise key takeaway for the investor."
                )},
            ],
            max_tokens=500,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception:
        return f"Market Data:\n{market_data}\n\n{news_data}"