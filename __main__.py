import os
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional, List, Literal, cast

import httpx
from azure.search.documents.indexes._generated.models import FieldMapping
from dotenv import load_dotenv

from mcp_foundry_knowledge import SearchIndexDao, SearchClientDao, SearchIndexerDao, SearchIndexSchema, \
    convert_pydantic_model_to_search_index, FieldMappingModel, convert_to_field_mappings, FoundryMCP, \
    OperationResult, \
    SearchDocument, LoggingLevel


def setup_mcp_service(host_name: str, port: int, log_level: LoggingLevel = "INFO"):
    settings = {"host": host_name, "port": port, "log_level": log_level}

    mcp = FoundryMCP("AI Search MCP Service", **settings)

    @mcp.tool(description="Reads the content of a local file and returns it as a string")
    def fk_fetch_local_file_contents(file_path: str, encoding: str = "utf-8") -> str:
        """
        Reads the content of a local file and returns it as a string.

        Args:
            file_path (str): The path to the local file.
            encoding (str): The character encoding to use (default is 'utf-8').

        Returns:
            str: The contents of the file as a string.

        Raises:
            FileNotFoundError: If the file does not exist.
            IOError: If the file cannot be read.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"No such file: '{file_path}'")

        return path.read_text(encoding=encoding)

    @mcp.tool(description="Fetches the contents of the given HTTP URL")
    async def fk_fetch_url_contents(url: str) -> str:
        """
        Fetches the contents of the given HTTP URL

        Args:
            url (str): The URL to fetch content from.

        Returns:
            str: The content retrieved from the URL.

        Raises:
            httpx.RequestError: If the request fails due to a network problem.
            httpx.HTTPStatusError: If the response status code is not 2xx.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    @mcp.tool(description="Retrieves the names of all indexes ")
    async def list_index_names() -> list[str]:
        """
        Retrieves the names of all indexes

        Returns:
            list[str]: A list containing the names of all available search indexes.
        """
        dao = SearchIndexDao()
        return dao.retrieve_index_names()

    @mcp.tool(description="Retrieves the schemas for all indexes ")
    async def list_index_schemas() -> list[OperationResult]:
        """
        Retrieves the schemas for all indexes.

        Returns:
            list[OperationResult]: A list of dictionaries, each representing the schema of an index.
        """
        dao = SearchIndexDao()
        return cast(list[OperationResult], dao.retrieve_index_schemas())

    @mcp.tool(description="Retrieves the schema for a specific index")
    async def retrieve_index_schema(index_name: str) -> OperationResult:
        """
        Retrieves the schema for a specific index

        Args:
            index_name (str): The name of the index for which the schema should be retrieved.

        Returns:
            OperationResult: A dictionary representing the schema of the specified index.
        """
        dao = SearchIndexDao()
        return cast(OperationResult, dao.retrieve_index_schema(index_name))

    @mcp.tool(description="Creates an AI Search index")
    async def create_index(index_definition: SearchIndexSchema) -> OperationResult:
        """
        Creates a new index.

        Args:
            index_definition (SearchIndexSchema): The full definition of the index to be created.

        Returns:
            OperationResult: The serialized response of the created index.
        """
        dao = SearchIndexDao()
        compatible_index_definition = convert_pydantic_model_to_search_index(index_definition)
        return cast(OperationResult, dao.create_index(compatible_index_definition))

    @mcp.tool(description="Updates an AI Search index with a new index definition")
    async def modify_index(index_name: str, updated_index_definition: SearchIndexSchema) -> OperationResult:
        """
        Updates an AI Search index with the modified index definition

        Args:
            index_name (str): The name of the index to be updated
            updated_index_definition (SearchIndexSchema): The full updated definition of the index.

        Returns:
            OperationResult: The serialized response of the modified index.
        """
        dao = SearchIndexDao()
        compatible_index_definition = convert_pydantic_model_to_search_index(updated_index_definition)
        return cast(OperationResult, dao.modify_index(index_name, compatible_index_definition))

    @mcp.tool(description="Deletes the specified index")
    async def delete_index(index_name: str) -> str:
        """
        Deletes an existing index .

        Args:
            index_name (str): The name of the index to be deleted.

        Returns:
            str: The result of the operation
        """
        dao = SearchIndexDao()
        dao.delete_index(index_name)
        return "Successful"

    @mcp.tool(description="Return the total number of documents in the index")
    def get_document_count(index_name: str) -> int:
        """
        Returns the total number of documents in the index

        Args:
            index_name (str): the name of the index

        Returns:
            int: The total number of documents in the index
        """
        search_client_dao = SearchClientDao(index_name)
        result = search_client_dao.get_document_count()
        return result

    @mcp.tool(description="Adds a document to the index")
    def add_document(index_name: str, document: SearchDocument) -> OperationResult:
        """
        Add a document to the specified Azure AI Search index

        Args:
            index_name (str): the name of the index we are adding the document to
            document (SearchDocument): The contents of the document to be added to the index.

        Returns:
            OperationResult: The serialized result of the add operation for the single document.
        """
        search_client_dao = SearchClientDao(index_name)
        result = search_client_dao.add_document(document.model_dump())
        return cast(OperationResult, result)

    @mcp.tool(description="Removes a document from the index")
    async def delete_document(index_name: str, key_field_name: str, key_value: str) -> OperationResult:
        """
        Removes a document from the index.

        Args:
            index_name (str): the name of the index from which to delete the document
            key_field_name (str): The name of the key field in the index we are removing the document from
            key_value (str): The value of the key field for the document we are deleting

        Returns:
            OperationResult: A list of serialized results for each document deletion operation.
        """
        search_client_dao = SearchClientDao(index_name)
        return cast(OperationResult, search_client_dao.delete_document(key_field_name, key_value))

    @mcp.tool(description="Search a specific index for documents in that index")
    async def query_index(
            index_name: str,
            search_text: Optional[str] = None,
            *,
            query_filter: Optional[str] = None,
            order_by: Optional[List[str]] = None,
            select: Optional[List[str]] = None,
            skip: Optional[int] = None,
            top: Optional[int] = None,
            include_total_count: Optional[bool] = None,
    ) -> list[dict]:
        """Searches the Azure search index for documents matching the query criteria

            :param str index_name: The name of the index to query. This parameter is required
            :param str search_text: A full-text search query expression; Use "*" or omit this parameter to
                match all documents.
            :param str query_filter: The OData $filter expression to apply to the search query.
            :param list[str] order_by: The list of OData $orderby expressions by which to sort the results. Each
                expression can be either a field name or a call to either the geo.distance() or the
                search.score() functions. Each expression can be followed by asc to indicate ascending, and
                desc to indicate descending. The default is ascending order. Ties will be broken by the match
                scores of documents. If no OrderBy is specified, the default sort order is descending by
                document match score. There can be at most 32 $orderby clauses.
            :param list[str] select: The list of fields to retrieve. If unspecified, all fields marked as retrievable
                in the schema are included.
            :param int skip: The number of search results to skip. This value cannot be greater than 100,000.
                If you need to scan documents in sequence, but cannot use $skip due to this limitation,
                consider using $orderby on a totally-ordered key and $filter with a range query instead.
            :param int top: The number of search results to retrieve. This can be used in conjunction with
                $skip to implement client-side paging of search results. If results are truncated due to
                server-side paging, the response will include a continuation token that can be used to issue
                another Search request for the next page of results.
            :param bool include_total_count: A value that specifies whether to fetch the total count of
                results. Default is false. Setting this value to true may have a performance impact. Note that
                the count returned is an approximation.
            :rtype: list[dict]
            """
        search_client_dao = SearchClientDao(index_name)

        search_results: list[dict] = search_client_dao.query_index(
            search_text=search_text,
            include_total_count=include_total_count,
            query_filter=query_filter,
            order_by=order_by,
            select=select,
            skip=skip,
            top=top
        )

        return search_results

    @mcp.tool(
        description="Retrieves the list of all the names of the indexers")
    async def list_indexers() -> list[str]:
        """
        Retrieves the list of all indexers registered .

        Returns:
            list[str]: A list of indexer names.
        """
        search_indexer_dao = SearchIndexerDao()
        return search_indexer_dao.list_indexers()

    @mcp.tool(description="Retrieves the details of a specific indexer by name.")
    async def get_indexer(name: str) -> OperationResult:
        """
        Retrieves the details of a specific indexer by name.

        Args:
            name (str): The name of the indexer to retrieve.

        Returns:
            OperationResult: A dictionary containing the indexer details.
        """
        search_indexer_dao = SearchIndexerDao()
        return cast(OperationResult, search_indexer_dao.get_indexer(name))

    @mcp.tool(description="Creates a new indexer")
    async def create_indexer(
            name: str,
            data_source_name: str,
            target_index_name: str,
            description: str,
            field_mappings: list[FieldMappingModel],
            output_field_mappings: list[FieldMappingModel],
            skill_set_name: str = None
    ) -> OperationResult:
        """
        Creates a new indexer.

        Args:
            name (str): The name of the indexer to be created.
            data_source_name (str): The name of the indexer to be created.
            target_index_name (str): The name of the indexer to be created.
            description (str): The name of the indexer to be created.
            field_mappings (list[FieldMapping]): The field mappings to be created.
            output_field_mappings (list[FieldMapping]): The field mappings in the index .
            skill_set_name (str): The name of the indexer to be created.

        Returns:
            OperationResult: A dictionary representing the created indexer.
        """
        search_indexer_dao = SearchIndexerDao()

        compat_field_mappings = convert_to_field_mappings(field_mappings)
        compat_output_field_mappings = convert_to_field_mappings(output_field_mappings)

        result = search_indexer_dao.create_indexer(
            name=name,
            data_source_name=data_source_name,
            target_index_name=target_index_name,
            description=description,
            field_mappings=compat_field_mappings,
            output_field_mappings=compat_output_field_mappings,
            skill_set_name=skill_set_name
        )

        return cast(OperationResult, result)

    @mcp.tool(description="Deletes the indexer")
    async def delete_indexer(name: str) -> str:
        """
        Deletes an indexer by name.

        Args:
            name (str): The name of the indexer to delete.

        Returns:
            None
        """
        search_indexer_dao = SearchIndexerDao()
        search_indexer_dao.delete_indexer(name)
        return "Successful"

    @mcp.tool(description="Retrieves the list of all data source names")
    async def list_data_sources() -> list[str]:
        """
        Retrieves the list of all data source names

        Returns:
            list[str]: A list of data source names.
        """
        search_indexer_dao = SearchIndexerDao()
        return search_indexer_dao.list_data_sources()

    @mcp.tool(description="Retrieves the details of a specific data source by name")
    async def get_data_source(name: str) -> OperationResult:
        """
        Retrieves the details of a specific data source by name.

        Args:
            name (str): The name of the data source to retrieve.

        Returns:
            OperationResult: A dictionary containing the data source details.
        """
        search_indexer_dao = SearchIndexerDao()
        return cast(OperationResult, search_indexer_dao.get_data_source(name))

    @mcp.tool(description="Retrieves the list of the names of all skill sets")
    async def list_skill_sets() -> list[str]:
        """
        Retrieves the list of all skill sets

        Returns:
            list[str]: A list of skill set names.
        """
        search_indexer_dao = SearchIndexerDao()
        return search_indexer_dao.list_skill_sets()

    @mcp.tool(description="Retrieves the details of a specific skill set by name")
    async def get_skill_set(skill_set_name: str) -> OperationResult:
        """
        Retrieves the details of a specific skill set by name.

        Args:
            skill_set_name (str): The name of the skill set to retrieve.

        Returns:
            OperationResult: A dictionary containing the skill set details.
        """
        search_indexer_dao = SearchIndexerDao()
        return cast(OperationResult, search_indexer_dao.get_skill_set(skill_set_name))

    @mcp.prompt(description="A prompt to list the names of all the indices")
    async def list_all_indices_prompt() -> str:
        return "List all the indices by name"

    @mcp.prompt(description="A prompt to retrieve the schema details of all the indices")
    async def list_all_indices_details_prompt() -> str:
        return "Show the schema details of all the indexes"

    @mcp.prompt(description="Get the detail for a specific schema")
    async def retrieve_index_schema_prompt(index_name: str) -> str:
        return f"Show the for the {index_name} index"

    @mcp.prompt(description="Display the contents of a local file")
    async def fetch_local_file_contents_prompt(file_path: str) -> str:
        return f"Display the contents of the local file {file_path}"

    @mcp.prompt(description="Display the contents of a URL")
    async def fetch_url_contents_prompt(url: str) -> str:
        return f"Display the contents of the file {url}"

    @mcp.prompt(description="Creates an index matching the schema of a JSON file (local file or URL)")
    async def create_index_from_file_analysis_prompt(index_name: str, url: str) -> str:
        return f"Create an index called '{index_name}' that is compatible with the JSON file contents in the file {url}"

    @mcp.prompt(description="Updates the index definition for a specific field")
    async def modify_index_field_definition_prompt(index_name: str, field_name: str) -> str:
        return f"Modify the index '{index_name}' and make the {field_name} retrievable, searchable and filterable"

    @mcp.prompt(description="Removes a specific index")
    async def remove_index_definition_prompt(index_name: str) -> str:
        return f"Remove the '{index_name}' index"

    @mcp.prompt(description="Adds the contents of a JSON file (local file or URL) to the specified index")
    async def add_document_from_file_analysis_prompt(index_name: str, url: str) -> str:
        return f"Add a document or documents to the '{index_name}' index using the contents of the file {url}"

    @mcp.prompt(description="Remove a document from the index")
    async def remove_document_prompt(index_name: str, id: str) -> str:
        return f"""
        Remove a document from the '{index_name}' index matching id '{id}'
        Remove all documents from the '{index_name}' where the preferred language is French
        Remove all documents from the '{index_name}' where the sign up date is March 30th 2025
        """

    @mcp.prompt(description="Queries the index")
    async def search_index_prompt(index_name: str, id: str) -> str:
        return f"""

        - Show all documents from the '{index_name}' index
        - Show all documents from the '{index_name}' where the preferred language is French
        - Show all documents from the '{index_name}' where the sign up date is March 30th 2025
        """

    @mcp.prompt(description="How many documents are in a specific document")
    async def get_document_count_prompt(index_name: str, id: str) -> str:
        return f"How many documents are in the '{index_name}' index"

    @mcp.prompt(description="List the names of the indexers in AI Search")
    async def list_indexers_prompt() -> str:
        return f"List the names of the indexers in AI Search"

    @mcp.prompt(description="Get details about a specific indexer")
    async def get_indexer_detail_prompt(name: str) -> str:
        return f"Show the details for the '{name}' indexer"

    @mcp.prompt(description="Creates and indexer with a datasource")
    async def create_indexer_datasource_prompt(indexer_name: str, data_source_name: str) -> str:
        return f"Create an indexer named '{indexer_name}' with field mappings using the data source '{data_source_name}'"

    @mcp.prompt(description="Creates and indexer with a datasource and skill set")
    async def create_indexer_datasource_skill_set_prompt(indexer_name: str, data_source_name: str,
                                                         skill_set_name: str) -> str:
        return f"Create an indexer named '{indexer_name}' with field mappings using the data source '{data_source_name}' and skillset '{skill_set_name}'"

    @mcp.prompt(description="List all the data sources and skill sets")
    async def list_skills_and_data_sources_prompt() -> str:
        return "List all the skill sets and data sources"

    @mcp.prompt(description="Show details for a specific data source")
    async def get_data_source_details_prompt(name: str) -> str:
        return f"Show details for the '{name}' data source"

    @mcp.prompt(description="Show details for a specific skill set")
    async def get_skillset_details_prompt(name: str) -> str:
        return f"Show details for the '{name}' skillset"

    @mcp.resource("examples://python-mcp-client-pydantic-ai",
                  description="A resource showing how to communicate with the MCP server using Pydantic AI",
                  mime_type="text/markdown")
    async def sample_python_mcp_client_resource() -> str:
        return """
        ## MCP Client Written with Pydantic AI
        This is an MCP client written with Pydantic AI that is intended to be used for checking out all the capabilities of the MCP service

        https://github.com/projectAcetylcholine/ai-search-pydantic-mcp-client
        """

    return mcp


