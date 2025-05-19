import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import dotenv
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import dotenv
import requests
from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from jinja2.sandbox import SandboxedEnvironment
from markupsafe import Markup
from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from jinja2.sandbox import SandboxedEnvironment
from markupsafe import Markup
from mcp.server.fastmcp import Context
from mcp_foundry.mcp_foundry_model.models import ModelsList

dotenv.load_dotenv()

logger = logging.getLogger("mcp_foundry")
logging.basicConfig(level=logging.DEBUG)

labs_api_url = os.environ.get("LABS_API_URL", "https://foundry-labs-mcp-api.azurewebsites.net/api/v1")

def get_client_headers_info(ctx):
    """Get client headers info."""
    client_info = getattr(
        getattr(ctx.session._client_params, "clientInfo", None), "__dict__", {}) or {}
    client_name = client_info.get("name", "UnknownClient").replace(" ", "-")
    client_version = client_info.get("version", "0.0.0")

    headers = {
        "User-Agent": f"MCP-Client/{client_name} - {client_version}"
    }
    return headers
 
def get_models_list(ctx: Context, search_for_free_playground: bool = False, publisher_name: str = "", license_name: str = "", 
                    max_pages: int = 10, model_name: str = "") -> ModelsList:
    """Get a list of all supported models from Azure AI Foundry with optional filters."""
    url = "https://api.catalog.azureml.ms/asset-gallery/v1.0/models"
    headers = get_client_headers_info(ctx)

    filters = []

    # Always include 'latest' label
    filters.append({"field": "labels", "values": ["latest"], "operator": "eq"})

    # Only add the freePlayground filter if the value is exactly True
    # If search_for_free_playground is False or None, do not add any filter for it
    if search_for_free_playground is True:
        filters.append({
            "field": "freePlayground",
            "values": ["true"],
            "operator": "eq"
        })

    if publisher_name is not None and publisher_name != "":
        filters.append({
            "field": "publisher",
            "values": [publisher_name],
            "operator": "contains"
        })

    if license_name is not None and license_name != "":
        filters.append({
            "field": "license",
            "values": [license_name],
            "operator": "contains"
        })

    if model_name is not None and model_name != "":
        filters.append({
            "field": "name",
            "values": [model_name],
            "operator": "eq"
        })

    body = {"filters": filters}
    logger.info(f"Request body: {body}")

    models_list = {"total_models_count": 0,
                   "fetched_models_count": 0, "summaries": []}

    page_count = 0

    try:
        while True and page_count < max_pages:
            page_count += 1
            try:
                response = requests.post(url, json=body, headers=headers)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Exception during POST request on page {page_count}: {e}")
                break
            try:
                res_json = response.json()
            except Exception as e:
                logger.error(f"Exception parsing JSON response on page {page_count}: {e}")
                break

            logger.info(f"### Page: {page_count}")
            # logger.debug(f"Response body: {res_json}")

            if "summaries" not in res_json:
                logger.warning(f"No 'summaries' in response on page {page_count}")
                break

            for summary in res_json["summaries"]:
                try:
                    summary["deployment_options"] = {
                        "openai": False,
                        "serverless_endpoint": False,
                        "managed_compute": False,
                        "free_playground": False,
                    }

                    if "playgroundLimits" in summary:
                        summary["deployment_options"]['free_playground'] = True

                    publisher = summary.get("publisher", "")
                    azureOffers = summary.get("azureOffers", [])
                    # Even if publisher and azureOffers are present, they can be None
                    # or empty, so we need to fall back to default values
                    if not publisher:
                        publisher = ""
                    if not azureOffers:
                        azureOffers = []

                    if publisher and publisher.lower() == "openai":
                        summary["deployment_options"]['openai'] = True
                    else:
                        if "standard-paygo" in azureOffers:
                            summary["deployment_options"]['serverless_endpoint'] = True
                        if "VM" in azureOffers or "VM-withSurcharge" in azureOffers:
                            summary["deployment_options"]['managed_compute'] = True
                except Exception as e:
                    logger.error(f"Exception processing summary on page {page_count}: {e}")
                    logger.error(f"publisher: {publisher}")
                    logger.error(f"azureOffers: {azureOffers}")
                    logger.error(f"Summary: {summary}")

            models_list["total_models_count"] = res_json.get("totalCount", 0)
            models_list["summaries"].extend(res_json["summaries"])

            # If there are no more pages, break the loop
            if not res_json.get("continuationToken", False):
                break

            # Update the body for the next request
            body["continuationToken"] = res_json.get("continuationToken")
    except Exception as e:
        logger.error(f"Exception in get_models_list main loop: {e}")

    models_list["fetched_models_count"] = len(models_list["summaries"])

    # logging the total models count and fetched models count
    logger.info(f"Total models count: {models_list['total_models_count']}")
    logger.info(f"Fetched models count: {models_list['fetched_models_count']}")

    try:
        return ModelsList(**models_list)
    except Exception as e:
        logger.error(f"Exception constructing ModelsList: {e}")
        return None

