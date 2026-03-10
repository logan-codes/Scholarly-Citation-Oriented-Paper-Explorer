from datetime import datetime
from sqlalchemy import Text, Float, TIMESTAMP, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from .papers import Base 

class AuthorScore(Base):
    __tablename__ = "author_scores"

    openalex_author_id: Mapped[str]         = mapped_column(Text, primary_key=True)
    author_name:        Mapped[str | None]  = mapped_column(Text, nullable=True)
    pr_score:           Mapped[float]       = mapped_column(Float, default=0)
    updated_at:         Mapped[datetime]    = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_author_pr", "pr_score", postgresql_ops={"pr_score": "float8_ops"}, postgresql_using="btree"),
    )