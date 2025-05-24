import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from spotify_agent.mcp_server.protocol import (
    MCPMessage, MCPMessageType, MCPResource, MCPTool, 
    MCPServer, MCPClient
)

@pytest.mark.unit
@pytest.mark.mcp
class TestMCPMessage:
    def test_request_message(self):
        msg = MCPMessage(
            type=MCPMessageType.REQUEST,
            id="123",
            method="test_method",
            params={"key": "value"}
        )
        assert msg.type == MCPMessageType.REQUEST
        assert msg.id == "123"
        assert msg.method == "test_method"
        assert msg.params == {"key": "value"}
        
    def test_response_message(self):
        msg = MCPMessage(
            type=MCPMessageType.RESPONSE,
            id="123",
            result={"data": "test"}
        )
        assert msg.type == MCPMessageType.RESPONSE
        assert msg.result == {"data": "test"}
        
    def test_error_message(self):
        msg = MCPMessage(
            type=MCPMessageType.ERROR,
            error={"code": -32603, "message": "Internal error"}
        )
        assert msg.type == MCPMessageType.ERROR
        assert msg.error["code"] == -32603

@pytest.mark.unit
@pytest.mark.mcp
class TestMCPResource:
    def test_resource_creation(self):
        resource = MCPResource(
            uri="test://resource",
            name="Test Resource",
            description="A test resource",
            mime_type="application/json"
        )
        assert resource.uri == "test://resource"
        assert resource.name == "Test Resource"
        assert resource.description == "A test resource"
        assert resource.mime_type == "application/json"

@pytest.mark.unit
@pytest.mark.mcp
class TestMCPTool:
    def test_tool_creation(self):
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            input_schema={
                "type": "object",
                "properties": {"param1": {"type": "string"}}
            }
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert "param1" in tool.input_schema["properties"]

@pytest.mark.unit
@pytest.mark.mcp
class TestMCPClient:
    def test_client_initialization(self):
        client = MCPClient()
        assert len(client.servers) == 0
        
    def test_register_server(self):
        client = MCPClient()
        mock_server = Mock()
        mock_server.name = "test_server"
        
        client.register_server("test_server", mock_server)
        assert "test_server" in client.servers
        assert client.servers["test_server"] == mock_server
        
    @pytest.mark.asyncio
    async def test_send_request_server_not_found(self):
        client = MCPClient()
        
        with pytest.raises(ValueError, match="Server unknown_server not found"):
            await client.send_request("unknown_server", "test_method")
            
    @pytest.mark.asyncio
    async def test_send_request_success(self):
        client = MCPClient()
        
        # Mock server
        mock_server = Mock()
        mock_response = MCPMessage(
            type=MCPMessageType.RESPONSE,
            result={"success": True}
        )
        mock_server.handle_request = AsyncMock(return_value=mock_response)
        
        client.register_server("test_server", mock_server)
        
        result = await client.send_request("test_server", "test_method", {"param": "value"})
        
        assert result == {"success": True}
        mock_server.handle_request.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_send_request_error_response(self):
        client = MCPClient()
        
        # Mock server with error response
        mock_server = Mock()
        mock_response = MCPMessage(
            type=MCPMessageType.ERROR,
            error={"code": -32603, "message": "Internal error"}
        )
        mock_server.handle_request = AsyncMock(return_value=mock_response)
        
        client.register_server("test_server", mock_server)
        
        with pytest.raises(Exception, match="MCP Error"):
            await client.send_request("test_server", "test_method")