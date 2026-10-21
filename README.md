# Personal AI Memory Assistant

## 🧠 Overview

A futuristic AI system that **remembers everything about you** and improves daily. This application combines advanced LLM APIs, vector databases, and personalized learning to create a digital brain that understands and adapts to your needs.

## ✨ Features

### Core Capabilities
- **🎯 Perfect Memory**: Never forget conversations, documents, or important information
- **🧠 Learning System**: AI learns your preferences and habits over time
- **💬 Natural Conversations**: Chat with your AI that knows your history
- **🔍 Semantic Search**: Find memories by meaning, not just keywords
- **💡 Smart Suggestions**: Get daily personalized recommendations
- **📊 Habit Analysis**: Understand your patterns and optimize your life
- **🔐 Privacy-First**: Your memories stay with you

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key (or alternative LLM)
- Git

### Installation and Run

**Windows:** run `start.bat` from the project folder. It installs the
requirements in a virtual environment and starts the backend and frontend in
separate terminal windows.

**macOS/Linux:** run `bash start.sh` from the project folder.

To start the services manually, run these commands from the project folder in
two terminals:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
uvicorn src.backend.main:app --reload
```

In the second terminal, start the frontend:

```powershell
.\.venv\Scripts\python.exe -m streamlit run src/frontend/app.py
```

The frontend is at http://localhost:8501 and the API documentation is at
http://127.0.0.1:8000/docs. An LLM API key is optional for local testing; set
`OPENAI_API_KEY` or `GEMINI_API_KEY` in `.env` to enable a hosted model. Without
a key, the backend uses its built-in development response mode.

## 📁 Project Structure

```
Personal AI/
├── src/
│   ├── backend/          # FastAPI backend server
│   │   ├── main.py       # Main application
│   │   └── routes/       # API endpoints
│   ├── frontend/         # Streamlit web interface
│   ├── memory/           # Memory management system
│   │   └── manager.py    # ChromaDB integration
│   ├── llm/              # LLM integration
│   │   └── llm_handler.py # OpenAI/Llama/Mistral handling
│   └── utils/            # Utility functions
├── data/                 # Vector database storage
├── requirements.txt      # Python dependencies
└── .env.example         # Environment template
```

## 🔌 API Endpoints

### Memory Management
- `POST /api/memory/add` - Add a new memory
- `POST /api/memory/search` - Search memories with semantic search
- `GET /api/memory/recent/{user_id}` - Get recent memories
- `DELETE /api/memory/{memory_id}` - Delete a memory

### Chat
- `POST /api/chat/send` - Send message and get response
- `GET /api/chat/history/{user_id}` - Get chat history

### Suggestions
- `GET /api/suggestions/daily/{user_id}` - Get daily suggestions
- `POST /api/suggestions/custom` - Create custom suggestion

### Habits
- `GET /api/habits/analyze/{user_id}` - Analyze user habits
- `POST /api/habits/track` - Track habit occurrence

## 🎯 How It Works

### 1. Memory Storage
- **Vector Embeddings**: Every memory is converted to embeddings using `sentence-transformers`
- **FAISS**: Stores memory and document embeddings locally for semantic search
- **Metadata**: Rich metadata tagging (type, created_at, category, etc.)

### 2. Learning System
- **Conversation Tracking**: All chats are stored for context
- **Pattern Recognition**: Identifies user habits and preferences
- **Preference Learning**: Adapts responses based on interaction history

### 3. Semantic Search
- **Natural Language**: Search by meaning, not just keywords
- **Context Aware**: Finds relevant memories even with different wording
- **Ranking**: Results ranked by relevance

### 4. AI Personalization
- **Memory Injection**: Relevant memories are provided to LLM for context
- **Preference Adaptation**: Responses adapted to user's communication style
- **Continuous Learning**: Each interaction improves future responses

## 🛠️ Configuration

### Environment Variables
```env
# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=
GEMINI_API_KEY=

# Local persistence
DB_PATH=./data/memory.db
FAISS_INDEX_PATH=./data/vector_store
DOC_VECTOR_STORE_PATH=./data/faiss_documents
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## 📚 Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI |
| Frontend | Streamlit |
| LLM | OpenAI / Google Gemini |
| Vector DB | FAISS |
| Embeddings | Sentence-Transformers |
| Memory Mgmt | LangChain |
| API Client | Requests, httpx |

## 🔄 Workflow

```
User Input
    ↓
Search Relevant Memories
    ↓
Inject Context to LLM
    ↓
Generate Personalized Response
    ↓
Store Conversation
    ↓
Update User Preferences
    ↓
Display Response
```

## 📊 Data Schema

### Memory Collection
```json
{
  "id": "user_001_1234567890",
  "content": "I love learning about machine learning",
  "embedding": [0.1, 0.2, ...],
  "metadata": {
    "user_id": "user_001",
    "type": "note",
    "created_at": "2024-01-01T10:00:00",
    "category": "learning"
  }
}
```

### Conversation Collection
```json
{
  "id": "user_001_conv_1234567890",
  "content": "User: How are you? Assistant: I'm great!",
  "metadata": {
    "user_id": "user_001",
    "user_message": "How are you?",
    "assistant_response": "I'm great!",
    "created_at": "2024-01-01T10:05:00"
  }
}
```

## 🚀 Advanced Features

### Coming Soon
- [ ] Multi-language support
- [ ] Voice memory input
- [ ] Emotional intelligence
- [ ] Long-term memory consolidation
- [ ] Predictive suggestions
- [ ] Social memory sharing
- [ ] Mobile app
- [ ] Calendar integration

## 🔐 Privacy & Security

- All memories stored locally by default
- Encryption support for sensitive data
- User-controlled data retention
- No external memory sharing without consent

## 📈 Performance Tips

1. **Batch Operations**: Add multiple memories at once
2. **Semantic Indexing**: Use meaningful keywords
3. **Regular Cleanup**: Archive old memories periodically
4. **API Caching**: Cache frequent queries

## 🐛 Troubleshooting

### ChromaDB Connection Issues
```bash
# Reset database
rm -rf ./data/chromadb
# Restart backend
```

### LLM API Errors
- Verify API keys in `.env`
- Check API quota
- Ensure rate limits aren't exceeded

### Frontend Connection Issues
- Ensure backend is running on port 8000
- Check CORS configuration
- Verify firewall settings

## 📝 License

MIT License - Feel free to use and modify

## 🤝 Contributing

We welcome contributions! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📧 Support

For issues and questions:
- Check existing issues on GitHub
- Create a new issue with details
- Include error logs and steps to reproduce

---

**🧠 Remember: An AI that learns becomes smarter every day.**
