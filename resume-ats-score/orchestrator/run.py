from graph import build_graph
import asyncio

async def main():
    graph = build_graph()
    # Add your main execution logic here
    initial_state = {
        "job_id": "job-001",
        "candidate_id": "cand-001",
        "job_description": "Backend Engineer: Python, FastAPI, Docker. Bonus: Kubernetes, Postgres",
        "resume_text": """
        John Doe
        Senior Backend Engineer with 8 years experience.
        Skills: Python, FastAPI, Docker, Kubernetes, Postgres, MySQL
        Experience: Led backend team, designed scalable APIs
        """,
        "profile": None,
        "jd_profile": None,
        "normalized_skills": None,
        "must_haves": None,
        "ats_score": None,
        "decision": None,
        "reasons": None,
        "stored": None
    }
    output = await graph.ainvoke(initial_state)
    print("\n ATS RESULT")
    print(f"Score: {output['ats_score']}")
    print(f"Decision: {output['decision']}")
    print(f"Reasons: {output['reasons']}")
    print(f"Stored: {output['stored']}")

if __name__ == "__main__":
    asyncio.run(main())

