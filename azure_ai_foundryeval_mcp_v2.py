import os
import sys
import json
import logging
import asyncio
import tempfile
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv
from datetime import datetime
import subprocess
import httpx
from jinja2.sandbox import SandboxedEnvironment
import re
import contextlib

# Azure Imports
from azure.identity import DefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import MessageRole, Agent, ConnectionType
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

# Azure AI Evaluation Imports
from azure.ai.evaluation import (
    # Text Evaluators
    GroundednessEvaluator,
    RelevanceEvaluator,
    CoherenceEvaluator,
    FluencyEvaluator,
    SimilarityEvaluator,
    RetrievalEvaluator,
    F1ScoreEvaluator,
    RougeScoreEvaluator,
    BleuScoreEvaluator,
    MeteorScoreEvaluator,
    ViolenceEvaluator,
    SexualEvaluator,
    SelfHarmEvaluator,
    HateUnfairnessEvaluator,
    IndirectAttackEvaluator,
    ProtectedMaterialEvaluator,
    UngroundedAttributesEvaluator,
    CodeVulnerabilityEvaluator,
    QAEvaluator,
    ContentSafetyEvaluator,
    evaluate,
    # Agent Evaluators
    IntentResolutionEvaluator,
    ToolCallAccuracyEvaluator,
    TaskAdherenceEvaluator,
    # Agent Converter
    AIAgentConverter
)

from mcp.server.fastmcp import FastMCP, Context

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("azure_ai_foundry_mcp")

# Configure PromptFlow logging to go to stderr
def configure_promptflow_logging():
    import logging
    promptflow_logger = logging.getLogger('promptflow')
    for handler in promptflow_logger.handlers:
        promptflow_logger.removeHandler(handler)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    promptflow_logger.addHandler(handler)
    promptflow_logger.propagate = False  # Don't propagate to root logger

# Call this function early in your script's execution
configure_promptflow_logging()

# Load environment variables
load_dotenv()

# Initialize MCP server
mcp = FastMCP(
    "azure-ai-foundry",
    description="MCP server for Azure AI Foundry Evaluation and Agent Service",
    dependencies=[
        "azure-identity", 
        "python-dotenv", 
        "azure-ai-projects", 
        "azure-ai-evaluation"
    ],
)

#######################
# CONFIGURATION SETUP #
#######################

# Initialize Azure AI project and Azure OpenAI connection with environment variables
try:
    # Sync credential for evaluations
    credential = DefaultAzureCredential()
    
    # Credentials for Azure AI project
    azure_ai_project = {
        "subscription_id": os.environ.get("AZURE_SUBSCRIPTION_ID"),
        "resource_group_name": os.environ.get("AZURE_RESOURCE_GROUP"),
        "project_name": os.environ.get("AZURE_PROJECT_NAME"),
    }
    
    # Azure OpenAI model configuration
    model_config = {
        "azure_endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT"),
        "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
        "azure_deployment": os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
        "api_version": os.environ.get("AZURE_OPENAI_API_VERSION"),
    }
    
    # Directory for evaluation data files
    eval_data_dir = os.environ.get("EVAL_DATA_DIR", ".")
    
    # Azure AI Agent configuration
    project_connection_string = os.environ.get("PROJECT_CONNECTION_STRING")
    default_agent_id = os.environ.get("DEFAULT_AGENT_ID")
    
    # Initialization flags
    evaluation_initialized = True
    if not all([azure_ai_project["subscription_id"], model_config["azure_endpoint"]]):
        evaluation_initialized = False
        logger.warning("Some evaluation credentials are missing, some evaluators may not work")
    
    agent_initialized = bool(project_connection_string)
    if not agent_initialized:
        logger.warning("PROJECT_CONNECTION_STRING is missing, agent features will not work")
    
except Exception as e:
    logger.error(f"Initialization error: {str(e)}")
    credential = None
    azure_ai_project = None
    model_config = None
    evaluation_initialized = False
    agent_initialized = False

# Global variables for agent client and cache
ai_client = None
agent_cache = {}

