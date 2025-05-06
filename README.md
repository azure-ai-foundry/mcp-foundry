# Azure AI Foundry MCP Servers

This repository showcases MCP servers that integrates with Azure AI Foundry to enable interesting scenarios powered by Azure AI Foundry.

[![GitHub watchers](https://img.shields.io/github/watchers/azure-ai-foundry/mcp-foundry.svg?style=social&label=Watch)](https://github.com/azure-ai-foundry/mcp-foundry/watchers)
[![GitHub forks](https://img.shields.io/github/forks/azure-ai-foundry/mcp-foundry.svg?style=social&label=Fork)](https://github.com/azure-ai-foundry/mcp-foundry/fork)
[![GitHub stars](https://img.shields.io/github/stars/azure-ai-foundry/mcp-foundry?style=social&label=Star)](https://github.com/azure-ai-foundry/mcp-foundry/stargazers)
[![Azure AI Community Discord](https://dcbadge.vercel.app/api/server/ByRwuEEgH4)](https://discord.gg/REmjGvvFpW)

## MCP Servers

- [Azure AI Agent Service MCP Server](./azure-ai-agent-service-mcp-server/README.md) - Connect to Azure AI Agents and use them in any MCP client.

### Usage with Other MCP Clients

These servers follow the MCP protocol specification and can be used with any MCP-compatible client. Refer to your client's documentation for specific instructions on how to connect to external MCP servers.

## Design Principles

When developing and contributing to MCP Servers within the Azure AI Foundry, please consider the following guiding principles. These are inspired by real-world user stories that demonstrate the value of scenario-driven, AI-first, and impact-focused tool design:

**Multi-MCP Server Strategy**: We recognize the value in complementary MCP server approaches:

- **Foundry MCP Server(s)**: Designed around a "Jobs to be Done" (JTBD) philosophy. JTBD means tools are built to solve complete user scenarios, not just expose APIs. For example, a tool might handle the entire workflow of selecting a region, checking quota, and deploying a model, rather than requiring users to call multiple low-level APIs. These servers allow for rapid iteration and experimentation, showcasing opinionated, scenario-driven solutions.
  - Foundry MCP server tools should focus on accomplishing these broader user "jobs" and may orchestrate or wrap multiple low-level APIs.
  - If fine-grained control or access to underlying configurations not directly exposed by a Foundry MCP tool is necessary, these tools can leverage the more granular APIs available in the Azure MCP Server.
  - Each tool within a Foundry MCP server should be clearly bound to a specific capability or service area of Azure AI Foundry. It's envisioned that there might be multiple, focused Foundry MCP servers, each dedicated to a distinct aspect of AI Foundry.
- **Azure MCP Server**: Suited for hosting atomic, general-purpose, and low-level APIs, providing a comprehensive toolkit of fundamental Azure capabilities. This server acts as a broad platform for a wide array of granular tools.

**Design for End-to-End Scenarios:**
   Tools should be designed to solve real user problems and business outcomes, not just expose technical capabilities. Contributors are encouraged to use user stories as inspiration, ensuring each tool can be invoked by an AI agent or user to accomplish a full scenario (e.g., “find and deploy models to a compliant region,” “summarize survey sentiment,” “automate index healing”).

**Enable Composability:**
   Tools should be designed to work well together, supporting orchestration by AI agents or users. Favor clear inputs/outputs and stateless operations where possible, so tools can be chained to automate complex workflows.

**Designing Discoverable Tools**: To ensure that tools are easily found and utilized by both end-users and AI agents, prioritize the creation of rich supporting assets for each tool. This includes:

- Clear and concise tool descriptions.
- Detailed descriptions for all parameters.
- Practical code samples and usage examples.
- User stories that illustrate the tool's value and typical use cases.
- Well-defined inputs/outputs.

**Security and Compliance**: All tools must adhere to Azure security and compliance best practices, including least-privilege access, data residency requirements, and auditability.

**Implement Consistent Error Handling**: Tools should follow a consistent approach to error handling, with clear, actionable error messages that help users and AI agents understand what went wrong and how to fix it. Provide structured error responses that include:

- An error code or identifier
- A human-readable description of the problem
- Suggestions for resolving the issue
- Links to relevant documentation when applicable

For contributors looking to get started, please see [CONTRIBUTING.md](CONTRIBUTING.md) for a step-by-step guide on the development and contribution process.

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
