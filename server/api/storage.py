from schema.storage import StorageRequest, ErrorResponse, SuccessfulResponse
from server.core.logger import logger
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from services.storage_service import storage_service

router = APIRouter(prefix="/store")

@router.post("/")
async def storage(payload: StorageRequest):
    logger.info("Starting Storage Service")
    pub_year=payload.year
    per_page= payload.per_page
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
        storage_service(pub_year=pub_year, per_page=per_page)
        return SuccessfulResponse(
            ingested= per_page
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
            )
        )