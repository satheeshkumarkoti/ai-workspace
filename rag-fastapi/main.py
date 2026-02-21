import os
import shutil
import logging
from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text

from db import init_db, get_db, File, FileChunk
from file_parser import FileParser
from background_tasks import EmbedProcessor

load_dotenv("/usercode/.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

UPLOAD_FOLDER = "/usercode/uploads"
ALLOWED_EXTENSIONS = {".txt", ".pdf"}

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ── Pydantic Models ───────────────────────────────────────────
class AskModel(BaseModel):
    question: str
    file_id: int


# ── Startup ───────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()


# ── Helper: similarity search ─────────────────────────────────
def get_similar_chunks(file_id: int, embedding: list, db: Session, limit: int = 5):
    """
    Finds the most similar chunks using L2 distance.
    Smaller distance = more similar.
    """
    chunks = db.query(FileChunk).filter(FileChunk.file_id == file_id).all()
    if not chunks:
        return []

    # Sort by L2 distance between query embedding and chunk embedding
    scored = []
    for chunk in chunks:
        if chunk.chunk_embedding is not None:
            distance = chunk.chunk_embedding.l2_distance(embedding)
            scored.append((distance, chunk.chunk_text))

    scored.sort(key=lambda x: x[0])
    return [text for _, text in scored[:limit]]


# ── Endpoints ─────────────────────────────────────────────────
@app.get("/")
def read_root(db: Session = Depends(get_db)):
    """Returns all uploaded files with their IDs and names."""
    files = db.query(File).all()
    return [{"file_id": f.id, "file_name": f.file_name} for f in files]


@app.post("/uploadfile/")
async def upload_file(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Step 1: Validate file type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed.")

    # Step 2: Save file to disk
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    # Step 3: Parse file content
    try:
        parser = FileParser(filepath=file_path)
        content = parser.parse()
    except Exception as e:
        logger.error(f"Failed to parse file: {e}")
        raise HTTPException(status_code=500, detail=f"Could not parse file: {e}")

    # Step 4: Save File record to DB
    try:
        db_file = File(file_name=file.filename, file_content=content)
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save to DB: {e}")
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    # Step 5: Offload chunking + embedding to background
    processor = EmbedProcessor(db=db, file_id=db_file.id, content=content)
    background_tasks.add_task(processor.chunk_and_embed)

    return {
        "info": "File saved and processing started",
        "filename": file.filename,
        "file_id": db_file.id
    }


# Fix find-similar-chunks to POST with JSON body
class SimilarChunksModel(BaseModel):
    question: str

@app.post("/find-similar-chunks/{file_id}")  # ← POST not GET
def find_similar_chunks(
    file_id: int,
    request: SimilarChunksModel,
    db: Session = Depends(get_db)
):
    response = client.embeddings.create(
        input=request.question,
        model="text-embedding-ada-002"
    )
    query_embedding = response.data[0].embedding
    chunks = get_similar_chunks(file_id, query_embedding, db)
    if not chunks:
        raise HTTPException(status_code=404, detail="No chunks found.")
    return {"similar_chunks": chunks}


# Fix AskModel
class AskModel(BaseModel):
    question: str
    document_id: int  # ← rename from file_id

# Fix ask_question to use document_id
@app.post("/ask/")
def ask_question(request: AskModel, db: Session = Depends(get_db)):
    embed_response = client.embeddings.create(
        input=request.question,
        model="text-embedding-ada-002"
    )
    query_embedding = embed_response.data[0].embedding
    chunks = get_similar_chunks(request.document_id, query_embedding, db)  # ← document_id
    if not chunks:
        raise HTTPException(status_code=404, detail="No chunks found.")
    context = "\n\n".join(chunks)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Answer based only on the provided context."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {request.question}"}
        ],
        temperature=0.2
    )
    return {"answer": response.choices[0].message.content, "chunks_used": chunks}