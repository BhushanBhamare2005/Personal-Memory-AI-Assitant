# Quick Start

## Start the application

From the project folder:

- **Windows:** run `start.bat`.
- **macOS/Linux:** run `bash start.sh`.

The startup script prepares a virtual environment, installs `requirements.txt`,
and starts FastAPI and Streamlit. The web app opens at
http://localhost:8501. The backend API and interactive API docs are at
http://127.0.0.1:8000 and http://127.0.0.1:8000/docs.

The project includes a local development response mode, so an LLM API key is
not required to test memory storage and chat. To use a hosted model, set
`LLM_PROVIDER=openai` and `OPENAI_API_KEY`, or `LLM_PROVIDER=gemini` and
`GEMINI_API_KEY`, in `.env`. Copy `.env.example` to `.env` if it does not
already exist, then restart the backend.

## Run services manually

From the project folder, create and install into a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

In terminal 1:

```powershell
uvicorn src.backend.main:app --reload
```

In terminal 2:

```powershell
.\.venv\Scripts\python.exe -m streamlit run src/frontend/app.py
```

## Smoke test

With the backend running, run:

```powershell
.\.venv\Scripts\python.exe test_api.py
```

To run the focused backend tests:

```powershell
.\.venv\Scripts\python.exe -m pytest src/backend/test_runtime_workflows.py src/backend/test_pdf_chunking_logic.py
```
