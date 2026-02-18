import pytest
from collections import defaultdict

@pytest.fixture
def sample_data():
    return {
        "query": "What is the capital of France?",
        "k": 5,
        "expanded_k": 30,
        "k_docs": 3,
        "retrieved_chunks": [],
        "documents": {}
    }
