"""
Enhanced MCP-enabled FastAPI server with Email and Calendar features
"""
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import logging
import asyncio
import os
from datetime import datetime, timedelta
from ..config import AgentConfig, PodcastPreference
import threading
import schedule
import time

# Global scheduler thread
scheduler_thread = None
scheduler_running = False

logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Enhanced MCP Spotify Podcast Agent API",
    description="MCP-based API with email summaries and calendar integration",
    version="2.1.0"
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
    """Get or create the enhanced MCP agent instance"""
    global agent, config
    if agent is None:
        try:
            logger.info("Initializing Enhanced MCP Agent...")
            from ..mcp_agent.enhanced_podcast_agent import EnhancedMCPPodcastAgent
            
            # Initialize config first
            config = AgentConfig()
            
            # Add user email if configured
            user_email = os.getenv('USER_EMAIL')
            if user_email:
                config.user_email = user_email
                logger.info(f"Email notifications configured for: {user_email}")
            
            logger.info("Config initialized successfully")
            
            # Check required environment variables
            if not config.openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            if not config.spotify_client_id:
                raise ValueError("SPOTIFY_CLIENT_ID environment variable not set")
            if not config.spotify_client_secret:
                raise ValueError("SPOTIFY_CLIENT_SECRET environment variable not set")
            
            # Initialize enhanced MCP agent
            agent = EnhancedMCPPodcastAgent(config)
            logger.info("Enhanced MCP Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced MCP agent: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize enhanced MCP agent: {str(e)}")
    
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
            result = loop.run_until_complete(current_agent.run(send_email_summary=True))
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
        
        # Add weekly digest job (Sundays at 09:00)
        schedule.every().sunday.at("09:00").do(run_weekly_digest_job)
        logger.info("📅 Weekly digest scheduled for Sundays at 09:00")
        
        scheduler_running = True
        
        while scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except Exception as e:
        logger.error(f"💥 Error in scheduler thread: {str(e)}")

def run_weekly_digest_job():
    """Run weekly digest job"""
    try:
        logger.info("📊 Running weekly digest job...")
        current_agent = get_agent()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(current_agent.run_weekly_digest())
            logger.info(f"📧 Weekly digest result: {result['message']}")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"💥 Error in weekly digest job: {str(e)}")

# Enhanced API Models
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
    user_email: Optional[EmailStr] = None

class EmailSettings(BaseModel):
    user_email: EmailStr
    send_summaries: Optional[bool] = True
    send_weekly_digest: Optional[bool] = True

class ListeningSchedule(BaseModel):
    day_of_week: str
    start_time: str  # HH:MM format
    duration_minutes: int
    title: Optional[str] = "Podcast Listening Time"

class MCPCallRequest(BaseModel):
    server_name: str
    tool_name: str
    arguments: Dict[str, Any]

# API Routes
@app.get("/")
def read_root():
    return {
        "status": "online", 
        "message": "Enhanced MCP Spotify Podcast Agent API", 
        "version": "2.1.0",
        "features": ["email_summaries", "calendar_integration", "mcp_architecture"],
        "endpoints": {
            "auth": "/auth - Get Spotify authorization URL",
            "status": "/status - Get comprehensive app status",
            "preferences": "/preferences - Manage podcast preferences", 
            "email": "/email/* - Email notification settings",
            "calendar": "/calendar/* - Calendar and scheduling features",
            "mcp": "/mcp/* - Direct MCP server interactions",
            "run": "/run - Run the podcast agent"
        }
    }

# ===== AUTHENTICATION ENDPOINTS =====
@app.get("/auth")
def initiate_auth():
    """Initiate Spotify OAuth flow"""
    try:
        current_agent = get_agent()
        spotify_client = current_agent.spotify_client
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
        
        token_info = spotify_client.sp.auth_manager.get_access_token(code)
        
        if token_info:
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
                        "🎵 Try: /run to discover podcast episodes",
                        "📧 Try: /email/settings to configure email summaries"
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

