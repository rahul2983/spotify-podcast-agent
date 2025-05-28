"""
MCP-enabled FastAPI server for Spotify Podcast Agent
"""
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import asyncio
import os
from datetime import datetime
from ..config import AgentConfig, PodcastPreference
import threading
import schedule
import time
from datetime import datetime

# Global scheduler thread
scheduler_thread = None
scheduler_running = False

logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="MCP Spotify Podcast Agent API",
    description="MCP-based API for automated Spotify podcast discovery and queueing",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent variable
agent = None
config = None

def get_agent():
    """Get or create the MCP agent instance"""
    global agent, config
    if agent is None:
        try:
            logger.info("Initializing MCP Agent...")
            from ..mcp_agent.podcast_agent import MCPPodcastAgent
            
            # Initialize config first
            config = AgentConfig()
            logger.info("Config initialized successfully")
            
            # Check required environment variables
            if not config.openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            if not config.spotify_client_id:
                raise ValueError("SPOTIFY_CLIENT_ID environment variable not set")
            if not config.spotify_client_secret:
                raise ValueError("SPOTIFY_CLIENT_SECRET environment variable not set")
            
            # Initialize MCP agent
            agent = MCPPodcastAgent(config)
            logger.info("MCP Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP agent: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize MCP agent: {str(e)}")
    
    return agent

def run_scheduled_agent_job():
    """Background job for scheduled agent runs"""
    try:
        logger.info("🕒 Running scheduled agent job...")
        current_agent = get_agent()
        
        # Run agent in background (async)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(current_agent.run())
            logger.info(f"📊 Scheduled run result: {result['message']}")
            
            # Also process pending episodes
            pending_result = loop.run_until_complete(current_agent.process_pending_episodes())
            if pending_result.get('episodes'):
                logger.info(f"✅ Processed {len(pending_result['episodes'])} pending episodes")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"💥 Error in scheduled job: {str(e)}")

def start_scheduler_thread():
    """Start the scheduler in a background thread"""
    global scheduler_running
    
    try:
        current_config = get_agent().config
        
        if current_config.check_frequency == "daily":
            schedule.every().day.at("08:00").do(run_scheduled_agent_job)
            logger.info("📅 Scheduler set to run daily at 08:00")
        elif current_config.check_frequency == "weekly":
            schedule.every().monday.at("08:00").do(run_scheduled_agent_job)
            logger.info("📅 Scheduler set to run weekly on Monday at 08:00")
        
        scheduler_running = True
        
        while scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except Exception as e:
        logger.error(f"💥 Error in scheduler thread: {str(e)}")

# API Models
class PreferenceCreate(BaseModel):
    show_name: Optional[str] = None
    show_id: Optional[str] = None
    topics: Optional[List[str]] = None
    min_duration_minutes: Optional[int] = None
    max_duration_minutes: Optional[int] = None

class AgentConfigUpdate(BaseModel):
    check_frequency: Optional[str] = None
    relevance_threshold: Optional[float] = None
    max_episodes_per_run: Optional[int] = None
    use_vector_memory: Optional[bool] = None

# API Routes
@app.get("/")
def read_root():
    return {
        "status": "online", 
        "message": "MCP Spotify Podcast Agent API is running", 
        "version": "2.0.0",
        "endpoints": {
            "auth": "/auth - Get Spotify authorization URL",
            "auth_status": "/auth/status - Check authentication status",
            "callback": "/callback - OAuth callback endpoint",
            "status": "/status - Get app status",
            "preferences": "/preferences - Manage podcast preferences",
            "devices": "/devices - Get Spotify devices",
            "run": "/run - Run the podcast agent"
        }
    }

# ===== AUTHENTICATION ENDPOINTS =====
@app.get("/auth")
def initiate_auth():
    """Initiate Spotify OAuth flow"""
    try:
        current_agent = get_agent()
        
        # Get the Spotify client from the agent
        spotify_client = current_agent.spotify_client
        
        # Get the authorization URL
        auth_url = spotify_client.sp.auth_manager.get_authorize_url()
        
        return {
            "auth_url": auth_url,
            "message": "Visit this URL to authorize the app with your Spotify account",
            "instructions": [
                "1. Click or visit the auth_url",
                "2. Log in to your Spotify account",
                "3. Click 'Agree' to authorize the app",
                "4. You'll be redirected back to confirm authentication"
            ]
        }
    except Exception as e:
        logger.error(f"Error initiating auth: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/callback")
