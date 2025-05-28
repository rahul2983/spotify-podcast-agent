# Spotify Podcast Agent (MCP-Enabled)

An advanced agentic AI system that automatically discovers, evaluates, and queues podcast episodes in Spotify based on your preferences. Now built with **Model Context Protocol (MCP)** architecture for enhanced modularity, extensibility, and maintainability.

## 🚀 What's New in v2.0

### **MCP Architecture**
- **Modular Design**: Separate MCP servers for Spotify, LLM, and Queue operations
- **Standardized Communication**: All components communicate via MCP protocol
- **Enhanced Extensibility**: Easy to add new integrations (calendar, email, etc.)
- **Better Error Handling**: Graceful degradation and comprehensive logging
- **Future-Proof**: Based on emerging industry standards

### **Production Features**
- **🔐 OAuth Authentication**: Full Spotify user authentication flow
- **⚙️ Configuration Management**: Dynamic agent settings via API
- **🕒 Automated Scheduling**: Daily/weekly runs via Heroku Scheduler
- **🎯 Background Processing**: Non-blocking agent runs
- **📊 Comprehensive Monitoring**: Detailed status and health endpoints

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

### Production-Ready Features
- 🆕 **OAuth Authentication**: Secure Spotify user authorization
- 🆕 **Configuration API**: Dynamic settings management
- 🆕 **Automated Scheduling**: Set-and-forget daily/weekly runs
- 🆕 **Background Processing**: Handles long-running tasks without timeouts
- 🆕 **Pending Queue**: Handles offline scenarios gracefully
- 🆕 **Health Monitoring**: Comprehensive status and debugging endpoints

## 🏗️ Architecture Overview

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
│  │  │ • Auth       │ │              │ │                  │  │  │
│  │  └──────────────┘ └──────────────┘ └──────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│            External Services (Spotify API, OpenAI)             │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start (Heroku Deployment)

### Prerequisites

- Heroku account
- Spotify Premium account
- OpenAI API key
- Spotify Developer app credentials

### 1. Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/yourusername/spotify-podcast-agent)

Or manually:

```bash
# Clone and deploy
git clone https://github.com/yourusername/spotify-podcast-agent.git
cd spotify-podcast-agent

# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set OPENAI_API_KEY=your_openai_api_key
heroku config:set SPOTIFY_CLIENT_ID=your_spotify_client_id
heroku config:set SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
heroku config:set SPOTIFY_REDIRECT_URI=https://your-app-name.herokuapp.com/callback

# Deploy
git push heroku main
```

### 2. Configure Spotify Developer App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create or edit your app
3. Add redirect URI: `https://your-app-name.herokuapp.com/callback`
4. Save settings

### 3. Authenticate with Spotify

```bash
# Check authentication status
curl https://your-app-name.herokuapp.com/auth/status

# If not authenticated, get auth URL
curl https://your-app-name.herokuapp.com/auth

# Visit the returned URL to authenticate
# Then verify authentication worked
curl https://your-app-name.herokuapp.com/auth/status
```

### 4. Configure Preferences

```bash
# Add a specific podcast
curl -X POST https://your-app-name.herokuapp.com/preferences \
  -H "Content-Type: application/json" \
  -d '{"show_name": "The Tim Ferriss Show", "min_duration_minutes": 30}'

# Add topic-based preferences
curl -X POST https://your-app-name.herokuapp.com/preferences \
  -H "Content-Type: application/json" \
  -d '{"topics": ["technology", "artificial intelligence"], "min_duration_minutes": 15}'
```

### 5. Test the Agent

```bash
# Run the agent manually
curl -X POST https://your-app-name.herokuapp.com/run

# Check status
curl https://your-app-name.herokuapp.com/status

# Process any pending episodes
curl -X POST https://your-app-name.herokuapp.com/process-pending
```

## 📋 API Documentation

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth` | GET | Get Spotify authorization URL |
| `/auth/status` | GET | Check authentication status |
| `/callback` | GET | OAuth callback (automatic) |

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and health check |
| `/status` | GET | Comprehensive agent status |
| `/preferences` | GET | Get all podcast preferences |
| `/preferences` | POST | Add new podcast preference |
| `/run` | POST | Run agent (background processing) |
| `/devices` | GET | Get available Spotify devices |
| `/process-pending` | POST | Process pending episodes |

### Configuration Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/config` | GET | Get current agent configuration |
| `/config` | PUT | Update agent configuration |

**Configuration Options:**
```json
{
  "relevance_threshold": 0.7,    // 0.0-1.0, how relevant episodes must be
  "max_episodes_per_run": 5,     // Maximum episodes to process per run
  "check_frequency": "daily",    // "daily" or "weekly"
  "use_vector_memory": false     // Enable vector storage (advanced)
}
```

### MCP Protocol Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mcp/servers` | GET | List all MCP servers and capabilities |
| `/mcp/call` | POST | Call a tool on a specific MCP server |
| `/mcp/resources/{server}` | GET | Read resources from MCP server |

### Scheduling Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scheduler/start` | POST | Start automated scheduling |
| `/scheduler/stop` | POST | Stop automated scheduling |
| `/scheduler/status` | GET | Get scheduler status |

## 🕒 Automated Scheduling Setup

### Option 1: Heroku Scheduler (Recommended)

```bash
# Add Heroku Scheduler add-on
heroku addons:create scheduler:standard

# Open scheduler dashboard
heroku addons:open scheduler

# Add job in dashboard:
# Command: python scheduler_job.py
# Frequency: Daily at 8:00 AM
```

### Option 2: Built-in Scheduler API

