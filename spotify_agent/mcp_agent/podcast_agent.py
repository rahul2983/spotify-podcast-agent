"""
MCP-based Podcast Agent - Main orchestration layer
"""
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from ..config import AgentConfig, PodcastPreference
from ..mcp_server.protocol import MCPClient
from ..mcp_server.spotify_server import SpotifyMCPServer
from ..mcp_server.llm_server import LLMMCPServer
from ..mcp_server.queue_server import QueueMCPServer
from ..spotify_client import SpotifyClient
from ..llm_agent import PodcastLLMAgent
from ..queue_manager import QueueManager

logger = logging.getLogger(__name__)

class MCPPodcastAgent:
    """MCP-based Podcast Agent with modular server architecture"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        
        # Initialize MCP client
        self.mcp_client = MCPClient()
        
        # Initialize component services
        self._setup_services()
        
        # Initialize MCP servers
        self._setup_mcp_servers()
        
        # Episode memory
        self.processed_episodes = set()
        
        logger.info("MCP Podcast Agent initialized successfully")
    
    def _setup_services(self):
        """Initialize the underlying services"""
        # Spotify client
        self.spotify_client = SpotifyClient(
            client_id=self.config.spotify_client_id,
            client_secret=self.config.spotify_client_secret,
            redirect_uri=self.config.spotify_redirect_uri
        )
        
        # LLM agent
        self.llm_agent = PodcastLLMAgent(
            openai_api_key=self.config.openai_api_key
        )
        
        # Queue manager
        self.queue_manager = QueueManager()
    
    def _setup_mcp_servers(self):
        """Setup and register MCP servers"""
        # Spotify MCP server
        spotify_server = SpotifyMCPServer(self.spotify_client)
        self.mcp_client.register_server("spotify", spotify_server)
        
        # LLM MCP server
        llm_server = LLMMCPServer(self.llm_agent)
        self.mcp_client.register_server("llm", llm_server)
        
        # Queue MCP server
        queue_server = QueueMCPServer(self.queue_manager)
        self.mcp_client.register_server("queue", queue_server)
    
    def add_podcast_preference(self, preference: PodcastPreference) -> None:
        """Add a new podcast preference"""
        self.config.podcast_preferences.append(preference)
        logger.info(f"Added new podcast preference: {preference}")
    
    def get_podcast_preferences(self) -> List[PodcastPreference]:
        """Get all podcast preferences"""
        return self.config.podcast_preferences
    
    def reset_processed_episodes(self) -> None:
        """Reset the list of processed episodes"""
        self.processed_episodes = set()
        logger.info("Reset processed episodes list")
    
    async def check_for_new_episodes(self) -> List[Dict[str, Any]]:
        """Check for new episodes using MCP servers"""
        logger.info("Checking for new episodes via MCP...")
        
        relevant_episodes = []
        processed_count = 0
        
        for preference in self.config.podcast_preferences:
            logger.info(f"Processing preference: {preference}")
            
            # Get episodes based on preference type
            episodes = await self._get_episodes_for_preference(preference)
            
            # Evaluate each episode
            for episode in episodes:
                try:
                    # Safety checks
                    if not isinstance(episode, dict) or 'id' not in episode:
                        continue
                    
                    # Skip if already processed
                    if episode['id'] in self.processed_episodes:
                        continue
                    
                    self.processed_episodes.add(episode['id'])
                    
                    # Check duration constraints
                    if not self._check_duration_constraints(episode, preference):
                        continue
                    
                    # Evaluate relevance using LLM MCP server
                    evaluation = await self.mcp_client.send_request(
                        "llm", "tools/call",
                        {
                            "name": "evaluate_episode",
                            "arguments": {
                                "episode": episode,
                                "preferences": [preference.dict(exclude_none=True)]
                            }
                        }
                    )
                    
                    relevance_score = evaluation["relevance_score"]
                    reasoning = evaluation["reasoning"]
                    
                    logger.info(f"Episode '{episode.get('name', 'Unknown')}' relevance: {relevance_score:.2f}")
                    
                    # If episode is relevant enough, add it
                    if relevance_score >= self.config.relevance_threshold:
                        # Generate summary using LLM MCP server
                        summary_result = await self.mcp_client.send_request(
                            "llm", "tools/call",
                            {
                                "name": "generate_summary",
                                "arguments": {"episode": episode}
                            }
                        )
                        
                        relevant_episodes.append({
                            'episode': episode,
                            'relevance_score': relevance_score,
                            'reasoning': reasoning,
                            'summary': summary_result["summary"],
                            'preference': str(preference)
                        })
                        
                        processed_count += 1
                        
                        if processed_count >= self.config.max_episodes_per_run:
                            break
                
                except Exception as e:
                    logger.error(f"Error processing episode: {str(e)}")
                    continue
            
            if processed_count >= self.config.max_episodes_per_run:
                break
        
        # Sort by relevance score
        relevant_episodes.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_episodes
    
    async def _get_episodes_for_preference(self, preference: PodcastPreference) -> List[Dict[str, Any]]:
        """Get episodes for a specific preference using MCP"""
        episodes = []
        
        if preference.show_id:
            # Get episodes directly by show ID
            episodes = await self.mcp_client.send_request(
                "spotify", "tools/call",
                {
                    "name": "get_show_episodes",
                    "arguments": {"show_id": preference.show_id, "limit": 10}
                }
            )
        
        elif preference.show_name:
            # Search for show by name, then get episodes
            shows = await self.mcp_client.send_request(
                "spotify", "tools/call",
                {
                    "name": "search_podcasts",
                    "arguments": {"query": preference.show_name, "limit": 1}
                }
            )
            
            if shows:
                show_id = shows[0]['id']
                episodes = await self.mcp_client.send_request(
                    "spotify", "tools/call",
                    {
                        "name": "get_show_episodes",
                        "arguments": {"show_id": show_id, "limit": 10}
                    }
                )
        
        elif preference.topics:
            # Search for shows by topics, then get episodes
            topics_query = " OR ".join(preference.topics)
            shows = await self.mcp_client.send_request(
                "spotify", "tools/call",
                {
                    "name": "search_podcasts",
                    "arguments": {"query": topics_query, "limit": 5}
                }
            )
            
            for show in shows:
                show_episodes = await self.mcp_client.send_request(
                    "spotify", "tools/call",
                    {
                        "name": "get_show_episodes",
                        "arguments": {"show_id": show['id'], "limit": 3}
                    }
                )
                episodes.extend(show_episodes)
        
        return episodes
    
    def _check_duration_constraints(self, episode: Dict[str, Any], preference: PodcastPreference) -> bool:
        """Check if episode meets duration constraints"""
        if not (preference.min_duration_minutes or preference.max_duration_minutes):
            return True
        
        duration_ms = episode.get('duration_ms', 0)
        duration_minutes = duration_ms / 60000
        
        if preference.min_duration_minutes and duration_minutes < preference.min_duration_minutes:
            return False
        
        if preference.max_duration_minutes and duration_minutes > preference.max_duration_minutes:
            return False
        
        return True
    
    async def check_spotify_active_device(self) -> bool:
        """Check if there's an active Spotify device using MCP"""
        try:
            devices_data = await self.mcp_client.send_request(
                "spotify", "tools/call",
                {"name": "get_devices", "arguments": {}}
            )
            
            devices = devices_data.get('devices', [])
            for device in devices:
                if device.get('is_active'):
                    logger.info(f"Found active Spotify device: {device.get('name')}")
                    return True
            
            logger.warning("No active Spotify devices found")
            return False
            
        except Exception as e:
            logger.error(f"Error checking Spotify devices: {str(e)}")
            return False
    
    async def add_episodes_to_queue(self, episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add episodes to Spotify queue using MCP"""
        logger.info(f"Adding {len(episodes)} episodes to queue...")
        
        # Check for active device
        has_active_device = await self.check_spotify_active_device()
        
        # If no active device, store in pending queue
        if not has_active_device and episodes:
            logger.info("No active Spotify device - storing episodes in pending queue")
            await self.mcp_client.send_request(
                "queue", "tools/call",
                {
                    "name": "add_pending",
                    "arguments": {"episodes": episodes}
                }
            )
            return []
        
        added_episodes = []
        
        for episode_data in episodes:
            try:
                episode = episode_data['episode']
                
                if 'uri' not in episode:
                    logger.error(f"Episode missing URI: {episode.get('name', 'Unknown')}")
                    continue
                
                # Add to Spotify queue via MCP
                result = await self.mcp_client.send_request(
                    "spotify", "tools/call",
                    {
                        "name": "add_to_queue",
                        "arguments": {"episode_uri": episode['uri']}
                    }
                )
                
                if result.get("success"):
                    added_episodes.append(episode_data)
                    logger.info(f"Added episode to queue: {episode.get('name', 'Unknown')}")
                else:
                    logger.error(f"Failed to add episode to queue: {episode.get('name', 'Unknown')}")
                    # Store failed episodes in pending queue
                    await self.mcp_client.send_request(
                        "queue", "tools/call",
                        {
                            "name": "add_pending",
                            "arguments": {"episodes": [episode_data]}
                        }
                    )
                
            except Exception as e:
                logger.error(f"Error adding episode to queue: {str(e)}")
                # Store failed episodes in pending queue
                await self.mcp_client.send_request(
                    "queue", "tools/call",
                    {
                        "name": "add_pending",
                        "arguments": {"episodes": [episode_data]}
                    }
                )
                continue
        
        return added_episodes
    
    async def process_pending_episodes(self) -> Dict[str, Any]:
        """Process pending episodes using MCP"""
        try:
            # Get pending episodes
            pending_data = await self.mcp_client.send_request(
                "queue", "tools/call",
                {"name": "get_pending", "arguments": {}}
            )
            
            pending_episodes = pending_data.get("episodes", [])
            if not pending_episodes:
                return {
                    'status': 'success',
                    'message': 'No pending episodes to process',
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.info(f"Processing {len(pending_episodes)} pending episodes")
            
            # Check for active device
            has_active_device = await self.check_spotify_active_device()
            if not has_active_device:
                return {
                    'status': 'warning',
                    'message': 'No active Spotify device found - cannot process pending episodes',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Process pending episodes
            added_episodes = []
            added_episode_ids = []
            
            for episode_data in pending_episodes:
                try:
                    episode = episode_data['episode']
                    
                    if 'uri' not in episode:
                        continue
                    
                    # Add to Spotify queue
                    result = await self.mcp_client.send_request(
                        "spotify", "tools/call",
                        {
                            "name": "add_to_queue",
                            "arguments": {"episode_uri": episode['uri']}
                        }
                    )
                    
                    if result.get("success"):
                        added_episodes.append(episode_data)
                        added_episode_ids.append(episode['id'])
                        logger.info(f"Added pending episode to queue: {episode.get('name', 'Unknown')}")
                    
                except Exception as e:
                    logger.error(f"Error adding pending episode: {str(e)}")
                    continue
            
            # Remove successfully processed episodes from pending queue
            if added_episode_ids:
                await self.mcp_client.send_request(
                    "queue", "tools/call",
                    {
                        "name": "remove_processed",
                        "arguments": {"episode_ids": added_episode_ids}
                    }
                )
            
            return {
                'status': 'success',
                'message': f'Processed {len(added_episodes)} of {len(pending_episodes)} pending episodes',
                'episodes': added_episodes,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing pending episodes: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def run(self) -> Dict[str, Any]:
        """Run the podcast discovery and queueing process"""
        logger.info("Starting MCP podcast agent run...")
        
        if not self.config.podcast_preferences:
            return {
                'status': 'error',
                'message': 'No podcast preferences configured',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Step 1: Process any pending episodes first
            pending_result = await self.process_pending_episodes()
            if pending_result['status'] == 'success' and pending_result.get('episodes'):
                return pending_result
            
            # Step 2: Discover new relevant episodes
            relevant_episodes = await self.check_for_new_episodes()
            
            # Step 3: Add episodes to queue
            if relevant_episodes:
                added_episodes = await self.add_episodes_to_queue(relevant_episodes)
                
                return {
                    'status': 'success',
                    'message': f'Added {len(added_episodes)} episodes to queue',
                    'episodes': added_episodes,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'success',
                    'message': 'No new relevant episodes found',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error running MCP agent: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }