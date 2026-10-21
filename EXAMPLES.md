# Personal AI Memory Assistant - Examples & Usage

## 📝 Example Use Cases

### 1. Student Learning Assistant

```
Monday Morning:
User: "I'm starting to learn about neural networks"
AI: Creates a memory "User interested in neural networks"

During the Week:
User: Adds memories:
  - "Learned about backpropagation"
  - "Transformers are attention mechanisms"
  - "Need to understand layer normalization"

Friday:
User: "What did I learn this week?"
AI: Searches memories and summarizes:
  - Key concepts learned
  - Topics to review
  - Suggested next steps based on your learning path
```

### 2. Professional Development

```
Daily Usage:
- Save key insights from meetings
- Record project decisions
- Track client preferences
- Store technical solutions

Monthly Review:
User: "Analyze my growth this month"
AI: 
  - Lists new skills acquired
  - Shows project progress
  - Suggests areas for improvement
```

### 3. Personal Health & Wellness

```
Daily:
- Log sleep hours
- Record workouts
- Note mood and energy
- Save wellness tips

Weekly:
User: "How's my health trending?"
AI: 
  - Analyzes patterns
  - Suggests optimizations
  - Recommends habits to build
```

### 4. Creative Projects

```
Brainstorming Session:
User: Adds multiple ideas/sketches/notes

Later:
User: "Show me all ideas about app design"
AI: Retrieves related concepts and builds upon them

Project Development:
- Store design decisions
- Track inspiration sources
- Remember user feedback
```

## 🔧 API Usage Examples

### Using `curl` or Postman

#### Add a Memory
```bash
curl -X POST http://localhost:8000/api/memory/add \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "content": "I want to build an AI application",
    "memory_type": "goal",
    "metadata": {"priority": "high"}
  }'
```

#### Search Memories
```bash
curl -X POST http://localhost:8000/api/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "query": "AI applications",
    "limit": 5
  }'
```

#### Send a Chat Message
```bash
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "message": "What are my goals?",
    "include_memories": true
  }'
```

### Using Python Requests

```python
import requests

API_URL = "http://localhost:8000/api"

# Add memory
response = requests.post(
    f"{API_URL}/memory/add",
    json={
        "user_id": "user_001",
        "content": "Today I learned about embeddings",
        "memory_type": "learning"
    }
)
print(response.json())

# Search memories
response = requests.post(
    f"{API_URL}/memory/search",
    json={
        "user_id": "user_001",
        "query": "machine learning concepts",
        "limit": 5
    }
)
results = response.json()
for memory in results['memories']:
    print(f"- {memory['content']}")

# Get daily suggestions
response = requests.get(
    f"{API_URL}/suggestions/daily/user_001"
)
suggestions = response.json()
for sugg in suggestions['suggestions']:
    print(f"- {sugg['title']}: {sugg['description']}")
```

### Using the Streamlit UI

#### Adding Memories
1. Go to "📝 Memories" tab
2. Click "⚡ Quick Add Memory" for fastest entry
3. Or use the search interface to organize

#### Chat Interaction
1. Go to "💬 Chat" tab
2. Type your message naturally
3. AI provides personalized responses with memory context
4. View how many memories were used

#### Getting Insights
1. Go to "📊 Habits" tab to see patterns
2. Go to "💡 Suggestions" for personalized recommendations
3. Track progress over time

## 📊 Data Example

### Adding Multiple Memories
```python
memories = [
    {
        "content": "Prefer morning meetings",
        "type": "preference"
    },
    {
        "content": "Interested in distributed systems",
        "type": "learning"
    },
    {
        "content": "Goal: Complete 3 online courses by year end",
        "type": "goal"
    },
    {
        "content": "Exercise routine: 30 min daily walk",
        "type": "habit"
    }
]

for mem in memories:
    requests.post(
        f"{API_URL}/memory/add",
        json={
            "user_id": "user_001",
            **mem
        }
    )
```

### Semantic Search Examples

```python
# Exact queries
queries = [
    "What are my goals?",
    "How much do I exercise?",
    "Tell me about my interests",
    "What meetings do I prefer?",
    "What courses am I taking?",
]

for query in queries:
    response = requests.post(
        f"{API_URL}/memory/search",
        json={
            "user_id": "user_001",
            "query": query,
            "limit": 3
        }
    )
    print(f"Query: {query}")
    for mem in response.json()['memories']:
        print(f"  - {mem['content']} (Score: {1-mem['distance']:.2f})")
```

