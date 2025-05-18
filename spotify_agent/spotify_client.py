import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SpotifyClient:
    """Client for interacting with Spotify API"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """Initialize Spotify client with authentication details"""
        self.scope = "user-read-playback-state user-modify-playback-state user-library-read user-read-recently-played playlist-read-private"
        
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=self.scope
            ))
            logger.info("Spotify client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {str(e)}")
            raise
    
    def search_podcast(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for podcasts by name or keywords"""
        try:
            results = self.sp.search(q=query, type='show', limit=limit)
            return results.get('shows', {}).get('items', [])
        except Exception as e:
            logger.error(f"Error searching for podcasts: {str(e)}")
            return []
    
    def get_show_by_id(self, show_id: str) -> Optional[Dict[str, Any]]:
        """Get podcast show details by ID"""
        try:
            return self.sp.show(show_id)
        except Exception as e:
            logger.error(f"Error getting podcast show {show_id}: {str(e)}")
            return None
    
    def get_show_episodes(self, show_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get episodes for a specific podcast show"""
        try:
            results = self.sp.show_episodes(show_id, limit=limit)
            return results.get('items', [])
        except Exception as e:
            logger.error(f"Error getting episodes for show {show_id}: {str(e)}")
            return []
    
    def add_to_queue(self, episode_uri: str) -> bool:
        """Add a podcast episode to the user's playback queue"""
        try:
            self.sp.add_to_queue(uri=episode_uri)
            logger.info(f"Successfully added episode {episode_uri} to queue")
            return True
        except Exception as e:
            logger.error(f"Error adding episode to queue: {str(e)}")
            return False
    
    def get_recently_played(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's recently played tracks/episodes"""
        try:
            results = self.sp.current_user_recently_played(limit=limit)
            return results.get('items', [])
        except Exception as e:
            logger.error(f"Error getting recently played: {str(e)}")
            return []
    
    def get_current_user_profile(self) -> Optional[Dict[str, Any]]:
        """Get the current user's Spotify profile"""
        try:
            return self.sp.current_user()
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None