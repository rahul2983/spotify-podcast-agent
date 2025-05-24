import pytest
from unittest.mock import Mock, AsyncMock
from spotify_agent.mcp_server.spotify_server import SpotifyMCPServer
from spotify_agent.mcp_server.protocol import MCPMessage, MCPMessageType

@pytest.mark.unit
@pytest.mark.mcp
class TestSpotifyMCPServer:
    def test_server_initialization(self, mock_spotify_client):
        server = SpotifyMCPServer(mock_spotify_client)
        assert server.name == "spotify"
        assert server.version == "1.0.0"
        assert len(server.tools) > 0
        assert len(server.resources) > 0
        
    def test_tools_registration(self, mock_spotify_client):
        server = SpotifyMCPServer(mock_spotify_client)
        
        expected_tools = [
            "search_podcasts", "get_show_episodes", "add_to_queue",
            "get_devices", "start_playback"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in server.tools
            
    def test_resources_registration(self, mock_spotify_client):
        server = SpotifyMCPServer(mock_spotify_client)
        
        expected_resources = ["user_profile", "devices", "recently_played"]
        
        for resource_name in expected_resources:
            assert resource_name in server.resources
            
    @pytest.mark.asyncio
    async def test_handle_tools_list_request(self, mock_spotify_client):
        server = SpotifyMCPServer(mock_spotify_client)
        
        request = MCPMessage(
            type=MCPMessageType.REQUEST,
            method="tools/list"
        )
        
        response = await server.handle_request(request)
        
        assert response.type == MCPMessageType.RESPONSE
        assert "tools" in response.result
        assert len(response.result["tools"]) > 0
        
    @pytest.mark.asyncio
    async def test_handle_search_podcasts_tool(self, mock_spotify_client):
        server = SpotifyMCPServer(mock_spotify_client)
        
        request = MCPMessage(
            type=MCPMessageType.REQUEST,
            method="tools/call",
            params={
                "name": "search_podcasts",
                "arguments": {"query": "test", "limit": 3}
            }
        )
        
        response = await server.handle_request(request)
        
        assert response.type == MCPMessageType.RESPONSE
        mock_spotify_client.search_podcast.assert_called_once_with("test", 3)
        
    @pytest.mark.asyncio
    async def test_handle_add_to_queue_tool(self, mock_spotify_client):
        server = SpotifyMCPServer(mock_spotify_client)
        
        request = MCPMessage(
            type=MCPMessageType.REQUEST,
            method="tools/call",
            params={
                "name": "add_to_queue",
                "arguments": {"episode_uri": "spotify:episode:123"}
            }
        )
        
        response = await server.handle_request(request)
        
        assert response.type == MCPMessageType.RESPONSE
        assert response.result["success"] is True
        mock_spotify_client.add_to_queue.assert_called_once_with("spotify:episode:123")
        
    @pytest.mark.asyncio
    async def test_handle_unknown_method(self, mock_spotify_client):
        server = SpotifyMCPServer(mock_spotify_client)
        
        request = MCPMessage(
            type=MCPMessageType.REQUEST,
            method="unknown_method"
        )
        
        response = await server.handle_request(request)
        
        assert response.type == MCPMessageType.ERROR
        assert response.error["code"] == -32601
        
    @pytest.mark.asyncio
    async def test_read_user_profile_resource(self, mock_spotify_client):
        server = SpotifyMCPServer(mock_spotify_client)
        
        result = await server._read_resource("spotify://user/profile")
        
        mock_spotify_client.get_current_user_profile.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_read_unknown_resource(self, mock_spotify_client):
        server = SpotifyMCPServer(mock_spotify_client)
        
        with pytest.raises(ValueError, match="Unknown resource URI"):
            await server._read_resource("unknown://resource")