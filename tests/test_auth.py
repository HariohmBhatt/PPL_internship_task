"""Authentication tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token

client = TestClient(app)


def test_login_success():
    """Test successful login with any credentials."""
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert isinstance(data["expires_in"], int)


def test_login_with_different_credentials():
    """Test login works with any username/password in development."""
    login_data = {
        "username": "anotheruser",
        "password": "anotherpass"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data


def test_login_validation():
    """Test login validation for missing fields."""
    # Missing password
    response = client.post("/auth/login", json={"username": "test"})
    assert response.status_code == 422
    
    # Missing username
    response = client.post("/auth/login", json={"password": "test"})
    assert response.status_code == 422
    
    # Empty payload
    response = client.post("/auth/login", json={})
    assert response.status_code == 422


def test_protected_route_without_token():
    """Test that protected routes block requests without token."""
    response = client.post("/quizzes", json={
        "subject": "Math",
        "grade_level": "8",
        "num_questions": 5,
        "difficulty": "medium",
        "topics": ["algebra"],
        "question_types": ["MCQ"]
    })
    assert response.status_code == 422  # Missing Authorization header


def test_protected_route_with_invalid_token():
    """Test that protected routes block requests with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.post("/quizzes", json={
        "subject": "Math",
        "grade_level": "8",
        "num_questions": 5,
        "difficulty": "medium",
        "topics": ["algebra"],
        "question_types": ["MCQ"]
    }, headers=headers)
    assert response.status_code == 401


def test_protected_route_with_valid_token():
    """Test that protected routes work with valid token."""
    # First login to get token
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass"
    })
    token = login_response.json()["access_token"]
    
    # Use token to access protected route
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/quizzes", json={
        "subject": "Math",
        "grade_level": "8",
        "num_questions": 5,
        "difficulty": "medium",
        "topics": ["algebra"],
        "question_types": ["MCQ"]
    }, headers=headers)
    
    # Should not be unauthorized (might be other errors, but not 401)
    assert response.status_code != 401


def test_jwt_token_creation():
    """Test JWT token creation utility."""
    token_data = {"sub": "123", "username": "testuser"}
    token = create_access_token(token_data)
    
    assert isinstance(token, str)
    assert len(token) > 0
    assert "." in token  # JWT has dots


def test_invalid_authorization_header_format():
    """Test invalid authorization header formats."""
    # Missing 'Bearer ' prefix
    headers = {"Authorization": "invalid_format_token"}
    response = client.post("/quizzes", json={
        "subject": "Math",
        "grade_level": "8", 
        "num_questions": 5,
        "difficulty": "medium",
        "topics": ["algebra"],
        "question_types": ["MCQ"]
    }, headers=headers)
    assert response.status_code == 401
