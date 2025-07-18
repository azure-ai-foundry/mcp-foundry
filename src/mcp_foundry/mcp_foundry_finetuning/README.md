
# Extending and Customizing Finetuning Tools in MCP Foundry

This comprehensive guide will help you extend the capabilities of the `mcp_foundry_finetuning` module by adding new tools. It covers both static MCP tools (Python functions) and dynamic tools generated from a Swagger/OpenAPI specification. You’ll also find troubleshooting tips, advanced usage, and best practices for robust tool development.

---

## 1. Adding Static MCP Tools (Python Functions)

Static tools are Python functions decorated with `@mcp.tool()` in `tools.py`. These are registered with the MCP server and can be called directly from the MCP client or other services. Static tools are ideal for custom logic, orchestration.

### Step-by-Step: Creating a Static Tool

1. **Navigate to the tools file:**
   - Open `src/mcp_foundry/mcp_foundry_finetuning/tools.py` in your editor.

2. **Define your function:**
   - Decorate your function with `@mcp.tool()`.
   - The first argument can be a `Context` object (from `mcp.server.fastmcp`).
   - Add any additional parameters your tool needs.

3. **Implement your logic:**
   - Use environment variables for configuration (see existing tools for examples).
   - You can make HTTP requests, call other Python functions, or interact with files.
   - Handle errors gracefully and log useful information for debugging.

4. **Return results:**
   - Return a JSON-serializable object or string. This ensures compatibility with the MCP server and clients.
   - If your tool returns complex data, use `json.dumps()` to serialize it.

#### Example: Adding a Simple Tool
```python
from mcp_foundry.mcp_server import mcp
from mcp.server.fastmcp import Context

@mcp.tool()
def my_new_tool(ctx: Context, param1: str) -> str:
    """
    Example tool that echoes the input parameter.
    """
    # Your logic here
    return f"Received: {param1}"
```

5. **Test your tool:**
   - Run the MCP server and use the client or test suite to call your new tool.
   - Check logs for errors or unexpected behavior.

## 2. Adding Dynamic Tools from Swagger/OpenAPI

Dynamic tools are generated automatically from the Swagger specification (`swagger.yaml`). The generator in `swagger.py` reads the spec and registers a tool for each operation. This is ideal for exposing REST API endpoints as MCP tools with minimal Python code.

### Step-by-Step: Creating a Dynamic Tool

1. **Edit the Swagger specification:**
   - Open `swagger.yaml` in the project root.
   - Add a new path and operation following the OpenAPI 3.0 format.
   - Each operation **must** have a unique `operationId` (this becomes the tool name).
   - Document parameters, request bodies, and responses clearly.

2. **(Optional) Add schemas:**
   - Define request/response schemas in the `components` section for better validation and documentation.

3. **Set the Swagger path:**
   - Ensure the `SWAGGER_PATH` environment variable is set to the path of your `swagger.yaml` file (found in `.env`).
   - Example: `SWAGGER_PATH=./swagger.yaml`

4. **Restart the MCP server:**
   - The dynamic tool will be auto-registered if the Swagger spec is valid.
   - Check logs for any errors during registration.

#### Example: Adding a Custom Endpoint
```yaml
paths:
  /openai/fine_tuning/jobs/my_custom:
    get:
      operationId: myCustomTool
      summary: My custom tool
      description: Does something custom
      responses:
        '200':
          description: Success
```

#### Example: Adding Parameters and Schemas
```yaml
paths:
  /openai/fine_tuning/jobs/{job_id}/custom:
    get:
      operationId: getCustomJobInfo
      summary: Get custom job info
      parameters:
        - name: job_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  info:
                    type: string
```

### How Dynamic Tools Work
- The generator in `swagger.py` parses the YAML and registers a tool for each operation.
- You can list all dynamic tools using the `list_dynamic_swagger_tools` MCP tool.
- Call a dynamic tool by its `operationId` using the `execute_dynamic_swagger_action` MCP tool, passing required parameters as needed.

#### Example: Calling a Dynamic Tool
```python
# Using the MCP client or another tool:
result = execute_dynamic_swagger_action(ctx, tool_name="myCustomTool")
```
NOTE: Dynamic tools can also be invoked by natural language prompts.

---

## 3. Troubleshooting and Advanced Usage

- **Tool not appearing?**  
  - Check that your function is decorated with `@mcp.tool()` (for static tools).
  - For dynamic tools, ensure your `swagger.yaml` is valid and `SWAGGER_PATH` is set correctly.
  - Restart the MCP server after changes.

- **Errors in logs?**
  - Look for missing environment variables, invalid YAML, or registration errors.
  - Use logging in your Python code to help debug issues.

- **Parameter issues?**
  - For dynamic tools, ensure all required parameters are defined in the Swagger spec and are passed when calling the tool.

- **Testing tools:**
  - Use the MCP client, test scripts, or unit tests to verify your tool’s behavior.
  - For dynamic tools, you can use the `list_dynamic_swagger_tools` tool to see all available endpoints and their parameters.

---

## 4. Best Practices

- **Use clear, unique `operationId`s** in Swagger for dynamic tools. This avoids naming collisions and makes tools easy to find.
- **Document parameters and responses** thoroughly in both Python and YAML.
- **Handle errors ** in both static and dynamic tools. Return helpful error messages and log details for debugging.
- **Keep your tools modular**. If logic is complex, break it into helper functions or modules.
- **Check logs** regularly for warnings or errors, especially after adding or modifying tools.

---

## 5. Useful References and Further Reading

- See `tools.py` for static tool examples and patterns.
- See `swagger.yaml` for dynamic tool definitions and OpenAPI structure.
- See `swagger.py` for the dynamic tool generator logic and advanced customization.
- [OpenAPI Specification](https://swagger.io/specification/)
- [Python logging documentation](https://docs.python.org/3/library/logging.html)

---