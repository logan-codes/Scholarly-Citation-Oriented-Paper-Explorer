from typing import Optional
from sqlalchemy.orm import Session
from ..models.citation_edges import CitationEdge 


class CitationEdgeRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_citing_id(self, openalex_id: str) -> Optional[CitationEdge]:
        return self.db.query(CitationEdge).filter(CitationEdge.citing_id == openalex_id).first()
    
    def get_by_cited_id(self, openalex_id: str) -> Optional[CitationEdge]:
        return self.db.query(CitationEdge).filter(CitationEdge.cited_id == openalex_id).first()

    def get_all(self) -> list[CitationEdge]:
        return self.db.query(CitationEdge).all()

    def insert(self, citation_edge: CitationEdge) -> CitationEdge:
        self.db.add(citation_edge)
        self.db.commit()
        self.db.refresh(citation_edge)
        return citation_edge

    def update_by_citing_id(self, paper_id: str, updates: dict) -> Optional[CitationEdge]:
        record = self.get_by_citing_id(paper_id)
        if not record:
            return None
        for key, value in updates.items():
            setattr(record, key, value)
        self.db.commit()
        self.db.refresh(record)
        return record
    
    def update_by_cited_id(self, paper_id: str, updates: dict) -> Optional[CitationEdge]:
        record = self.get_by_cited_id(paper_id)
        if not record:
            return None
        for key, value in updates.items():
            setattr(record, key, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def upsert_by_citing_id(self, citation_score: CitationEdge) -> CitationEdge:
        existing = self.get_by_citing_id(citation_score.citing_id)
        if existing:
            updates = {
                col: getattr(citation_score, col)
                for col in citation_score.__table__.columns.keys()
                if col not in ("citing_id", "id")
            }
            return self.update_by_citing_id(citation_score.citing_id, updates)
        return self.insert(citation_score)

    def upsert_by_cited_id(self, citation_score: CitationEdge) -> CitationEdge:
        existing = self.get_by_cited_id(citation_score.cited_id)
        if existing:
            updates = {
                col: getattr(citation_score, col)
                for col in citation_score.__table__.columns.keys()
                if col not in ("cited_id", "id")
            }
            return self.update_by_cited_id(citation_score.cited_id, updates)
        return self.insert(citation_score)

    def bulk_insert(self, records: list[CitationEdge]) -> None:
        self.db.add_all(records)
        self.db.commit()