def run_mcp_service():
    parser = ArgumentParser(description="Start the MCP service with provided or default configuration.")

    parser.add_argument('--transport', required=True, default='stdio',
                        help='Transport protocol (sse | stdio) (default: stdio)')
    parser.add_argument('--envFile', required=False, default='.env',
                        help='Path to .env file (default: .env)')
    parser.add_argument('--host', required=False, default='0.0.0.0',
                        help='Host IP or name for SSE (default: 0.0.0.0)')
    parser.add_argument('--port', required=False, type=int, default=8000,
                        help='Port number for SSE (default: 8000)')
    parser.add_argument('--logLevel', required=False, default='DEBUG',
                        help='Logging Level (default: DEBUG) one of: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]')

    # Parse the application arguments
    args = parser.parse_args()

    # Retrieve the specified transport
    transport: Literal["stdio", "sse"] = args.transport
    mcp_env_file = args.envFile
    log_level: LoggingLevel = args.logLevel

    # Set up the Host name and port
    mcp_host: str = args.host
    mcp_port: int = args.port

    if transport in ["sse", "stdio"]:
        print("")
        print("")
        print(f"Transport is specified as {transport}")
    else:
        print("")
        print("")
        print(f"Invalid transport was specified: transport={transport}")
        parser.print_help()
        sys.exit(1)

    # Check if envFile exists and load it
    if mcp_env_file and os.path.exists(mcp_env_file):
        load_dotenv(dotenv_path=mcp_env_file)
        print(f"Environment variables loaded from {mcp_env_file}")
    else:
        print(f"Env file '{mcp_env_file}' not found. Skipping environment loading.")

    mcp_service = setup_mcp_service(mcp_host, mcp_port, log_level=log_level)

    # Check all params and then run or print the help message
    mcp_service.run(transport)


if __name__ == "__main__":
    run_mcp_service()
