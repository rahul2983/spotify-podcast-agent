import pytest
from pydantic import ValidationError
from spotify_agent.config import AgentConfig, PodcastPreference

@pytest.mark.unit
class TestPodcastPreference:
    def test_preference_with_show_name(self):
        pref = PodcastPreference(show_name="Test Show")
        assert pref.show_name == "Test Show"
        assert pref.topics is None
        
    def test_preference_with_topics(self):
        pref = PodcastPreference(topics=["tech", "AI"])
        assert pref.topics == ["tech", "AI"]
        assert pref.show_name is None
        
    def test_preference_with_duration_constraints(self):
        pref = PodcastPreference(
            show_name="Test Show",
            min_duration_minutes=10,
            max_duration_minutes=60
        )
        assert pref.min_duration_minutes == 10
        assert pref.max_duration_minutes == 60
        
    def test_preference_string_representation(self):
        pref1 = PodcastPreference(show_name="Test Show")
        assert str(pref1) == "Podcast: Test Show"
        
        pref2 = PodcastPreference(topics=["tech", "AI"])
        assert str(pref2) == "Topics: tech, AI"

@pytest.mark.unit 
class TestAgentConfig:
    def test_default_config(self):
        config = AgentConfig()
        assert config.check_frequency == "daily"
        assert config.relevance_threshold == 0.7
        assert config.max_episodes_per_run == 5
        assert config.use_vector_memory is False
        
    def test_config_with_preferences(self):
        prefs = [PodcastPreference(show_name="Test Show")]
        config = AgentConfig(podcast_preferences=prefs)
        assert len(config.podcast_preferences) == 1
        assert config.podcast_preferences[0].show_name == "Test Show"