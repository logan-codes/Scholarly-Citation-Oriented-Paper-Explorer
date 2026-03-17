from schema.search import SearchRequest, SearchResponse, SearchResult
from core.logger import get_logger
from services.search_service import search_service
from fastapi import APIRouter

router = APIRouter(prefix="/search")
logger = get_logger(__name__)


@router.post("/", response_model=SearchResponse)
async def search(payload: SearchRequest):
    logger.info(f"Search Starting |query:{payload.query}| limit:{payload.limit}")
    
    results = search_service(query=payload.query, limit=payload.limit)
    
    logger.info(f"Search completed successfully result_count:{len(results)}")
    return SearchResponse(
        query=payload.query,
        total=len(results),
        results=[SearchResult(**r) for r in results]
    )