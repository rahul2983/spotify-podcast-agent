"""
MCP-enabled FastAPI server for Spotify Podcast Agent
"""
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

from ..config import AgentConfig, PodcastPreference

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

class MCPServerInfo(BaseModel):
    name: str
    version: str
    tools: List[Dict[str, Any]]
    resources: List[Dict[str, Any]]

# API Routes
@app.get("/")
def read_root():
    return {"status": "online", "message": "MCP Spotify Podcast Agent API is running", "version": "2.0.0"}

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
        "current_agent_status": "initialized" if agent is not None else "not_initialized"
    }

@app.get("/mcp/servers")
async def list_mcp_servers():
    """List all registered MCP servers and their capabilities"""
    try:
        current_agent = get_agent()
        servers_info = []
        
        for server_name in ["spotify", "llm", "queue"]:
            try:
                # Get tools
                tools = await current_agent.mcp_client.list_server_tools(server_name)
                
                # Get resources
                resources = await current_agent.mcp_client.list_server_resources(server_name)
                
                servers_info.append({
                    "name": server_name,
                    "tools": [tool.dict() for tool in tools],
                    "resources": [resource.dict() for resource in resources]
                })
            except Exception as e:
                logger.error(f"Error getting info for MCP server {server_name}: {str(e)}")
        
        return {"servers": servers_info}
    except Exception as e:
        logger.error(f"Error listing MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/call")
async def call_mcp_tool(server_name: str, tool_name: str, arguments: Dict[str, Any] = None):
    """Call a tool on a specific MCP server"""
    try:
        current_agent = get_agent()
        result = await current_agent.mcp_client.send_request(
            server_name, "tools/call",
            {
                "name": tool_name,
                "arguments": arguments or {}
            }
        )
        return {"result": result}
    except Exception as e:
        logger.error(f"Error calling MCP tool {tool_name} on {server_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/resources/{server_name}")
async def get_mcp_resource(server_name: str, uri: str):
    """Read a resource from a specific MCP server"""
    try:
        current_agent = get_agent()
        result = await current_agent.mcp_client.send_request(
            server_name, "resources/read",
            {"uri": uri}
        )
        return result
    except Exception as e:
        logger.error(f"Error reading MCP resource {uri} from {server_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/run")
async def run_agent():
    """Run the MCP agent"""
    try:
        current_agent = get_agent()
        result = await current_agent.run()
        return result
    except Exception as e:
        logger.error(f"Error running MCP agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
            "mcp_servers": ["spotify", "llm", "queue"]
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return {"status": "error", "message": str(e)}

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

@app.get("/devices")
async def get_devices():
    """Get Spotify devices via MCP"""
    try:
        current_agent = get_agent()
        devices = await current_agent.mcp_client.send_request(
            "spotify", "tools/call",
            {"name": "get_devices", "arguments": {}}
        )
        return devices
    except Exception as e:
        logger.error(f"Error getting devices: {str(e)}")
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
    import os
    port = int(os.environ.get("PORT", 8000))
    
    # For Heroku deployment, use simpler configuration
    uvicorn.run(
        "spotify_agent.mcp_api.api:app",
        host="0.0.0.0", 
        port=port,
        reload=False,
        workers=1
    )

if __name__ == "__main__":
    start_api()