# 💹 FINNIE — AI FINANCE ASSISTANT

> **Democratizing Financial Literacy Through Intelligent Multi-Agent AI**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red?logo=streamlit)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-green)](https://langchain-ai.github.io/langgraph/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-black?logo=openai)](https://openai.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-purple)](https://www.trychroma.com/)
[![Tavily](https://img.shields.io/badge/Tavily-AI%20Search-orange)](https://tavily.com)
[![Redis](https://img.shields.io/badge/Redis-Shared%20Memory-red?logo=redis)](https://redis.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/Tests-82%20Passing-brightgreen)](./tests)
[![Coverage](https://img.shields.io/badge/Coverage-85%25-green)](./tests)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

---

> 🏆 **Capstone Project** — Multi-Agent Generative AI System with RAG, A2A Communication, Live Market Data, and Personalized Learning

---

## 📌 OVERVIEW

**Finnie** is a production-grade, multi-agent AI finance assistant built for Indian retail investors. It combines **Generative AI**, **Retrieval-Augmented Generation (RAG)**, **Tavily AI Search**, and **Agent-to-Agent (A2A) communication** to deliver personalized, accurate, and real-time financial guidance.

Built as a Capstone Project demonstrating enterprise-level AI architecture — from intent routing to live market data, from vector search to cross-agent collaboration.

---

## ✨ KEY FEATURES

| Feature | Description |
|---|---|
| 🤖 **4 Specialist Agents** | Literacy, Market, Portfolio, Learning — each expert in its domain |
| 🔁 **A2A Communication** | Agents collaborate — Market Agent feeds live prices to Portfolio Agent |
| 📚 **RAG Pipeline** | ChromaDB vector store with cosine similarity filtering for accurate answers |
| 📈 **Live Market Data** | Real-time NSE/BSE prices via yFinance |
| 🔍 **Tavily AI Search** | Latest financial news with Bullish/Bearish/Neutral sentiment tagging |
| 🎓 **Personalized Learning** | Dynamic learning paths based on experience, risk appetite, and goals |
| 💼 **Portfolio Analysis** | Risk scoring, sector concentration, P&L tracking, rebalancing advice |
| 🧠 **Shared Memory** | Redis-powered cross-agent state persistence |
| ⚡ **FastAPI Backend** | REST API with Swagger docs for all 4 agents |
| 🧪 **82 Tests** | Pytest test suite with ~85% code coverage |

---

## 🎯 BUSINESS PROBLEM

| Problem | Finnie's Solution |
|---|---|
| Financial jargon stops people from investing | Literacy Agent explains concepts in plain language |
| Generic tools don't adapt to individual goals | Personalized learning paths per user profile |
| No real-time insights for beginners | Market Agent fetches live prices via YFinance |
| News is scattered across multiple sources | Tavily AI aggregates and summarizes top financial news |
| Quality financial education doesn't scale | Multi-agent AI scales to unlimited users |
| Portfolio analysis is expensive | AI-powered risk scoring and rebalancing — free |

---

## 🏗️ ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│              STREAMLIT UI  (4 TABS)                 │
│     Chat │ Portfolio │ Market Trends │ Learning     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│         ORCHESTRATOR AGENT  (LangGraph)             │
│     Intent Detection → Route → A2A Coordinator      │
└───────┬───────────┬───────────┬──────────┬──────────┘
        │           │           │          │
   ┌────▼───┐  ┌────▼───┐  ┌───▼────┐ ┌───▼────┐
   │AGENT 1 │  │AGENT 2 │  │AGENT 3 │ │AGENT 4 │
   │Literacy│  │Market  │  │Portfo- │ │Learning│
   │  RAG   │  │+ Tavily│  │  lio   │ │  Path  │
   └────────┘  └────────┘  └────────┘ └────────┘
        │           │           │          │
┌───────▼───────────▼───────────▼──────────▼──────────┐
│              A2A COMMUNICATION LAYER                │
│         Redis Shared State · LangGraph Edges        │
└───────┬──────────────┬────────────┬─────────────────┘
        │              │            │
  ┌─────▼──────┐ ┌─────▼─────┐ ┌───▼──────┐
  │  CHROMADB  │ │  YFINANCE │ │  TAVILY  │
  │ Vector DB  │ │ Live Data │ │AI Search │
  └────────────┘ └───────────┘ └──────────┘
```

---

## 🤖 THE 4 AGENTS

### AGENT 1 — Financial Literacy Agent 📚
- Answers finance education queries using **RAG Pipeline**
- Knowledge Base: SIPs, ELSS, P/E Ratios, Diversification, LTCG Tax
- Embedding Model: `text-embedding-ada-002` → ChromaDB (Cosine Similarity)
- Threshold Filtering: Rejects chunks with similarity score > 0.4
- LLM: **GPT-4** with constrained prompting to prevent hallucination

### AGENT 2 — Market Data Agent 📈
- Fetches **live stock prices** from NSE/BSE via `yFinance`
- Fetches **latest financial news** via `Tavily AI Search`
- Covers: NIFTY 50, SENSEX, individual stocks (INFY, TCS, HDFC, etc.)
- Tags every news item: 🟢 Bullish / 🔴 Bearish / 🔵 Neutral
- Called independently **and** via A2A by the Portfolio Agent

### AGENT 3 — Portfolio Analyst Agent 💼
- Analyses user holdings: risk score, sector concentration, P&L
- **A2A Pattern**: Orchestrator fetches live prices from Agent 2 first, injects into context, then calls Agent 3
- Generates rebalancing recommendations aligned to user's risk profile
- Supports dynamic portfolio management (add/remove holdings)

### AGENT 4 — Learning Path Agent 🎓
- Generates **personalized** financial education journeys
- Adapts to: experience level (Beginner/Intermediate/Advanced), risk appetite, and financial goals
- Tracks progress in **Redis** shared memory across sessions
- Recommends free Indian resources: SEBI, NSE Academy, AMFI

---

## 🔁 A2A COMMUNICATION PATTERN

```python
# Example: User asks "Analyse my portfolio"
# Orchestrator implements A2A:

1. Detects Intent  →  "portfolio"
2. Calls Agent 2 (Market): get_portfolio_prices(["INFY", "TCS", "HDFC"])
   → Returns: {"INFY": 1842.0, "TCS": 3820.0, "HDFC": 1680.0}
3. Injects live prices into Redis A2A shared state
4. Calls Agent 3 (Portfolio) with enriched context
   → Generates analysis with live valuations, not stale prices
5. Returns unified response to user
```

> This pattern ensures **agents collaborate** rather than operate in silos.

---

## 🔍 TAVILY AI SEARCH INTEGRATION

Tavily is purpose-built for AI agents — replaces traditional scraping APIs:

```python
# Auto-triggered for queries containing:
# "news", "suggest", "today", "latest", "should I invest", "trend"

tavily.search(
    query="Indian stock market outlook today",
    search_depth="basic",
    max_results=4,
    include_domains=[
        "economictimes.indiatimes.com",
        "moneycontrol.com",
        "livemint.com",
        "ndtvprofit.com"
    ]
)
# Returns clean structured articles
# GPT-4 tags each: Bullish / Bearish / Neutral
# Presented alongside live prices in one unified response
```

---

## 🛠️ TECH STACK

| Layer | Technology |
|---|---|
| **UI** | Streamlit 1.32+ |
| **Agent Orchestration** | LangGraph, LangChain |
| **LLMs** | OpenAI GPT-4, GPT-4o-mini |
| **Embeddings** | OpenAI text-embedding-ada-002 |
| **Vector Store** | ChromaDB (HNSW Index, Cosine Similarity) |
| **Market Data** | YFinance (NSE/BSE Live Prices) |
| **News Search** | Tavily AI Search (1000 Free Searches/Month) |
| **Shared Memory** | Redis (A2A State, Session Persistence) |
| **Backend** | FastAPI + Uvicorn |
| **Testing** | Pytest (82 Tests, ~85% Coverage) |
| **Language** | Python 3.10+ |

---

## 🚀 QUICK START

### Prerequisites
- Python 3.10+
- OpenAI API Key ([Get one here](https://platform.openai.com))
- Tavily API Key ([Free at tavily.com](https://tavily.com))
- Redis (Optional — App runs without it)

### Installation

```bash
# Step 1 — Clone the repository
git clone https://github.com/satheeshkumarkoti/ai-workspace.git
cd ai-workspace/finnie-ai

# Step 2 — Install all dependencies
pip install -r requirements.txt

# Step 3 — Configure environment (Windows)
copy .env.template .env
# Open .env and add your API keys

# Step 4 — Load RAG Knowledge Base (run once)
python -m rag.ingestor

# Step 5 — Launch Finnie!
streamlit run ui/app.py
```

Open your browser at **http://localhost:8501** 🎉

### Run FastAPI Backend (Optional)

```bash
uvicorn api.main:app --reload --port 8000
# Swagger Docs → http://localhost:8000/docs
```

---

## 📁 PROJECT STRUCTURE

```
FINNIE-AI/
├── agents/
│   ├── orchestrator.py       # Intent Detection + A2A Routing (LangGraph)
│   ├── literacy_agent.py     # Agent 1 — RAG-Powered Financial Education
│   ├── market_agent.py       # Agent 2 — Live Data (YFinance) + News (Tavily)
│   ├── portfolio_agent.py    # Agent 3 — Portfolio Analysis + Risk Scoring
│   └── learning_agent.py     # Agent 4 — Personalized Learning Paths
├── rag/
│   ├── ingestor.py           # Document Chunking + Embedding Pipeline
│   ├── embedder.py           # OpenAI Embedding Wrapper
│   └── retriever.py          # ChromaDB Similarity Search
├── memory/
│   └── redis_store.py        # Shared A2A State + Session Memory
├── tools/
│   ├── tavily_tool.py        # Tavily AI News Search Tool
│   ├── yfinance_tool.py      # LangGraph-Compatible Market Data Tool
│   └── portfolio_tools.py    # Portfolio Calculation + Risk Scoring
├── api/
│   └── main.py               # FastAPI Backend (REST + Swagger)
├── ui/
│   └── app.py                # Streamlit Multi-Tab UI
├── tests/
│   ├── conftest.py           # Shared Fixtures
│   ├── test_orchestrator.py  # 15 Tests — Routing + Intent Detection
│   ├── test_agents.py        # 24 Tests — All 4 Agents
│   ├── test_rag.py           # 12 Tests — RAG Pipeline
│   ├── test_memory.py        # 16 Tests — Redis Store
│   └── test_tools.py         # 15 Tests — Tools + Integration
├── .env.template             # Environment Variable Template
├── requirements.txt          # Python Dependencies
├── pytest.ini                # Test Configuration
├── LICENSE                   # MIT License
└── README.MD
```

---

## 🧪 RUNNING TESTS

```bash
# Run all 82 tests
pytest

# Run with coverage report
pip install pytest-cov
pytest --cov=. --cov-report=term-missing

# Run a specific test file
pytest tests/test_agents.py -v
```

**Test Results:**
```
82 Passed  —  ~85% Code Coverage
├── test_orchestrator.py   15 Tests ✅
├── test_agents.py         24 Tests ✅
├── test_rag.py            12 Tests ✅
├── test_memory.py         16 Tests ✅
└── test_tools.py          15 Tests ✅
```

---

## 🖥️ UI FEATURES

| Tab | Features |
|---|---|
| 💬 **Chat** | Multi-Agent Chat, Agent Badge Indicators, Suggested Queries, Conversation History |
| 📊 **Portfolio** | Holdings Table, P&L Tracking, AI Risk Analysis, Add/Remove Holdings |
| 📈 **Market Trends** | Live Indices (NIFTY, SENSEX), Stock Prices, Tavily News Digest |
| 🎓 **Learning Path** | Personalized Curriculum, Progress Tracking, Module Completion |

---

## 📊 SAMPLE QUERIES

```
# Financial Literacy Agent (RAG)
"What is a SIP and how does it work?"
"Explain P/E ratio in simple terms"
"What are ELSS mutual funds?"
"How does compound interest work?"
"What is rupee cost averaging?"

# Market Data Agent (yFinance + Tavily)
"What is NIFTY 50 today?"
"Show me latest market trends"
"What do you suggest for investment today?"
"Should I invest in IT stocks now?"

# Portfolio Analyst Agent (A2A)
"Analyse my portfolio risk"
"Should I rebalance my investments?"
"What is my sector concentration?"
"How much profit am I making?"

# Learning Path Agent
"Build my learning path"
"I am a beginner, guide me"
"Create a tax-saving investment plan for me"
"What should I learn next?"
```

---

## 🔑 ENVIRONMENT VARIABLES

```env
# Required
OPENAI_API_KEY=sk-your-openai-key-here

# Tavily AI Search — Free 1000 Searches/Month
# Get your key at: https://tavily.com
TAVILY_API_KEY=tvly-your-tavily-key-here

# Optional — Session Persistence (App works without Redis)
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## 🗺️ ROADMAP

- [ ] LangGraph Full StateGraph Implementation
- [ ] Azure OpenAI Support
- [ ] Docker + Kubernetes Deployment
- [ ] M365 Copilot Integration
- [ ] Mobile-Responsive React Frontend
- [ ] Agent Performance Monitoring (LangSmith)
- [ ] Multi-Language Support (Hindi, Tamil)
- [ ] Voice Interface Integration
- [ ] Agentic Proctoring for Financial Quizzes

---

## 👤 AUTHOR

**SATHEESH KUMAR K**
Solution Architect | Gen AI & LLM Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://linkedin.com/in/satheesh-kumar-k11a98823)
[![GitHub](https://img.shields.io/badge/GitHub-Portfolio-black?logo=github)](https://github.com/satheeshkumarkoti)

- 18+ Years in Enterprise IT Architecture
- 10+ Years Java Full Stack | 2+ Years Generative AI
- AWS Certified Solutions Architect | Azure AI Engineer Associate
- Expertise: LangGraph · LangChain · RAG · Agentic AI · MCP · Spring Boot · AWS

---

## 📄 LICENSE

This project is licensed under the MIT License — see [LICENSE](./LICENSE) for details.

---

> *"Finnie makes financial literacy accessible to every Indian investor — one conversation at a time."*
