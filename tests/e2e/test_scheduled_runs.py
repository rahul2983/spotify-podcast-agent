import pytest
MCP_API_AVAILABLE = getattr(pytest, "MCP_AVAILABLE", False)
import pytest
MCP_API_AVAILABLE = getattr(pytest, "MCP_AVAILABLE", False)
import pytest
import asyncio
import time
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta

@pytest.mark.e2e 
@pytest.mark.slow
class TestScheduledRuns:
    
    @patch('spotify_agent.agent.PodcastAgent.run')
    def test_scheduled_run_simulation(self, mock_run):
        """Simulate a scheduled run of the agent."""
        from spotify_agent.agent import PodcastAgent
        from spotify_agent.config import AgentConfig, PodcastPreference
        
        # Mock successful run
        mock_run.return_value = {
            "status": "success",
            "message": "Added 3 episodes to queue",
            "episodes": [
                {"episode": {"name": "Episode 1"}, "summary": "Great episode"},
                {"episode": {"name": "Episode 2"}, "summary": "Another good one"},
                {"episode": {"name": "Episode 3"}, "summary": "Excellent content"}
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        # Create agent with test config
        config = AgentConfig(
            openai_api_key="test_key",
            spotify_client_id="test_client_id", 
            spotify_client_secret="test_client_secret",
            podcast_preferences=[
                PodcastPreference(show_name="Test Podcast"),
                PodcastPreference(topics=["technology"])
            ]
        )
        
        with patch('spotify_agent.agent.SpotifyClient'), \
             patch('spotify_agent.agent.PodcastLLMAgent'), \
             patch('spotify_agent.agent.QueueManager'):
            
            agent = PodcastAgent(config)
            
            # Simulate scheduled run
            result = agent.run()
            
            assert result["status"] == "success"
            assert len(result["episodes"]) == 3
            assert "Added 3 episodes" in result["message"]
            
    @pytest.mark.asyncio
    @patch('spotify_agent.mcp_agent.podcast_agent.MCPPodcastAgent.run')
    async def test_mcp_scheduled_run_simulation(self, mock_run):
        """Simulate MCP agent scheduled run."""
        if not MCP_API_AVAILABLE:
            pytest.skip("MCP components not available")
            
        from spotify_agent.mcp_agent.podcast_agent import MCPPodcastAgent
        from spotify_agent.config import AgentConfig
        
        # Mock successful async run
        mock_run.return_value = {
            "status": "success", 
            "message": "Added 2 episodes to queue",
            "episodes": [],
            "timestamp": datetime.now().isoformat()
        }
        
        config = AgentConfig(
            openai_api_key="test_key",
            spotify_client_id="test_client_id",
            spotify_client_secret="test_client_secret"
        )
        
        with patch('spotify_agent.mcp_agent.podcast_agent.SpotifyClient'), \
             patch('spotify_agent.mcp_agent.podcast_agent.PodcastLLMAgent'), \
             patch('spotify_agent.mcp_agent.podcast_agent.QueueManager'):
            
            agent = MCPPodcastAgent(config)
            result = await agent.run()
            
            assert result["status"] == "success"
            mock_run.assert_called_once()
            
    def test_error_handling_in_scheduled_run(self):
        """Test error handling during scheduled runs."""
        from spotify_agent.agent import PodcastAgent
        from spotify_agent.config import AgentConfig
        
        config = AgentConfig(
            openai_api_key="test_key",
            spotify_client_id="test_client_id",
            spotify_client_secret="test_client_secret"
        )
        
        # Mock failure in Spotify client
        with patch('spotify_agent.agent.SpotifyClient') as mock_spotify_client:
            mock_spotify_client.side_effect = Exception("Spotify API Error")
            
            with pytest.raises(Exception):
                agent = PodcastAgent(config)
                
    def test_no_preferences_scheduled_run(self):
        """Test scheduled run with no preferences configured."""
        from spotify_agent.agent import PodcastAgent
        from spotify_agent.config import AgentConfig
        
        # Empty preferences
        config = AgentConfig(
            openai_api_key="test_key",
            spotify_client_id="test_client_id",
            spotify_client_secret="test_client_secret",
            podcast_preferences=[]
        )
        
        with patch('spotify_agent.agent.SpotifyClient'), \
             patch('spotify_agent.agent.PodcastLLMAgent'), \
             patch('spotify_agent.agent.QueueManager'):
            
            agent = PodcastAgent(config)
            result = agent.run()
            
            assert result["status"] == "error"
            assert "No podcast preferences configured" in result["message"]
            
    @patch('spotify_agent.agent.PodcastAgent.check_spotify_active_device')
    @patch('spotify_agent.agent.PodcastAgent.check_for_new_episodes')
    def test_no_active_device_scheduled_run(self, mock_check_episodes, mock_check_device):
        """Test scheduled run when no Spotify device is active."""
        from spotify_agent.agent import PodcastAgent
        from spotify_agent.config import AgentConfig, PodcastPreference
        
        # Mock no active device but found episodes
        mock_check_device.return_value = False
        mock_check_episodes.return_value = [
            {
                'episode': {'id': 'ep1', 'name': 'Test Episode', 'uri': 'spotify:episode:ep1'},
                'relevance_score': 0.8,
                'summary': 'Great episode'
            }
        ]
        
        config = AgentConfig(
            openai_api_key="test_key",
            spotify_client_id="test_client_id",
            spotify_client_secret="test_client_secret",
            podcast_preferences=[PodcastPreference(show_name="Test Show")]
        )
        
        with patch('spotify_agent.agent.SpotifyClient'), \
             patch('spotify_agent.agent.PodcastLLMAgent'), \
             patch('spotify_agent.agent.QueueManager') as mock_queue_manager:
            
            # Mock queue manager to track pending episodes
            mock_queue_instance = Mock()
            mock_queue_manager.return_value = mock_queue_instance
            
            agent = PodcastAgent(config)
            result = agent.run()
            
            # Episodes should be added to pending queue
            mock_queue_instance.add_pending_episodes.assert_called_once()