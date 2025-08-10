"""Submission and evaluation tests."""

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
    """Helper to create a test quiz and return quiz_id and questions."""
    headers = get_auth_headers()
    
    quiz_data = {
        "subject": "Mathematics",
        "grade_level": "8",
        "num_questions": 4,
        "difficulty": "medium",
        "topics": ["algebra", "geometry"],
        "question_types": ["MCQ", "TF", "short_answer"]
    }
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    quiz_id = response.json()["id"]
    
    # Get questions
    questions_response = client.get(f"/quizzes/{quiz_id}/questions", headers=headers)
    questions = questions_response.json()
    
    return quiz_id, questions


def test_submit_quiz_success():
    """Test successful quiz submission and evaluation."""
    headers = get_auth_headers()
    quiz_id, questions = create_test_quiz()
    
    # Prepare answers for all questions
    answers = []
    for question in questions:
        if question["question_type"] == "MCQ":
            # Select first option
            answers.append({
                "question_id": question["id"],
                "selected_option": question["options"][0] if question["options"] else "Option A",
                "time_spent_seconds": 30
            })
        elif question["question_type"] == "TF":
            answers.append({
                "question_id": question["id"],
                "selected_option": "True",
                "time_spent_seconds": 15
            })
        else:  # short_answer
            answers.append({
                "question_id": question["id"],
                "answer_text": "This is my answer explaining the mathematical concept in detail.",
                "time_spent_seconds": 60
            })
    
    submission_data = {
        "answers": answers,
        "time_taken_minutes": 10
    }
    
    response = client.post(
        f"/quizzes/{quiz_id}/submit",
        json=submission_data,
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check evaluation structure
    assert "submission_id" in data
    assert "quiz_id" in data
    assert data["quiz_id"] == quiz_id
    assert "total_score" in data
    assert "max_possible_score" in data
    assert "percentage" in data
    assert "correct_answers" in data
    assert "total_questions" in data
    assert data["total_questions"] == len(questions)
    assert "performance_level" in data
    assert "answers" in data
    assert len(data["answers"]) == len(questions)
    
    # Check per-question breakdown
    for answer_eval in data["answers"]:
        assert "question_id" in answer_eval
        assert "points_earned" in answer_eval
        assert "max_points" in answer_eval
        assert "is_correct" in answer_eval
    
    # Check exactly 2 suggestions as per requirements
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) == 2
    
    # Check timing
    assert data["time_taken_minutes"] == 10


def test_submit_quiz_deterministic_grading():
    """Test that submission grading is deterministic under MockProvider."""
    headers = get_auth_headers()
    quiz_id, questions = create_test_quiz()
    
    # Submit same answers twice
    answers = [{
        "question_id": questions[0]["id"],
        "answer_text": "Test answer for deterministic grading",
        "time_spent_seconds": 30
    }]
    
    submission_data = {"answers": answers}
    
    # First submission
    response1 = client.post(f"/quizzes/{quiz_id}/submit", json=submission_data, headers=headers)
    
    # Create new quiz for second submission (to avoid submission conflicts)
    quiz_id2, questions2 = create_test_quiz()
    answers2 = [{
        "question_id": questions2[0]["id"],
        "answer_text": "Test answer for deterministic grading",
        "time_spent_seconds": 30
    }]
    submission_data2 = {"answers": answers2}
    
    response2 = client.post(f"/quizzes/{quiz_id2}/submit", json=submission_data2, headers=headers)
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Should get same score for same answer (deterministic AI grading)
    eval1 = response1.json()
    eval2 = response2.json()
    
    assert eval1["answers"][0]["points_earned"] == eval2["answers"][0]["points_earned"]


