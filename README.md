# Spotify Podcast Agent (MCP-Enabled)

An advanced agentic AI system that automatically discovers, evaluates, and queues podcast episodes in Spotify based on your preferences. Now built with **Model Context Protocol (MCP)** architecture for enhanced modularity, extensibility, and maintainability.

## 🚀 What's New in v2.1

### **Enhanced Email Integration**
- **📧 Episode Summaries**: Automatic email summaries with AI-generated episode insights
- **📊 Weekly Digests**: Comprehensive weekly listening reports with statistics
- **🎯 Smart Content**: Rich HTML emails with episode details, relevance scores, and summaries
- **🔧 Unicode Safe**: Bulletproof email handling for international podcast content
- **🚨 Pending Notifications**: Email alerts when episodes are queued offline

### **Advanced Calendar Integration**
- **📅 Listening Schedule**: Schedule dedicated podcast listening times
- **🎯 Smart Time Slots**: AI-powered suggestions for optimal listening times
- **📈 Listening Analytics**: Track patterns, adherence, and listening habits
- **⏰ Episode Reminders**: Set reminders for specific episodes
- **🧠 Intelligent Scheduling**: Optimal schedule suggestions based on your queue and patterns
- **📊 Time Management**: Find available time slots and manage listening sessions

### **Production Features**
- **🔐 OAuth Authentication**: Full Spotify user authentication flow
- **⚙️ Configuration Management**: Dynamic agent settings via API
- **🕒 Automated Scheduling**: Daily/weekly runs via Heroku Scheduler
- **🎯 Background Processing**: Non-blocking agent runs
- **📊 Comprehensive Monitoring**: Detailed status and health endpoints

### **MCP Architecture**
- **Modular Design**: Separate MCP servers for Spotify, LLM, Queue, Email, and Calendar operations
- **Standardized Communication**: All components communicate via MCP protocol
- **Enhanced Extensibility**: Easy to add new integrations
- **Better Error Handling**: Graceful degradation and comprehensive logging
- **Future-Proof**: Based on emerging industry standards

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

### Email Integration Features
- 🆕 **Episode Summary Emails**: Rich HTML emails with episode details and AI summaries
- 🆕 **Weekly Digest Reports**: Comprehensive weekly listening analytics
- 🆕 **Pending Episode Notifications**: Alerts when episodes are queued offline
- 🆕 **Smart Unicode Handling**: Safe email delivery for international content
- 🆕 **Email Debug Tools**: Advanced debugging for email delivery issues
- 🆕 **Customizable Templates**: Multiple email template options

### Calendar Integration Features
- 🆕 **Listening Schedule Management**: Schedule recurring podcast listening sessions
- 🆕 **Smart Time Slot Discovery**: AI-powered available time slot finder
- 🆕 **Listening Analytics & Patterns**: Track habits, adherence rates, and preferences
- 🆕 **Episode Reminders**: Set custom reminders for specific episodes
- 🆕 **Optimal Schedule Suggestions**: AI recommendations based on queue and patterns
- 🆕 **Time Block Management**: Organize and optimize listening time
- 🆕 **Next Session Tracking**: Always know when your next listening time is

### MCP-Enhanced Features
- 🆕 **Email MCP Server**: Dedicated email operations with tools and resources
- 🆕 **Calendar MCP Server**: Advanced scheduling and listening analytics integration
- 🆕 **Modular MCP Servers**: Spotify, LLM, Queue, Email, and Calendar as separate services
- 🆕 **MCP Tool Discovery**: List and call available tools across all servers
- 🆕 **Resource Management**: Structured access to data and configurations
- 🆕 **Enhanced API**: Direct MCP server interaction endpoints

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              Enhanced MCP Spotify Podcast Agent                │
├─────────────────────────────────────────────────────────────────┤
│                        FastAPI Server                          │
│                  (mcp_api/enhanced_api.py)                     │
├─────────────────────────────────────────────────────────────────┤
│                    Enhanced MCP Agent                          │
│             (mcp_agent/enhanced_podcast_agent.py)              │
│                                                                 │
│  ┌─────────────────── MCP Client ───────────────────────────┐  │
│  │                                                          │  │
│  │  ┌───────────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌────────┐  │  │
│  │  │  Spotify  │ │  LLM  │ │ Queue │ │ Email │ │Calendar│  │  │
│  │  │MCP Server │ │Server │ │Server │ │Server │ │ Server │  │  │
│  │  │           │ │       │ │       │ │       │ │        │  │  │
│  │  │• Search   │ │• Eval │ │• Pend │ │• Send │ │• Sched │  │  │
│  │  │• Episodes │ │• Summ │ │• Get  │ │• Test │ │• Stats │  │  │
│  │  │• Queue    │ │• Score│ │• Proc │ │• Temp │ │• Sugg  │  │  │
│  │  │• Devices  │ │       │ │       │ │• Debug│ │        │  │  │
│  │  │• Auth     │ │       │ │       │ │       │ │        │  │  │
│  │  └───────────┘ └───────┘ └───────┘ └───────┘ └────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│        External Services (Spotify API, OpenAI, SMTP)           │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start (Heroku Deployment)

### Prerequisites

- Heroku account
- Spotify Premium account
- OpenAI API key
- Spotify Developer app credentials
- Gmail account (for email notifications)

### 1. Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/yourusername/spotify-podcast-agent)

Or manually:

```bash
# Clone and deploy
git clone https://github.com/yourusername/spotify-podcast-agent.git
cd spotify-podcast-agent

# Create Heroku app
heroku create your-app-name

# Set required environment variables
heroku config:set OPENAI_API_KEY=your_openai_api_key
heroku config:set SPOTIFY_CLIENT_ID=your_spotify_client_id
heroku config:set SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
heroku config:set SPOTIFY_REDIRECT_URI=https://your-app-name.herokuapp.com/callback

# Set email configuration (Gmail recommended)
heroku config:set SMTP_HOST=smtp.gmail.com
heroku config:set SMTP_PORT=587
heroku config:set SMTP_USERNAME=your_email@gmail.com
heroku config:set SMTP_PASSWORD=your_gmail_app_password
heroku config:set FROM_EMAIL=your_email@gmail.com
heroku config:set USER_EMAIL=your_email@gmail.com

# Deploy
git push heroku main
```

### 2. Configure Gmail App Password

1. Enable 2-Factor Authentication on your Gmail account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate an app password for "Mail"
4. Use this app password (not your regular password) for `SMTP_PASSWORD`

### 3. Configure Spotify Developer App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create or edit your app
3. Add redirect URI: `https://your-app-name.herokuapp.com/callback`
4. Save settings

### 4. Authenticate with Spotify

```bash
# Check authentication status
curl https://your-app-name.herokuapp.com/auth/status

# If not authenticated, get auth URL
curl https://your-app-name.herokuapp.com/auth

# Visit the returned URL to authenticate
# Then verify authentication worked
curl https://your-app-name.herokuapp.com/auth/status
```

### 5. Configure Email Settings

```bash
# Check email configuration
curl https://your-app-name.herokuapp.com/email/settings

# Send a test email
curl -X POST https://your-app-name.herokuapp.com/email/test

# Debug email issues (if needed)
curl -X POST https://your-app-name.herokuapp.com/email/debug-test
```

### 6. Configure Preferences

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

### 8. Configure Listening Schedule

```bash
# Add morning listening time
curl -X POST https://your-app-name.herokuapp.com/calendar/schedule \
  -H "Content-Type: application/json" \
  -d '{"day_of_week": "monday", "start_time": "08:00", "duration_minutes": 30, "title": "Morning Tech News"}'

# Get current schedule
curl https://your-app-name.herokuapp.com/calendar/schedule

# Get optimal schedule suggestions
curl https://your-app-name.herokuapp.com/calendar/suggestions
```

### 9. Test the Agent

```bash
# Run the agent manually with email summary
curl -X POST "https://your-app-name.herokuapp.com/run?send_email=true"

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
| `/run` | POST | Run agent with email summary option |
| `/devices` | GET | Get available Spotify devices |
| `/process-pending` | POST | Process pending episodes |

### Email Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/email/settings` | GET | Get email configuration status |
| `/email/settings` | POST | Update email settings |
| `/email/test` | POST | Send test email |
| `/email/debug-test` | POST | Debug email Unicode issues |
| `/email/weekly-digest` | POST | Send weekly digest immediately |

**Email Settings Model:**
```json
{
  "user_email": "your@email.com",
  "send_summaries": true,
  "send_weekly_digest": true
}
```

### Calendar Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/calendar/schedule` | GET | Get current podcast listening schedule |
| `/calendar/schedule` | POST | Add new listening time to schedule |
| `/calendar/suggestions` | GET | Get optimal schedule suggestions |
| `/calendar/stats` | GET | Get listening statistics and patterns |
| `/calendar/time-slots` | GET | Find available time slots |
| `/calendar/reminders` | POST | Set episode reminders |

**Listening Schedule Model:**
```json
{
  "day_of_week": "monday",
  "start_time": "08:00",
  "duration_minutes": 30,
  "title": "Morning Podcast Time",
  "recurring": true
}
```

**Schedule Response:**
```json
{
  "schedule": [...],
  "total_weekly_minutes": 150,
  "formatted_total": "2h 30m",
  "next_session": {
    "session": {...},
    "datetime": "2025-06-05T08:00:00",
    "relative_time": "in 2 hours"
  }
}
```

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
  "use_vector_memory": false,    // Enable vector storage (advanced)
  "user_email": "your@email.com" // Email for notifications
}
```

### MCP Protocol Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mcp/servers` | GET | List all MCP servers and capabilities |
| `/mcp/call` | POST | Call a tool on a specific MCP server |

### Scheduling Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scheduler/start` | POST | Start automated scheduling |
| `/scheduler/stop` | POST | Stop automated scheduling |
| `/scheduler/status` | GET | Get scheduler status |

## 📧 Email Features

### Episode Summary Emails

The agent automatically sends rich HTML email summaries containing:

- **Episode Details**: Title, show name, duration, and relevance score
- **AI-Generated Summaries**: Intelligent summaries of each episode's content
- **Clean Formatting**: Professional HTML layout with episode cards
- **Unicode Safe**: Handles international characters and emojis properly

### Weekly Digest Reports

Comprehensive weekly reports include:

- **Listening Statistics**: Total episodes, listening time, average relevance scores
- **Episode List**: All episodes discovered during the week
- **Listening Patterns**: Insights into your podcast consumption habits

### Smart Email Handling

- **Unicode Cleaning**: Removes problematic characters while preserving content
- **UTF-8 Encoding**: Modern email compatibility with international content
- **Error Recovery**: Automatic fallback mechanisms for delivery issues
- **Debug Tools**: Advanced debugging for troubleshooting email problems

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

The scheduler job includes:
- Daily episode discovery with email summaries
- Weekly digest generation (Sundays)
- Pending episode processing
- Error notifications via email

### Option 2: Built-in 