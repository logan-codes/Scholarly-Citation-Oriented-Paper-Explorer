from core.logger import logger

from typing import List, Dict, Any, Optional
from sqlalchemy import text

from db.postgres_db import SessionLocal
from db.qdrant_db import QdrantDB
from utils.embedding_util import embed_query
from db.repo.papers import PaperRepository
from db.models.papers import Paper
from utils.score_fusion_util import fuse_results

DEFAULT_LIMIT = 20
DEFAULT_VECTOR_LIMIT = 100
DEFAULT_KEYWORD_LIMIT = 100

def search_service(
    query: str,
    limit: int = DEFAULT_LIMIT,
) -> List[Dict[str, Any]]:
    logger.info(f"Starting search pipeline for query: {query[:50]}")

    query_vectors = embed_query(query)
    logger.info("Query embedded")

    qdrant=QdrantDB()
    vector_results = qdrant.search(
        query_vectors=query_vectors,
        limit=DEFAULT_VECTOR_LIMIT,
    )
    logger.info(f"Vector search returned {len(vector_results)} results")

    vector_candidate_ids = [r["id"] for r in vector_results]
    session = SessionLocal()
    with session:
        paper_repo = PaperRepository(session)
        keyword_results = paper_repo.search_papers_bm25(
            query=query,
            paper_ids=vector_candidate_ids if vector_candidate_ids else None,
        )
    logger.info(f"Keyword search returned {len(keyword_results)} results")

    all_paper_ids = list(set(
        [r["id"] for r in vector_results] + [r["id"] for r in keyword_results]
    ))

    pr_scores, velocity_scores = _fetch_scores(all_paper_ids)
    logger.info(f"Fetched PR and velocity scores for {len(pr_scores)} papers")

    fused_results = fuse_results(
        vector_results=vector_results,
        keyword_results=keyword_results,
        pr_scores=pr_scores,
        velocity_scores=velocity_scores,
    )
    logger.info(f"Fused results: {len(fused_results)} papers")

    final_results = _fetch_display_details(
        fused_results[:limit]
    )
    logger.info(f"Search complete. Returning {len(final_results)} results")

    return final_results

def _fetch_scores(
    paper_ids: List[str],
) -> tuple[Dict[str, float], Dict[str, float]]:
    if not paper_ids:
        return {}, {}

    session = SessionLocal()
    try:
        paper_repo=PaperRepository(session)
        pr_scores = {}
        velocity_scores = {}
        for id in paper_ids:
            paper=paper_repo.get_by_id(paper_id=id)
            doc_id = paper.paper_id
            pr_scores[doc_id]= paper.pr_score
            velocity_scores[doc_id]= paper.velocity_score
        return pr_scores, velocity_scores
    except Exception as e:
        logger.error(f"Failed to fetch scores: {e}")
        return {}, {}
    finally:
        session.close()

def _fetch_display_details(
    paper_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if not paper_results:
        return []

    paper_ids = [r["id"] for r in paper_results]
    score_map = {r["id"]: r["score"] for r in paper_results}

    session = SessionLocal()
    try:
        paper_repo=PaperRepository(session)
        result =[]
        details = []
        for id in paper_ids: 
            paper=paper_repo.get_by_id(paper_id=id)
            details.append({
                "paper_id": paper.paper_id,
                "openalex_id": paper.openalex_id,
                "title": paper.title,
                "abstract": paper.abstract,
                "venue": paper.venue,
                "year": paper.year,
                "citation_count": paper.citation_count,
                "pr_score": float(paper.pr_score) if paper.pr_score else 0.0,
                "velocity_score": float(paper.velocity_score) if paper.velocity_score else 0.0,
                "score": score_map.get(paper.paper_id, 0),
            })
        return sorted(details, key=lambda x: x["score"], reverse=True)
    except Exception as e:
        logger.error(f"Failed to fetch display details: {e}")
        return []
    finally:
        session.close()


if __name__ == "__main__":
    print(search_service(query="black holes", limit=5))