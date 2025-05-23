"""
MCP Protocol implementation for Spotify Podcast Agent
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic
from pydantic import BaseModel
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class MCPMessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

class MCPMessage(BaseModel):
    """Base MCP message structure"""
    type: MCPMessageType
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class MCPResource(BaseModel):
    """Represents a resource that can be accessed via MCP"""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None

class MCPTool(BaseModel):
    """Represents a tool that can be called via MCP"""
    name: str
    description: str
    input_schema: Dict[str, Any]

class MCPServer(ABC):
    """Abstract base class for MCP servers"""
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.resources: Dict[str, MCPResource] = {}
        self.tools: Dict[str, MCPTool] = {}
        
    @abstractmethod
    async def handle_request(self, message: MCPMessage) -> MCPMessage:
        """Handle incoming MCP requests"""
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[MCPResource]:
        """List available resources"""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[MCPTool]:
        """List available tools"""
        pass
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool by name"""
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        return await self._execute_tool(name, arguments)
    
    @abstractmethod
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a specific tool"""
        pass

class MCPClient:
    """MCP client for communicating with servers"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
    
    def register_server(self, name: str, server: MCPServer):
        """Register an MCP server"""
        self.servers[name] = server
        logger.info(f"Registered MCP server: {name}")
    
    async def send_request(self, server_name: str, method: str, params: Dict[str, Any] = None) -> Any:
        """Send a request to a specific server"""
        if server_name not in self.servers:
            raise ValueError(f"Server {server_name} not found")
        
        server = self.servers[server_name]
        message = MCPMessage(
            type=MCPMessageType.REQUEST,
            method=method,
            params=params or {}
        )
        
        response = await server.handle_request(message)
        
        if response.error:
            raise Exception(f"MCP Error: {response.error}")
        
        return response.result
    
    async def list_server_resources(self, server_name: str) -> List[MCPResource]:
        """List resources from a specific server"""
        if server_name not in self.servers:
            raise ValueError(f"Server {server_name} not found")
        
        return await self.servers[server_name].list_resources()
    
    async def list_server_tools(self, server_name: str) -> List[MCPTool]:
        """List tools from a specific server"""
        if server_name not in self.servers:
            raise ValueError(f"Server {server_name} not found")
        
        return await self.servers[server_name].list_tools()