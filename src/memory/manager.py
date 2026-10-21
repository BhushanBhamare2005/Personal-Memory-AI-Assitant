"""
Memory management system for storing and retrieving user memories
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from .vector_store import FAISSVectorStore
from .document_processor import DocumentStore, PDFLoader, RAGRetriever
from .document_vector_store import DocumentVectorStore

from .database import DatabaseManager


class MemoryManager:
    """Manages user memories with FAISS vector store and SQLite database"""
    
    def __init__(self):
        """Initialize memory manager with all components"""
        try:
            # Initialize vector store
            self.vector_store = FAISSVectorStore(
                model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            )
            
            # Initialize database
            self.db = DatabaseManager(
                db_path=os.getenv("DB_PATH", "data/memory.db")
            )
            
            # Initialize document components
            self.document_store = DocumentStore()
            self.pdf_loader = PDFLoader()
            self.rag_retriever = RAGRetriever(self.vector_store, self.document_store)

            # Dedicated document vector store (LangChain FAISS)
            self.document_vector_store = DocumentVectorStore(
                persist_path=os.getenv("DOC_VECTOR_STORE_PATH", "data/faiss_documents"),
                embedding_model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            )

            
            logger.info("Memory Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing MemoryManager: {e}")
            raise
    
    async def add_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "note",
        importance_score: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Add a memory for user"""
        memory_id = await self.db.add_memory(
            user_id, content, memory_type, importance_score
        )

        vector_metadata = {
            **(metadata or {}),
            "user_id": user_id,
            "type": memory_type,
            "importance": importance_score,
            "content": content,
            "memory_id": memory_id,
        }
        indices = self.vector_store.add_texts(
            texts=[content],
            metadata=[vector_metadata],
        )
        if not indices:
            raise RuntimeError("Memory was saved but could not be indexed for search")

        logger.info("Memory %s added for user %s", memory_id, user_id)
        return memory_id
    
    def search_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search user memories using semantic search via FAISS vector store."""
        try:
            filters = {"user_id": user_id, "type": "note"}
            # Note: stored memory type varies; fallback to all types if no note exists.
            results = self.vector_store.search(query, k=limit, filters={"user_id": user_id})
            # Keep only memory-like items (documents are type=document)
            filtered = [r for r in results if r.get("metadata", {}).get("type") != "document"]
            return filtered[:limit]
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    def add_conversation(self, user_id: str, message: str, response: str, context: Dict = None) -> str:
        """Store a conversation turn"""
        if context is None:
            context = {}
        
        conversation_id = f"{user_id}_conv_{datetime.now().timestamp()}"
        content = f"User: {message}\nAssistant: {response}"
        
        metadata = {
            "user_id": user_id,
            "user_message": message,
            "assistant_response": response,
            "created_at": datetime.now().isoformat(),
            **context
        }
        
        self.conversations_collection.add(
            ids=[conversation_id],
            documents=[content],
            metadatas=[metadata]
        )
        
        return conversation_id
    
    async def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations for a user"""
        return await self.db.get_recent_conversations(user_id, limit)
    
    def save_preference(self, user_id: str, key: str, value: Any) -> None:
        """Save a user preference"""
        pref_id = f"{user_id}_pref_{key}"
        
        metadata = {
            "user_id": user_id,
            "preference_key": key,
            "preference_value": str(value),
            "updated_at": datetime.now().isoformat()
        }
        
        self.preferences_collection.add(
            ids=[pref_id],
            documents=[f"{key}: {value}"],
            metadatas=[metadata]
        )
    
    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all preferences for a user"""
        try:
            results = self.preferences_collection.get(
                where={"user_id": {"$eq": user_id}}
            )
            
            preferences = {}
            if results and results['documents']:
                for i, _ in enumerate(results['documents']):
                    metadata = results['metadatas'][i]
                    key = metadata['preference_key']
                    value = metadata['preference_value']
                    preferences[key] = value
            
            return preferences
        except:
            return {}
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory"""
        try:
            self.memories_collection.delete(ids=[memory_id])
            return True
        except:
            return False
