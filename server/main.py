from fastapi import FastAPI
from api import search
from api import storage
from contextlib import asynccontextmanager
from db.postgres_db import init_db, clear_db
from db.qdrant_db import QdrantDB

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting application...")
    
    # init_db()
    # qdrant = QdrantDB()
    # qdrant.create_collection()
    
    yield
    
    # clear_db()
    # qdrant.delete_collection()
    # shutdown logic
    print("Shutting down application...")
app = FastAPI(lifespan=lifespan)


app.include_router(search.router)
app.include_router(storage.router)


@app.get("/")
async def health_check():
    return {"message": "The server is running."}