import sqlite3
from fastmcp import FastMCP
from typing import List, Dict, Any

mcp = FastMCP("ats-tools")

from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "ats.db"

# DB_PATH = "/data/ats.db"  LLM, LangChain, Langgrph, Agentic, MCP, RAG - > doployment (cloud)
# Req --> anlaysis --> design data flow --> implement tools --> test tools --> deploy server
# Python, FastAPI, SQLite, MCP, LLM, LangChain, LangGraph, Agentic, RAG

def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ats_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            candidate_id TEXT NOT NULL,
            ats_score REAL NOT NULL,
            decision TEXT,
            reasons TEXT
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    return conn

@mcp.tool()
def parse_jd(job_description: str
) -> Dict[str, Any]:
    """Parse job description and return structured data"""
    text = job_description.lower()
    role = "backend engineer"  if "backend" in text else "unknown"
    return {
        "role": role,
        "text_excerpt": job_description.strip()[:300],
    }

@mcp.tool()
def parse_resume(resume_text: str) -> Dict[str, Any]:
    """Parse resume text and return structured data"""
    # This is a mock implementation - replace with actual parsing logic
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "skills": ["Python", "fastapi", "docker"],
        "years_experience": 5,
        "raw_excerpt": resume_text.strip()[:300],
    }

@mcp.tool()
def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text"""
    # Mock implementation
    return ["python", "api", "development"]


@mcp.tool()
def extract_must_haves(job_description: str) -> List[str]:
    """Extract must-have requirements from job description"""
    # Mock implementation
    return ["5+ years experience", "python", "api development"]


@mcp.tool()
def store_score(
    job_id: str,
    candidate_id: str,
    ats_score: float,
    decision: str,
    reasons: str
) -> Dict[str, Any]:
    conn = _db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ats_scores (job_id, candidate_id, ats_score, decision, reasons)
        VALUES (?, ?, ?, ?, ?)
        """,
        (job_id, candidate_id, float(ats_score), decision, reasons)
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return {"status": "ok", "id": row_id}

@mcp.tool()
def list_scores(job_id: str) -> List[Dict[str, Any]]:
    """Retrieve all ATS scores for a given job"""
    conn = _db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, candidate_id, ats_score, decision, reasons, created_at
        FROM ats_scores
        WHERE job_id = ?
        ORDER BY created_at DESC
        """,
        (job_id,)
    )
    rows = cur.fetchall()
    conn.close()
    
    return [
        {
            "id": row[0],
            "candidate_id": row[1],
            "ats_score": row[2],
            "decision": row[3],
            "reasons": row[4],
            "created_at": row[5]
        }
        for row in rows
    ]


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)