async def get_code_sample_for_github_model(publisher_name: str, model_name: str, ctx: Context) -> str:
    headers = get_client_headers_info(ctx)
    try:
        response = requests.get(f"{labs_api_url}/resources/resource/gh_guidance.md", headers=headers)
        if response.status_code != 200:
            return f"Error fetching projects from API: {response.status_code}"
        guidance = response.json()
        GH_GUIDANCE = guidance["resource"]["content"]
        guidance = GH_GUIDANCE.replace("{{inference_model_name}}", f"{publisher_name}/{model_name}")
        return guidance
    except Exception as e:
        logger.error(f"Exception in get_code_sample_for_github_model: {e}")
        return f"Exception: {e}"

async def get_code_sample_for_labs_model(model_name: str, ctx: Context) -> str:
    headers = get_client_headers_info(ctx)
    try:
        response = requests.get(f"{labs_api_url}/projects/{model_name}/implementation", headers=headers)
        if response.status_code != 200:
            return f"Error fetching projects from API: {response.status_code}"
        project_response = response.json()
        return project_response['project']
    except Exception as e:
        logger.error(f"Exception in get_code_sample_for_labs_model: {e}")
        return f"Exception: {e}"

def get_cognitiveservices_client(
    subscription_id: str,
) -> CognitiveServicesManagementClient:
    return CognitiveServicesManagementClient(
        credential=DefaultAzureCredential(), subscription_id=subscription_id
    )

def  get_code_sample_for_deployment_under_ai_services(model_name:str, inference_task: str, endpoint: str, deployment_name: str) -> Optional[str]:
    """Get a code snippet for a specific deployment.

    This function is used to get code examples and implementation instructions for deploying models in Azure AI Services, helping users understand how to integrate and use the models effectively in their applications.

    Args:
        deployment_name: The name of the deployment.
        model_name: The name of the model.
        endpoint_name: The Azure OpenAI endpoint.

    Returns:
        str: A rendered code snippet demonstrating usage of the deployment.
    """

    template_response = requests.get(
            f"https://ai.azure.com/modelcache/code2/oai-sdk-key-auth/en/{inference_task}-python-template.md",
        )

    if not template_response.ok:
        logger.error(f"Error fetching template: {template_response.status_code}")
        return None

    ejs_template = template_response.text
    try:
        model_template_config = (
            requests.get(
                f"https://ai.azure.com/modelcache/widgets/en/Serverless/azure-openai/{model_name}.json"
            )
        ).json()
    except Exception as e:
        logger.error(f"Error fetching model template config: {e}")
        return None

    naive_jinja2_template = re.sub(r"<%=\s+([\w\.]+)\s%>", r"{{ \1|e }}", ejs_template)

    env = SandboxedEnvironment()

    template = env.from_string(naive_jinja2_template)

    additionalParameters = {}

    if inference_task == "chat-completion":
        example_content = [
            history["content"]
            for history in model_template_config[0]["config"]["examples"][0]["chatHistory"]
        ]
        additionalParameters = {
            "example": {
                "example_1": example_content[0],
                "example_2": example_content[1],
                "example_3": example_content[2],
            },
        }
    elif inference_task == "embeddings":
        additionalParameters = {
            "example": {
                "input": Markup(', '.join(map(repr,model_template_config[0]["config"]["examples"][0]["jsonInput"]["input"])))
            }
        }

    return template.render(
        **{
            "endpointUrl": endpoint,
            "deploymentName": deployment_name,
            "modelName": model_name,
            **additionalParameters
        }
    )


async def get_ai_services_usage_list(ctx: Context) -> str:
    """
    Retrieves a list of usage examples for Azure AI Services.

    This function is used to get examples of how to use Azure AI Services, helping users understand the various applications and use cases for the services.

    Returns:
        str: A string containing the usage examples for Azure AI Services.
    """

    headers = get_client_headers_info(ctx)

    pass

def az(*args: str) -> dict:
    """Run azure-cli and return output

    :param str *args: The command line arguments to provide to git
    :returns: The standard output of the git command. Surrounding whitespace is removed
    :rtype: str
    """
    output = subprocess.run(
        [sys.executable, "-m", "azure.cli", *args, "-o", "json"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()

    return json.loads(output)

def deploy_inline_bicep_template(
    subscription_id: str, resource_group: str, bicep_template: str
):
    """Deploy a bicep template from a string"""
    with tempfile.NamedTemporaryFile(suffix=".bicep") as tmp:
        Path(tmp.name).write_text(bicep_template, encoding="utf-8")
        try:
            return az(
                "deployment",
                "group",
                "create",
                "--subscription",
                subscription_id,
                "--resource-group",
                resource_group,
                "--template-file",
                tmp.name,
            )
        except subprocess.CalledProcessError as e:
            logger.exception(e.stderr + e.stdout)
            raise