import pytest
from services.retrieval import rrf_score
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

@pytest.fixture
def get_embed_model():
    """Fixture to get the embedding model for testing."""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

@pytest.fixture
def sample_vector_db(get_embed_model):
    """ testing vector database with dummy data """
    # Create an temporary Chroma collection for testing
    collection = Chroma(collection_name="test_collection", embedding_function=get_embed_model, persist_directory=None)

    yield collection

class TestingChromadb:
    def test_chromadb_retrieval(self, sample_vector_db):
        """Test that ChromaDB retrieval returns expected results."""
        # Add some dummy documents
        sample_vector_db.add_documents(
            [
                Document(page_content="This is the first test document.", metadata={"id": "doc1"}),
                Document(page_content="This is the second test document.", metadata={"id": "doc2"}),
                Document(page_content="This is the third test document.", metadata={"id": "doc3"})
            ]
        )

        # Test retrieval
        results = sample_vector_db.similarity_search("test document", k=2)
        retrieved_ids = [doc.metadata["id"] for doc in results]
        assert set(retrieved_ids).intersection({"doc1", "doc2", "doc3"})
    
    def test_chromadb_ingestion(self, sample_vector_db):
        """Test that ChromaDB ingestion works correctly."""
        # Add a new document
        sample_vector_db.add_documents(
            [
                Document(page_content="This is the fourth test document.", metadata={"id": "doc4"}),
            ]
        )

        # Test retrieval of the new document
        results = sample_vector_db.similarity_search("fourth test document", k=1)
        assert len(results) == 1
        assert results[0].metadata["id"] == "doc4"
    
class TestRRF:
    def test_rrf_basic(self):
        """Test that RRF scores are computed correctly."""

        # Simulate retrieved documents for two different retrieval methods
        retrieved_docs_1 = ["doc1", "doc2", "doc3"]
        retrieved_docs_2 = ["doc2", "doc3", "doc4"]

        # Compute RRF scores
        rrf_scores = rrf_score([retrieved_docs_1, retrieved_docs_2], k=3)

        # doc2 and doc3 should have higher scores than doc1 and doc4
        assert rrf_scores["doc2"] > rrf_scores["doc1"]
        assert rrf_scores["doc3"] > rrf_scores["doc4"]