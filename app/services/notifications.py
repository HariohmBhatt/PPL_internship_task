"""Email notification service for quiz results."""

import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

import aiosmtplib
import structlog
from jinja2 import Template
from pydantic import BaseModel, EmailStr

from app.core.config import get_settings

logger = structlog.get_logger()


class EmailNotification(BaseModel):
    """Email notification model."""
    
    to_email: EmailStr
    subject: str
    template_name: str
    template_data: Dict[str, Any]


class NotificationService:
    """Service for sending email notifications."""
    
    def __init__(self) -> None:
        self.settings = get_settings()
        
    async def send_quiz_result_email(
        self, 
        user_email: str, 
        user_name: str,
        quiz_title: str,
        score_percentage: float,
        total_score: int,
        max_possible_score: int,
        correct_answers: int,
        total_questions: int,
        performance_level: str,
        suggestions: Optional[list[str]] = None,
        strengths: Optional[list[str]] = None,
        weaknesses: Optional[list[str]] = None
    ) -> bool:
        """Send quiz result notification email."""
        
        if not self.settings.notification_enabled:
            logger.info("Email notifications disabled, skipping")
            return True
            
        if not self.settings.smtp_username or not self.settings.smtp_password:
            logger.warning("SMTP credentials not configured, skipping email")
            return False
            
        try:
            # validate target email
            to_email = (user_email or "").strip()
            if not to_email:
                logger.warning("No user email provided; cannot send notification")
                return False

            template_data = {
                "user_name": user_name,
                "quiz_title": quiz_title,
                "score_percentage": round(score_percentage, 1),
                "total_score": total_score,
                "max_possible_score": max_possible_score,
                "correct_answers": correct_answers,
                "total_questions": total_questions,
                "performance_level": performance_level,
                "suggestions": suggestions or [],
                "strengths": strengths or [],
                "weaknesses": weaknesses or []
            }
            
            subject = f"Quiz Results: {quiz_title} - {round(score_percentage)}%"
            
            html_content = self._render_quiz_result_template(template_data)
            text_content = self._render_quiz_result_text_template(template_data)
            
            await self._send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            logger.info(
                "Quiz result email sent successfully",
                to_email=to_email,
                quiz_title=quiz_title,
                score=score_percentage
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send quiz result email",
                error=str(e),
                to_email=user_email,
                quiz_title=quiz_title
            )
            return False
    
    async def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        text_content: str
    ) -> None:
        """Send email via SMTP."""
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = self.settings.notification_from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        
        # Add text and HTML parts
        text_part = MIMEText(text_content, "plain")
        html_part = MIMEText(html_content, "html")
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        await aiosmtplib.send(
            msg,
            hostname=self.settings.smtp_host,
            port=self.settings.smtp_port,
            start_tls=self.settings.smtp_use_tls,
            username=self.settings.smtp_username,
            password=self.settings.smtp_password,
        )
    
    def _render_quiz_result_template(self, data: Dict[str, Any]) -> str:
        """Render HTML email template for quiz results."""
        
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #667eea; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .score-box { background: #e6fffa; border: 2px solid #38a169; padding: 15px; margin: 15px 0; text-align: center; }
        .score { font-size: 24px; font-weight: bold; color: #38a169; }
        .suggestions { background: #fff5f5; border-left: 4px solid #e53e3e; padding: 15px; margin: 15px 0; }
        .strengths { background: #f0fff4; border-left: 4px solid #38a169; padding: 15px; margin: 15px 0; }
        .weaknesses { background: #fef5e7; border-left: 4px solid #ed8936; padding: 15px; margin: 15px 0; }
        ul { padding-left: 20px; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 AI Quiz Results</h1>
            <h2>{{ quiz_title }}</h2>
        </div>
        
        <div class="content">
            <p>Hi {{ user_name }},</p>
            
            <p>Congratulations on completing your quiz! Here are your results:</p>
            
            <div class="score-box">
                <div class="score">{{ score_percentage }}%</div>
                <p><strong>Score:</strong> {{ total_score }}/{{ max_possible_score }} points</p>
                <p><strong>Correct Answers:</strong> {{ correct_answers }}/{{ total_questions }}</p>
                <p><strong>Performance Level:</strong> {{ performance_level }}</p>
            </div>
            
            {% if strengths %}
            <div class="strengths">
                <h3>💪 Your Strengths</h3>
                <ul>
                {% for strength in strengths %}
                    <li>{{ strength }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if suggestions %}
            <div class="suggestions">
                <h3>🤖 AI Improvement Suggestions</h3>
                <ul>
                {% for suggestion in suggestions %}
                    <li>{{ suggestion }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if weaknesses %}
            <div class="weaknesses">
                <h3>🎯 Areas for Improvement</h3>
                <ul>
                {% for weakness in weaknesses %}
                    <li>{{ weakness }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            <p>Keep up the great work and continue learning!</p>
            
            <p>Best regards,<br>
            The AI Quiz Team</p>
        </div>
        
        <div class="footer">
            <p>This is an automated message from AI Quiz Microservice.</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        return template.render(**data)
    
    def _render_quiz_result_text_template(self, data: Dict[str, Any]) -> str:
        """Render text email template for quiz results."""
        
        template_str = """
AI Quiz Results: {{ quiz_title }}

Hi {{ user_name }},

Congratulations on completing your quiz! Here are your results:

SCORE: {{ score_percentage }}%
- Score: {{ total_score }}/{{ max_possible_score }} points  
- Correct Answers: {{ correct_answers }}/{{ total_questions }}
- Performance Level: {{ performance_level }}

{% if strengths %}
YOUR STRENGTHS:
{% for strength in strengths %}
• {{ strength }}
{% endfor %}

{% endif %}
{% if suggestions %}
AI IMPROVEMENT SUGGESTIONS:
{% for suggestion in suggestions %}
• {{ suggestion }}
{% endfor %}

{% endif %}
{% if weaknesses %}
AREAS FOR IMPROVEMENT:
{% for weakness in weaknesses %}
• {{ weakness }}
{% endfor %}

{% endif %}
Keep up the great work and continue learning!

Best regards,
The AI Quiz Team

---
This is an automated message from AI Quiz Microservice.
        """
        
        template = Template(template_str)
        return template.render(**data)


# Global notification service instance
notification_service = NotificationService()
