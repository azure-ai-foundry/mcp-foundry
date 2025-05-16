

## Running the Server in SSE Mode for MCP Client

Boot up the MCP Server in SSE mode using one of the following commands:

````bash 

git clone https://github.com/azure-ai-foundry/mcp-foundry.git -b msbuild2025

# Navigate to the project on your machine
cd /path/to/project

# With pipx
pipx run --no-cache --spec . run-azure-ai-foundry-mcp --transport sse --envFile .env

# With uvx
uvx --no-cache --from . run-azure-ai-foundry-mcp --transport sse --envFile .env

# With uv
uv run --prerelease=allow python -m mcp_foundry --transport sse

````


You can also run it using the remote URL for the repo directly

````bash

# With pipx
pipx run --no-cache --spec git+https://github.com/azure-ai-foundry/mcp-foundry.git@msbuild2025 run-azure-ai-foundry-mcp --transport sse --envFile .env

# With uvx
uvx --no-cache --from git+https://github.com/azure-ai-foundry/mcp-foundry.git@msbuild2025 run-azure-ai-foundry-mcp --transport sse --envFile .env

````

We have this example to help you configure your VSCode MCP client in SSE mode:

- mcp.sse.json

Once the server is up and running you can point your code client or VSCode to the SSE endpoint of the service to start exploring the tools.

After the server is up, you can point the MCP Client to this endpoint.

### Running the Server in STDIO Mode from VSCode or other MCP Hosts that Supports STDIO Transport

We have the following config examples for your reference using uv, uvx and pipx:

- mcp.stdio.pipx.1.json
- mcp.stdio.pipx.1.json 
- mcp.stdio.pipx.2.json 
- mcp.stdio.uv.json     
- mcp.stdio.uvx.1.json  
- mcp.stdio.uvx.2.json

You can use the examples from [this folder](./vscode/mcp-configs) to configure your MCP Host using your preferred command.