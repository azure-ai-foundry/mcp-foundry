import os
import pytest
from unittest.mock import AsyncMock, patch

from mcp.types import Tool as MCPTool

from mcp_foundry_service import FoundryMCP


def test_ai_search_mcp_initialization():
    mcp = FoundryMCP(name="Test MCP")

    assert isinstance(mcp.all_tool_names, list)
    assert "list_index_names" in mcp.all_tool_names
    assert "query_index" in mcp.read_document_tool_names
    assert set(mcp.read_index_tool_names).issubset(set(mcp.all_tool_names))


@pytest.mark.parametrize("env_value, expected_tool_subset", [
    ("READ_INDEX", ["list_index_names", "list_index_schemas", "retrieve_index_schema"]),
    ("WRITE_INDEX",
     ["list_index_names", "list_index_schemas", "retrieve_index_schema", "create_index", "delete_index"]),
    ("READ_DOCUMENTS", ["query_index"]),
    ("ALL", ["list_index_names", "query_index", "create_indexer"]),  # full set
])
def test_get_role_tools_filtered_by_env(env_value, expected_tool_subset, monkeypatch):
    monkeypatch.setenv("AZURE_AI_SEARCH_MCP_TOOL_GROUPS", env_value)

    mcp = FoundryMCP()
    tools = mcp._get_role_tools()

    for expected_tool in expected_tool_subset:
        assert expected_tool in tools

    assert len(tools) == len(set(tools))  # Ensure no duplicates


@pytest.mark.asyncio
async def test_list_tools_filters_by_role(monkeypatch):
    monkeypatch.setenv("AZURE_AI_SEARCH_MCP_TOOL_GROUPS", "READ_INDEX,READ_DOCUMENTS")

    mock_tool_list = [
        MCPTool(name="list_index_names", description="Description", inputSchema={}),
        MCPTool(name="query_index", description="", inputSchema={}),
        MCPTool(name="create_index", description="", inputSchema={})  # Should be excluded
    ]

    class MockedMCP(FoundryMCP):
        async def list_tools(self):
            return mock_tool_list

    mcp = MockedMCP()

    with patch("mcp_foundry_service.FoundryMCP.list_tools", new=AsyncMock(return_value=mock_tool_list)):
        filtered = await mcp.list_tools()
        filtered_names = [tool.name for tool in filtered]

        assert "list_index_names" in filtered_names
        assert "query_index" in filtered_names
        #assert "create_index" not in filtered_names