async def initialize_agent_client():
    """Initialize the Azure AI Agent client asynchronously."""
    global ai_client
    
    if not agent_initialized:
        return False
        
    try:
        async_credential = AsyncDefaultAzureCredential()
        ai_client = AIProjectClient.from_connection_string(
            credential=async_credential,
            conn_str=project_connection_string,
            user_agent="mcp-azure-ai-foundry",
        )
        return True
    except Exception as e:
        logger.error(f"Failed to initialize AIProjectClient: {str(e)}")
        return False

#######################
# EVALUATOR MAPPINGS  #
#######################

# Map evaluator names to classes for dynamic instantiation
text_evaluator_map = {
    "groundedness": GroundednessEvaluator,
    "relevance": RelevanceEvaluator,
    "coherence": CoherenceEvaluator,
    "fluency": FluencyEvaluator,
    "similarity": SimilarityEvaluator,
    "retrieval": RetrievalEvaluator,
    "f1": F1ScoreEvaluator,
    "rouge": RougeScoreEvaluator,
    "bleu": BleuScoreEvaluator,
    "meteor": MeteorScoreEvaluator,
    "violence": ViolenceEvaluator,
    "sexual": SexualEvaluator,
    "self_harm": SelfHarmEvaluator,
    "hate_unfairness": HateUnfairnessEvaluator,
    "indirect_attack": IndirectAttackEvaluator,
    "protected_material": ProtectedMaterialEvaluator,
    "ungrounded_attributes": UngroundedAttributesEvaluator,
    "code_vulnerability": CodeVulnerabilityEvaluator,
    "qa": QAEvaluator,
    "content_safety": ContentSafetyEvaluator
}

# Map agent evaluator names to classes
agent_evaluator_map = {
    "intent_resolution": IntentResolutionEvaluator,
    "tool_call_accuracy": ToolCallAccuracyEvaluator,
    "task_adherence": TaskAdherenceEvaluator
}

# Required parameters for each text evaluator
text_evaluator_requirements = {
    "groundedness": {"query": "Optional", "response": "Required", "context": "Required"},
    "relevance": {"query": "Required", "response": "Required"},
    "coherence": {"query": "Required", "response": "Required"},
    "fluency": {"response": "Required"},
    "similarity": {"query": "Required", "response": "Required", "ground_truth": "Required"},
    "retrieval": {"query": "Required", "context": "Required"},
    "f1": {"response": "Required", "ground_truth": "Required"},
    "rouge": {"response": "Required", "ground_truth": "Required"},
    "bleu": {"response": "Required", "ground_truth": "Required"},
    "meteor": {"response": "Required", "ground_truth": "Required"},
    "violence": {"query": "Required", "response": "Required"},
    "sexual": {"query": "Required", "response": "Required"},
    "self_harm": {"query": "Required", "response": "Required"},
    "hate_unfairness": {"query": "Required", "response": "Required"},
    "indirect_attack": {"query": "Required", "response": "Required", "context": "Required"},
    "protected_material": {"query": "Required", "response": "Required"},
    "ungrounded_attributes": {"query": "Required", "response": "Required", "context": "Required"},
    "code_vulnerability": {"query": "Required", "response": "Required"},
    "qa": {"query": "Required", "response": "Required", "context": "Required", "ground_truth": "Required"},
    "content_safety": {"query": "Required", "response": "Required"}
}

# Required parameters for each agent evaluator
agent_evaluator_requirements = {
    "intent_resolution": {
        "query": "Required (Union[str, list[Message]])",
        "response": "Required (Union[str, list[Message]])", 
        "tool_definitions": "Optional (list[ToolDefinition])"
    },
    "tool_call_accuracy": {
        "query": "Required (Union[str, list[Message]])",
        "response": "Optional (Union[str, list[Message]])",
        "tool_calls": "Optional (Union[dict, list[ToolCall]])",
        "tool_definitions": "Required (list[ToolDefinition])"
    },
    "task_adherence": {
        "query": "Required (Union[str, list[Message]])",
        "response": "Required (Union[str, list[Message]])",
        "tool_definitions": "Optional (list[ToolCall])"
    }
}

