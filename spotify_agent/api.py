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
from spotify_agent.agent import PodcastAgent

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

# Initialize configuration
try:
    config = AgentConfig()
    agent = PodcastAgent(config)
    logger.info("Agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize agent: {str(e)}")
    raise

# Scheduler for running agent periodically
def run_agent_job():
    """Run the agent as a scheduled job"""
    logger.info("Running scheduled agent job...")
    try:
        result = agent.run()
        logger.info(f"Agent job completed: {result['message']}")
    except Exception as e:
        logger.error(f"Error in scheduled agent job: {str(e)}")

# Start scheduler in a background thread
def start_scheduler():
    """Start the scheduler in a background thread"""
    if config.check_frequency == "daily":
        schedule.every().day.at("08:00").do(run_agent_job)
        logger.info("Scheduler set to run daily at 08:00")
    elif config.check_frequency == "weekly":
        schedule.every().monday.at("08:00").do(run_agent_job)
        logger.info("Scheduler set to run weekly on Monday at 08:00")
    else:
        logger.warning(f"Unknown check frequency: {config.check_frequency}")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

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

@app.get("/preferences")
def get_preferences():
    """Get all podcast preferences"""
    return {"preferences": [pref.dict() for pref in agent.get_podcast_preferences()]}

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
        pref = PodcastPreference(**preference.dict())
        agent.add_podcast_preference(pref)
        
        return {"status": "success", "message": "Preference added", "preference": pref.dict()}
    except Exception as e:
        logger.error(f"Error adding preference: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run")
def run_agent(background_tasks: BackgroundTasks):
    """Run the agent manually to discover and queue podcasts"""
    try:
        background_tasks.add_task(agent.run)
        return {
            "status": "success", 
            "message": "Agent started in background", 
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
def get_config():
    """Get the current agent configuration"""
    return {
        "check_frequency": config.check_frequency,
        "relevance_threshold": config.relevance_threshold,
        "max_episodes_per_run": config.max_episodes_per_run,
        "use_vector_memory": config.use_vector_memory
    }

@app.put("/config")
def update_config(config_update: AgentConfigUpdate):
    """Update the agent configuration"""
    try:
        update_dict = config_update.dict(exclude_none=True)
        
        for key, value in update_dict.items():
            setattr(config, key, value)
        
        return {"status": "success", "message": "Configuration updated", "config": config.dict()}
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
def get_status():
    """Get the agent status"""
    try:
        # Get Spotify connection status
        spotify_status = "connected" if agent.spotify.get_current_user_profile() else "disconnected"
        
        # Check if there's an active device
        has_active_device = agent.check_spotify_active_device()
        
        # Get pending episodes count if queue manager is available
        pending_count = 0
        if hasattr(agent, 'queue_manager') and agent.queue_manager:
            pending_count = len(agent.queue_manager.get_pending_episodes())
        
        return {
            "status": "online",
            "spotify_status": spotify_status,
            "active_device": has_active_device,
            "preferences_count": len(agent.get_podcast_preferences()),
            "processed_episodes_count": len(agent.processed_episodes),
            "pending_episodes_count": pending_count,
            "last_run": "Not available" # This would be stored and retrieved in a real implementation
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

# New endpoint to reset processed episodes
@app.post("/reset-episodes")
def reset_episodes():
    """Reset the list of processed episodes"""
    try:
        agent.reset_processed_episodes()
        return {
            "status": "success", 
            "message": "Reset processed episodes list", 
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error resetting episodes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint to process pending episodes
@app.post("/process-pending")
def process_pending():
    """Process any pending episodes from previous runs"""
    try:
        result = agent.process_pending_episodes()
        return result
    except Exception as e:
        logger.error(f"Error processing pending episodes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint to check Spotify devices
@app.get("/devices")
def get_devices():
    """Get available Spotify devices"""
    try:
        devices = agent.spotify.get_devices()
        return devices
    except Exception as e:
        logger.error(f"Error getting Spotify devices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint to start playback
@app.post("/start-playback")
def start_playback(device_id: Optional[str] = None):
    """Start playback on a Spotify device"""
    try:
        success = agent.spotify.start_playback(device_id=device_id)
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
    # Use port 8080 instead of 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_api()