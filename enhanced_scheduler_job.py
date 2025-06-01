#!/usr/bin/env python3
"""
Enhanced Heroku Scheduler Job for Spotify Podcast Agent
Now with email summaries and calendar integration
"""
import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
import traceback

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spotify_agent.config import AgentConfig, PodcastPreference
from spotify_agent.mcp_agent.enhanced_podcast_agent import EnhancedMCPPodcastAgent

# Configure comprehensive logging for scheduler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - SCHEDULER - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'OPENAI_API_KEY', 
        'SPOTIFY_CLIENT_ID', 
        'SPOTIFY_CLIENT_SECRET', 
        'SPOTIFY_REDIRECT_URI'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    # Check optional email variables
    email_vars = ['SMTP_USERNAME', 'SMTP_PASSWORD', 'USER_EMAIL']
    email_configured = all(os.getenv(var) for var in email_vars)
    
    if email_configured:
        logger.info("✅ Email notifications configured")
    else:
        logger.info("ℹ️  Email notifications not configured (optional)")
    
    return True

async def run_scheduled_agent():
    """Run the enhanced podcast agent as a scheduled job"""
    run_start_time = datetime.now()
    
    try:
        logger.info("🚀 Starting enhanced scheduled podcast agent run...")
        
        # Check environment
        if not check_environment():
            logger.error("❌ Environment check failed")
            return
        
        # Initialize configuration
        config = AgentConfig()
        
        # Add user email if configured
        user_email = os.getenv('USER_EMAIL')
        if user_email:
            config.user_email = user_email
            logger.info(f"📧 Email notifications will be sent to: {user_email}")
        
        # Check if we have preferences configured
        if not config.podcast_preferences:
            logger.warning("⚠️ No podcast preferences configured - adding default examples")
            
            # Add some default preferences for first-time users
            default_preferences = [
                PodcastPreference(
                    topics=["technology", "artificial intelligence", "startups"],
                    min_duration_minutes=15,
                    max_duration_minutes=90
                ),
                PodcastPreference(
                    topics=["business", "entrepreneurship"],
                    min_duration_minutes=20,
                    max_duration_minutes=60
                ),
                PodcastPreference(
                    show_name="The Tim Ferriss Show",
                    min_duration_minutes=30,
                    max_duration_minutes=120
                )
            ]
            
            config.podcast_preferences = default_preferences
            logger.info(f"✅ Added {len(default_preferences)} default preferences")
        
        # Initialize enhanced MCP agent
        agent = EnhancedMCPPodcastAgent(config)
        logger.info(f"✅ Enhanced agent initialized with {len(config.podcast_preferences)} preferences")
        
        # Check MCP servers status
        servers_status = await agent.get_mcp_servers_status()
        online_servers = servers_status.get('online_servers', 0)
        total_servers = servers_status.get('total_servers', 0)
        logger.info(f"🔌 MCP Servers status: {online_servers}/{total_servers} online")
        
        if online_servers < total_servers:
            logger.warning("⚠️ Some MCP servers are offline - functionality may be limited")
        
        # Run the agent with email summary
        result = await agent.run(send_email_summary=True)
        
        # Log results
        if result["status"] == "success":
            if result.get("episodes"):
                episode_count = len(result["episodes"])
                logger.info(f"🎵 Successfully processed {episode_count} episodes")
                
                # Log episode details
                for i, episode_data in enumerate(result["episodes"], 1):
                    episode = episode_data["episode"]
                    score = episode_data.get("relevance_score", 0)
                    duration_ms = episode.get('duration_ms', 0)
                    duration_str = f"{duration_ms // 60000}m" if duration_ms else "Unknown"
                    logger.info(f"  {i}. {episode.get('name', 'Unknown')} ({duration_str}, score: {score:.2f})")
                
                # Log email status
                if result.get("email_sent"):
                    logger.info("📧 Episode summary email sent successfully")
                elif agent.email_enabled:
                    logger.warning("📧 Email summary failed to send")
                else:
                    logger.info("📧 Email summary skipped (not configured)")
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
        elif pending_result["status"] == "warning":
            logger.warning(f"⚠️ {pending_result.get('message', 'Warning processing pending episodes')}")
        
        # Check if it's time for weekly digest (run on Sundays)
        if datetime.now().weekday() == 6:  # Sunday
            logger.info("📊 Running weekly digest...")
            digest_result = await agent.run_weekly_digest()
            
            if digest_result.get("digest_sent"):
                logger.info("📧 Weekly digest sent successfully")
            else:
                logger.info("📧 Weekly digest skipped or failed")
        
        # Calculate run duration
        run_duration = datetime.now() - run_start_time
        logger.info(f"⏱️ Run completed in {run_duration.total_seconds():.1f} seconds")
        logger.info("🏁 Scheduled agent run completed successfully")
        
    except Exception as e:
        run_duration = datetime.now() - run_start_time
        logger.error(f"💥 Error in scheduled agent run after {run_duration.total_seconds():.1f}s: {str(e)}")
        
        # Log full traceback for debugging
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        
        # Try to send error notification if email is configured
        try:
            user_email = os.getenv('USER_EMAIL')
            if user_email and os.getenv('SMTP_USERNAME'):
                # Create a minimal email client for error notifications
                import smtplib
                from email.mime.text import MIMEText
                
                msg = MIMEText(f"""
                Your Spotify Podcast Agent encountered an error during its scheduled run:
                
                Error: {str(e)}
                Time: {datetime.now().isoformat()}
                Duration: {run_duration.total_seconds():.1f} seconds
                
                Please check the logs for more details.
                """)
                
                msg['Subject'] = '🚨 Podcast Agent Error'
                msg['From'] = os.getenv('SMTP_USERNAME')
                msg['To'] = user_email
                
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
                    server.send_message(msg)
                
                logger.info(f"📧 Error notification sent to {user_email}")
                
        except Exception as email_error:
            logger.error(f"Failed to send error notification: {str(email_error)}")
        
        sys.exit(1)

def main():
    """Main entry point for scheduler"""
    logger.info("=" * 70)
    logger.info(f"🚀 ENHANCED SCHEDULED RUN STARTED - {datetime.now().isoformat()}")
    logger.info("=" * 70)
    
    # Check if we're in the right environment
    if 'DYNO' in os.environ:
        logger.info("🌊 Running on Heroku")
    else:
        logger.info("💻 Running locally")
    
    # Log basic environment info
    logger.info(f"🐍 Python version: {sys.version.split()[0]}")
    logger.info(f"📁 Working directory: {os.getcwd()}")
    logger.info(f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    try:
        # Run the async agent
        asyncio.run(run_scheduled_agent())
        logger.info("✅ Scheduled job completed successfully")
    except KeyboardInterrupt:
        logger.info("⏹️ Scheduled job interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Scheduled job failed with unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()