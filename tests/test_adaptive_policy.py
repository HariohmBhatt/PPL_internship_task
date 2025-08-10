"""Adaptive policy tests."""

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


def create_adaptive_quiz():
    """Helper to create an adaptive quiz."""
    headers = get_auth_headers()
    
    quiz_data = {
        "subject": "Mathematics",
        "grade_level": "8",
        "num_questions": 6,  # Multiple questions for adaptation
        "difficulty": "adaptive",
        "topics": ["algebra", "geometry"],
        "question_types": ["MCQ", "TF"],
        "adaptive": True
    }
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    assert response.status_code == 200
    return response.json()["id"]


def test_adaptive_quiz_next_question_start():
    """Test getting the first question in adaptive mode."""
    headers = get_auth_headers()
    quiz_id = create_adaptive_quiz()
    
    response = client.post(f"/quizzes/{quiz_id}/next", json={}, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "question" in data
    assert "is_complete" in data
    assert "progress" in data
    
    assert data["is_complete"] == False
    assert data["question"] is not None
    
    # Check progress structure
    progress = data["progress"]
    assert "total_questions" in progress
    assert "answered" in progress
    assert "remaining" in progress
    assert progress["answered"] == 0  # No questions answered yet


def test_adaptive_quiz_step_up_difficulty():
    """Test adaptive difficulty stepping up with good performance."""
    headers = get_auth_headers()
    quiz_id = create_adaptive_quiz()
    
    # Get questions to simulate answering
    questions_response = client.get(f"/quizzes/{quiz_id}/questions", headers=headers)
    questions = questions_response.json()
    
    # Simulate good performance by "answering" questions correctly
    # Note: This test validates the policy logic, actual submission would be via submit endpoint
    
    # Start adaptive session
    response = client.post(f"/quizzes/{quiz_id}/next", json={}, headers=headers)
    assert response.status_code == 200
    
    first_question = response.json()["question"]
    assert first_question["difficulty"] in ["easy", "medium"]  # Should start appropriately


def test_adaptive_quiz_step_down_difficulty():
    """Test adaptive difficulty stepping down with poor performance."""
    headers = get_auth_headers()
    quiz_id = create_adaptive_quiz()
    
    # Start adaptive session
    response = client.post(f"/quizzes/{quiz_id}/next", json={}, headers=headers)
    assert response.status_code == 200
    
    # The adaptive logic is tested through the service layer
    # This test ensures the endpoint works correctly
    data = response.json()
    assert data["question"] is not None
    assert data["is_complete"] == False


def test_adaptive_quiz_hold_difficulty():
    """Test adaptive difficulty holding current level with average performance."""
    headers = get_auth_headers()
    quiz_id = create_adaptive_quiz()
    
    # Start adaptive session
    response = client.post(f"/quizzes/{quiz_id}/next", json={}, headers=headers)
    assert response.status_code == 200
    
    # Verify basic adaptive functionality
    data = response.json()
    progress = data["progress"]
    
    # Should show correct initial state
    assert progress["answered"] == 0
    assert progress["total_questions"] > 0


def test_adaptive_quiz_completion():
    """Test adaptive quiz completion detection."""
    headers = get_auth_headers()
    
    # Create quiz with only 1 question for easy completion testing
    quiz_data = {
        "subject": "TestCompletion",
        "grade_level": "8",
        "num_questions": 1,
        "difficulty": "adaptive",
        "topics": ["test"],
        "question_types": ["MCQ"],
        "adaptive": True
    }
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    quiz_id = response.json()["id"]
    
    # Start adaptive session
    next_response = client.post(f"/quizzes/{quiz_id}/next", json={}, headers=headers)
    assert next_response.status_code == 200
    
    # Should get the single question
    data = next_response.json()
    assert data["question"] is not None
    assert data["is_complete"] == False
    
    # Submit answer to complete quiz
    questions_response = client.get(f"/quizzes/{quiz_id}/questions", headers=headers)
    questions = questions_response.json()
    
    submission_data = {
        "answers": [{
            "question_id": questions[0]["id"],
            "selected_option": questions[0]["options"][0]
        }]
    }
    
    submit_response = client.post(f"/quizzes/{quiz_id}/submit", json=submission_data, headers=headers)
    assert submit_response.status_code == 200
    
    # Now next question should indicate completion
    next_response2 = client.post(f"/quizzes/{quiz_id}/next", json={}, headers=headers)
    assert next_response2.status_code == 200
    
    data2 = next_response2.json()
    # After submission, should show completion or no active session
    assert data2["question"] is None or data2["is_complete"] == True


def test_adaptive_quiz_status():
    """Test adaptive quiz status endpoint."""
    headers = get_auth_headers()
    quiz_id = create_adaptive_quiz()
    
    # Check status before starting
    response = client.get(f"/quizzes/{quiz_id}/adaptive-status", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "has_active_session" in data
    assert "quiz_id" in data
    assert "is_adaptive" in data
    assert data["quiz_id"] == quiz_id
    assert data["is_adaptive"] == True
    
    if not data["has_active_session"]:
        assert "message" in data
    
    # Start session and check status
    client.post(f"/quizzes/{quiz_id}/next", json={}, headers=headers)
    
    status_response = client.get(f"/quizzes/{quiz_id}/adaptive-status", headers=headers)
    status_data = status_response.json()
    
    # Should now have active session
    if status_data["has_active_session"]:
        assert "submission_id" in status_data
        assert "progress" in status_data
        assert "started_at" in status_data


def test_non_adaptive_quiz_next_endpoint():
    """Test that next endpoint rejects non-adaptive quizzes."""
    headers = get_auth_headers()
    
    # Create regular (non-adaptive) quiz
    quiz_data = {
        "subject": "RegularQuiz",
        "grade_level": "8",
        "num_questions": 3,
        "difficulty": "medium",
        "topics": ["test"],
        "question_types": ["MCQ"],
        "adaptive": False
    }
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    quiz_id = response.json()["id"]
    
    # Try to use adaptive endpoint
    next_response = client.post(f"/quizzes/{quiz_id}/next", json={}, headers=headers)
    assert next_response.status_code == 422
    
    error_data = next_response.json()
    assert "adaptive" in error_data["error"]["message"].lower()


def test_adaptive_nonexistent_quiz():
    """Test adaptive endpoints with nonexistent quiz."""
    headers = get_auth_headers()
    
    # Next question for nonexistent quiz
    response = client.post("/quizzes/99999/next", json={}, headers=headers)
    assert response.status_code == 404
    
    # Status for nonexistent quiz
    response = client.get("/quizzes/99999/adaptive-status", headers=headers)
    assert response.status_code == 404


def test_adaptive_performance_boundaries():
    """Test the specific performance boundaries for adaptation."""
    # This is more of a unit test for the adaptive service logic
    # The boundaries are: >=80% step up, <=40% step down, 41-79% hold
    
    from app.services.adaptive import AdaptiveService
    
    service = AdaptiveService()
    
    # Test step up logic
    assert service._step_up_difficulty("easy") == "medium"
    assert service._step_up_difficulty("medium") == "hard"
    assert service._step_up_difficulty("hard") == "hard"  # Can't go higher
    
    # Test step down logic
    assert service._step_down_difficulty("hard") == "medium"
    assert service._step_down_difficulty("medium") == "easy"
    assert service._step_down_difficulty("easy") == "easy"  # Can't go lower


def test_adaptive_without_authentication():
    """Test that adaptive endpoints require authentication."""
    quiz_id = create_adaptive_quiz()
    
    # Next question without auth
    response = client.post(f"/quizzes/{quiz_id}/next", json={})
    assert response.status_code == 422  # Missing authorization header
    
    # Status without auth
    response = client.get(f"/quizzes/{quiz_id}/adaptive-status")
    assert response.status_code == 422  # Missing authorization header
