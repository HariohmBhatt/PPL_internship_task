# Authentication Guide

This guide explains how authentication works in the AI Quiz Service.

## Overview

The service uses JWT (JSON Web Token) based authentication. Each token is valid for 24 hours (configurable) and must be included in the `Authorization` header for all protected endpoints.

## Authentication Flow

1. **User Login**
   ```mermaid
   sequenceDiagram
       participant Client
       participant Server
       participant JWT
       Client->>Server: POST /auth/login
       Server->>JWT: Create token
       JWT-->>Server: Signed token
       Server-->>Client: Return token
   ```

2. **Using the Token**
   ```mermaid
   sequenceDiagram
       participant Client
       participant Server
       participant JWT
       Client->>Server: Request with Bearer token
       Server->>JWT: Verify token
       JWT-->>Server: Token valid
       Server-->>Client: Protected resource
   ```

## Implementation Details

### 1. Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "student123",
  "password": "password123"
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

### 2. Using the Token

Include the token in all subsequent requests:

```http
GET /protected-endpoint
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 3. Token Structure

The JWT token contains:

```json
{
  "sub": "1",           // User ID
  "username": "user123", // Username
  "exp": 1704067200,    // Expiration timestamp
  "iat": 1703980800     // Issued at timestamp
}
```

## Development Mode

In development mode (`ENV=dev`), the service accepts any username/password combination and creates a mock user with ID 1. This is useful for testing but should never be used in production.

## Error Handling

Common authentication errors:

1. **Invalid Token**
   ```json
   {
     "error": {
       "code": "INVALID_TOKEN",
       "message": "Token is invalid or expired"
     }
   }
   ```

2. **Missing Token**
   ```json
   {
     "error": {
       "code": "MISSING_TOKEN",
       "message": "Authentication token is required"
     }
   }
   ```

3. **Invalid Credentials**
   ```json
   {
     "error": {
       "code": "INVALID_CREDENTIALS",
       "message": "Invalid username or password"
     }
   }
   ```

## Security Best Practices

1. **Token Storage**
   - Store tokens securely (e.g., HttpOnly cookies)
   - Never store in localStorage due to XSS risks

2. **Token Refresh**
   - Implement token refresh before expiration
   - Clear expired tokens

3. **HTTPS**
   - Always use HTTPS in production
   - Never send credentials over HTTP

## Example Implementation

### Frontend (JavaScript)

```javascript
// Login
async function login(username, password) {
  const response = await fetch('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  if (response.ok) {
    // Store token securely
    setAuthToken(data.access_token);
    return data;
  }
  throw new Error(data.error.message);
}

// Using the token
async function fetchProtectedResource() {
  const token = getAuthToken();
  const response = await fetch('/protected-endpoint', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
}
```

### Error Handling

```javascript
async function handleApiRequest() {
  try {
    const response = await fetchProtectedResource();
    // Handle success
  } catch (error) {
    if (error.status === 401) {
      // Token expired or invalid
      redirectToLogin();
    } else {
      // Handle other errors
      showError(error.message);
    }
  }
}
```

## Configuration

Environment variables for authentication:

```env
# JWT Configuration
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440  # 24 hours

# Environment
ENV=dev  # or 'prod' for production
```

## Testing Authentication

Use the provided Postman collection for testing:

1. **Login Test**
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"test","password":"test"}'
   ```

2. **Protected Endpoint Test**
   ```bash
   curl -X GET http://localhost:8000/protected-endpoint \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

## Troubleshooting

1. **Token Expired**
   - Check token expiration time
   - Implement automatic token refresh
   - Clear expired tokens from storage

2. **Invalid Token Format**
   - Ensure proper Bearer prefix
   - Verify token is properly encoded
   - Check for token tampering

3. **Development Mode Issues**
   - Verify ENV=dev is set
   - Check if mock authentication is enabled
   - Verify database connection for user lookup
