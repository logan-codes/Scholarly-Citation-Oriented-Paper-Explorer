import pytest
from services.citationNetwork import CitationNetwork

@pytest.fixture
def empty_citation_network():
    """Blank citation network for testing basic functionality."""
    return CitationNetwork()

@pytest.fixture
def small_citation_network():
    """Small citation network with a few papers and citations."""
    cn = CitationNetwork()

    cn.build_from_pdfs(
        pdf_files=[],
        paper_metadata={
            "paper_A": {
                "year": 2023,
                "references": ["paper_B", "paper_C"],
            },
            "paper_B": {
                "year": 2019,
                "references": ["paper_C"],
            },
            "paper_C": {
                "year": 2015,
                "references": [],
            },
        },
    )

    return cn

class TestCitationNetwork:
    def test_empty_network(self, empty_citation_network):
        """Test that an empty citation network has no papers or citations."""
        cn = empty_citation_network
        assert len(cn.graph) == 0
        assert cn.weighted_pagerank() == {}

    def test_small_network(self, small_citation_network):
        """Test that a small citation network computes PageRank scores correctly."""
        cn = small_citation_network
        scores = cn.weighted_pagerank()

        # paper_C should have the highest score since it's cited by both A and B
        assert scores["paper_C"] > scores["paper_B"] > scores["paper_A"]

class TestAddPaperAndCitation:
    def test_add_paper(self, empty_citation_network):
        """Test adding a paper to the citation network."""
        cn = empty_citation_network
        cn.add_paper("paper_X", year=2020)
        assert "paper_X" in cn.graph
        assert cn.paper_years["paper_X"] == 2020

    def test_add_citation(self, empty_citation_network):
        """Test adding a citation between two papers."""
        cn = empty_citation_network
        cn.add_paper("paper_Y")
        cn.add_paper("paper_Z")
        cn.add_citation("paper_Y", "paper_Z")

        assert set(cn.get_citations("paper_Y")) == {"paper_Z"}
        assert set(cn.get_cited_by("paper_Z")) == {"paper_Y"}

class TestGraphQueries:
    def test_all_papers(self, small_citation_network):
        """Test retrieving all papers in the citation network."""
        cn = small_citation_network
        papers = cn.get_all_papers()
        assert set(papers) == {"paper_A", "paper_B", "paper_C"}

    def test_get_citations(self, small_citation_network):
        """Test retrieving the list of papers cited by a given paper."""
        cn = small_citation_network
        citations = cn.get_citations("paper_A")
        assert set(citations) == {"paper_B", "paper_C"}

    def test_get_cited_by(self, small_citation_network):
        """Test retrieving the list of papers that cite a given paper."""
        cn = small_citation_network
        cited_by = cn.get_cited_by("paper_C")
        assert set(cited_by) == {"paper_A", "paper_B"}

    def test_citation_count(self, small_citation_network):
        """Test counting the number of citations for a given paper."""
        cn = small_citation_network
        count = cn.get_citation_count("paper_C")
        assert count == 2
    
    def test_most_cited_papers(self, small_citation_network):
        """Test retrieving the most cited papers in the network."""
        cn = small_citation_network
        most_cited = cn.get_most_cited_papers(n=1)
        assert most_cited == [("paper_C", 2)]

class TestWeightedPageRank:
    def test_weighted_pagerank(self, small_citation_network):
        """Test that weighted PageRank scores are computed correctly."""
        cn = small_citation_network
        scores = cn.weighted_pagerank()

        # paper_C should have the highest score since it's cited by both A and B
        assert scores["paper_C"] > scores["paper_B"] > scores["paper_A"]

    def test_returns_score_for_all_papers(self, small_citation_network):
        """Test that PageRank returns a score for all papers in the network."""
        cn = small_citation_network
        scores = cn.weighted_pagerank()
        assert set(scores.keys()) == {"paper_A", "paper_B", "paper_C"}

    def test_most_cited_has_highest_score(self, small_citation_network):
        """Test that the most cited paper has the highest PageRank score."""
        cn = small_citation_network
        scores = cn.weighted_pagerank()
        most_cited = cn.get_most_cited_papers(n=1)[0][0]
        highest_score = max(scores.values())
        assert scores[most_cited] == highest_score

    def test_self_citation_penalty(self, small_citation_network):
        """Test that self-citations are penalized in the PageRank score."""
        cn = small_citation_network
        cn.add_citation("paper_A", "paper_A")  # Add a self-citation
        scores = cn.weighted_pagerank()
        assert scores["paper_A"] < scores["paper_B"] < scores["paper_C"]

    def test_scores_sum_to_one(self, small_citation_network):
        """Test that the PageRank scores sum to 1."""
        cn = small_citation_network
        scores = cn.weighted_pagerank()
        total_score = sum(scores.values())
        assert abs(total_score - 1.0) < 1e-6

    def test_empty_network_pagerank(self, empty_citation_network):
        """Test that PageRank on an empty network returns an empty score dict."""
        cn = empty_citation_network
        scores = cn.weighted_pagerank()
        assert scores == {}
    
