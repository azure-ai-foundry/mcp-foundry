# Azure AI Foundry MCP Servers

This repository showcases MCP servers that integrates with Azure AI Foundry to enable interesting scenarios powered by Azure AI Foundry.

[![GitHub watchers](https://img.shields.io/github/watchers/azure-ai-foundry/mcp-foundry.svg?style=social&label=Watch)](https://github.com/azure-ai-foundry/mcp-foundry/watchers)
[![GitHub forks](https://img.shields.io/github/forks/azure-ai-foundry/mcp-foundry.svg?style=social&label=Fork)](https://github.com/azure-ai-foundry/mcp-foundry/fork)
[![GitHub stars](https://img.shields.io/github/stars/azure-ai-foundry/mcp-foundry?style=social&label=Star)](https://github.com/azure-ai-foundry/mcp-foundry/stargazers)
[![Azure AI Community Discord](https://dcbadge.vercel.app/api/server/ByRwuEEgH4)](https://discord.gg/REmjGvvFpW)

---

# Foundry-Observability
## Tools

### Evaluator Utilities
- **list_text_evaluators** - List all available text evaluators.
- **list_agent_evaluators** - List all available agent evaluators.
- **get_text_evaluator_requirements** - Show input requirements for each text evaluator.
- **get_agent_evaluator_requirements** - Show input requirements for each agent evaluator.

### Text Evaluation
- **run_text_eval** - Run one or multiple text evaluators on a JSONL file or content.
- **format_evaluation_report** - Convert evaluation output into a readable Markdown report.

### Agent Evaluation
- **agent_query_and_evaluate** - Query an agent and evaluate its response using selected evaluators. End-to-End agent evaluation.
- **run_agent_eval** - Evaluate a single agent interaction with specific data (query, response, tool calls, definitions).

### Agent Service
- **list_agents** - List all Azure AI Agents available in the configured project.
- **connect_agent** - Send a query to a specified agent.
- **query_default_agent** - Query the default agent defined in environment variables.

---

## Configuration of Environment Variables in MCP Host
In your setup, environment variables are defined directly in the **Claude config file** under the `env` block of the `mcpServers` section. You need to download Claude Desktop app for using MCP server

### Example
<details>
<summary>Click to expand JSON config</summary>

```json
{
  "mcpServers": {
    "azure-ai-foundry": {
      "command": "C:\\Users\\<user_name>\\.venv\\Scripts\\python.exe",
      "args": [
        "path/to/<filename>.py"
      ],
      "env": {
        "EVAL_DATA_DIR": "path/to/eval/",
        "AZURE_SUBSCRIPTION_ID": "",
        "AZURE_RESOURCE_GROUP": "",
        "AZURE_PROJECT_NAME": "",
        "AZURE_OPENAI_ENDPOINT": "",
        "AZURE_OPENAI_API_KEY": "",
        "AZURE_OPENAI_DEPLOYMENT": "",
        "AZURE_OPENAI_API_VERSION": "",
        "PROJECT_CONNECTION_STRING": ""
      }
    }
  }
}
```

</details>

> 💡 You do **not** need to use a `.env` file when environment variables are configured this way.

---

### Required Environment Variables
| **Variable**                | **Required When**               | **Description**                                 |
| --------------------------- | ------------------------------- | ----------------------------------------------- |
| `EVAL_DATA_DIR`             | Always                          | Path to the JSONL evaluation dataset            |
| `AZURE_SUBSCRIPTION_ID`     | Agent eval or risk/safety evals | Azure subscription ID                           |
| `AZURE_RESOURCE_GROUP`      | Agent eval or risk/safety evals | Resource group of your Azure AI project         |
| `AZURE_PROJECT_NAME`        | Agent eval or risk/safety evals | Azure AI project name                           |
| `AZURE_OPENAI_ENDPOINT`     | Text quality evaluators         | Endpoint for Azure OpenAI                       |
| `AZURE_OPENAI_API_KEY`      | Text quality evaluators         | API key for Azure OpenAI                        |
| `AZURE_OPENAI_DEPLOYMENT`   | Text quality evaluators         | Deployment name (e.g., `gpt-4o`)                |
| `AZURE_OPENAI_API_VERSION`  | Text quality evaluators         | Version of the OpenAI API                       |
| `PROJECT_CONNECTION_STRING` | Agent services                  | Used for Azure AI Agent querying and evaluation |

---

### Notes

* If you're using **agent tools or safety evaluators**, make sure the Azure project credentials are valid.
* If you're only doing **text quality evaluation**, the OpenAI endpoint and key are sufficient.
* These variables are automatically read by the MCP when the config file is correctly set up.
  
---

## Configuration

Configure environment variables inside the `claude` config file under the `mcpServers` section. This allows MCP to start the server with the correct environment setup - No `.env` file is required if using this method.

Refer to the [Configuration of Environment Variables](#configuration-of-environment-variables-in-mcp-host) section above for details.

---

## Deployment

### Quick Start (vscode)

You can  run the server in VS Code using the same `uv` command in the integrated terminal:

```bash
uv run --directory <path-to-your-local-python-file-directory>
```

Replace `<path-to-your-local-python-file-directory>` with the folder containing your script (e.g., `azure_ai_foundryeval_mcp_v2.py`).

> ✅ Make sure your Claude `claude_desktop_config.json` is configured to reference the correct Python interpreter, file path, and environment variables.

---

# (Pending)
## MCP Servers

- [Azure AI Agent Service MCP Server](./azure-ai-agent-service-mcp-server/README.md) - Connect to Azure AI Agents and use them in any MCP client.

### Usage with Other MCP Clients

These servers follow the MCP protocol specification and can be used with any MCP-compatible client. Refer to your client's documentation for specific instructions on how to connect to external MCP servers.

## Development Notes

This project follows a polyglot structure with implementations in both Python and TypeScript:

### Python Development

1. Python code is located in the src/python directory
2. Always activate the virtual environment from the project root
3. For package installation, ensure you're in the Python directory where pyproject.toml is located

### TypeScript Development

1. TypeScript code is located in the src/typescript directory
2. Uses ES Modules for modern JavaScript compatibility
3. Standard npm workflow: `npm install` → `npm run build` → `npm start`

## License

This project is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
