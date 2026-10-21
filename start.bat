@echo off
setlocal
cd /d "%~dp0"

echo Personal AI Memory Assistant
echo ============================

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    set "VENV_SCRIPTS=.venv\Scripts"
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON=venv\Scripts\python.exe"
    set "VENV_SCRIPTS=venv\Scripts"
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create the virtual environment.
        exit /b 1
    )
    set "PYTHON=.venv\Scripts\python.exe"
    set "VENV_SCRIPTS=.venv\Scripts"
)

echo Installing or updating dependencies...
"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed.
    exit /b 1
)

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Created .env from .env.example.
)

if not exist "data\documents" mkdir "data\documents"
if not exist "logs" mkdir "logs"

echo Starting the backend and Streamlit frontend...
start "Personal AI Backend" cmd /k "call %VENV_SCRIPTS%\activate.bat && uvicorn src.backend.main:app --reload"
start "Personal AI Frontend" cmd /k ""%PYTHON%" -m streamlit run src/frontend/app.py"

echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:8501
echo Close the two application windows to stop the services.
