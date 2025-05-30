from tool_usage_evals.multi_step import run_agent_turn
from pathlib import Path
from tool_usage_evals.mcp_handling import (
    mcp_session_context_manager,
    extract_tool_definitions,
    build_mcp_tool_caller,
)
import os
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AzureOpenAI

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
import openai
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
from tqdm import tqdm


retry_decorator = retry(
    retry=retry_if_exception_type(openai.RateLimitError),
    wait=wait_random_exponential(min=10, max=90),
    stop=stop_after_attempt(6),
    reraise=True,
)

load_dotenv()
MCP_SERVER_SCRIPT = Path(__file__).parent / "../src/mcp_foundry/__main__.py"


@pytest.fixture(scope="session")
def aoai_client() -> AzureOpenAI:
    """Azure OpenAI client"""
    token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    client = AzureOpenAI(
        azure_ad_token_provider=token_provider,
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    )
    return client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_client_lists_tools_using_pipx():
    server_params = StdioServerParameters(
        command="pipx",
        args=["run", "--no-cache", "--spec", "..", "run-azure-ai-foundry-mcp"],
    )

    async with stdio_client(server_params) as (stdio, write):
        async with ClientSession(stdio, write) as session:
            await session.initialize()
            response = await session.list_tools()
            tools = response.tools
            assert tools, "Expected at least one tool from the MCP server"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_client_message_1(aoai_client) -> None:
    """Test tool usage for a user message asking about foundry labs projects."""
    user_message = "What are the projects in Azure AI Foundry Labs?"
    async with mcp_session_context_manager("python", [str(MCP_SERVER_SCRIPT)]) as session:
        tools = await extract_tool_definitions(session)
        call_tool_fn = await build_mcp_tool_caller(session)

        result = await retry_decorator(run_agent_turn)(
            aoai_client=aoai_client,
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            tools=tools,
            call_tool_fn=call_tool_fn,
            user_message=user_message,
        )

        tool_call_names = [t.name for t in result.tool_calls]
        assert "list_azure_ai_foundry_labs_projects" in tool_call_names


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_client_message_2(aoai_client) -> None:
    """Test tool usage for a user message asking about prototyping with foundry labs projects."""
    user_message = "I want to prototype an app with Azure AI Foundry Labs. Where do I start?"
    async with mcp_session_context_manager("python", [str(MCP_SERVER_SCRIPT)]) as session:
        tools = await extract_tool_definitions(session)
        call_tool_fn = await build_mcp_tool_caller(session)

        result = await retry_decorator(run_agent_turn)(
            aoai_client=aoai_client,
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            tools=tools,
            call_tool_fn=call_tool_fn,
            user_message=user_message,
        )

        tool_call_names = [t.name for t in result.tool_calls]
        assert "get_prototyping_instructions_for_github_and_labs" in tool_call_names


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_client_message_3(aoai_client) -> None:
    """
    Test tool usage for a user message asking code/implementation details.
    Because of stochasticity of response (sometimes uses the prototyping tool or list-projects
    tool instead of intended code-samples tool), we do n repeated trials.
    """
    user_message = "Give me code and implementation details for the Aurora model."
    n_trials = 3
    async with mcp_session_context_manager("python", [str(MCP_SERVER_SCRIPT)]) as session:
        tools = await extract_tool_definitions(session)
        call_tool_fn = await build_mcp_tool_caller(session)

        results = []
        for trial in tqdm(range(n_trials)):
            result = await retry_decorator(run_agent_turn)(
                aoai_client=aoai_client,
                model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
                tools=tools,
                call_tool_fn=call_tool_fn,
                user_message=user_message,
            )
            results.append(result)

        all_tool_call_names = [[t.name for t in result.tool_calls] for result in results]

        n_found_correct_tool = sum(["get_model_details_and_code_samples" in names for names in all_tool_call_names])
        accuracy = n_found_correct_tool / n_trials

        assert accuracy > 0.5
