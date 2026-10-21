"""
Utility functions for the Personal AI Memory Assistant
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

def format_timestamp(timestamp: str) -> str:
    """Format timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except:
        return timestamp

def get_time_ago(timestamp: str) -> str:
    """Get relative time (e.g., '2 hours ago')"""
    try:
        dt = datetime.fromisoformat(timestamp)
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} day(s) ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hour(s) ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minute(s) ago"
        else:
            return "just now"
    except:
        return "unknown time"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text for tagging"""
    # Simple keyword extraction (can be enhanced with NLP)
    keywords = []
    important_words = text.split()
    
    for word in important_words:
        if len(word) > 4:  # Only words longer than 4 characters
            keywords.append(word.lower().strip(".,!?;:"))
    
    return list(set(keywords))[:5]  # Return top 5 unique keywords

def calculate_memory_score(memory_usage_count: int, days_since_creation: int) -> float:
    """Calculate importance score for a memory"""
    # Score based on usage frequency and age
    usage_score = min(memory_usage_count * 10, 100)
    time_decay = max(100 - (days_since_creation * 0.5), 10)
    
    return (usage_score + time_decay) / 2

def batch_process_memories(memories: List[Dict], batch_size: int = 10) -> List[List[Dict]]:
    """Batch memories for processing"""
    batches = []
    for i in range(0, len(memories), batch_size):
        batches.append(memories[i:i + batch_size])
    return batches
