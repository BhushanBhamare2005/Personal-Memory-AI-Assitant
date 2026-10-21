"""
Suggestions API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class DailySuggestionsRequest(BaseModel):
    user_id: str
    category: Optional[str] = None  # study, health, tasks, etc.

@router.get("/daily/{user_id}")
async def get_daily_suggestions(user_id: str, category: Optional[str] = None):
    """Get personalized daily suggestions based on user patterns"""
    try:
        suggestions = [
            {
                "title": "Review your learning goals",
                "description": "Based on your past interests, consider reviewing machine learning fundamentals",
                "category": "study",
                "priority": "high"
            },
            {
                "title": "Take a break",
                "description": "You've been working for several hours, take a 15-minute break",
                "category": "health",
                "priority": "medium"
            },
            {
                "title": "Update your project memories",
                "description": "Document your progress on current projects for future reference",
                "category": "productivity",
                "priority": "medium"
            }
        ]
        
        # Filter by category if provided
        if category:
            suggestions = [s for s in suggestions if s["category"] == category]
        
        return {
            "success": True,
            "user_id": user_id,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/custom")
async def create_custom_suggestion(user_id: str, suggestion: str):
    """Create a custom suggestion for the user"""
    try:
        return {
            "success": True,
            "user_id": user_id,
            "suggestion": suggestion,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