######################
# HELPER FUNCTIONS   #
######################

def create_text_evaluator(evaluator_name: str) -> Any:
    """Create and configure an appropriate text evaluator instance."""
    if evaluator_name not in text_evaluator_map:
        raise ValueError(f"Unknown text evaluator: {evaluator_name}")
    
    EvaluatorClass = text_evaluator_map[evaluator_name]
    
    # AI-assisted quality evaluators need a model
    if evaluator_name in ["groundedness", "relevance", "coherence", "fluency", "similarity"]:
        if not model_config or not all([model_config["azure_endpoint"], model_config["api_key"]]):
            raise ValueError(f"Model configuration required for {evaluator_name} evaluator")
        return EvaluatorClass(model_config)
    
    # AI-assisted risk and safety evaluators need Azure credentials
    elif evaluator_name in ["violence", "sexual", "self_harm", "hate_unfairness", 
                        "indirect_attack", "protected_material", "ungrounded_attributes", 
                        "code_vulnerability", "content_safety"]:
        if credential is None or azure_ai_project is None:
            raise ValueError(f"Azure credentials required for {evaluator_name} evaluator")
        return EvaluatorClass(credential=credential, azure_ai_project=azure_ai_project)
    
    # NLP evaluators don't need special configuration
    else:
        return EvaluatorClass()

def create_agent_evaluator(evaluator_name: str) -> Any:
    """Create and configure an appropriate agent evaluator instance."""
    if evaluator_name not in agent_evaluator_map:
        raise ValueError(f"Unknown agent evaluator: {evaluator_name}")
    
    if not model_config or not all([model_config["azure_endpoint"], model_config["api_key"]]):
        raise ValueError(f"Model configuration required for {evaluator_name} evaluator")
    
    EvaluatorClass = agent_evaluator_map[evaluator_name]
    return EvaluatorClass(model_config=model_config)

async def get_agent(agent_id: str) -> Agent:
    """Get an agent by ID with simple caching."""
    global agent_cache

    # Check cache first
    if agent_id in agent_cache:
        return agent_cache[agent_id]

    # Fetch agent if not in cache
    try:
        agent = await ai_client.agents.get_agent(agent_id=agent_id)
        agent_cache[agent_id] = agent
        return agent
    except Exception as e:
        logger.error(f"Agent retrieval failed - ID: {agent_id}, Error: {str(e)}")
        raise ValueError(f"Agent not found or inaccessible: {agent_id}")

async def query_agent(agent_id: str, query: str) -> Dict:
    """Query an Azure AI Agent and get the response with full thread/run data."""
    try:
        # Get agent (from cache or fetch it)
        agent = await get_agent(agent_id)

        # Always create a new thread
        thread = await ai_client.agents.create_thread()
        thread_id = thread.id

        # Add message to thread
        await ai_client.agents.create_message(
            thread_id=thread_id, role=MessageRole.USER, content=query
        )

        # Process the run
        run = await ai_client.agents.create_run(thread_id=thread_id, agent_id=agent_id)
        run_id = run.id

        # Poll until the run is complete
        while run.status in ["queued", "in_progress", "requires_action"]:
            await asyncio.sleep(1)  # Non-blocking sleep
            run = await ai_client.agents.get_run(thread_id=thread_id, run_id=run.id)

        if run.status == "failed":
            error_msg = f"Agent run failed: {run.last_error}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "thread_id": thread_id,
                "run_id": run_id,
                "result": f"Error: {error_msg}"
            }

        # Get the agent's response
        response_messages = await ai_client.agents.list_messages(thread_id=thread_id)
        response_message = response_messages.get_last_message_by_role(MessageRole.AGENT)

        result = ""
        citations = []

        if response_message:
            # Collect text content
            for text_message in response_message.text_messages:
                result += text_message.text.value + "\n"

            # Collect citations
            for annotation in response_message.url_citation_annotations:
                citation = (
                    f"[{annotation.url_citation.title}]({annotation.url_citation.url})"
                )
                if citation not in citations:
                    citations.append(citation)

        # Add citations if any
        if citations:
            result += "\n\n## Sources\n"
            for citation in citations:
                result += f"- {citation}\n"

        return {
            "success": True,
            "thread_id": thread_id,
            "run_id": run_id,
            "result": result.strip(),
            "citations": citations
        }

    except Exception as e:
        logger.error(f"Agent query failed - ID: {agent_id}, Error: {str(e)}")
        raise
    
