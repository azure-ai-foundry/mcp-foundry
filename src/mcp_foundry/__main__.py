import logging
import os
import sys
from argparse import ArgumentParser
from typing import Literal
from dotenv import load_dotenv

from mcp_foundry.logging_config import configure_utf8_logging
configure_utf8_logging()

logger = logging.getLogger(__name__)

from .mcp_server import mcp, auto_import_modules

def main() -> None:
    """Runs the MCP server"""

    parser = ArgumentParser(description="Start the MCP service with provided or default configuration.")

    parser.add_argument('--transport', required=False, default='stdio',
                        help='Transport protocol (sse | stdio | streamable-http) (default: stdio)')
    parser.add_argument('--envFile', required=False, default='.env',
                        help='Path to .env file (default: .env)')

    # Parse the application arguments
    args = parser.parse_args()

    # Retrieve the specified transport and environment file
    specified_transport: Literal["stdio", "sse", "streamable-http"] = args.transport
    mcp_env_file = args.envFile

    logger.info(f"Starting MCP server: Transport = {specified_transport}")

    # Check if envFile exists and load it
    if mcp_env_file and os.path.exists(mcp_env_file):
        load_dotenv(dotenv_path=mcp_env_file)
        logger.info(f"Environment variables loaded from {mcp_env_file}")
    else:
        logger.warning(f"Environment file '{mcp_env_file}' not found. Skipping environment loading.")

    # Run this on startup
    auto_import_modules("mcp_foundry", targets=["tools", "resources", "prompts"])
    mcp.run(transport=specified_transport)


if __name__ == "__main__":
    main()