def spotify_callback(code: str):
    """Handle Spotify OAuth callback"""
    try:
        current_agent = get_agent()
        spotify_client = current_agent.spotify_client
        
        # Exchange code for token
        token_info = spotify_client.sp.auth_manager.get_access_token(code)
        
        if token_info:
            # Try to get user info to confirm it worked
            try:
                profile = spotify_client.get_current_user_profile()
                user_name = profile.get("display_name", "Unknown User")
                
                return {
                    "status": "success",
                    "message": f"Successfully authenticated with Spotify!",
                    "user": user_name,
                    "instructions": [
                        "✅ Authentication complete!",
                        "✅ You can now use all app features",
                        "🎵 Try: /devices to see your Spotify devices",
                        "🎵 Try: /run to discover podcast episodes"
                    ]
                }
            except Exception as e:
                logger.warning(f"Auth succeeded but couldn't get profile: {str(e)}")
                return {
                    "status": "success",
                    "message": "Authentication completed, but couldn't fetch profile",
                    "note": "This is usually fine - try using the app features"
                }
        else:
            raise HTTPException(status_code=400, detail="Failed to get access token")
            
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/status")
def check_auth_status():
    """Check if the user is authenticated"""
    try:
        current_agent = get_agent()
        
        # Try to get user profile to test authentication
        try:
            profile = current_agent.spotify_client.get_current_user_profile()
            if profile:
                return {
                    "authenticated": True,
                    "user": profile.get("display_name", "Unknown"),
                    "user_id": profile.get("id"),
                    "country": profile.get("country"),
                    "message": "✅ User is authenticated and ready to use the app"
                }
        except Exception as auth_error:
            logger.info(f"User not authenticated: {str(auth_error)}")
            
        # If we get here, user is not authenticated
        base_url = os.getenv('SPOTIFY_REDIRECT_URI', '').replace('/callback', '')
        return {
            "authenticated": False,
            "message": "❌ User needs to authenticate with Spotify",
            "instructions": [
                "1. Visit the auth_url below to authenticate",
                "2. Log in to your Spotify account", 
                "3. Authorize the app",
                "4. Come back and check your devices with /devices"
            ],
            "auth_url": f"{base_url}/auth"
        }
            
    except Exception as e:
        logger.error(f"Error checking auth status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/config")
def get_config():
    """Get the current agent configuration"""
    try:
        current_agent = get_agent()
        return {
            "check_frequency": current_agent.config.check_frequency,
            "relevance_threshold": current_agent.config.relevance_threshold,
            "max_episodes_per_run": current_agent.config.max_episodes_per_run,
            "use_vector_memory": current_agent.config.use_vector_memory,
            "preferences_count": len(current_agent.config.podcast_preferences),
            "current_settings": "These are the active agent configuration settings"
        }
    except Exception as e:
        logger.error(f"Error getting configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/config")
