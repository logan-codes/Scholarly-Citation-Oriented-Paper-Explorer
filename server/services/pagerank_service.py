import igraph as ig
from datetime import datetime
from typing import List

from core.logger import logger
from db.repo.citation_edges import CitationEdgeRepository
from db.repo.papers import PaperRepository
from db.postgres_db import SessionLocal

# Shared helpers
def _build_citation_graph():
    session = SessionLocal()
    try:
        cer = CitationEdgeRepository(session)
        raw_data = cer.get_all()
    finally:
        session.close()

    if not raw_data:
        logger.warning("No citation edges found — skipping graph build")
        return [], None

    node_set = set()
    for edge in raw_data:
        node_set.add(edge.citing_id)
        node_set.add(edge.cited_id)

    node_list = list(node_set)
    node_to_idx = {uid: idx for idx, uid in enumerate(node_list)}

    edges = [(node_to_idx[e.citing_id], node_to_idx[e.cited_id]) for e in raw_data]
    graph = ig.Graph(n=len(node_list), edges=edges, directed=True)

    return node_list, graph


# PageRank
def calculate_global_pr() -> list[list]:
    """Compute PageRank scores for every paper in the citation graph."""
    node_list, graph = _build_citation_graph()
    if graph is None:
        return []

    pr_scores = graph.pagerank(damping=0.85)

    return [[node_list[idx], score] for idx, score in enumerate(pr_scores)]


def update_global_pr():
    """Calculate PageRank and persist scores to Postgres."""
    pr_data = calculate_global_pr()
    if not pr_data:
        logger.info("No PageRank data to update")
        return

    session = SessionLocal()
    try:
        pr_repo = PaperRepository(session)
        for paper_id, score in pr_data:
            pr_repo.update_pr_by_id(paper_id, score)
        logger.info("Updated PageRank for %d papers", len(pr_data))
    except Exception:
        session.rollback()
        logger.exception("Failed to update PageRank scores")
        raise
    finally:
        session.close()


# Citation Velocity
def _weighted_slope(yearly_counts: list[dict], decay: float = 0.7) -> float:
    if not yearly_counts or len(yearly_counts) < 2:
        return 0.0

    # Sort ascending by year
    sorted_counts = sorted(yearly_counts, key=lambda d: d["year"])
    max_year = sorted_counts[-1]["year"]

    # Build weighted sums for slope = (Σw·x·y − Σw·x·Σw·y / Σw) / (Σw·x² − (Σw·x)² / Σw)
    sw = sx = sy = sxy = sxx = 0.0

    for entry in sorted_counts:
        year = entry["year"]
        count = entry.get("cited_by_count", 0)
        age = max_year - year          # 0 for most recent year
        w = decay ** age               # most recent year gets weight 1.0

        sw  += w
        sx  += w * year
        sy  += w * count
        sxy += w * year * count
        sxx += w * year * year

    denom = sw * sxx - sx * sx
    if abs(denom) < 1e-12:
        return 0.0

    slope = (sw * sxy - sx * sy) / denom
    return round(slope, 6)


def calculate_citation_velocity() -> list[list]:
    session = SessionLocal()
    try:
        paper_repo = PaperRepository(session)
        papers = paper_repo.get_all_need_pr()  # papers that still need ranking updates

        results = []
        for paper in papers:
            counts = paper.counts_by_year
            # counts_by_year is JSONB — may be None, a list, or empty
            if not counts or not isinstance(counts, list):
                velocity = 0.0
            else:
                velocity = _weighted_slope(counts)

            results.append([paper.paper_id, velocity])

        logger.info("Calculated citation velocity for %d papers", len(results))
        return results

    finally:
        session.close()


def update_citation_velocity():
    cv_data = calculate_citation_velocity()
    if not cv_data:
        logger.info("No citation velocity data to update")
        return

    session = SessionLocal()
    try:
        paper_repo = PaperRepository(session)
        for paper_id, velocity in cv_data:
            paper_repo.update_velocity_by_id(paper_id, velocity)
        logger.info("Updated citation velocity for %d papers", len(cv_data))
    except Exception:
        session.rollback()
        logger.exception("Failed to update citation velocity scores")
        raise
    finally:
        session.close()
