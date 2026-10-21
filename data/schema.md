# Database Schema

## Collections Overview

The Personal AI Memory Assistant uses ChromaDB with three main collections:

### 1. Memories Collection
Stores all user memories, notes, and information.

```
Collection: memories
├── id (String): unique_memory_id
├── content (String): memory_text
├── embedding (Vector): semantic_embedding
└── metadata (Object):
    ├── user_id (String): owner user ID
    ├── type (String): note|idea|learning|goal|document|conversation
    ├── created_at (DateTime): creation timestamp
    ├── updated_at (DateTime): last update timestamp
    ├── category (String): topic_category
    ├── tags (Array): [tag1, tag2, ...]
    ├── importance (Number): 1-10 importance score
    └── source (String): web|document|manual|import
```

### 2. Conversations Collection
Stores all chat history and interactions.

```
Collection: conversations
├── id (String): conversation_id
├── content (String): "User: message\nAssistant: response"
├── embedding (Vector): combined_embedding
└── metadata (Object):
    ├── user_id (String): user ID
    ├── user_message (String): user's input
    ├── assistant_response (String): AI response
    ├── created_at (DateTime): conversation time
    ├── model_used (String): gpt-3.5-turbo|gpt-4|etc
    ├── tokens_used (Number): token count
    ├── memories_referenced (Array): [memory_id_1, memory_id_2, ...]
    ├── intent (String): query|command|conversation|learning
    └── satisfaction (Number): 1-5 user satisfaction rating
```

### 3. Preferences Collection
Stores user preferences and settings.

```
Collection: preferences
├── id (String): preference_id
├── content (String): "key: value"
├── embedding (Vector): key_embedding
└── metadata (Object):
    ├── user_id (String): user ID
    ├── preference_key (String): setting_name
    ├── preference_value (String): setting_value
    ├── category (String): communication|behavior|content|interface
    ├── created_at (DateTime): creation time
    └── updated_at (DateTime): last update time
```

## Metadata Categories

### Memory Types
- `note` - General notes and observations
- `idea` - Creative ideas and brainstorms
- `learning` - Educational content and learnings
- `goal` - Personal and professional goals
- `document` - Imported documents and files
- `conversation` - Conversational exchanges

### Preference Categories
- `communication` - How to communicate (tone, style, verbosity)
- `behavior` - Behavioral patterns and habits
- `content` - Content preferences (topics, formats)
- `interface` - UI/UX preferences

## Query Examples

### Search memories by semantic similarity
```python
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={"user_id": {"$eq": user_id}}
)
```

### Filter by type and date range
```python
results = collection.get(
    where={
        "user_id": {"$eq": user_id},
        "type": {"$eq": "learning"},
        "created_at": {"$gte": "2024-01-01T00:00:00"}
    }
)
```

### Find high-importance memories
```python
results = collection.get(
    where={
        "user_id": {"$eq": user_id},
        "importance": {"$gte": 8}
    }
)
```

## Indexes

ChromaDB automatically creates indexes on:
- `user_id` for faster user-specific queries
- `created_at` for temporal queries
- Vector embeddings for semantic search

## Storage

### Default Locations
- **ChromaDB**: `./data/chromadb/`
- **Parquet Files**: `./data/chromadb/*.parquet`
- **Index**: `./data/chromadb/index/`

### Data Persistence
- All data persists across application restarts
- Automatic backups recommended for production
- Export functionality for data portability

## Scaling Considerations

For large datasets:
- Consider FAISS for in-memory vector search
- Use Qdrant for distributed deployments
- Implement archival strategy for old memories
- Partition data by user or date range
- Monitor ChromaDB performance metrics

## Migration Guide

To migrate data between storage backends:
1. Export from ChromaDB (Parquet format)
2. Convert embeddings if needed
3. Import to new backend (FAISS, Qdrant, etc.)
4. Validate data integrity
5. Update configuration

## Backup & Recovery

### Regular Backups
```bash
# Backup ChromaDB directory
cp -r ./data/chromadb ./backups/chromadb_$(date +%Y%m%d)
```

### Recovery
```bash
# Restore from backup
cp -r ./backups/chromadb_YYYYMMDD/* ./data/chromadb/
```
