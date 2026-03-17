from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from api import search
from api import storage
from contextlib import asynccontextmanager
from db.postgres_db import init_db, clear_db
from db.qdrant_db import QdrantDB
from core.logger import get_logger
import time
import uuid

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    
    # init_db()
    # qdrant = QdrantDB()
    # qdrant.create_collection()
    
    yield
    
    # clear_db()
    # qdrant.delete_collection()
    logger.info("Shutting down application")

app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def add_trace_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error" }
    )


app.include_router(search.router)
app.include_router(storage.router)

@app.get("/")
async def health_check():
    return {"message": "The server is running."}