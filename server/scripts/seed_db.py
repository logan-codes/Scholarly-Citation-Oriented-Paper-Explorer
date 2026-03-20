import sys
import os
import time
import uuid
from collections import deque
from typing import List, Set, Dict

# Add parent directory to sys.path to allow importing from server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.postgres_db import SessionLocal
from db.repo.papers import PaperRepository
from db.repo.citation_edges import CitationEdgeRepository
from db.models.citation_edges import CitationEdge
from db.qdrant_db import QdrantDB
from services.api_harvest_service import fetch_single_work
from services.enrich_service import enrich_paper, GROQ_MODEL
from utils.embedding_util import embed_title, embed_abstract, embed_contribution
from core.logger import get_logger
from langchain_groq import ChatGroq
from core.config import settings

logger = get_logger("seed_db")

# Seed IDs (Attention, ResNet, BERT, GANs, ImageNet, GPT-3, Adam)
SEED_IDS = [
    "W2741809807", "W2755957008", "W2818903334", "W2049079997",
    "W2116016186", "W3010079919", "W2137119036"
]

TARGET_COUNT = 100

class Seeder:
    def __init__(self):
        self.session = SessionLocal()
        self.paper_repo = PaperRepository(self.session)
        self.edge_repo = CitationEdgeRepository(self.session)
        self.qdrant = QdrantDB()
        
        # Initialize LLM for enrichment
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            self.llm = ChatGroq(model=GROQ_MODEL, temperature=0.1, groq_api_key=api_key)
        else:
            logger.warning("GROQ_API_KEY not found. Enrichment will use extractive fallback.")
            self.llm = None

    def seed(self):
        queue = deque(SEED_IDS)
        processed_ids: Set[str] = set()
        count = 0

        # Pre-check existing papers in DB
        # Skip this for simplicity, our insert will handle existing via get_by_oa_id check

        logger.info(f"Starting seed process for {TARGET_COUNT} papers...")

        while queue and count < TARGET_COUNT:
            oa_id = queue.popleft()
            
            if oa_id in processed_ids:
                continue
            
            # Check if already in Postgres
            existing = self.paper_repo.get_by_oa_id(oa_id)
            if existing:
                logger.info(f"Paper {oa_id} already exists in DB. Skipping fetch.")
                # Still add its references to queue to continue snowball
                if existing.counts_by_year: # Hack: check if we have data
                    # We don't store referenced_works in the Paper model yet? 
                    # Let's check api_harvest_service parse_work output.
                    pass 
                processed_ids.add(oa_id)
                # count += 1 # We count it as processed
                continue

            logger.info(f"Fetching paper {oa_id}... ({count+1}/{TARGET_COUNT})")
            paper_data = fetch_single_work(oa_id)
            if not paper_data:
                continue

            # 1. Enrich (Tags & Contribution)
            logger.info(f"Enriching: {paper_data['title'][:60]}...")
            enrichment = enrich_paper(
                llm=self.llm,
                abstract=paper_data.get("abstract", ""),
                title=paper_data.get("title", ""),
                rate_limit_sleep=True if self.llm else False
            )
            
            paper_data["contribution"] = enrichment.contribution
            # Note: tags are currently not in our Paper model but could be useful for fields
            if enrichment.tags:
                paper_data["fields"] = list(set((paper_data["fields"] or []) + enrichment.tags))

            # 2. Generate Embeddings
            logger.info("Generating embeddings...")
            title_vec = embed_title(paper_data["title"])
            abstract_vec = embed_abstract(paper_data["abstract"] or "")
            contrib_vec = embed_contribution(paper_data["contribution"])

            # 3. Save to Postgres
            refs = paper_data.pop("referenced_works", [])
            paper_data.pop("updated_date", None)
            
            try:
                self.paper_repo.insert(paper_data)
                
                # 4. Save to Qdrant
                self.qdrant.upsert_paper(
                    paper_id=oa_id,
                    title_vector=title_vec,
                    abstract_vector=abstract_vec,
                    contribution_vector=contrib_vec,
                    payload={
                        "contribution": paper_data["contribution"],
                        "year": paper_data["year"],
                        "fields": paper_data["fields"],
                        "open_access": paper_data["open_access"]
                    }
                )

                # 5. Save Citation Edges & Add to Queue
                edges = []
                for ref_id in refs:
                    edges.append(CitationEdge(citing_id=oa_id, cited_id=ref_id))
                    if len(queue) < (TARGET_COUNT * 2): # Don't bloat the queue too much
                        queue.append(ref_id)
                
                if edges:
                    self.edge_repo.bulk_insert(edges)

                count += 1
                processed_ids.add(oa_id)
                logger.info(f"Successfully processed: {paper_data['title'][:60]}")

            except Exception as e:
                logger.error(f"Failed to process paper {oa_id}: {e}")
                self.session.rollback()

        logger.info(f"Seed process completed. Total papers added: {count}")

    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()

if __name__ == "__main__":
    seeder = Seeder()
    seeder.seed()
