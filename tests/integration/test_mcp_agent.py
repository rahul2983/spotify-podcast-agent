import pytest
MCP_API_AVAILABLE = getattr(pytest, "MCP_AVAILABLE", False)
import pytest
MCP_API_AVAILABLE = getattr(pytest, "MCP_AVAILABLE", False)
import pytest
from unittest.mock import Mock, patch, AsyncMock
from spotify_agent.mcp_agent.podcast_agent import MCPPodcastAgent

@pytest.mark.integration
@pytest.mark.mcp
class TestMCPPodcastAgent:
    @pytest.mark.asyncio
    async def test_agent_initialization(self, test_config, mock_spotify_client, mock_llm_agent, mock_queue_manager):
        with patch('spotify_agent.mcp_agent.podcast_agent.SpotifyClient', return_value=mock_spotify_client), \
             patch('spotify_agent.mcp_agent.podcast_agent.PodcastLLMAgent', return_value=mock_llm_agent), \
             patch('spotify_agent.mcp_agent.podcast_agent.QueueManager', return_value=mock_queue_manager):
            
            agent = MCPPodcastAgent(test_config)
            
            assert agent.config == test_config
            assert len(agent.mcp_client.servers) == 3  # Spotify, LLM, Queue
            assert "spotify" in agent.mcp_client.servers
            assert "llm" in agent.mcp_client.servers
            assert "queue" in agent.mcp_client.servers
            
    @pytest.mark.asyncio
    async def test_check_for_new_episodes(self, mcp_agent, sample_episodes):
        # Mock MCP client responses
        mcp_agent.mcp_client.send_request = AsyncMock()
        
        # Mock Spotify server responses
        async def mock_send_request(server_name, method, params=None):
            if server_name == "spotify" and params and params.get("name") == "search_podcasts":
                return [{"id": "show1", "name": "Test Show"}]
            elif server_name == "spotify" and params and params.get("name") == "get_show_episodes":
                return sample_episodes
            elif server_name == "llm" and params and params.get("name") == "evaluate_episode":
                return {"relevance_score": 0.8, "reasoning": "Relevant episode"}
            elif server_name == "llm" and params and params.get("name") == "generate_summary":
                return {"summary": "Great episode about AI"}
            return {}
            
        mcp_agent.mcp_client.send_request.side_effect = mock_send_request
        
        relevant_episodes = await mcp_agent.check_for_new_episodes()
        
        assert len(relevant_episodes) > 0
        assert all(ep["relevance_score"] >= mcp_agent.config.relevance_threshold for ep in relevant_episodes)
        
    @pytest.mark.asyncio
    async def test_add_episodes_to_queue_with_active_device(self, mcp_agent, sample_episodes):
        # Mock active device check
        mcp_agent.check_spotify_active_device = AsyncMock(return_value=True)
        
        # Mock MCP client
        mcp_agent.mcp_client.send_request = AsyncMock(return_value={"success": True})
        
        episode_data = [{"episode": sample_episodes[0], "relevance_score": 0.8}]
        
        added_episodes = await mcp_agent.add_episodes_to_queue(episode_data)
        
        assert len(added_episodes) == 1
        assert added_episodes[0]["episode"]["id"] == "episode1"
        
    @pytest.mark.asyncio
    async def test_add_episodes_to_queue_no_active_device(self, mcp_agent, sample_episodes):
        # Mock no active device
        mcp_agent.check_spotify_active_device = AsyncMock(return_value=False)
        
        # Mock MCP client for queue operations
        mcp_agent.mcp_client.send_request = AsyncMock(return_value={"success": True})
        
        episode_data = [{"episode": sample_episodes[0], "relevance_score": 0.8}]
        
        added_episodes = await mcp_agent.add_episodes_to_queue(episode_data)
        
        # Should return empty list when no device, episodes go to pending
        assert len(added_episodes) == 0
        
        # Verify episodes were added to pending queue
        mcp_agent.mcp_client.send_request.assert_called_with(
            "queue", "tools/call",
            {"name": "add_pending", "arguments": {"episodes": episode_data}}
        )
        
    @pytest.mark.asyncio
    async def test_process_pending_episodes(self, mcp_agent, sample_episodes):
        # Mock pending episodes exist
        pending_episodes = [{"episode": sample_episodes[0], "added_at": "2024-01-01T08:00:00"}]
        
        # Mock MCP client responses
        async def mock_send_request(server_name, method, params=None):
            if server_name == "queue" and params and params.get("name") == "get_pending":
                return {"episodes": pending_episodes, "count": 1}
            elif server_name == "spotify" and params and params.get("name") == "add_to_queue":
                return {"success": True}
            elif server_name == "queue" and params and params.get("name") == "remove_processed":
                return {"success": True}
            return {}
            
        mcp_agent.mcp_client.send_request = AsyncMock(side_effect=mock_send_request)
        mcp_agent.check_spotify_active_device = AsyncMock(return_value=True)
        
        result = await mcp_agent.process_pending_episodes()
        
        assert result["status"] == "success"
        assert "1 of 1 pending episodes" in result["message"]
        assert len(result["episodes"]) == 1
        
    @pytest.mark.asyncio
    async def test_run_complete_workflow(self, mcp_agent, sample_episodes):
        # Mock complete workflow
        async def mock_send_request(server_name, method, params=None):
            if server_name == "queue" and params and params.get("name") == "get_pending":
                return {"episodes": [], "count": 0}
            elif server_name == "spotify" and params and params.get("name") == "search_podcasts":
                return [{"id": "show1", "name": "Test Show"}]
            elif server_name == "spotify" and params and params.get("name") == "get_show_episodes":
                return sample_episodes
            elif server_name == "llm" and params and params.get("name") == "evaluate_episode":
                return {"relevance_score": 0.8, "reasoning": "Relevant"}
            elif server_name == "llm" and params and params.get("name") == "generate_summary":
                return {"summary": "Great episode"}
            elif server_name == "spotify" and params and params.get("name") == "add_to_queue":
                return {"success": True}
            return {}
            
        mcp_agent.mcp_client.send_request = AsyncMock(side_effect=mock_send_request)
        mcp_agent.check_spotify_active_device = AsyncMock(return_value=True)
        
        result = await mcp_agent.run()
        
        assert result["status"] == "success"
        assert "episodes to queue" in result["message"]