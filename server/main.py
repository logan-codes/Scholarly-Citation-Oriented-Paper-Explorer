from fastapi import FastAPI
from api.endpoint import search

app = FastAPI()

app.include_router(search.router)


@app.get("/")
async def root():
    return {"message": "The server is running."}