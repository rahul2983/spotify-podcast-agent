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

### Email-Enhanced Setup

```bash
# Configure email notifications
curl -X POST https://your-app-name.herokuapp.com/email/settings \
  -H "Content-Type: application/json" \
  -d '{"user_email": "your@email.com", "send_summaries": true, "send_weekly_digest": true}'

# Set agent to send email summaries
curl -X PUT https://your-app-name.herokuapp.com/config \
  -H "Content-Type: application/json" \
  -d '{"relevance_threshold": 0.7, "max_episodes_per_run": 5, "user_email": "your@email.com"}'
```

### Calendar-Enhanced Setup

```bash
# Set up listening schedule
curl -X POST https://your-app-name.herokuapp.com/calendar/schedule \
  -H "Content-Type: application/json" \
  -d '{"day_of_week": "monday", "start_time": "08:00", "duration_minutes": 30, "title": "Morning Podcast Time"}'

curl -X POST https://your-app-name.herokuapp.com/calendar/schedule \
  -H "Content-Type: application/json" \
  -d '{"day_of_week": "friday", "start_time": "17:30", "duration_minutes": 45, "title": "Commute Listening"}'

# Get schedule optimization suggestions
curl https://your-app-name.herokuapp.com/calendar/suggestions
```

### Aggressive Discovery with Email

```bash
# Get more episodes with email summaries
curl -X PUT https://your-app-name.herokuapp.com/config \
  -H "Content-Type: application/json" \
  -d '{"relevance_threshold": 0.5, "max_episodes_per_run": 10, "user_email": "your@email.com"}'
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
# Comprehensive status (includes email and calendar status)
curl https://your-app-name.herokuapp.com/status

# Email-specific status
curl https://your-app-name.herokuapp.com/email/settings

# Calendar-specific status
curl https://your-app-name.herokuapp.com/calendar/schedule

# Authentication status
curl https://your-app-name.herokuapp.com/auth/status

# Current configuration
curl https://your-app-name.herokuapp.com/config
```

### Email Debugging

```bash
# Test basic email functionality
curl -X POST https://your-app-name.herokuapp.com/email/test

# Advanced Unicode debugging
curl -X POST https://your-app-name.herokuapp.com/email/debug-test

# Send manual weekly digest
curl -X POST https://your-app-name.herokuapp.com/email/weekly-digest
```

### Calendar Debugging & Management

```bash
# Get current listening schedule
curl https://your-app-name.herokuapp.com/calendar/schedule

# Get listening statistics
curl https://your-app-name.herokuapp.com/calendar/stats?period=week

# Find available time slots
curl https://your-app-name.herokuapp.com/calendar/time-slots

# Get schedule optimization suggestions
curl https://your-app-name.herokuapp.com/calendar/suggestions

# Set episode reminders
curl -X POST https://your-app-name.herokuapp.com/calendar/reminders \
  -H "Content-Type: application/json" \
  -d '{"episodes": [...], "reminder_time": "+1 hour", "reminder_type": "listening"}'
```

### Logs

```bash
# Real-time logs
heroku logs --tail

# Filter for email activity
heroku logs --tail | grep -i "email\|smtp\|unicode"

# Filter for agent activity
heroku logs --tail | grep -i "episode\|found\|added\|relevance"

# Search recent logs
heroku logs --num 100 | grep "Background agent"
```

### MCP Server Testing

```bash
# Test Calendar MCP server
curl -X POST https://your-app-name.herokuapp.com/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"server_name": "calendar", "tool_name": "schedule_listening_time", "arguments": {"day_of_week": "tuesday", "start_time": "09:00", "duration_minutes": 25, "title": "Quick Morning Catch-up"}}'

# Test Email MCP server
curl -X POST https://your-app-name.herokuapp.com/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"server_name": "email", "tool_name": "send_notification", "arguments": {"to_email": "your@email.com", "subject": "Test", "message": "Testing MCP email server"}}'

# Test Spotify integration
curl -X POST https://your-app-name.herokuapp.com/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"server_name": "spotify", "tool_name": "search_podcasts", "arguments": {"query": "technology", "limit": 3}}'
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
- Check environment variables
- Re-authenticate: `/auth`

**Email delivery issues:**
- Test email configuration: `/email/test`
- Check SMTP credentials in Heroku config
- Use email debug tool: `/email/debug-test`
- Verify Gmail app password (not regular password)

**Empty email content:**
- Usually indicates Unicode cleaning issues
- Run debug test: `/email/debug-test`
- Check logs for "Unicode" or "ASCII" errors
- Verify episode data doesn't contain problematic characters

**No listening time scheduled:**
- Set up listening schedule: `/calendar/schedule`
- Get time slot suggestions: `/calendar/suggestions`
- Find available time slots: `/calendar/time-slots`

**Poor schedule optimization:**
- Add more listening history data
- Update user preferences in suggestions
- Check listening statistics: `/calendar/stats`

**Timeouts:**
- Agent runs in background automatically
- Check logs for completion: `heroku logs --tail`
- Use `/status` to check progress

### Error Codes

- **H10 (App crashed)**: Check logs for startup errors
- **H12 (Request timeout)**: Normal for `/run` - uses background processing
- **500 errors**: Check environment variables and authentication
- **Email errors**: Check SMTP configuration and credentials

## 🔐 Security Notes

- **Environment Variables**: Never commit API keys to git
- **Gmail App Passwords**: Use app-specific passwords, not regular passwords
- **OAuth Tokens**: Cached securely on Heroku filesystem
- **Rate Limiting**: Built-in Spotify API rate limit handling
- **CORS**: Configured for web access (adjust for production)

## 📈 Performance Tips

- **Email Frequency**: Daily summaries work well for most users
- **Calendar Optimization**: Set 2-3 regular listening times for best habit formation
- **Relevance Threshold**: Start with 0.7, adjust based on results
- **Episode Limits**: 3-5 episodes per run for daily use
- **Scheduling**: Daily runs with weekly digests provide good coverage
- **Preferences**: 2-5 preferences provide good variety without overwhelming
- **Listening Sessions**: 20-45 minute sessions work well for most people
- **Time Slot Quality**: Morning and commute times typically have highest adherence rates

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

# Create .env file with email configuration
cp .env.example .env
# Edit .env with your API keys and email settings:
# OPENAI_API_KEY=your_key
# SPOTIFY_CLIENT_ID=your_id
# SPOTIFY_CLIENT_SECRET=your_secret
# SMTP_USERNAME=your_email@gmail.com
# SMTP_PASSWORD=your_app_password
# USER_EMAIL=your_email@gmail.com

# Run locally
python main.py --mode api
```