# ===== EMAIL ENDPOINTS =====
@app.get("/email/settings")
def get_email_settings():
    """Get current email settings"""
    try:
        current_agent = get_agent()
        
        return {
            "email_enabled": current_agent.email_enabled,
            "user_email": getattr(current_agent.config, 'user_email', None),
            "smtp_configured": bool(os.getenv('SMTP_USERNAME') and os.getenv('SMTP_PASSWORD')),
            "features": {
                "daily_summaries": current_agent.email_enabled,
                "weekly_digest": current_agent.email_enabled,
                "pending_notifications": current_agent.email_enabled
            }
        }
    except Exception as e:
        logger.error(f"Error getting email settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/email/settings")
def update_email_settings(settings: EmailSettings):
    """Update email settings"""
    try:
        current_agent = get_agent()
        
        # Update config
        current_agent.config.user_email = str(settings.user_email)
        current_agent.email_enabled = True
        
        # Set environment variable for scheduler
        os.environ['USER_EMAIL'] = str(settings.user_email)
        
        return {
            "status": "success",
            "message": "Email settings updated successfully",
            "user_email": str(settings.user_email),
            "email_enabled": True
        }
    except Exception as e:
        logger.error(f"Error updating email settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/email/test")
async def send_test_email():
    """Send a test email"""
    try:
        current_agent = get_agent()
        
        if not current_agent.email_enabled:
            raise HTTPException(status_code=400, detail="Email not configured")
        
        result = await current_agent.mcp_client.send_request(
            "email", "tools/call",
            {
                "name": "send_notification",
                "arguments": {
                    "to_email": current_agent.config.user_email,
                    "subject": "🎵 Test Email from Podcast Agent",
                    "message": f"This is a test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Your email notifications are working correctly!"
                }
            }
        )
        
        return {
            "status": "success" if result.get("success") else "failed",
            "message": result.get("message", "Test email sent"),
            "email": current_agent.config.user_email
        }
        
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/email/weekly-digest")
async def send_weekly_digest_now():
    """Send weekly digest immediately"""
    try:
        current_agent = get_agent()
        result = await current_agent.run_weekly_digest()
        return result
    except Exception as e:
        logger.error(f"Error sending weekly digest: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== CALENDAR ENDPOINTS =====
@app.get("/calendar/schedule")
async def get_listening_schedule():
    """Get current podcast listening schedule"""
    try:
        current_agent = get_agent()
        schedule = await current_agent.get_listening_schedule()
        return schedule
    except Exception as e:
        logger.error(f"Error getting listening schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calendar/schedule")
async def add_listening_schedule(schedule: ListeningSchedule):
    """Add new listening time to schedule"""
    try:
        current_agent = get_agent()
        
        result = await current_agent.schedule_listening_time(
            schedule.day_of_week,
            schedule.start_time,
            schedule.duration_minutes,
            schedule.title
        )
        
        return result
    except Exception as e:
        logger.error(f"Error adding listening schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calendar/suggestions")
async def get_schedule_suggestions():
    """Get optimal schedule suggestions"""
    try:
        current_agent = get_agent()
        suggestions = await current_agent.suggest_optimal_schedule()
        return suggestions
    except Exception as e:
        logger.error(f"Error getting schedule suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calendar/stats")
async def get_listening_stats(period: str = "week"):
    """Get listening statistics"""
    try:
        current_agent = get_agent()
        
        stats = await current_agent.mcp_client.send_request(
            "calendar", "tools/call",
            {
                "name": "get_listening_stats",
                "arguments": {"period": period}
            }
        )
        
        return stats
    except Exception as e:
        logger.error(f"Error getting listening stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== MCP ENDPOINTS =====
@app.get("/mcp/servers")
async def get_mcp_servers():
    """Get status of all MCP servers"""
    try:
        current_agent = get_agent()
        servers_status = await current_agent.get_mcp_servers_status()
        
        # Get detailed info for each server
        detailed_servers = []
        for server_name in ["spotify", "llm", "queue", "email", "calendar"]:
            server_info = servers_status["servers"].get(server_name, {})
            
            # Get tools for online servers
            tools = []
            if server_info.get("status") == "online":
                try:
                    tools_result = await current_agent.mcp_client.send_request(
                        server_name, "tools/list", {}
                    )
                    tools = tools_result.get("tools", [])
                except:
                    pass
            
            detailed_servers.append({
                "name": server_name,
                "status": server_info.get("status", "unknown"),
                "tools": tools,
                "tools_count": len(tools),
                "error": server_info.get("error")
            })
        
        return {
            "servers": detailed_servers,
            "summary": servers_status
        }
        
    except Exception as e:
        logger.error(f"Error getting MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/call")
async def call_mcp_tool(request: MCPCallRequest):
    """Call a tool on a specific MCP server"""
    try:
        current_agent = get_agent()
        
        result = await current_agent.mcp_client.send_request(
            request.server_name,
            "tools/call",
            {
                "name": request.tool_name,
                "arguments": request.arguments
            }
        )
        
        return {
            "status": "success",
            "server": request.server_name,
            "tool": request.tool_name,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error calling MCP tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENHANCED STATUS AND CONFIG =====
@app.get("/status")
async def get_status():
    """Get comprehensive agent status"""
    try:
        current_agent = get_agent()
        
        # Check Spotify connection
        try:
            spotify_profile = await current_agent.mcp_client.send_request(
                "spotify", "resources/read",
                {"uri": "spotify://user/profile"}
            )
            spotify_status = "connected" if spotify_profile else "disconnected"
        except:
            spotify_status = "disconnected"
        
        # Check active device
        try:
            has_active_device = await current_agent.check_spotify_active_device()
        except:
            has_active_device = False
        
        # Get pending episodes count
        try:
            pending_data = await current_agent.mcp_client.send_request(
                "queue", "tools/call",
                {"name": "get_pending", "arguments": {}}
            )
            pending_count = pending_data.get("count", 0)
        except:
            pending_count = 0
        
        # Get MCP servers status
        servers_status = await current_agent.get_mcp_servers_status()
        
        return {
            "status": "online",
            "version": "2.1.0",
            "architecture": "Enhanced MCP-based",
            "spotify_status": spotify_status,
            "active_device": has_active_device,
            "preferences_count": len(current_agent.get_podcast_preferences()),
            "processed_episodes_count": len(current_agent.processed_episodes),
            "pending_episodes_count": pending_count,
            "email_enabled": current_agent.email_enabled,
            "calendar_enabled": current_agent.calendar_enabled,
            "mcp_servers": servers_status,
            "features": {
                "email_summaries": current_agent.email_enabled,
                "calendar_integration": True,
                "weekly_digest": current_agent.email_enabled,
                "pending_notifications": current_agent.email_enabled
            }
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {"status": "error", "message": str(e)}

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
            "email_enabled": current_agent.email_enabled,
            "user_email": getattr(current_agent.config, 'user_email', None),
            "features": {
                "email_summaries": current_agent.email_enabled,
                "calendar_integration": True,
                "mcp_architecture": True
            }
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
            if key == "user_email":
                current_agent.config.user_email = str(value)
                current_agent.email_enabled = True
                os.environ['USER_EMAIL'] = str(value)
            elif hasattr(current_agent.config, key):
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
                "use_vector_memory": current_agent.config.use_vector_memory,
                "email_enabled": current_agent.email_enabled,
                "user_email": getattr(current_agent.config, 'user_email', None)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== CORE FUNCTIONALITY =====
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
                "suggestion": "Try /auth/status to check if you're authenticated"
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
async def run_agent(background_tasks: BackgroundTasks, send_email: bool = True):
    """Run the enhanced MCP agent in background"""
    try:
        current_agent = get_agent()
        
        # Add the agent run to background tasks
        background_tasks.add_task(run_agent_background, current_agent, send_email)
        
        return {
            "status": "started",
            "message": "Enhanced agent started in background",
            "timestamp": datetime.now().isoformat(),
            "features": {
                "email_summary": send_email and current_agent.email_enabled,
                "calendar_integration": True,
                "mcp_architecture": True
            },
            "instructions": [
                "🤖 Enhanced agent is running in the background",
                "⏱️  This may take 1-2 minutes",
                "📊 Check /status to see progress",
                "🎵 Episodes will be added to your Spotify queue",
                "📧 Email summary will be sent if configured" if send_email else ""
            ]
        }
    except Exception as e:
        logger.error(f"Error starting enhanced MCP agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_agent_background(agent, send_email: bool):
    """Background task to run the enhanced agent"""
    try:
        logger.info("Starting background enhanced agent run...")
        result = await agent.run(send_email_summary=send_email)
        logger.info(f"Background enhanced agent run completed: {result}")
        
        if result.get("episodes"):
            logger.info(f"✅ Added {len(result['episodes'])} episodes to queue")
            for episode_data in result["episodes"]:
                episode = episode_data["episode"]
                logger.info(f"  🎵 {episode.get('name', 'Unknown')} - {episode_data.get('summary', 'No summary')}")
        
        if result.get("email_sent"):
            logger.info("📧 Email summary sent successfully")
            
    except Exception as e:
        logger.error(f"Error in background enhanced agent run: {str(e)}")

# Additional existing endpoints...
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

# ===== SCHEDULER ENDPOINTS =====
@app.post("/scheduler/start")
def start_scheduler():
    """Start the built-in scheduler"""
    global scheduler_thread, scheduler_running
    
    if scheduler_thread and scheduler_thread.is_alive():
        return {
            "status": "already_running",
            "message": "Scheduler is already running"
        }
    
    try:
        scheduler_running = True
        scheduler_thread = threading.Thread(target=start_scheduler_thread, daemon=True)
        scheduler_thread.start()
        
        return {
            "status": "started",
            "message": "Enhanced scheduler started successfully",
            "features": ["daily_runs", "weekly_digest", "email_summaries"]
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
    
    return {
        "running": is_running,
        "jobs_count": len(schedule.jobs),
        "jobs": [str(job) for job in schedule.jobs] if is_running else [],
        "frequency": get_agent().config.check_frequency if is_running else None
    }

# Add this endpoint to your enhanced_api.py file in the EMAIL ENDPOINTS section

@app.post("/email/debug-test")
async def debug_test_email():
    """Debug test endpoint to identify Unicode issues"""
    try:
        current_agent = get_agent()
        
        if not current_agent.email_enabled:
            raise HTTPException(status_code=400, detail="Email not configured")
        
        # Get the user email
        user_email = getattr(current_agent.config, 'user_email', None)
        if not user_email:
            raise HTTPException(status_code=400, detail="User email not configured")
        
        # Call the debug test method via MCP
        result = await current_agent.mcp_client.send_request(
            "email", "tools/call",
            {
                "name": "test_email_with_debug",
                "arguments": {
                    "to_email": user_email
                }
            }
        )
        
        return {
            "status": "completed",
            "message": "Debug test completed - check logs for detailed Unicode analysis",
            "result": result,
            "instructions": [
                "📋 Check your application logs for detailed Unicode debugging info",
                "🔍 Look for lines containing 'Non-ASCII character' to identify problems",
                "📧 A simple test email should have been sent if successful",
                "⚠️ If test failed, the logs will show exactly which characters are problematic"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug test failed: {str(e)}")
        return {
            "status": "error", 
            "error": str(e),
            "message": "Debug test failed - check logs for details"
        }

def start_api():
    """Start the enhanced MCP-enabled API server"""
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "spotify_agent.mcp_api.enhanced_api:app",
        host="0.0.0.0", 
        port=port,
        reload=False,
        workers=1
    )

if __name__ == "__main__":
    start_api()