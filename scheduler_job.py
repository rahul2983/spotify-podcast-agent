#!/usr/bin/env python3
"""
Heroku Scheduler Job for Spotify Podcast Agent
Runs the agent automatically on schedule
"""
import os
import sys
import asyncio
import logging
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spotify_agent.config import AgentConfig
from spotify_agent.mcp_agent.podcast_agent import MCPPodcastAgent

# Configure logging for scheduler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - SCHEDULER - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

async def run_scheduled_agent():
    """Run the podcast agent as a scheduled job"""
    try:
        logger.info("🕒 Starting scheduled podcast agent run...")
        
        # Initialize configuration
        config = AgentConfig()
        
        # Check if we have preferences configured
        if not config.podcast_preferences:
            logger.warning("⚠️ No podcast preferences configured - skipping run")
            return
        
        # Initialize MCP agent
        agent = MCPPodcastAgent(config)
        logger.info(f"✅ Agent initialized with {len(config.podcast_preferences)} preferences")
        
        # Run the agent
        result = await agent.run()
        
        # Log results
        if result["status"] == "success":
            if result.get("episodes"):
                episode_count = len(result["episodes"])
                logger.info(f"🎵 Successfully added {episode_count} episodes to queue")
                
                # Log episode details
                for i, episode_data in enumerate(result["episodes"], 1):
                    episode = episode_data["episode"]
                    score = episode_data.get("relevance_score", 0)
                    logger.info(f"  {i}. {episode.get('name', 'Unknown')} (score: {score:.2f})")
            else:
                logger.info("ℹ️ No new relevant episodes found this run")
        else:
            logger.error(f"❌ Agent run failed: {result.get('message', 'Unknown error')}")
        
        # Process any pending episodes
        logger.info("🔄 Processing any pending episodes...")
        pending_result = await agent.process_pending_episodes()
        
        if pending_result["status"] == "success" and pending_result.get("episodes"):
            pending_count = len(pending_result["episodes"])
            logger.info(f"✅ Processed {pending_count} pending episodes")
        
        logger.info("🏁 Scheduled agent run completed successfully")
        
    except Exception as e:
        logger.error(f"💥 Error in scheduled agent run: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def main():
    """Main entry point for scheduler"""
    logger.info("="*50)
    logger.info(f"🚀 SCHEDULED RUN STARTED - {datetime.now().isoformat()}")
    logger.info("="*50)
    
    # Check required environment variables
    required_vars = ['OPENAI_API_KEY', 'SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'SPOTIFY_REDIRECT_URI']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        sys.exit(1)
    
    try:
        # Run the async agent
        asyncio.run(run_scheduled_agent())
        logger.info("✅ Scheduled job completed successfully")
    except Exception as e:
        logger.error(f"💥 Scheduled job failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()