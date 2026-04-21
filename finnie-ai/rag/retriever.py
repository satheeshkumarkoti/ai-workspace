"""
RAG Retriever — Finnie
Queries ChromaDB vector store for relevant financial content chunks.
Used by Literacy Agent.
"""
import os
from typing import List

COLLECTION_NAME = "finnie_knowledge"


def retrieve(query: str, top_k: int = 3) -> List[str]:
    """
    Embed the query and retrieve top-k similar chunks from ChromaDB.
    Returns list of text chunks, empty list if store not populated.
    """
    try:
        import chromadb
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        chroma = chromadb.PersistentClient(path="./chroma_db")

        collection = chroma.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        if collection.count() == 0:
            return []

        # Embed the query
        embed_response = client.embeddings.create(
            input=query,
            model="text-embedding-ada-002"
        )
        query_embedding = embed_response.data[0].embedding

        # Query ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "distances"]
        )

        # Filter by similarity threshold (cosine distance < 0.4 = good match)
        chunks = []
        docs      = results.get("documents", [[]])[0]
        distances = results.get("distances",  [[]])[0]
        for doc, dist in zip(docs, distances):
            if dist < 0.4:
                chunks.append(doc)

        return chunks

    except ImportError:
        return []
    except Exception:
        return []
