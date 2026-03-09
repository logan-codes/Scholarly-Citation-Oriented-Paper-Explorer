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

    cn.graph.add_node("paper_A")
    cn.graph.add_node("paper_B")
    cn.graph.add_node("paper_C")
    cn.graph.add_edge("paper_A", "paper_B")  # A cites B
    cn.graph.add_edge("paper_A", "paper_C")  # A cites C
    cn.graph.add_edge("paper_B", "paper_C")  # B cites C

    return cn

class TestCitationNetwork:
    def test_empty_network(self, empty_citation_network):
        """Test that an empty citation network has no papers or citations."""
        cn = empty_citation_network
        assert len(cn.graph) == 0
        assert cn.pagerank_based_ranking("paper_C", top_k=3) == []

    def test_small_network(self, small_citation_network):
        """Test that a small citation network computes PageRank scores correctly."""
        cn = small_citation_network
        scores = cn.pagerank_based_ranking("paper_C", top_k=3)

        # paper_C should have the highest score since it's cited by both A and B
        assert scores[0][0] == "paper_C"

    def test_save_and_load(self, small_citation_network, tmp_path):
        """Test that saving and loading the citation network works correctly."""
        cn = small_citation_network
        file_path = tmp_path / "citation_network.csv"
        cn.save_to_file(file_path)

        loaded_cn = CitationNetwork.load_from_file(file_path)
        assert set(cn.graph.nodes) == set(loaded_cn.graph.nodes)
        assert set(cn.graph.edges) == set(loaded_cn.graph.edges)

class TestAddPaperAndCitation:
    def test_add_paper(self, empty_citation_network):
        """Test adding a paper to the citation network."""
        cn = empty_citation_network
        cn.graph.add_node("paper_X")
        assert "paper_X" in cn.graph.nodes

    def test_add_citation(self, empty_citation_network):
        """Test adding a citation between two papers."""
        cn = empty_citation_network
        cn.graph.add_edge("paper_Y", "paper_Z")

        assert set(cn.graph.successors("paper_Y")) == {"paper_Z"}
        assert set(cn.graph.predecessors("paper_Z")) == {"paper_Y"}

class TestGraphQueries:
    def test_most_cited_papers(self, small_citation_network):
        """Test retrieving the most cited papers in the network."""
        cn = small_citation_network
        most_cited = cn.pagerank_based_ranking("paper_C", top_k=1)
        assert most_cited[0][0] == "paper_C"

