# Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│                  (Streamlit Web Frontend)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP Requests
                      │ REST API
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway Layer                          │
│                   (FastAPI Server)                           │
│  - Memory Routes    - Chat Routes                            │
│  - Suggestion       - Habits Routes                          │
└──────┬──────────────┬──────────────┬────────────────────────┘
       │              │              │
       ▼              ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│   Memory     │ │   LLM       │ │   Vector     │
│  Manager     │ │  Handler    │ │   Database   │
│              │ │             │ │              │
│ - Add        │ │ - Generate  │ │ - ChromaDB   │
│ - Search     │ │ - Analyze   │ │ - Embeddings │
│ - Store      │ │ - Suggest   │ │ - Search     │
└──────┬───────┘ └─────┬───────┘ └──────┬───────┘
       │                │                │
       └────────┬───────┴────────┬───────┘
                ▼                ▼
        ┌──────────────────────────────┐
        │   Data Persistence Layer     │
        │                              │
        │ - chromadb/                  │
        │ - qdrant/ (future)           │
        │ - User memories              │
        │ - Conversations              │
        │ - Preferences                │
        └──────────────────────────────┘
```

## Data Flow

### Memory Addition Flow
```
User Input
    ↓
[Frontend: Memory Tab]
    ↓
POST /api/memory/add
    ↓
[Memory Manager]
    ├→ Generate embeddings (sentence-transformers)
    ├→ Create metadata
    └→ Store in ChromaDB
    ↓
Confirmation to User
```

### Chat Flow
```
User Message
    ↓
[Frontend: Chat Tab]
    ↓
POST /api/chat/send
    ↓
[Memory Manager]
    ├→ Search relevant memories
    └→ Return top K results
    ↓
[LLM Handler]
    ├→ Inject context (memories + system prompt)
    ├→ Call OpenAI API
    └→ Get response
    ↓
[Memory Manager]
    ├→ Store conversation
    └→ Update preferences
    ↓
Response to User
```

### Daily Suggestions Flow
```
User Requests Suggestions
    ↓
[Habits Analyzer]
    ├→ Analyze past conversations
    ├→ Identify patterns
    └→ Extract habits
    ↓
[Suggestion Engine]
    ├→ Generate recommendations
    ├→ Prioritize by importance
    └→ Filter by category
    ↓
Display Suggestions
```

## Key Technologies

### Backend
- **FastAPI**: High-performance async web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### Frontend
- **Streamlit**: Rapid prototyping UI framework
- **Requests**: HTTP client

### Memory & Storage
- **ChromaDB**: Vector database with Parquet persistence
- **SQLite**: Built-in for ChromaDB
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)

### LLM Integration
- **OpenAI API**: Primary LLM provider
- **LangChain**: LLM orchestration (prepared for expansion)
- **Python-dotenv**: Environment management

### Data Processing
- **NumPy**: Numerical computations
- **Pandas**: Data manipulation (future: analytics)

## Memory Structure

### Collections

#### 1. Memories Collection
- User's saved notes, ideas, learnings
- Embedded as vectors
- Searchable by semantic similarity
- Rich metadata (type, category, importance)

#### 2. Conversations Collection
- Chat history between user and AI
- Full context preservation
- Memory references
- User satisfaction ratings

#### 3. Preferences Collection
- User's communication style
- Learning preferences
- Content preferences
- System settings

## API Design

### RESTful Endpoints
```
Memory Management:
  POST   /api/memory/add              → Create memory
  POST   /api/memory/search           → Semantic search
  GET    /api/memory/recent/{user_id} → Recent memories
  DELETE /api/memory/{id}             → Delete memory

Chat:
  POST   /api/chat/send               → Send message
  GET    /api/chat/history/{user_id}  → Chat history

Suggestions:
  GET    /api/suggestions/daily/{user_id}      → Daily suggestions
  POST   /api/suggestions/custom               → Custom suggestion

Habits:
  GET    /api/habits/analyze/{user_id}        → Analyze habits
  POST   /api/habits/track                    → Track habit
```

## Scalability Considerations

### Current State (Single User)
- Direct ChromaDB access
- In-memory embeddings
- Synchronous LLM calls

### Future Enhancements
- Multi-user support with authentication
- Distributed vector search (Qdrant)
- Message queue (Celery/RabbitMQ)
- Caching layer (Redis)
- Multi-LLM load balancing
- Real-time WebSocket support

## Security Notes

### Current Implementation
- Environment-based API keys
- No authentication (single-user)
- Local data storage

### Production Recommendations
- Add JWT authentication
- Encrypt sensitive data
- Implement rate limiting
- Add HTTPS
- Sanitize user inputs
- Add audit logging

## Performance Metrics

### Expected Performance
- Memory add: ~100ms (embedding generation)
- Memory search: ~50ms (vector search)
- Chat response: 2-5s (LLM API latency)
- Memory retrieval: ~10ms (ChromaDB query)

### Optimization Opportunities
- Cache frequent queries
- Batch memory operations
- Implement fuzzy search
- Optimize embedding model
- Parallel LLM requests

## Extension Points

### Easy to Add
- New memory types
- Additional LLM providers
- New suggestion categories
- Custom preference fields

### Moderate Complexity
- Multi-user support
- Advanced analytics
- Voice input
- Document import

### Complex Features
- Real-time collaboration
- Distributed deployment
- Mobile synchronization
- Advanced NLP features
