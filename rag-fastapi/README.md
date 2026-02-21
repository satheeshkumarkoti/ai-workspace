
# Building a RAG System Using FastAPI + PostgreSQL + OpenAI

### Local Setup Guide 

---

## WHAT WE ARE BUILDING

A system where:
1. User uploads a `.txt` document via API
2. System chunks the text, generates embeddings using OpenAI, stores in PostgreSQL (pgvector)
3. User sends a question via chat API
4. System finds the most relevant chunks (semantic search) and sends them to GPT to generate an answer

---

## FOLDER / FILE STRUCTURE

```
rag-fastapi/
│
├── main.py               # FastAPI app, registers routes, creates DB tables
├── db.py                 # DB engine, session, Base
├── models.py             # SQLAlchemy table definition (with vector column)
├── schemas.py            # Pydantic models for request/response validation
├── embeddings.py         # Chunking + OpenAI embedding logic
├── routes/
│   ├── __init__.py       # Empty file (makes routes a package)
│   ├── ingest.py         # POST /ingest — upload & store document
│   └── chat.py           # POST /chat  — ask question, get answer
├── .env                  # Environment variables (DB URL, OpenAI key)
└── requirements.txt      # All dependencies
```

---

## STEP 1: DOCKER — Run pgvector Locally

pgvector is a PostgreSQL extension that adds vector storage and similarity search.

```bash
docker run -d \
    --name rag-pgvector \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=rag_db \
    -p 5433:5432 \
    pgvector/pgvector:pg16
```

> Use port **5433** if you already have local PostgreSQL running on 5432.

### Enable the vector extension inside the DB:
```bash
docker exec -it rag-pgvector psql -U postgres -d rag_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Verify it's working:
```bash
docker exec -it rag-pgvector psql -U postgres -d rag_db -c "\dx"
```
You should see `vector` listed in extensions.

---

## STEP 2: Install Dependencies

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pgvector python-dotenv openai
```

### requirements.txt
```
fastapi
uvicorn
sqlalchemy
psycopg2-binary
pgvector
python-dotenv
openai
```

---

## STEP 3: Environment Variables

### .env
```dotenv
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/rag_db
OPENAI_API_KEY=sk-your-openai-key-here
```

> Never commit `.env` to GitHub. Add it to `.gitignore`.

---

## STEP 4: Database Connection

### db.py
```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print("DB URL:", DATABASE_URL)

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Session factory — used in routes to talk to DB
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base class for all models
Base = declarative_base()


def get_db():
        """
        FastAPI dependency that provides a DB session per request.
        Automatically closes session when request is done.
        """
        db = SessionLocal()
        try:
                yield db
        finally:
                db.close()


def test_connection():
        with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("DB Test Result:", result.scalar())
```

---

## STEP 5: Database Model (Table Definition)

### models.py
```python
from sqlalchemy import Column, Integer, String, Text
from pgvector.sqlalchemy import Vector
from db import Base


class Document(Base):
        """
        Represents a single text chunk stored with its embedding.

        - filename : original file name (for source tracking)
        - chunk    : the actual text piece
        - embedding: 1536-dimensional vector from OpenAI
        """
        __tablename__ = "documents"

        id        = Column(Integer, primary_key=True, index=True)
        filename  = Column(String,  nullable=False)
        chunk     = Column(Text,    nullable=False)
        embedding = Column(Vector(1536), nullable=False)
```

> **Why 1536?**
> OpenAI's `text-embedding-ada-002` model outputs a vector of 1536 floats.
> If you switch models, this number must match the new model's output dimension.

---

## STEP 6: Pydantic Schemas (Request & Response Models)

### schemas.py
```python
from pydantic import BaseModel


class ChatRequest(BaseModel):
        """Request body for the /chat endpoint."""
        question: str
        top_k: int = 5          # how many chunks to retrieve


class ChunkResult(BaseModel):
        """A single retrieved chunk with its similarity score."""
        chunk: str
        similarity: float


class ChatResponse(BaseModel):
        """Response from the /chat endpoint."""
        answer: str
        sources: list[ChunkResult]
```

---

## STEP 7: Embeddings & Chunking Logic

