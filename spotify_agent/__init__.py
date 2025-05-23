"""
Spotify Podcast Agent

An agentic AI system that automatically discovers, evaluates, and queues 
podcast episodes in Spotify based on user preferences.

Now with MCP (Model Context Protocol) support for enhanced modularity.
"""

__version__ = "2.0.0"

# Legacy imports for backward compatibility
from .agent import PodcastAgent
from .config import AgentConfig, PodcastPreference
from .api import start_api as start_legacy_api

# New MCP imports
try:
    from .mcp_agent.podcast_agent import MCPPodcastAgent
    from .mcp_api.api import start_api as start_mcp_api
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Default to MCP if available, fallback to legacy
if MCP_AVAILABLE:
    from .mcp_api.api import start_api
    from .mcp_agent.podcast_agent import MCPPodcastAgent as DefaultAgent
else:
    from .api import start_api
    from .agent import PodcastAgent as DefaultAgent

__all__ = [
    'AgentConfig', 
    'PodcastPreference', 
    'PodcastAgent',  # Legacy
    'start_api',
    'start_legacy_api'
]

if MCP_AVAILABLE:
    __all__.extend(['MCPPodcastAgent', 'start_mcp_api'])