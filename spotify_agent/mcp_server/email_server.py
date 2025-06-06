"""
MCP Server for Email operations - FIXED VERSION WITH DEBUG
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
            ),
            "test_email_with_debug": MCPTool(
                name="test_email_with_debug",
                description="Test email with known problematic content to debug Unicode issues",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to_email": {"type": "string", "description": "Recipient email"}
                    },
                    "required": ["to_email"]
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
        
        elif name == "test_email_with_debug":
            return await self.test_email_with_debug(arguments["to_email"])
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def test_email_with_debug(self, to_email: str) -> Dict[str, Any]:
        """Test email with known problematic content to debug Unicode issues"""
        
        # Test with known problematic content
        test_cases = [
            "Simple ASCII text",
            "Text with\xa0non-breaking space",
            "Text with \u2014 em dash",
            "Text with \u201csmart quotes\u201d",
            "Text with\u2026ellipsis",
        ]
        
        for i, test_content in enumerate(test_cases):
            logger.error(f"=== Testing case {i}: {repr(test_content)} ===")
            
            # Clean the content
            cleaned = self._clean_text(test_content)
            logger.error(f"Cleaned to: {repr(cleaned)}")
            
            # Test ASCII encoding
            try:
                cleaned.encode('ascii')
                logger.error("✓ ASCII encoding successful")
            except UnicodeEncodeError as e:
                logger.error(f"✗ ASCII encoding failed: {e}")
        
        # Now test with minimal email
        minimal_subject = "Test Email"
        minimal_content = "This is a test email with basic content."
        
        logger.error(f"Testing minimal email: subject={repr(minimal_subject)}, content={repr(minimal_content)}")
        
        success = await self._send_email(to_email, minimal_subject, minimal_content, is_html=False)
        
        return {
            "success": success,
            "message": "Test completed - check logs for details",
            "test_cases_count": len(test_cases)
        }
    
    def _clean_text(self, text: str) -> str:
        """Smart text cleaning - preserves HTML structure while removing problematic Unicode"""
        if not text:
            return ""
        
        # Convert to string if not already
        text = str(text)
        
        # Log the exact problematic characters for debugging
        problematic_chars = []
        for i, char in enumerate(text):
            if ord(char) > 127:
                problematic_chars.append((i, char, ord(char)))
        
        if problematic_chars:
            logger.debug(f"Found {len(problematic_chars)} non-ASCII characters in text")
        
        # SMART cleaning: Replace only known problematic characters, preserve everything else
        replacements = {
            '\xa0': ' ',      # non-breaking space
            '\u00a0': ' ',    # unicode non-breaking space
            '\u2013': '-',    # en dash
            '\u2014': '-',    # em dash (changed from '--' to '-')
            '\u2018': "'",    # left single quote
            '\u2019': "'",    # right single quote
            '\u201c': '"',    # left double quote
            '\u201d': '"',    # right double quote
            '\u2026': '...',  # ellipsis
            '\u00a9': '(c)',  # copyright symbol
            '\u00ae': '(R)',  # registered trademark
            '\u2122': '(TM)', # trademark
            # Add emoji removal only for very common ones
            '🎵': '',         # musical note
            '📧': '',         # email
            '🎧': '',         # headphones
            '📊': '',         # chart
        }
        
        # Apply targeted replacements
        cleaned_text = text
        for old, new in replacements.items():
            cleaned_text = cleaned_text.replace(old, new)
        
        # Remove any remaining high Unicode characters (but preserve basic HTML and text)
        # Only remove characters that are definitely problematic
        final_chars = []
        for char in cleaned_text:
            char_code = ord(char)
            if char_code <= 127:  # Keep all ASCII
                final_chars.append(char)
            elif char_code == 160:  # Non-breaking space variants
                final_chars.append(' ')
            elif 8192 <= char_code <= 8303:  # Various Unicode spaces and punctuation
                final_chars.append(' ')
            elif char_code >= 127000:  # Emoji range
                final_chars.append('')  # Remove emojis
            else:
                # Keep other Unicode characters (like accented letters, etc.)
                final_chars.append(char)
        
        result = ''.join(final_chars)
        
        # Normalize multiple spaces
        import re
        result = re.sub(r'\s+', ' ', result)
        result = result.strip()
        
        # Final verification - only warn, don't force ASCII
        try:
            result.encode('utf-8')  # Check UTF-8 instead of ASCII
        except UnicodeEncodeError as e:
            logger.warning(f"Text still has encoding issues: {e}")
        
        return result
    
    # Updated _send_summary_email method with debugging
    async def _send_summary_email(self, to_email: str, episodes: List[Dict], 
                                subject: str, template: str) -> Dict[str, Any]:
        """Send episode summary email with maximum debugging"""
        try:
            if not episodes:
                return {"success": False, "message": "No episodes to summarize"}
            
            # DEBUG: Check all episode data for Unicode before processing
            self.debug_episode_data(episodes)
            
            # Generate HTML with ultra-clean data
            html_content = self._generate_summary_html(episodes, template)
            
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
        """Ultra-safe email sending with maximum debugging"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.error("SMTP credentials not configured")
                return False
            
            # Log the raw inputs first
            logger.error(f"RAW SUBJECT: {repr(subject)}")
            logger.error(f"RAW CONTENT (first 200 chars): {repr(content[:200])}")
            
            # Ultra-aggressive cleaning
            subject = self._clean_text(str(subject))
            content = self._clean_text(str(content))
            
            # Verify cleaning worked
            logger.error(f"CLEANED SUBJECT: {repr(subject)}")
            logger.error(f"CLEANED CONTENT (first 200 chars): {repr(content[:200])}")
            
            # Double-check for problematic characters
            for i, char in enumerate(subject):
                if ord(char) > 127:
                    logger.error(f"SUBJECT still has non-ASCII at position {i}: {repr(char)}")
            
            for i, char in enumerate(content[:1000]):  # Check first 1000 chars
                if ord(char) > 127:
                    logger.error(f"CONTENT still has non-ASCII at position {i}: {repr(char)}")
                    break  # Stop after first problematic char to avoid spam
            
            # Triple-check with encoding test
            try:
                subject.encode('ascii')
                content.encode('ascii')
                logger.info("Both subject and content are ASCII-safe")
            except UnicodeEncodeError as e:
                logger.error(f"ENCODING CHECK FAILED: {e}")
                return False
            
            # BETTER APPROACH: Use UTF-8 encoding instead of forcing ASCII
            msg = MIMEText('', 'html' if is_html else 'plain', 'utf-8')
            
            # Manually set headers using cleaned strings
            msg['From'] = self._clean_text(str(self.from_email))
            msg['To'] = self._clean_text(str(to_email))
            msg['Subject'] = subject
            
            # Set the payload manually
            msg.set_payload(content)
            
            # Keep UTF-8 charset for better compatibility
            msg.set_charset('utf-8')
            
            # Convert to string and clean LIGHTLY
            try:
                msg_string = str(msg)
                
                # Light cleaning - only remove the most problematic characters
                msg_string = msg_string.replace('\xa0', ' ')  # Just non-breaking spaces
                
                # Try UTF-8 encoding first
                try:
                    msg_bytes = msg_string.encode('utf-8')
                    logger.info(f"Message encoded with UTF-8 ({len(msg_bytes)} bytes)")
                except UnicodeEncodeError:
                    # Fallback to ASCII with replacement only if UTF-8 fails
                    msg_bytes = msg_string.encode('ascii', errors='replace')
                    logger.info(f"Message encoded with ASCII replacement ({len(msg_bytes)} bytes)")
                
            except Exception as e:
                logger.error(f"Message string conversion failed: {e}")
                return False
            
            # Send with maximum safety and ASCII-only credentials
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                
                # Clean SMTP credentials - this might be the source!
                clean_username = self._clean_text(str(self.smtp_username))
                clean_password = self._clean_text(str(self.smtp_password))
                clean_from = self._clean_text(str(self.from_email))
                clean_to = self._clean_text(str(to_email))
                
                logger.error(f"SMTP CREDENTIALS - Username: {repr(clean_username[:10])}...")
                
                try:
                    clean_username.encode('ascii')
                    clean_password.encode('ascii')
                    logger.info("SMTP credentials are ASCII-safe")
                except UnicodeEncodeError as e:
                    logger.error(f"SMTP CREDENTIALS have Unicode: {e}")
                    # Force clean them
                    clean_username = clean_username.encode('ascii', errors='replace').decode('ascii')
                    clean_password = clean_password.encode('ascii', errors='replace').decode('ascii')
                
                server.login(clean_username, clean_password)
                
                # Send with ASCII-cleaned addresses
                server.sendmail(clean_from, [clean_to], msg_bytes)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # If it's a Unicode error, log more details
            if isinstance(e, UnicodeEncodeError):
                logger.error(f"Unicode error details: start={e.start}, end={e.end}, object={repr(e.object[max(0,e.start-10):e.end+10])}")
            
            return False
        
    # Also add this debugging method to find the source of the problem
    def debug_episode_data(self, episodes: List[Dict]) -> None:
        """Debug method to find Unicode characters in episode data"""
        logger.error("=== DEBUGGING EPISODE DATA FOR UNICODE ===")
        
        for i, episode_data in enumerate(episodes):
            logger.error(f"--- Episode {i} ---")
            
            # Check all string fields in episode data
            episode = episode_data.get('episode', {})
            
            fields_to_check = [
                ('summary', episode_data.get('summary', '')),
                ('episode_name', episode.get('name', '')),
                ('show_name', episode.get('show', {}).get('name', '')),
                ('description', episode.get('description', '')),
            ]
            
            for field_name, field_value in fields_to_check:
                if field_value:
                    field_str = str(field_value)
                    for j, char in enumerate(field_str):
                        if ord(char) > 127:
                            logger.error(f"{field_name} has non-ASCII at pos {j}: {repr(char)} (code: {ord(char)})")
                            logger.error(f"{field_name} context: {repr(field_str[max(0,j-10):j+10])}")
                            break  # Just show first problematic char per field
    
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
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Your Podcast Summary</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h1 style="color: #1db954; text-align: center;">Your Daily Podcast Summary</h1>
    <p style="text-align: center; color: #666;">
        {current_time}
    </p>
    
    <div style="background: #1db954; color: white; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
        <h2 style="margin: 0;">Found {len(episodes)} New Episode{'s' if len(episodes) != 1 else ''} for You!</h2>
    </div>
    
    {episodes_html}
    
    <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f0f0f0; border-radius: 8px;">
        <p style="margin: 0; color: #666;">
            These episodes have been automatically added to your Spotify queue.<br>
            Open Spotify to start listening!
        </p>
    </div>
    
    <p style="text-align: center; color: #999; font-size: 12px; margin-top: 30px;">
        Powered by Enhanced MCP Spotify Podcast Agent
    </p>
</body>
</html>"""
        
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
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Weekly Podcast Digest</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h1 style="color: #1db954; text-align: center;">Your Weekly Podcast Digest</h1>
    
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
            Keep up the great listening!
        </p>
    </div>
</body>
</html>"""
        
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