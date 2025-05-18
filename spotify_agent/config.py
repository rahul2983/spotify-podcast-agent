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
    relevance_threshold: float = 0.7  # 0.0 to 1.0, how relevant episode must be to be added
    max_episodes_per_run: int = 5  # Maximum episodes to add in a single run
    use_vector_memory: bool = False  # Whether to store episode data in vector DB
    podcast_preferences: List[PodcastPreference] = []

    class Config:
        env_file = ".env"