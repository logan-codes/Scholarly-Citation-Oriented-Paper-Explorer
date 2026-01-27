from fastapi import FastAPI
from services.retrieval import retrieval_service

app = FastAPI()

@app.get("/")
async def health_check():
    """
    health check for the server

    :return: status ok
    """
    return {"status": "ok"}

@app.get("/search")
async def search(query: str):
    """
    Search endpoint

    :param query: search query string
    """

    # Call the retrieval service
    results = retrieval_service(query, k_chunks=5, k_docs=3)

    return results