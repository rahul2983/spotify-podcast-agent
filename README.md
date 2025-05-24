# Spotify Podcast Agent (MCP-Enabled)

An advanced agentic AI system that automatically discovers, evaluates, and queues podcast episodes in Spotify based on your preferences. Now built with **Model Context Protocol (MCP)** architecture for enhanced modularity, extensibility, and maintainability.

## 🚀 What's New in v2.0

### **MCP Architecture**
- **Modular Design**: Separate MCP servers for Spotify, LLM, and Queue operations
- **Standardized Communication**: All components communicate via MCP protocol
- **Enhanced Extensibility**: Easy to add new integrations (calendar, email, etc.)
- **Better Error Handling**: Graceful degradation and comprehensive logging
- **Future-Proof**: Based on emerging industry standards

### **New Features**
- **MCP Server Introspection**: Discover available tools and resources
- **Direct MCP Tool Calling**: Call individual server functions via API
- **Enhanced Status Reporting**: Comprehensive system health monitoring
- **Async-First Design**: Fully asynchronous architecture for better performance
- **Improved Debugging**: MCP protocol provides structured logging and debugging

## Features

### Core Functionality
- ✅ Automatically checks for new episodes from your favorite podcast shows
- ✅ Discovers podcasts based on topics of interest
- ✅ Uses AI to evaluate episode relevance based on your preferences
- ✅ Adds selected episodes to your Spotify queue
- ✅ Runs on a schedule (daily or weekly)
- ✅ Provides AI-generated episode summaries
- ✅ RESTful API for integration with other tools
- ✅ Offline queuing system for handling no-device scenarios

### MCP-Enhanced Features
- 🆕 **Modular MCP Servers**: Spotify, LLM, and Queue operations as separate services
- 🆕 **MCP Tool Discovery**: List and call available tools across all servers
- 🆕 **Resource Management**: Structured access to Spotify data and queue information
- 🆕 **Enhanced API**: Direct MCP server interaction endpoints
- 🆕 **Better Monitoring**: Comprehensive status reporting across all components
- 🆕 **Debugging Support**: MCP protocol debugging and introspection

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Spotify Podcast Agent                    │
├─────────────────────────────────────────────────────────────────┤
│                        FastAPI Server                          │
│                     (mcp_api/api.py)                           │
├─────────────────────────────────────────────────────────────────┤
│                       MCP Agent                                │
│                 (mcp_agent/podcast_agent.py)                   │
│                                                                 │
│  ┌─────────────────── MCP Client ───────────────────────────┐  │
│  │                                                          │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │  │
│  │  │   Spotify    │ │     LLM      │ │      Queue       │  │  │
│  │  │ MCP Server   │ │ MCP Server   │ │   MCP Server     │  │  │
│  │  │              │ │              │ │                  │  │  │
│  │  │ • Search     │ │ • Evaluate   │ │ • Add Pending    │  │  │
│  │  │ • Episodes   │ │ • Summarize  │ │ • Get Pending    │  │  │
│  │  │ • Queue      │ │ • Reason     │ │ • Remove Proc.   │  │  │
│  │  │ • Devices    │ │              │ │                  │  │  │
│  │  └──────────────┘ └──────────────┘ └──────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│            External Services (Spotify API, OpenAI)             │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Documentation

### Architecture
- **[Interactive Architecture Diagram](./docs/architecture.html)** - Comprehensive MCP architecture visualization
- **[Documentation Hub](./docs/)** - Complete technical documentation