def az(*args: str) -> dict:
    """Run azure-cli and return output with improved error handling"""
    cmd = [sys.executable, "-m", "azure.cli", *args, "-o", "json"]
    
    # Log the command that's about to be executed
    logger.warning(f"Attempting to run: {' '.join(cmd)}")
    
    try:
        # Run with full logging
        result = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            check=False  # Don't raise exception to see all errors
        )
        
        # Log the results
        logger.warning(f"Command exit code: {result.returncode}")
        logger.warning(f"Command stdout (first 100 chars): {result.stdout[:100] if result.stdout else 'Empty'}")
        logger.warning(f"Command stderr (first 100 chars): {result.stderr[:100] if result.stderr else 'Empty'}")
        
        if result.returncode != 0:
            # Command failed
            return {
                "error": "Command failed",
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        
        try:
            # Try to parse JSON
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError as json_err:
            # JSON parsing failed
            return {
                "error": f"Failed to parse JSON: {str(json_err)}",
                "raw_output": result.stdout[:500]  # First 500 chars for debugging
            }
            
    except Exception as e:
        # Catch all other exceptions
        logger.error(f"Exception executing command: {str(e)}")
        return {
            "error": f"Exception: {str(e)}",
            "type": type(e).__name__
        }

########################
# TEXT EVALUATION TOOLS #
########################

@mcp.tool()
def list_text_evaluators() -> List[str]:
    """
    Returns a list of available text evaluator names for evaluating text outputs.
    """
    return list(text_evaluator_map.keys())

@mcp.tool()
def list_agent_evaluators() -> List[str]:
    """
    Returns a list of available agent evaluator names for evaluating agent behaviors.
    """
    return list(agent_evaluator_map.keys())

@mcp.tool()
def get_text_evaluator_requirements(evaluator_name: str = None) -> Dict:
    """
    Get the required input fields for a specific text evaluator or all text evaluators.
    
    Parameters:
    - evaluator_name: Optional name of evaluator. If None, returns requirements for all evaluators.
    """
    if evaluator_name is not None:
        if evaluator_name not in text_evaluator_map:
            raise ValueError(f"Unknown evaluator {evaluator_name}")
        return {evaluator_name: text_evaluator_requirements[evaluator_name]}
    else:
        return text_evaluator_requirements

@mcp.tool()
def get_agent_evaluator_requirements(evaluator_name: str = None) -> Dict:
    """
    Get the required input fields for a specific agent evaluator or all agent evaluators.
    
    Parameters:
    - evaluator_name: Optional name of evaluator. If None, returns requirements for all evaluators.
    """
    if evaluator_name is not None:
        if evaluator_name not in agent_evaluator_map:
            raise ValueError(f"Unknown evaluator {evaluator_name}")
        return {evaluator_name: agent_evaluator_requirements[evaluator_name]}
    else:
        return agent_evaluator_requirements

@mcp.tool()
def run_text_eval(
    evaluator_names: Union[str, List[str]],  # Single evaluator name or list of evaluator names
    file_path: Optional[str] = None,  # Path to JSONL file 
    content: Optional[str] = None,  # JSONL content as a string (optional)
    include_studio_url: bool = True,  # Option to include studio URL in response
    return_row_results: bool = False  # Option to include detailed row results
) -> Dict:
    """
    Run one or multiple evaluators on a JSONL file or content string.
    
    Parameters:
    - evaluator_names: Either a single evaluator name (string) or a list of evaluator names
    - file_path: Path to a JSONL file to evaluate (preferred for efficiency)
    - content: JSONL content as a string (alternative if file_path not available)
    - include_studio_url: Whether to include the Azure AI studio URL in the response
    - return_row_results: Whether to include detailed row results (False by default for large datasets)
    """
    # Save original stdout so we can restore it later
    original_stdout = sys.stdout
    # Redirect stdout to stderr to prevent PromptFlow output from breaking MCP
    sys.stdout = sys.stderr
    
    # Heartbeat mechanism
    import threading
    import time

    # Set up a heartbeat mechanism to keep the connection alive
    heartbeat_active = True

    def send_heartbeats():
        count = 0
        while heartbeat_active:
            count += 1
            logger.info(f"Heartbeat {count} - Evaluation in progress...")
            # Print to stderr to keep connection alive
            print(f"Evaluation in progress... ({count * 15}s)", file=sys.stderr, flush=True)
            time.sleep(15)  # Send heartbeat every 15 seconds

    # Start heartbeat thread
    heartbeat_thread = threading.Thread(target=send_heartbeats, daemon=True)
    heartbeat_thread.start()
    
    try:
        if not evaluation_initialized:
            heartbeat_active = False  # Stop heartbeat
            return {"error": "Evaluation not initialized. Check environment variables."}
        
        # Validate inputs
        if content is None and file_path is None:
            heartbeat_active = False  # Stop heartbeat
            return {"error": "Either file_path or content must be provided"}
        
        # Convert single evaluator to list for unified processing
        if isinstance(evaluator_names, str):
            evaluator_names = [evaluator_names]
        
        # Validate evaluator names
        for name in evaluator_names:
            if name not in text_evaluator_map:
                heartbeat_active = False  # Stop heartbeat
                return {"error": f"Unknown evaluator: {name}"}
        
        # Variable to track if we need to clean up a temp file
        temp_file = None
        
        try:
            # Determine which input to use (prioritize file_path for efficiency)
            input_file = None
            if file_path:
                # Resolve file path
                if os.path.isfile(file_path):
                    input_file = file_path
                else:
                    # Check in data directory
                    data_dir = os.environ.get("EVAL_DATA_DIR", ".")
                    alternate_path = os.path.join(data_dir, file_path)
                    if os.path.isfile(alternate_path):
                        input_file = alternate_path
                    else:
                        heartbeat_active = False  # Stop heartbeat
                        return {"error": f"File not found: {file_path} (also checked in {data_dir})"}
                    
                # Count rows quickly using file iteration
                with open(input_file, 'r', encoding='utf-8') as f:
                    row_count = sum(1 for line in f if line.strip())
                    
            elif content:
                # Create temporary file for content string
                fd, temp_file = tempfile.mkstemp(suffix='.jsonl')
                os.close(fd)
                
                # Write content to temp file
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                input_file = temp_file
                row_count = content.count('\n') + (0 if content.endswith('\n') else 1)
                
            logger.info(f"Processing {row_count} rows for {len(evaluator_names)} evaluator(s)")
            
            # Prepare evaluators
            evaluators = {}
            eval_config = {}
            
            for name in evaluator_names:
                # Create evaluator instance
                evaluators[name] = create_text_evaluator(name)
                
                # Set up column mapping for this evaluator
                requirements = text_evaluator_requirements[name]
                column_mapping = {}
                for field, requirement in requirements.items():
                    if requirement == "Required":
                        column_mapping[field] = f"${{data.{field}}}"                
                eval_config[name] = {
                    "column_mapping": column_mapping
                }
            
            # Prepare evaluation args
            eval_args = {
                "data": input_file,
                "evaluators": evaluators,
                "evaluator_config": eval_config
            }
            
            # Add Azure AI project info if initialized
            if azure_ai_project and include_studio_url:
                eval_args["azure_ai_project"] = azure_ai_project
            
            # Run evaluation with additional stdout redirection for extra safety
            with contextlib.redirect_stdout(sys.stderr):
                result = evaluate(**eval_args)
            
            # Prepare response
            response = {
                "evaluators": evaluator_names,
                "row_count": row_count,
                "metrics": result.get("metrics", {})
            }
            
            # Only include detailed row results if explicitly requested
            if return_row_results:
                response["row_results"] = result.get("rows", [])
            
            # Include studio URL if available
            if include_studio_url and "studio_url" in result:
                response["studio_url"] = result.get("studio_url")
            heartbeat_active = False  # Stop heartbeat    
            return response
        
        except Exception as e:
            logger.error(f"Evaluation error: {str(e)}")
            heartbeat_active = False  # Stop heartbeat
            return {"error": str(e)}
        
        finally:
            # Clean up temp file if we created one
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
                
            # Make sure heartbeat is stopped
            heartbeat_active = False
    
    finally:
        # Always restore stdout, even if an exception occurs
        sys.stdout = original_stdout
        heartbeat_active = False

# Add this new helper function to format evaluation outputs
@mcp.tool()
def format_evaluation_report(evaluation_result: Dict) -> str:
    """
    Format evaluation results into a readable report with metrics and Studio URL.
    
    Parameters:
    - evaluation_result: The evaluation result dictionary from run_text_eval or agent_query_and_evaluate
    
    Returns a formatted report with metrics and Azure AI Studio URL if available
    """
    if "error" in evaluation_result:
        return f"❌ Evaluation Error: {evaluation_result['error']}"
    
    # Start the report
    report = ["# Evaluation Report\n"]
    
    # Add evaluator info
    evaluator = evaluation_result.get("evaluator")
    if evaluator:
        report.append(f"## Evaluator: {evaluator}\n")
    
    # Add metrics
    metrics = evaluation_result.get("metrics", {})
    if metrics:
        report.append("## Metrics\n")
        for metric_name, metric_value in metrics.items():
            # Format metric value based on type
            if isinstance(metric_value, (int, float)):
                formatted_value = f"{metric_value:.4f}" if isinstance(metric_value, float) else str(metric_value)
            else:
                formatted_value = str(metric_value)
                
            report.append(f"- **{metric_name}**: {formatted_value}")
        report.append("\n")
    
    # Add studio URL if available
    studio_url = evaluation_result.get("studio_url")
    if studio_url:
        report.append(f"## Azure AI Studio\n")
        report.append(f"📊 [View detailed evaluation results in Azure AI Studio]({studio_url})\n")
    
    # Return the formatted report
    return "\n".join(report)

@mcp.tool()
def run_agent_eval(
    evaluator_name: str,
    query: str,
    response: Optional[str] = None,
    tool_calls: Optional[str] = None,
    tool_definitions: Optional[str] = None
) -> Dict:
    """
    Run agent evaluation on agent data. Accepts both plain text and JSON strings.
    
    Parameters:
    - evaluator_name: Name of the agent evaluator to use (intent_resolution, tool_call_accuracy, task_adherence)
    - query: User query (plain text or JSON string)
    - response: Agent response (plain text or JSON string)
    - tool_calls: Optional tool calls data (JSON string)
    - tool_definitions: Optional tool definitions (JSON string)
    """
    if not evaluation_initialized:
        return {"error": "Evaluation not initialized. Check environment variables."}
        
    if evaluator_name not in agent_evaluator_map:
        raise ValueError(f"Unknown agent evaluator: {evaluator_name}")
    
    try:
        # Helper function to process inputs
        def process_input(input_str):
            if not input_str:
                return None
                
            # Check if it's already a valid JSON string
            try:
                # Try to parse as JSON
                return json.loads(input_str)
            except json.JSONDecodeError:
                # If not a JSON string, treat as plain text
                return input_str
        
        # Process inputs - handle both direct text and JSON strings
        query_data = process_input(query)
        response_data = process_input(response) if response else None
        tool_calls_data = process_input(tool_calls) if tool_calls else None
        tool_definitions_data = process_input(tool_definitions) if tool_definitions else None
        
        # If query/response are plain text, wrap them in the expected format
        if isinstance(query_data, str):
            query_data = {"content": query_data}
            
        if isinstance(response_data, str):
            response_data = {"content": response_data}
        
        # Create evaluator instance
        evaluator = create_agent_evaluator(evaluator_name)
        
        # Prepare kwargs for the evaluator
        kwargs = {"query": query_data}
        if response_data:
            kwargs["response"] = response_data
        if tool_calls_data:
            kwargs["tool_calls"] = tool_calls_data
        if tool_definitions_data:
            kwargs["tool_definitions"] = tool_definitions_data
        
        # Run evaluation
        result = evaluator(**kwargs)
        
        return {
            "evaluator": evaluator_name,
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Agent evaluation error: {str(e)}")
        return {"error": str(e)}

########################
# AGENT SERVICE TOOLS  #
########################

@mcp.tool()
async def list_agents() -> str:
    """List available agents in the Azure AI Agent Service."""
    if not agent_initialized:
        return "Error: Azure AI Agent service is not initialized. Check environment variables."
    
    if ai_client is None:
        await initialize_agent_client()
        if ai_client is None:
            return "Error: Failed to initialize Azure AI Agent client."

    try:
        agents = await ai_client.agents.list_agents()
        if not agents or not agents.data:
            return "No agents found in the Azure AI Agent Service."

        result = "## Available Azure AI Agents\n\n"
        for agent in agents.data:
            result += f"- **{agent.name}**: `{agent.id}`\n"

        if default_agent_id:
            result += f"\n**Default Agent ID**: `{default_agent_id}`"

        return result
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        return f"Error listing agents: {str(e)}"

@mcp.tool()
async def connect_agent(agent_id: str, query: str) -> Dict:
    """
    Connect to a specific Azure AI Agent and run a query.
    
    Parameters:
    - agent_id: ID of the agent to connect to
    - query: Text query to send to the agent
    
    Returns a dict with the agent's response and thread/run IDs for potential evaluation
    """
    if not agent_initialized:
        return {"error": "Azure AI Agent service is not initialized. Check environment variables."}
    
    if ai_client is None:
        await initialize_agent_client()
        if ai_client is None:
            return {"error": "Failed to initialize Azure AI Agent client."}

    try:
        response = await query_agent(agent_id, query)
        return response
    except Exception as e:
        logger.error(f"Error connecting to agent: {str(e)}")
        return {"error": f"Error connecting to agent: {str(e)}"}

@mcp.tool()
async def query_default_agent(query: str) -> Dict:
    """
    Send a query to the default configured Azure AI Agent.
    
    Parameters:
    - query: Text query to send to the default agent
    
    Returns a dict with the agent's response and thread/run IDs for potential evaluation
    """
    if not agent_initialized:
        return {"error": "Azure AI Agent service is not initialized. Check environment variables."}
    
    if not default_agent_id:
        return {"error": "No default agent configured. Set DEFAULT_AGENT_ID environment variable or use connect_agent tool."}
    
    if ai_client is None:
        await initialize_agent_client()
        if ai_client is None:
            return {"error": "Failed to initialize Azure AI Agent client."}

    try:
        response = await query_agent(default_agent_id, query)
        return response
    except Exception as e:
        logger.error(f"Error querying default agent: {str(e)}")
        return {"error": f"Error querying default agent: {str(e)}"}

if __name__ == "__main__":
    # Initialize agent client in the back
    if agent_initialized:
        asyncio.get_event_loop().run_until_complete(initialize_agent_client())
    
    # Log initialization status
    status = []
    if evaluation_initialized:
        status.append("evaluation")
    if agent_initialized and ai_client is not None:
        status.append("agent service")
        
    if status:
        logger.info(f"Azure AI Foundry MCP Server initialized with: {', '.join(status)}")
        print(f"Azure AI Foundry MCP Server initialized with: {', '.join(status)}", file=sys.stderr)
    else:
        logger.warning("Azure AI Foundry MCP Server initialized with limited functionality")
        print("Azure AI Foundry MCP Server initialized with limited functionality", file=sys.stderr)
    
    # Run with stdio transport
    mcp.run()