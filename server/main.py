from fastapi import FastAPI
from services.retrieval import retrieval_service
from services.citationNetwork import CitationNetwork

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

    # Start building citation network
    citation_network = CitationNetwork()
    citation_network.build_from_pdfs(pdf_files=results.keys(), paper_metadata={})

    # Run the citation network analysis
    scores=citation_network.weighted_pagerank()

    # Aggregating the results with citation scores
    sorted_results = sorted(
        results.items(),
        key=lambda item: scores.get(item[0], 0),
        reverse=True,
    )
    results = [
        {
            "document_id": doc_id,
            "chunks": chunks,
            "citation_score": scores.get(doc_id, 0),
        }
        for doc_id, chunks in sorted_results
    ]
    
    return results