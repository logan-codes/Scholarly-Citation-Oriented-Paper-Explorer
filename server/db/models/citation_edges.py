from sqlalchemy import Index
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .papers import Base 
from .papers import Paper
import uuid

class CitationEdge(Base):
    __tablename__ = "citation_edges"
    id:       Mapped[uuid.UUID]   = mapped_column(UUID(as_uuid=True),primary_key=True, default=uuid.uuid4)
    # Composite primary key
    citing_id: Mapped[str] = mapped_column(Text, nullable=False)
    cited_id: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (
        Index("idx_citing", "citing_id"),
        Index("idx_cited",  "cited_id"),
    )