from typing import Optional, List, Dict, Any
from core.logger import logger
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..models.papers import Paper  

class PaperRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all_need_pr(self) -> list[Paper]:
        return self.db.query(Paper).filter(Paper.needs_pr == True).all()

    def get_all_need_enrich(self) -> list[Paper]:
        return self.db.query(Paper).filter(Paper.needs_enrich == True).all()

    def get_by_id(self, paper_id: str) -> Optional[Paper]:
        return self.db.query(Paper).filter(Paper.openalex_id == paper_id).first()

    def insert(self, paper_data: dict) -> Paper:
        paper = Paper(**paper_data)

        self.db.add(paper)
        self.db.commit()
        self.db.refresh(paper)
        return paper

    def update_by_id(self, paper_id: str, updates: dict) -> Optional[Paper]:
        paper = self.get_by_id(paper_id)
        if not paper:
            return None
        for key, value in updates.items():
            setattr(paper, key, value)
        self.db.commit()
        self.db.refresh(paper)
        return paper
    
    def update_pr_by_id(self, paper_id: str, pr: float) -> Optional[Paper]:
        paper = self.get_by_id(paper_id)
        if not paper:
            return None
        setattr(paper, "pr_score", pr)
        setattr(paper, "needs_pr", False)
        self.db.commit()
        self.db.refresh(paper)
        return paper    

    def update_velocity_by_id(self, paper_id: str, cv: float) -> Optional[Paper]:
        paper = self.get_by_id(paper_id)
        if not paper:
            return None
        setattr(paper, "velocity_score", cv)
        self.db.commit()
        self.db.refresh(paper)
        return paper

    def search_papers_bm25(
        self,
        query: str,
        paper_ids: List[str] | None = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:

        try:
            ts_query = func.plainto_tsquery("english", query)

            rank = func.ts_rank(
                Paper.search_vector,
                ts_query
            ).label("bm25_score")

            stmt = (
                select(Paper.paper_id, rank)
                .where(Paper.search_vector.op("@@")(ts_query))
            )

            if paper_ids:
                stmt = stmt.where(Paper.paper_id.in_(paper_ids))

            stmt = stmt.order_by(rank.desc()).limit(limit)

            result = self.db.execute(stmt)

            return [
                {"id": row.paper_id, "score": row.bm25_score}
                for row in result
            ]

        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []