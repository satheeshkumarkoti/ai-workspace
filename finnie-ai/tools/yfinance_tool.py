"""
YFinance Tool — Finnie
LangGraph-compatible tool wrapper for fetching live NSE/BSE market data.
Used by Market Agent and called via A2A by Portfolio Agent.
"""
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# NSE ticker symbol mapping → yFinance format
NSE_TICKER_MAP = {
    "INFY":      "INFY.NS",
    "TCS":       "TCS.NS",
    "HDFC":      "HDFCBANK.NS",
    "WIPRO":     "WIPRO.NS",
    "RELIANCE":  "RELIANCE.NS",
    "ICICI":     "ICICIBANK.NS",
    "AXISBANK":  "AXISBANK.NS",
    "BAJFINANCE":"BAJFINANCE.NS",
    "HCLTECH":   "HCLTECH.NS",
    "TATAMOTORS":"TATAMOTORS.NS",
    "NIFTY_MF":  "^NSEI",
    "SENSEX":    "^BSESN",
}


def get_stock_price(ticker: str) -> Dict[str, Any]:
    """
    Fetch live price for a single NSE stock.
    Returns price, change%, 52-week range.
    """
    try:
        import yfinance as yf

        symbol = NSE_TICKER_MAP.get(ticker.upper(), ticker.upper() + ".NS")
        stock  = yf.Ticker(symbol)
        info   = stock.fast_info

        current  = round(float(info.last_price), 2)
        prev     = round(float(info.previous_close), 2)
        change   = round(((current - prev) / prev) * 100, 2) if prev else 0.0
        high_52w = round(float(info.year_high), 2)
        low_52w  = round(float(info.year_low),  2)

        return {
            "ticker":        ticker.upper(),
            "symbol":        symbol,
            "current_price": current,
            "previous_close":prev,
            "change_pct":    change,
            "52w_high":      high_52w,
            "52w_low":       low_52w,
            "status":        "success"
        }

    except ImportError:
        return {"ticker": ticker, "status": "error", "error": "yfinance not installed"}
    except Exception as e:
        return {"ticker": ticker, "status": "error", "error": str(e)}


def get_multiple_prices(tickers: List[str]) -> Dict[str, Optional[float]]:
    """
    Fetch current prices for multiple tickers efficiently.
    Used by A2A flow — Market Agent → Portfolio Agent.
    Returns: {ticker: price} dict.
    """
    prices = {}
    try:
        import yfinance as yf
        for ticker in tickers:
            symbol = NSE_TICKER_MAP.get(ticker.upper(), ticker.upper() + ".NS")
            try:
                data  = yf.Ticker(symbol)
                price = round(float(data.fast_info.last_price), 2)
                prices[ticker.upper()] = price
            except Exception:
                prices[ticker.upper()] = None
    except ImportError:
        for ticker in tickers:
            prices[ticker.upper()] = None
    return prices


def get_index_data() -> Dict[str, Any]:
    """
    Fetch live data for major Indian indices: NIFTY 50, SENSEX, Bank NIFTY.
    """
    indices = {
        "NIFTY 50":   "^NSEI",
        "SENSEX":     "^BSESN",
        "BANK NIFTY": "^NSEBANK",
    }
    results = {}
    try:
        import yfinance as yf
        for name, symbol in indices.items():
            try:
                t     = yf.Ticker(symbol)
                info  = t.fast_info
                price = round(float(info.last_price), 2)
                prev  = round(float(info.previous_close), 2)
                chg   = round(((price - prev) / prev) * 100, 2) if prev else 0.0
                results[name] = {
                    "price":      price,
                    "change_pct": chg,
                    "status":     "success"
                }
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
    except ImportError:
        return {"error": "yfinance not installed"}
    return results


def get_stock_history(ticker: str, period: str = "1mo") -> Dict[str, Any]:
    """
    Fetch historical price data for a stock.
    period options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y
    """
    try:
        import yfinance as yf
        symbol = NSE_TICKER_MAP.get(ticker.upper(), ticker.upper() + ".NS")
        data   = yf.Ticker(symbol).history(period=period)

        if data.empty:
            return {"ticker": ticker, "status": "error", "error": "No data found"}

        history = [
            {
                "date":  str(idx.date()),
                "open":  round(row["Open"],  2),
                "close": round(row["Close"], 2),
                "high":  round(row["High"],  2),
                "low":   round(row["Low"],   2),
            }
            for idx, row in data.iterrows()
        ]
        return {
            "ticker":  ticker.upper(),
            "period":  period,
            "history": history,
            "count":   len(history),
            "status":  "success"
        }

    except Exception as e:
        return {"ticker": ticker, "status": "error", "error": str(e)}


# ── LangGraph Tool wrapper ──

def get_yfinance_langchain_tool():
    """
    Returns a LangChain-compatible tool for use in LangGraph agents.
    """
    try:
        from langchain.tools import Tool
        return Tool(
            name="get_stock_price",
            func=lambda ticker: str(get_stock_price(ticker)),
            description=(
                "Fetch live NSE/BSE stock price. "
                "Input: ticker symbol like INFY, TCS, HDFC, RELIANCE. "
                "Returns current price, change%, and 52-week range."
            )
        )
    except ImportError:
        return None
