from core.logger import logger

from services.enrich_service import enrich_batch
from services.api_harvest_service import get_data
from services.pagerank_service import update_global_pr, update_citation_velocity

from db.repo.papers import PaperRepository
from db.repo.citation_edges import CitationEdgeRepository
from db.repo.author_scores import AuthorScoreRepository
from db.postgres_db import SessionLocal
from db.qdrant_db import QdrantDB
from db.models.citation_edges import CitationEdge
from db.models.author_scores import AuthorScore

from utils.embedding_util import embed_abstracts, embed_contributions, embed_titles
from utils.llm_util import get_groq_llm

# Store raw data in Postgres
def store_postgres(papers: list[dict]) -> list[str]:
    logger.info("Storing %d papers in Postgres", len(papers))
    stored_ids: list[str] = []

    session = SessionLocal()
    try:
        paper_repo = PaperRepository(session)
        edge_repo  = CitationEdgeRepository(session)
        author_repo = AuthorScoreRepository(session)

        for paper in papers:
            openalex_id = paper["openalex_id"]

            # Skip if already ingested 
            existing = paper_repo.get_by_oa_id(str(openalex_id))
            if existing:
                logger.debug("Skipping duplicate: %s", openalex_id)
                continue
            if paper.get("doi")!=None:
                # Insert paper 
                paper_row = paper_repo.insert({
                    "openalex_id":    openalex_id,
                    "doi":            paper.get("doi") or None,
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
                    # Only create edge if the referenced paper also exists
                    ref_paper = paper_repo.get_by_oa_id(ref_id)
                    if ref_paper:
                        edge = CitationEdge(
                            citing_id=paper_row.paper_id,
                            cited_id=ref_paper.paper_id,
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

            stored_ids.append(openalex_id)

        logger.info("Stored %d new papers", len(stored_ids))
    except Exception:
        session.rollback()
        logger.exception("✘ Postgres storage failed")
        raise
    finally:
        session.close()

    return stored_ids

# LLM Enrichment (tags + contributions)
def enrich():
    llm = get_groq_llm()

    session = SessionLocal()
    try:
        paper_repo = PaperRepository(session)
        papers_to_enrich = paper_repo.get_all_need_enrich()

        if not papers_to_enrich:
            logger.info("No papers need enrichment — skipping")
            return

        logger.info("Enriching %d papers", len(papers_to_enrich))

        # Build the batch input expected by enrich_batch
        batch_input = [
            {
                "openalex_id": p.openalex_id,
                "abstract":    p.abstract or "",
                "title":       p.title,
            }
            for p in papers_to_enrich
        ]

        enrichment_results = enrich_batch(llm=llm, papers=batch_input)

        # Write enrichment results back to Postgres
        for openalex_id, result in enrichment_results:
            paper_repo.update_by_id(openalex_id, {
                "needs_enrich": False,
            })

        fallback_count = sum(1 for _, r in enrichment_results if r.used_fallback)
        logger.info(
            "Enriched %d papers (%d used fallback)",
            len(enrichment_results), fallback_count,
        )

        return enrichment_results

    except Exception:
        session.rollback()
        logger.exception("Enrichment failed")
        raise
    finally:
        session.close()


# Embed & store in Qdrant
def store_qdrant(enrichment_results: list | None = None):
    session = SessionLocal()
    try:
        paper_repo = PaperRepository(session)
        qdrant = QdrantDB()

        # Determine which papers to embed
        if enrichment_results:
            oa_ids = [oa_id for oa_id, _ in enrichment_results]
            enrichment_map = {oa_id: res for oa_id, res in enrichment_results}
        else:
            # Fallback: embed everything that was recently ingested
            papers_db = paper_repo.get_all_need_enrich()
            oa_ids = [p.openalex_id for p in papers_db]
            enrichment_map = {}

        if not oa_ids:
            logger.info("No papers to embed — skipping")
            return

        logger.info("Embedding %d papers into Qdrant", len(oa_ids))

        # Collect texts for batch embedding
        titles        = []
        abstracts     = []
        contributions = []
        paper_rows    = []

        for oa_id in oa_ids:
            paper = paper_repo.get_by_oa_id(oa_id)
            if not paper:
                logger.warning("Paper %s not found in DB — skipping Qdrant upsert", oa_id)
                continue

            paper_rows.append(paper)
            titles.append(paper.title or "")
            abstracts.append(paper.abstract or "")

            # Get contribution from enrichment results (if available)
            enrich_res = enrichment_map.get(oa_id)
            if enrich_res and enrich_res.contribution:
                contributions.append(enrich_res.contribution)
            else:
                contributions.append(paper.abstract or paper.title or "")

        if not paper_rows:
            logger.info("No valid papers found — skipping")
            return

        # Batch embed
        title_vectors        = embed_titles(titles)
        abstract_vectors     = embed_abstracts(abstracts)
        contribution_vectors = embed_contributions(contributions)

        # Upsert into Qdrant
        for i, paper in enumerate(paper_rows):
            qdrant.upsert_paper(
                paper_id=str(paper.paper_id),
                title_vector=title_vectors[i],
                abstract_vector=abstract_vectors[i],
                contribution_vector=contribution_vectors[i],
                payload=paper,
            )

        logger.info("Upserted %d papers into Qdrant", len(paper_rows))

    except Exception:
        logger.exception("Qdrant storage failed")
        raise
    finally:
        session.close()


# Full pipeline orchestrator
def storage_service(pub_year: int = 2026, per_page: int = 50):
    logger.info("Storage Started (year=%d, per_page=%d)", pub_year, per_page)

    # Get api data
    papers = get_data(pub_year, per_page)
    logger.info("Fetched data from OpenAlex")
    if not papers:
        logger.warning("No papers returned — aborting pipeline")
        return

    # Storing in postgres
    store_postgres(papers)

    # Calculating and updating pagerank and citation velocity in postgres
    logger.info("Computing PageRank & citation velocity")
    update_global_pr()
    update_citation_velocity()
    logger.info("Ranking scores updated")

    # Enriching the data
    enrichment_results = enrich()

    # storing in qdrant
    store_qdrant(enrichment_results)

    logger.info("Storage complete")
    return papers

# Usage
if __name__ == "__main__":
    from db.postgres_db import init_db
    init_db()
    storage_service(pub_year=2020, per_page=10)