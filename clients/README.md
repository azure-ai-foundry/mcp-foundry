# Client examples

## Prepare the environment to run the server

To run the MCP server, you need to have a Python version that's compatible with the server and one of the following dependencies installed to run the server: `pipx`, `uvx`, or `uv`. You can compare and choose the one that best fits your needs.

First, you need to create a Python environment. You can use `conda` or `venv` to create a virtual environment. The following instructions will help you set up the environment.

```bash
conda create -n mcp-env python=3.10
conda activate mcp-env
# or `python3 -m venv mcp-env` and `source mcp-env/bin/activate`
```

Next, you need to install the dependencies. You can use `pipx`, `uvx`, or `uv` to run the server. The following instructions will help you install the dependencies. For more options and guidance, please refer to the official documentation of each tool.

- [pipx](https://pypi.org/project/pipx/)

```bash
pip install pipx
pipx ensurepath
```

- [uvx](https://pypi.org/project/uvx/)

```bash
pip install uvx<2.0
# or `uv install uvx` or `pipx install uvx`
```

- [uv](https://pypi.org/project/uv/)

```bash
pip install uv
# or `pipx install uv`
```

## Run the server in SSE mode for MCP Client

To run the MCP server in SSE mode, you need to have the MCP server installed and running.

You can choose one of the following options (using `pipx`, `uvx`, or `uv` commands) to run the server in SSE mode.

<details>
<summary>Run server using a cloned repo</summary>

You can clone this repo in the environment you want to run the server, and start the server in SSE mode.

First clone the repo:

```bash
git clone https://github.com/azure-ai-foundry/mcp-foundry.git -b msbuild2025

# Navigate to the project on your machine
cd mcp-foundry
```

Now you can run the server using *one* of the following commands:

```bash
# With pipx
pipx run --no-cache --spec . run-azure-ai-foundry-mcp --transport sse --envFile .env

# With uvx
uvx --no-cache --from . run-azure-ai-foundry-mcp --transport sse --envFile .env

# With uv
uv run --prerelease=allow python -m mcp_foundry --transport sse --envFile .env
```

If you do not need `.env` file, you can remove the `--envFile .env` option from the command.

</details>

<details>
<summary>Run server using a remote URL</summary>

You can alternatively run it using the remote URL for the repo directly. In this case, you don't need to clone the repo in the environment you want to run the server.

You can choose one of the following options (using `pipx`, `uvx`, or `uv` commands) to run the server in SSE mode.

```bash

# With pipx
pipx run --no-cache --spec git+https://github.com/azure-ai-foundry/mcp-foundry.git@msbuild2025 run-azure-ai-foundry-mcp --transport sse --envFile .env

# With uvx
uvx --no-cache --from git+https://github.com/azure-ai-foundry/mcp-foundry.git@msbuild2025 run-azure-ai-foundry-mcp --transport sse --envFile .env

```

</details>

We have this example to help you configure your VSCode MCP client in SSE mode:

- mcp.sse.json

Once the server is up and running you can point your code client or VSCode to the SSE endpoint of the service to start exploring the tools.

After the server is up, you can point the MCP Client to this endpoint.

## Run the server in STDIO mode from VSCode or other MCP Hosts that Supports STDIO Transport

We have the following config examples for your reference using uv, uvx and pipx:

- mcp.stdio.pipx.1.json
- mcp.stdio.pipx.1.json
- mcp.stdio.pipx.2.json
- mcp.stdio.uv.json
- mcp.stdio.uvx.1.json  
- mcp.stdio.uvx.2.json

You can use the examples from [this folder](./vscode/mcp-configs) to configure your MCP Host using your preferred command.