### Quick Links
- [API Usage](#api-usage) - REST API examples
- [Production Deployment](#deployment) - Deployment guides
- [MCP Protocol](#mcp-specific-endpoints) - Model Context Protocol usage

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

All required packages will be installed, including:
- **Core**: langchain, openai, spotipy, pydantic, python-dotenv, fastapi, uvicorn
- **MCP**: asyncio-mqtt, websockets, jsonrpc-base, typing-extensions

### Step 3: Set Up Spotify Developer App

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Log in with your Spotify account
3. Click "Create an App"
4. Fill in the app name and description
5. Add `http://127.0.0.1:8000/callback` as a Redirect URI
6. Save your Client ID and Client Secret

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/callback
```

## Running the Agent

### API Mode (Recommended)

Start the MCP-enabled web API:

```bash
# Standard mode
python main.py --mode api

# With MCP debugging enabled
python main.py --mode api --mcp-debug
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
2. After logging in, authorize the app with the requested permissions
3. The app will capture the authorization code and proceed
4. Subsequent runs will use cached credentials

## API Usage

### Core Podcast Management

```bash
# Test server connectivity
curl http://127.0.0.1:8000/

# Get current preferences (empty initially)
curl http://127.0.0.1:8000/preferences

# Add specific podcast show with duration constraints
curl -X POST http://127.0.0.1:8000/preferences -H "Content-Type: application/json" -d '{"show_name": "The Tim Ferriss Show", "min_duration_minutes": 30, "max_duration_minutes": 120}'

# Add preference by topics with minimum duration
curl -X POST http://127.0.0.1:8000/preferences -H "Content-Type: application/json" -d '{"topics": ["artificial intelligence", "technology", "startup"], "min_duration_minutes": 15}'

# Add preference for specific show ID (more reliable than name)
curl -X POST http://127.0.0.1:8000/preferences -H "Content-Type: application/json" -d '{"show_id": "4rOoJ6Egrf8K2IrywzwOMk", "min_duration_minutes": 10}'

# Add tech news preference with short duration
curl -X POST http://127.0.0.1:8000/preferences -H "Content-Type: application/json" -d '{"show_name": "Daily Tech Headlines", "min_duration_minutes": 5, "max_duration_minutes": 30}'

# Add business/entrepreneurship topics
curl -X POST http://127.0.0.1:8000/preferences -H "Content-Type: application/json" -d '{"topics": ["business", "entrepreneurship", "investing"], "min_duration_minutes": 20, "max_duration_minutes": 60}'

# View all configured preferences
curl http://127.0.0.1:8000/preferences

# Run the agent to discover and queue episodes
curl -X POST http://127.0.0.1:8000/run

# Get comprehensive system status
curl http://127.0.0.1:8000/status
```

### MCP-Specific Endpoints

#### Discover MCP Servers and Capabilities

```bash
# List all MCP servers and their tools/resources
curl http://127.0.0.1:8000/mcp/servers
```

Example response:
```json
{
  "servers": [
    {
      "name": "spotify",
      "tools": [
        {
          "name": "search_podcasts",
          "description": "Search for podcasts by query",
          "input_schema": {...}
        },
        {
          "name": "get_show_episodes",
          "description": "Get episodes for a specific show",
          "input_schema": {...}
        }
      ],
      "resources": [
        {
          "uri": "spotify://user/profile",
          "name": "User Profile",
          "description": "Current user's Spotify profile"
        }
      ]
    }
  ]
}
```

#### Call MCP Tools Directly

```bash
# Search for podcasts via Spotify MCP server
curl -X POST http://127.0.0.1:8000/mcp/call -H "Content-Type: application/json" -d '{"server_name": "spotify", "tool_name": "search_podcasts", "arguments": {"query": "artificial intelligence", "limit": 3}}'

# Get episodes for a specific show
curl -X POST http://127.0.0.1:8000/mcp/call -H "Content-Type: application/json" -d '{"server_name": "spotify", "tool_name": "get_show_episodes", "arguments": {"show_id": "4rOoJ6Egrf8K2IrywzwOMk", "limit": 5}}'

# Get available Spotify devices
curl -X POST http://127.0.0.1:8000/mcp/call -H "Content-Type: application/json" -d '{"server_name": "spotify", "tool_name": "get_devices", "arguments": {}}'

# Add episode to queue via MCP
curl -X POST http://127.0.0.1:8000/mcp/call -H "Content-Type: application/json" -d '{"server_name": "spotify", "tool_name": "add_to_queue", "arguments": {"episode_uri": "spotify:episode:4TnieuwqFfVL0YlKKzPacJ"}}'

# Evaluate episode via LLM MCP server (example with mock data)
curl -X POST http://127.0.0.1:8000/mcp/call -H "Content-Type: application/json" -d '{"server_name": "llm", "tool_name": "evaluate_episode", "arguments": {"episode": {"name": "AI Future", "description": "Discussion about AI"}, "preferences": [{"topics": ["artificial intelligence"]}]}}'

# Generate episode summary via LLM MCP server
curl -X POST http://127.0.0.1:8000/mcp/call -H "Content-Type: application/json" -d '{"server_name": "llm", "tool_name": "generate_summary", "arguments": {"episode": {"name": "Tech Trends 2025", "description": "Latest technology trends"}}}'

# Get pending episodes via Queue MCP server
curl -X POST http://127.0.0.1:8000/mcp/call -H "Content-Type: application/json" -d '{"server_name": "queue", "tool_name": "get_pending", "arguments": {}}'

# Add episodes to pending queue
curl -X POST http://127.0.0.1:8000/mcp/call -H "Content-Type: application/json" -d '{"server_name": "queue", "tool_name": "add_pending", "arguments": {"episodes": [{"episode": {"id": "123", "name": "Test Episode"}}]}}'
```

#### Access MCP Resources

```bash
# Get user profile from Spotify MCP server
curl "http://127.0.0.1:8000/mcp/resources/spotify?uri=spotify://user/profile"

# Get available Spotify devices
curl "http://127.0.0.1:8000/mcp/resources/spotify?uri=spotify://devices"

# Get recently played tracks and episodes
curl "http://127.0.0.1:8000/mcp/resources/spotify?uri=spotify://user/recently_played"

# Get pending episodes queue
curl "http://127.0.0.1:8000/mcp/resources/queue?uri=queue://pending"
```

### Queue Management

```bash
# Process pending episodes (when device becomes available)
curl -X POST http://127.0.0.1:8000/process-pending

# Get available Spotify devices
curl http://127.0.0.1:8000/devices

# Start playback on default device
curl -X POST http://127.0.0.1:8000/start-playback

# Reset processed episodes list
curl -X POST http://127.0.0.1:8000/reset-episodes
```

## Project Structure

```
spotify-podcast-agent/
├── spotify_agent/
│   ├── __init__.py
│   ├── config.py                    # Configuration models
│   ├── spotify_client.py            # Spotify API client
│   ├── llm_agent.py                 # LLM-based evaluation
│   ├── queue_manager.py             # Queue management
│   │
│   ├── mcp_server/                  # MCP Protocol Implementation
│   │   ├── __init__.py
│   │   ├── protocol.py              # Core MCP protocol classes
│   │   ├── spotify_server.py        # Spotify MCP server
│   │   ├── llm_server.py            # LLM MCP server
│   │   └── queue_server.py          # Queue MCP server
│   │
│   ├── mcp_agent/                   # MCP-based Agent
│   │   ├── __init__.py
│   │   └── podcast_agent.py         # Main MCP agent orchestration
│   │
│   ├── mcp_api/                     # MCP-enabled API
│   │   ├── __init__.py
│   │   └── api.py                   # FastAPI with MCP endpoints
│   │
│   └── agent.py                     # Legacy agent (backward compatibility)
│
├── main.py                          # Entry point with MCP support
├── requirements.txt                 # Dependencies (including MCP)
├── setup.py                         # Package setup
├── .env                             # Environment variables
└── README.md                        # This file
```

## Advanced Usage

### MCP Server Development

You can extend the system by creating new MCP servers:

```python
from spotify_agent.mcp_server.protocol import MCPServer, MCPTool

class CalendarMCPServer(MCPServer):
    def __init__(self, calendar_client):
        super().__init__("calendar", "1.0.0")
        self.calendar = calendar_client
        self._register_tools()
    
    def _register_tools(self):
        self.tools.update({
            "schedule_listening_time": MCPTool(
                name="schedule_listening_time",
                description="Schedule podcast listening time",
                input_schema={
                    "type": "object",
                    "properties": {
                        "datetime": {"type": "string"},
                        "duration_minutes": {"type": "integer"}
                    }
                }
            )
        })
    
    async def _execute_tool(self, name: str, arguments: dict):
        if name == "schedule_listening_time":
            # Implementation here
            pass
```

### Custom MCP Tool Chains

Create complex workflows by chaining MCP tools:

```python
async def discover_and_schedule_podcasts(agent):
    # 1. Search for podcasts
    podcasts = await agent.mcp_client.send_request(
        "spotify", "tools/call",
        {"name": "search_podcasts", "arguments": {"query": "tech news"}}
    )
    
    # 2. Evaluate episodes
    for podcast in podcasts:
        evaluation = await agent.mcp_client.send_request(
            "llm", "tools/call",
            {"name": "evaluate_episode", "arguments": {"episode": podcast}}
        )
        
        # 3. Schedule if relevant
        if evaluation["relevance_score"] > 0.8:
            await agent.mcp_client.send_request(
                "calendar", "tools/call",
                {"name": "schedule_listening_time", "arguments": {...}}
            )
```

## Troubleshooting

### MCP-Specific Issues

#### MCP Server Communication Errors
```bash
# Check MCP server status
curl http://127.0.0.1:8000/mcp/servers

# Enable MCP debugging
python main.py --mode api --mcp-debug
```

#### Tool Discovery Issues
```bash
# List available tools for a specific server
curl http://127.0.0.1:8000/mcp/servers | jq '.servers[] | select(.name=="spotify") | .tools'
```

### Legacy Issues

#### Spotify Authentication
If you encounter authentication issues:
1. Ensure your Spotify Developer app has the correct redirect URI
2. Check credentials in `.env` file
3. Delete `.cache` files to force re-authentication

#### No Active Device Error
The system handles this gracefully with pending queues:
```bash
# Check device status
curl http://127.0.0.1:8000/devices

# Process pending episodes when device is available
curl -X POST http://127.0.0.1:8000/process-pending
```

#### Module Import Errors
If you see MCP-related import errors:
1. Ensure you've installed all requirements: `pip install -r requirements.txt`
2. Check Python version is 3.9+
3. Verify virtual environment is activated

## Development and Testing

### Running Tests

```bash
# Run basic functionality tests
python -m pytest tests/

# Test MCP server communication
python -m pytest tests/test_mcp_servers.py

# Test with MCP debugging
python -m pytest tests/ --mcp-debug
```

### MCP Server Testing

```bash
# Test individual MCP servers
curl -X POST http://127.0.0.1:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"server_name": "spotify", "tool_name": "get_devices", "arguments": {}}'
```

## Migration from v1.x

The MCP-based architecture is backward compatible. Existing API endpoints continue to work:

### Automatic Migration
- All existing API endpoints remain functional
- Configuration files (.env) work without changes
- Existing preferences and queues are preserved

### Gradual Adoption
- Start using new MCP endpoints alongside existing ones
- Migrate custom integrations to use MCP servers over time
- Take advantage of enhanced debugging and monitoring

## Performance Considerations

### MCP Benefits
- **Async Architecture**: Better concurrency and resource utilization
- **Modular Loading**: Only load required MCP servers
- **Error Isolation**: Server failures don't crash the entire system
- **Resource Management**: Better memory and connection management

### Optimization Tips
- Use MCP resource caching for frequently accessed data
- Implement MCP server connection pooling for high-load scenarios
- Monitor MCP server performance via the status endpoints

## Contributing

We welcome contributions! The MCP architecture makes it easier to contribute:

### Adding New MCP Servers
1. Create a new server in `mcp_server/`
2. Implement the required MCP protocol methods
3. Register tools and resources
4. Add tests and documentation

### Extending Existing Servers
1. Add new tools to existing MCP servers
2. Update input schemas and documentation
3. Ensure backward compatibility

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### v2.0.0 (MCP Release)
- 🆕 **MCP Architecture**: Complete refactor using Model Context Protocol
- 🆕 **Modular Design**: Separate MCP servers for different concerns
- 🆕 **Enhanced API**: New MCP-specific endpoints
- 🆕 **Better Debugging**: MCP protocol debugging support
- 🆕 **Async-First**: Fully asynchronous architecture
- ✅ **Backward Compatibility**: All v1.x features preserved

### v1.0.0 (Original Release)
- ✅ Basic podcast discovery and queueing
- ✅ LLM-based episode evaluation
- ✅ Spotify integration
- ✅ RESTful API
- ✅ Offline queue management