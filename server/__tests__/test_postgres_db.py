from dotenv import load_dotenv
load_dotenv()
import os

import uuid
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch

from db.models.papers import Paper, Base
from db.models.citation_edges import CitationEdge
from db.models.author_scores import AuthorScore

from db.repo.papers import PaperRepository
from db.repo.citation_edges import CitationEdgeRepository
from db.repo.author_scores import AuthorScoreRepository

DATABASE_URL = os.getenv("POSTGRES_URL")


# Session fixtures
@pytest.fixture(scope="session")
def engine():
    """Create engine and all tables once for the entire test session."""
    engine = create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def session(engine):
    """Each test gets a fresh session rolled back after the test — nothing persists."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    sess = Session()
    yield sess
    sess.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def paper_repo(session):
    repo = PaperRepository(db=session)
    with patch.object(session, "commit", side_effect=session.flush):
        yield repo


@pytest.fixture
def citation_edge_repo(session):
    repo = CitationEdgeRepository(db=session)
    with patch.object(session, "commit", side_effect=session.flush):
        yield repo


@pytest.fixture
def author_score_repo(session):
    repo = AuthorScoreRepository(db=session)
    with patch.object(session, "commit", side_effect=session.flush):
        yield repo


# Helpers
def make_paper(**kwargs) -> Paper:
    defaults = dict(
        openalex_id=f"W{uuid.uuid4().hex[:10]}",
        title="Test Paper",
        doi="2345678",
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


# PaperRepository
class TestPaperRepository:

    def test_insert_minimal_paper(self, paper_repo):
        paper = paper_repo.insert(make_paper())
        assert paper.paper_id is not None

    def test_insert_full_paper(self, paper_repo):
        paper = paper_repo.insert(make_paper(
            title="Attention Is All You Need",
            abstract="We propose a new simple network architecture...",
            doi="2345678",
            venue="NeurIPS",
            year=2017,
            fields=["Machine Learning", "NLP", "Transformers"],
            authors=[{"name": "Vaswani", "openalex_id": "A123", "institution": "Google"}],
            citation_count=90000,
            open_access=True,
        ))
        fetched = paper_repo.get_by_id(paper.paper_id)
        assert fetched.title       == "Attention Is All You Need"
        assert fetched.year        == 2017
        assert len(fetched.fields) == 3
        assert fetched.open_access is True

    def test_openalex_id_unique(self, paper_repo, session):
        openalex_id = f"W{uuid.uuid4().hex[:10]}"
        paper_repo.insert(make_paper(openalex_id=openalex_id))
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                paper_repo.insert(make_paper(openalex_id=openalex_id))

    def test_title_required(self, paper_repo, session):
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                paper_repo.insert(Paper(openalex_id=f"W{uuid.uuid4().hex[:10]}", title=None))

    def test_default_flags(self, paper_repo):
        paper = paper_repo.insert(make_paper())
        assert paper.needs_pr       is True
        assert paper.needs_enrich   is True
        assert paper.open_access    is False
        assert paper.citation_count == 0
        assert paper.source         == "openalex"

    def test_get_by_id_returns_correct_paper(self, paper_repo):
        inserted = paper_repo.insert(make_paper(title="Findable Paper"))
        fetched  = paper_repo.get_by_id(inserted.paper_id)
        assert fetched.paper_id == inserted.paper_id
        assert fetched.title    == "Findable Paper"

    def test_get_by_id_missing_returns_none(self, paper_repo):
        assert paper_repo.get_by_id(uuid.uuid4()) is None

    def test_update_by_id(self, paper_repo):
        paper   = paper_repo.insert(make_paper())
        updated = paper_repo.update_by_id(paper.paper_id, {"citation_count": 42})
        assert updated.citation_count == 42

    def test_update_nonexistent_returns_none(self, paper_repo):
        assert paper_repo.update_by_id(uuid.uuid4(), {"citation_count": 1}) is None

    def test_get_all_need_pr(self, paper_repo):
        paper_repo.insert(make_paper(needs_pr=True,doi="2345"))
        paper_repo.insert(make_paper(needs_pr=True,doi="256785"))
        paper_repo.insert(make_paper(needs_pr=False,doi="45678"))
        results = paper_repo.get_all_need_pr()
        assert len(results) >= 2
        assert all(p.needs_pr is True for p in results)

    def test_get_all_need_enrich(self, paper_repo):
        paper_repo.insert(make_paper(needs_enrich=True,doi="2345"))
        paper_repo.insert(make_paper(needs_enrich=False,doi="2345645"))
        results = paper_repo.get_all_need_enrich()
        assert len(results) >= 1
        assert all(p.needs_enrich is True for p in results)

    def test_search_vector_populated_by_trigger(self, paper_repo, session):
        paper = paper_repo.insert(make_paper(
            title="Deep Learning",
            abstract="Neural networks are powerful."
        ))
        session.refresh(paper)
        result = session.execute(
            text("SELECT search_vector FROM papers WHERE paper_id = :id"),
            {"id": str(paper.paper_id)}
        ).scalar()
        assert result is not None


# CitationEdge  (direct session — no repo yet, edge model only)
class TestCitationEdgeRepository:

    def _make_two_papers(self, paper_repo):
        p1 = paper_repo.insert(make_paper())
        p2 = paper_repo.insert(make_paper(doi="45678"))
        return p1, p2

    def test_insert_and_get_by_citing(self, paper_repo, citation_edge_repo):
        p1, p2 = self._make_two_papers(paper_repo)
        citation_edge_repo.insert(CitationEdge(citing_id=p1.paper_id, cited_id=p2.paper_id))
        results = citation_edge_repo.get_by_citing_id(p1.paper_id)
        assert results.cited_id == p2.paper_id

    def test_insert_and_get_by_cited(self, paper_repo, citation_edge_repo):
        p1, p2 = self._make_two_papers(paper_repo)
        citation_edge_repo.insert(CitationEdge(citing_id=p1.paper_id, cited_id=p2.paper_id))
        results = citation_edge_repo.get_by_cited_id(p2.paper_id)
        assert results.citing_id == p1.paper_id

    def test_get_missing_returns_empty(self, citation_edge_repo):
        assert citation_edge_repo.get_by_citing_id(str(uuid.uuid4())) == None

    def test_duplicate_edge_rejected(self, paper_repo, citation_edge_repo, session):
        p1, p2 = self._make_two_papers(paper_repo)
        citation_edge_repo.insert(CitationEdge(citing_id=p1.paper_id, cited_id=p2.paper_id))
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                citation_edge_repo.insert(CitationEdge(citing_id=p1.paper_id, cited_id=p2.paper_id))

    def test_relationship_traversal(self, paper_repo, citation_edge_repo, session):
        p1 = paper_repo.insert(make_paper(title="Citing Paper"))
        p2 = paper_repo.insert(make_paper(title="Cited Paper", doi="45678"))
        edge = citation_edge_repo.insert(CitationEdge(citing_id=p1.paper_id, cited_id=p2.paper_id))
        session.refresh(edge)
        assert edge.citing_paper.title == "Citing Paper"
        assert edge.cited_paper.title  == "Cited Paper"

    def test_bulk_insert(self, paper_repo, citation_edge_repo):
        papers = [paper_repo.insert(make_paper(doi=_)) for _ in range(4)]
        # fan-out: papers[0] cites papers[1], [2], [3]
        records = [CitationEdge(citing_id=papers[0].paper_id, cited_id=papers[i].paper_id) for i in range(1, 4)]
        citation_edge_repo.bulk_insert(records)
        assert len([citation_edge_repo.get_by_citing_id(papers[i].paper_id) for i in range(1,4)]) == 3

    def test_get_all(self, paper_repo, citation_edge_repo):
        p1, p2 = self._make_two_papers(paper_repo)
        citation_edge_repo.insert(CitationEdge(citing_id=p1.paper_id, cited_id=p2.paper_id))
        assert len(citation_edge_repo.get_all()) >= 1


# AuthorScoreRepository
class TestAuthorScoreRepository:

    def test_insert_and_get(self, author_score_repo):
        author_score_repo.insert(AuthorScore(openalex_author_id="A123", author_name="Alice", pr_score=0.95))
        fetched = author_score_repo.get_by_author_id("A123")
        assert fetched.author_name == "Alice"
        assert fetched.pr_score    == 0.95

    def test_get_missing_returns_none(self, author_score_repo):
        assert author_score_repo.get_by_author_id("NONEXISTENT") is None

    def test_primary_key_unique(self, author_score_repo, session):
        author_score_repo.insert(AuthorScore(openalex_author_id="A999", pr_score=0.1))
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                author_score_repo.insert(AuthorScore(openalex_author_id="A999", pr_score=0.2))

    def test_default_pr_score(self, author_score_repo):
        author_score_repo.insert(AuthorScore(openalex_author_id="A000"))
        fetched = author_score_repo.get_by_author_id("A000")
        assert fetched.pr_score == 0.0

    def test_update_by_author_id(self, author_score_repo):
        author_score_repo.insert(AuthorScore(openalex_author_id="A111", pr_score=0.1))
        updated = author_score_repo.update_by_author_id("A111", {"pr_score": 0.88})
        assert updated.pr_score == 0.88

    def test_update_nonexistent_returns_none(self, author_score_repo):
        assert author_score_repo.update_by_author_id("GHOST", {"pr_score": 1.0}) is None

    def test_upsert_inserts_when_missing(self, author_score_repo):
        result = author_score_repo.upsert(AuthorScore(openalex_author_id="A222", pr_score=0.5))
        assert result.openalex_author_id == "A222"

    def test_upsert_updates_when_exists(self, author_score_repo):
        author_score_repo.insert(AuthorScore(openalex_author_id="A333", pr_score=0.2))
        author_score_repo.upsert(AuthorScore(openalex_author_id="A333", pr_score=0.8))
        fetched = author_score_repo.get_by_author_id("A333")
        assert fetched.pr_score == 0.8

    def test_bulk_insert(self, author_score_repo):
        records = [AuthorScore(openalex_author_id=f"BULK{i}", pr_score=0.1 * i) for i in range(3)]
        author_score_repo.bulk_insert(records)
        assert len(author_score_repo.get_all()) >= 3

    def test_get_all(self, author_score_repo):
        author_score_repo.insert(AuthorScore(openalex_author_id="A444", pr_score=0.6))
        all_records = author_score_repo.get_all()
        assert len(all_records) >= 1