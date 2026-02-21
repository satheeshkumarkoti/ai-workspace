
# Building a RAG System Using FastAPI + PostgreSQL (pgvector) + OpenAI

A fully working **Retrieval-Augmented Generation (RAG)** system built with FastAPI. Upload `.txt` or `.pdf` documents and ask questions about them — the system finds the most relevant content and uses GPT to generate accurate answers.

---

## What It Does

1. User uploads a `.txt` or `.pdf` file via API
2. System parses the file and splits it into sentences using NLTK
3. Each sentence is embedded using OpenAI (`text-embedding-ada-002`) and stored in PostgreSQL with pgvector
4. User asks a question — system finds the most similar sentences and sends them to GPT to generate an answer

---

## Project Structure

```
rag-fastapi/
│
├── main.py                 # FastAPI app — all routes and startup logic
├── db.py                   # DB engine, session, models (File, FileChunk)
├── background_tasks.py     # NLTK chunking + OpenAI embedding (runs in background)
├── file_parser.py          # Text and PDF parsers with OCR fallback
├── file_parser_tests.py    # Tests for file parsers
├── api_tests.sh            # Bash script to test all API endpoints
├── .env                    # Environment variables (not committed to git)
├── .gitignore
├── requirements.txt
├── obama.txt               # Sample test document
├── obama.pdf               # Sample PDF document
└── obama-ocr.pdf           # Sample scanned/image-based PDF
```

---

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| **FastAPI** | REST API framework |
| **PostgreSQL + pgvector** | Vector storage and similarity search |
| **SQLAlchemy** | ORM for database operations |
| **OpenAI API** | Embeddings (`text-embedding-ada-002`) + Chat (`gpt-3.5-turbo`) |
| **NLTK** | Sentence tokenization for smart chunking |
| **PyPDF2 + pytesseract** | PDF parsing with OCR fallback |
| **Docker** | Run pgvector locally |

---

## Prerequisites

- Python 3.8+
- Docker Desktop
- OpenAI API key (with credits)

---

## Local Setup Guide

### Step 1 — Clone the repo

```bash
git clone <your-repo-url>
cd rag-fastapi
```

### Step 2 — Create virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pgvector \
            python-dotenv openai nltk PyPDF2 pytesseract pymupdf pillow
```

### Step 4 — Set up environment variables

Create a `.env` file in the project root:

```dotenv
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/rag_db
OPENAI_API_KEY=sk-your-openai-key-here
```

> ⚠️ Never commit `.env` to GitHub. It's already in `.gitignore`.

### Step 5 — Start pgvector with Docker

```bash
docker run -d \
  --name rag-pgvector \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=rag_db \
  -p 5433:5432 \
  pgvector/pgvector:pg16
```

> Use port **5433** to avoid conflicts if local PostgreSQL is running on 5432.

Enable the vector extension:

```bash
docker exec -it rag-pgvector psql -U postgres -d rag_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Step 6 — Run the server

```bash
uvicorn main:app --reload --port 8000
```

On startup, the app automatically creates the `files` and `file_chunks` tables.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all uploaded files |
| `POST` | `/uploadfile/` | Upload a `.txt` or `.pdf` file |
| `POST` | `/ask/` | Ask a question about a file |
| `POST` | `/find-similar-chunks/{file_id}` | Find similar text chunks |

### Swagger UI (interactive docs)

```
http://localhost:8000/docs
```

---

## Testing the API

### Upload a file

```bash
# Linux/Mac
curl -X POST "http://127.0.0.1:8000/uploadfile/" -F "file=@obama.txt"

# Windows PowerShell
curl.exe -X POST "http://127.0.0.1:8000/uploadfile/" -F "file=@obama.txt"
```

Expected response:
```json
{"info": "File saved and processing started", "filename": "obama.txt", "file_id": 1}
```

### List all files

```bash
curl.exe http://127.0.0.1:8000/
```

### Ask a question (wait 30 seconds after upload for embedding to complete)

