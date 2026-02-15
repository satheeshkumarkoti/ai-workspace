from typing import TypedDict, Optional, List, Dict, Any

class State(TypedDict):
    job_id: str
    job_description: str
    resume_text: str
    candidate_id: str

    # MCP outputs
    profile: Optional[Dict[str, Any]]
    jd_profile: Optional[Dict[str, Any]]
    normalized_skills: Optional[List[str]]
    jd_keywords: Optional[List[str]]
    must_haves: Optional[List[str]]

    # Agent Outputs
    ats_score: Optional[float]
    decision: Optional[str] 
    reasons: Optional[str]

    # Persistence results
    stored: Optional[Dict[str, Any]]