def test_submit_quiz_mcq_grading():
    """Test MCQ and TF question grading logic."""
    headers = get_auth_headers()
    
    # Create quiz with only MCQ/TF questions for predictable grading
    quiz_data = {
        "subject": "Test",
        "grade_level": "8",
        "num_questions": 2,
        "difficulty": "easy",
        "topics": ["test"],
        "question_types": ["MCQ", "TF"]
    }
    
    response = client.post("/quizzes", json=quiz_data, headers=headers)
    quiz_id = response.json()["id"]
    
    questions_response = client.get(f"/quizzes/{quiz_id}/questions", headers=headers)
    questions = questions_response.json()
    
    # Submit answers
    answers = []
    for question in questions:
        if question["question_type"] == "MCQ":
            # Select first option (may or may not be correct)
            answers.append({
                "question_id": question["id"],
                "selected_option": question["options"][0]
            })
        elif question["question_type"] == "TF":
            answers.append({
                "question_id": question["id"],
                "selected_option": "True"
            })
    
    submission_data = {"answers": answers}
    
    response = client.post(f"/quizzes/{quiz_id}/submit", json=submission_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    
    # Check that objective questions have is_correct boolean
    for answer_eval in data["answers"]:
        assert isinstance(answer_eval["is_correct"], bool)
        # Objective questions should have full or zero points
        assert answer_eval["points_earned"] in [0, answer_eval["max_points"]]


def test_submit_quiz_validation():
    """Test submission validation."""
    headers = get_auth_headers()
    quiz_id, questions = create_test_quiz()
    
    # Empty answers
    response = client.post(f"/quizzes/{quiz_id}/submit", json={"answers": []}, headers=headers)
    assert response.status_code == 422
    
    # Invalid question ID
    invalid_answers = [{
        "question_id": 99999,
        "answer_text": "test"
    }]
    response = client.post(f"/quizzes/{quiz_id}/submit", json={"answers": invalid_answers}, headers=headers)
    assert response.status_code == 422
    
    # Missing answer content
    missing_content = [{
        "question_id": questions[0]["id"]
        # No answer_text or selected_option
    }]
    response = client.post(f"/quizzes/{quiz_id}/submit", json={"answers": missing_content}, headers=headers)
    assert response.status_code == 422


def test_submit_nonexistent_quiz():
    """Test submitting to nonexistent quiz."""
    headers = get_auth_headers()
    
    answers = [{
        "question_id": 1,
        "answer_text": "test"
    }]
    
    response = client.post("/quizzes/99999/submit", json={"answers": answers}, headers=headers)
    assert response.status_code == 404


def test_evaluation_performance_categories():
    """Test evaluation includes performance by type and difficulty."""
    headers = get_auth_headers()
    quiz_id, questions = create_test_quiz()
    
    # Submit answers
    answers = []
    for question in questions:
        if question["question_type"] in ["MCQ", "TF"]:
            answers.append({
                "question_id": question["id"],
                "selected_option": question["options"][0] if question["options"] else "True"
            })
        else:
            answers.append({
                "question_id": question["id"],
                "answer_text": "Good answer with proper explanation and details."
            })
    
    submission_data = {"answers": answers}
    
    response = client.post(f"/quizzes/{quiz_id}/submit", json=submission_data, headers=headers)
    data = response.json()
    
    # Should have performance breakdowns
    assert "mcq_score" in data
    assert "tf_score" in data
    assert "short_answer_score" in data
    assert "easy_score" in data
    assert "medium_score" in data
    assert "hard_score" in data
    assert "topic_scores" in data
    
    # Should have AI-generated feedback
    assert "strengths" in data
    assert "weaknesses" in data
    assert isinstance(data["strengths"], list)
    assert isinstance(data["weaknesses"], list)


def test_submit_without_authentication():
    """Test that submission requires authentication."""
    quiz_id, questions = create_test_quiz()
    
    answers = [{
        "question_id": questions[0]["id"],
        "answer_text": "test"
    }]
    
    response = client.post(f"/quizzes/{quiz_id}/submit", json={"answers": answers})
    assert response.status_code == 422  # Missing authorization header