### embeddings.py
```python
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_embedding(text: str) -> list[float]:
        """
        Calls OpenAI to convert text into a 1536-dimensional vector.
        This vector captures the 'meaning' of the text numerically.
        """
        response = client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
        )
        return response.data[0].embedding


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """
        Splits a large text into smaller overlapping chunks.

        Why overlap? So that context at the boundary of two chunks isn't lost.

        Example:
                chunk_size = 500 words
                overlap    = 50 words
                Chunk 1: words 0–499
                Chunk 2: words 450–949   ← 50-word overlap with chunk 1
                Chunk 3: words 900–1399
        """
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
                chunk = " ".join(words[i : i + chunk_size])
                chunks.append(chunk)
                i += chunk_size - overlap
        return chunks
```

---

## STEP 8: Ingest Route — Upload & Store Document

### routes/ingest.py
```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models import Document
from embeddings import get_embedding, chunk_text

router = APIRouter()


@router.post("/ingest")
async def ingest_document(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
        """
        Upload a .txt file. The system will:
        1. Read the file content
        2. Split it into overlapping chunks
        3. Generate an embedding for each chunk using OpenAI
        4. Store each chunk + embedding in PostgreSQL
        """

        # Only allow .txt files
        if not file.filename.endswith(".txt"):
                raise HTTPException(status_code=400, detail="Only .txt files are supported.")

        # Read and decode the file
        content = await file.read()
        try:
                text = content.decode("utf-8")
        except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text.")

        # Chunk the text
        chunks = chunk_text(text)
        if not chunks:
                raise HTTPException(status_code=400, detail="File appears to be empty.")

        # Embed each chunk and save to DB
        saved = 0
        for chunk in chunks:
                embedding = get_embedding(chunk)
                doc = Document(
                        filename=file.filename,
                        chunk=chunk,
                        embedding=embedding
                )
                db.add(doc)
                saved += 1

        db.commit()
        return {
                "message": f"Successfully ingested '{file.filename}'",
                "chunks_stored": saved
        }
```

---

## STEP 9: Chat Route — Ask a Question

### routes/chat.py
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import OpenAI
import os

from db import get_db
from embeddings import get_embedding
from schemas import ChatRequest, ChatResponse, ChunkResult

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
        """
        Accept a user question and return an AI-generated answer.

        Steps:
        1. Embed the user's question
        2. Search DB for the top-K most similar chunks (cosine similarity)
        3. Build a prompt combining context + question
        4. Send to OpenAI GPT and return the answer
        """

        # Step 1: Embed the question
        query_embedding = get_embedding(request.question)

        # Step 2: Vector similarity search using pgvector's <=> operator (cosine distance)
        # Lower <=> value = more similar. We convert to similarity: 1 - distance
        results = db.execute(
                text("""
                        SELECT chunk, 1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                        FROM documents
                        ORDER BY embedding <=> CAST(:embedding AS vector)
                        LIMIT :top_k
                """),
                {
                        "embedding": str(query_embedding),
                        "top_k": request.top_k
                }
        ).fetchall()

        if not results:
                raise HTTPException(status_code=404, detail="No documents found. Please ingest documents first.")

        # Step 3: Build context string from retrieved chunks
        context = "\n\n---\n\n".join([row.chunk for row in results])

        # Step 4: Send to OpenAI GPT
        response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                        {
                                "role": "system",
                                "content": (
                                        "You are a helpful assistant. Answer the user's question "
                                        "based ONLY on the context provided below. "
                                        "If the answer is not in the context, say 'I don't have enough information to answer that.'"
                                )
                        },
                        {
                                "role": "user",
                                "content": f"Context:\n{context}\n\nQuestion: {request.question}"
                        }
                ],
                temperature=0.2    # low temperature = more factual, less creative
        )

        answer = response.choices[0].message.content

        # Return answer + source chunks with similarity scores
        sources = [
                ChunkResult(chunk=row.chunk, similarity=round(float(row.similarity), 4))
                for row in results
        ]

        return ChatResponse(answer=answer, sources=sources)
```

---

## STEP 10: Main App Entry Point

### main.py
```python
from fastapi import FastAPI
from db import engine, Base
import models  # important: registers Document model with Base
from routes.ingest import router as ingest_router
from routes.chat import router as chat_router

# Create all tables in DB on startup (if they don't exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(
        title="RAG System API",
        description="Upload documents and chat about their content using OpenAI.",
        version="1.0.0"
)

# Register routes
app.include_router(ingest_router, prefix="/api", tags=["Ingest"])
app.include_router(chat_router,   prefix="/api", tags=["Chat"])


