"""
Tests for RAG Pipeline — ingestor, retriever, embedder
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock


# ══════════════════════════════════════════════════════════════
# INGESTOR TESTS
# ══════════════════════════════════════════════════════════════

class TestIngestor:

    def test_chunk_text_basic(self):
        from rag.ingestor import chunk_text
        text   = "A" * 1200
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) > 1

    def test_chunk_text_overlap(self):
        from rag.ingestor import chunk_text
        text   = "Hello world " * 100
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) >= 1

    def test_chunk_text_short_input(self):
        from rag.ingestor import chunk_text
        text   = "Short text"
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) == 1
        assert chunks[0] == "Short text"

    def test_chunk_text_filters_tiny_chunks(self):
        from rag.ingestor import chunk_text
        text   = "Hi" + ("X" * 500)
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        for chunk in chunks:
            assert len(chunk) > 50

    def test_sample_docs_not_empty(self):
        from rag.ingestor import SAMPLE_DOCS
        assert len(SAMPLE_DOCS) > 0
        for doc in SAMPLE_DOCS:
            assert "title"   in doc
            assert "content" in doc
            assert len(doc["content"]) > 100

    def test_sample_docs_cover_key_topics(self):
        from rag.ingestor import SAMPLE_DOCS
        titles = [d["title"].lower() for d in SAMPLE_DOCS]
        assert any("sip"        in t for t in titles)
        assert any("elss"       in t for t in titles)
        assert any("diversif"   in t or "asset" in t for t in titles)


# ══════════════════════════════════════════════════════════════
# RETRIEVER TESTS
# ══════════════════════════════════════════════════════════════

class TestRetriever:

    def test_retrieve_returns_list(self):
        from rag.retriever import retrieve
        with patch("chromadb.PersistentClient") as mock_chroma:
            mock_collection = MagicMock()
            mock_collection.count.return_value = 0
            mock_chroma.return_value.get_or_create_collection.return_value = mock_collection
            with patch("openai.OpenAI"):
                result = retrieve("What is SIP?")
                assert isinstance(result, list)

    def test_retrieve_empty_store_returns_empty(self):
        from rag.retriever import retrieve
        with patch("chromadb.PersistentClient") as mock_chroma:
            mock_collection = MagicMock()
            mock_collection.count.return_value = 0
            mock_chroma.return_value.get_or_create_collection.return_value = mock_collection
            result = retrieve("test query")
            assert result == []

    def test_retrieve_filters_low_similarity(self):
        from rag.retriever import retrieve
        with patch("chromadb.PersistentClient") as mock_chroma:
            mock_collection = MagicMock()
            mock_collection.count.return_value = 3
            mock_collection.query.return_value = {
                "documents": [["chunk1", "chunk2"]],
                "distances": [[0.8, 0.9]]   # both above 0.4 threshold → filtered out
            }
            mock_chroma.return_value.get_or_create_collection.return_value = mock_collection
            with patch("openai.OpenAI") as mock_openai:
                mock_openai.return_value.embeddings.create.return_value = MagicMock(
                    data=[MagicMock(embedding=[0.1] * 1536)]
                )
                result = retrieve("test query")
                assert result == []

    def test_retrieve_returns_good_similarity_chunks(self):
        from rag.retriever import retrieve
        with patch("chromadb.PersistentClient") as mock_chroma:
            mock_collection = MagicMock()
            mock_collection.count.return_value = 3
            mock_collection.query.return_value = {
                "documents": [["SIP is a plan", "ELSS saves tax"]],
                "distances": [[0.2, 0.3]]    # both below 0.4 threshold → included
            }
            mock_chroma.return_value.get_or_create_collection.return_value = mock_collection
            with patch("openai.OpenAI") as mock_openai:
                mock_openai.return_value.embeddings.create.return_value = MagicMock(
                    data=[MagicMock(embedding=[0.1] * 1536)]
                )
                result = retrieve("What is SIP?")
                assert len(result) == 2
                assert "SIP is a plan" in result

    def test_retrieve_handles_chromadb_import_error(self):
        from rag.retriever import retrieve
        with patch("builtins.__import__", side_effect=ImportError("chromadb not installed")):
            result = retrieve("test")
            assert result == []

    def test_retrieve_handles_generic_exception(self):
        from rag.retriever import retrieve
        with patch("chromadb.PersistentClient", side_effect=Exception("DB error")):
            result = retrieve("test")
            assert result == []
