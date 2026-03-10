from dotenv import load_dotenv
load_dotenv()
import os

import uuid
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from db.models.papers import Paper, Base
from db.models.citation_edges import CitationEdge
from db.models.author_scores import AuthorScore

DATABASE_URL = os.getenv("POSTGRES_URL")

# Fixtures
@pytest.fixture(scope="session")
def engine():
    """Create engine and all tables once for the entire test session."""
    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)   # clean up after all tests finish


@pytest.fixture(scope="function")
def session(engine):
    """Each test gets a fresh session that is rolled back after the test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    sess = Session()

    yield sess

    sess.close()
    transaction.rollback()   # nothing persists between tests
    connection.close()

@pytest.fixture(scope="function")
def session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    sess = Session()

    yield sess

    sess.close()
    transaction.rollback()
    connection.close()

# Helpers
def make_paper(**kwargs) -> Paper:
    defaults = dict(
        openalex_id=f"W{uuid.uuid4().hex[:10]}",
        title="Test Paper",
        doi=None,
    )
    defaults.update(kwargs)
    return Paper(**defaults)


# Connection
class TestConnection:
    def test_db_is_reachable(self, engine):
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_all_tables_exist(self, engine):
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "papers"         in tables
        assert "citation_edges" in tables
        assert "author_scores"  in tables


# Paper CRUD
class TestPaper:
    def test_insert_minimal_paper(self, session):
        paper = make_paper()
        session.add(paper)
        session.flush()
        assert paper.paper_id is not None

    def test_insert_full_paper(self, session):
        paper = make_paper(
            title="Attention Is All You Need",
            abstract="We propose a new simple network architecture...",
            venue="NeurIPS",
            venue_tier="A*",
            year=2017,
            fields=["Machine Learning", "NLP", "Transformers"],
            authors=[{"name": "Vaswani", "openalex_id": "A123", "institution": "Google"}],
            citation_count=90000,
            open_access=True,
        )
        session.add(paper)
        session.flush()
        fetched = session.get(Paper, paper.paper_id)
        assert fetched.title      == "Attention Is All You Need"
        assert fetched.venue_tier == "A*"
        assert fetched.year       == 2017
        assert len(fetched.fields) == 3
        assert fetched.open_access is True

    def test_openalex_id_unique(self, session):
        from sqlalchemy.exc import IntegrityError
        openalex_id = f"W{uuid.uuid4().hex[:10]}"
        session.add(make_paper(openalex_id=openalex_id))
        session.flush()
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                session.add(make_paper(openalex_id=openalex_id))
                session.flush()

    def test_title_required(self, session):
        from sqlalchemy.exc import IntegrityError
        paper = Paper(openalex_id=f"W{uuid.uuid4().hex[:10]}", title=None)
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                session.add(paper)
                session.flush()

    def test_default_flags(self, session):
        paper = make_paper()
        session.add(paper)
        session.flush()
        assert paper.needs_pr      is True
        assert paper.is_enriched   is False
        assert paper.open_access   is False
        assert paper.citation_count == 0
        assert paper.source        == "openalex"

    def test_update_paper(self, session):
        paper = make_paper()
        session.add(paper)
        session.flush()
        paper.citation_count = 42
        session.flush()
        fetched = session.get(Paper, paper.paper_id)
        assert fetched.citation_count == 42

    def test_search_vector_populated_by_trigger(self, session):
        paper = make_paper(title="Deep Learning", abstract="Neural networks are powerful.")
        session.add(paper)
        session.flush()
        session.refresh(paper)
        # tsvector trigger should have populated search_vector
        result = session.execute(
            text("SELECT search_vector FROM papers WHERE paper_id = :id"),
            {"id": str(paper.paper_id)}
        ).scalar()
        assert result is not None


# CitationEdge
class TestCitationEdge:
    def test_insert_edge(self, session):
        p1 = make_paper(openalex_id=f"W{uuid.uuid4().hex[:10]}")
        p2 = make_paper(openalex_id=f"W{uuid.uuid4().hex[:10]}")
        session.add_all([p1, p2])
        session.flush()

        edge = CitationEdge(citing_id=p1.paper_id, cited_id=p2.paper_id)
        session.add(edge)
        session.flush()
        assert edge.citing_id == p1.paper_id
        assert edge.cited_id  == p2.paper_id

    def test_duplicate_edge_rejected(self, session):
        from sqlalchemy.exc import IntegrityError
        p1 = make_paper(openalex_id=f"W{uuid.uuid4().hex[:10]}")
        p2 = make_paper(openalex_id=f"W{uuid.uuid4().hex[:10]}")
        session.add_all([p1, p2])
        session.flush()

        session.add(CitationEdge(citing_id=p1.paper_id, cited_id=p2.paper_id))
        session.flush()
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                session.add(CitationEdge(citing_id=p1.paper_id, cited_id=p2.paper_id))
                session.flush()

    def test_relationship_traversal(self, session):
        p1 = make_paper(openalex_id=f"W{uuid.uuid4().hex[:10]}", title="Citing Paper")
        p2 = make_paper(openalex_id=f"W{uuid.uuid4().hex[:10]}", title="Cited Paper")
        session.add_all([p1, p2])
        session.flush()

        edge = CitationEdge(citing_id=p1.paper_id, cited_id=p2.paper_id)
        session.add(edge)
        session.flush()
        session.refresh(edge)

        assert edge.citing_paper.title == "Citing Paper"
        assert edge.cited_paper.title  == "Cited Paper"


# AuthorScore
class TestAuthorScore:
    def test_insert_author(self, session):
        author = AuthorScore(openalex_author_id="A123", author_name="Alice", pr_score=0.95)
        session.add(author)
        session.flush()
        fetched = session.get(AuthorScore, "A123")
        assert fetched.author_name == "Alice"
        assert fetched.pr_score    == 0.95

    def test_primary_key_unique(self, session):
        from sqlalchemy.exc import IntegrityError
        session.add(AuthorScore(openalex_author_id="A999", pr_score=0.1))
        session.flush()
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                session.add(AuthorScore(openalex_author_id="A999", pr_score=0.2))
                session.flush()

    def test_default_pr_score(self, session):
        author = AuthorScore(openalex_author_id="A000")
        session.add(author)
        session.flush()
        assert author.pr_score == 0.0