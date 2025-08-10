# API Usage Examples

This document provides practical examples of using the AI Quiz Service API.

## Table of Contents

1. [Complete Quiz Flow](#complete-quiz-flow)
2. [Working with Adaptive Quizzes](#working-with-adaptive-quizzes)
3. [Using AI Hints](#using-ai-hints)
4. [Filtering Quiz History](#filtering-quiz-history)
5. [Quiz Retry Flow](#quiz-retry-flow)

## Complete Quiz Flow

### 1. Authentication

```javascript
// Login and get token
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'student123',
    password: 'password123'
  })
});

const { access_token } = await loginResponse.json();
const headers = {
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
};
```

### 2. Create Quiz

```javascript
// Create a new quiz
const quizResponse = await fetch('http://localhost:8000/quizzes', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    subject: 'Mathematics',
    grade_level: '8',
    num_questions: 5,
    difficulty: 'medium',
    topics: ['algebra'],
    question_types: ['MCQ', 'TF'],
    adaptive: false
  })
});

const quiz = await quizResponse.json();
console.log('Quiz created:', quiz.id);
```

### 3. Get Questions

```javascript
// Get quiz questions
const questionsResponse = await fetch(`http://localhost:8000/quizzes/${quiz.id}/questions`, {
  headers
});

const questions = await questionsResponse.json();
console.log('Questions:', questions);
```

### 4. Submit Answers

```javascript
// Submit quiz answers
const submitResponse = await fetch(`http://localhost:8000/quizzes/${quiz.id}/submit`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    answers: [
      {
        question_id: questions[0].id,
        selected_option: 'Option A',
        time_spent_seconds: 30
      },
      {
        question_id: questions[1].id,
        selected_option: 'Option B',
        time_spent_seconds: 45
      }
    ],
    time_taken_minutes: 5
  })
});

const result = await submitResponse.json();
console.log('Score:', result.percentage);
console.log('Suggestions:', result.suggestions);
```

## Working with Adaptive Quizzes

### 1. Create Adaptive Quiz

```javascript
// Create adaptive quiz
const adaptiveQuizResponse = await fetch('http://localhost:8000/quizzes', {
  method: 'POST',
  headers,
  body: JSON.stringify({
    subject: 'Science',
    grade_level: '10',
    num_questions: 8,
    difficulty: 'adaptive',
    topics: ['physics'],
    question_types: ['MCQ', 'TF'],
    adaptive: true
  })
});

const adaptiveQuiz = await adaptiveQuizResponse.json();
```

### 2. Get Adaptive Status

```javascript
// Check adaptive status
const statusResponse = await fetch(`http://localhost:8000/quizzes/${adaptiveQuiz.id}/adaptive-status`, {
  headers
});

const status = await statusResponse.json();
console.log('Current difficulty:', status.current_difficulty);
console.log('Progress:', `${status.questions_answered}/${status.total_questions}`);
```

### 3. Submit and Track Progress

```javascript
// Submit answer and check new difficulty
const submitAdaptiveResponse = await fetch(`http://localhost:8000/quizzes/${adaptiveQuiz.id}/submit`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    answers: [
      {
        question_id: questions[0].id,
        selected_option: 'Option A',
        time_spent_seconds: 30
      }
    ],
    time_taken_minutes: 1
  })
});

const adaptiveResult = await submitAdaptiveResponse.json();
console.log('New difficulty:', adaptiveResult.next_question_difficulty);
```

## Using AI Hints

### 1. Request Hint

```javascript
// Get hint for a question
const hintResponse = await fetch(`http://localhost:8000/quizzes/${quiz.id}/questions/${questions[0].id}/hint`, {
  method: 'POST',
  headers,
  body: JSON.stringify({})
});

