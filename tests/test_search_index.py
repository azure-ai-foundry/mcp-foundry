
from unittest.mock import patch, MagicMock
import pytest

from mcp_foundry_knowledge import SearchIndexDao


@pytest.fixture
def mock_dao():
    with patch("azure.search.documents.indexes.SearchIndexClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        dao = SearchIndexDao()
        dao.client = mock_client
        yield dao


def test_retrieve_index_names(mock_dao):
    mock_dao.client.list_index_names.return_value = ["index1", "index2"]

    result = mock_dao.retrieve_index_names()

    assert result == ["index1", "index2"]
    mock_dao.client.list_index_names.assert_called_once()


def test_retrieve_index_schemas(mock_dao):
    mock_index_1 = MagicMock()
    mock_index_1.serialize.return_value = {"name": "index1", "fields": []}

    mock_index_2 = MagicMock()
    mock_index_2.serialize.return_value = {"name": "index2", "fields": []}

    mock_dao.client.list_indexes.return_value = [mock_index_1, mock_index_2]

    result = mock_dao.retrieve_index_schemas()

    assert result == [
        {"name": "index1", "fields": []},
        {"name": "index2", "fields": []}
    ]
    mock_dao.client.list_indexes.assert_called_once()


def test_retrieve_index_schema(mock_dao):
    mock_index = MagicMock()
    mock_index.serialize.return_value = {"name": "index1", "fields": ["field1", "field2"]}

    mock_dao.client.get_index.return_value = mock_index

    result = mock_dao.retrieve_index_schema("index1")

    assert result == {"name": "index1", "fields": ["field1", "field2"]}
    mock_dao.client.get_index.assert_called_once_with("index1")
