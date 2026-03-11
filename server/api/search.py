from schema.search import SearchRequest, SearchResponse, SearchResult
from server.core.logger import logger
from server.services.search_service import search_service
from fastapi import APIRouter

router = APIRouter(prefix="/search")

@router.post("/", response_model=SearchResponse)
async def search(payload: SearchRequest):
    logger.info("Search Starting")
    results = search_service(query=payload.query, limit=payload.limit)
    logger.info("Search completed successfully")
    return SearchResponse(
        query=payload.query,
        total=len(results),
        results=[SearchResult(**r) for r in results]
    )