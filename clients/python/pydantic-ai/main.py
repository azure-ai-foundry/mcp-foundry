import os
from typing import Sequence

from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from pydantic_ai import Agent
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.mcp import MCPServerHTTP, MCPServer
from pydantic_ai.messages import ModelRequest, ModelResponse
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from rich.prompt import Prompt

mcp_env_file: str = '.env'

if mcp_env_file and os.path.exists(mcp_env_file):
    load_dotenv(dotenv_path=mcp_env_file)
    print(f"Environment variables loaded from {mcp_env_file}")
else:
    print(f"Env file '{mcp_env_file}' not found. Skipping environment loading.")

# Run the program as:
# uv run main.py

# These MCP servers have to be running in SSE mode before you start this Python program

# Tools for Azure AI Search Operations
ai_search_mcp_server = MCPServerHTTP(url='http://127.0.0.1:8000/sse')

my_mcp_servers: Sequence[MCPServer] = [ai_search_mcp_server]

# This is the OpenAI model name
model_name = 'gpt-4o-mini'

client = AsyncAzureOpenAI()
model = OpenAIModel(model_name, provider=OpenAIProvider(openai_client=client))
agent = Agent(model, mcp_servers=my_mcp_servers)


global_message = """
Hello AI Search Developer,
I am a helpful assistant and I can answer questions about Contoso Groceries - an online grocery service where shopping is a pleasure. 
I have access to the AI Search Index for Contoso Groceries and can help developers interact with the data and resources in the AI Search service.
Please let me know how I can help you. 
Ask me to show you what tools I have available to support your development efforts. If you forget the tools, please ask me again.

"""
prompt = """
How can I help you?"""

print(global_message)


async def main():
    async with agent.run_mcp_servers():

        message_history: list[ModelRequest | ModelResponse] = []

        while True:
            # Prompt the user for input
            # and send it to the agent for processing
            # Use rich prompt for better user experience
            question = Prompt.ask(prompt)
            result: AgentRunResult = await agent.run(question, message_history=message_history)

            latest_message_history:  list[ModelRequest | ModelResponse]  = result.all_messages()

            message_history = latest_message_history

            print(result.output)

if __name__ == '__main__':
    import asyncio
    import sys
    asyncio.run(main())