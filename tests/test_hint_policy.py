"""Hint policy and rate limiting tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_auth_headers():
    """Helper to get authentication headers."""
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass"
    })
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_test_quiz():
    """Helper to create a test quiz and return quiz_id and question_id."""
    headers = get_auth_headers()
    
    quiz_data = {
        "subject": "Mathematics",
        "grade_level": "8",
        "num_questions": 3,
        "difficulty": "medium",
        "topics": ["algebra"],
        "question_types": ["MCQ"]
    }
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    quiz_id = response.json()["id"]
    
    # Get questions
    questions_response = client.get(f"/quizzes/{quiz_id}/questions", headers=headers)
    questions = questions_response.json()
    question_id = questions[0]["id"]
    
    return quiz_id, question_id


def test_get_hint_success():
    """Test successful hint generation."""
    headers = get_auth_headers()
    quiz_id, question_id = create_test_quiz()
    
    response = client.post(
        f"/quizzes/{quiz_id}/questions/{question_id}/hint",
        json={},
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "hint" in data
    assert isinstance(data["hint"], str)
    assert len(data["hint"]) > 0
    assert data["hints_used"] == 1
    assert data["remaining_hints"] == 2  # Default limit is 3


def test_hint_actionable_content():
    """Test that hints contain actionable content."""
    headers = get_auth_headers()
    quiz_id, question_id = create_test_quiz()
    
    response = client.post(
        f"/quizzes/{quiz_id}/questions/{question_id}/hint",
        json={},
        headers=headers
    )
    
    hint = response.json()["hint"]
    
    # Hint should be helpful but not give away the answer
    assert len(hint) > 10  # Reasonable length
    assert "answer" not in hint.lower()  # Shouldn't directly give answer
    assert any(word in hint.lower() for word in [
        "think", "consider", "review", "what", "how", "concept", "fundamental"
    ])  # Should contain guiding words


def test_hint_rate_limiting():
    """Test hint rate limiting per user per question."""
    headers = get_auth_headers()
    quiz_id, question_id = create_test_quiz()
    
    # Use hints up to the limit (3 by default)
    for i in range(3):
        response = client.post(
            f"/quizzes/{quiz_id}/questions/{question_id}/hint",
            json={},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hints_used"] == i + 1
        assert data["remaining_hints"] == 3 - (i + 1)
    
    # Fourth hint should be rate limited
    response = client.post(
        f"/quizzes/{quiz_id}/questions/{question_id}/hint",
        json={},
        headers=headers
    )
    assert response.status_code == 429
    
    error_data = response.json()
    assert "error" in error_data
    assert "rate" in error_data["error"]["message"].lower()


def test_hint_rate_limiting_per_question():
    """Test that rate limiting is per question, not per quiz."""
    headers = get_auth_headers()
    
    # Create quiz with multiple questions
    quiz_data = {
        "subject": "Mathematics",
        "grade_level": "8",
        "num_questions": 2,
        "difficulty": "medium",
        "topics": ["algebra"],
        "question_types": ["MCQ"]
    }
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    quiz_id = response.json()["id"]
    
    # Get questions
    questions_response = client.get(f"/quizzes/{quiz_id}/questions", headers=headers)
    questions = questions_response.json()
    question1_id = questions[0]["id"]
    question2_id = questions[1]["id"]
    
    # Use all hints for question 1
    for i in range(3):
        response = client.post(
            f"/quizzes/{quiz_id}/questions/{question1_id}/hint",
            json={},
            headers=headers
        )
        assert response.status_code == 200
    
    # Should still be able to get hints for question 2
    response = client.post(
        f"/quizzes/{quiz_id}/questions/{question2_id}/hint",
        json={},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["hints_used"] == 1


def test_hint_for_nonexistent_question():
    """Test hint request for nonexistent question."""
    headers = get_auth_headers()
    
    response = client.post(
        "/quizzes/99999/questions/99999/hint",
        json={},
        headers=headers
    )
    assert response.status_code == 404


def test_hint_deterministic_behavior():
    """Test that hints are deterministic for same question."""
    headers = get_auth_headers()
    quiz_id, question_id = create_test_quiz()
    
    # Get hint multiple times (after resetting rate limit in dev mode)
    response1 = client.post(
        f"/quizzes/{quiz_id}/questions/{question_id}/hint",
        json={},
        headers=headers
    )
    
    # Reset hint usage for testing
    client.delete(
        f"/quizzes/{quiz_id}/questions/{question_id}/hint-usage",
        headers=headers
    )
    
    response2 = client.post(
        f"/quizzes/{quiz_id}/questions/{question_id}/hint",
        json={},
        headers=headers
    )
    
    # Should get same hint (MockProvider is deterministic)
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json()["hint"] == response2.json()["hint"]


def test_hint_reset_development_only():
    """Test that hint reset is only available in development mode."""
    headers = get_auth_headers()
    quiz_id, question_id = create_test_quiz()
    
    # This should work in development mode (which is set in test environment)
    response = client.delete(
        f"/quizzes/{quiz_id}/questions/{question_id}/hint-usage",
        headers=headers
    )
    
    # Should succeed in development
    assert response.status_code == 200
    assert "reset" in response.json()["message"].lower()


def test_hint_without_authentication():
    """Test that hints require authentication."""
    quiz_id, question_id = create_test_quiz()
    
    response = client.post(
        f"/quizzes/{quiz_id}/questions/{question_id}/hint",
        json={}
    )
    
    # Should be unauthorized
    assert response.status_code == 422  # Missing authorization header
