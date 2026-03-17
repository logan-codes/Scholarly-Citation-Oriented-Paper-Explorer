from schema.storage import StorageRequest, ErrorResponse, SuccessfulResponse
from core.logger import get_logger
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from services.storage_service import storage_service
from opentelemetry import trace

router = APIRouter(prefix="/store")
logger = get_logger(__name__)


@router.post("/")
async def storage(payload: StorageRequest, request: Request):
    logger.info("Starting Storage Service", extra={"year":payload.year, "per_page":payload.per_page})
    pub_year=payload.year
    per_page= payload.per_page
    limit=payload.limit
    if not pub_year and not per_page:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error_code="MISSING_PARAMETERS",
                message="year and per_page are required"
            ).model_dump()
        )

    if not pub_year:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error_code="YEAR_MISSING",
                message="year is required"
            ).model_dump()
        )

    if not per_page:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error_code="PER_PAGE_MISSING",
                message="per_page is required"
            ).model_dump()
        )
    
    try:
        papers=storage_service(pub_year=pub_year, per_page=per_page,limit=limit)
        return JSONResponse(
            status_code=200,
            content=SuccessfulResponse(
                    ingested= per_page,
                    papers=papers
            ).model_dump()
        )
    except Exception as e:
        logger.warning(f"Storage Service failed: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code="STORAGE_FAILED",
                message="something went wrong in the storing the pipeline.",
                details= {
                    "details": f"{e}"
                }
            ).model_dump()
        )