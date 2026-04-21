"""
Finnie — FastAPI Backend
Exposes all 4 agents as REST API endpoints.
Can be used independently or alongside the Streamlit UI.

Run with:
    uvicorn api.main:app --reload --port 8000

API Docs:
    http://localhost:8000/docs
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

from agents.orchestrator import route_query

# ── App setup ──
app = FastAPI(
    title="Finnie AI Finance Assistant",
    description="Multi-Agent AI Finance Assistant API — 4 specialist agents with A2A communication",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ──

class ChatRequest(BaseModel):
    query: str
    user_profile: Optional[Dict[str, Any]] = {
        "name": "User",
        "risk_level": "moderate",
        "experience": "intermediate",
        "goals": ["wealth_creation"]
    }
    portfolio: Optional[Dict[str, Any]] = {}


class ChatResponse(BaseModel):
    agent: str
    response: str
    query: str


class PortfolioRequest(BaseModel):
    portfolio: Dict[str, Any]
    user_profile: Optional[Dict[str, Any]] = {
        "risk_level": "moderate",
        "experience": "intermediate",
        "goals": ["wealth_creation"]
    }


class LearningRequest(BaseModel):
    experience: str = "intermediate"
    risk_level: str = "moderate"
    goals: List[str] = ["wealth_creation"]


# ── Health Check ──

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "online",
        "app": "Finnie AI Finance Assistant",
        "agents": ["literacy", "market", "portfolio", "learning"],
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "agents_online": 4}


# ── Chat Endpoint — routes to correct agent automatically ──

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest):
    """
    Main chat endpoint. Automatically routes to the correct agent based on query intent.

    - Financial concepts → Literacy Agent (RAG)
    - Live prices / news → Market Agent (yFinance)
    - Portfolio analysis → Portfolio Agent (A2A with Market Agent)
    - Learning paths → Learning Agent
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        result = route_query(
            query=request.query,
            user_profile=request.user_profile,
            portfolio=request.portfolio
        )
        return ChatResponse(
            agent=result.get("agent", "orchestrator"),
            response=result.get("response", ""),
            query=request.query
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Agent-Specific Endpoints ──

@app.post("/agents/literacy", tags=["Agents"])
def literacy_agent(request: ChatRequest):
    """Direct call to Financial Literacy Agent — RAG-powered finance education."""
    try:
        from agents.literacy_agent import run
        context = {
            "query": request.query,
            "user_profile": request.user_profile,
            "a2a_data": {}
        }
        return run(context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/market", tags=["Agents"])
def market_agent(request: ChatRequest):
    """Direct call to Market Data Agent — live NSE/BSE prices via yFinance."""
    try:
        from agents.market_agent import run
        context = {
            "query": request.query,
            "user_profile": request.user_profile,
            "portfolio": request.portfolio,
            "a2a_data": {}
        }
        return run(context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/portfolio", tags=["Agents"])
def portfolio_agent(request: PortfolioRequest):
    """
    Direct call to Portfolio Analyst Agent.
    Implements A2A: fetches live prices from Market Agent before analysis.
    """
    try:
        from agents.market_agent import get_portfolio_prices
        from agents.portfolio_agent import run

        live_prices = get_portfolio_prices(list(request.portfolio.keys()))
        context = {
            "query": "Analyse my portfolio and give detailed risk assessment",
            "user_profile": request.user_profile,
            "portfolio": request.portfolio,
            "a2a_data": {"live_prices": live_prices}
        }
        return run(context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/learning", tags=["Agents"])
def learning_agent(request: LearningRequest):
    """Direct call to Learning Path Agent — personalized financial education."""
    try:
        from agents.learning_agent import run
        context = {
            "query": (
                f"Create a personalized learning path for a {request.experience} investor "
                f"with {request.risk_level} risk appetite. "
                f"Goals: {', '.join(request.goals)}"
            ),
            "user_profile": {
                "experience": request.experience,
                "risk_level": request.risk_level,
                "goals": request.goals
            },
            "a2a_data": {}
        }
        return run(context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Market Data Endpoints ──

@app.get("/market/prices", tags=["Market"])
def get_market_prices():
    """Fetch live prices for NIFTY 50, SENSEX and top Indian stocks."""
    try:
        from agents.market_agent import get_portfolio_prices
        tickers = ["INFY", "TCS", "HDFC", "WIPRO", "RELIANCE"]
        prices  = get_portfolio_prices(tickers)
        return {"prices": prices, "source": "yFinance"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/market/prices/{ticker}", tags=["Market"])
def get_ticker_price(ticker: str):
    """Fetch live price for a specific NSE ticker."""
    try:
        from agents.market_agent import get_portfolio_prices
        prices = get_portfolio_prices([ticker.upper()])
        price  = prices.get(ticker.upper())
        if price is None:
            raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
        return {"ticker": ticker.upper(), "price": price, "source": "yFinance"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── RAG Knowledge Base ──

@app.get("/rag/search", tags=["RAG"])
def search_knowledge_base(query: str, top_k: int = 3):
    """Search the ChromaDB knowledge base for relevant financial content."""
    try:
        from rag.retriever import retrieve
        chunks = retrieve(query, top_k=top_k)
        return {
            "query":   query,
            "chunks":  chunks,
            "count":   len(chunks),
            "source":  "ChromaDB"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))