const hint = await hintResponse.json();
console.log('Hint:', hint.hint);
console.log('Hints remaining:', hint.remaining_hints);
```

### 2. Handle Rate Limiting

```javascript
// Example of handling rate limits
async function getHint(quizId, questionId) {
  try {
    const response = await fetch(`http://localhost:8000/quizzes/${quizId}/questions/${questionId}/hint`, {
      method: 'POST',
      headers,
      body: JSON.stringify({})
    });
    
    if (response.status === 429) {
      console.log('Hint limit reached for this question');
      return null;
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error getting hint:', error);
    return null;
  }
}
```

## Filtering Quiz History

### 1. Basic Filtering

```javascript
// Get history with filters
const historyResponse = await fetch(
  'http://localhost:8000/quiz-history?subject=Mathematics&grade=8&min_marks=70&max_marks=100',
  { headers }
);

const history = await historyResponse.json();
console.log('Filtered results:', history.total);
```

### 2. Date Range Filtering

```javascript
// Filter by date range
const dateFilterResponse = await fetch(
  'http://localhost:8000/quiz-history?from_date=01/01/2024&to_date=31/12/2024',
  { headers }
);

const dateFilteredHistory = await dateFilterResponse.json();
```

### 3. Combined Filters

```javascript
// Complex filtering
const url = new URL('http://localhost:8000/quiz-history');
const params = {
  subject: 'Mathematics',
  grade: '8',
  min_marks: '70',
  max_marks: '100',
  from_date: '01/01/2024',
  to_date: '31/12/2024'
};
url.search = new URLSearchParams(params).toString();

const complexFilterResponse = await fetch(url, { headers });
const complexFilteredHistory = await complexFilterResponse.json();
```

## Quiz Retry Flow

### 1. Create Retry

```javascript
// Create quiz retry
const retryResponse = await fetch(`http://localhost:8000/quizzes/${quiz.id}/retry`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    reason: 'Want to improve my score'
  })
});

const retry = await retryResponse.json();
console.log('Retry quiz ID:', retry.retried_quiz_id);
```

### 2. Compare Performances

```javascript
// Get both quiz results
async function compareQuizzes(originalId, retryId) {
  const [originalHistory, retryHistory] = await Promise.all([
    fetch(`http://localhost:8000/quiz-history?quiz_id=${originalId}`, { headers }),
    fetch(`http://localhost:8000/quiz-history?quiz_id=${retryId}`, { headers })
  ]);
  
  const original = await originalHistory.json();
  const retry = await retryHistory.json();
  
  console.log('Original score:', original.submissions[0].percentage);
  console.log('Retry score:', retry.submissions[0].percentage);
  console.log('Improvement:', retry.submissions[0].percentage - original.submissions[0].percentage);
}
```

## Error Handling

```javascript
async function safeApiCall(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${getToken()}`
      }
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        // Token expired
        redirectToLogin();
        return;
      }
      
      if (response.status === 429) {
        // Rate limited
        const resetTime = response.headers.get('X-RateLimit-Reset');
        throw new Error(`Rate limited. Try again after ${new Date(resetTime * 1000)}`);
      }
      
      const error = await response.json();
      throw new Error(error.error.message);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

## Frontend Integration Tips

1. **Token Management**
   ```javascript
   // Store token
   function setToken(token) {
     sessionStorage.setItem('quiz_token', token);
   }
   
   // Get token
   function getToken() {
     return sessionStorage.getItem('quiz_token');
   }
   
   // Clear token
   function logout() {
     sessionStorage.removeItem('quiz_token');
     window.location.href = '/login';
   }
   ```

2. **API Client**
   ```javascript
   class QuizApi {
     constructor(baseUrl) {
       this.baseUrl = baseUrl;
     }
     
     async request(endpoint, options = {}) {
       const url = `${this.baseUrl}${endpoint}`;
       return safeApiCall(url, options);
     }
     
     async createQuiz(data) {
       return this.request('/quizzes', {
         method: 'POST',
         body: JSON.stringify(data)
       });
     }
     
     // Add other API methods...
   }
   ```

3. **Real-time Updates**
   ```javascript
   // Poll adaptive status
   function pollAdaptiveStatus(quizId) {
     const interval = setInterval(async () => {
       const status = await getAdaptiveStatus(quizId);
       if (status.questions_answered === status.total_questions) {
         clearInterval(interval);
       }
       updateUI(status);
     }, 5000);
   }
   ```

4. **Progress Tracking**
   ```javascript
   // Track quiz progress
   class QuizProgress {
     constructor(quizId, totalQuestions) {
       this.quizId = quizId;
       this.totalQuestions = totalQuestions;
       this.answers = new Map();
       this.startTime = Date.now();
     }
     
     addAnswer(questionId, answer, timeSpent) {
       this.answers.set(questionId, { answer, timeSpent });
     }
     
     async submit() {
       const timeTaken = Math.round((Date.now() - this.startTime) / 60000);
       const answers = Array.from(this.answers.entries()).map(([id, data]) => ({
         question_id: id,
         ...data
       }));
       
       return submitQuiz(this.quizId, { answers, time_taken_minutes: timeTaken });
     }
   }
   ```
