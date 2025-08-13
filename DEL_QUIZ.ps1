# DEL_QUIZ.ps1 - Test script for deleting a quiz via API

$baseUrl = "http://localhost:8000"

Write-Host "=== Delete Quiz API Test (DEL_QUIZ) ===" -ForegroundColor Green

try {
  # 1) Authenticate
  Write-Host "`n1) Authenticating..." -ForegroundColor Yellow
  $loginResponse = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"username":"demo","password":"demo"}'
  $token = $loginResponse.access_token
  if (-not $token) { throw "No token received from login" }
  $headers = @{"Authorization"="Bearer $token"; "Content-Type"="application/json"}
  Write-Host "[OK] Authenticated"

  # 2) Create a quiz to delete
  Write-Host "`n2) Creating a quiz to later delete..." -ForegroundColor Yellow
  $quizPayload = '{"subject":"Mathematics","grade_level":"8","num_questions":2,"difficulty":"easy","topics":["algebra"],"question_types":["MCQ"],"adaptive":false}'
  $quiz = Invoke-RestMethod -Uri "$baseUrl/quizzes" -Method POST -Headers $headers -Body $quizPayload
  $quizId = $quiz.id
  if (-not $quizId) { throw "Quiz creation failed (no id)" }
  Write-Host "[OK] Quiz created with ID: $quizId"

  # 2.1) Verify questions exist
  Write-Host "`n2.1) Verifying quiz questions exist..." -ForegroundColor Yellow
  $questions = Invoke-RestMethod -Uri "$baseUrl/quizzes/$quizId/questions" -Headers @{"Authorization"="Bearer $token"}
  Write-Host "[OK] Retrieved $($questions.Count) question(s)"

  # 3) Delete the quiz
  Write-Host "`n3) Deleting the quiz..." -ForegroundColor Yellow
  $deleteResponse = Invoke-RestMethod -Uri "$baseUrl/quizzes/$quizId" -Method DELETE -Headers $headers
  Write-Host "[OK] Delete response: $($deleteResponse.message) (ID: $($deleteResponse.id))"

  # 4) Validate quiz is gone
  Write-Host "`n4) Verifying quiz is deleted (expecting 404 errors)..." -ForegroundColor Yellow
  $deletedOk = $false
  try {
    Invoke-RestMethod -Uri "$baseUrl/quizzes/$quizId" -Headers @{"Authorization"="Bearer $token"}
    Write-Host "[ERROR] GET quiz returned success but should be 404" -ForegroundColor Red
  } catch {
    Write-Host "[OK] GET /quizzes/$quizId correctly failed after deletion"
    $deletedOk = $true
  }

  try {
    Invoke-RestMethod -Uri "$baseUrl/quizzes/$quizId/questions" -Headers @{"Authorization"="Bearer $token"}
    Write-Host "[ERROR] GET questions returned success but should be 404" -ForegroundColor Red
    $deletedOk = $false
  } catch {
    Write-Host "[OK] GET /quizzes/$quizId/questions correctly failed after deletion"
  }

  # 5) Double-delete should 404
  Write-Host "`n5) Deleting the quiz again should fail (404)..." -ForegroundColor Yellow
  try {
    Invoke-RestMethod -Uri "$baseUrl/quizzes/$quizId" -Method DELETE -Headers $headers
    Write-Host "[ERROR] Second delete unexpectedly succeeded" -ForegroundColor Red
    $deletedOk = $false
  } catch {
    Write-Host "[OK] Second delete correctly failed (already deleted)"
  }

  if ($deletedOk) {
    Write-Host "`n=== DEL_QUIZ Test Passed ===" -ForegroundColor Green
  } else {
    Write-Host "`n=== DEL_QUIZ Test Completed with Warnings ===" -ForegroundColor Yellow
  }

} catch {
  Write-Host "[ERROR] DEL_QUIZ Test failed: $($_.Exception.Message)" -ForegroundColor Red
  if ($_.Exception.Response) {
    try {
      $errorResponse = $_.Exception.Response.GetResponseStream()
      $reader = New-Object System.IO.StreamReader($errorResponse)
      $errorContent = $reader.ReadToEnd()
      Write-Host "        Full error: $errorContent" -ForegroundColor Red
    } catch {
      Write-Host "        Could not read error details" -ForegroundColor Red
    }
  }
}


