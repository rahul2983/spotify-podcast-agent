import pytest
from unittest.mock import Mock, patch
from spotify_agent.llm_agent import PodcastLLMAgent

@pytest.mark.unit
class TestPodcastLLMAgent:
    @patch('spotify_agent.llm_agent.ChatOpenAI')
    def test_initialization(self, mock_chat_openai):
        agent = PodcastLLMAgent("test_api_key")
        mock_chat_openai.assert_called_once()
        
    @patch('spotify_agent.llm_agent.LLMChain')
    @patch('spotify_agent.llm_agent.ChatOpenAI')
    def test_evaluate_episode_relevance(self, mock_chat_openai, mock_llm_chain):
        # Mock LLM chain response
        mock_chain = Mock()
        mock_chain.run.return_value = '{"relevance_score": 0.8, "reasoning": "Test reasoning"}'
        mock_llm_chain.return_value = mock_chain
        
        agent = PodcastLLMAgent("test_api_key")
        
        episode = {
            "name": "AI Episode",
            "description": "About artificial intelligence"
        }
        preferences = [{"topics": ["AI", "technology"]}]
        
        score, reasoning = agent.evaluate_episode_relevance(episode, preferences)
        
        assert score == 0.8
        assert reasoning == "Test reasoning"
        mock_chain.run.assert_called_once()
        
    @patch('spotify_agent.llm_agent.LLMChain')
    @patch('spotify_agent.llm_agent.ChatOpenAI')  
    def test_generate_episode_summary(self, mock_chat_openai, mock_llm_chain):
        mock_chain = Mock()
        mock_chain.run.return_value = "Great episode about AI trends and future implications."
        mock_llm_chain.return_value = mock_chain
        
        agent = PodcastLLMAgent("test_api_key")
        
        episode = {
            "name": "AI Future",
            "description": "Discussion about AI trends"
        }
        
        summary = agent.generate_episode_summary(episode)
        
        assert summary == "Great episode about AI trends and future implications."
        mock_chain.run.assert_called_once()
        
    @patch('spotify_agent.llm_agent.LLMChain')
    @patch('spotify_agent.llm_agent.ChatOpenAI')
    def test_evaluate_episode_json_parsing_error(self, mock_chat_openai, mock_llm_chain):
        # Mock invalid JSON response
        mock_chain = Mock()
        mock_chain.run.return_value = "Invalid JSON response"
        mock_llm_chain.return_value = mock_chain
        
        agent = PodcastLLMAgent("test_api_key")
        
        episode = {"name": "Test", "description": "Test"}
        preferences = [{"topics": ["test"]}]
        
        score, reasoning = agent.evaluate_episode_relevance(episode, preferences)
        
        # Should return default values on JSON parsing error
        assert score == 0.75
        assert "Auto-approved due to parsing error" in reasoning