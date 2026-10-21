# Personal AI Memory Assistant - Development Guide

## Project Overview
A futuristic AI system that remembers everything about users and improves daily. It combines LLM APIs, vector databases, and personalized learning to create a digital brain for users.

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit
- **LLM**: OpenAI API / Mistral / Llama
- **Vector DB**: ChromaDB / FAISS / Qdrant
- **Memory Management**: LangChain
- **ML**: sentence-transformers for embeddings

## Setup Instructions

### 1. Environment Setup
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2. Configuration
- Copy `.env.example` to `.env`
- Add your API keys (OpenAI, Mistral, etc.)
- Configure vector database path

### 3. Running the Application

**Backend Server:**
```bash
cd src/backend
python -m uvicorn main:app --reload --port 8000
```

**Frontend (Streamlit):**
```bash
streamlit run src/frontend/app.py
```

## Project Structure
- `src/backend/` - FastAPI backend server
- `src/frontend/` - Streamlit web interface
- `src/memory/` - Memory management system
- `src/llm/` - LLM integration and chains
- `src/utils/` - Utility functions
- `data/` - Vector database and storage

## Core Features
1. **Memory Storage**: Persistent user memories and conversations
2. **Vector Embeddings**: Semantic search across memories
3. **Daily Suggestions**: Personalized recommendations
4. **Habit Tracking**: Learn user patterns
5. **Long-term Personalization**: Improve responses over time

## API Endpoints
- `POST /api/memory/add` - Add new memory
- `GET /api/memory/search` - Search memories
- `GET /api/suggestions/daily` - Get daily suggestions
- `GET /api/habits/analyze` - Analyze user habits
- `POST /api/chat` - Chat with AI assistant

## Database Schema
See `data/schema.md` for detailed database structure.
