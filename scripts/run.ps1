# JARVIS OS Windows Startup Script

Write-Output "============================================================"
Write-Output "           STARTING JARVIS OS APPLICATION SUITE             "
Write-Output "============================================================"

# Check Python installation
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
    Exit
}

# Check Node installation
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js (npm) is not installed or not in PATH."
    Exit
}

# 1. Start Server in background
Write-Output "[STEP 1/2] Launching Python FastAPI Server..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd server; python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt; python main.py"

# 2. Start Dashboard in background
Write-Output "[STEP 2/2] Launching React Vite Dashboard..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd dashboard; npm install; npm run dev"

Write-Output "Services started in separate terminal windows."
Write-Output "Dashboard should be available at http://localhost:5173"
Write-Output "Server API available at http://localhost:8000"
Write-Output "============================================================"