def update_config(config_update: AgentConfigUpdate):
    """Update the agent configuration"""
    try:
        current_agent = get_agent()
        update_dict = config_update.dict(exclude_none=True)
        
        # Validate values
        if "relevance_threshold" in update_dict:
            if not 0.0 <= update_dict["relevance_threshold"] <= 1.0:
                raise HTTPException(status_code=400, detail="Relevance threshold must be between 0.0 and 1.0")
        
        if "max_episodes_per_run" in update_dict:
            if update_dict["max_episodes_per_run"] < 1 or update_dict["max_episodes_per_run"] > 20:
                raise HTTPException(status_code=400, detail="Max episodes per run must be between 1 and 20")
        
        if "check_frequency" in update_dict:
            if update_dict["check_frequency"] not in ["daily", "weekly"]:
                raise HTTPException(status_code=400, detail="Check frequency must be 'daily' or 'weekly'")
        
        # Apply updates
        for key, value in update_dict.items():
            if hasattr(current_agent.config, key):
                setattr(current_agent.config, key, value)
                logger.info(f"Updated config: {key} = {value}")
        
        return {
            "status": "success", 
            "message": "Configuration updated successfully", 
            "updated_fields": list(update_dict.keys()),
            "config": {
                "check_frequency": current_agent.config.check_frequency,
                "relevance_threshold": current_agent.config.relevance_threshold,
                "max_episodes_per_run": current_agent.config.max_episodes_per_run,
                "use_vector_memory": current_agent.config.use_vector_memory
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/scheduler/start")
def start_scheduler():
    """Start the built-in scheduler"""
    global scheduler_thread, scheduler_running
    
    if scheduler_thread and scheduler_thread.is_alive():
        return {
            "status": "already_running",
            "message": "Scheduler is already running",
            "next_run": "Varies based on configuration"
        }
    
    try:
        scheduler_running = True
        scheduler_thread = threading.Thread(target=start_scheduler_thread, daemon=True)
        scheduler_thread.start()
        
        current_config = get_agent().config
        
        return {
            "status": "started",
            "message": "Scheduler started successfully",
            "frequency": current_config.check_frequency,
            "next_run": "Daily at 08:00" if current_config.check_frequency == "daily" else "Monday at 08:00"
        }
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scheduler/stop")
def stop_scheduler():
    """Stop the built-in scheduler"""
    global scheduler_running
    
    scheduler_running = False
    schedule.clear()
    
    return {
        "status": "stopped",
        "message": "Scheduler stopped successfully"
    }

@app.get("/scheduler/status")
def get_scheduler_status():
    """Get scheduler status"""
    global scheduler_thread, scheduler_running
    
    is_running = scheduler_thread and scheduler_thread.is_alive() and scheduler_running
    next_run = None
    
    if is_running and schedule.jobs:
        next_job = schedule.next_run()
        next_run = next_job.isoformat() if next_job else None
    
    return {
        "running": is_running,
        "next_run": next_run,
        "jobs_count": len(schedule.jobs),
        "frequency": get_agent().config.check_frequency if is_running else None
    }

# ===== EXISTING ENDPOINTS =====
@app.get("/debug/env")
def debug_env():
    """Debug endpoint to check environment variables"""
    return {
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "has_spotify_client_id": bool(os.getenv("SPOTIFY_CLIENT_ID")),
        "has_spotify_client_secret": bool(os.getenv("SPOTIFY_CLIENT_SECRET")),
        "has_spotify_redirect_uri": bool(os.getenv("SPOTIFY_REDIRECT_URI")),
        "redirect_uri": os.getenv("SPOTIFY_REDIRECT_URI"),
        "python_version": os.sys.version,
        "current_agent_status": "initialized" if agent is not None else "not_initialized"
    }

@app.get("/status")
async def get_status():
    """Get comprehensive agent status including MCP server info"""
    try:
        current_agent = get_agent()
        
        # Check Spotify connection via MCP
        try:
            spotify_profile = await current_agent.mcp_client.send_request(
                "spotify", "resources/read",
                {"uri": "spotify://user/profile"}
            )
            spotify_status = "connected" if spotify_profile else "disconnected"
        except Exception as e:
            logger.warning(f"Could not check Spotify status: {str(e)}")
            spotify_status = "disconnected"
        
        # Check active device
        try:
            has_active_device = await current_agent.check_spotify_active_device()
        except Exception as e:
            logger.warning(f"Could not check active device: {str(e)}")
            has_active_device = False
        
        # Get pending episodes count
        try:
            pending_data = await current_agent.mcp_client.send_request(
                "queue", "tools/call",
                {"name": "get_pending", "arguments": {}}
            )
            pending_count = pending_data.get("count", 0)
        except Exception as e:
            logger.warning(f"Could not get pending episodes: {str(e)}")
            pending_count = 0
        
        return {
            "status": "online",
            "version": "2.0.0",
            "architecture": "MCP-based",
            "spotify_status": spotify_status,
            "active_device": has_active_device,
            "preferences_count": len(current_agent.get_podcast_preferences()),
            "processed_episodes_count": len(current_agent.processed_episodes),
            "pending_episodes_count": pending_count,
            "mcp_servers": ["spotify", "llm", "queue"],
            "auth_note": "Use /auth/status to check if you're authenticated"
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/preferences")
def get_preferences():
    current_agent = get_agent()
    return {"preferences": [pref.dict() for pref in current_agent.get_podcast_preferences()]}

@app.post("/preferences")
def add_preference(preference: PreferenceCreate):
    try:
        if not preference.show_name and not preference.show_id and not preference.topics:
            raise HTTPException(
                status_code=400, 
                detail="At least one of show_name, show_id, or topics must be provided"
            )
        
        current_agent = get_agent()
        pref = PodcastPreference(**preference.dict())
        current_agent.add_podcast_preference(pref)
        
        return {"status": "success", "message": "Preference added", "preference": pref.dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding preference: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices")
async def get_devices():
    """Get Spotify devices via MCP"""
    try:
        current_agent = get_agent()
        devices = await current_agent.mcp_client.send_request(
            "spotify", "tools/call",
            {"name": "get_devices", "arguments": {}}
        )
        
        if not devices.get("devices"):
            return {
                "devices": [],
                "message": "No devices found - you may need to authenticate first",
                "suggestion": "Try /auth/status to check if you're authenticated with your personal Spotify account"
            }
        
        return devices
    except Exception as e:
        logger.error(f"Error getting devices: {str(e)}")
        return {
            "devices": [],
            "error": str(e),
            "suggestion": "Try authenticating first with /auth"
        }

@app.post("/run")
async def run_agent(background_tasks: BackgroundTasks):
    """Run the MCP agent in background"""
    try:
        current_agent = get_agent()
        
        # Add the agent run to background tasks
        background_tasks.add_task(run_agent_background, current_agent)
        
        return {
            "status": "started",
            "message": "Agent started in background - check /status for results",
            "timestamp": datetime.now().isoformat(),
            "instructions": [
                "🤖 Agent is running in the background",
                "⏱️  This may take 1-2 minutes",
                "📊 Check /status to see progress",
                "🎵 Episodes will be added to your Spotify queue automatically"
            ]
        }
    except Exception as e:
        logger.error(f"Error starting MCP agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_agent_background(agent):
    """Background task to run the agent"""
    try:
        logger.info("Starting background agent run...")
        result = await agent.run()
        logger.info(f"Background agent run completed: {result}")
        
        # You could store the result in a database or cache here
        # For now, we'll just log it
        
        if result.get("episodes"):
            logger.info(f"✅ Added {len(result['episodes'])} episodes to queue")
            for episode_data in result["episodes"]:
                episode = episode_data["episode"]
                logger.info(f"  🎵 {episode.get('name', 'Unknown')} - {episode_data.get('summary', 'No summary')}")
        else:
            logger.info("ℹ️  No new episodes found this run")
            
    except Exception as e:
        logger.error(f"Error in background agent run: {str(e)}")

@app.get("/run/status")
def get_run_status():
    """Get the status of the last agent run"""
    # This is a simple implementation - in production you'd use a database
    return {
        "message": "Check the logs for the latest run status",
        "instructions": [
            "Use 'heroku logs --tail' to see real-time agent activity",
            "Look for messages like '✅ Added X episodes to queue'",
            "Episodes are automatically added to your Spotify queue"
        ]
    }

# Additional endpoints remain the same...
@app.post("/reset-episodes")
def reset_episodes():
    try:
        current_agent = get_agent()
        current_agent.reset_processed_episodes()
        return {
            "status": "success", 
            "message": "Reset processed episodes list", 
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error resetting episodes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-pending")
async def process_pending():
    """Process pending episodes via MCP"""
    try:
        current_agent = get_agent()
        result = await current_agent.process_pending_episodes()
        return result
    except Exception as e:
        logger.error(f"Error processing pending episodes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start-playback")
async def start_playback(device_id: Optional[str] = None):
    """Start playback via MCP"""
    try:
        current_agent = get_agent()
        result = await current_agent.mcp_client.send_request(
            "spotify", "tools/call",
            {
                "name": "start_playback",
                "arguments": {"device_id": device_id} if device_id else {}
            }
        )
        
        if result.get("success"):
            return {
                "status": "success",
                "message": f"Started playback on device {device_id if device_id else 'default'}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to start playback")
    except Exception as e:
        logger.error(f"Error starting playback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def start_api():
    """Start the MCP-enabled API server"""
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "spotify_agent.mcp_api.api:app",
        host="0.0.0.0", 
        port=port,
        reload=False,
        workers=1
    )

if __name__ == "__main__":
    start_api()