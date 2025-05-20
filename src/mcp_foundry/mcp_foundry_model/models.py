from enum import Enum
from pydantic import BaseModel

class DeploymentOption(Enum):
    """
    Enum to represent the deployment options for a model in the MCP Foundry.
    """
    FREE_PLAYGROUND = "Free Playground"
    SERVERLESS_ENDPOINT = "Serverless Endpoint"
    OPENAI = "OpenAI"
    MANAGED_COMPUTE = "Managed Compute"
    LABS = "Labs"

class ModelsList(BaseModel):
    """
    Model to store the list of models in the MCP Foundry.
    """
    total_models_count: int
    fetched_models_count: int
    summaries: list[dict]

class ModelDetails(BaseModel):
    """
    Model to store the details of a model in the MCP Foundry.
    """
    details: dict
    code_sample_azure: str | dict | None
    code_sample_github: str | dict | None
    type: DeploymentOption
    link: str