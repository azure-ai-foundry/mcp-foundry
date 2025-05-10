from typing import Any, Literal

from mcp.server.fastmcp.server import FastMCP

LoggingLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

class FoundryMCP(FastMCP):
    """
    Custom implementation of the FastMCP class for Foundry-specific behavior.

    This class extends the base `FastMCP` to allow for potential future overrides
    or enhancements specific to the Foundry context. Currently, it inherits all
    behavior from `FastMCP` without modification, but serves as an extension point.
    """

    def __init__(self, name: str | None = None, instructions: str | None = None, **settings: Any):
        """
        Initializes the FoundryMCP instance.

        Args:
            name (str | None): Optional name of the MCP instance.
            instructions (str | None): Optional instructions or description of the MCP's purpose.
            **settings (Any): Additional keyword arguments passed to the base FastMCP initializer.

        Notes:
            This constructor currently delegates all behavior to the parent FastMCP class.
            Future enhancements specific to Foundry can be implemented here.
        """
        super().__init__(name=name, instructions=instructions, **settings)