## 🎯 Advanced Patterns

### Building a Knowledge Base Over Time

```
Day 1: Add 5 foundational memories
Day 2-7: Add daily learnings and experiences
Week 2: Start using semantic search for connections
Week 3: AI starts suggesting connections between topics
Month 2: Use habit analysis for optimization

Result: Rich, interconnected knowledge base with AI insights
```

### Creating Custom Workflows

```python
def daily_review(user_id):
    """Daily review workflow"""
    
    # Get yesterday's memories
    yesterday = requests.post(
        f"{API_URL}/memory/search",
        json={
            "user_id": user_id,
            "query": "daily activities",
            "limit": 10
        }
    )
    
    # Get habits analysis
    habits = requests.get(
        f"{API_URL}/habits/analyze/{user_id}"
    ).json()
    
    # Generate summary
    summary_request = requests.post(
        f"{API_URL}/chat/send",
        json={
            "user_id": user_id,
            "message": "Summarize my progress and provide recommendations",
            "include_memories": True
        }
    )
    
    return summary_request.json()

# Run daily review
daily_summary = daily_review("user_001")
print(daily_summary['assistant_response'])
```

### Integration with External Tools

```python
def sync_with_calendar(user_id, calendar_events):
    """Sync calendar events to memory"""
    
    for event in calendar_events:
        memory_content = f"Meeting: {event['title']} at {event['time']}"
        
        requests.post(
            f"{API_URL}/memory/add",
            json={
                "user_id": user_id,
                "content": memory_content,
                "memory_type": "event",
                "metadata": {
                    "calendar_id": event['id'],
                    "date": event['date']
                }
            }
        )

def sync_with_tasks(user_id):
    """Create tasks from AI suggestions"""
    
    suggestions = requests.get(
        f"{API_URL}/suggestions/daily/{user_id}"
    ).json()
    
    tasks = []
    for sugg in suggestions['suggestions']:
        tasks.append({
            "title": sugg['title'],
            "description": sugg['description'],
            "priority": sugg['priority']
        })
    
    # Push to task management system
    return tasks
```

## 🔄 Batch Operations

### Bulk Import Memories

```python
def bulk_import(user_id, source_data):
    """Import memories from external source"""
    
    imported = 0
    failed = 0
    
    for item in source_data:
        try:
            response = requests.post(
                f"{API_URL}/memory/add",
                json={
                    "user_id": user_id,
                    "content": item['text'],
                    "memory_type": item.get('type', 'note'),
                    "metadata": item.get('metadata', {})
                }
            )
            
            if response.status_code == 200:
                imported += 1
            else:
                failed += 1
        except Exception as e:
            print(f"Error importing: {e}")
            failed += 1
    
    return {"imported": imported, "failed": failed}

# Import from CSV, JSON, or other format
source_data = [
    {"text": "Learning goal: Python mastery", "type": "goal"},
    {"text": "Completed: FastAPI tutorial", "type": "learning"},
    {"text": "Prefer: Async operations", "type": "preference"},
]

result = bulk_import("user_001", source_data)
print(f"Imported: {result['imported']}, Failed: {result['failed']}")
```

## 📈 Analytics

### Track Engagement Over Time

```python
def get_engagement_stats(user_id, days=30):
    """Get engagement statistics"""
    
    # Get memory count
    recent = requests.get(
        f"{API_URL}/memory/recent/{user_id}",
        params={"limit": 1000}
    ).json()
    
    # Get chat history
    chats = requests.get(
        f"{API_URL}/chat/history/{user_id}",
        params={"limit": 100}
    ).json()
    
    # Get habits
    habits = requests.get(
        f"{API_URL}/habits/analyze/{user_id}"
    ).json()
    
    return {
        "total_memories": len(recent.get('memories', [])),
        "total_chats": len(chats.get('conversations', [])),
        "habits": habits.get('habits', {})
    }

stats = get_engagement_stats("user_001")
print(f"Total memories: {stats['total_memories']}")
print(f"Total chats: {stats['total_chats']}")
print(f"Habits: {stats['habits']}")
```

---

These examples show the flexibility and power of the Personal AI Memory Assistant. Mix and match them to create your own unique workflow!
