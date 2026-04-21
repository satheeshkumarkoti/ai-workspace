"""
RAG Ingestor — Finnie
Loads financial education documents, chunks them, embeds them,
and stores in ChromaDB. Run this once before starting the app.

Usage:
    python -m rag.ingestor
"""
import os
import json
from typing import List
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

COLLECTION_NAME = "finnie_knowledge"
CHUNK_SIZE      = 500   # characters per chunk
CHUNK_OVERLAP   = 50


# ── Sample financial knowledge base (extend with real PDFs) ──
SAMPLE_DOCS = [
    {
        "title": "What is a SIP?",
        "content": """A Systematic Investment Plan (SIP) is a method of investing in mutual funds 
where you invest a fixed amount at regular intervals — weekly, monthly, or quarterly. 
SIPs allow investors to benefit from rupee cost averaging: when markets are down, 
your fixed amount buys more units; when markets are up, it buys fewer. 
Over time this averages out your cost per unit. 
SIPs can be started with as little as ₹500 per month on most platforms like Zerodha, Groww, or Paytm Money. 
The power of SIPs comes from compounding — reinvested returns generate returns of their own. 
A monthly SIP of ₹5,000 for 20 years at 12% annual return gives approximately ₹49 lakhs.""",
    },
    {
        "title": "Understanding ELSS Mutual Funds",
        "content": """ELSS (Equity Linked Savings Scheme) are tax-saving mutual funds under Section 80C 
of the Income Tax Act. You can claim a deduction of up to ₹1.5 lakhs per year by investing in ELSS. 
Key features: 3-year lock-in period (shortest among 80C instruments), 
equity exposure (invested primarily in stocks), historically returns of 12-15% CAGR over long periods. 
ELSS is better than PPF or NSC for investors with a long time horizon and moderate-to-high risk appetite. 
Popular ELSS funds include Mirae Asset Tax Saver, Axis Long Term Equity, and DSP Tax Saver Fund.""",
    },
    {
        "title": "P/E Ratio Explained",
        "content": """The Price-to-Earnings (P/E) ratio measures how much investors pay for each rupee of a company's earnings. 
Formula: P/E = Stock Price / Earnings Per Share (EPS). 
A P/E of 20 means investors pay ₹20 for every ₹1 of annual earnings. 
High P/E (>30): Market expects strong future growth — common in IT/tech stocks. 
Low P/E (<15): Stock may be undervalued or facing challenges. 
Industry comparison matters — compare P/E within the same sector. 
For NIFTY 50, the historical average P/E is around 18-22. 
Above 25 signals the market may be overvalued; below 15 may signal undervaluation.""",
    },
    {
        "title": "Diversification and Asset Allocation",
        "content": """Diversification means spreading investments across different asset classes, sectors, and geographies 
to reduce risk. The key principle: don't put all eggs in one basket.
Asset classes to consider: equity (stocks/mutual funds), debt (bonds/FDs), gold, real estate, international funds.
A common rule of thumb for equity allocation: 100 minus your age. 
A 30-year-old could have 70% in equity, 20% in debt, 10% in gold.
For Indian investors, avoid having more than 30-40% in a single sector.
Rebalance your portfolio once a year to maintain target allocations.""",
    },
    {
        "title": "Long Term Capital Gains (LTCG) Tax in India",
        "content": """LTCG tax applies when you sell equity investments held for more than 1 year.
Rate: 10% on gains exceeding ₹1 lakh in a financial year (no indexation benefit for equity).
Short Term Capital Gains (STCG) — held less than 1 year — taxed at 15%.
Tax harvesting strategy: Book profits up to ₹1 lakh each year tax-free, reinvest immediately.
This resets your cost basis and eliminates future LTCG liability on those units.
For debt mutual funds: LTCG (>3 years) is taxed as per your income tax slab with indexation benefit.""",
    },
]


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start  = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap
    return [c for c in chunks if len(c) > 50]


def ingest_documents():
    """Embed and store all documents into ChromaDB."""
    try:
        import chromadb

        chroma     = chromadb.PersistentClient(path="./chroma_db")
        collection = chroma.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        all_docs, all_ids, all_embeddings, all_meta = [], [], [], []
        doc_id = 0

        for doc in SAMPLE_DOCS:
            chunks = chunk_text(doc["content"])
            for i, chunk in enumerate(chunks):
                embed = client.embeddings.create(
                    input=chunk,
                    model="text-embedding-ada-002"
                ).data[0].embedding

                all_docs.append(chunk)
                all_ids.append(f"doc_{doc_id}_{i}")
                all_embeddings.append(embed)
                all_meta.append({"title": doc["title"], "chunk": i})
            doc_id += 1
            print(f"  ✅ Ingested: {doc['title']} ({len(chunks)} chunks)")

        collection.upsert(
            documents=all_docs,
            embeddings=all_embeddings,
            ids=all_ids,
            metadatas=all_meta
        )
        print(f"\nTotal chunks stored: {collection.count()}")

    except ImportError:
        print("chromadb not installed. Run: pip install chromadb")
    except Exception as e:
        print(f"Ingestion error: {e}")


if __name__ == "__main__":
    print("Finnie RAG Ingestor — loading knowledge base...")
    ingest_documents()
    print("Done! Knowledge base ready.")
