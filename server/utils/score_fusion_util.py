from typing import List, Dict, Any, Optional
from collections import defaultdict
import numpy as np

RRF_K = 60


def normalize_min_max(scores: List[float]) -> List[float]:
    if not scores:
        return []
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [1.0] * len(scores)
    return [(s - min_score) / (max_score - min_score) for s in scores]


def normalize_rrf(scores: List[float], k: int = RRF_K) -> List[float]:
    if not scores:
        return []
    return [1.0 / (k + s) for s in scores]


def rrf_fusion(
    results_by_source: Dict[str, List[Dict[str, Any]]],
    k: int = RRF_K,
) -> List[tuple[str, float]]:
    rrf_scores: Dict[str, float] = defaultdict(float)

    for source, results in results_by_source.items():
        for rank, item in enumerate(results, start=1):
            doc_id = str(item["id"])
            rrf_scores[doc_id] += 1.0 / (k + rank)

    sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_docs


def weighted_fusion(
    results_by_source: Dict[str, List[Dict[str, Any]]],
    weights: Dict[str, float],
) -> List[tuple[str, float]]:
    combined_scores: Dict[str, float] = defaultdict(float)

    source_scores: Dict[str, Dict[str, float]] = {}
    max_scores: Dict[str, float] = {}

    for source, results in results_by_source.items():
        if not results:
            continue
        scores = [r.get("score", 1.0) for r in results]
        source_scores[source] = {str(r["id"]): r.get("score", 1.0) for r in results}
        max_scores[source] = max(scores) if scores else 1.0

    all_doc_ids = set()
    for scores in source_scores.values():
        all_doc_ids.update(scores.keys())

    for doc_id in all_doc_ids:
        for source, scores in source_scores.items():
            if doc_id in scores:
                weight = weights.get(source, 1.0)
                normalized = scores[doc_id] / max_scores[source] if max_scores[source] else 0
                combined_scores[doc_id] += weight * normalized

    sorted_docs = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_docs


def standardize_scores(scores: List[float], target_max: float = 100.0) -> List[float]:
    if not scores:
        return []
    max_score = max(scores)
    if max_score <= 0:
        return [0.0] * len(scores)
    return [(s / max_score) * target_max for s in scores]


def fuse_results(
    vector_results: List[Dict[str, Any]],
    keyword_results: List[Dict[str, Any]],
    pr_scores: Dict[str, float],
    velocity_scores: Dict[str, float],
    vector_weight: float = 0.4,
    keyword_weight: float = 0.3,
    pr_weight: float = 0.2,
    velocity_weight: float = 0.1,
) -> List[Dict[str, Any]]:

    weights = {
        "vector": vector_weight,
        "keyword": keyword_weight,
        "pr": pr_weight,
        "velocity": velocity_weight,
    }

    # Collect all document ids
    vector_ids = [str(r["payload"]["paper id"]) for r in vector_results]
    keyword_ids = [str(r["id"]) for r in keyword_results]
    all_doc_ids = list(set(vector_ids) | set(keyword_ids) | set(pr_scores.keys()) | set(velocity_scores.keys()))

    if not all_doc_ids:
        return []

    # Prepare score arrays for standardization
    vector_raw = [next((r.get("score", 0.0) for r in vector_results if str(r["payload"]["paper id"]) == doc_id), 0.0) for doc_id in all_doc_ids]
    keyword_raw = [next((r.get("score", 0.0) for r in keyword_results if str(r["id"]) == doc_id), 0.0) for doc_id in all_doc_ids]
    pr_raw = [pr_scores.get(doc_id, 0.0) for doc_id in all_doc_ids]
    velocity_raw = [velocity_scores.get(doc_id, 0.0) for doc_id in all_doc_ids]

    # Standardize to 0-100
    vector_std = standardize_scores(vector_raw)
    keyword_std = standardize_scores(keyword_raw)
    pr_std = standardize_scores(pr_raw)
    velocity_std = standardize_scores(velocity_raw)

    final_results = []
    for i, doc_id in enumerate(all_doc_ids):
        v_s = vector_std[i]
        k_s = keyword_std[i]
        p_s = pr_std[i]
        vel_s = velocity_std[i]

        combined_score = (
            weights["vector"] * v_s +
            weights["keyword"] * k_s +
            weights["pr"] * p_s +
            weights["velocity"] * vel_s
        )

        final_results.append({
            "id": doc_id,
            "score": round(combined_score, 2),
            "relevancy": round(v_s, 2),
            "BM25": round(k_s, 2),
            "pr_score": round(p_s, 2),
            "velocity_score": round(vel_s, 2),
        })

    return sorted(final_results, key=lambda x: x["score"], reverse=True)