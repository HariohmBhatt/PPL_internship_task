# test-live.ps1
$base = "https://ai-quiz-microservice.onrender.com"

function Get-Json($obj) { $obj | ConvertTo-Json -Depth 6 }

try {
  Write-Host "== Health =="
  $health  = Invoke-RestMethod -Uri "$base/healthz"
  $ready   = Invoke-RestMethod -Uri "$base/readyz"
  Write-Host "healthz:" (Get-Json $health)
  Write-Host "readyz :" (Get-Json $ready)

  Write-Host "`n== Auth =="
  $loginBody = @{ username = "demo"; password = "demo" } | ConvertTo-Json
  $login = Invoke-RestMethod -Uri "$base/auth/login" -Method POST -Headers @{ "Content-Type"="application/json" } -Body $loginBody
  $token = $login.access_token
  $authH = @{ Authorization = "Bearer $token"; "Content-Type"="application/json" }
  Write-Host "token acquired"

  Write-Host "`n== Create Quiz =="
  $quizReq = @{
    subject="Mathematics"; grade_level="8"; num_questions=3; difficulty="easy"
    topics=@("algebra"); question_types=@("MCQ","TF"); adaptive=$false
  } | ConvertTo-Json -Depth 4
  $quiz = Invoke-RestMethod -Uri "$base/quizzes" -Method POST -Headers $authH -Body $quizReq
  $quizId = $quiz.id
  Write-Host "quizId:" $quizId

  Write-Host "`n== Get Questions =="
  $questions = Invoke-RestMethod -Uri "$base/quizzes/$quizId/questions" -Headers @{ Authorization = "Bearer $token" }
  Write-Host "questions:" $questions.Count

  Write-Host "`n== Hint =="
  $firstQ = $questions[0].id
  $hint = Invoke-RestMethod -Uri "$base/quizzes/$quizId/questions/$firstQ/hint" -Method POST -Headers $authH -Body "{}"
  Write-Host "hint:" $hint.hint

  Write-Host "`n== Submit Quiz =="
  $answers = @()
  foreach ($q in $questions) {
    $sel = if ($q.options -and $q.options.Count -gt 0) { $q.options[0] } else { "True" }
    $answers += @{ question_id = $q.id; selected_option = $sel; time_spent_seconds = 10 }
  }
  $submitBody = @{ answers = $answers; time_taken_minutes = 1 } | ConvertTo-Json -Depth 5
  $result = Invoke-RestMethod -Uri "$base/quizzes/$quizId/submit" -Method POST -Headers $authH -Body $submitBody
  Write-Host "score:" $([math]::Round($result.percentage,1)) "%"

  Write-Host "`n== Retry Quiz =="
  $retry = Invoke-RestMethod -Uri "$base/quizzes/$quizId/retry" -Method POST -Headers $authH -Body (@{reason="test"} | ConvertTo-Json)
  Write-Host "new_quiz_id:" $retry.new_quiz_id "retry_number:" $retry.retry_number

  Write-Host "`n== History =="
  $history = Invoke-RestMethod -Uri "$base/quiz-history" -Headers @{ Authorization = "Bearer $token" }
  Write-Host "history total:" $history.total

  Write-Host "`n== Leaderboard =="
  $lb = Invoke-RestMethod -Uri "$base/leaderboard?subject=Mathematics&grade_level=8&limit=5" -Headers @{ Authorization = "Bearer $token" }
  Write-Host "lb total users:" $lb.total_users
  $myRank = Invoke-RestMethod -Uri "$base/leaderboard/my-rank?subject=Mathematics&grade_level=8" -Headers @{ Authorization = "Bearer $token" }
  Write-Host "my rank:" $myRank.current_rank "of" $myRank.total_participants

  Write-Host "`nAll tests done."
}
catch {
  Write-Host "ERROR:" $_.Exception.Message -ForegroundColor Red
  if ($_.Exception.Response) {
    try {
      $rs = $_.Exception.Response.GetResponseStream()
      $rd = New-Object System.IO.StreamReader($rs)
      $body = $rd.ReadToEnd()
      Write-Host "Details: $body" -ForegroundColor Red
    } catch {}
  }
  exit 1
}