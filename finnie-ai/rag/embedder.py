"""
RAG Embedder — Finnie
Wraps OpenAI text-embedding-ada-002 for generating vector embeddings.
Used by both the ingestor (batch) and retriever (single query).
"""
import os
from typing import List, Union
from dotenv import load_dotenv

load_dotenv()


def get_embedding(text: str) -> List[float]:
    """
    Generate a single embedding vector for a text string.
    Returns a 1536-dimension vector (text-embedding-ada-002).
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Clean text — remove excessive whitespace
    text = text.strip().replace("\n", " ")

    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts in a single API call.
    More efficient than calling get_embedding() in a loop.
    Max batch size: 2048 inputs per OpenAI API call.
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Clean all texts
    cleaned = [t.strip().replace("\n", " ") for t in texts]

    response = client.embeddings.create(
        input=cleaned,
        model="text-embedding-ada-002"
    )
    # Sort by index to preserve order
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two embedding vectors.
    Returns value between -1 and 1 (1 = identical, 0 = unrelated).
    Used for manual similarity checks outside ChromaDB.
    """
    import math
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1  = math.sqrt(sum(a * a for a in vec1))
    magnitude2  = math.sqrt(sum(b * b for b in vec2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)


def get_embedding_dimension() -> int:
    """Returns the embedding dimension for text-embedding-ada-002."""
    return 1536


if __name__ == "__main__":
    # Quick test
    print("Testing embedder...")
    vec = get_embedding("What is a SIP in Indian mutual funds?")
    print(f"Embedding dimension: {len(vec)}")
    print(f"First 5 values: {vec[:5]}")
    print("Embedder working correctly!")
