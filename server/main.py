from fastapi import FastAPI
from api import search
from api import storage

app = FastAPI()

app.include_router(search.router)
app.include_router(storage.router)


@app.get("/")
async def health_check():
    return {"message": "The server is running."}