"""
Memory API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class MemoryRequest(BaseModel):
    user_id: str
    content: str
    memory_type: str = "note"
    metadata: Optional[dict] = None

class MemoryResponse(BaseModel):
    id: str
    content: str
    created_at: str
    type: str

class SearchRequest(BaseModel):
    user_id: str
    query: str
    limit: int = 5

@router.post("/add", response_model=dict)
async def add_memory(memory_req: MemoryRequest):
    """Add a new memory for the user"""
    try:
        from ..main import memory_manager
        
        if memory_manager is None:
            raise RuntimeError("Memory system is not initialized")

        memory_id = await memory_manager.add_memory(
            user_id=memory_req.user_id,
            content=memory_req.content,
            memory_type=memory_req.memory_type,
            metadata=memory_req.metadata
        )

        if not memory_id:
            raise RuntimeError("Memory could not be saved")
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Memory added successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_memories(search_req: SearchRequest):
    """Search user memories using semantic search"""
    try:
        from ..main import memory_manager
        
        results = memory_manager.search_memories(
            user_id=search_req.user_id,
            query=search_req.query,
            limit=search_req.limit
        )
        
        return {
            "success": True,
            "count": len(results),
            "memories": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent/{user_id}")
async def get_recent_memories(user_id: str, limit: int = 10):
    """Get recent memories for a user"""
    try:
        from ..main import memory_manager

        if memory_manager is None:
            raise RuntimeError("Memory system is not initialized")

        memories = await memory_manager.db.get_user_memories(user_id, limit)
        return {
            "success": True,
            "user_id": user_id,
            "memories": memories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a specific memory"""
    try:
        from ..main import memory_manager
        
        success = memory_manager.delete_memory(memory_id)
        
        return {
            "success": success,
            "message": "Memory deleted" if success else "Memory not found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
