# AI Quiz Microservice

A production-ready FastAPI microservice for AI-powered quiz generation, evaluation, and adaptive learning. Built with Python 3.11, PostgreSQL, and comprehensive testing.

## Features

- 🤖 **AI-Powered Quiz Generation**: Automatically generates questions using configurable AI providers
- 📊 **Intelligent Evaluation**: AI-based grading for subjective questions with detailed feedback
- 🎯 **Adaptive Learning**: Dynamic difficulty adjustment based on student performance
- 📈 **Comprehensive Analytics**: Detailed performance tracking and improvement suggestions
- 🔒 **Secure Authentication**: JWT-based authentication with proper authorization
- 🌐 **RESTful API**: Clean, well-documented API with OpenAPI/Swagger docs
- 📦 **Production Ready**: Docker support, health checks, structured logging, and CI/CD

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker and Docker Compose (optional)

### Local Development Setup

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd ai-quiz-microservice
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   make install
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start database and run migrations**:
   ```bash
   # Start PostgreSQL (adjust connection details in .env)
   make migrate
   ```

5. **Start development server**:
   ```bash
   make dev
   ```

6. **Verify installation**:
   ```bash
   curl http://localhost:8000/healthz
   # Should return: {"status": "healthy", "service": "ai-quiz-microservice"}
   ```

### Docker Compose Setup

For the fastest setup with all services:

```bash
# Copy environment file
cp .env.example .env

# Start all services
make up

# Wait for services to be ready
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz

# View logs
make logs

# Stop services
make down
```

## API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

#### Authentication
```bash
# Login (accepts any username/password in development)
POST /auth/login
{
  "username": "demo_user",
  "password": "demo_password"
}
```

#### Quiz Management
```bash
# Create a quiz
POST /quizzes
Authorization: Bearer <token>
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

# Get quiz questions
GET /quizzes/{quiz_id}/questions

# Submit quiz answers
POST /quizzes/{quiz_id}/submit
{
  "answers": [
    {
      "question_id": 1,
      "selected_option": "Option A",
      "time_spent_seconds": 30
    }
  ],
  "time_taken_minutes": 15
}
```

#### Hints and Adaptive Features
```bash
# Get a hint
POST /quizzes/{quiz_id}/questions/{question_id}/hint

# Get next question (adaptive quizzes)
POST /quizzes/{quiz_id}/next

# Get quiz history with filters
GET /quizzes/history?subject=Math&grade=8&min_marks=60
```

## Development

### Available Commands

```bash
make install       # Install dependencies and setup pre-commit
make dev          # Run development server with auto-reload
make lint         # Run ruff linter
make format       # Format code with black and ruff
make type         # Run mypy type checking
make test         # Run tests with coverage
make migrate      # Run database migrations
make new-migration MESSAGE="description"  # Create new migration
make run          # Run production server
make up           # Start services with docker-compose
make down         # Stop docker-compose services
make logs         # Show docker-compose logs
make clean        # Clean cache and build artifacts
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_quiz_generation.py

# Run tests with coverage report
pytest --cov=app --cov-report=html
```

### Database Migrations

```bash
# Create a new migration
make new-migration MESSAGE="add user preferences table"

# Apply migrations
make migrate

# Check migration status
alembic current
alembic history
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET` | Secret key for JWT tokens | Required |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | localhost:3000,localhost:8000 |
| `OPENAI_API_KEY` | OpenAI API key (optional) | "" |
| `ENV` | Environment (dev/test/prod) | dev |
| `LOG_LEVEL` | Logging level | INFO |

### AI Providers

The service supports multiple AI providers:

- **MockProvider** (default): Deterministic fake content for development/testing
- **OpenAIProvider**: Real AI using OpenAI API (requires `OPENAI_API_KEY`)

### Rate Limiting

- **Hints**: 3 hints per user per question
- **Submissions**: 10 submissions per quiz per user

## Architecture

### Project Structure

```
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API route handlers
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── quizzes.py      # Quiz management
│   │   ├── hints.py        # Hint generation
│   │   ├── history.py      # Quiz history and filtering
│   │   ├── adaptive.py     # Adaptive quiz features
│   │   └── health.py       # Health check endpoints
│   ├── core/               # Core application logic
│   │   ├── config.py       # Configuration management
│   │   ├── security.py     # JWT and password utilities
│   │   ├── logging.py      # Structured logging setup
│   │   ├── deps.py         # FastAPI dependencies
│   │   └── errors.py       # Custom exception classes
│   ├── models/             # SQLAlchemy database models
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic services
│   │   ├── ai/            # AI provider implementations
│   │   ├── grading.py     # Quiz grading logic
│   │   ├── adaptive.py    # Adaptive learning algorithms
│   │   └── datetime.py    # Date/time utilities
│   └── db/                # Database configuration and migrations
├── tests/                 # Comprehensive test suite
├── .postman/             # Postman collection
├── .github/workflows/    # CI/CD workflows
└── scripts/              # Setup and utility scripts
```