```bash
# Start automated scheduling
curl -X POST https://your-app-name.herokuapp.com/scheduler/start

# Check scheduler status
curl https://your-app-name.herokuapp.com/scheduler/status

# Stop scheduler
curl -X POST https://your-app-name.herokuapp.com/scheduler/stop
```

## 🔧 Configuration Examples

### Basic Setup

```bash
# Set conservative settings
curl -X PUT https://your-app-name.herokuapp.com/config \
  -H "Content-Type: application/json" \
  -d '{"relevance_threshold": 0.7, "max_episodes_per_run": 3}'
```

### Aggressive Discovery

```bash
# Get more episodes with lower threshold
curl -X PUT https://your-app-name.herokuapp.com/config \
  -H "Content-Type: application/json" \
  -d '{"relevance_threshold": 0.5, "max_episodes_per_run": 10}'
```

### Add Diverse Preferences

```bash
# Tech news (short episodes)
curl -X POST https://your-app-name.herokuapp.com/preferences \
  -H "Content-Type: application/json" \
  -d '{"topics": ["technology", "startup"], "min_duration_minutes": 10, "max_duration_minutes": 30}'

# Business interviews (longer episodes)  
curl -X POST https://your-app-name.herokuapp.com/preferences \
  -H "Content-Type: application/json" \
  -d '{"topics": ["business", "entrepreneurship"], "min_duration_minutes": 45, "max_duration_minutes": 120}'

# Specific high-quality shows
curl -X POST https://your-app-name.herokuapp.com/preferences \
  -H "Content-Type: application/json" \
  -d '{"show_name": "Lex Fridman Podcast", "min_duration_minutes": 60}'
```

## 🔍 Monitoring and Debugging

### Health Checks

```bash
# Comprehensive status
curl https://your-app-name.herokuapp.com/status

# Authentication status
curl https://your-app-name.herokuapp.com/auth/status

# Current configuration
curl https://your-app-name.herokuapp.com/config

# Environment variables (debug)
curl https://your-app-name.herokuapp.com/debug/env
```

### Logs

```bash
# Real-time logs
heroku logs --tail

# Filter for agent activity
heroku logs --tail | grep -i "episode\|found\|added\|relevance"

# Search recent logs
heroku logs --num 100 | grep "Background agent"
```

### MCP Server Testing

```bash
# Test Spotify integration
curl -X POST https://your-app-name.herokuapp.com/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"server_name": "spotify", "tool_name": "search_podcasts", "arguments": {"query": "technology", "limit": 3}}'

# Test LLM evaluation
curl -X POST https://your-app-name.herokuapp.com/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"server_name": "llm", "tool_name": "evaluate_episode", "arguments": {"episode": {"name": "AI Episode", "description": "About AI"}, "preferences": [{"topics": ["AI"]}]}}'
```

## 🚨 Troubleshooting

### Common Issues

**No episodes found:**
- Check if preferences are configured: `/preferences`
- Lower relevance threshold: `/config` 
- Verify Spotify authentication: `/auth/status`

**Episodes not in queue:**
- Check for pending episodes: `/status`
- Process pending: `/process-pending`
- Ensure Spotify is active (play something briefly)

**Authentication errors:**
- Verify redirect URI in Spotify Developer Dashboard
- Check environment variables: `/debug/env`
- Re-authenticate: `/auth`

**Timeouts:**
- Agent runs in background automatically
- Check logs for completion: `heroku logs --tail`
- Use `/status` to check progress

### Error Codes

- **H10 (App crashed)**: Check logs for startup errors
- **H12 (Request timeout)**: Normal for `/run` - uses background processing
- **500 errors**: Check environment variables and authentication

## 🔐 Security Notes

- **Environment Variables**: Never commit API keys to git
- **OAuth Tokens**: Cached securely on Heroku filesystem
- **Rate Limiting**: Built-in Spotify API rate limit handling
- **CORS**: Configured for web access (adjust for production)

## 📈 Performance Tips

- **Relevance Threshold**: Start with 0.7, adjust based on results
- **Episode Limits**: 3-5 episodes per run for daily use
- **Scheduling**: Daily runs work well for active listeners
- **Preferences**: 2-5 preferences provide good variety

## 🔧 Development Setup (Local)

```bash
# Clone repository
git clone https://github.com/yourusername/spotify-podcast-agent.git
cd spotify-podcast-agent

# Create virtual environment
python -m venv podcast-agent-env
source podcast-agent-env/bin/activate  # Windows: podcast-agent-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys

# Run locally
python main.py --mode api
```

## 📚 Advanced Features

### Custom MCP Servers

Create custom servers for extended functionality:

```python
from spotify_agent.mcp_server.protocol import MCPServer

class CalendarMCPServer(MCPServer):
    def __init__(self):
        super().__init__("calendar", "1.0.0")
        # Implementation...
```

### Webhook Integration

Set up webhooks for external triggers:

```python
@app.post("/webhook/spotify")
def spotify_webhook(data: dict):
    # Trigger agent on specific Spotify events
    pass
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following MCP patterns
4. Add tests for new functionality
5. Update documentation
6. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **GitHub Issues**: For bugs and feature requests
- **Documentation**: Complete API reference in `/docs`
- **Heroku Logs**: Use `heroku logs --tail` for debugging

## 🎯 Roadmap

- [ ] Calendar integration for scheduled listening
- [ ] Email notifications for new episodes
- [ ] Advanced AI filtering with custom models
- [ ] Multi-user support
- [ ] Mobile app integration
- [ ] Podcast analytics and insights

---

**Built with ❤️ using MCP, FastAPI, OpenAI, and Spotify APIs**