import os
import logging
import sys
import json
import requests
import yaml
import re
from typing import Dict, List, Any, Callable, Optional, Union
from urllib.parse import urljoin, quote
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_foundry_finetuning")

# Load environment variables
load_dotenv()

# Use consistent environment variable names following the codebase pattern
azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
api_key = os.environ.get("AZURE_OPENAI_API_KEY")

class HttpMethod(Enum):
    """HTTP methods supported by the API."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

@dataclass
class ToolInfo:
    """Information about a dynamically generated tool."""
    name: str
    operation_id: str
    method: str
    path: str
    description: str
    parameters: Dict[str, Any]
    tags: List[str]

class SwaggerToolGenerator:
    """
    Dynamically generates MCP tools from Swagger/OpenAPI specifications.
    Specifically optimized for Azure OpenAI APIs with proper error handling and validation.
    """
    def __init__(self, swagger_file_path: str):
        """
        Initialize the SwaggerToolGenerator with a YAML file.
        Args:
            swagger_file_path: Path to local swagger YAML file
        Raises:
            FileNotFoundError: If swagger file doesn't exist
            ValueError: If parsing fails
        """

        # Initialize registered_tools dictionary
        self.registered_tools = {}

        # Set instance attributes for Azure config
        self.api_key = api_key
        self.api_version = api_version
        self.azure_endpoint = azure_endpoint

        # Load and store the swagger YAML data
        self.swagger_data = self._load_yaml_file(swagger_file_path)
        # Set the base_url attribute
        self.base_url = self._extract_base_url()

        # Validate required Azure configuration
        if not all([self.api_key, self.api_version, self.azure_endpoint]):
            logger.warning(
                "Missing Azure OpenAI configuration. "
                "Ensure AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and AZURE_OPENAI_API_VERSION are set."
            )

    def _load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse YAML swagger specification.
        Args:
            file_path: Path to YAML file
        Returns:
            Parsed swagger specification as dictionary
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If parsing fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Swagger file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML file '{file_path}': {str(e)}")
        except Exception as e:
            raise ValueError(f"Error reading swagger file: {str(e)}")

    def _extract_base_url(self, config=None) -> str:
        azure_endpoint = self.azure_endpoint
        api_key = self.api_key
        
        # Ensure the endpoint doesn't have trailing slashes
        if azure_endpoint:
            azure_endpoint = azure_endpoint.rstrip('/')
        
        # OpenAPI 3.0 servers
        if "servers" in self.swagger_data and self.swagger_data["servers"]:
            server = self.swagger_data["servers"][0]
            url = server.get("url", "")

            # Handle variable substitution for Azure endpoints
            if "variables" in server:
                for var_name, var_info in server["variables"].items():
                    placeholder = f"{{{var_name}}}"
                    if placeholder in url:
                        if var_name == "azure_endpoint":
                            replacement = azure_endpoint or var_info.get("default", "")
                        else:
                            replacement = os.environ.get(var_name.upper(), var_info.get("default", ""))
                        url = url.replace(placeholder, replacement)

            if "{azure_endpoint}" in url:
                url = url.replace("{azure_endpoint}", azure_endpoint or "")

            return url.rstrip('/')

        elif "host" in self.swagger_data:
            scheme = self.swagger_data.get("schemes", ["https"])[0]
            host = self.swagger_data.get("host", "")
            base_path = self.swagger_data.get("basePath", "")
            return f"{scheme}://{host}{base_path}".rstrip('/')

        return azure_endpoint or "https://your-resource.openai.azure.com"


    def _resolve_reference(self, ref: str) -> Dict[str, Any]:
        if not ref.startswith("#/"):
            logger.warning(f"External references not supported: {ref}")
            return {}

        path_parts = ref[2:].split("/")
        result = self.swagger_data

        try:
            for part in path_parts:
                if isinstance(result, dict) and part in result:
                    result = result[part]
                else:
                    logger.warning(f"Reference not found: {ref}")
                    return {}
            return result
        except Exception as e:
            logger.error(f"Error resolving reference {ref}: {str(e)}")
            return {}

    def _build_parameter_schema(self, parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        properties = {}
        required = []

        for param in parameters:
            if "$ref" in param:
                param = self._resolve_reference(param["$ref"])
                if not param:
                    continue

            param_name = param.get("name", "")
            param_in = param.get("in", "")

            if param_name == "api-version":
                continue

            if param_in == "path":
                continue

            param_schema = param.get("schema", {})
            param_def = {
                "type": param_schema.get("type", "string"),
                "description": param.get("description", "")
            }

            for constraint in ["enum", "pattern", "minimum", "maximum"]:
                if constraint in param_schema:
                    param_def[constraint] = param_schema[constraint]

            if "example" in param:
                param_def["example"] = param["example"]
            elif "example" in param_schema:
                param_def["example"] = param_schema["example"]

            properties[param_name] = param_def

            if param.get("required", False):
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }

    def _create_tool_function(
        self, 
        path: str, 
        method: str, 
        operation: Dict[str, Any]
    ) -> Callable[[Any], str]:
        def tool_function(**kwargs) -> str:
            try:
                base_url = self._extract_base_url()

                if not all([self.api_key, self.api_version, base_url]):
                    return json.dumps({
                        "error": "Azure OpenAI configuration not properly set",
                        "required": ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_API_VERSION"]
                    })

                # Start with the base URL
                url = urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))
                
                path_params = {}
                query_params = {"api-version": api_version}
                headers = {
                    "api-key": self.api_key,
                    "Content-Type": "application/json"
                }
                body_params = {}

                # Process parameters
                for param in operation.get("parameters", []):
                    if "$ref" in param:
                        param = self._resolve_reference(param["$ref"])
                        if not param:
                            continue

                    param_name = param.get("name", "")
                    param_in = param.get("in", "")

                    if param_name in kwargs:
                        value = kwargs[param_name]

                        if param_in == "path":
                            path_params[param_name] = value
                        elif param_in == "query":
                            query_params[param_name] = value
                        elif param_in == "header":
                            headers[param_name] = str(value)
                        elif param_in == "body":
                            body_params = value

                # Replace path parameters in the URL
                for param_name, param_value in path_params.items():
                    placeholder = f"{{{param_name}}}"
                    if placeholder in url:
                        # Don't URL encode the path parameter value
                        url = url.replace(placeholder, str(param_value))

                # Log the final URL before making the request
                logger.info(f"Making {method.upper()} request to: {url}")
                if query_params:
                    logger.info(f"Query params: {query_params}")

                json_data = None
                if method.lower() in ["post", "put", "patch"]:
                    if not body_params:
                        body_params = {
                            k: v for k, v in kwargs.items()
                            if k not in path_params and k not in query_params
                        }
                    if body_params:
                        json_data = body_params

                response = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=query_params,
                    json=json_data,
                    timeout=30
                )

                if response.status_code >= 400:
                    error_body = {}
                    try:
                        error_body = response.json()
                    except:
                        error_body = {"message": response.text}

                    return json.dumps({
                        "error": f"HTTP {response.status_code}",
                        "status_code": response.status_code,
                        "message": error_body.get("error", {}).get("message", response.text),
                        "details": error_body
                    })

                try:
                    return json.dumps(response.json(), indent=2)
                except:
                    return json.dumps({
                        "content": response.text,
                        "status_code": response.status_code
                    })

            except Exception as e:
                logger.error(f"Error in tool function: {str(e)}")
                return json.dumps({
                    "error": "Unexpected error",
                    "message": str(e)
                })

        tool_function.__name__ = f"dynamic_{method}_{path.replace('/', '_')}"
        tool_function.__doc__ = operation.get("summary", f"Execute {method.upper()} {path}")

        return tool_function

    def generate_and_register_tools(self) -> Dict[str, Any]:
        results = {
            "api_info": {
                "title": self.swagger_data.get("info", {}).get("title", "Unknown API"),
                "version": self.swagger_data.get("info", {}).get("version", "1.0.0"),
                "description": self.swagger_data.get("info", {}).get("description", ""),
                "base_url": self.base_url
            },
            "registered_tools": [],
            "errors": []
        }

        paths = self.swagger_data.get("paths", {})

        if not paths:
            logger.warning("No paths found in swagger specification")
            results["errors"].append("No API paths found in specification")
            return results

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method in ["get", "post", "put", "patch", "delete"]:
                if method not in path_item:
                    continue

                operation = path_item[method]

                if operation.get("deprecated", False):
                    continue

                operation_id = operation.get("operationId", f"{method}_{path.replace('/', '_')}")
                clean_operation_id = re.sub(r'[^a-zA-Z0-9_]', '_', operation_id)
                clean_operation_id = re.sub(r'_+', '_', clean_operation_id).strip('_')

                try:
                    parameters = operation.get("parameters", [])
                    param_schema = self._build_parameter_schema(parameters)
                    tool_func = self._create_tool_function(path, method, operation)
                    description = operation.get("summary", f"Execute {method.upper()} {path}")
                    tool_info = ToolInfo(
                        name=clean_operation_id,
                        operation_id=operation_id,
                        method=method.upper(),
                        path=path,
                        description=description,
                        parameters=param_schema,
                        tags=operation.get("tags", [])
                    )
                    self.registered_tools[clean_operation_id] = {
                        "function": tool_func,
                        "info": tool_info
                    }
                    results["registered_tools"].append({
                        "name": tool_info.name,
                        "method": tool_info.method,
                        "path": tool_info.path,
                        "description": tool_info.description
                    })
                    logger.info(f"Registered tool: {clean_operation_id} ({method.upper()} {path})")
                except Exception as e:
                    error_msg = f"Failed to register {operation_id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

        logger.info(f"Tool registration complete: {len(results['registered_tools'])} registered")
        return results

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        if tool_name not in self.registered_tools:
            return json.dumps({
                "error": f"Tool '{tool_name}' not found",
                "hint": "Use list_dynamic_swagger_tools() to see all available tools"
            })
        tool_func = self.registered_tools[tool_name]["function"]
        return tool_func(**kwargs)

_swagger_generator: Optional[SwaggerToolGenerator] = None

def auto_register_swagger_tools():
    """
    Auto-register swagger tools from the YAML file specified in SWAGGER_PATH environment variable.
    This should be called after environment variables are loaded.
    """
    swagger_path = os.environ.get("SWAGGER_PATH", "").strip()

    if not swagger_path:
        logger.info("SWAGGER_PATH not set in .env file, skipping swagger tool registration")
        return

    swagger_path = os.path.expanduser(swagger_path)

    if not os.path.exists(swagger_path):
        logger.error(f"SWAGGER_PATH specified but file not found: {swagger_path}")
        return

    if not swagger_path.lower().endswith(('.yaml', '.yml')):
        logger.error(f"SWAGGER_PATH must point to a YAML file (.yaml or .yml), got: {swagger_path}")
        return

    logger.info(f"Registering swagger tools from: {swagger_path}")

    try:
        global _swagger_generator
        _swagger_generator = SwaggerToolGenerator(swagger_path)
        results = _swagger_generator.generate_and_register_tools()
        registered_count = len(results.get('registered_tools', []))
        if registered_count > 0:
            logger.info(f"✅ Successfully registered {registered_count} tools from {swagger_path}")
            if results.get('api_info'):
                api_info = results['api_info']
                logger.info(
                    f"   API: {api_info.get('title', 'Unknown')} "
                    f"v{api_info.get('version', 'Unknown')}"
                )
        else:
            logger.warning("No tools were registered from the swagger file")
    except Exception as e:
        logger.error(f"Failed to register swagger tools: {str(e)}")

def get_swagger_generator() -> Optional[SwaggerToolGenerator]:
    """Get the global swagger generator instance."""
    return _swagger_generator