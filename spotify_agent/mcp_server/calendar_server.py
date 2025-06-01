"""
MCP Server for Calendar operations
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, time
import json
import os
import logging

from .protocol import MCPServer, MCPMessage, MCPResource, MCPTool, MCPMessageType

logger = logging.getLogger(__name__)

class CalendarMCPServer(MCPServer):
    """MCP Server for calendar operations and listening schedule management"""
    
    def __init__(self, calendar_file: str = None):
        super().__init__("calendar", "1.0.0")
        
        # Calendar storage (simple JSON file for now, can integrate with Google Calendar later)
        self.calendar_file = calendar_file or os.path.join(
            os.path.expanduser("~"), ".spotify_podcast_agent", "calendar.json"
        )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.calendar_file), exist_ok=True)
        
        self._register_tools()
        self._register_resources()
        
        # Load existing calendar data
        self.calendar_data = self._load_calendar_data()
    
    def _register_tools(self):
        """Register available calendar tools"""
        self.tools.update({
            "schedule_listening_time": MCPTool(
                name="schedule_listening_time",
                description="Schedule dedicated podcast listening time",
                input_schema={
                    "type": "object",
                    "properties": {
                        "day_of_week": {"type": "string", "description": "Day of week (monday, tuesday, etc.)"},
                        "start_time": {"type": "string", "description": "Start time (HH:MM format)"},
                        "duration_minutes": {"type": "integer", "description": "Duration in minutes"},
                        "title": {"type": "string", "description": "Event title", "default": "Podcast Listening Time"},
                        "recurring": {"type": "boolean", "description": "Is this a recurring event", "default": True}
                    },
                    "required": ["day_of_week", "start_time", "duration_minutes"]
                }
            ),
            "get_listening_schedule": MCPTool(
                name="get_listening_schedule",
                description="Get current podcast listening schedule",
                input_schema={"type": "object", "properties": {}}
            ),
            "get_available_time_slots": MCPTool(
                name="get_available_time_slots",
                description="Find available time slots for podcast listening",
                input_schema={
                    "type": "object",
                    "properties": {
                        "min_duration": {"type": "integer", "description": "Minimum duration in minutes", "default": 30},
                        "preferred_days": {"type": "array", "description": "Preferred days of week", "default": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
                        "time_range": {"type": "object", "description": "Preferred time range"}
                    }
                }
            ),
            "schedule_episode_reminder": MCPTool(
                name="schedule_episode_reminder",
                description="Schedule a reminder for specific episodes",
                input_schema={
                    "type": "object",
                    "properties": {
                        "episodes": {"type": "array", "description": "Episodes to set reminders for"},
                        "reminder_time": {"type": "string", "description": "When to remind (ISO format or relative like '+1 hour')"},
                        "reminder_type": {"type": "string", "description": "Type of reminder", "default": "listening"}
                    },
                    "required": ["episodes", "reminder_time"]
                }
            ),
            "get_listening_stats": MCPTool(
                name="get_listening_stats",
                description="Get listening statistics and patterns",
                input_schema={
                    "type": "object",
                    "properties": {
                        "period": {"type": "string", "description": "Time period (week, month, all)", "default": "week"}
                    }
                }
            ),
            "suggest_optimal_schedule": MCPTool(
                name="suggest_optimal_schedule",
                description="Suggest optimal podcast schedule based on patterns",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_preferences": {"type": "object", "description": "User preferences and constraints"},
                        "episode_queue": {"type": "array", "description": "Current episode queue"}
                    }
                }
            )
        })
    
    def _register_resources(self):
        """Register available calendar resources"""
        self.resources.update({
            "listening_schedule": MCPResource(
                uri="calendar://listening_schedule",
                name="Listening Schedule",
                description="Current podcast listening schedule",
                mime_type="application/json"
            ),
            "time_blocks": MCPResource(
                uri="calendar://time_blocks",
                name="Time Blocks",
                description="Scheduled time blocks for podcast listening",
                mime_type="application/json"
            ),
            "listening_patterns": MCPResource(
                uri="calendar://patterns",
                name="Listening Patterns",
                description="Historical listening patterns and analytics",
                mime_type="application/json"
            )
        })
    
    async def handle_request(self, message: MCPMessage) -> MCPMessage:
        """Handle incoming MCP requests"""
        try:
            if message.method == "tools/list":
                return MCPMessage(
                    type=MCPMessageType.RESPONSE,
                    result={"tools": [tool.dict() for tool in self.tools.values()]}
                )
            elif message.method == "tools/call":
                tool_name = message.params.get("name")
                arguments = message.params.get("arguments", {})
                result = await self._execute_tool(tool_name, arguments)
                return MCPMessage(
                    type=MCPMessageType.RESPONSE,
                    result=result
                )
            elif message.method == "resources/list":
                resources = await self.list_resources()
                return MCPMessage(
                    type=MCPMessageType.RESPONSE,
                    result={"resources": [resource.dict() for resource in resources]}
                )
            elif message.method == "resources/read":
                uri = message.params.get("uri")
                content = await self._read_resource(uri)
                return MCPMessage(
                    type=MCPMessageType.RESPONSE,
                    result={"contents": content}
                )
            else:
                return MCPMessage(
                    type=MCPMessageType.ERROR,
                    error={"code": -32601, "message": f"Method not found: {message.method}"}
                )
        except Exception as e:
            logger.error(f"Error handling calendar MCP request: {str(e)}")
            return MCPMessage(
                type=MCPMessageType.ERROR,
                error={"code": -32603, "message": f"Internal error: {str(e)}"}
            )
    
    async def list_resources(self) -> List[MCPResource]:
        """List available calendar resources"""
        return list(self.resources.values())
    
    async def list_tools(self) -> List[MCPTool]:
        """List available calendar tools"""
        return list(self.tools.values())
    
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a specific calendar tool"""
        if name == "schedule_listening_time":
            return await self._schedule_listening_time(
                arguments["day_of_week"],
                arguments["start_time"],
                arguments["duration_minutes"],
                arguments.get("title", "Podcast Listening Time"),
                arguments.get("recurring", True)
            )
        
        elif name == "get_listening_schedule":
            return await self._get_listening_schedule()
        
        elif name == "get_available_time_slots":
            return await self._get_available_time_slots(
                arguments.get("min_duration", 30),
                arguments.get("preferred_days", ["monday", "tuesday", "wednesday", "thursday", "friday"]),
                arguments.get("time_range", {})
            )
        
        elif name == "schedule_episode_reminder":
            return await self._schedule_episode_reminder(
                arguments["episodes"],
                arguments["reminder_time"],
                arguments.get("reminder_type", "listening")
            )
        
        elif name == "get_listening_stats":
            return await self._get_listening_stats(
                arguments.get("period", "week")
            )
        
        elif name == "suggest_optimal_schedule":
            return await self._suggest_optimal_schedule(
                arguments.get("user_preferences", {}),
                arguments.get("episode_queue", [])
            )
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    def _load_calendar_data(self) -> Dict[str, Any]:
        """Load calendar data from file"""
        try:
            if os.path.exists(self.calendar_file):
                with open(self.calendar_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading calendar data: {str(e)}")
        
        return {
            "listening_schedule": [],
            "reminders": [],
            "time_blocks": [],
            "listening_history": [],
            "preferences": {
                "preferred_times": ["morning", "commute", "evening"],
                "max_session_duration": 120,
                "min_session_duration": 15
            }
        }
    
    def _save_calendar_data(self) -> None:
        """Save calendar data to file"""
        try:
            with open(self.calendar_file, 'w') as f:
                json.dump(self.calendar_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving calendar data: {str(e)}")
    
    async def _schedule_listening_time(self, day_of_week: str, start_time: str, 
                                     duration_minutes: int, title: str, recurring: bool) -> Dict[str, Any]:
        """Schedule dedicated podcast listening time"""
        try:
            # Validate day of week
            valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            if day_of_week.lower() not in valid_days:
                return {"success": False, "message": "Invalid day of week"}
            
            # Validate time format
            try:
                time_obj = datetime.strptime(start_time, "%H:%M").time()
            except ValueError:
                return {"success": False, "message": "Invalid time format. Use HH:MM"}
            
            # Create schedule entry
            schedule_entry = {
                "id": f"{day_of_week}_{start_time}_{datetime.now().timestamp()}",
                "day_of_week": day_of_week.lower(),
                "start_time": start_time,
                "duration_minutes": duration_minutes,
                "title": title,
                "recurring": recurring,
                "created_at": datetime.now().isoformat(),
                "active": True
            }
            
            # Add to calendar data
            self.calendar_data["listening_schedule"].append(schedule_entry)
            self._save_calendar_data()
            
            return {
                "success": True,
                "message": f"Listening time scheduled for {day_of_week} at {start_time}",
                "schedule_entry": schedule_entry
            }
            
        except Exception as e:
            logger.error(f"Error scheduling listening time: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def _get_listening_schedule(self) -> Dict[str, Any]:
        """Get current podcast listening schedule"""
        try:
            active_schedule = [
                entry for entry in self.calendar_data["listening_schedule"]
                if entry.get("active", True)
            ]
            
            # Sort by day of week and time
            day_order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            active_schedule.sort(key=lambda x: (day_order.index(x["day_of_week"]), x["start_time"]))
            
            # Calculate total weekly listening time
            total_weekly_minutes = sum(entry["duration_minutes"] for entry in active_schedule if entry.get("recurring"))
            
            return {
                "schedule": active_schedule,
                "total_weekly_minutes": total_weekly_minutes,
                "formatted_total": self._format_duration_minutes(total_weekly_minutes),
                "next_session": self._get_next_listening_session(active_schedule)
            }
            
        except Exception as e:
            logger.error(f"Error getting listening schedule: {str(e)}")
            return {"schedule": [], "error": str(e)}
    
    async def _get_available_time_slots(self, min_duration: int, preferred_days: List[str], 
                                      time_range: Dict[str, Any]) -> Dict[str, Any]:
        """Find available time slots for podcast listening"""
        try:
            existing_schedule = self.calendar_data["listening_schedule"]
            
            # Default time preferences if not specified
            default_start = time_range.get("start", "07:00")
            default_end = time_range.get("end", "22:00")
            
            available_slots = []
            
            for day in preferred_days:
                day_schedule = [
                    entry for entry in existing_schedule 
                    if entry["day_of_week"] == day.lower() and entry.get("active", True)
                ]
                
                # Find gaps in the schedule
                day_slots = self._find_time_gaps(day_schedule, default_start, default_end, min_duration)
                
                for slot in day_slots:
                    available_slots.append({
                        "day": day,
                        "start_time": slot["start"],
                        "end_time": slot["end"],
                        "duration_minutes": slot["duration"],
                        "quality_score": self._calculate_time_quality(day, slot["start"])
                    })
            
            # Sort by quality score (best times first)
            available_slots.sort(key=lambda x: x["quality_score"], reverse=True)
            
            return {
                "available_slots": available_slots[:10],  # Top 10 suggestions
                "total_found": len(available_slots),
                "criteria": {
                    "min_duration": min_duration,
                    "preferred_days": preferred_days,
                    "time_range": f"{default_start} - {default_end}"
                }
            }
            
        except Exception as e:
            logger.error(f"Error finding available time slots: {str(e)}")
            return {"available_slots": [], "error": str(e)}
    
    async def _schedule_episode_reminder(self, episodes: List[Dict], reminder_time: str, 
                                       reminder_type: str) -> Dict[str, Any]:
        """Schedule a reminder for specific episodes"""
        try:
            reminders = []
            
            for episode in episodes:
                reminder = {
                    "id": f"reminder_{episode.get('episode', {}).get('id', 'unknown')}_{datetime.now().timestamp()}",
                    "episode_id": episode.get('episode', {}).get('id'),
                    "episode_name": episode.get('episode', {}).get('name', 'Unknown Episode'),
                    "reminder_time": reminder_time,
                    "reminder_type": reminder_type,
                    "created_at": datetime.now().isoformat(),
                    "completed": False
                }
                reminders.append(reminder)
            
            # Add to calendar data
            self.calendar_data["reminders"].extend(reminders)
            self._save_calendar_data()
            
            return {
                "success": True,
                "message": f"Scheduled {len(reminders)} episode reminders",
                "reminders": reminders
            }
            
        except Exception as e:
            logger.error(f"Error scheduling episode reminders: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def _get_listening_stats(self, period: str) -> Dict[str, Any]:
        """Get listening statistics and patterns"""
        try:
            history = self.calendar_data.get("listening_history", [])
            schedule = self.calendar_data.get("listening_schedule", [])
            
            # Calculate stats based on period
            if period == "week":
                cutoff_date = datetime.now() - timedelta(days=7)
            elif period == "month":
                cutoff_date = datetime.now() - timedelta(days=30)
            else:
                cutoff_date = datetime.min
            
            # Filter history by period
            period_history = [
                entry for entry in history
                if datetime.fromisoformat(entry.get("date", "1970-01-01")) >= cutoff_date
            ]
            
            # Calculate statistics
            total_sessions = len(period_history)
            total_minutes = sum(entry.get("duration_minutes", 0) for entry in period_history)
            scheduled_minutes = sum(
                entry["duration_minutes"] for entry in schedule 
                if entry.get("active", True) and entry.get("recurring", True)
            )
            
            # Find patterns
            day_patterns = {}
            time_patterns = {}
            
            for entry in period_history:
                day = entry.get("day_of_week", "unknown")
                hour = entry.get("start_time", "00:00").split(":")[0]
                
                day_patterns[day] = day_patterns.get(day, 0) + 1
                time_patterns[hour] = time_patterns.get(hour, 0) + 1
            
            return {
                "period": period,
                "total_sessions": total_sessions,
                "total_minutes": total_minutes,
                "formatted_total": self._format_duration_minutes(total_minutes),
                "scheduled_weekly_minutes": scheduled_minutes,
                "average_session_minutes": total_minutes / max(total_sessions, 1),
                "favorite_day": max(day_patterns, key=day_patterns.get) if day_patterns else None,
                "favorite_time": f"{max(time_patterns, key=time_patterns.get)}:00" if time_patterns else None,
                "day_patterns": day_patterns,
                "time_patterns": time_patterns,
                "adherence_rate": self._calculate_adherence_rate(schedule, period_history)
            }
            
        except Exception as e:
            logger.error(f"Error getting listening stats: {str(e)}")
            return {"error": str(e)}
    
    async def _suggest_optimal_schedule(self, user_preferences: Dict[str, Any], 
                                      episode_queue: List[Dict]) -> Dict[str, Any]:
        """Suggest optimal podcast schedule based on patterns"""
        try:
            # Analyze current patterns
            stats = await self._get_listening_stats("month")
            
            # Calculate total queue time
            total_queue_minutes = sum(
                ep.get('episode', {}).get('duration_ms', 0) / 60000
                for ep in episode_queue
            )
            
            # Get user constraints
            max_session = user_preferences.get("max_session_duration", 90)
            min_session = user_preferences.get("min_session_duration", 20)
            preferred_times = user_preferences.get("preferred_times", ["morning", "commute", "evening"])
            available_days = user_preferences.get("available_days", ["monday", "tuesday", "wednesday", "thursday", "friday"])
            
            suggestions = []
            
            # Suggest based on favorite patterns
            favorite_day = stats.get("favorite_day")
            favorite_time = stats.get("favorite_time", "08:00")
            
            if favorite_day and favorite_day in available_days:
                suggestions.append({
                    "type": "pattern_based",
                    "day": favorite_day,
                    "start_time": favorite_time,
                    "duration_minutes": min(max_session, max(min_session, total_queue_minutes / 3)),
                    "reason": f"Based on your listening pattern - you often listen on {favorite_day}s at {favorite_time}"
                })
            
            # Suggest optimal distribution
            sessions_needed = max(1, int(total_queue_minutes / max_session))
            session_duration = min(max_session, total_queue_minutes / sessions_needed)
            
            optimal_times = {
                "morning": "08:00",
                "commute": "17:30", 
                "evening": "19:00"
            }
            
            for i, time_slot in enumerate(preferred_times[:sessions_needed]):
                if i < len(available_days):
                    suggestions.append({
                        "type": "optimal_distribution",
                        "day": available_days[i],
                        "start_time": optimal_times.get(time_slot, "12:00"),
                        "duration_minutes": int(session_duration),
                        "reason": f"Optimal {time_slot} session to distribute your {self._format_duration_minutes(total_queue_minutes)} queue"
                    })
            
            # Suggest quick sessions for short episodes
            short_episodes = [
                ep for ep in episode_queue 
                if ep.get('episode', {}).get('duration_ms', 0) / 60000 < 30
            ]
            
            if short_episodes:
                suggestions.append({
                    "type": "quick_session",
                    "day": "daily",
                    "start_time": "12:00",
                    "duration_minutes": 20,
                    "reason": f"Quick lunch break sessions for {len(short_episodes)} short episodes"
                })
            
            return {
                "suggestions": suggestions,
                "queue_analysis": {
                    "total_episodes": len(episode_queue),
                    "total_minutes": int(total_queue_minutes),
                    "formatted_total": self._format_duration_minutes(total_queue_minutes),
                    "estimated_sessions": sessions_needed,
                    "avg_session_duration": int(session_duration)
                },
                "current_patterns": {
                    "favorite_day": favorite_day,
                    "favorite_time": favorite_time,
                    "weekly_average": stats.get("total_minutes", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error suggesting optimal schedule: {str(e)}")
            return {"suggestions": [], "error": str(e)}
    
    def _find_time_gaps(self, day_schedule: List[Dict], start_time: str, 
                       end_time: str, min_duration: int) -> List[Dict[str, Any]]:
        """Find available time gaps in a day's schedule"""
        gaps = []
        
        # Convert times to minutes for easier calculation
        start_minutes = self._time_to_minutes(start_time)
        end_minutes = self._time_to_minutes(end_time)
        
        # Sort existing events by start time
        events = []
        for event in day_schedule:
            event_start = self._time_to_minutes(event["start_time"])
            event_end = event_start + event["duration_minutes"]
            events.append((event_start, event_end))
        
        events.sort()
        
        # Find gaps
        current_time = start_minutes
        
        for event_start, event_end in events:
            if event_start > current_time:
                gap_duration = event_start - current_time
                if gap_duration >= min_duration:
                    gaps.append({
                        "start": self._minutes_to_time(current_time),
                        "end": self._minutes_to_time(event_start),
                        "duration": gap_duration
                    })
            current_time = max(current_time, event_end)
        
        # Check for gap at end of day
        if end_minutes > current_time:
            gap_duration = end_minutes - current_time
            if gap_duration >= min_duration:
                gaps.append({
                    "start": self._minutes_to_time(current_time),
                    "end": self._minutes_to_time(end_minutes),
                    "duration": gap_duration
                })
        
        return gaps
    
    def _calculate_time_quality(self, day: str, start_time: str) -> float:
        """Calculate quality score for a time slot (higher is better)"""
        score = 0.5  # Base score
        
        # Prefer weekdays
        if day.lower() in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            score += 0.2
        
        # Prefer certain times
        hour = int(start_time.split(":")[0])
        
        if 7 <= hour <= 9:  # Morning
            score += 0.3
        elif 12 <= hour <= 14:  # Lunch
            score += 0.2
        elif 17 <= hour <= 19:  # Evening commute
            score += 0.3
        elif 19 <= hour <= 21:  # Evening
            score += 0.2
        
        return min(1.0, score)
    
    def _get_next_listening_session(self, schedule: List[Dict]) -> Optional[Dict[str, Any]]:
        """Get the next scheduled listening session"""
        if not schedule:
            return None
        
        now = datetime.now()
        current_weekday = now.weekday()  # 0 = Monday
        current_time = now.time()
        
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        # Look for next session in current week
        for days_ahead in range(7):
            check_day = (current_weekday + days_ahead) % 7
            check_day_name = day_names[check_day]
            
            day_sessions = [
                session for session in schedule
                if session["day_of_week"] == check_day_name and session.get("active", True)
            ]
            
            for session in sorted(day_sessions, key=lambda x: x["start_time"]):
                session_time = datetime.strptime(session["start_time"], "%H:%M").time()
                
                # If it's today, check if session is in the future
                if days_ahead == 0 and session_time <= current_time:
                    continue
                
                # Calculate the actual datetime
                session_date = now.date() + timedelta(days=days_ahead)
                session_datetime = datetime.combine(session_date, session_time)
                
                return {
                    "session": session,
                    "datetime": session_datetime.isoformat(),
                    "relative_time": self._get_relative_time(session_datetime)
                }
        
        return None
    
    def _calculate_adherence_rate(self, schedule: List[Dict], history: List[Dict]) -> float:
        """Calculate how well user adheres to their schedule"""
        if not schedule:
            return 0.0
        
        scheduled_sessions = len([s for s in schedule if s.get("active", True) and s.get("recurring", True)])
        actual_sessions = len(history)
        
        if scheduled_sessions == 0:
            return 1.0 if actual_sessions == 0 else 0.0
        
        return min(1.0, actual_sessions / (scheduled_sessions * 4))  # Assume 4 weeks
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM to minutes since midnight"""
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    
    def _minutes_to_time(self, minutes: int) -> str:
        """Convert minutes since midnight to HH:MM"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def _format_duration_minutes(self, minutes: int) -> str:
        """Format duration in minutes to human readable string"""
        if minutes < 60:
            return f"{minutes}m"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours}h"
            else:
                return f"{hours}h {remaining_minutes}m"
    
    def _get_relative_time(self, target_datetime: datetime) -> str:
        """Get relative time description"""
        now = datetime.now()
        diff = target_datetime - now
        
        if diff.days > 0:
            return f"in {diff.days} day{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"in {hours} hour{'s' if hours > 1 else ''}"
        else:
            minutes = diff.seconds // 60
            return f"in {minutes} minute{'s' if minutes > 1 else ''}"
    
    async def _read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific calendar resource"""
        if uri == "calendar://listening_schedule":
            return await self._get_listening_schedule()
        elif uri == "calendar://time_blocks":
            return {
                "time_blocks": self.calendar_data.get("time_blocks", []),
                "description": "Scheduled time blocks for podcast listening"
            }
        elif uri == "calendar://patterns":
            return await self._get_listening_stats("all")
        else:
            raise ValueError(f"Unknown resource URI: {uri}")