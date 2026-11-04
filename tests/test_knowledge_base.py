"""Unit and API tests for the project knowledge base (project_knowledge_base)."""
import pytest
from fastapi.testclient import TestClient
from server import app
from project_knowledge_base.kb_core import (
    get_status,
    search_knowledge_base,
)

client = TestClient(app)


def test_kb_status():
    status = get_status()
    assert status.get("ready") is True
    assert status.get("document_count", 0) > 0
    assert "categories" in status
    assert "top_tools" in status


def test_kb_search():
    results = search_knowledge_base("reference", limit=5)
    assert len(results) > 0
    first = results[0]
    assert first.title
    assert first.rel_path
    assert first.category


def test_api_knowledge_status():
    resp = client.get("/api/knowledge/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["data"]["document_count"] > 0


def test_api_knowledge_search():
    resp = client.get("/api/knowledge/search", params={"q": "pipeline", "limit": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["count"] > 0
    assert len(data["results"]) <= 3


def test_api_knowledge_cross_search():
    resp = client.get("/api/knowledge/search", params={"q": "LUT", "cross_search": "true", "limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "watch_results" in data
    assert isinstance(data["watch_results"], list)


def test_api_knowledge_document():
    # First search to get an existing document id
    resp = client.get("/api/knowledge/search", params={"q": "pipeline", "limit": 1})
    assert resp.status_code == 200
    results = resp.json().get("results", [])
    if results:
        doc_id = results[0]["document_id"]
        doc_resp = client.get(f"/api/knowledge/document/{doc_id}")
        assert doc_resp.status_code == 200
        doc_data = doc_resp.json()
        assert doc_data["ok"] is True
        assert "document" in doc_data
        assert "content" in doc_data["document"]
        assert doc_data["document"]["id"] == doc_id
