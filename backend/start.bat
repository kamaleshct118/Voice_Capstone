@echo off
title Voice Capstone — Backend Server

echo =======================================
echo  Voice AI Healthcare Assistant Backend
echo =======================================

:: ── Activate Conda environment ────────────────────────────────────
call conda activate venv
if errorlevel 1 (
    echo [ERROR] Failed to activate conda environment 'venv'.
    echo Make sure conda is installed and 'venv' environment exists.
    echo Run: conda create -n venv python=3.10
    pause
    exit /b 1
)

echo [OK] Conda environment 'venv' activated.

:: ── Change to backend directory (in case bat is run from elsewhere) ─
cd /d "%~dp0"

echo [OK] Working directory set to: %~dp0

:: ── Start backend with hot-reload ─────────────────────────────────
echo.
echo [STARTING] uvicorn — http://localhost:8000
echo [DOCS]     Swagger UI — http://localhost:8000/docs
echo [NOTE]     Auto-reload is ON. Save any .py file to trigger reload.
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app

:: ── If server exits ───────────────────────────────────────────────
echo.
echo [STOPPED] Backend server has stopped.
pause
