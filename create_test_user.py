#!/usr/bin/env python3
"""
Script to create a test user with the specified email address.
This ensures we have a user in the database with hariohm.b@ahduni.edu.in for testing.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import get_async_session
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select

async def create_test_user():
    """Create a test user with the specified email address."""
    
    print("👤 Creating Test User")
    print("=" * 30)
    
    # Test user details
    username = "hariohm"
    email = "hariohm.b@ahduni.edu.in"
    password = "testpassword123"
    
    try:
        async with get_async_session() as session:
            # Check if user already exists
            existing_user = await session.execute(
                select(User).where(User.email == email)
            )
            user = existing_user.scalar_one_or_none()
            
            if user:
                print(f"✅ User already exists: {user.username} ({user.email})")
                print(f"🆔 User ID: {user.id}")
                return user.id
            
            # Create new user
            hashed_password = get_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            print(f"✅ Test user created successfully!")
            print(f"👤 Username: {new_user.username}")
            print(f"📧 Email: {new_user.email}")
            print(f"🆔 User ID: {new_user.id}")
            print(f"🔑 Password: {password}")
            
            return new_user.id
            
    except Exception as e:
        print(f"❌ Failed to create test user: {str(e)}")
        return None

async def main():
    """Main function."""
    print("🚀 AI Quiz Microservice - Test User Creation")
    print("=" * 50)
    print()
    
    user_id = await create_test_user()
    
    print()
    print("=" * 50)
    
    if user_id:
        print("🎉 Test User Setup Complete!")
        print(f"🔗 You can now use this user for testing the email functionality")
        print()
        print("📋 Login credentials for testing:")
        print("  Username: hariohm")
        print("  Password: testpassword123")
        print("  Email: hariohm.b@ahduni.edu.in")
    else:
        print("💥 Test User Creation Failed!")
    
    return user_id is not None

if __name__ == "__main__":
    # Run the script
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
