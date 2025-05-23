"""
Updated main entry point for MCP-based Spotify Podcast Agent
"""
import os
import logging
import asyncio
from spotify_agent.config import AgentConfig, PodcastPreference
from spotify_agent.mcp_agent.podcast_agent import MCPPodcastAgent
from spotify_agent.mcp_api.api import start_api

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

async def start_agent_cli():
    """Start the MCP agent in CLI mode"""
    logger.info("Starting MCP Spotify Podcast Agent in CLI mode...")
    
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
        
        # Initialize MCP agent
        agent = MCPPodcastAgent(config)
        
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
        logger.info("Running MCP agent...")
        result = await agent.run()
        
        # Display results
        logger.info(f"MCP Agent run complete: {result['message']}")
        
        if result.get('episodes'):
            logger.info("Episodes processed:")
            for idx, episode_data in enumerate(result['episodes'], 1):
                episode = episode_data['episode']
                logger.info(f"{idx}. {episode['name']} - {episode_data['summary']}")
        
    except Exception as e:
        logger.error(f"Error in MCP agent CLI mode: {str(e)}")

def main():
    """Main entry point with support for MCP architecture"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MCP-based Spotify Podcast Agent')
    parser.add_argument('--mode', type=str, default='api', choices=['api', 'cli'],
                        help='Mode to run: api (default) or cli')
    parser.add_argument('--mcp-debug', action='store_true',
                        help='Enable MCP debugging output')
    
    args = parser.parse_args()
    
    if args.mcp_debug:
        logging.getLogger('mcp_server').setLevel(logging.DEBUG)
        logger.info("MCP debugging enabled")
    
    if args.mode == 'cli':
        asyncio.run(start_agent_cli())
    else:
        logger.info("Starting MCP Spotify Podcast Agent in API mode...")
        start_api()

if __name__ == "__main__":
    main()