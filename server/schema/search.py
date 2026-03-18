from pydantic import BaseModel
from typing import List, Optional

class SearchRequest(BaseModel):
    query: str
    limit: int = 20

class Author(BaseModel):
    name: str
    openalex_id: str | None = None

class SearchResult(BaseModel):
    openalex_id: str
    title: str
    abstract: Optional[str] = None
    venue: Optional[str] = None
    year: Optional[int] = None
    fields: Optional[List[str]] = None
    authors: Optional[List[Author]] = None
    citation_count: Optional[int] = 0
    contribution: str = ""
    relevancy_score:float = 0.0
    B25_score: float = 0.0
    pr_score: float = 0.0
    velocity_score: float = 0.0
    final_score: float = 0.0


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResult]
        