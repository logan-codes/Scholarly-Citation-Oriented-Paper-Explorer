import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from services.apiOrchestration import fetch_arxiv, fetch_semantic_scholar, fetch_core
from dotenv import load_dotenv
import os

load_dotenv()

@pytest.mark.asyncio
async def test_fetch_arxiv():
    """Test fetching papers from arXiv."""
    papers = fetch_arxiv("machine learning", max_results=2)
    assert len(papers) == 2
    for paper in papers:
        assert paper["source"] == "arXiv"
        assert "title" in paper
        assert "authors" in paper
        assert "abstract" in paper
        assert "published" in paper
        assert "pdf_link" in paper

@pytest.mark.asyncio
async def test_fetch_semantic_scholar():
    """Test fetching papers from Semantic Scholar."""
    papers = fetch_semantic_scholar("deep learning", limit=2)
    assert len(papers) == 2
    for paper in papers:
        assert paper["source"] == "Semantic Scholar"
        assert "title" in paper
        assert "authors" in paper
        assert "abstract" in paper
        assert "year" in paper
        assert "citations" in paper
        assert "doi" in paper
        assert "url" in paper

@pytest.mark.asyncio
async def test_fetch_core():
    """Test fetching papers from CORE."""
    api_key= os.getenv("CORE_API_KEY")
    if not api_key:
        pytest.skip("CORE API key not set in environment variables.")
    papers = fetch_core("artificial intelligence", api_key=api_key, limit=2)
    assert len(papers) == 2
    for paper in papers:
        assert paper["source"] == "CORE"
        assert "title" in paper
        assert "authors" in paper
        assert "abstract" in paper
        assert "year" in paper
        assert "doi" in paper
        assert "url" in paper