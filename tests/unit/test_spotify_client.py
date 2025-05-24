import pytest
from unittest.mock import Mock, patch
from spotify_agent.spotify_client import SpotifyClient

@pytest.mark.unit
class TestSpotifyClient:
    @patch('spotify_agent.spotify_client.spotipy.Spotify')
    def test_initialization(self, mock_spotify):
        client = SpotifyClient("client_id", "client_secret", "redirect_uri")
        assert client.scope is not None
        mock_spotify.assert_called_once()
        
    @patch('spotify_agent.spotify_client.spotipy.Spotify')
    def test_search_podcast(self, mock_spotify):
        mock_sp = Mock()
        mock_sp.search.return_value = {
            'shows': {
                'items': [{'id': 'show1', 'name': 'Test Show'}]
            }
        }
        mock_spotify.return_value = mock_sp
        
        client = SpotifyClient("client_id", "client_secret", "redirect_uri")
        results = client.search_podcast("test query")
        
        assert len(results) == 1
        assert results[0]['name'] == 'Test Show'
        mock_sp.search.assert_called_once_with(q="test query", type='show', limit=5)
        
    @patch('spotify_agent.spotify_client.spotipy.Spotify')
    def test_get_show_episodes(self, mock_spotify):
        mock_sp = Mock()
        mock_sp.show_episodes.return_value = {
            'items': [{'id': 'episode1', 'name': 'Test Episode'}]
        }
        mock_spotify.return_value = mock_sp
        
        client = SpotifyClient("client_id", "client_secret", "redirect_uri")
        episodes = client.get_show_episodes("show1")
        
        assert len(episodes) == 1
        assert episodes[0]['name'] == 'Test Episode'
        mock_sp.show_episodes.assert_called_once_with("show1", limit=10)
        
    @patch('spotify_agent.spotify_client.spotipy.Spotify')
    def test_add_to_queue_success(self, mock_spotify):
        mock_sp = Mock()
        mock_sp.add_to_queue.return_value = None  # Success
        mock_spotify.return_value = mock_sp
        
        client = SpotifyClient("client_id", "client_secret", "redirect_uri")
        result = client.add_to_queue("spotify:episode:123")
        
        assert result is True
        mock_sp.add_to_queue.assert_called_once_with(uri="spotify:episode:123")
        
    @patch('spotify_agent.spotify_client.spotipy.Spotify')
    def test_add_to_queue_failure(self, mock_spotify):
        mock_sp = Mock()
        mock_sp.add_to_queue.side_effect = Exception("API Error")
        mock_spotify.return_value = mock_sp
        
        client = SpotifyClient("client_id", "client_secret", "redirect_uri")
        result = client.add_to_queue("spotify:episode:123")
        
        assert result is False