### Key Features

#### AI-Powered Question Generation
- Configurable topics, difficulty levels, and question types
- Deterministic MockProvider for consistent testing
- OpenAI integration for production use
- Template-based prompting with validation

#### Intelligent Grading
- Rule-based grading for MCQ/True-False questions
- AI-based evaluation for subjective responses
- Detailed feedback and confidence scoring
- Performance analysis by topic and difficulty

#### Adaptive Learning
- Rolling window performance analysis (last 3 answers)
- Dynamic difficulty adjustment (step up/down/hold)
- Configurable adaptation thresholds
- Progress tracking and completion detection

#### Comprehensive Analytics
- Performance breakdown by question type and difficulty
- Topic-wise scoring analysis
- AI-generated improvement suggestions
- Historical trends and filtering

## Testing

### Test Coverage

The project maintains 80%+ test coverage across:

- **Health endpoints**: Basic health and readiness checks
- **Authentication**: JWT token validation and security
- **Quiz generation**: AI integration and deterministic behavior
- **Hint policy**: Rate limiting and content validation
- **Submission evaluation**: Grading accuracy and feedback
- **History filtering**: Date parsing and pagination
- **Adaptive policy**: Difficulty adjustment boundaries

### Test Environment

Tests use:
- In-memory SQLite for fast execution
- MockProvider for deterministic AI responses
- Pytest fixtures for data setup
- Comprehensive assertion patterns

## Deployment

### Docker Production Deployment

```bash
# Build production image
docker build -t ai-quiz-microservice .

# Run with environment variables
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e JWT_SECRET="your-secret-key" \
  ai-quiz-microservice
```

### Health Monitoring

The service provides comprehensive health endpoints:

- `GET /healthz`: Basic health check (always returns 200)
- `GET /readyz`: Readiness check with database connectivity

### Observability

- **Structured Logging**: JSON formatted logs with request IDs
- **Error Tracking**: Comprehensive error handling and reporting
- **Performance Monitoring**: Request timing and database query metrics
- **Security Logging**: Redacted sensitive information

## API Examples

### Complete Workflow Example

```bash
# 1. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "student1", "password": "password123"}'

# Response: {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 86400}

# 2. Create a quiz
curl -X POST http://localhost:8000/quizzes \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Physics",
    "grade_level": "10",
    "num_questions": 3,
    "difficulty": "medium",
    "topics": ["mechanics", "thermodynamics"],
    "question_types": ["MCQ", "short_answer"]
  }'

# 3. Get quiz questions
curl -X GET http://localhost:8000/quizzes/1/questions \
  -H "Authorization: Bearer eyJ..."

# 4. Get a hint
curl -X POST http://localhost:8000/quizzes/1/questions/1/hint \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{}'

# 5. Submit answers
curl -X POST http://localhost:8000/quizzes/1/submit \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {
        "question_id": 1,
        "selected_option": "Newton'\''s First Law"
      },
      {
        "question_id": 2,
        "answer_text": "Heat transfer occurs through conduction, convection, and radiation..."
      }
    ],
    "time_taken_minutes": 20
  }'

# 6. View history
curl -X GET "http://localhost:8000/quizzes/history?subject=Physics&min_marks=70" \
  -H "Authorization: Bearer eyJ..."
```

## Postman Collection

Import the provided Postman collection from `.postman/quiz-service.postman_collection.json`:

1. Open Postman
2. Import → Upload Files → Select the collection file
3. Set the `base_url` variable to your server URL
4. Run the "Login" request to automatically set the JWT token
5. Explore all available endpoints with sample data

## Contributing

1. **Setup development environment**:
   ```bash
   make install
   pre-commit install
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes and test**:
   ```bash
   make lint
   make type
   make test
   ```

4. **Commit with conventional commits**:
   ```bash
   git commit -m "feat: add new quiz analytics endpoint"
   ```

5. **Push and create pull request**

### Code Quality Standards

- **Linting**: Ruff for fast Python linting
- **Formatting**: Black for consistent code style
- **Type Checking**: MyPy for static type analysis
- **Testing**: Pytest with 80%+ coverage requirement
- **Documentation**: Comprehensive docstrings and API docs

## License

[MIT License](LICENSE)

## Support

For questions or issues:

1. Check the [API Documentation](http://localhost:8000/docs)
2. Review the test cases for usage examples
3. Examine the Postman collection for request formats
4. Open an issue for bugs or feature requests

---

**Built with ❤️ using FastAPI, SQLAlchemy, and modern Python practices.**
