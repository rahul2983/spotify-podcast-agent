"""
Enhanced MCP-based Podcast Agent with Email summaries and Calendar integration
"""
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime, timedelta

from ..config import AgentConfig, PodcastPreference
from ..mcp_server.protocol import MCPClient
from ..mcp_server.spotify_server import SpotifyMCPServer
from ..mcp_server.llm_server import LLMMCPServer
from ..mcp_server.queue_server import QueueMCPServer
from ..mcp_server.email_server import EmailMCPServer
from ..mcp_server.calendar_server import CalendarMCPServer
from ..spotify_client import SpotifyClient
from ..llm_agent import PodcastLLMAgent
from ..queue_manager import QueueManager

logger = logging.getLogger(__name__)

class EnhancedMCPPodcastAgent:
    """Enhanced MCP-based Podcast Agent with Email and Calendar features"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        
        # Initialize MCP client
        self.mcp_client = MCPClient()
        
        # Initialize component services
        self._setup_services()
        
        # Initialize MCP servers (including new ones)
        self._setup_mcp_servers()
        
        # Episode memory
        self.processed_episodes = set()
        
        # Enhanced features
        self.email_enabled = bool(config.user_email)
        self.calendar_enabled = True  # Always enabled for scheduling
        
        logger.info("Enhanced MCP Podcast Agent initialized successfully")
    
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
        """Setup and register MCP servers including new ones"""
        # Core servers
        spotify_server = SpotifyMCPServer(self.spotify_client)
        self.mcp_client.register_server("spotify", spotify_server)
        
        llm_server = LLMMCPServer(self.llm_agent)
        self.mcp_client.register_server("llm", llm_server)
        
        queue_server = QueueMCPServer(self.queue_manager)
        self.mcp_client.register_server("queue", queue_server)
        
        # New enhanced servers
        email_server = EmailMCPServer()
        self.mcp_client.register_server("email", email_server)
        
        calendar_server = CalendarMCPServer()
        self.mcp_client.register_server("calendar", calendar_server)
        
        logger.info("All MCP servers registered: spotify, llm, queue, email, calendar")
    
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
                            'preference': str(preference),
                            'discovered_at': datetime.now().isoformat()
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
            episodes = await self.mcp_client.send_request(
                "spotify", "tools/call",
                {
                    "name": "get_show_episodes",
                    "arguments": {"show_id": preference.show_id, "limit": 10}
                }
            )
        
        elif preference.show_name:
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
            
            # Send notification if email is enabled
            if self.email_enabled:
                await self._send_pending_notification(episodes)
            
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
    
    async def _send_pending_notification(self, episodes: List[Dict[str, Any]]) -> None:
        """Send notification about pending episodes"""
        if not self.email_enabled or not episodes:
            return
        
        try:
            await self.mcp_client.send_request(
                "email", "tools/call",
                {
                    "name": "send_notification",
                    "arguments": {
                        "to_email": self.config.user_email,
                        "subject": f"🎵 {len(episodes)} Podcast Episodes Ready",
                        "message": f"I found {len(episodes)} great podcast episodes for you, but no active Spotify device was found. They've been saved and will be added to your queue when you next open Spotify!"
                    }
                }
            )
            logger.info(f"Sent pending episodes notification to {self.config.user_email}")
        except Exception as e:
            logger.error(f"Failed to send pending notification: {str(e)}")
    
    async def send_episode_summary_email(self, episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send email summary of new episodes"""
        if not self.email_enabled or not episodes:
            return {"success": False, "message": "Email not enabled or no episodes"}
        
        try:
            result = await self.mcp_client.send_request(
                "email", "tools/call",
                {
                    "name": "send_summary_email",
                    "arguments": {
                        "to_email": self.config.user_email,
                        "episodes": episodes,
                        "subject": f"🎵 Your Daily Podcast Summary - {len(episodes)} New Episodes"
                    }
                }
            )
            return result
        except Exception as e:
            logger.error(f"Failed to send episode summary email: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def send_weekly_digest(self, episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send weekly podcast digest"""
        if not self.email_enabled:
            return {"success": False, "message": "Email not enabled"}
        
        try:
            # Get listening stats for the week
            stats = await self.mcp_client.send_request(
                "calendar", "tools/call",
                {
                    "name": "get_listening_stats",
                    "arguments": {"period": "week"}
                }
            )
            
            result = await self.mcp_client.send_request(
                "email", "tools/call",
                {
                    "name": "send_weekly_digest",
                    "arguments": {
                        "to_email": self.config.user_email,
                        "episodes": episodes,
                        "stats": stats
                    }
                }
            )
            return result
        except Exception as e:
            logger.error(f"Failed to send weekly digest: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def schedule_listening_time(self, day_of_week: str, start_time: str, 
                                    duration_minutes: int, title: str = None) -> Dict[str, Any]:
        """Schedule dedicated podcast listening time"""
        try:
            result = await self.mcp_client.send_request(
                "calendar", "tools/call",
                {
                    "name": "schedule_listening_time",
                    "arguments": {
                        "day_of_week": day_of_week,
                        "start_time": start_time,
                        "duration_minutes": duration_minutes,
                        "title": title or "Podcast Listening Time"
                    }
                }
            )
            return result
        except Exception as e:
            logger.error(f"Failed to schedule listening time: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def get_listening_schedule(self) -> Dict[str, Any]:
        """Get current podcast listening schedule"""
        try:
            result = await self.mcp_client.send_request(
                "calendar", "tools/call",
                {"name": "get_listening_schedule", "arguments": {}}
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get listening schedule: {str(e)}")
            return {"schedule": [], "error": str(e)}
    
    async def suggest_optimal_schedule(self, user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get optimal schedule suggestions based on current queue"""
        try:
            # Get current queue
            pending_data = await self.mcp_client.send_request(
                "queue", "tools/call",
                {"name": "get_pending", "arguments": {}}
            )
            
            episode_queue = pending_data.get("episodes", [])
            
            result = await self.mcp_client.send_request(
                "calendar", "tools/call",
                {
                    "name": "suggest_optimal_schedule",
                    "arguments": {
                        "user_preferences": user_preferences or {},
                        "episode_queue": episode_queue
                    }
                }
            )
            return result
        except Exception as e:
            logger.error(f"Failed to suggest optimal schedule: {str(e)}")
            return {"suggestions": [], "error": str(e)}
    
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
    
    async def run(self, send_email_summary: bool = True) -> Dict[str, Any]:
        """Run the enhanced podcast discovery and queueing process"""
        logger.info("Starting enhanced MCP podcast agent run...")
        
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
                # If we processed pending episodes, send summary and return
                if send_email_summary and self.email_enabled:
                    await self.send_episode_summary_email(pending_result['episodes'])
                return pending_result
            
            # Step 2: Discover new relevant episodes
            relevant_episodes = await self.check_for_new_episodes()
            
            # Step 3: Add episodes to queue
            if relevant_episodes:
                added_episodes = await self.add_episodes_to_queue(relevant_episodes)
                
                # Step 4: Send email summary if enabled and episodes were added
                email_result = None
                if send_email_summary and self.email_enabled and (added_episodes or not await self.check_spotify_active_device()):
                    # Send email for added episodes, or all relevant episodes if they went to pending
                    episodes_to_summarize = added_episodes if added_episodes else relevant_episodes
                    email_result = await self.send_episode_summary_email(episodes_to_summarize)
                
                # Step 5: Update calendar with listening history
                await self._update_listening_history(added_episodes)
                
                return {
                    'status': 'success',
                    'message': f'Added {len(added_episodes)} episodes to queue',
                    'episodes': added_episodes,
                    'email_sent': email_result.get('success', False) if email_result else False,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'success',
                    'message': 'No new relevant episodes found',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error running enhanced MCP agent: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_weekly_digest(self) -> Dict[str, Any]:
        """Run weekly digest process"""
        logger.info("Running weekly digest...")
        
        try:
            # Get this week's episodes from calendar/history
            stats = await self.mcp_client.send_request(
                "calendar", "tools/call",
                {
                    "name": "get_listening_stats",
                    "arguments": {"period": "week"}
                }
            )
            
            # For now, use recent episodes as a placeholder
            # In a full implementation, you'd track actual listening history
            pending_data = await self.mcp_client.send_request(
                "queue", "tools/call",
                {"name": "get_pending", "arguments": {}}
            )
            
            recent_episodes = pending_data.get("episodes", [])
            
            if self.email_enabled:
                digest_result = await self.send_weekly_digest(recent_episodes)
                return {
                    'status': 'success',
                    'message': 'Weekly digest sent',
                    'digest_sent': digest_result.get('success', False),
                    'episodes_count': len(recent_episodes),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'info',
                    'message': 'Weekly digest not sent - email not configured',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error running weekly digest: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def _update_listening_history(self, episodes: List[Dict[str, Any]]) -> None:
        """Update listening history in calendar"""
        if not episodes:
            return
        
        try:
            # This would update the calendar with actual listening data
            # For now, we'll just log it
            logger.info(f"Would update listening history with {len(episodes)} episodes")
            
            # In a full implementation, you'd:
            # 1. Track when episodes were actually listened to
            # 2. Update calendar data with listening sessions
            # 3. Calculate listening patterns and statistics
            
        except Exception as e:
            logger.error(f"Error updating listening history: {str(e)}")
    
    async def get_mcp_servers_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers"""
        servers_status = {}
        
        for server_name in ["spotify", "llm", "queue", "email", "calendar"]:
            try:
                # Test server by listing tools
                tools = await self.mcp_client.send_request(
                    server_name, "tools/list", {}
                )
                servers_status[server_name] = {
                    "status": "online",
                    "tools_count": len(tools.get("tools", [])),
                    "error": None
                }
            except Exception as e:
                servers_status[server_name] = {
                    "status": "error",
                    "tools_count": 0,
                    "error": str(e)
                }
        
        return {
            "servers": servers_status,
            "total_servers": len(servers_status),
            "online_servers": len([s for s in servers_status.values() if s["status"] == "online"]),
            "email_enabled": self.email_enabled,
            "calendar_enabled": self.calendar_enabled
        }