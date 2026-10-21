"""
Chat API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class ChatMessage(BaseModel):
    user_id: str
    message: str
    include_memories: bool = True

class ChatResponse(BaseModel):
    user_id: str
    user_message: str
    assistant_response: str
    memories_used: List[str]
    timestamp: str

@router.post("/send", response_model=dict)
async def send_message(chat_msg: ChatMessage):
    """Send a message and get an AI response"""
    try:
        from ..main import memory_manager, llm_handler

        if memory_manager is None or llm_handler is None:
            raise RuntimeError("Assistant systems are not initialized")
        
        # Retrieve relevant memories + documents and generate response end-to-end
        start_ts = datetime.now().isoformat()

        from ...llm.assistant import PersonalAIAssistant

        assistant = PersonalAIAssistant(
            llm_handler=llm_handler,
            vector_store=getattr(memory_manager, "vector_store", None),
            memory_db=getattr(memory_manager, "db", None),
        )

        rag_result = await assistant.generate_response(
            user_id=chat_msg.user_id,
            user_message=chat_msg.message,
            retrieve_memories=chat_msg.include_memories,
            retrieve_documents=True,
            top_k=5,
        )
        if rag_result.get("error"):
            raise RuntimeError(rag_result["error"])

        # Persist conversation if assistant did not (some implementations may return only response)
        # We rely on PersonalAIAssistant+DatabaseManager; if that fails, still return answer.


        return {
            "success": True,
            "user_id": chat_msg.user_id,
            "user_message": chat_msg.message,
            "assistant_response": rag_result.get("response", ""),
            "memories_used": rag_result.get("memory_count", 0),
            "documents_used": rag_result.get("document_count", 0),
            "sources": rag_result.get("sources", []),
            "timestamp": datetime.now().isoformat(),
            "rag_started_at": start_ts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 10):
    """Get chat history for a user"""
    try:
        from ..main import memory_manager
        
        conversations = await memory_manager.get_recent_conversations(
            user_id=user_id,
            limit=limit
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "conversations": conversations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
