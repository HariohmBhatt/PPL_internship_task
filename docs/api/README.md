# API Documentation

Detailed documentation for all API endpoints in the AI Quiz Service.

## Table of Contents

- [Authentication](#authentication)
- [Quiz Management](#quiz-management)
- [Quiz History](#quiz-history)
- [AI Features](#ai-features)
- [Quiz Retry](#quiz-retry)

## Authentication

### Login

Authenticate a user and receive a JWT token.

```http
POST /auth/login
```

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Invalid credentials

### Register (Development Only)

Register a new user account.

```http
POST /auth/register
```

**Request Body:**
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "string",
  "email": "user@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Status Codes:**
- `201 Created` - Success
- `409 Conflict` - Username/email already exists

## Quiz Management

### Create Quiz

Create a new quiz with AI-generated questions.

```http
POST /quizzes
```

**Request Body:**
```json
{
  "subject": "Mathematics",
  "grade_level": "8",
  "num_questions": 5,
  "difficulty": "medium",
  "topics": ["algebra", "geometry"],
  "question_types": ["MCQ", "TF", "short_answer"],
  "standard": "Common Core",
  "adaptive": false
}
```

**Response:**
```json
{
  "id": 1,
  "title": "Mathematics - 8 Quiz",
  "subject": "Mathematics",
  "grade_level": "8",
  "questions": [
    {
      "id": 1,
      "question_text": "What is the main concept of algebra?",
      "question_type": "MCQ",
      "difficulty": "medium",
      "topic": "algebra",
      "order": 1,
      "points": 2,
      "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "hint_text": "Think about variables and equations."
    }
  ],
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Status Codes:**
- `201 Created` - Success
- `400 Bad Request` - Invalid input
- `500 Internal Server Error` - Failed to generate questions

### Get Quiz Questions

Get questions for a specific quiz.

```http
GET /quizzes/{quiz_id}/questions
```

**Response:**
```json
[
  {
    "id": 1,
    "question_text": "What is the main concept of algebra?",
    "question_type": "MCQ",
    "difficulty": "medium",
    "topic": "algebra",
    "order": 1,
    "points": 2,
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "hint_text": "Think about variables and equations."
  }
]
```

### Submit Quiz

Submit answers and get evaluation.

```http
POST /quizzes/{quiz_id}/submit
```

**Request Body:**
```json
{
  "answers": [
    {
      "question_id": 1,
      "selected_option": "Option A",
      "time_spent_seconds": 30
    },
    {
      "question_id": 2,
      "answer_text": "This is my detailed answer",
      "time_spent_seconds": 120
    }
  ],
  "time_taken_minutes": 15
}
```

**Response:**
```json
{
  "submission_id": 1,
  "quiz_id": 1,
  "total_score": 8.5,
  "max_possible_score": 10.0,
  "percentage": 85.0,
  "correct_answers": 4,
  "total_questions": 5,
  "performance_level": "excellent",
  "answers": [
    {
      "question_id": 1,
      "is_correct": true,
      "points_earned": 2.0,
      "max_points": 2.0,
      "ai_feedback": "Good understanding shown",
      "confidence_score": 0.95
    }
  ],
  "mcq_score": 90.0,
  "tf_score": 80.0,
  "topic_scores": {
    "algebra": 85.0
  },
  "suggestions": [
    "Review fundamental concepts",
    "Practice more complex problems"
  ],
  "strengths": [
    "Strong understanding of basic concepts"
  ],
  "weaknesses": [
    "Need improvement in advanced topics"
  ],
  "time_taken_minutes": 15,
  "submitted_at": "2024-01-01T00:15:00Z"
}
```

## Quiz History

### Get Quiz History

Get user's quiz history with optional filters.

```http
GET /quiz-history
```

**Query Parameters:**
- `subject` (string) - Filter by subject
- `grade` (string) - Filter by grade level
- `min_marks` (number) - Minimum percentage score
- `max_marks` (number) - Maximum percentage score
- `from_date` (string) - Start date (DD/MM/YYYY)
- `to_date` (string) - End date (DD/MM/YYYY)
- `completed_date` (string) - Specific completion date

**Response:**
```json
{
  "total": 10,
  "filters_applied": {
    "subject": "Mathematics",
    "min_marks": 70,
    "max_marks": 100
  },
  "submissions": [
    {
      "quiz_id": 1,
      "quiz_title": "Mathematics - 8 Quiz",
      "subject": "Mathematics",
      "grade_level": "8",
      "percentage": 85.0,
      "completed_at": "2024-01-01T00:15:00Z"
    }
  ]
}
```

## AI Features

### Get Hint

Get AI-generated hint for a question.

```http
POST /quizzes/{quiz_id}/questions/{question_id}/hint
```

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "hint": "Think about the relationship between variables in an equation.",
  "usage_count": 1,
  "max_hints": 3,
  "remaining_hints": 2
}
```

**Status Codes:**
- `200 OK` - Success
- `429 Too Many Requests` - Hint limit exceeded

### Get Adaptive Status

Get current adaptive quiz status.

```http
GET /quizzes/{quiz_id}/adaptive-status
```

**Response:**
```json
{
  "current_difficulty": "medium",
  "questions_answered": 3,
  "total_questions": 5,
  "performance_trend": "improving",
  "next_question_difficulty": "hard"
}
```

## Quiz Retry

### Create Quiz Retry

Create a retry attempt for a quiz.

```http
POST /quizzes/{quiz_id}/retry
```

**Request Body:**
```json
{
  "reason": "Want to improve my score"
}
```

**Response:**
```json
{
  "original_quiz_id": 1,
  "retried_quiz_id": 2,
  "retry_number": 1,
  "reason": "Want to improve my score",
  "created_at": "2024-01-01T01:00:00Z"
}
```

## Common Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Headers

All authenticated endpoints require:
```http
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

## Rate Limiting

- Hints: 3 per question
- Submissions: 10 per quiz

Rate limit headers in responses:
```http
X-RateLimit-Limit: 3
X-RateLimit-Remaining: 2
X-RateLimit-Reset: 1704067200
```
