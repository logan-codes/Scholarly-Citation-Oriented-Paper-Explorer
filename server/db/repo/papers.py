from typing import Optional
from sqlalchemy.orm import Session
from ..models.papers import Paper  

class PaperRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all_need_pr(self) -> list[Paper]:
        return self.db.query(Paper).filter(Paper.needs_pr == True).all()

    def get_all_need_enrich(self) -> list[Paper]:
        return self.db.query(Paper).filter(Paper.needs_enrich == True).all()

    def get_by_id(self, paper_id: str) -> Optional[Paper]:
        return self.db.query(Paper).filter(Paper.paper_id == paper_id).first()

    def insert(self, paper: Paper) -> Paper:
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