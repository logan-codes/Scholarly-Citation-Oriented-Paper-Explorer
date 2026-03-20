from core.logger import get_logger
from typing import List, Dict, Any, Optional
from sqlalchemy import text

from db.postgres_db import SessionLocal
from db.qdrant_db import QdrantDB
from utils.embedding_util import embed_query
from db.repo.papers import PaperRepository
from db.models.papers import Paper
from utils.score_fusion_util import fuse_results

logger = get_logger(__name__)

DEFAULT_LIMIT = 20
DEFAULT_VECTOR_LIMIT = 100
DEFAULT_KEYWORD_LIMIT = 100

def search_service(
    query: str,
    limit: int = DEFAULT_LIMIT,
) -> List[Dict[str, Any]]:
    logger.info(f"Starting search pipeline for query: {query[:50]}...")

    query_vectors = embed_query(query)
    logger.info("Query embedded")

    qdrant=QdrantDB()
    vector_results = qdrant.search(
        query_vectors=query_vectors,
        limit=DEFAULT_VECTOR_LIMIT,
    )
    logger.info(f"Vector search returned {len(vector_results)} results")
    vector_candidate_ids = [r["payload"]["paper id"] for r in vector_results]
    
    session = SessionLocal()
    with session:
        paper_repo = PaperRepository(session)
        keyword_results = paper_repo.search_papers_bm25(
            query=query,
            paper_ids=vector_candidate_ids if vector_candidate_ids else None,
        )
    logger.info(f"Keyword search returned {len(keyword_results)} results")

    all_paper_ids = list(set(
        [r for r in vector_candidate_ids] + [r["id"] for r in keyword_results]
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

    vector_payloads ={r["payload"]["paper id"]: r["payload"] for r in vector_results}

    final_results = _fetch_display_details(
        fused_results[:limit],
        vector_payloads=vector_payloads
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
            paper=paper_repo.get_by_oa_id(oa_id=id)
            doc_id = paper.openalex_id
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
    vector_payloads: Dict[str, Dict]={}
) -> List[Dict[str, Any]]:
    if not paper_results:
        return []

    paper_ids = [r["id"] for r in paper_results]
    score_map = {r["id"]: r for r in paper_results}
    session = SessionLocal()
    try:
        paper_repo=PaperRepository(session)
        result =[]
        details = []
        for id in paper_ids: 
            paper=paper_repo.get_by_oa_id(oa_id=id)
            if paper is None:
                continue
            payload = vector_payloads.get(paper.openalex_id, {})
            details.append({
                "openalex_id": paper.openalex_id,
                "doi": paper.doi,
                "title": paper.title,
                "abstract": paper.abstract,
                "venue": paper.venue,
                "year": paper.year,
                "fields": payload.get("fields") or paper.fields,
                "authors":paper.authors,
                "contribution": payload.get("contribution",""),
                "citation_count": paper.citation_count,
                "relevancy_score": score_map.get(paper.openalex_id,{}).get("relevancy",0.0),
                "B25_score": score_map.get(paper.openalex_id,{}).get("BM25",0.0),
                "pr_score": score_map.get(paper.openalex_id,{}).get("pr_score",0.0),
                "velocity_score": score_map.get(paper.openalex_id,{}).get("velocity_score",0.0),
                "final_score": score_map.get(paper.openalex_id, {}).get("score",0.0),
            })
        return sorted(details, key=lambda x: x["final_score"], reverse=True)
    except Exception as e:
        logger.error(f"Failed to fetch display details: {e}")
        return []
    finally:
        session.close()


if __name__ == "__main__":
    print(search_service(query="black holes", limit=5))