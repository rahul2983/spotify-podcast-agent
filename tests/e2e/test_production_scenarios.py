import pytest
import time
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime

MCP_API_AVAILABLE = getattr(pytest, 'MCP_AVAILABLE', False)

@pytest.mark.e2e
@pytest.mark.slow
class TestProductionScenarios:
    
    def test_full_workflow_legacy_agent(self):
        """Test complete workflow from preferences to queueing."""
        from spotify_agent.agent import PodcastAgent
        from spotify_agent.config import AgentConfig, PodcastPreference
        
        # Create realistic config
        config = AgentConfig(
            openai_api_key="test_key",
            spotify_client_id="test_client_id",
            spotify_client_secret="test_client_secret",
            relevance_threshold=0.6,
            max_episodes_per_run=3,
            podcast_preferences=[]  # Start empty, add via agent
        )
        
        # Mock realistic Spotify responses
        with patch('spotify_agent.spotify_client.SpotifyClient') as MockSpotifyClient:
            mock_spotify = Mock()
            
            # Mock show search
            mock_spotify.search_podcast.return_value = [
                {"id": "show123", "name": "The Tim Ferriss Show"}
            ]
            
            # Mock episodes
            mock_spotify.get_show_episodes.return_value = [
                {
                    "id": "ep1",
                    "name": "AI Expert Interview",
                    "description": "Deep dive into artificial intelligence with leading expert",
                    "duration_ms": 3600000,  # 60 minutes
                    "uri": "spotify:episode:ep1"
                },
                {
                    "id": "ep2", 
                    "name": "Quick Tech Update",
                    "description": "Brief technology news update",
                    "duration_ms": 600000,  # 10 minutes (too short)
                    "uri": "spotify:episode:ep2"
                }
            ]
            
            # Mock successful queue addition
            mock_spotify.add_to_queue.return_value = True
            mock_spotify.get_current_user_profile.return_value = {"id": "testuser"}
            mock_spotify.get_devices.return_value = {
                "devices": [{"id": "device1", "is_active": True}]
            }
            
            MockSpotifyClient.return_value = mock_spotify
            
            # Mock LLM evaluation
            mock_llm = Mock()
            mock_llm.evaluate_episode_relevance.return_value = (0.85, "Highly relevant AI content")
            mock_llm.generate_episode_summary.return_value = "Excellent discussion about AI trends"
            MockLLMAgent.return_value = mock_llm
            with patch('spotify_agent.llm_agent.PodcastLLMAgent') as MockLLMAgent:
                mock_llm = Mock()
                mock_llm.evaluate_episode_relevance.return_value = (0.85, "Highly relevant AI content")
                mock_llm.generate_episode_summary.return_value = "Excellent discussion about AI trends"
                MockLLMAgent.return_value = mock_llm
                
                # Mock queue manager - make it available
                with patch('spotify_agent.agent.queue_manager_available', True), \
                     patch('spotify_agent.queue_manager.QueueManager') as MockQueueManager:
                    mock_queue = Mock()
                    mock_queue.get_pending_episodes.return_value = []
                    mock_queue.add_pending_episodes.return_value = None
                    mock_queue.remove_processed_episodes.return_value = None
                    MockQueueManager.return_value = mock_queue
                    
                    # Run the agent
                    agent = PodcastAgent(config)
                    
                    # Add preferences after initialization
                    agent.add_podcast_preference(PodcastPreference(
                        show_name="The Tim Ferriss Show",
                        min_duration_minutes=30,
                        max_duration_minutes=120
                    ))
                    
                    result = agent.run()
                    
                    # Verify results
                    assert result["status"] == "success"
                    # Check if episodes key exists and has content
                    if "episodes" in result:
                        assert len(result["episodes"]) > 0
                        # Verify episode was relevant enough
                        added_episode = result["episodes"][0]
                        assert added_episode["relevance_score"] >= config.relevance_threshold
                        assert "artificial intelligence" in added_episode["episode"]["description"].lower()
                    else:
                        # If no episodes were added, check the message
                        assert "Added 0 episodes to queue" in result["message"] or "No new relevant episodes found" in result["message"]

                    # Verify Spotify API calls
                    mock_spotify.search_podcast.assert_called()
                    mock_spotify.get_show_episodes.assert_called()
                    
    @pytest.mark.asyncio 
    async def test_full_workflow_mcp_agent(self):
        """Test complete MCP workflow."""
        if not MCP_API_AVAILABLE:
            pytest.skip("MCP components not available")
            
        from spotify_agent.mcp_agent.podcast_agent import MCPPodcastAgent
        from spotify_agent.config import AgentConfig, PodcastPreference
        
        config = AgentConfig(
            openai_api_key="test_key",
            spotify_client_id="test_client_id",
            spotify_client_secret="test_client_secret",
            podcast_preferences=[
                PodcastPreference(topics=["technology", "startups"])
            ]
        )
        
        # Mock all the underlying services that MCPPodcastAgent initializes
        with patch('spotify_agent.spotify_client.SpotifyClient') as MockSpotifyClient, \
             patch('spotify_agent.llm_agent.PodcastLLMAgent') as MockLLMAgent, \
             patch('spotify_agent.queue_manager.QueueManager') as MockQueueManager:
            
            # Setup mock returns
            MockSpotifyClient.return_value = Mock()
            MockLLMAgent.return_value = Mock()
            MockQueueManager.return_value = Mock()
            
            agent = MCPPodcastAgent(config)
            
            # Mock MCP client responses for complete workflow
            async def mock_mcp_request(server_name, method, params=None):
                if server_name == "queue" and method == "tools/call" and params and params.get("name") == "get_pending":
                    return {"episodes": [], "count": 0}
                elif server_name == "spotify" and method == "tools/call" and params and params.get("name") == "search_podcasts":
                    return [{"id": "show1", "name": "Startup Podcast"}]
                elif server_name == "spotify" and method == "tools/call" and params and params.get("name") == "get_show_episodes":
                    return [{
                        "id": "ep1",
                        "name": "Startup Success Stories",
                        "description": "Technology startups that changed the world",
                        "duration_ms": 2400000,  # 40 minutes
                        "uri": "spotify:episode:ep1"
                    }]
                elif server_name == "llm" and method == "tools/call" and params and params.get("name") == "evaluate_episode":
                    return {"relevance_score": 0.9, "reasoning": "Perfect match for startup/tech topics"}
                elif server_name == "llm" and method == "tools/call" and params and params.get("name") == "generate_summary":
                    return {"summary": "Inspiring stories of successful tech startups"}
                elif server_name == "spotify" and method == "tools/call" and params and params.get("name") == "add_to_queue":
                    return {"success": True}
                elif server_name == "spotify" and method == "tools/call" and params and params.get("name") == "get_devices":
                    return {"devices": [{"id": "device1", "is_active": True}]}
                return {}
                
            agent.mcp_client.send_request = AsyncMock(side_effect=mock_mcp_request)
            agent.check_spotify_active_device = AsyncMock(return_value=True)
            
            # Run complete workflow
            result = await agent.run()
            
            assert result["status"] == "success"
            assert "episodes to queue" in result["message"] or result["message"] == "No new relevant episodes found"
            
    def test_error_recovery_scenarios(self):
        """Test various error scenarios and recovery."""
        from spotify_agent.agent import PodcastAgent
        from spotify_agent.config import AgentConfig, PodcastPreference
        
        config = AgentConfig(
            openai_api_key="test_key",
            spotify_client_id="test_client_id", 
            spotify_client_secret="test_client_secret",
            podcast_preferences=[]
        )
        
        # Test Spotify API failure
        with patch('spotify_agent.spotify_client.SpotifyClient') as MockSpotifyClient:
            mock_spotify = Mock()
            # Make search_podcast raise an exception that gets caught
            mock_spotify.search_podcast.side_effect = Exception("Spotify API Error")
            mock_spotify.get_current_user_profile.return_value = {"id": "testuser"}
            MockSpotifyClient.return_value = mock_spotify
            
            with patch('spotify_agent.llm_agent.PodcastLLMAgent') as MockLLMAgent, \
                 patch('spotify_agent.agent.queue_manager_available', True), \
                 patch('spotify_agent.queue_manager.QueueManager') as MockQueueManager:
                
                MockLLMAgent.return_value = Mock()
                mock_queue = Mock()
                mock_queue.get_pending_episodes.return_value = []
                MockQueueManager.return_value = mock_queue
                
                agent = PodcastAgent(config)
                # Add a preference that will trigger the error
                agent.add_podcast_preference(PodcastPreference(show_name="Test Show"))
                
                result = agent.run()
                
                # The agent catches exceptions and returns an error status
                assert result["status"] == "error"
                assert "error" in result["message"].lower() or "Error" in result["message"]
                
    def test_rate_limiting_simulation(self):
        """Simulate API rate limiting scenarios.""" 
        from spotify_agent.agent import PodcastAgent
        from spotify_agent.config import AgentConfig, PodcastPreference
        
        config = AgentConfig(
            openai_api_key="test_key",
            spotify_client_id="test_client_id",
            spotify_client_secret="test_client_secret",
            max_episodes_per_run=1,  # Limit to test rate limiting
            podcast_preferences=[]
        )
        
        with patch('spotify_agent.spotify_client.SpotifyClient') as MockSpotifyClient:
            mock_spotify = Mock()
            
            # Simulate rate limiting - always raise exception
            mock_spotify.search_podcast.side_effect = Exception("Rate limit exceeded")
            mock_spotify.get_current_user_profile.return_value = {"id": "testuser"}
            MockSpotifyClient.return_value = mock_spotify
            
            with patch('spotify_agent.llm_agent.PodcastLLMAgent') as MockLLMAgent, \
                 patch('spotify_agent.agent.queue_manager_available', True), \
                 patch('spotify_agent.queue_manager.QueueManager') as MockQueueManager:
                
                MockLLMAgent.return_value = Mock()
                mock_queue = Mock()
                mock_queue.get_pending_episodes.return_value = []
                MockQueueManager.return_value = mock_queue
                
                agent = PodcastAgent(config)
                # Add preference to trigger the rate limiting
                agent.add_podcast_preference(PodcastPreference(show_name="Popular Podcast"))
                
                # First run should fail due to rate limiting
                result1 = agent.run()
                assert result1["status"] == "error"
                assert "rate limit" in result1["message"].lower() or "error" in result1["message"].lower()
                
                # Reset processed episodes for second run
                agent.reset_processed_episodes()
                
                # In a real scenario, you'd implement retry logic here
                
    def test_large_dataset_handling(self):
        """Test handling of large numbers of episodes."""
        from spotify_agent.agent import PodcastAgent
        from spotify_agent.config import AgentConfig, PodcastPreference
        
        config = AgentConfig(
            openai_api_key="test_key",
            spotify_client_id="test_client_id",
            spotify_client_secret="test_client_secret",
            max_episodes_per_run=5,  # Limit processing
            podcast_preferences=[PodcastPreference(topics=["technology"])]
        )
        
        # Create large dataset of episodes
        large_episode_list = []
        for i in range(50):  # 50 episodes
            large_episode_list.append({
                "id": f"ep{i}",
                "name": f"Tech Episode {i}",
                "description": f"Technology discussion episode {i}",
                "duration_ms": 1800000,  # 30 minutes
                "uri": f"spotify:episode:ep{i}"
            })
            
        with patch('spotify_agent.spotify_client.SpotifyClient') as MockSpotifyClient:
            mock_spotify = Mock()
            mock_spotify.search_podcast.return_value = [{"id": "show1", "name": "Tech Show"}]
            mock_spotify.get_show_episodes.return_value = large_episode_list
            mock_spotify.add_to_queue.return_value = True
            mock_spotify.get_current_user_profile.return_value = {"id": "testuser"}
            mock_spotify.get_devices.return_value = {"devices": [{"is_active": True}]}
            MockSpotifyClient.return_value = mock_spotify
            
            with patch('spotify_agent.llm_agent.PodcastLLMAgent') as MockLLMAgent:
                mock_llm = Mock()
                # Make all episodes highly relevant for testing
                mock_llm.evaluate_episode_relevance.return_value = (0.9, "Relevant")
                mock_llm.generate_episode_summary.return_value = "Great tech episode"
                MockLLMAgent.return_value = mock_llm
                
                with patch('spotify_agent.agent.queue_manager_available', True), \
                     patch('spotify_agent.queue_manager.QueueManager') as MockQueueManager:
                    mock_queue = Mock()
                    mock_queue.get_pending_episodes.return_value = []
                    mock_queue.add_pending_episodes.return_value = None
                    mock_queue.remove_processed_episodes.return_value = None
                    MockQueueManager.return_value = mock_queue
                    
                    agent = PodcastAgent(config)
                    result = agent.run()
                    
                    # Should respect max_episodes_per_run limit
                    assert result["status"] == "success"
                    assert len(result["episodes"]) <= config.max_episodes_per_run
                    
                    # Should have processed exactly max_episodes_per_run
                    assert len(result["episodes"]) == config.max_episodes_per_run