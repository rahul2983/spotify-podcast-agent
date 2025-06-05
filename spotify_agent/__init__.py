"""
Spotify Podcast Agent

An agentic AI system that automatically discovers, evaluates, and queues 
podcast episodes in Spotify based on user preferences.

Now with MCP (Model Context Protocol) support for enhanced modularity.
"""

__version__ = "2.1.0"  # Updated version for enhanced features

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

# Enhanced features imports
try:
    from .mcp_agent.enhanced_podcast_agent import EnhancedMCPPodcastAgent
    from .mcp_server.email_server import EmailMCPServer
    from .mcp_server.calendar_server import CalendarMCPServer
    from .mcp_api.enhanced_api import start_api as start_enhanced_api
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False

# Default to enhanced if available, then MCP, then legacy
if ENHANCED_AVAILABLE:
    from .mcp_api.enhanced_api import start_api
    from .mcp_agent.enhanced_podcast_agent import EnhancedMCPPodcastAgent as DefaultAgent
elif MCP_AVAILABLE:
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

if ENHANCED_AVAILABLE:
    __all__.extend(['EnhancedMCPPodcastAgent', 'EmailMCPServer', 'CalendarMCPServer', 'start_enhanced_api'])