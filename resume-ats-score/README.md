**📄 Resume ATS Scorer – Agentic GenAI Application**
**📌 Project Overview**

Resume ATS Scorer is an Agentic GenAI application designed to evaluate candidate resumes against job descriptions using LLMs, MCP (Model Context Protocol), and LangGraph orchestration.

The system simulates a real-world Applicant Tracking System (ATS) by:

Parsing resumes and job descriptions

Scoring candidates using AI reasoning

Persisting ATS results via a distributed MCP tool server

The architecture is modular, scalable, and production-aligned, separating AI orchestration from persistence and tooling.

**🧠 High-Level Architecture**

The project is divided into two independent components:

MCP Server – Tool & Persistence Layer

MCP Orchestrator – Agentic AI Workflow Layer

This separation follows modern Agentic AI and microservice principles.

**🧩 Part 1: MCP Server (Tool & Persistence Layer)
🔹 Purpose**

The MCP Server acts as a tool provider responsible for:

Persisting ATS scores

Managing structured data storage

Exposing tools over HTTP using MCP protocol

It is intentionally LLM-agnostic and does not contain any AI logic.

**🔹 Key Responsibilities**

Exposes tools like:

store_score

parse_resume

parse_jd

Handles database interactions

Ensures data consistency and durability

**🔹 Technology Stack**

FastMCP – MCP tool server

SQLite – Lightweight relational database

Docker – Containerized deployment

Python – Backend implementation

**🔹 Why MCP Server?**

Decouples business logic from AI reasoning

Allows multiple orchestrators or agents to reuse the same tools

Enables future upgrades (SQLite → Postgres, local → cloud)

**🤖 Part 2: MCP Orchestrator (Agentic AI Layer)
🔹 Purpose**

The MCP Orchestrator is the Agentic AI brain of the system.

It coordinates multiple steps using LangGraph, invokes MCP tools, and applies LLM-based reasoning to compute ATS scores.

🔹 Agentic Workflow

The orchestrator executes a state-driven workflow:

Resume Parsing (MCP Tool)

Job Description Parsing (MCP Tool)

ATS Scoring Agent (LLM Reasoning)

Score Persistence (MCP Tool)

Each step operates on a shared state object, enabling deterministic and debuggable execution.

**🔹 Technology Stack**

LangGraph – Agent workflow orchestration

LangChain – LLM abstraction

Google Gemini / Vertex AI – LLM provider

MCP Client Adapters – Tool invocation

Async Python – Non-blocking execution

🔹 Why LangGraph?

Explicit control over agent flow

Deterministic execution

Better than linear chains for complex workflows

Suitable for Agentic AI systems

🔄 Why Agentic Architecture?

This project follows Agentic AI principles:

Agents reason, decide, and act

Tools are externalized via MCP

State flows through well-defined nodes

AI decisions are auditable and reproducible

This architecture mirrors production-grade GenAI systems used in real enterprises.

**🗃️ Data Flow Summary**
Resume + JD
     ↓
MCP Tools (Parsing)
     ↓
LLM ATS Scoring Agent
     ↓
MCP Tool (store_score)
     ↓
SQLite Database

**🚀 Key Highlights**

Agentic AI with LangGraph

MCP-based tool abstraction

Clean separation of concerns

Docker-ready MCP Server

Persistent ATS scoring

Production-aligned design

**🧪 Use Cases**

Resume screening automation

AI-powered candidate ranking

HR tech experimentation

Agentic GenAI learning project

**📌 Future Enhancements**

Replace SQLite with PostgreSQL

Add vector embeddings for semantic matching

Introduce multi-agent scoring strategies

Add observability with LangSmith

Deploy MCP server to cloud (GCP / AWS)

**🎯 Learning Outcome**s

Hands-on experience with Agentic AI

Understanding MCP protocol in practice

LangGraph-based orchestration

Real-world GenAI system design

Debugging distributed AI systems

