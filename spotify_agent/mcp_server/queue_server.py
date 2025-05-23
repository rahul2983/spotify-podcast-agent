"""
MCP Server for queue management operations
"""
from typing import Dict, Any, List
from .protocol import MCPServer, MCPMessage, MCPResource, MCPTool, MCPMessageType
from ..queue_manager import QueueManager
import logging

logger = logging.getLogger(__name__)

class QueueMCPServer(MCPServer):
    """MCP Server for queue management operations"""
    
    def __init__(self, queue_manager: QueueManager):
        super().__init__("queue", "1.0.0")
        self.queue_manager = queue_manager
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self):
        """Register available queue management tools"""
        self.tools.update({
            "add_pending": MCPTool(
                name="add_pending",
                description="Add episodes to pending queue",
                input_schema={
                    "type": "object",
                    "properties": {
                        "episodes": {"type": "array", "description": "Episodes to add"}
                    },
                    "required": ["episodes"]
                }
            ),
            "get_pending": MCPTool(
                name="get_pending",
                description="Get pending episodes",
                input_schema={"type": "object", "properties": {}}
            ),
            "remove_processed": MCPTool(
                name="remove_processed",
                description="Remove processed episodes from queue",
                input_schema={
                    "type": "object",
                    "properties": {
                        "episode_ids": {"type": "array", "description": "Episode IDs to remove"}
                    },
                    "required": ["episode_ids"]
                }
            )
        })
    
    def _register_resources(self):
        """Register available queue resources"""
        self.resources.update({
            "pending_episodes": MCPResource(
                uri="queue://pending",
                name="Pending Episodes",
                description="Episodes waiting to be added to Spotify queue",
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
            logger.error(f"Error handling queue MCP request: {str(e)}")
            return MCPMessage(
                type=MCPMessageType.ERROR,
                error={"code": -32603, "message": f"Internal error: {str(e)}"}
            )
    
    async def list_resources(self) -> List[MCPResource]:
        """List available queue resources"""
        return list(self.resources.values())
    
    async def list_tools(self) -> List[MCPTool]:
        """List available queue tools"""
        return list(self.tools.values())
    
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a specific queue tool"""
        if name == "add_pending":
            episodes = arguments["episodes"]
            self.queue_manager.add_pending_episodes(episodes)
            return {"success": True, "count": len(episodes)}
        
        elif name == "get_pending":
            episodes = self.queue_manager.get_pending_episodes()
            return {"episodes": episodes, "count": len(episodes)}
        
        elif name == "remove_processed":
            episode_ids = arguments["episode_ids"]
            self.queue_manager.remove_processed_episodes(episode_ids)
            return {"success": True, "removed_count": len(episode_ids)}
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def _read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific queue resource"""
        if uri == "queue://pending":
            episodes = self.queue_manager.get_pending_episodes()
            return {"episodes": episodes, "count": len(episodes)}
        else:
            raise ValueError(f"Unknown resource URI: {uri}")