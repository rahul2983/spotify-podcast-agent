"""
MCP Server for Email operations - FIXED VERSION
"""
from typing import Dict, Any, List
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
import re
import unicodedata

from .protocol import MCPServer, MCPMessage, MCPResource, MCPTool, MCPMessageType

logger = logging.getLogger(__name__)

class EmailMCPServer(MCPServer):
    """MCP Server for email operations"""
    
    def __init__(self, smtp_host: str = None, smtp_port: int = 587, 
                 smtp_username: str = None, smtp_password: str = None):
        super().__init__("email", "1.0.0")
        
        # Email configuration from environment or parameters
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.getenv("SMTP_USERNAME")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self):
        """Register available email tools"""
        self.tools.update({
            "send_summary_email": MCPTool(
                name="send_summary_email",
                description="Send episode summary email to user",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to_email": {"type": "string", "description": "Recipient email"},
                        "episodes": {"type": "array", "description": "Episodes to summarize"},
                        "subject": {"type": "string", "description": "Email subject", "default": "Your Daily Podcast Summary"},
                        "template": {"type": "string", "description": "Email template", "default": "default"}
                    },
                    "required": ["to_email", "episodes"]
                }
            ),
            "send_notification": MCPTool(
                name="send_notification",
                description="Send a simple notification email",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to_email": {"type": "string", "description": "Recipient email"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "message": {"type": "string", "description": "Email message"}
                    },
                    "required": ["to_email", "subject", "message"]
                }
            ),
            "send_weekly_digest": MCPTool(
                name="send_weekly_digest",
                description="Send weekly podcast digest",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to_email": {"type": "string", "description": "Recipient email"},
                        "episodes": {"type": "array", "description": "Week's episodes"},
                        "stats": {"type": "object", "description": "Weekly stats"}
                    },
                    "required": ["to_email", "episodes"]
                }
            )
        })
    
    def _register_resources(self):
        """Register available email resources"""
        self.resources.update({
            "email_templates": MCPResource(
                uri="email://templates",
                name="Email Templates",
                description="Available email templates",
                mime_type="application/json"
            ),
            "email_history": MCPResource(
                uri="email://history",
                name="Email History",
                description="Recent email sending history",
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
            logger.error(f"Error handling email MCP request: {str(e)}")
            return MCPMessage(
                type=MCPMessageType.ERROR,
                error={"code": -32603, "message": f"Internal error: {str(e)}"}
            )
    
    async def list_resources(self) -> List[MCPResource]:
        """List available email resources"""
        return list(self.resources.values())
    
    async def list_tools(self) -> List[MCPTool]:
        """List available email tools"""
        return list(self.tools.values())
    
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a specific email tool"""
        if name == "send_summary_email":
            return await self._send_summary_email(
                arguments["to_email"],
                arguments["episodes"],
                arguments.get("subject", "Your Daily Podcast Summary"),
                arguments.get("template", "default")
            )
        
        elif name == "send_notification":
            return await self._send_notification(
                arguments["to_email"],
                arguments["subject"],
                arguments["message"]
            )
        
        elif name == "send_weekly_digest":
            return await self._send_weekly_digest(
                arguments["to_email"],
                arguments["episodes"],
                arguments.get("stats", {})
            )
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    def _clean_text(self, text: str) -> str:
        """Clean text to remove ALL problematic characters - aggressive approach"""
        if not text:
            return ""
        
        # Convert to string if not already
        text = str(text)
        
        # Debug: Log what we're cleaning
        logger.debug(f"Original text (first 100 chars): {repr(text[:100])}")
        
        # Step 1: Replace ALL Unicode whitespace with regular space
        # This is more comprehensive than just replacing \xa0
        text = re.sub(r'\s+', ' ', text)  # Replace any whitespace sequence with single space
        
        # Step 2: Replace specific problematic characters
        replacements = {
            '\xa0': ' ',     # non-breaking space
            '\u00a0': ' ',   # another way to represent non-breaking space
            '\u2013': '-',   # en dash
            '\u2014': '--',  # em dash
            '\u2018': "'",   # left single quote
            '\u2019': "'",   # right single quote
            '\u201c': '"',   # left double quote
            '\u201d': '"',   # right double quote
            '\u2026': '...',  # ellipsis
            '\u00a9': '(c)', # copyright symbol
            '\u00ae': '(R)', # registered trademark
            '\u2122': '(TM)', # trademark
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Step 3: Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Step 4: AGGRESSIVE cleaning - only keep safe characters
        safe_chars = []
        for i, char in enumerate(text):
            char_code = ord(char)
            if char_code <= 127:  # Pure ASCII
                safe_chars.append(char)
            elif char.isprintable() and not unicodedata.combining(char):
                # For non-ASCII chars, replace with closest ASCII equivalent or remove
                if char_code == 160:  # Another non-breaking space variant
                    safe_chars.append(' ')
                else:
                    # Try to get ASCII equivalent
                    ascii_equiv = unicodedata.normalize('NFKD', char).encode('ascii', 'ignore').decode('ascii')
                    if ascii_equiv:
                        safe_chars.append(ascii_equiv)
                    else:
                        safe_chars.append('?')  # Replace with ? or skip entirely
            # Skip combining characters and other problematic chars
        
        result = ''.join(safe_chars)
        
        # Step 5: Final check - ensure no problematic characters remain
        try:
            result.encode('ascii')
            logger.debug(f"Cleaned text (first 100 chars): {repr(result[:100])}")
            return result
        except UnicodeEncodeError as e:
            logger.error(f"Text still contains non-ASCII after cleaning: {e}")
            # Last resort: force ASCII
            return result.encode('ascii', errors='replace').decode('ascii')
    
    async def _send_summary_email(self, to_email: str, episodes: List[Dict], 
                                 subject: str, template: str) -> Dict[str, Any]:
        """Send episode summary email with enhanced debugging"""
        try:
            if not episodes:
                return {"success": False, "message": "No episodes to summarize"}
            
            # Debug each episode for problematic characters BEFORE processing
            for i, ep in enumerate(episodes):
                ep_name = str(ep.get('episode', {}).get('name', ''))
                summary = str(ep.get('summary', ''))
                if '\xa0' in ep_name or '\xa0' in summary:
                    logger.error(f"Found \\xa0 in episode {i}: name={repr(ep_name[:50])}, summary={repr(summary[:50])}")
            
            # Generate HTML email content with aggressive cleaning
            html_content = self._generate_summary_html(episodes, template)
            
            # Debug the final content
            logger.error(f"DEBUG - Subject: {repr(subject)}")
            logger.error(f"DEBUG - Content preview: {repr(html_content[:200])}")
            
            # Send email
            success = await self._send_email(to_email, subject, html_content, is_html=True)
            
            return {
                "success": success,
                "message": f"Summary email sent to {to_email}" if success else "Failed to send email",
                "episodes_count": len(episodes)
            }
            
        except Exception as e:
            logger.error(f"Error sending summary email: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def _send_notification(self, to_email: str, subject: str, message: str) -> Dict[str, Any]:
        """Send simple notification email"""
        try:
            success = await self._send_email(to_email, subject, message)
            return {
                "success": success,
                "message": f"Notification sent to {to_email}" if success else "Failed to send notification"
            }
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def _send_weekly_digest(self, to_email: str, episodes: List[Dict], 
                                 stats: Dict[str, Any]) -> Dict[str, Any]:
        """Send weekly digest email"""
        try:
            subject = f"Your Weekly Podcast Digest - {datetime.now().strftime('%B %d, %Y')}"
            html_content = self._generate_weekly_digest_html(episodes, stats)
            
            success = await self._send_email(to_email, subject, html_content, is_html=True)
            
            return {
                "success": success,
                "message": f"Weekly digest sent to {to_email}" if success else "Failed to send digest",
                "episodes_count": len(episodes)
            }
            
        except Exception as e:
            logger.error(f"Error sending weekly digest: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    async def _send_email(self, to_email: str, subject: str, content: str, is_html: bool = False) -> bool:
        """Send email using SMTP with bulletproof encoding"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.error("SMTP credentials not configured")
                return False
            
            # AGGRESSIVE cleaning
            subject = self._clean_text(str(subject))
            content = self._clean_text(str(content))
            
            # Debug the cleaned content
            logger.debug(f"Final subject: {repr(subject[:50])}")
            logger.debug(f"Final content preview: {repr(content[:100])}")
            
            # Verify no problematic characters remain
            try:
                subject.encode('ascii')
                content.encode('ascii')
            except UnicodeEncodeError as e:
                logger.error(f"Still have encoding issues after cleaning: {e}")
                # Force brutal ASCII conversion
                subject = subject.encode('ascii', errors='replace').decode('ascii')
                content = content.encode('ascii', errors='replace').decode('ascii')
            
            # Create message with ASCII charset to be safe
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Use ASCII charset for maximum compatibility
            if is_html:
                html_part = MIMEText(content, 'html', 'ascii')
                msg.attach(html_part)
            else:
                text_part = MIMEText(content, 'plain', 'ascii')
                msg.attach(text_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                # Convert message to string with ASCII encoding
                msg_string = msg.as_string()
                server.sendmail(self.from_email, [to_email], msg_string.encode('ascii', errors='replace'))
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            # Log the actual problematic content for debugging
            if "ascii" in str(e).lower():
                logger.error("ASCII encoding issue detected. Check your episode data for Unicode characters.")
                # You might want to inspect the raw episode data here
            return False
    
    def _generate_summary_html(self, episodes: List[Dict], template: str) -> str:
        """Generate HTML content for episode summary with extra cleaning"""
        episodes_html = ""
        
        for i, episode_data in enumerate(episodes, 1):
            episode = episode_data.get('episode', {})
            
            # Clean ALL text fields thoroughly
            summary = self._clean_text(str(episode_data.get('summary', 'No summary available')))
            relevance_score = episode_data.get('relevance_score', 0)
            episode_name = self._clean_text(str(episode.get('name', 'Unknown Episode')))
            show_name = self._clean_text(str(episode.get('show', {}).get('name', 'Unknown Show')))
            description = self._clean_text(str(episode.get('description', '')))
            
            # Debug log the cleaned content
            logger.debug(f"Episode {i} cleaned - Name: {repr(episode_name[:50])}")
            logger.debug(f"Episode {i} cleaned - Summary: {repr(summary[:50])}")
            
            episodes_html += f"""
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 15px 0; background: #f9f9f9;">
                <h3 style="color: #1db954; margin-top: 0;">{i}. {episode_name}</h3>
                <p style="color: #666; font-size: 14px;">
                    <strong>Show:</strong> {show_name}<br>
                    <strong>Duration:</strong> {self._format_duration(episode.get('duration_ms', 0))}<br>
                    <strong>Relevance Score:</strong> {relevance_score:.1f}/1.0
                </p>
                <p style="line-height: 1.6;">{summary}</p>
                <p style="color: #888; font-size: 12px; font-style: italic;">
                    {description[:200]}{'...' if len(description) > 200 else ''}
                </p>
            </div>
            """
        
        current_time = datetime.now().strftime('%A, %B %d, %Y')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Your Podcast Summary</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #1db954; text-align: center;">🎵 Your Daily Podcast Summary</h1>
            <p style="text-align: center; color: #666;">
                {current_time}
            </p>
            
            <div style="background: #1db954; color: white; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <h2 style="margin: 0;">Found {len(episodes)} New Episode{'s' if len(episodes) != 1 else ''} for You!</h2>
            </div>
            
            {episodes_html}
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f0f0f0; border-radius: 8px;">
                <p style="margin: 0; color: #666;">
                    🎧 These episodes have been automatically added to your Spotify queue.<br>
                    Open Spotify to start listening!
                </p>
            </div>
            
            <p style="text-align: center; color: #999; font-size: 12px; margin-top: 30px;">
                Powered by Enhanced MCP Spotify Podcast Agent
            </p>
        </body>
        </html>
        """
        
        # Final cleaning of the entire HTML
        return self._clean_text(html_content)
    
    def _generate_weekly_digest_html(self, episodes: List[Dict], stats: Dict[str, Any]) -> str:
        """Generate HTML content for weekly digest"""
        total_episodes = len(episodes)
        total_duration = sum(ep.get('episode', {}).get('duration_ms', 0) for ep in episodes)
        avg_score = sum(ep.get('relevance_score', 0) for ep in episodes) / max(len(episodes), 1)
        
        episodes_html = ""
        for i, episode_data in enumerate(episodes, 1):
            episode = episode_data.get('episode', {})
            episode_name = self._clean_text(str(episode.get('name', 'Unknown')))
            show_name = self._clean_text(str(episode.get('show', {}).get('name', 'Unknown Show')))
            
            episodes_html += f"""
            <li style="margin: 10px 0;">
                <strong>{episode_name}</strong> 
                ({self._format_duration(episode.get('duration_ms', 0))})
                <br><span style="color: #666; font-size: 14px;">{show_name}</span>
            </li>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Weekly Podcast Digest</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #1db954; text-align: center;">📊 Your Weekly Podcast Digest</h1>
            
            <div style="background: #1db954; color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <div style="text-align: center;">
                    <div style="margin: 10px;">
                        <h3 style="margin: 0; font-size: 24px;">{total_episodes}</h3>
                        <p style="margin: 5px 0 0 0;">Episodes</p>
                    </div>
                    <div style="margin: 10px;">
                        <h3 style="margin: 0; font-size: 24px;">{self._format_duration(total_duration)}</h3>
                        <p style="margin: 5px 0 0 0;">Total Time</p>
                    </div>
                    <div style="margin: 10px;">
                        <h3 style="margin: 0; font-size: 24px;">{avg_score:.1f}/1.0</h3>
                        <p style="margin: 5px 0 0 0;">Avg Score</p>
                    </div>
                </div>
            </div>
            
            <h2 style="color: #333;">This Week's Episodes:</h2>
            <ul style="line-height: 1.8;">
                {episodes_html}
            </ul>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f0f0f0; border-radius: 8px;">
                <p style="margin: 0; color: #666;">
                    Keep up the great listening! 🎧
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._clean_text(html_content)
    
    def _format_duration(self, duration_ms: int) -> str:
        """Format duration from milliseconds to human readable"""
        if not duration_ms:
            return "Unknown"
        
        minutes = duration_ms // 60000
        if minutes < 60:
            return f"{minutes}m"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"{hours}h {remaining_minutes}m"
    
    async def _read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific email resource"""
        if uri == "email://templates":
            return {
                "templates": ["default", "minimal", "detailed"],
                "description": "Available email templates"
            }
        elif uri == "email://history":
            return {
                "recent_emails": [],
                "description": "Email sending history (not implemented)"
            }
        else:
            raise ValueError(f"Unknown resource URI: {uri}")