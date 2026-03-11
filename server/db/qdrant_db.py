from core.config import settings
from core.logger import logger

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    SearchParams,
    Prefetch,
    FusionQuery,
    FusionParams,
)

from typing import List, Dict, Any


TITLE_DIM = 384
ABSTRACT_DIM = 768
CONTRIBUTION_DIM = 768


class QdrantDB:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.create_collection()

    # Collection Setup
    def create_collection(self):
        self.client.recreate_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config={
                "title": VectorParams(size=TITLE_DIM, distance=Distance.COSINE),
                "abstract": VectorParams(size=ABSTRACT_DIM, distance=Distance.COSINE),
                "contribution": VectorParams(size=CONTRIBUTION_DIM, distance=Distance.COSINE),
            },
        )

    # Insert Paper
    def upsert_paper(
        self,
        paper_id: str,
        title_vector: List[float],
        abstract_vector: List[float],
        contribution_vector: List[float],
        payload: Dict[str, Any],
    ):

        point = PointStruct(
            id=paper_id,
            vector={
                "title": title_vector,
                "abstract": abstract_vector,
                "contribution": contribution_vector,
            },
            payload={
                "year":payload.year,
                "fields":payload.fields,
                "open access":payload.open_access 
            },
        )

        self.client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=[point],
        )

    def search(
        self,
        query_vectors: Dict[str, List[float]],
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        try:
            results = self.client.query_points(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vectors=self._build_rrf_query(query_vectors),
                limit=limit,
                with_payload=True,
            )
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload,
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def _build_rrf_query(
        self,
        query_vectors: Dict[str, List[float]],
    ) -> FusionQuery:
        return FusionQuery(
            fusion=FusionParams(fusion=2),
            prefetch=[
                Prefetch(
                    query=query_vectors.get("title", []),
                    using="title",
                    limit=50,
                ),
                Prefetch(
                    query=query_vectors.get("abstract", []),
                    using="abstract",
                    limit=50,
                ),
                Prefetch(
                    query=query_vectors.get("contribution", []),
                    using="contribution",
                    limit=50,
                ),
            ],
        )

    def search_with_filter(
        self,
        query_vectors: Dict[str, List[float]],
        filter_query: Dict[str, Any],
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        try:
            results = self.client.query_points(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vector=self._build_rrf_query(query_vectors),
                query_filter=filter_query,
                limit=limit,
                with_payload=True,
            )
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload,
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Vector search with filter failed: {e}")
            return []
