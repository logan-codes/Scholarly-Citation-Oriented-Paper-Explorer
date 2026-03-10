import uuid
from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .papers import Base 
from .papers import Paper

class CitationEdge(Base):
    __tablename__ = "citation_edges"

    # Composite primary key
    citing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.paper_id"), primary_key=True)
    cited_id:  Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.paper_id"), primary_key=True)

    # Relationships (optional but useful for ORM traversal)
    citing_paper: Mapped["Paper"] = relationship("Paper", foreign_keys=[citing_id])
    cited_paper:  Mapped["Paper"] = relationship("Paper", foreign_keys=[cited_id])

    __table_args__ = (
        Index("idx_citing", "citing_id"),
        Index("idx_cited",  "cited_id"),
    )