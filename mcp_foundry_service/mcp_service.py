import os
from typing import Any, Literal

from mcp.server.fastmcp.server import logger, FastMCP
from mcp.types import Tool as MCPTool

LoggingLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class FoundryMCP(FastMCP):

    def __init__(self, name: str | None = None, instructions: str | None = None, **settings: Any):
        super().__init__(name=name, instructions=instructions, local_level="DEBUG", **settings)

        self.all_tool_names: list[str] = [
            "list_index_names",
            "list_index_schemas",
            "retrieve_index_schema",
            "create_index",
            "delete_index",
            "modify_index",
            "add_document",
            "delete_document",
            "query_index",
            "get_document_count",
            "list_indexers",
            "get_indexer",
            "create_indexer",
            "delete_indexer",
            "list_data_sources",
            "get_data_source",
            "list_skill_sets",
            "get_skill_set",
            "fk_fetch_local_file_contents",
            "fk_fetch_url_contents",
        ]

        self.fetch_file_contents = [
            "fk_fetch_local_file_contents",
            "fk_fetch_url_contents",
        ]

        self.read_index_tool_names = [
            "list_index_names",
            "list_index_schemas",
            "retrieve_index_schema"
        ]

        self.write_index_tool_names = [
            "list_index_names",
            "list_index_schemas",
            "retrieve_index_schema",
            "create_index",
            "delete_index",
            "modify_index",
        ]

        self.read_document_tool_names = [
            "query_index",
            "get_document_count"
        ]

        self.write_document_tool_names = [
            "add_document",
            "delete_document",
            "query_index",
        ]

        self.read_indexer_tool_names = [
            "list_indexers",
            "get_indexer",
            "list_data_sources",
            "get_data_source",
            "list_skill_sets",
            "get_skill_set"
        ]

        self.write_indexer_tool_names = [
            "list_indexers",
            "get_indexer",
            "create_indexer",
            "delete_indexer",
            "list_data_sources",
            "get_data_source",
            "list_skill_sets",
            "get_skill_set"
        ]

    def _get_role_tools(self) -> list[str]:
        tool_groups_raw = os.environ.get("AZURE_AI_SEARCH_MCP_TOOL_GROUPS", "ALL")
        tool_groups_list = tool_groups_raw.split(",")

        filtered_list_of_tools: list[str] = []

        # This is a dictionary of the groups
        # @TODO: define and validate the filtering of tool names for each group accordingly
        tool_database: dict[str, list[str]] = {
            "ALL": self.all_tool_names,
            "WRITE_OPERATIONS": self.all_tool_names,
            "READ_OPERATIONS": self.read_indexer_tool_names + self.read_index_tool_names + self.read_document_tool_names + self.fetch_file_contents,
            "READ_INDEX": self.read_index_tool_names,
            "WRITE_INDEX": self.write_index_tool_names,
            "READ_DOCUMENTS": self.read_document_tool_names,
            "WRITE_DOCUMENTS": self.write_document_tool_names,
            "READ_INDEXERS": self.read_indexer_tool_names,
            "WRITE_INDEXERS": self.write_indexer_tool_names,
            "FETCH_FILE_CONTENTS": self.fetch_file_contents
        }

        for tool_group_name in tool_groups_list:
            current_list_of_tools = tool_database[tool_group_name]
            filtered_list_of_tools += current_list_of_tools

        # Eliminate duplicates while preserving order
        unique_tool_names = list(dict.fromkeys(filtered_list_of_tools))

        return unique_tool_names

    async def list_tools(self) -> list[MCPTool]:

        # This is the filtered names of tools to send back to calling MCP client
        filtered_tool_names = self._get_role_tools()
        filtered_tool_list: list[MCPTool] = []

        # This is the list of tools registered at the service
        tool_list: list[MCPTool] = await super().list_tools()

        # Preparing the filtered list of tools
        for current_tool in tool_list:
            if current_tool.name in filtered_tool_names:
                filtered_tool_list.append(current_tool)

        return filtered_tool_list
