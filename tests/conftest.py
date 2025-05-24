# tests/conftest.py
import pytest
import pytest_asyncio  # Add this import
import asyncio
import json
import os
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from spotify_agent.config import AgentConfig, PodcastPreference
from spotify_agent.spotify_client import SpotifyClient
from spotify_agent.llm_agent import PodcastLLMAgent
from spotify_agent.queue_manager import QueueManager

# Try to import MCP components with fallback
MCP_AVAILABLE = False
try:
    from spotify_agent.mcp_server.protocol import MCPClient
    from spotify_agent.mcp_server.spotify_server import SpotifyMCPServer
    from spotify_agent.mcp_server.llm_server import LLMMCPServer
    from spotify_agent.mcp_server.queue_server import QueueMCPServer
    from spotify_agent.mcp_agent.podcast_agent import MCPPodcastAgent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from spotify_agent.agent import PodcastAgent

# Make MCP_AVAILABLE available to tests
pytest.MCP_AVAILABLE = MCP_AVAILABLE

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """Create test configuration."""
    return AgentConfig(
        openai_api_key="test_openai_api_key",
        spotify_client_id="test_spotify_client_id",
        spotify_client_secret="test_spotify_client_secret",
        spotify_redirect_uri="http://localhost:8000/callback",
        check_frequency="daily",
        relevance_threshold=0.7,
        max_episodes_per_run=5,
        podcast_preferences=[
            PodcastPreference(
                show_name="Test Podcast",
                min_duration_minutes=10,
                max_duration_minutes=60
            ),
            PodcastPreference(
                topics=["technology", "AI"],
                min_duration_minutes=15
            )
        ]
    )

@pytest.fixture
def sample_episodes():
    """Load sample episode data."""
    return [
        {
            "id": "episode1",
            "name": "AI Revolution in 2024",
            "description": "Deep dive into artificial intelligence trends",
            "duration_ms": 3600000,  # 60 minutes
            "uri": "spotify:episode:episode1",
            "show": {"name": "Tech Talk", "id": "show1"}
        },
        {
            "id": "episode2", 
            "name": "Quick Tech News",
            "description": "Latest technology news roundup",
            "duration_ms": 900000,  # 15 minutes
            "uri": "spotify:episode:episode2",
            "show": {"name": "Daily Tech", "id": "show2"}
        }
    ]

@pytest.fixture
def mock_spotify_client():
    """Mock Spotify client with proper return values."""
    client = Mock(spec=SpotifyClient)
    client.search_podcast.return_value = [
        {"id": "show1", "name": "Test Podcast", "description": "Test description"}
    ]
    client.get_show_episodes.return_value = [
        {
            "id": "episode1",
            "name": "Test Episode",
            "description": "Test episode description",
            "duration_ms": 3600000,
            "uri": "spotify:episode:episode1"
        }
    ]
    client.add_to_queue.return_value = True
    client.get_devices.return_value = {
        "devices": [
            {"id": "device1", "name": "Test Device", "is_active": True}
        ]
    }
    client.get_current_user_profile.return_value = {
        "id": "testuser",
        "display_name": "Test User"
    }
    client.start_playback.return_value = True
    return client

@pytest.fixture
def mock_llm_agent():
    """Mock LLM agent."""
    agent = Mock(spec=PodcastLLMAgent)
    agent.evaluate_episode_relevance.return_value = (0.8, "Highly relevant to AI topics")
    agent.generate_episode_summary.return_value = "Great episode about AI trends"
    return agent

@pytest.fixture
def mock_queue_manager():
    """Mock queue manager with proper list return."""
    manager = Mock(spec=QueueManager)
    manager.get_pending_episodes.return_value = []  # Return empty list, not Mock
    manager.add_pending_episodes.return_value = None
    manager.remove_processed_episodes.return_value = None
    return manager

@pytest.fixture
def legacy_agent(test_config, mock_spotify_client, mock_llm_agent, mock_queue_manager):
    """Create legacy podcast agent with mocked dependencies."""
    with patch('spotify_agent.agent.SpotifyClient', return_value=mock_spotify_client), \
         patch('spotify_agent.agent.PodcastLLMAgent', return_value=mock_llm_agent), \
         patch('spotify_agent.agent.QueueManager', return_value=mock_queue_manager):
        return PodcastAgent(test_config)

# Fix the MCP agent fixture
@pytest_asyncio.fixture
async def mcp_agent(test_config, mock_spotify_client, mock_llm_agent, mock_queue_manager):
    """Create MCP podcast agent with mocked dependencies."""
    if not MCP_AVAILABLE:
        pytest.skip("MCP components not available")
    
    with patch('spotify_agent.mcp_agent.podcast_agent.SpotifyClient', return_value=mock_spotify_client), \
         patch('spotify_agent.mcp_agent.podcast_agent.PodcastLLMAgent', return_value=mock_llm_agent), \
         patch('spotify_agent.mcp_agent.podcast_agent.QueueManager', return_value=mock_queue_manager):
        agent = MCPPodcastAgent(test_config)
        return agent