# Uruchamia backend i frontend w osobnych oknach PowerShell

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
  Set-Location '$root\backend'
  if (-not (Test-Path .venv)) {
    python -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt
  }
  .\.venv\Scripts\uvicorn main:app --reload --port 8000
"

# Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
  Set-Location '$root\frontend'
  if (-not (Test-Path node_modules)) { npm install }
  npm run dev
"

Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
