# 🧪 MCP Server for Foundry Labs

This server exposes tools for Copilot to interact with projects from **MSR Foundry Labs**.

---

## 🛠 Tools Provided

- `get_azure_ai_foundry_projects_list`: Lists available projects from Foundry Labs.
- `get_implementation_details_for_labs_project`: Retrieves implementation guidance for a specific Labs project.

---

[![Use The Template](https://img.shields.io/badge/-Use%20this%20template-2ea44f?style=for-the-badge&logo=github)](https://github.com/tendau/foundrylabsagent/generate)

---

## 🚀 Getting Started

### ✅ Recommended (Codespaces)

1. Click the **"Use this template"** button above to create your own copy of the project.
2. Open your new repo in **GitHub Codespaces** — the servers will start automatically via the dev container.

---

### 🧑‍🔧 Manual Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/tendau/foundrylabsagent
   cd foundrylabsagent
   ```

2. Add the following entry to your MCP client (e.g., Copilot Labs) configuration:

   ```json
   {
     "Foundry Labs MCP": {
       "command": "uv",
       "args": [
         "--directory",
         "C:/Users/your-username/path/to/mcp-foundry/src/python",
         "run",
         "-m",
         "mcp_server_for_foundry_labs"
       ]
     }
   }
   ```

   > Adjust the path above to reflect your local environment.

---

## 💡 Notes

- This is a **stdio-based MCP server**.
- GitHub Copilot invokes it automatically once it detects tool availability.
