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
            
    def get_devices(self) -> Dict[str, Any]:
        """Get the user's available Spotify devices"""
        try:
            return self.sp.devices()
        except Exception as e:
            logger.error(f"Error getting devices: {str(e)}")
            return {"devices": []}
            
    def start_playback(self, device_id: Optional[str] = None) -> bool:
        """Start playback on a device"""
        try:
            # Try to resume playback if possible
            self.sp.start_playback(device_id=device_id)
            logger.info(f"Successfully started playback on device {device_id if device_id else 'default'}")
            return True
        except Exception as e:
            # If we can't resume, try to play a fallback track
            try:
                # Find a track to play - user's first saved track or a popular track
                tracks = self.sp.current_user_saved_tracks(limit=1).get('items', [])
                
                if tracks:
                    track_uri = tracks[0]['track']['uri']
                else:
                    # Default to a popular track if user has no saved tracks
                    results = self.sp.search(q='genre:pop', limit=1, type='track')
                    track_uri = results['tracks']['items'][0]['uri']
                
                self.sp.start_playback(device_id=device_id, uris=[track_uri])
                logger.info(f"Started playback with fallback track on device {device_id if device_id else 'default'}")
                return True
                
            except Exception as inner_e:
                logger.error(f"Error starting playback: {str(e)} -> {str(inner_e)}")
                return False
                
    def transfer_playback(self, device_id: Optional[str] = None) -> bool:
        """Transfer playback to another device"""
        try:
            # If no device_id provided, get available devices
            if not device_id:
                devices = self.get_devices().get('devices', [])
                if not devices:
                    logger.error("No available devices to transfer playback to")
                    return False
                    
                # Filter for available (not active) devices
                available_devices = [d for d in devices if not d.get('is_active', False)]
                if not available_devices:
                    logger.error("No inactive devices available to transfer playback to")
                    return False
                    
                device_id = available_devices[0]['id']
                
            # Transfer playback to the device
            self.sp.transfer_playback(device_id=device_id, force_play=True)
            logger.info(f"Successfully transferred playback to device {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error transferring playback: {str(e)}")
            return False