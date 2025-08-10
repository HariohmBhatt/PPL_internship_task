"""History filtering tests."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone

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


def create_and_submit_quiz(subject, grade_level, score_range="good"):
    """Helper to create and submit a quiz for testing history."""
    headers = get_auth_headers()
    
    quiz_data = {
        "subject": subject,
        "grade_level": grade_level,
        "num_questions": 2,
        "difficulty": "easy",
        "topics": ["test_topic"],
        "question_types": ["MCQ"]
    }
    
    # Create quiz
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    quiz_id = response.json()["id"]
    
    # Get questions
    questions_response = client.get(f"/quizzes/{quiz_id}/questions", headers=headers)
    questions = questions_response.json()
    
    # Submit answers to get different score ranges
    answers = []
    for question in questions:
        if score_range == "good":
            # Good answer
            answers.append({
                "question_id": question["id"],
                "selected_option": question["options"][0] if question["options"] else "True"
            })
        else:
            # Potentially wrong answer
            answers.append({
                "question_id": question["id"],
                "selected_option": question["options"][-1] if question["options"] else "False"
            })
    
    submission_data = {"answers": answers}
    client.post(f"/quizzes/{quiz_id}/submit", json=submission_data, headers=headers)
    
    return quiz_id


def test_get_history_basic():
    """Test basic history retrieval."""
    headers = get_auth_headers()
    
    # Create some test submissions
    create_and_submit_quiz("Mathematics", "8")
    create_and_submit_quiz("Science", "9")
    
    response = client.get("/quizzes/history", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "submissions" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "has_next" in data
    assert "has_prev" in data
    assert "filters_applied" in data
    
    # Should have submissions
    assert len(data["submissions"]) >= 2
    
    # Check submission structure
    for submission in data["submissions"]:
        assert "id" in submission
        assert "quiz_id" in submission
        assert "quiz_title" in submission
        assert "subject" in submission
        assert "grade_level" in submission
        assert "is_completed" in submission
        assert "created_at" in submission


def test_history_filter_by_subject():
    """Test filtering history by subject."""
    headers = get_auth_headers()
    
    # Create quizzes with different subjects
    create_and_submit_quiz("Physics", "10")
    create_and_submit_quiz("Chemistry", "10")
    
    # Filter by Physics
    response = client.get("/quizzes/history?subject=Physics", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    physics_submissions = data["submissions"]
    
    # All results should be Physics
    for submission in physics_submissions:
        assert submission["subject"] == "Physics"
    
    assert data["filters_applied"]["subject"] == "Physics"


def test_history_filter_by_grade():
    """Test filtering history by grade level."""
    headers = get_auth_headers()
    
    # Create quizzes with different grades
    create_and_submit_quiz("Math", "7")
    create_and_submit_quiz("Math", "8")
    
    # Filter by grade 7
    response = client.get("/quizzes/history?grade=7", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    grade7_submissions = data["submissions"]
    
    # All results should be grade 7
    for submission in grade7_submissions:
        assert submission["grade_level"] == "7"
    
    assert data["filters_applied"]["grade"] == "7"


def test_history_filter_by_marks():
    """Test filtering history by marks range."""
    headers = get_auth_headers()
    
    # Create quizzes with different expected scores
    create_and_submit_quiz("Test_High", "8", "good")
    create_and_submit_quiz("Test_Low", "8", "poor")
    
    # Filter by high marks (80-100%)
    response = client.get("/quizzes/history?min_marks=80&max_marks=100", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["filters_applied"]["min_marks"] == "80.0"
    assert data["filters_applied"]["max_marks"] == "100.0"
    
    # Check that returned submissions have percentage in range
    for submission in data["submissions"]:
        if submission["percentage"] is not None:
            assert 80 <= submission["percentage"] <= 100


def test_history_date_parsing_iso():
    """Test date parsing with ISO format."""
    headers = get_auth_headers()
    
    # Create a submission
    create_and_submit_quiz("DateTest", "8")
    
    # Test with ISO date format
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    response = client.get(f"/quizzes/history?from_date={today}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["filters_applied"]["from_date"] == today


def test_history_date_parsing_ddmmyyyy():
    """Test date parsing with DD/MM/YYYY format."""
    headers = get_auth_headers()
    
    # Create a submission
    create_and_submit_quiz("DateTest2", "8")
    
    # Test with DD/MM/YYYY format
    today = datetime.now(timezone.utc)
    date_str = today.strftime("%d/%m/%Y")
    
    response = client.get(f"/quizzes/history?from_date={date_str}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["filters_applied"]["from_date"] == date_str


def test_history_pagination():
    """Test history pagination."""
    headers = get_auth_headers()
    
    # Create multiple submissions
    for i in range(5):
        create_and_submit_quiz(f"Subject{i}", "8")
    
    # Test first page
    response = client.get("/quizzes/history?limit=2&offset=0", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["submissions"]) <= 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert data["has_prev"] == False
    
    if data["total"] > 2:
        assert data["has_next"] == True
    
    # Test second page
    response = client.get("/quizzes/history?limit=2&offset=2", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["offset"] == 2
    assert data["has_prev"] == True


def test_history_multiple_filters():
    """Test applying multiple filters together."""
    headers = get_auth_headers()
    
    # Create specific quiz
    create_and_submit_quiz("FilterTest", "9")
    
    # Apply multiple filters
    response = client.get(
        "/quizzes/history?subject=FilterTest&grade=9&min_marks=0&max_marks=100",
        headers=headers
    )
    assert response.status_code == 200
    
    data = response.json()
    filters = data["filters_applied"]
    
    assert filters["subject"] == "FilterTest"
    assert filters["grade"] == "9"
    assert filters["min_marks"] == "0.0"
    assert filters["max_marks"] == "100.0"
    
    # Results should match all filters
    for submission in data["submissions"]:
        assert submission["subject"] == "FilterTest"
        assert submission["grade_level"] == "9"


def test_history_invalid_date_format():
    """Test that invalid date formats are handled gracefully."""
    headers = get_auth_headers()
    
    # Invalid date format should not cause error, just be ignored
    response = client.get("/quizzes/history?from_date=invalid-date", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    # Filter should not be applied for invalid date
    assert "from_date" not in data["filters_applied"]


def test_history_validation():
    """Test history parameter validation."""
    headers = get_auth_headers()
    
    # Invalid marks range
    response = client.get("/quizzes/history?min_marks=150", headers=headers)
    assert response.status_code == 422
    
    # Invalid limit
    response = client.get("/quizzes/history?limit=1000", headers=headers)
    assert response.status_code == 422
    
    # Negative offset
    response = client.get("/quizzes/history?offset=-1", headers=headers)
    assert response.status_code == 422


def test_history_empty_results():
    """Test history with filters that return no results."""
    headers = get_auth_headers()
    
    # Filter for non-existent subject
    response = client.get("/quizzes/history?subject=NonExistentSubject", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["submissions"] == []
    assert data["total"] == 0
    assert data["has_next"] == False
    assert data["has_prev"] == False


def test_history_without_authentication():
    """Test that history requires authentication."""
    response = client.get("/quizzes/history")
    assert response.status_code == 422  # Missing authorization header
