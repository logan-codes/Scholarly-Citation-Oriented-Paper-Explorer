from schema.search import SearchRequest
from services.retrieval import retrieval_service
from services.citationNetwork import CitationNetwork
from fastapi import Depends
from utils.logger import get_logger
from fastapi import APIRouter

router = APIRouter(prefix="/search")

@router.post("/")
async def search(search_request: SearchRequest, logger=Depends(get_logger)):
    """
    Search endpoint

    :param query: search query string
    """

    # Call the retrieval service
    results = retrieval_service(search_request.query, k_chunks=5, k_docs=3)

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
    logger.info(f"Search completed for query: {search_request.query}. Number of results: {len(results)}")
    return results