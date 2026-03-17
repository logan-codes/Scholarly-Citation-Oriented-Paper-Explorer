from core.logger import get_logger

from services.enrich_service import enrich_paper
from schema.enrich import EnrichmentResult
from services.api_harvest_service import stream_data
from services.pagerank_service import update_global_pr, update_citation_velocity

from db.repo.papers import PaperRepository
from db.repo.citation_edges import CitationEdgeRepository
from db.repo.author_scores import AuthorScoreRepository
from db.postgres_db import SessionLocal
from db.qdrant_db import QdrantDB
from db.models.citation_edges import CitationEdge
from db.models.author_scores import AuthorScore

from typing import Dict, List

from utils.embedding_util import embed_abstract, embed_contribution, embed_title
from utils.llm_util import get_groq_llm

logger = get_logger(__name__)

# Store raw data in Postgres
def _store_postgres(paper: Dict) -> str:
    logger.info("Storing paper in Postgres")

    session = SessionLocal()
    try:
        paper_repo = PaperRepository(session)
        edge_repo  = CitationEdgeRepository(session)
        author_repo = AuthorScoreRepository(session)

        
        openalex_id = paper["openalex_id"]

        # Skip if already ingested 
        existing = paper_repo.get_by_oa_id(str(openalex_id))
        if existing:
            logger.debug("Skipping duplicate: %s", openalex_id)
            return existing.openalex_id
        if paper.get("doi")!=None:
            # Insert paper 
            paper_row = paper_repo.insert({
                "openalex_id":    openalex_id,
                "doi":            paper.get("doi"),
                "title":          paper["title"],
                "abstract":       paper.get("abstract"),
                "venue":          paper.get("venue"),
                "year":           paper.get("year"),
                "fields":         paper.get("fields"),
                "authors":        paper.get("authors"),
                "citation_count": paper.get("citation_count", 0),
                "counts_by_year": paper.get("counts_by_year"),
                "open_access":    paper.get("open_access", False),
            })

            # Citation edges (citing → referenced) 
            for ref_id in paper.get("referenced_works", []):
                edge = CitationEdge(
                    citing_id=paper_row.openalex_id,
                    cited_id=ref_id,
                )
                edge_repo.upsert_by_citing_id(edge)

            # Author scores (seed rows) 
            for author in paper.get("authors", []):
                author_oa_id = author.get("openalex_id")
                if not author_oa_id:
                    continue
                author_score = AuthorScore(
                    openalex_author_id=author_oa_id,
                    author_name=author.get("name"),
                )
                author_repo.upsert(author_score)

            return paper_row.openalex_id

        logger.info(f"Stored {openalex_id} papers" )
    except Exception:
        session.rollback()
        logger.exception("Postgres storage failed")
        raise
    finally:
        session.close()

# LLM Enrichment (tags + contributions)
def _enrich(paper: Dict)->EnrichmentResult:
    llm = get_groq_llm()

    session = SessionLocal()
    try:
        paper_repo = PaperRepository(session)

        enrichment_result = enrich_paper(llm=llm, title=paper.get("title",""), abstract=paper.get("abstract",""))

        # Updates enrich flag on Postgres
        paper_repo.update_by_id(paper.get("openalex_id"), {
                "needs_enrich": False,
            })

        logger.info("Enriched %s paper",paper.get("openalex_id",""))
        
        return enrichment_result

    except Exception:
        session.rollback()
        logger.exception("Enrichment failed")
        raise
    finally:
        session.close()


# Embed & store in Qdrant
def _store_qdrant(
    paper_id: str,
    title: str,
    abstract: str,
    payload: Dict,
    enrichment_result: EnrichmentResult | None = None
    ):
    logger.info("Embedding paper into Qdrant",)
    try:
        qdrant = QdrantDB()
        # embed vectors
        title_vectors = embed_title(title)
        abstract_vectors     = embed_abstract(abstract)
        contribution_vectors = embed_contribution(enrichment_result.contribution)

        # Upsert into Qdrant
        qdrant.upsert_paper(
            paper_id=str(paper_id),
            title_vector=title_vectors,
            abstract_vector=abstract_vectors,
            contribution_vector=contribution_vectors,
            payload=payload,
        )

        logger.info("Upserted paper into Qdrant")

    except Exception:
        logger.exception("Qdrant storage failed")
        raise
    


# Full pipeline orchestrator
def storage_service(pub_year: int = 2026, limit: int = 100, per_page: int=200):
    logger.info("Storage Started (year=%d, per_page=%d)", pub_year, limit)
    count =0
    # stream api data
    for paper in stream_data(pub_year=pub_year,limit=limit,per_page=per_page):
        # Store in postgres
        paper_id=_store_postgres(paper)
        # Enriching the data
        enrichment_result = _enrich(paper)
        # Store in qdrant
        title= paper.get("title")
        abstract= paper.get("abstract")
        payload={
            "contribution":enrichment_result.contribution,
            "year":paper.get("year"),
            "fields":paper.get("fields"),
            "open_access":paper.get("open_access")
        }
        _store_qdrant(paper_id,title,abstract,payload,enrichment_result)

        count+=1
    # Calculating and updating pagerank and citation velocity in postgres
    logger.info("Computing PageRank & citation velocity")
    update_global_pr()
    update_citation_velocity()
    logger.info("Ranking scores updated")
    logger.info("Storage complete")
    return {"ingested":count}

# Usage
if __name__ == "__main__":
    from db.postgres_db import init_db
    init_db()
    storage_service(pub_year=2020, per_page=10)