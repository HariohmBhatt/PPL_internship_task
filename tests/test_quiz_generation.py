"""Quiz generation tests."""

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


def test_create_quiz_success():
    """Test successful quiz creation."""
    headers = get_auth_headers()
    
    quiz_data = {
        "subject": "Mathematics",
        "grade_level": "8",
        "num_questions": 5,
        "difficulty": "medium",
        "topics": ["algebra", "geometry"],
        "question_types": ["MCQ", "TF"],
        "standard": "Common Core",
        "adaptive": False
    }
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["subject"] == "Mathematics"
    assert data["grade_level"] == "8"
    assert data["num_questions"] == 5
    assert data["difficulty"] == "medium"
    assert data["topics"] == ["algebra", "geometry"]
    assert data["question_types"] == ["MCQ", "TF"]
    assert data["standard"] == "Common Core"
    assert data["adaptive"] == False
    assert "id" in data
    assert "title" in data
    assert data["is_published"] == True


def test_create_adaptive_quiz():
    """Test creating an adaptive quiz."""
    headers = get_auth_headers()
    
    quiz_data = {
        "subject": "Science",
        "grade_level": "10",
        "num_questions": 8,
        "difficulty": "adaptive",
        "topics": ["physics", "chemistry"],
        "question_types": ["MCQ", "short_answer"],
        "adaptive": True
    }
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["adaptive"] == True
    assert data["difficulty"] == "adaptive"


def test_get_quiz_by_id():
    """Test retrieving quiz by ID."""
    headers = get_auth_headers()
    
    # First create a quiz
    quiz_data = {
        "subject": "History",
        "grade_level": "7",
        "num_questions": 3,
        "difficulty": "easy",
        "topics": ["ancient_history"],
        "question_types": ["MCQ"]
    }
    
    create_response = client.post("/quizzes", json=quiz_data, headers=headers)
    quiz_id = create_response.json()["id"]
    
    # Get the quiz
    response = client.get(f"/quizzes/{quiz_id}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == quiz_id
    assert data["subject"] == "History"


def test_get_quiz_questions():
    """Test retrieving quiz questions without revealing answers."""
    headers = get_auth_headers()
    
    # Create a quiz
    quiz_data = {
        "subject": "English",
        "grade_level": "9",
        "num_questions": 4,
        "difficulty": "medium",
        "topics": ["grammar", "literature"],
        "question_types": ["MCQ", "TF"]
    }
    
    create_response = client.post("/quizzes", json=quiz_data, headers=headers)
    quiz_id = create_response.json()["id"]
    
    # Get questions
    response = client.get(f"/quizzes/{quiz_id}/questions", headers=headers)
    assert response.status_code == 200
    
    questions = response.json()
    assert len(questions) == 4
    
    # Check that questions don't reveal answers
    for question in questions:
        assert "question_text" in question
        assert "question_type" in question
        assert "difficulty" in question
        assert "topic" in question
        assert "points" in question
        assert "order" in question
        
        # Should NOT include these fields (answers not revealed)
        assert "correct_answer" not in question
        assert "explanation" not in question


def test_quiz_validation():
    """Test quiz creation validation."""
    headers = get_auth_headers()
    
    # Invalid difficulty
    quiz_data = {
        "subject": "Math",
        "grade_level": "8",
        "num_questions": 5,
        "difficulty": "invalid_difficulty",
        "topics": ["algebra"],
        "question_types": ["MCQ"]
    }
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    assert response.status_code == 422
    
    # Invalid question type
    quiz_data["difficulty"] = "medium"
    quiz_data["question_types"] = ["INVALID_TYPE"]
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    assert response.status_code == 422
    
    # Too many questions
    quiz_data["question_types"] = ["MCQ"]
    quiz_data["num_questions"] = 100  # Over limit
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    assert response.status_code == 422
    
    # Empty topics
    quiz_data["num_questions"] = 5
    quiz_data["topics"] = []
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    assert response.status_code == 422


def test_get_nonexistent_quiz():
    """Test getting a quiz that doesn't exist."""
    headers = get_auth_headers()
    
    response = client.get("/quizzes/99999", headers=headers)
    assert response.status_code == 404


def test_quiz_creation_deterministic():
    """Test that quiz creation with same parameters produces consistent results."""
    headers = get_auth_headers()
    
    quiz_data = {
        "subject": "Test_Subject",
        "grade_level": "Test_Grade",
        "num_questions": 3,
        "difficulty": "easy",
        "topics": ["test_topic"],
        "question_types": ["MCQ"]
    }
    
    # Create two quizzes with identical parameters
    response1 = client.post("/quizzes", json=quiz_data, headers=headers)
    response2 = client.post("/quizzes", json=quiz_data, headers=headers)
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    quiz1_id = response1.json()["id"]
    quiz2_id = response2.json()["id"]
    
    # Get questions for both quizzes
    questions1 = client.get(f"/quizzes/{quiz1_id}/questions", headers=headers).json()
    questions2 = client.get(f"/quizzes/{quiz2_id}/questions", headers=headers).json()
    
    # Should have same structure (MockProvider is deterministic)
    assert len(questions1) == len(questions2) == 3
    
    # Questions should be similar (same topics, types, etc.)
    for q1, q2 in zip(questions1, questions2):
        assert q1["question_type"] == q2["question_type"]
        assert q1["topic"] == q2["topic"]
        assert q1["difficulty"] == q2["difficulty"]
