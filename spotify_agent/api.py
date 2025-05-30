import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import json
import schedule
import time
import threading
from datetime import datetime

from spotify_agent.config import AgentConfig, PodcastPreference

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Spotify Podcast Agent API",
    description="API for managing your automated Spotify podcast discovery and queueing",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent variable - initialize on first request
agent = None
config = None

def get_agent():
    """Get or create the agent instance"""
    global agent, config
    if agent is None:
        from spotify_agent.agent import PodcastAgent
        try:
            config = AgentConfig()
            agent = PodcastAgent(config)
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}")
    return agent

def get_config():
    """Get or create the config instance"""
    global config
    if config is None:
        try:
            config = AgentConfig()
        except Exception as e:
            logger.error(f"Failed to initialize config: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize config: {str(e)}")
    return config

# Scheduler for running agent periodically
def run_agent_job():
    """Run the agent as a scheduled job"""
    logger.info("Running scheduled agent job...")
    try:
        current_agent = get_agent()
        result = current_agent.run()
        logger.info(f"Agent job completed: {result['message']}")
    except Exception as e:
        logger.error(f"Error in scheduled agent job: {str(e)}")

# Start scheduler in a background thread
def start_scheduler():
    """Start the scheduler in a background thread"""
    try:
        current_config = get_config()
        if current_config.check_frequency == "daily":
            schedule.every().day.at("08:00").do(run_agent_job)
            logger.info("Scheduler set to run daily at 08:00")
        elif current_config.check_frequency == "weekly":
            schedule.every().monday.at("08:00").do(run_agent_job)
            logger.info("Scheduler set to run weekly on Monday at 08:00")
        else:
            logger.warning(f"Unknown check frequency: {current_config.check_frequency}")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    except Exception as e:
        logger.error(f"Error in scheduler: {str(e)}")

# Models for API
class PreferenceCreate(BaseModel):
    """Model for creating podcast preferences"""
    show_name: Optional[str] = None
    show_id: Optional[str] = None
    topics: Optional[List[str]] = None
    min_duration_minutes: Optional[int] = None
    max_duration_minutes: Optional[int] = None

class AgentConfigUpdate(BaseModel):
    """Model for updating agent configuration"""
    check_frequency: Optional[str] = None
    relevance_threshold: Optional[float] = None
    max_episodes_per_run: Optional[int] = None
    use_vector_memory: Optional[bool] = None

class EmailSettings(BaseModel):
    """Model for email notification settings"""
    email: str

# API Routes
@app.get("/")
def read_root():
    """Root endpoint"""
    return {"status": "online", "message": "Spotify Podcast Agent API is running"}

@app.get("/debug/env")
def debug_env():
    """Debug endpoint to check environment variables"""
    import os
    return {
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "has_spotify_client_id": bool(os.getenv("SPOTIFY_CLIENT_ID")),
        "has_spotify_client_secret": bool(os.getenv("SPOTIFY_CLIENT_SECRET")),
        "has_spotify_redirect_uri": bool(os.getenv("SPOTIFY_REDIRECT_URI")),
        "python_version": os.sys.version,
        "env_keys": [k for k in sorted(os.environ.keys()) if not k.startswith('_')][:20]  # More env keys for debugging
    }

@app.get("/preferences")
def get_preferences():
    """Get all podcast preferences"""
    current_agent = get_agent()
    return {"preferences": [pref.dict() for pref in current_agent.get_podcast_preferences()]}

@app.post("/preferences")
def add_preference(preference: PreferenceCreate):
    """Add a new podcast preference"""
    try:
        # Validate that at least one identifier is provided
        if not preference.show_name and not preference.show_id and not preference.topics:
            raise HTTPException(
                status_code=400, 
                detail="At least one of show_name, show_id, or topics must be provided"
            )
        
        # Create and add the preference
        current_agent = get_agent()
        pref = PodcastPreference(**preference.dict())
        current_agent.add_podcast_preference(pref)
        
        return {"status": "success", "message": "Preference added", "preference": pref.dict()}
    except HTTPException:
        # Re-raise HTTPExceptions as-is (don't convert them to 500)
        raise
    except Exception as e:
        logger.error(f"Error adding preference: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run")
def run_agent_endpoint(background_tasks: BackgroundTasks):
    """Run the agent manually to discover and queue podcasts"""
    try:
        current_agent = get_agent()
        background_tasks.add_task(current_agent.run)
        return {
            "status": "success", 
            "message": "Agent started in background", 
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
def get_config_endpoint():
    """Get the current agent configuration"""
    current_config = get_config()
    return {
        "check_frequency": current_config.check_frequency,
        "relevance_threshold": current_config.relevance_threshold,
        "max_episodes_per_run": current_config.max_episodes_per_run,
        "use_vector_memory": current_config.use_vector_memory
    }

@app.put("/config")
def update_config(config_update: AgentConfigUpdate):
    """Update the agent configuration"""
    try:
        current_config = get_config()
        update_dict = config_update.dict(exclude_none=True)
        
        for key, value in update_dict.items():
            setattr(current_config, key, value)
        
        return {"status": "success", "message": "Configuration updated", "config": current_config.dict()}
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
def get_status():
    """Get the agent status"""
    try:
        current_agent = get_agent()
        
        # Get Spotify connection status
        try:
            current_agent.spotify.get_current_user_profile()
            spotify_status = "connected"
        except:
            spotify_status = "disconnected"
        
        # Check if there's an active device
        has_active_device = current_agent.check_spotify_active_device()
        
        # Get pending episodes count if queue manager is available
        pending_count = 0
        if hasattr(current_agent, 'queue_manager') and current_agent.queue_manager:
            pending_count = len(current_agent.queue_manager.get_pending_episodes())
        
        return {
            "status": "online",
            "spotify_status": spotify_status,
            "active_device": has_active_device,
            "preferences_count": len(current_agent.get_podcast_preferences()),
            "processed_episodes_count": len(current_agent.processed_episodes),
            "pending_episodes_count": pending_count,
            "last_run": "Not available"  # This would be stored and retrieved in a real implementation
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/reset-episodes")
def reset_episodes():
    """Reset the list of processed episodes"""
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
def process_pending():
    """Process any pending episodes from previous runs"""
    try:
        current_agent = get_agent()
        result = current_agent.process_pending_episodes()
        return result
    except Exception as e:
        logger.error(f"Error processing pending episodes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices")
def get_devices():
    """Get available Spotify devices"""
    try:
        current_agent = get_agent()
        devices = current_agent.spotify.get_devices()
        return devices
    except Exception as e:
        logger.error(f"Error getting Spotify devices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start-playback")
def start_playback(device_id: Optional[str] = None):
    """Start playback on a Spotify device"""
    try:
        current_agent = get_agent()
        success = current_agent.spotify.start_playback(device_id=device_id)
        if success:
            return {
                "status": "success",
                "message": f"Started playback on device {device_id if device_id else 'default'}"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to start playback"
            )
    except Exception as e:
        logger.error(f"Error starting playback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Start scheduler thread when app starts
@app.on_event("startup")
def on_startup():
    """Start the scheduler when the app starts"""
    threading.Thread(target=start_scheduler, daemon=True).start()
    logger.info("Scheduler thread started")

def start_api():
    """Start the API server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_api()