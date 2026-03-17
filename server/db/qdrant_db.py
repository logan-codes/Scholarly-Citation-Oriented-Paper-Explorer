from core.config import settings
from core.logger import logger

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Prefetch,
    FusionQuery,
    Fusion
)


from typing import List, Dict, Any
import uuid


TITLE_DIM = 384
ABSTRACT_DIM = 768
CONTRIBUTION_DIM = 768


class QdrantDB:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)

    # Collection Setup
    def create_collection(self):
        self.client.create_collection(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            vectors_config={
                "title": VectorParams(size=TITLE_DIM, distance=Distance.COSINE),
                "abstract": VectorParams(size=ABSTRACT_DIM, distance=Distance.COSINE),
                "contribution": VectorParams(size=CONTRIBUTION_DIM, distance=Distance.COSINE),
            },
        )
    
    def delete_collection(self):
        self.client.delete_collection(collection_name=settings.QDRANT_COLLECTION_NAME)

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
            id= str(uuid.uuid5(uuid.NAMESPACE_DNS, paper_id)),
            vector={
                "title": title_vector,
                "abstract": abstract_vector,
                "contribution": contribution_vector,
            },
            payload={
                "paper id":paper_id,
                "contribution":payload["contribution"],
                "year":payload["year"],
                "fields":payload["fields"],
                "open access":payload["open_access"] 
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
                prefetch=self._build_prefetches(query_vectors),
                query=FusionQuery(fusion=Fusion.RRF),
                limit=limit,
                with_payload=True,
            )
            print(results)
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload,
                }
                for hit in results.points
            ]
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def _build_prefetches(
        self,
        query_vectors: Dict[str, List[float]],
    ):
        return [
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
            ]

    def search_with_filter(
        self,
        query_vectors: Dict[str, List[float]],
        filter_query: Dict[str, Any],
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        try:
            results = self.client.query_points(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query=self._build_rrf_query(query_vectors),
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
