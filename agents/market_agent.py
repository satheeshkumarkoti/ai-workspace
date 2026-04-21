"""
Agent 2 — Market Data Agent
Fetches live stock prices via yFinance and news summaries.
Called directly by orchestrator AND by portfolio agent via A2A.
"""
import os
from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are Finnie's Market Data Agent.
You have access to real-time market data.
Present prices clearly, add brief context about what the numbers mean,
and flag any significant moves the user should know about.
Focus on Indian markets (NSE/BSE) but cover global context where relevant.
Keep responses concise and factual. Never give buy/sell advice.
"""

# Ticker map — NSE symbols to yFinance format
NSE_TICKER_MAP = {
    "INFY":     "INFY.NS",
    "TCS":      "TCS.NS",
    "HDFC":     "HDFCBANK.NS",
    "WIPRO":    "WIPRO.NS",
    "RELIANCE": "RELIANCE.NS",
    "NIFTY_MF": "^NSEI",   # NIFTY 50 index
}


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
                data = yf.Ticker(yf_symbol)
                info = data.fast_info
                prices[ticker] = round(float(info.last_price), 2)
            except Exception:
                prices[ticker] = None
    except ImportError:
        pass
    return prices


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point called by orchestrator."""
    query    = context["query"]
    portfolio = context.get("portfolio", {})

    market_data = _fetch_market_data(query, portfolio)
    response    = _generate_response(query, market_data)

    return {"agent": "market", "response": response}


def _fetch_market_data(query: str, portfolio: Dict) -> str:
    """Fetch relevant market data using yFinance."""
    try:
        import yfinance as yf
        results = []
        q_lower = query.lower()

        # Fetch indices
        if any(kw in q_lower for kw in ["nifty", "market", "sensex", "index", "overview"]):
            for name, symbol in [("NIFTY 50", "^NSEI"), ("SENSEX", "^BSESN")]:
                try:
                    t = yf.Ticker(symbol)
                    price = round(t.fast_info.last_price, 2)
                    prev  = round(t.fast_info.previous_close, 2)
                    chg   = round(((price - prev) / prev) * 100, 2) if prev else 0
                    results.append(f"{name}: {price:,.2f} ({chg:+.2f}%)")
                except Exception:
                    pass

        # Fetch specific stocks mentioned in query or portfolio
        stocks_to_fetch = []
        for ticker in list(NSE_TICKER_MAP.keys()) + list(portfolio.keys()):
            if ticker.lower() in q_lower or "portfolio" in q_lower:
                stocks_to_fetch.append(ticker)

        for ticker in set(stocks_to_fetch[:5]):  # cap at 5 to avoid latency
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


def _generate_response(query: str, market_data: str) -> str:
    """Use LLM to present market data in a helpful narrative."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": (
                    f"User asked: {query}\n\n"
                    f"Live market data:\n{market_data}\n\n"
                    "Present this data clearly with brief context."
                )},
            ],
            max_tokens=400,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception:
        return f"Market Data:\n{market_data}"
