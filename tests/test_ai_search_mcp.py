from mcp_foundry_service import  FoundryMCP


def test_foundry_mcp_initialization():
    """
    Test that FoundryMCP can be instantiated and inherits from FastMCP.
    """
    name = "Test MCP"
    instructions = "Follow these instructions"
    settings = {"log_level": "DEBUG"}

    mcp = FoundryMCP(name=name, instructions=instructions, **settings)

    assert mcp.name == name
    assert mcp.instructions == instructions
    assert isinstance(mcp, FoundryMCP)