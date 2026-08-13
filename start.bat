@echo off
echo ============================================================
echo           STARTING JARVIS OS APPLICATION SUITE             
echo ============================================================

echo [STEP 1/2] Launching Python FastAPI Server...
start "JARVIS Server" /D server .venv\Scripts\python.exe main.py

echo [STEP 2/2] Launching React Vite Dashboard...
start "JARVIS Dashboard" /D dashboard npm.cmd run dev -- --host

echo ============================================================
echo Services started.
echo Local Dashboard: http://localhost:5173
echo Server API: http://localhost:8000
echo To access from your mobile phone, open the URL shown in the
echo "JARVIS Dashboard" terminal under "Network:" (e.g. http://192.168.1.XX:5173)
echo ============================================================
