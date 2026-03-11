import uuid
from datetime import datetime
from sqlalchemy import Text, Integer, Float, Boolean, CHAR, ARRAY, TIMESTAMP, Index, func, text, DDL, event
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

class Base(DeclarativeBase):
    pass

class Paper(Base):
    __tablename__ = "papers"

    # Identity
    paper_id:       Mapped[uuid.UUID]   = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    openalex_id:    Mapped[str]         = mapped_column(Text, unique=True, nullable=False)
    doi:            Mapped[str | None]  = mapped_column(Text, unique=True, nullable=True)

    # Core metadata
    title:          Mapped[str]         = mapped_column(Text, nullable=False)
    abstract:       Mapped[str | None]  = mapped_column(Text, nullable=True)
    venue:          Mapped[str | None]  = mapped_column(Text, nullable=True)
    year:           Mapped[int | None]  = mapped_column(Integer, nullable=True)
    fields:         Mapped[list | None] = mapped_column(ARRAY(Text), nullable=True)

    # Authors
    authors:        Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Citation signals
    citation_count: Mapped[int]         = mapped_column(Integer, default=0)
    counts_by_year: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Computed ranking signals
    pr_score:       Mapped[float]       = mapped_column(Float, default=0)
    velocity_score: Mapped[float]       = mapped_column(Float, default=0)

    # Access flags
    open_access:    Mapped[bool]        = mapped_column(Boolean, default=False)

    # Pipeline flags
    needs_pr:       Mapped[bool]        = mapped_column(Boolean, default=True)
    needs_enrich:    Mapped[bool]        = mapped_column(Boolean, default=True)

    # Provenance
    source:         Mapped[str]         = mapped_column(Text, default="openalex")
    ingested_at:    Mapped[datetime]    = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at:     Mapped[datetime]    = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # BM25 — trigger-managed, never written by ORM
    search_vector:  Mapped[None]        = mapped_column(TSVECTOR, nullable=True)

    __table_args__ = (
        Index("idx_year",           "year"),
        Index("idx_fields",         "fields",           postgresql_using="gin"),
        Index("idx_search_vector",  "search_vector",    postgresql_using="gin"),
        Index("idx_needs_pr",       "needs_pr",         postgresql_where=text("needs_pr = true")),
    )

# Trigger attached after table creation — __table_args__ doesn't support triggers
event.listen(
    Paper.__table__,
    "after_create",
    DDL("""
        CREATE TRIGGER tsvector_update
        BEFORE INSERT OR UPDATE ON papers
        FOR EACH ROW EXECUTE FUNCTION
        tsvector_update_trigger(
            search_vector, 'pg_catalog.english', title, abstract
        )
    """)
)