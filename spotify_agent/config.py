# Update your spotify_agent/config.py to use faster settings for production:

import os
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PodcastPreference(BaseModel):
    """Model to store podcast preferences"""
    show_name: Optional[str] = None
    show_id: Optional[str] = None
    topics: Optional[List[str]] = None
    min_duration_minutes: Optional[int] = None
    max_duration_minutes: Optional[int] = None
    
    def __str__(self):
        if self.show_name:
            return f"Podcast: {self.show_name}"
        else:
            return f"Topics: {', '.join(self.topics or [])}"

class AgentConfig(BaseModel):
    """Configuration for the podcast agent"""
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    spotify_client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    spotify_client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    spotify_redirect_uri: str = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8000/callback")
    check_frequency: str = "daily"  # 'daily' or 'weekly'
    relevance_threshold: float = 0.6  # Lower threshold for faster processing
    max_episodes_per_run: int = 3     # Reduced from 5 to 3 for faster processing
    use_vector_memory: bool = False   # Keep false for faster startup
    podcast_preferences: List[PodcastPreference] = []

    class Config:
        env_file = ".env"