```bash
# Windows PowerShell
$body = '{"document_id": 1, "question": "When was Obama elected for the second time?"}'
curl.exe -X POST "http://127.0.0.1:8000/ask/" -H "Content-Type: application/json" -d $body
```

```bash
# Linux/Mac
curl -X POST "http://127.0.0.1:8000/ask/" \
  -H "Content-Type: application/json" \
  -d '{"document_id": 1, "question": "When was Obama elected for the second time?"}'
```

### Find similar chunks

```bash
$body = '{"question": "Who is Barack Obama wife?"}'
curl.exe -X POST "http://127.0.0.1:8000/find-similar-chunks/1" -H "Content-Type: application/json" -d $body
```

### Run all tests at once

```bash
bash api_tests.sh
```

> The script uploads a file, waits 30 seconds for background embedding, then tests `/ask/` and `/find-similar-chunks/`.

---

## Database Schema

```
files                          file_chunks
──────────────────────         ─────────────────────────────
id          (PK)          ──►  id              (PK)
file_name                      file_id         (FK → files.id)
file_content                   chunk_text
                               chunk_embedding (Vector 1536)
```

### Check data in database

```bash
docker exec -it rag-pgvector psql -U postgres -d rag_db

# Inside psql:
\dt                                          -- list tables
SELECT id, file_name FROM files;             -- see uploaded files
SELECT COUNT(*) FROM file_chunks;            -- count chunks
SELECT id, chunk_text FROM file_chunks LIMIT 5;  -- sample chunks
\q                                           -- exit
```

---

## How RAG Works

```
UPLOAD FLOW:
User uploads obama.txt
        │
        ▼
Parse file content (TextParser / PDFParser with OCR fallback)
        │
        ▼
Save to files table → get file_id
        │
        ▼
Background task: NLTK splits text into sentences
        │
        ▼
Each sentence → OpenAI embedding API → 1536-float vector
        │
        ▼
Save to file_chunks table (chunk_text + chunk_embedding)

─────────────────────────────────────────────────────

QUESTION FLOW:
User asks: "When was Obama elected?"
        │
        ▼
Embed the question → 1536-float query vector
        │
        ▼
L2 distance search → find top 5 most similar chunks
        │
        ▼
Build prompt: system + context chunks + question
        │
        ▼
Send to GPT-3.5-turbo → generate answer
        │
        ▼
Return answer + source chunks used
```

---

## File Parser Design

```
BaseParser (Abstract)
    │
    ├── TextParser       → reads .txt files directly
    └── PDFParser        → tries PyPDF2 first
                           falls back to OCR (pytesseract + fitz)

ParserFactory            → registry: maps ".txt" / ".pdf" to parser
FileParser               → single interface, auto-selects the right parser
```

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `password authentication failed` | Wrong password or wrong port | Check `.env`, use port 5433 |
| `Connection refused` | Docker not running | `docker start rag-pgvector` |
| `type "vector" does not exist` | pgvector extension missing | `CREATE EXTENSION IF NOT EXISTS vector;` |
| `DB URL: None` | `.env` not loaded | Ensure `load_dotenv()` is at top of `db.py` |
| `NameError: engine not defined` | Wrong code order in `db.py` | Define engine before SessionLocal |
| `openai 429 insufficient_quota` | No OpenAI credits | Add billing at platform.openai.com |
| `JSON decode error` in PowerShell | PowerShell quote handling | Use `$body = '...'` variable or use `curl.exe` |

---

## Key Concepts

| Term | Meaning |
|------|---------|
| **Embedding** | A list of 1536 numbers representing the meaning of text |
| **pgvector** | PostgreSQL extension for storing and searching vectors |
| **L2 distance** | How far apart two vectors are — smaller = more similar |
| **RAG** | Retrieve relevant context, then generate answer using LLM |
| **Background task** | FastAPI runs embedding after returning HTTP response — keeps API fast |
| **NLTK** | Smart sentence splitter — respects sentence boundaries unlike word splitting |
| **OCR** | Optical Character Recognition — extracts text from image-based PDFs |