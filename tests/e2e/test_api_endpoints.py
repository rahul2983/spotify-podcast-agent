import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
import json

MCP_API_AVAILABLE = getattr(pytest, 'MCP_AVAILABLE', False)

# Try to import MCP API, fallback to legacy
try:
    from spotify_agent.mcp_api.api import app as mcp_app
    MCP_API_AVAILABLE = True
except ImportError:
    MCP_API_AVAILABLE = False

from spotify_agent.api import app as legacy_app

@pytest.mark.e2e
@pytest.mark.api
class TestAPIEndpoints:
    
    @pytest.fixture
    def legacy_client(self):
        """Test client for legacy API."""
        return TestClient(legacy_app)
        
    @pytest.fixture  
    def mcp_client(self):
        """Test client for MCP API."""
        if not MCP_API_AVAILABLE:
            pytest.skip("MCP API not available")
        return TestClient(mcp_app)
    
    def test_root_endpoint_legacy(self, legacy_client):
        response = legacy_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "Spotify Podcast Agent API is running" in data["message"]
        
    def test_root_endpoint_mcp(self, mcp_client):
        response = mcp_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["version"] == "2.0.0"
        assert data["message"] == "MCP Spotify Podcast Agent API is running"
        
    def test_preferences_get_empty(self, legacy_client):
        response = legacy_client.get("/preferences")
        assert response.status_code == 200
        data = response.json()
        assert "preferences" in data
        
    def test_preferences_post_valid(self, legacy_client):
        preference_data = {
            "show_name": "Test Podcast",
            "min_duration_minutes": 10,
            "max_duration_minutes": 60
        }
        
        response = legacy_client.post(
            "/preferences",
            headers={"Content-Type": "application/json"},
            json=preference_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["preference"]["show_name"] == "Test Podcast"
        
    def test_preferences_post_invalid(self, legacy_client):
        # Empty preference (should fail validation)
        response = legacy_client.post(
            "/preferences",
            headers={"Content-Type": "application/json"},
            json={}
        )
        
        # Update expectation to match actual behavior
        assert response.status_code == 400  # This should be 400, not 500
        data = response.json()
        assert "At least one of show_name, show_id, or topics must be provided" in str(data.get("detail", ""))
        
    def test_preferences_post_topics(self, legacy_client):
        preference_data = {
            "topics": ["technology", "artificial intelligence"],
            "min_duration_minutes": 15
        }
        
        response = legacy_client.post(
            "/preferences",
            headers={"Content-Type": "application/json"},
            json=preference_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "technology" in data["preference"]["topics"]
        
    @patch('spotify_agent.agent.PodcastAgent.run')
    def test_run_endpoint_legacy(self, mock_run, legacy_client):
        mock_run.return_value = {
            "status": "success",
            "message": "Added 2 episodes to queue",
            "episodes": []
        }
        
        response = legacy_client.post("/run")
        assert response.status_code == 200
        
    @patch('spotify_agent.agent.PodcastAgent.check_spotify_active_device')
    def test_status_endpoint_legacy(self, mock_check_device, legacy_client):
        mock_check_device.return_value = True
        
        response = legacy_client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["active_device"] is True
        
    def test_reset_episodes_endpoint(self, legacy_client):
        response = legacy_client.post("/reset-episodes")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Reset processed episodes" in data["message"]
        
    @pytest.mark.skipif(not MCP_API_AVAILABLE, reason="MCP API not available")
    def test_mcp_servers_endpoint(self, mcp_client):
        response = mcp_client.get("/mcp/servers")
        assert response.status_code == 200
        data = response.json()
        assert "servers" in data
        
        # Should have spotify, llm, and queue servers
        server_names = [server["name"] for server in data["servers"]]
        assert "spotify" in server_names
        assert "llm" in server_names  
        assert "queue" in server_names
        
    @pytest.mark.skipif(not MCP_API_AVAILABLE, reason="MCP API not available")
    @patch('spotify_agent.mcp_agent.podcast_agent.MCPPodcastAgent')
    def test_mcp_call_endpoint(self, mock_agent_class, mcp_client):
        # Mock MCP agent and client
        mock_agent = Mock()
        mock_mcp_client = Mock()
        mock_mcp_client.send_request = AsyncMock(return_value={"test": "result"})
        mock_agent.mcp_client = mock_mcp_client
        mock_agent_class.return_value = mock_agent
        
        call_data = {
            "server_name": "spotify",
            "tool_name": "search_podcasts", 
            "arguments": {"query": "test", "limit": 3}
        }
        
        response = mcp_client.post(
            "/mcp/call",
            json=call_data  # Use json instead of params
        )
        
        # Note: This test may need adjustment based on actual MCP API implementation
        # The exact behavior depends on how the MCP endpoints are implemented
        
    def test_concurrent_requests(self, legacy_client):
        """Test API can handle concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = legacy_client.get("/status")
            results.append(response.status_code)
            
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            
        # Start all threads
        for thread in threads:
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join()
            
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5