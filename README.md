# Spotify Podcast Agent

An agentic AI system that automatically discovers, evaluates, and queues podcast episodes in Spotify based on your preferences.

## Features

- Automatically checks for new episodes from your favorite podcast shows
- Discovers podcasts based on topics of interest
- Uses AI to evaluate episode relevance based on your preferences
- Adds selected episodes to your Spotify queue
- Runs on a schedule (daily or weekly)
- Provides summarizations of episodes
- RESTful API for integration with other tools

## Setup Instructions

### Prerequisites

- Python 3.9+ installed
- Spotify Premium account
- OpenAI API key
- Spotify Developer app credentials

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/spotify-podcast-agent.git
cd spotify-podcast-agent
```

### Step 2: Install Dependencies

```bash
# Create and activate a virtual environment
python -m venv podcast-agent-env
source podcast-agent-env/bin/activate  # On Windows: podcast-agent-env\Scripts\activate

# Install the required packages
pip install -r requirements.txt
```

All required packages should be installed, including:
- langchain and langchain-community
- openai
- spotipy
- pydantic
- python-dotenv
- fastapi
- uvicorn
- schedule

### Step 3: Set Up Spotify Developer App

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Log in with your Spotify account
3. Click "Create an App"
4. Fill in the app name and description
5. Add `http://127.0.0.1:8000/callback` as a Redirect URI
6. Save your Client ID and Client Secret

### Step 4: Configure Environment Variables

Create a `.env` file in the project root with the following contents:

```
OPENAI_API_KEY=your_openai_api_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/callback
```

Replace the placeholder values with your actual API keys and credentials.

## Running the Agent

### Important: Active Spotify Device Required

**Before running the agent, make sure to:**
1. Open the Spotify app on your computer, phone, or web browser
2. Start playing any song or podcast
3. Keep Spotify running while the agent is working

This is required for the agent to be able to add episodes to your queue. Without an active Spotify device, the API calls will fail.

### API Mode (Recommended)

This starts a web API that you can interact with:

```bash
python main.py --mode api
```

The API will be available at `http://127.0.0.1:8000`

### CLI Mode

For quick tests or one-off runs:

```bash
python main.py --mode cli
```

### First Run Authentication

The first time you run the application:

1. A browser window will open asking you to log in to Spotify
2. After logging in, Spotify will ask you to authorize the app with the requested permissions
3. Once you approve, Spotify will redirect to the callback URL
4. The application will automatically capture the authorization code and proceed
5. Subsequent runs will use the cached credentials

## API Usage

### Add Podcast Preferences

```bash
# Add a specific podcast show
curl -X POST http://127.0.0.1:8000/preferences \
  -H "Content-Type: application/json" \
  -d '{"show_name": "The Tim Ferriss Show"}'

# Add by topics
curl -X POST http://127.0.0.1:8000/preferences \
  -H "Content-Type: application/json" \
  -d '{"topics": ["artificial intelligence", "technology", "startup"]}'

# Add with duration constraints
curl -X POST http://127.0.0.1:8000/preferences \
  -H "Content-Type: application/json" \
  -d '{"show_name": "The Daily", "min_duration_minutes": 10, "max_duration_minutes": 30}'
```

### Run the Agent Manually

```bash
curl -X POST http://127.0.0.1:8000/run
```

### Get Current Preferences

```bash
curl http://127.0.0.1:8000/preferences
```

### Update Configuration

```bash
# Change relevance threshold and max episodes per run
curl -X PUT http://127.0.0.1:8000/config \
  -H "Content-Type: application/json" \
  -d '{"relevance_threshold": 0.5, "max_episodes_per_run": 5}'
```

### Reset Processed Episodes

If you want the agent to reconsider episodes it has processed before:

```bash
curl -X POST http://127.0.0.1:8000/reset-episodes
```

## Project Structure

```
spotify-podcast-agent/
├── spotify_agent/
│   ├── __init__.py
│   ├── config.py         # Configuration models
│   ├── spotify_client.py # Spotify API client
│   ├── llm_agent.py      # LLM-based evaluation
│   ├── agent.py          # Main agent orchestration
│   └── api.py            # FastAPI web API
├── main.py               # Entry point script
├── requirements.txt      # Dependencies
├── setup.py              # Package setup file
├── .env                  # Environment variables (create this)
└── README.md             # This file
```

## Troubleshooting

### Spotify Authentication

If you encounter authentication issues:

1. Ensure your Spotify Developer app has the correct redirect URI
2. Check that your credentials in the `.env` file are correct
3. The first time you run the agent, you'll need to authorize via a browser window

### No Active Device Error

If you see "No active device found" errors:

1. Make sure Spotify is open and playing something
2. This creates an active device that the agent can target
3. Run the agent again after Spotify is playing

### Error Processing Episodes

If you see errors like "episode not a dictionary" or missing 'id' key:

1. This might be due to inconsistent data from the Spotify API
2. The agent has built-in protection against these errors now
3. Check the logs (`podcast_agent.log`) for specific details about which podcasts are causing issues

### Module Not Found Errors

If you encounter "module not found" errors:

1. Make sure you've activated your virtual environment
2. Install all dependencies: `pip install -r requirements.txt`
3. Check that you're running the script from the project root directory

## Advanced Features and Extensions

Here are some ways to extend the agent's functionality:

### 1. Episode Summarization (Already Implemented)
- The agent automatically generates summaries of episodes

### 2. Transcript Analysis
- Add functionality to download and analyze episode transcripts
- Extract key topics and themes for better relevance evaluation

### 3. Calendar Integration
- Connect to Google Calendar or other calendar services
- Queue shorter podcasts for commute times
- Schedule longer episodes for dedicated listening time

### 4. Smarter Recommendations
- Implement feedback mechanisms to learn from your listening habits
- Track which queued episodes you actually listen to vs. skip

## License

This project is licensed under the MIT License - see the LICENSE file for details.