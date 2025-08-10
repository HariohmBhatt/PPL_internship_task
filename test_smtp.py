#!/usr/bin/env python3
"""
Test script for SMTP email functionality.
This script tests the email notification system with real SMTP credentials.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.notifications import notification_service

async def test_smtp_connection():
    """Test SMTP connection and send a test email."""
    
    print("🧪 Testing SMTP Email Functionality")
    print("=" * 50)
    
    # Test email details
    test_email = "hariohm.b@ahduni.edu.in"
    user_name = "Hariohm Bhatt"
    quiz_title = "Test Quiz - Bonus Features Demo"
    
    # Sample quiz results
    quiz_results = {
        "score_percentage": 85.5,
        "total_score": 8.5,
        "max_possible_score": 10.0,
        "correct_answers": 4,
        "total_questions": 5,
        "performance_level": "Excellent",
        "suggestions": [
            "Great job on algebra problems! Keep practicing factorization.",
            "Consider reviewing quadratic equations for even better performance.",
            "Your problem-solving approach is systematic and effective."
        ],
        "strengths": [
            "Strong understanding of mathematical concepts",
            "Excellent calculation accuracy",
            "Good time management"
        ],
        "weaknesses": [
            "Minor computational errors in complex problems",
            "Could improve speed on basic arithmetic"
        ]
    }
    
    print(f"📧 Sending test email to: {test_email}")
    print(f"📝 Quiz: {quiz_title}")
    print(f"📊 Score: {quiz_results['score_percentage']}%")
    print()
    
    try:
        # Attempt to send the email
        success = await notification_service.send_quiz_result_email(
            user_email=test_email,
            user_name=user_name,
            quiz_title=quiz_title,
            score_percentage=quiz_results["score_percentage"],
            total_score=quiz_results["total_score"],
            max_possible_score=quiz_results["max_possible_score"],
            correct_answers=quiz_results["correct_answers"],
            total_questions=quiz_results["total_questions"],
            performance_level=quiz_results["performance_level"],
            suggestions=quiz_results["suggestions"],
            strengths=quiz_results["strengths"],
            weaknesses=quiz_results["weaknesses"]
        )
        
        if success:
            print("✅ Email sent successfully!")
            print(f"📬 Check {test_email} for the quiz results email")
            print()
            print("📋 Email should contain:")
            print("  • Quiz title and score")
            print("  • Performance breakdown")
            print("  • AI-generated suggestions")
            print("  • Strengths and improvement areas")
            print("  • Professional HTML formatting")
            
        else:
            print("❌ Failed to send email - check SMTP configuration")
            return False
            
    except Exception as e:
        print(f"❌ Email sending failed with error: {str(e)}")
        print()
        print("🔍 Troubleshooting tips:")
        print("  • Verify Gmail app password is correct")
        print("  • Ensure 2FA is enabled on Gmail account")
        print("  • Check internet connectivity")
        print("  • Verify SMTP settings in environment variables")
        return False
    
    return True

async def test_smtp_settings():
    """Test SMTP configuration settings."""
    
    print("🔧 Checking SMTP Configuration")
    print("-" * 30)
    
    # Check environment variables
    settings = notification_service.settings
    
    config_items = [
        ("NOTIFICATION_ENABLED", settings.notification_enabled),
        ("SMTP_HOST", settings.smtp_host),
        ("SMTP_PORT", settings.smtp_port),
        ("SMTP_USERNAME", settings.smtp_username),
        ("SMTP_PASSWORD", "***" if settings.smtp_password else "NOT SET"),
        ("SMTP_USE_TLS", settings.smtp_use_tls),
        ("NOTIFICATION_FROM_EMAIL", settings.notification_from_email),
    ]
    
    all_configured = True
    
    for name, value in config_items:
        status = "✅" if value else "❌"
        print(f"  {status} {name}: {value}")
        if not value and name != "SMTP_PASSWORD":
            all_configured = False
    
    print()
    
    if all_configured:
        print("✅ SMTP configuration looks good!")
    else:
        print("❌ SMTP configuration incomplete")
        print("💡 Make sure all environment variables are set correctly")
    
    return all_configured

def set_environment_variables():
    """Set environment variables for testing."""
    
    # Set the environment variables if not already set
    env_vars = {
        "NOTIFICATION_ENABLED": "true",
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "bhatthariohm2004@gmail.com",
        "SMTP_PASSWORD": "hxae rqgy wklt kabl",
        "SMTP_USE_TLS": "true",
        "NOTIFICATION_FROM_EMAIL": "bhatthariohm2004@gmail.com",
    }
    
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value

async def main():
    """Main test function."""
    
    print("🚀 AI Quiz Microservice - SMTP Test")
    print("=" * 50)
    print()
    
    # Set environment variables for testing
    set_environment_variables()
    
    # Test configuration
    config_ok = await test_smtp_settings()
    
    if not config_ok:
        print("❌ Cannot proceed with SMTP test - configuration incomplete")
        return False
    
    print()
    
    # Test actual email sending
    email_sent = await test_smtp_connection()
    
    print()
    print("=" * 50)
    
    if email_sent:
        print("🎉 SMTP Test Completed Successfully!")
        print("📧 Email notification system is working correctly")
    else:
        print("💥 SMTP Test Failed!")
        print("🔧 Check configuration and try again")
    
    return email_sent

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
