from core.logger import logger

from typing import List, Dict, Any, Optional
from sqlalchemy import text

from db.postgres_db import SessionLocal
from server.db.qdrant_db import QdrantDB
from server.utils.embedding_util import embed_query
from db.repo.papers import PaperRepository
from server.utils.score_fusion_util import fuse_results

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
        paper_repo = PaperRepository()
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
    paper_ids: List[int],
) -> tuple[Dict[str, float], Dict[str, float]]:
    if not paper_ids:
        return {}, {}

    session = SessionLocal()
    try:
        paper_repo=PaperRepository(session)
        result =[]
        for id in paper_ids: 
            result.append(paper_repo.get_by_id(paper_id=id))
        
        pr_scores = {}
        velocity_scores = {}
        
        for row in result:
            doc_id = str(row[0])
            pr_scores[doc_id] = float(row[7])
            velocity_scores[doc_id] = float(row[8])
        
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
        for id in paper_ids: 
            result.append(paper_repo.get_by_id(paper_id=id))
        details = []
        for row in result:
            paper_id = row[0]
            details.append({
                "paper_id": paper_id,
                "openalex_id": row[1],
                "title": row[2],
                "abstract": row[3],
                "venue": row[4],
                "year": row[5],
                "citation_count": row[6],
                "pr_score": float(row[7]) if row[7] else 0.0,
                "velocity_score": float(row[8]) if row[8] else 0.0,
                "tags": row[9] if isinstance(row[9], list) else [],
                "contribution": row[10] or "",
                "score": score_map.get(paper_id, 0),
            })

        return sorted(details, key=lambda x: x["score"], reverse=True)
    except Exception as e:
        logger.error(f"Failed to fetch display details: {e}")
        return []
    finally:
        session.close()
