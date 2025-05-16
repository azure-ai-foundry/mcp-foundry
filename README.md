[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/azure-ai-foundry-mcp-foundry-badge.png)](https://mseep.ai/app/azure-ai-foundry-mcp-foundry)

# Azure AI Foundry MCP Servers

This repository showcases MCP servers that integrates with Azure AI Foundry to enable interesting scenarios powered by Azure AI Foundry.

[![GitHub watchers](https://img.shields.io/github/watchers/azure-ai-foundry/mcp-foundry.svg?style=social&label=Watch)](https://github.com/azure-ai-foundry/mcp-foundry/watchers)
[![GitHub forks](https://img.shields.io/github/forks/azure-ai-foundry/mcp-foundry.svg?style=social&label=Fork)](https://github.com/azure-ai-foundry/mcp-foundry/fork)
[![GitHub stars](https://img.shields.io/github/stars/azure-ai-foundry/mcp-foundry?style=social&label=Star)](https://github.com/azure-ai-foundry/mcp-foundry/stargazers)
[![Azure AI Community Discord](https://dcbadge.vercel.app/api/server/ByRwuEEgH4)](https://discord.gg/REmjGvvFpW)

## MCP Servers

- [Azure AI Agent Service MCP Server](./docs/azure-ai-agent-service-mcp-server.md) - Connect to Azure AI Agents and use them in any MCP client.

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
