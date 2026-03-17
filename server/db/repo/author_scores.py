from typing import Optional
from sqlalchemy.orm import Session
from ..models.author_scores import AuthorScore 


class AuthorScoreRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_author_id(self, author_id: str) -> Optional[AuthorScore]:
        return self.db.query(AuthorScore).filter(AuthorScore.openalex_author_id == author_id).first()

    def get_all(self) -> list[AuthorScore]:
        return self.db.query(AuthorScore).all()

    def insert(self, author_score: AuthorScore) -> AuthorScore:
        self.db.add(author_score)
        self.db.commit()
        self.db.refresh(author_score)
        return author_score

    def update_by_author_id(self, author_id: str, updates: dict) -> Optional[AuthorScore]:
        record = self.get_by_author_id(author_id)
        if not record:
            return None
        for key, value in updates.items():
            setattr(record, key, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def upsert(self, author_score: AuthorScore) -> AuthorScore:
        existing = self.get_by_author_id(author_score.openalex_author_id)
        if existing:
            updates = {}

            for col in author_score.__table__.columns.keys():
                if col in ("author_id", "updated_at"):
                    continue

                value = getattr(author_score, col)

                if value is not None:
                    updates[col] = value
                else:
                    updates[col] = 0.0
            return self.update_by_author_id(author_score.openalex_author_id, updates)
        return self.insert(author_score)

    def bulk_insert(self, records: list[AuthorScore]) -> None:
        self.db.add_all(records)
        self.db.commit()