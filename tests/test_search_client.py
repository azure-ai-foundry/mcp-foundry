
import pytest
from unittest.mock import patch, MagicMock

from mcp_foundry_knowledge import SearchClientDao


@pytest.fixture
def mock_dao():
    with patch("azure.search.documents.SearchClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        dao = SearchClientDao(index_name="test-index")
        dao.client = mock_client
        yield dao

def test_query_index_basic(mock_dao):
    mock_dao.client.search.return_value = [
        {"id": "1", "name": "Item One"},
        {"id": "2", "name": "Item Two"}
    ]

    results = mock_dao.query_index(search_text="item")

    assert len(results) == 2
    assert results[0]["id"] == "1"
    assert results[1]["name"] == "Item Two"

    mock_dao.client.search.assert_called_once_with(
        search_text="item",
        include_total_count=None,
        filter=None,
        order_by=None,
        select=None,
        skip=None,
        top=None
    )


def test_query_index_with_all_params(mock_dao):
    mock_dao.client.search.return_value = [
        {"id": "101", "title": "Test Doc"}
    ]

    results = mock_dao.query_index(
        search_text="test",
        query_filter="category eq 'books'",
        order_by=["title desc"],
        select=["title"],
        skip=10,
        top=5,
        include_total_count=True
    )

    assert results == [{"id": "101", "title": "Test Doc"}]

    mock_dao.client.search.assert_called_once_with(
        search_text="test",
        include_total_count=True,
        filter="category eq 'books'",
        order_by=["title desc"],
        select=["title"],
        skip=10,
        top=5
    )
