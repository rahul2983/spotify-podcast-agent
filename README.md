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
- **NEW**: Offline queuing system for handling no-device scenarios

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

### Scheduled Operation with Queue Manager

The agent now includes a queue management system that allows it to run on a schedule even when no Spotify device is active:

1. When the agent runs on schedule and no device is available, it stores recommended episodes to a local queue
2. The next time you open Spotify and a device becomes active, you can process the pending episodes:
   ```bash
   curl -X POST http://127.0.0.1:8000/process-pending
   ```
3. Alternatively, start a scheduled task that periodically checks for an active device and processes the queue when available

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

### Working with Spotify Devices

```bash
# Get available Spotify devices
curl -X GET http://127.0.0.1:8000/devices

# Start playback on a device (needed for adding to queue)
curl -X POST http://127.0.0.1:8000/start-playback

# Process pending episodes (when a device is available)
curl -X POST http://127.0.0.1:8000/process-pending
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
│   ├── queue_manager.py  # Queue management for offline mode
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

1. The agent will now store episodes in a pending queue when no device is available
2. When you open Spotify, you can process pending episodes with `curl -X POST http://127.0.0.1:8000/process-pending`
3. You can also start playback directly: `curl -X POST http://127.0.0.1:8000/start-playback`

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

## Scheduling Options for Fully Automated Operation

### 1. System Scheduler with Multiple Steps

Set up your system scheduler (cron, Task Scheduler, etc.) to:

1. Start Spotify (script or app)
2. Wait a few seconds for Spotify to initialize
3. Run a script that calls the agent's API

Example cron job script:
```bash
#!/bin/bash
# Start Spotify app (MacOS example)
open -a Spotify

# Wait for Spotify to start
sleep 10

# Start playback
curl -X POST http://127.0.0.1:8000/start-playback

# Wait for playback to be active
sleep 5

# Process any pending episodes first
curl -X POST http://127.0.0.1:8000/process-pending

# Then run the agent for new episodes
curl -X POST http://127.0.0.1:8000/run
```

### 2. Service Integration

For users with smart home systems or automation tools:

1. Set up a morning routine with your smart assistant (e.g., "Alexa, start my morning podcast")
2. Have this routine start Spotify and trigger the podcast agent
3. The agent will add new episodes to your queue

### 3. Periodic Queue Processing

The simplest approach:

1. Let the agent run on its own schedule (building up a queue of episodes)
2. Whenever you open Spotify to listen to podcasts, manually process the queue:
   ```bash
   curl -X POST http://127.0.0.1:8000/process-pending
   ```
3. Or create a browser extension or menu bar app to do this with a single click

## Advanced Features and Extensions

### 1. Episode Summarization (Already Implemented)
- The agent automatically generates summaries of episodes

### 2. Queue Management System (New)
- The agent stores episodes when no Spotify device is available
- Episodes are queued for later processing
- You can process the queue when a device becomes available

### 3. Device Management and Playback Control
- The agent can now start playback on Spotify devices
- It can check for available devices and their status
- This enables more automated workflows

### 4. Custom Scheduling
- Set up a system-level scheduler to work with the agent
- Create multi-step routines that handle all aspects of podcast management
- Integrate with smart home systems or automation tools

### 5. Future Extensions
- **Transcript Analysis**: Download and analyze episode transcripts
- **Calendar Integration**: Connect to Google Calendar for scheduling episodes
- **Listening History**: Track listened episodes to improve recommendations
- **Mobile App**: Create a companion mobile app for easier control

## License

This project is licensed under the MIT License - see the LICENSE file for details.