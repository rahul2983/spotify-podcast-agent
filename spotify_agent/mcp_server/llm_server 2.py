"""
MCP Server for LLM operations
"""
from typing import Dict, Any, List
from .protocol import MCPServer, MCPMessage, MCPResource, MCPTool, MCPMessageType
from ..llm_agent import PodcastLLMAgent
import logging

logger = logging.getLogger(__name__)

class LLMMCPServer(MCPServer):
    """MCP Server for LLM operations"""
    
    def __init__(self, llm_agent: PodcastLLMAgent):
        super().__init__("llm", "1.0.0")
        self.llm_agent = llm_agent
        self._register_tools()
    
    def _register_tools(self):
        """Register available LLM tools"""
        self.tools.update({
            "evaluate_episode": MCPTool(
                name="evaluate_episode",
                description="Evaluate episode relevance against user preferences",
                input_schema={
                    "type": "object",
                    "properties": {
                        "episode": {"type": "object", "description": "Episode data"},
                        "preferences": {"type": "array", "description": "User preferences"}
                    },
                    "required": ["episode", "preferences"]
                }
            ),
            "generate_summary": MCPTool(
                name="generate_summary",
                description="Generate episode summary",
                input_schema={
                    "type": "object",
                    "properties": {
                        "episode": {"type": "object", "description": "Episode data"}
                    },
                    "required": ["episode"]
                }
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
            else:
                return MCPMessage(
                    type=MCPMessageType.ERROR,
                    error={"code": -32601, "message": f"Method not found: {message.method}"}
                )
        except Exception as e:
            logger.error(f"Error handling LLM MCP request: {str(e)}")
            return MCPMessage(
                type=MCPMessageType.ERROR,
                error={"code": -32603, "message": f"Internal error: {str(e)}"}
            )
    
    async def list_resources(self) -> List[MCPResource]:
        """List available LLM resources"""
        return []
    
    async def list_tools(self) -> List[MCPTool]:
        """List available LLM tools"""
        return list(self.tools.values())
    
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a specific LLM tool"""
        if name == "evaluate_episode":
            episode = arguments["episode"]
            preferences = arguments["preferences"]
            score, reasoning = self.llm_agent.evaluate_episode_relevance(episode, preferences)
            return {"relevance_score": score, "reasoning": reasoning}
        
        elif name == "generate_summary":
            episode = arguments["episode"]
            summary = self.llm_agent.generate_episode_summary(episode)
            return {"summary": summary}
        
        else:
            raise ValueError(f"Unknown tool: {name}")