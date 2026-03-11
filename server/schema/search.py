from pydantic import BaseModel
from typing import List, Optional


class SearchRequest(BaseModel):
    query: str
    limit: int = 20


class SearchResult(BaseModel):
    paper_id: int
    openalex_id: str
    title: str
    abstract: Optional[str] = None
    venue: Optional[str] = None
    year: Optional[int] = None
    citation_count: Optional[int] = 0
    pr_score: float = 0.0
    velocity_score: float = 0.0
    tags: List[str] = []
    contribution: str = ""
    score: float = 0.0


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResult]
        