## 📚 Advanced Features

### Custom Email Templates

Create custom email templates by extending the EmailMCPServer:

```python
def _generate_custom_template(self, episodes, template_name):
    if template_name == "minimal":
        # Generate minimal template
        pass
    elif template_name == "detailed":
        # Generate detailed template with more analysis
        pass
```

### Email Analytics

Track email engagement and optimize content:

```python
# Add to EmailMCPServer
async def track_email_engagement(self, email_id, action):
    # Track opens, clicks, etc.
    pass
```

### Calendar Integration

Schedule listening time and track habits:

```python
# Schedule automatic listening sessions
await agent.schedule_listening_time("Monday", "08:00", 30, "Morning Tech News")

# Get listening analytics
stats = await agent.get_listening_schedule()

# Find optimal time slots
available_slots = await agent.get_available_time_slots(min_duration=20)

# Get schedule suggestions based on your queue
suggestions = await agent.suggest_optimal_schedule(user_preferences, episode_queue)
```

### Advanced Analytics

Track and optimize your listening habits:

```python
# Get detailed listening statistics
weekly_stats = await calendar_server.get_listening_stats("week")
monthly_patterns = await calendar_server.get_listening_stats("month")

# Schedule episode-specific reminders
await calendar_server.schedule_episode_reminder(episodes, "+2 hours", "listening")

# Calculate time quality scores for different slots
quality_score = calendar_server._calculate_time_quality("monday", "08:00")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following MCP patterns
4. Add tests for new functionality
5. Update documentation
6. Submit pull request

### Email Development Guidelines

- Always test Unicode handling with international content
- Use the debug tools for troubleshooting email issues
- Follow UTF-8 encoding practices
- Include error handling for SMTP failures
- Test with different email providers

### Calendar Development Guidelines

- Always validate time formats and day names
- Use relative time descriptions for better UX
- Track listening patterns for better suggestions
- Implement smart time slot quality scoring
- Provide clear adherence rate calculations
- Support both one-time and recurring events

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **GitHub Issues**: For bugs and feature requests
- **Documentation**: Complete API reference in `/docs`
- **Heroku Logs**: Use `heroku logs --tail` for debugging
- **Email Issues**: Use `/email/debug-test` endpoint for troubleshooting

## 🎯 Roadmap

- [x] Advanced email integration with Unicode handling
- [x] Weekly digest reports with analytics
- [x] Email debugging and testing tools
- [x] Advanced calendar integration with scheduling
- [x] Listening analytics and pattern tracking
- [x] Smart time slot discovery and optimization
- [ ] Google Calendar integration
- [ ] Advanced AI filtering with custom models
- [ ] Multi-user support
- [ ] Mobile app integration
- [ ] Podcast analytics and insights
- [ ] Email template customization
- [ ] Push notification support
- [ ] Calendar sync with external providers

---

**Built with ❤️ using MCP, FastAPI, OpenAI, Spotify APIs, and SMTP integration**

## 🎉 New in This Release

The email and calendar integration makes this podcast agent truly production-ready:

- **📧 Set it and forget it**: Configure once, get daily email summaries automatically
- **📅 Smart scheduling**: AI-powered listening time optimization based on your patterns  
- **🎯 Never miss great content**: Offline queueing with email notifications
- **📊 Rich insights**: AI-generated summaries help you choose what to listen to
- **📈 Track your habits**: Comprehensive listening analytics and adherence tracking
- **🌍 International support**: Unicode-safe email handling for global podcast content
- **🔧 Debug-friendly**: Advanced troubleshooting tools for email delivery issues
- **⏰ Time optimization**: Find perfect listening slots and manage your schedule

Perfect for busy professionals who want personalized podcast discovery with intelligent email summaries and optimized listening schedules!