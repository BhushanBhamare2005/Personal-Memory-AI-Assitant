"""
Memory management system for storing and retrieving user memories
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

from .vector_store import FAISSVectorStore, EmbeddingService
from .document_processor import DocumentStore, PDFLoader, RAGRetriever
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
            
            # Initialize embedding service
            self.embedding_service = EmbeddingService()
            
            logger.info("Memory Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing MemoryManager: {e}")
            raise
    
    async def add_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "note",
        importance_score: float = 0.5
    ) -> bool:
        """Add a memory for user"""
        try:
            # Add to vector store
            self.vector_store.add_texts(
                texts=[content],
                metadata=[{
                    "user_id": user_id,
                    "type": memory_type,
                    "importance": importance_score,
                    "content": content
                }]
            )
            
            # Add to database
            await self.db.add_memory(user_id, content, memory_type, importance_score)
            
            logger.info(f"Memory added for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return False
    
    async def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search user memories using semantic search"""
        try:
            results = self.vector_store.search(
                query=query,
                k=limit,
                filters={"user_id": user_id}
            )
            return results
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def add_document(
        self,
        user_id: str,
        file_path: str,
        doc_type: str = "pdf"
    ) -> Optional[str]:
        """Add and process a document"""
        try:
            if doc_type == "pdf":
                doc_info = self.pdf_loader.load_pdf(file_path)
                
                # Add chunks to vector store
                chunks = doc_info["chunks"]
                chunk_texts = [chunk["content"] for chunk in chunks]
                doc_id = doc_info["filename"].replace(".pdf", "")
                
                self.vector_store.add_texts(
                    texts=chunk_texts,
                    metadata=[{
                        "user_id": user_id,
                        "type": "document",
                        "document_id": doc_id,
                        "filename": doc_info["filename"],
                        "content": text,
                        "chunk_id": i
                    } for i, text in enumerate(chunk_texts)]
                )
                
                # Add to document store
                self.document_store.add_document(
                    doc_id=doc_id,
                    filename=doc_info["filename"],
                    content_chunks=chunks,
                    metadata={
                        "user_id": user_id,
                        "pages": doc_info["total_pages"]
                    }
                )
                
                # Add to database
                await self.db.add_document(
                    doc_id=doc_id,
                    user_id=user_id,
                    filename=doc_info["filename"],
                    file_path=file_path,
                    chunk_count=len(chunks),
                    total_pages=doc_info["total_pages"],
                    metadata={"added_at": datetime.now().isoformat()}
                )
                
                logger.info(f"Document {doc_info['filename']} added for user {user_id}")
                return doc_id
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return None
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile"""
        return await self.db.get_user_profile(user_id)
    
    async def update_user_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any]
    ) -> bool:
        """Update user profile"""
        return await self.db.update_user_profile(user_id, profile_data)
    
    async def add_conversation(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        sources: List[Dict] = None
    ) -> bool:
        """Add conversation to memory"""
        try:
            # Also add to vector store for semantic search
            self.vector_store.add_texts(
                texts=[user_message, assistant_response],
                metadata=[
                    {
                        "user_id": user_id,
                        "type": "conversation",
                        "role": "user",
                        "content": user_message
                    },
                    {
                        "user_id": user_id,
                        "type": "conversation",
                        "role": "assistant",
                        "content": assistant_response
                    }
                ]
            )
            
            # Add to database
            return await self.db.add_conversation(
                user_id, user_message, assistant_response, sources
            )
            
        except Exception as e:
            logger.error(f"Error adding conversation: {e}")
            return False
    
    async def get_recent_conversations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent conversations"""
        return await self.db.get_recent_conversations(user_id, limit)
    
    async def retrieve_for_rag(
        self,
        user_id: str,
        query: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve documents for RAG"""
        return await self.rag_retriever.retrieve(query, k, user_id)
    
    async def get_user_documents(self, user_id: str) -> List[Dict]:
        """Get user's documents"""
        return await self.db.get_user_documents(user_id)
    
    async def set_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Set user preferences"""
        return await self.db.set_preferences(user_id, preferences)
    
    async def get_preferences(self, user_id: str) -> Optional[Dict]:
        """Get user preferences"""
        return await self.db.get_preferences(user_id)
    
    def close(self):
        """Close connections"""
        if self.db:
            self.db.close()
