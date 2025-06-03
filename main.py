"""
Updated main entry point for MCP-based Spotify Podcast Agent with Enhanced Features
"""
import os
import logging
import asyncio
import argparse
import sys
import uvicorn
from spotify_agent.config import AgentConfig, PodcastPreference

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("podcast_agent.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Try to import enhanced features
try:
    from spotify_agent.mcp_agent.enhanced_podcast_agent import EnhancedMCPPodcastAgent
    from spotify_agent.mcp_api.enhanced_api import start_api as start_enhanced_api
    ENHANCED_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Enhanced features not available: {e}")
    ENHANCED_AVAILABLE = False

# Fallback to regular MCP
try:
    from spotify_agent.mcp_agent.podcast_agent import MCPPodcastAgent
    from spotify_agent.mcp_api.api import start_api as start_mcp_api
    MCP_AVAILABLE = True
except ImportError as e:
    logger.warning(f"MCP features not available: {e}")
    MCP_AVAILABLE = False

# Final fallback to legacy
from spotify_agent.api import start_api as start_legacy_api

async def start_agent_cli():
    """Start the agent in CLI mode"""
    logger.info("Starting Spotify Podcast Agent in CLI mode...")
    
    if not os.path.exists(".env"):
        logger.error(
            ".env file not found. Please create a .env file with your API keys and Spotify credentials."
        )
        return
    
    try:
        # Load configuration
        config = AgentConfig()
        
        # Check API keys
        if not config.openai_api_key or not config.spotify_client_id or not config.spotify_client_secret:
            logger.error(
                "API keys not found in .env file. Please set OPENAI_API_KEY, "
                "SPOTIFY_CLIENT_ID, and SPOTIFY_CLIENT_SECRET."
            )
            return
        
        # Choose best available agent
        if ENHANCED_AVAILABLE:
            agent = EnhancedMCPPodcastAgent(config)
            logger.info("Using Enhanced MCP Agent")
        elif MCP_AVAILABLE:
            agent = MCPPodcastAgent(config)
            logger.info("Using MCP Agent")
        else:
            from spotify_agent.agent import PodcastAgent
            agent = PodcastAgent(config)
            logger.info("Using Legacy Agent")
        
        # Add example preferences if none exist
        if not config.podcast_preferences:
            logger.info("No podcast preferences found. Adding examples...")
            
            agent.add_podcast_preference(PodcastPreference(
                show_name="The Tim Ferriss Show",
                min_duration_minutes=30,
                max_duration_minutes=120
            ))
            
            agent.add_podcast_preference(PodcastPreference(
                topics=["artificial intelligence", "machine learning", "technology"],
                min_duration_minutes=20
            ))
            
            logger.info("Example preferences added.")
        
        # Run the agent
        logger.info("Running agent...")
        if ENHANCED_AVAILABLE:
            result = await agent.run(send_email_summary=True)
        elif MCP_AVAILABLE:
            result = await agent.run()
        else:
            result = agent.run()
        
        # Display results
        logger.info(f"Agent run complete: {result['message']}")
        
        if result.get('episodes'):
            logger.info("Episodes processed:")
            for idx, episode_data in enumerate(result['episodes'], 1):
                episode = episode_data['episode']
                logger.info(f"{idx}. {episode['name']} - {episode_data.get('summary', 'No summary')}")
        
    except Exception as e:
        logger.error(f"Error in agent CLI mode: {str(e)}")

def main():
    """Main entry point with support for enhanced MCP architecture"""
    parser = argparse.ArgumentParser(description='MCP-based Spotify Podcast Agent')
    parser.add_argument('--mode', type=str, default='api', choices=['api', 'cli', 'enhanced', 'legacy'],
                        help='Mode to run: api (default), cli, enhanced, or legacy')
    parser.add_argument('--mcp-debug', action='store_true',
                        help='Enable MCP debugging output')
    parser.add_argument('--enhanced', action='store_true',
                        help='Force enhanced features')
    
    args = parser.parse_args()
    
    if args.mcp_debug:
        logging.getLogger('mcp_server').setLevel(logging.DEBUG)
        logger.info("MCP debugging enabled")
    
    if args.mode == 'cli':
        asyncio.run(start_agent_cli())
    elif args.mode == 'enhanced' or args.enhanced:
        if ENHANCED_AVAILABLE:
            logger.info("Starting Enhanced MCP Spotify Podcast Agent...")
            start_enhanced_api()
        else:
            logger.error("Enhanced features not available. Falling back to regular MCP.")
            if MCP_AVAILABLE:
                start_mcp_api()
            else:
                start_legacy_api()
    elif args.mode == 'legacy':
        logger.info("Starting Legacy Spotify Podcast Agent...")
        start_legacy_api()
    else:
        # Default API mode - use best available
        if ENHANCED_AVAILABLE:
            logger.info("Starting Enhanced MCP Spotify Podcast Agent in API mode...")
            start_enhanced_api()
        elif MCP_AVAILABLE:
            logger.info("Starting MCP Spotify Podcast Agent in API mode...")
            start_mcp_api()
        else:
            logger.info("Starting Legacy Spotify Podcast Agent in API mode...")
            start_legacy_api()

if __name__ == "__main__":
    # Check if running in Heroku
    if os.getenv("PORT"):
        # Heroku deployment - start enhanced API directly
        port = int(os.getenv("PORT"))
        logger.info(f"Starting on Heroku port {port}")
        
        if ENHANCED_AVAILABLE:
            from spotify_agent.mcp_api.enhanced_api import app
            uvicorn.run(app, host="0.0.0.0", port=port)
        elif MCP_AVAILABLE:
            from spotify_agent.mcp_api.api import app
            uvicorn.run(app, host="0.0.0.0", port=port)
        else:
            from spotify_agent.api import app
            uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        # Local development
        main()