"""
MCP Server for Spotify operations
"""
from typing import Dict, Any, List, Optional
import asyncio
from .protocol import MCPServer, MCPMessage, MCPResource, MCPTool, MCPMessageType
from ..spotify_client import SpotifyClient
import logging

logger = logging.getLogger(__name__)

class SpotifyMCPServer(MCPServer):
    """MCP Server for Spotify API operations"""
    
    def __init__(self, spotify_client: SpotifyClient):
        super().__init__("spotify", "1.0.0")
        self.spotify = spotify_client
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self):
        """Register available Spotify tools"""
        self.tools.update({
            "search_podcasts": MCPTool(
                name="search_podcasts",
                description="Search for podcasts by query",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            ),
            "get_show_episodes": MCPTool(
                name="get_show_episodes",
                description="Get episodes for a specific show",
                input_schema={
                    "type": "object",
                    "properties": {
                        "show_id": {"type": "string", "description": "Spotify show ID"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["show_id"]
                }
            ),
            "add_to_queue": MCPTool(
                name="add_to_queue",
                description="Add episode to playback queue",
                input_schema={
                    "type": "object",
                    "properties": {
                        "episode_uri": {"type": "string", "description": "Spotify episode URI"}
                    },
                    "required": ["episode_uri"]
                }
            ),
            "get_devices": MCPTool(
                name="get_devices",
                description="Get available Spotify devices",
                input_schema={"type": "object", "properties": {}}
            ),
            "start_playback": MCPTool(
                name="start_playback",
                description="Start playback on a device",
                input_schema={
                    "type": "object",
                    "properties": {
                        "device_id": {"type": "string", "description": "Device ID (optional)"}
                    }
                }
            )
        })
    
    def _register_resources(self):
        """Register available Spotify resources"""
        self.resources.update({
            "user_profile": MCPResource(
                uri="spotify://user/profile",
                name="User Profile",
                description="Current user's Spotify profile",
                mime_type="application/json"
            ),
            "devices": MCPResource(
                uri="spotify://devices",
                name="Devices",
                description="Available Spotify devices",
                mime_type="application/json"
            ),
            "recently_played": MCPResource(
                uri="spotify://user/recently_played",
                name="Recently Played",
                description="Recently played tracks and episodes",
                mime_type="application/json"
            )
        })
    
    async def handle_request(self, message: MCPMessage) -> MCPMessage:
        """Handle incoming MCP requests"""
        try:
            if message.method == "tools/list":
                return MCPMessage(
                    type=MCPMessageType.RESPONSE,
                    result={"tools": [tool.dict() for tool in self.tools.values()]}
                )
            elif message.method == "tools/call":
                tool_name = message.params.get("name")
                arguments = message.params.get("arguments", {})
                result = await self._execute_tool(tool_name, arguments)
                return MCPMessage(
                    type=MCPMessageType.RESPONSE,
                    result=result
                )
            elif message.method == "resources/list":
                resources = await self.list_resources()
                return MCPMessage(
                    type=MCPMessageType.RESPONSE,
                    result={"resources": [resource.dict() for resource in resources]}
                )
            elif message.method == "resources/read":
                uri = message.params.get("uri")
                content = await self._read_resource(uri)
                return MCPMessage(
                    type=MCPMessageType.RESPONSE,
                    result={"contents": content}
                )
            else:
                return MCPMessage(
                    type=MCPMessageType.ERROR,
                    error={"code": -32601, "message": f"Method not found: {message.method}"}
                )
        except Exception as e:
            logger.error(f"Error handling MCP request: {str(e)}")
            return MCPMessage(
                type=MCPMessageType.ERROR,
                error={"code": -32603, "message": f"Internal error: {str(e)}"}
            )
    
    async def list_resources(self) -> List[MCPResource]:
        """List available Spotify resources"""
        return list(self.resources.values())
    
    async def list_tools(self) -> List[MCPTool]:
        """List available Spotify tools"""
        return list(self.tools.values())
    
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a specific Spotify tool"""
        if name == "search_podcasts":
            query = arguments["query"]
            limit = arguments.get("limit", 5)
            return self.spotify.search_podcast(query, limit)
        
        elif name == "get_show_episodes":
            show_id = arguments["show_id"]
            limit = arguments.get("limit", 10)
            return self.spotify.get_show_episodes(show_id, limit)
        
        elif name == "add_to_queue":
            episode_uri = arguments["episode_uri"]
            success = self.spotify.add_to_queue(episode_uri)
            return {"success": success}
        
        elif name == "get_devices":
            return self.spotify.get_devices()
        
        elif name == "start_playback":
            device_id = arguments.get("device_id")
            success = self.spotify.start_playback(device_id)
            return {"success": success}
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def _read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific Spotify resource"""
        if uri == "spotify://user/profile":
            return self.spotify.get_current_user_profile()
        elif uri == "spotify://devices":
            return self.spotify.get_devices()
        elif uri == "spotify://user/recently_played":
            return {"items": self.spotify.get_recently_played()}
        else:
            raise ValueError(f"Unknown resource URI: {uri}")