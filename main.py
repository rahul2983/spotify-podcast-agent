import os
import logging
from spotify_agent.config import AgentConfig, PodcastPreference
from spotify_agent.agent import PodcastAgent
from spotify_agent.api import start_api

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

def start_agent_cli():
    """Start the agent in CLI mode - for testing or quick runs"""
    logger.info("Starting Spotify Podcast Agent in CLI mode...")
    
    # Check if .env exists
    if not os.path.exists(".env"):
        logger.error(
            ".env file not found. Please create a .env file with your API keys and Spotify credentials. "
            "See .env.example for required variables."
        )
        return
    
    try:
        # Load configuration
        config = AgentConfig()
        
        # Check if API keys are set
        if not config.openai_api_key or not config.spotify_client_id or not config.spotify_client_secret:
            logger.error(
                "API keys not found in .env file. Please set OPENAI_API_KEY, "
                "SPOTIFY_CLIENT_ID, and SPOTIFY_CLIENT_SECRET."
            )
            return
        
        # Initialize agent
        agent = PodcastAgent(config)
        
        # If no preferences are set, add some example ones
        if not config.podcast_preferences:
            logger.info("No podcast preferences found. Adding some examples...")
            
            # Example 1: Specific show by name
            agent.add_podcast_preference(PodcastPreference(
                show_name="The Tim Ferriss Show",
                min_duration_minutes=30,
                max_duration_minutes=120
            ))
            
            # Example 2: By topics
            agent.add_podcast_preference(PodcastPreference(
                topics=["artificial intelligence", "machine learning", "technology"],
                min_duration_minutes=20
            ))
            
            logger.info("Example preferences added.")
        
        # Run the agent
        logger.info("Running agent...")
        result = agent.run()
        
        # Display results
        logger.info(f"Agent run complete: {result['message']}")
        
        if result.get('episodes'):
            logger.info("Episodes added to queue:")
            for idx, episode_data in enumerate(result['episodes'], 1):
                episode = episode_data['episode']
                logger.info(f"{idx}. {episode['name']} - {episode_data['summary']}")
        
    except Exception as e:
        logger.error(f"Error in agent CLI mode: {str(e)}")

def main():
    """Main entry point with CLI arguments for different modes"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Spotify Podcast Agent')
    parser.add_argument('--mode', type=str, default='api', choices=['api', 'cli'],
                        help='Mode to run: api (default) or cli')
    
    args = parser.parse_args()
    
    if args.mode == 'cli':
        start_agent_cli()
    else:
        logger.info("Starting Spotify Podcast Agent in API mode...")
        start_api()

if __name__ == "__main__":
    main()