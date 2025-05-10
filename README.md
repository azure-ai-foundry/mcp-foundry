# MCP Foundry Server

A Model Context Protocol server for Azure AI Foundry, providing a unified set of tools for knowledge, models, content safety, observability, and more.

[![GitHub watchers](https://img.shields.io/github/watchers/azure-ai-foundry/mcp-foundry.svg?style=social&label=Watch)](https://github.com/azure-ai-foundry/mcp-foundry/watchers)
[![GitHub forks](https://img.shields.io/github/forks/azure-ai-foundry/mcp-foundry.svg?style=social&label=Fork)](https://github.com/azure-ai-foundry/mcp-foundry/fork)
[![GitHub stars](https://img.shields.io/github/stars/azure-ai-foundry/mcp-foundry?style=social&label=Star)](https://github.com/azure-ai-foundry/mcp-foundry/stargazers)
[![Azure AI Community Discord](https://dcbadge.vercel.app/api/server/ByRwuEEgH4)](https://discord.gg/REmjGvvFpW)

## Tool Categories

### Foundry-Knowledge
#### Tools
- **list_index_names** - Retrieve all names of indexes from the AI Search Service  
- **list_index_schemas** - Retrieve all index schemas from the AI Search Service  
- **retrieve_index_schema** - Retrieve the schema for a specific index from the AI Search Service  
- **create_index** - Creates a new index  
- **modify_index** - Modifies the index definition of an existing index  
- **delete_index** - Removes an existing index  
- **add_document** - Adds a document to the index  
- **delete_document** - Removes a document from the index  
- **query_index** - Searches a specific index to retrieve matching documents  
- **get_document_count** - Returns the total number of documents in the index  
- **list_indexers** - Retrieve all names of indexers from the AI Search Service  
- **get_indexer** - Retrieve the full definition of a specific indexer from the AI Search Service  
- **create_indexer** - Create a new indexer in the Search Service with the skill, index and data source  
- **delete_indexer** - Delete an indexer from the AI Search Service by name  
- **list_data_sources** - Retrieve all names of data sources from the AI Search Service  
- **get_data_source** - Retrieve the full definition of a specific data source  
- **list_skill_sets** - Retrieve all names of skill sets from the AI Search Service  
- **get_skill_set** - Retrieve the full definition of a specific skill set  
- **fk_fetch_local_file_contents** - Retrieves the contents of a local file path (sample JSON, document etc)  
- **fk_fetch_url_contents** - Retrieves the contents of a URL (sample JSON, document etc)


##### Configuration of Environment Variables in MCP Host

You will need to create an .env file in the directory you have cloned the repo to

If you are authenticating with a managed identity you will need to pass in the environment variables in your MCP host configuration. You can also use the AI Search API Key to Authenticate.

The authentication method and search endpoints needs to be specified. These are required environment variables

If you are authenticating with a service principal, then you should configure the following variable:
- AZURE_AUTHENTICATION_METHOD - default is "api-search-key"
- AZURE_AI_SEARCH_ENDPOINT
- AZURE_TENANT_ID
- AZURE_CLIENT_ID
- AZURE_CLIENT_SECRET

If you are authenticating with an API key, then you have to configure the following environment variables:
- AZURE_AUTHENTICATION_METHOD - default is "api-search-key"
- AZURE_AI_SEARCH_ENDPOINT
- AZURE_AUTHENTICATION_METHOD
- AZURE_AI_SEARCH_API_KEY

You can also filter the list of tools returned to your MCP host by specifying a comma-delimited list of tool groups in your configuration.

| Environment Variable            | Value Data Type  | Why It Is Needed                                                                                           |
|---------------------------------|------------------|------------------------------------------------------------------------------------------------------------|
| AZURE_AUTHENTICATION_METHOD     | `string`         | `"service-principal"` for service principal based, or `"api-search-key"` for key-based access.             |
| AZURE_AI_SEARCH_ENDPOINT        | `string (URL)`   | Specifies the Azure AI Search endpoint URL; used to send REST API requests to the service.                 |
| AZURE_TENANT_ID                 | `string`         | Identifies the Azure Active Directory (AAD) tenant used for authentication via the Service Principal.      |
| AZURE_CLIENT_ID                 | `string`         | The unique identifier of the Service Principal (app registration) used for Azure authentication.           |
| AZURE_CLIENT_SECRET             | `string`         | The secret credential for the Service Principal; used to authenticate and obtain tokens from AAD.          |
| AZURE_AI_SEARCH_API_KEY         | `string`         | Used to authenticate read/write API requests to the Azure AI Search instance; must be kept secure.         |
| AZURE_AI_SEARCH_API_VERSION     | `string`         | API Version to use.                                                                                        |


### Foundry-Models
#### Tools
- Tool 1: [placeholder]
- Tool 2: [placeholder]

### Foundry-Content-Safety
#### Tools
- Tool 1: [placeholder]
- Tool 2: [placeholder]

### Foundry-Observability
#### Tools
- Tool 1: [placeholder]
- Tool 2: [placeholder]

---

## Configuration

Edit `mcp.json` to configure server options and tool settings.

## Deployment

### Quick Start

[![Open in GitHub Codespaces](https://img.shields.io/static/v1?style=for-the-badge&label=GitHub+Codespaces&message=Open&color=brightgreen&logo=github)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=599293758&machine=standardLinux32gb&devcontainer_path=.devcontainer%2Fdevcontainer.json&location=WestUs2)
[![Open in Dev Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/azure-samples/azure-search-openai-demo)

### GitHub Codespaces

- Open this repo in Codespaces and run:
  ```sh
  # If you are running the server in SSE mode with default settings
  uv run __main__.py --transport sse
  
  # If you need to override the port and use a custom environment variable file
  uv run __main__.py --transport sse --host 127.0.0.1 --port 8080 --envFile .env --logLevel DEBUG 
  
  # If you, are running in STDIO mode, please refer to the mcp.json file for how to configure your MCP host
  ```

### VS Code

- Open in VS Code and run:
  ```sh
  uv run __main__.py --transport sse
  ```

### Docker

- Build and run:
  ```sh
  docker build -t mcp/foundry .
  docker run -it --rm mcp/foundry
  ```

## License

MIT License. See LICENSE for details.
