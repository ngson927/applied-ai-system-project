import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rag_utils import load_knowledge_base, retrieve_relevant_chunks


def test_knowledge_base_loads():
    chunks = load_knowledge_base()
    assert len(chunks) > 0, "Knowledge base should contain at least one chunk"


def test_chunks_have_required_keys():
    chunks = load_knowledge_base()
    for chunk in chunks:
        assert "title" in chunk
        assert "text" in chunk
        assert len(chunk["text"]) > 0


def test_retrieve_returns_top_k():
    chunks = load_knowledge_base()
    results = retrieve_relevant_chunks("binary search midpoint", chunks, top_k=3)
    assert len(results) <= 3


def test_retrieve_relevant_content():
    chunks = load_knowledge_base()
    results = retrieve_relevant_chunks("binary search midpoint optimal", chunks, top_k=2)
    # At least one result should mention binary search
    combined = " ".join(results).lower()
    assert "binary" in combined or "search" in combined or "midpoint" in combined


def test_retrieve_empty_chunks():
    results = retrieve_relevant_chunks("anything", [], top_k=3)
    assert results == []
