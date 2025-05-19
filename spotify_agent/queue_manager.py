import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class QueueManager:
    """Manages episode queuing when no active Spotify device is available"""
    
    def __init__(self, cache_dir: str = None):
        """Initialize the queue manager with a cache directory"""
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser("~"), ".spotify_podcast_agent")
        self.pending_file = os.path.join(self.cache_dir, "pending_episodes.json")
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load any pending episodes
        self.pending_episodes = self._load_pending_episodes()
        
    def _load_pending_episodes(self) -> List[Dict[str, Any]]:
        """Load pending episodes from disk"""
        if not os.path.exists(self.pending_file):
            return []
            
        try:
            with open(self.pending_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading pending episodes: {str(e)}")
            return []
    
    def _save_pending_episodes(self) -> None:
        """Save pending episodes to disk"""
        try:
            with open(self.pending_file, 'w') as f:
                json.dump(self.pending_episodes, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving pending episodes: {str(e)}")
    
    def add_pending_episodes(self, episodes: List[Dict[str, Any]]) -> None:
        """Add episodes to the pending queue"""
        # Add timestamp to track when episodes were added
        for episode in episodes:
            episode_copy = episode.copy()
            episode_copy['added_at'] = datetime.now().isoformat()
            self.pending_episodes.append(episode_copy)
        
        # Save to disk
        self._save_pending_episodes()
        logger.info(f"Added {len(episodes)} episodes to pending queue")
    
    def get_pending_episodes(self) -> List[Dict[str, Any]]:
        """Get all pending episodes"""
        return self.pending_episodes
    
    def remove_processed_episodes(self, episode_ids: List[str]) -> None:
        """Remove episodes that have been successfully added to queue"""
        original_count = len(self.pending_episodes)
        self.pending_episodes = [
            e for e in self.pending_episodes 
            if e['episode']['id'] not in episode_ids
        ]
        
        # Save changes to disk
        self._save_pending_episodes()
        logger.info(f"Removed {original_count - len(self.pending_episodes)} episodes from pending queue")
    
    def send_notification(self, user_email: Optional[str] = None) -> None:
        """Send a notification about pending episodes"""
        if not self.pending_episodes:
            return
            
        count = len(self.pending_episodes)
        message = f"You have {count} podcast episodes ready to be added to your Spotify queue."
        
        # Log notification
        logger.info(f"Notification: {message}")
        
        # If user email is provided, send email notification
        # This would integrate with an email sending service
        if user_email:
            self._send_email_notification(user_email, message)
    
    def _send_email_notification(self, email: str, message: str) -> None:
        """Send an email notification (placeholder)"""
        # In a real implementation, this would use an email service like SendGrid
        logger.info(f"Would send email to {email}: {message}")
        # Add your email sending code here