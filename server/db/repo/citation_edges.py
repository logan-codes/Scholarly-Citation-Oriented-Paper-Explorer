from typing import Optional
from sqlalchemy.orm import Session
from ..models.citation_edges import CitationEdge 


class CitationEdgeRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_citing_id(self, paper_id: str) -> Optional[CitationEdge]:
        return self.db.query(CitationEdge).filter(CitationEdge.citing_id == paper_id).first()
    
    def get_by_cited_id(self, paper_id: str) -> Optional[CitationEdge]:
        return self.db.query(CitationEdge).filter(CitationEdge.cited_id == paper_id).first()

    def get_all(self) -> list[CitationEdge]:
        return self.db.query(CitationEdge).all()

    def insert(self, citation_score: CitationEdge) -> CitationEdge:
        self.db.add(citation_score)
        self.db.commit()
        self.db.refresh(citation_score)
        return citation_score

    def update_by_paper_id(self, paper_id: str, updates: dict) -> Optional[CitationEdge]:
        record = self.get_by_paper_id(paper_id)
        if not record:
            return None
        for key, value in updates.items():
            setattr(record, key, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def upsert(self, citation_score: CitationEdge) -> CitationEdge:
        existing = self.get_by_paper_id(citation_score.paper_id)
        if existing:
            updates = {
                col: getattr(citation_score, col)
                for col in citation_score.__table__.columns.keys()
                if col != "paper_id"
            }
            return self.update_by_paper_id(citation_score.paper_id, updates)
        return self.insert(citation_score)

    def bulk_insert(self, records: list[CitationEdge]) -> None:
        self.db.add_all(records)
        self.db.commit()