@app.get("/")
def root():
        return {"status": "RAG API is running ✅"}
```

### Run the server:
```bash
uvicorn main:app --reload --port 8000
```

### Auto-generated API docs (Swagger UI):
```
http://localhost:8000/docs
```

---

## STEP 11: Testing the API

### Test 1 — Health Check
```bash
curl http://localhost:8000/
```
Expected: `{"status": "RAG API is running ✅"}`

---

### Test 2 — Ingest a Document
Create a sample text file first:
```
echo "FastAPI is a modern, fast web framework for building APIs with Python. It is based on standard Python type hints. PostgreSQL is a powerful open-source relational database. pgvector adds vector similarity search to PostgreSQL." > sample.txt
```

Upload it:
```bash
curl -X POST http://localhost:8000/api/ingest \
    -F "file=@sample.txt"
```
Expected:
```json
{
    "message": "Successfully ingested 'sample.txt'",
    "chunks_stored": 1
}
```

---

### Test 3 — Ask a Question
```bash
curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"question": "What is FastAPI?", "top_k": 3}'
```
Expected:
```json
{
    "answer": "FastAPI is a modern, fast web framework for building APIs with Python...",
    "sources": [
        {"chunk": "FastAPI is a modern...", "similarity": 0.9231}
    ]
}
```

---

## HOW THE FULL FLOW WORKS (Concept Summary)

```
INGEST FLOW:
────────────
User uploads sample.txt
                │
                ▼
Split into chunks (500 words, 50 overlap)
                │
                ▼
For each chunk → call OpenAI Embeddings API → get 1536-float vector
                │
                ▼
INSERT INTO documents (filename, chunk, embedding) → PostgreSQL


CHAT FLOW:
──────────
User asks: "What is FastAPI?"
                │
                ▼
Embed the question → get 1536-float query vector
                │
                ▼
SELECT chunk FROM documents ORDER BY embedding <=> query_vector LIMIT 5
(finds the 5 most semantically similar chunks)
                │
                ▼
Build prompt: "Here is the context... Answer this question..."
                │
                ▼
Send to GPT-3.5-turbo → get answer
                │
                ▼
Return answer + source chunks to user
```

---

## pgvector OPERATORS CHEAT SHEET

| Operator | Type             | When to use               |
|----------|------------------|---------------------------|
| `<=>`    | Cosine distance  | Text embeddings (default) |
| `<->`    | L2 / Euclidean   | Image embeddings          |
| `<#>`    | Inner product    | When vectors are normalized |

Similarity = `1 - cosine_distance`. Range: 0 (unrelated) to 1 (identical).

---

## COMMON ERRORS & FIXES

| Error | Cause | Fix |
|-------|-------|-----|
| `password authentication failed` | Wrong PG password | `ALTER USER postgres WITH PASSWORD 'postgres';` inside psql |
| `connection refused on 5432` | Port conflict with local PG | Use `-p 5433:5432` in Docker, update `.env` to 5433 |
| `type "vector" does not exist` | pgvector extension missing | `CREATE EXTENSION IF NOT EXISTS vector;` |
| `dimension mismatch` | Model changed or wrong size | Ensure `Vector(1536)` matches your embedding model |
| `.env values are None` | `load_dotenv()` not called | Add `load_dotenv()` at top of `db.py` and `embeddings.py` |
| `ModuleNotFoundError: pgvector` | Package not installed | `pip install pgvector` |
| `openai.AuthenticationError` | Wrong API key | Check `OPENAI_API_KEY` in `.env` |
| `No documents found` | Ingestion not done yet | Call `/api/ingest` before `/api/chat` |

---

## KEY CONCEPTS GLOSSARY

| Term | Meaning |
|------|---------|
| **Embedding** | A list of numbers (vector) that represents the meaning of text |
| **Chunking** | Splitting large text into smaller pieces for better retrieval |
| **Cosine Similarity** | Measures how similar two vectors are (0=different, 1=identical) |
| **pgvector** | PostgreSQL extension that stores and searches vectors |
| **RAG** | Retrieve relevant context first, then generate an answer using LLM |
| **`<=>` operator** | pgvector's cosine distance operator for nearest-neighbor search |
| **top_k** | How many similar chunks to retrieve before sending to LLM |
| **Temperature** | Controls GPT creativity: 0=factual, 1=creative |
