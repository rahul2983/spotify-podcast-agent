from spotify_agent.config import AgentConfig, PodcastPreference
from spotify_agent.spotify_client import SpotifyClient
from spotify_agent.llm_agent import PodcastLLMAgent
from typing import List, Dict, Any, Optional
import logging
import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("podcast_agent.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class PodcastAgent:
    """Main agent that orchestrates podcast discovery and management"""
    
    def __init__(self, config: AgentConfig):
        """Initialize the podcast agent with configuration"""
        self.config = config
        
        # Initialize Spotify client
        self.spotify = SpotifyClient(
            client_id=config.spotify_client_id,
            client_secret=config.spotify_client_secret,
            redirect_uri=config.spotify_redirect_uri
        )
        
        # Initialize LLM agent
        self.llm_agent = PodcastLLMAgent(
            openai_api_key=config.openai_api_key
        )
        
        # Episode memory to avoid recommending duplicates
        self.processed_episodes = set()
        
        # Default to a lower relevance threshold to catch more episodes
        if config.relevance_threshold > 0.7:
            config.relevance_threshold = 0.5
            logger.info(f"Setting default relevance threshold to 0.5")
        
        logger.info("Podcast agent initialized successfully")
    
    def add_podcast_preference(self, preference: PodcastPreference) -> None:
        """Add a new podcast preference"""
        self.config.podcast_preferences.append(preference)
        logger.info(f"Added new podcast preference: {preference}")
    
    def get_podcast_preferences(self) -> List[PodcastPreference]:
        """Get all podcast preferences"""
        return self.config.podcast_preferences
    
    def _convert_preference_to_dict(self, preference: PodcastPreference) -> Dict[str, Any]:
        """Convert preference model to dictionary for LLM evaluation"""
        return preference.dict(exclude_none=True)
    
    def reset_processed_episodes(self) -> None:
        """Reset the list of processed episodes"""
        self.processed_episodes = set()
        logger.info("Reset processed episodes list")
    
    def check_for_new_episodes(self) -> List[Dict[str, Any]]:
        """Check for new episodes based on user preferences"""
        logger.info("Checking for new episodes...")
        
        relevant_episodes = []
        processed_count = 0
        
        # Process each podcast preference
        for preference in self.config.podcast_preferences:
            logger.info(f"Processing preference: {preference}")
            
            # If show_id is provided, get episodes directly
            if preference.show_id:
                try:
                    episodes = self.spotify.get_show_episodes(preference.show_id, limit=10)
                    logger.info(f"Found {len(episodes)} episodes for show ID {preference.show_id}")
                except Exception as e:
                    logger.error(f"Error fetching episodes for show ID {preference.show_id}: {str(e)}")
                    episodes = []
            
            # If show_name is provided, search for it first
            elif preference.show_name:
                try:
                    shows = self.spotify.search_podcast(preference.show_name, limit=1)
                    if not shows:
                        logger.warning(f"No shows found for name: {preference.show_name}")
                        continue
                    
                    show_id = shows[0]['id']
                    episodes = self.spotify.get_show_episodes(show_id, limit=10)
                    logger.info(f"Found {len(episodes)} episodes for show name {preference.show_name}")
                except Exception as e:
                    logger.error(f"Error fetching episodes for show name {preference.show_name}: {str(e)}")
                    episodes = []
            
            # If topics are provided, search for relevant shows
            elif preference.topics:
                try:
                    # Join topics with OR for search
                    topics_query = " OR ".join(preference.topics)
                    shows = self.spotify.search_podcast(topics_query, limit=5)
                    
                    episodes = []
                    for show in shows:
                        try:
                            show_episodes = self.spotify.get_show_episodes(show['id'], limit=3)
                            episodes.extend(show_episodes)
                        except Exception as e:
                            logger.error(f"Error fetching episodes for show {show.get('name', 'Unknown')}: {str(e)}")
                    
                    logger.info(f"Found {len(episodes)} episodes for topics: {preference.topics}")
                except Exception as e:
                    logger.error(f"Error searching for shows with topics {preference.topics}: {str(e)}")
                    episodes = []
            
            else:
                logger.warning("Skipping preference with no show_id, show_name, or topics")
                continue
            
            # Evaluate each episode
            for episode in episodes:
                try:
                    # Safety check: Ensure episode is a dictionary and has an ID
                    if not isinstance(episode, dict):
                        logger.warning(f"Skipping episode - not a dictionary: {episode}")
                        continue
                    
                    if 'id' not in episode:
                        logger.warning(f"Skipping episode - no ID found: {episode.get('name', 'Unknown')}")
                        continue
                    
                    # Skip if already processed
                    if episode['id'] in self.processed_episodes:
                        logger.info(f"Skipping already processed episode: {episode.get('name', 'Unknown')}")
                        continue
                    
                    # Mark as processed
                    self.processed_episodes.add(episode['id'])
                    
                    # Check duration constraints if specified
                    if preference.min_duration_minutes or preference.max_duration_minutes:
                        duration_ms = episode.get('duration_ms', 0)
                        duration_minutes = duration_ms / 60000
                        
                        if preference.min_duration_minutes and duration_minutes < preference.min_duration_minutes:
                            logger.info(f"Skipping episode {episode.get('name', 'Unknown')} - too short ({duration_minutes:.1f} min)")
                            continue
                        
                        if preference.max_duration_minutes and duration_minutes > preference.max_duration_minutes:
                            logger.info(f"Skipping episode {episode.get('name', 'Unknown')} - too long ({duration_minutes:.1f} min)")
                            continue
                    
                    # Evaluate relevance using LLM
                    preference_dict = self._convert_preference_to_dict(preference)
                    relevance_score, reasoning = self.llm_agent.evaluate_episode_relevance(
                        episode, [preference_dict]
                    )
                    
                    logger.info(f"Episode '{episode.get('name', 'Unknown')}' relevance: {relevance_score:.2f} - {reasoning}")
                    
                    # If episode is relevant enough, add it to the list
                    if relevance_score >= self.config.relevance_threshold:
                        # Generate a summary
                        summary = self.llm_agent.generate_episode_summary(episode)
                        
                        relevant_episodes.append({
                            'episode': episode,
                            'relevance_score': relevance_score,
                            'reasoning': reasoning,
                            'summary': summary,
                            'preference': str(preference)
                        })
                        
                        processed_count += 1
                        
                        # Stop if we've reached the maximum episodes to process in one run
                        if processed_count >= self.config.max_episodes_per_run:
                            logger.info(f"Reached max episodes per run ({self.config.max_episodes_per_run})")
                            break
                except Exception as e:
                    logger.error(f"Error processing episode {episode.get('name', 'Unknown') if isinstance(episode, dict) else 'Unknown'}: {str(e)}")
                    continue
            
            # Stop processing preferences if we've reached the limit
            if processed_count >= self.config.max_episodes_per_run:
                break
        
        # Sort episodes by relevance score (highest first)
        relevant_episodes.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return relevant_episodes
    
    def add_episodes_to_queue(self, episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add relevant episodes to the Spotify queue"""
        logger.info(f"Adding {len(episodes)} episodes to queue...")
        
        added_episodes = []
        
        for episode_data in episodes:
            try:
                episode = episode_data['episode']
                
                # Safety check: Ensure episode has the required URI
                if 'uri' not in episode:
                    logger.error(f"Cannot add episode to queue - missing URI: {episode.get('name', 'Unknown')}")
                    continue
                    
                episode_uri = episode['uri']
                
                success = self.spotify.add_to_queue(episode_uri)
                
                if success:
                    added_episodes.append(episode_data)
                    logger.info(f"Added episode to queue: {episode.get('name', 'Unknown')}")
                else:
                    logger.error(f"Failed to add episode to queue: {episode.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error adding episode to queue: {str(e)}")
                continue
        
        return added_episodes
    
    def run(self) -> Dict[str, Any]:
        """Run the podcast discovery and queueing process"""
        logger.info("Starting podcast agent run...")
        
        # Check if we have preferences configured
        if not self.config.podcast_preferences:
            return {
                'status': 'error',
                'message': 'No podcast preferences configured',
                'timestamp': datetime.datetime.now().isoformat()
            }
        
        try:
            # Step 1: Discover new relevant episodes
            relevant_episodes = self.check_for_new_episodes()
            
            # Step 2: Add episodes to queue
            if relevant_episodes:
                added_episodes = self.add_episodes_to_queue(relevant_episodes)
                
                return {
                    'status': 'success',
                    'message': f'Added {len(added_episodes)} episodes to queue',
                    'episodes': added_episodes,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'success',
                    'message': 'No new relevant episodes found',
                    'timestamp': datetime.datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error running agent: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error: {str(e)}',
                'timestamp': datetime.datetime.now().isoformat()
            }