import pytest
from services.apiOrchestration import get_data

def test_get_data():
    res = get_data(2026, 5)
    assert isinstance(res, list)
    assert len(res) == 5
    if res:
        # Check that each item is a dict with expected keys
        expected_keys = ["openalex_id", "doi", "title", "abstract", "authors", "venue", "year", "fields", "citation_count", "counts_by_year", "referenced_works", "open_access", "updated_date"]
        for item in res:
            assert isinstance(item, dict)
            for key in expected_keys:
                assert key in item
    
