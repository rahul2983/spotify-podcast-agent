"""Mock MCP servers for testing."""
from unittest.mock import Mock, AsyncMock
from spotify_agent.mcp_server.protocol import MCPServer, MCPMessage, MCPMessageType

class MockMCPServer(MCPServer):
    """Mock MCP server for testing."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        super().__init__(name, version)
        self.handle_request = AsyncMock()
        self.list_resources = AsyncMock(return_value=[])
        self.list_tools = AsyncMock(return_value=[])
        
    async def _execute_tool(self, name: str, arguments: dict):
        return {"mock": "response", "tool": name, "args": arguments}

class MockSpotifyMCPServer(MockMCPServer):
    """Mock Spotify MCP server."""
    
    def __init__(self):
        super().__init__("spotify")
        
        # Mock tool responses
        async def handle_request_impl(message):
            if message.method == "tools/call":
                tool_name = message.params.get("name")