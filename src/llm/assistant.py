"""
Enhanced AI Assistant with RAG and memory context integration
"""
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime


logger = logging.getLogger(__name__)


# NOTE: This assistant wires together memory + document retrieval and then calls the LLM.

class PersonalAIAssistant:
    """Main AI Assistant combining LLM and RAG"""
    
    def __init__(self, llm_handler, vector_store=None, memory_db=None):
        """
        Initialize the assistant
        
        Args:
            llm_handler: LLM handler instance
            vector_store: FAISS vector store instance
            memory_db: SQLite memory database instance
        """
        self.llm = llm_handler
        self.vector_store = vector_store
        self.memory_db = memory_db
        
    async def generate_response(
        self,
        user_id: str,
        user_message: str,
        retrieve_memories: bool = True,
        retrieve_documents: bool = True,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Generate response with full RAG context
        
        Args:
            user_id: User ID
            user_message: User's message
            retrieve_memories: Whether to retrieve memories
            retrieve_documents: Whether to retrieve documents
            top_k: Number of top results to retrieve
            
        Returns:
            Dict with response and metadata
        """
        try:
            context_items = []
            sources = []
            
            # Retrieve relevant memories
            memory_context = []
            retrieved_memory_scores = []
            if retrieve_memories and self.vector_store:
                memory_results = self.vector_store.search(
                    user_message,
                    k=top_k,
                    filters={"user_id": user_id}
                )
                # MemoryManager filters documents out; here we just keep items with metadata.type != document.
                memory_context_items = [r for r in memory_results if r.get("metadata", {}).get("type") != "document"]
                memory_context = [r.get("content", "") for r in memory_context_items]
                retrieved_memory_scores = [r.get("similarity") for r in memory_context_items]
                context_items.extend(memory_context)
                sources.extend([{"type": "memory", "content": m} for m in memory_context])
            
            # Retrieve relevant documents
            document_context = []
            document_results = []
            if retrieve_documents and self.vector_store:
                document_results = self.vector_store.search_documents(
                    user_message,
                    k=top_k,
                    filters={"user_id": user_id}
                )
                document_context = [r.get("content", "") for r in document_results]
                context_items.extend(document_context)
                # Provide rich source info for UI/answering.
                for r in document_results:
                    meta = r.get("metadata", {})
                    sources.append({
                        "type": "document",
                        "content": r.get("content", ""),
                        "source": meta.get("document_name") or meta.get("filename") or "Unknown",
                        "page_number": meta.get("page_number"),
                        "document_id": meta.get("document_id"),
                        "chunk_id": meta.get("chunk_id"),
                        "similarity": r.get("similarity"),
                    })

            
            # Get user profile for personalization
            user_profile = {}
            if self.memory_db:
                user_profile = await self.memory_db.get_user_profile(user_id) or {}
            
            # Build comprehensive context
            context_str = self._build_context(
                user_message,
                memory_context,
                document_context,
                user_profile
            )
            
            # Generate response from LLM
            response = await self.llm.generate_response_with_context(
                user_message=user_message,
                context=context_str,
                user_profile=user_profile
            )
            
            # Store conversation
            if self.memory_db:
                await self.memory_db.add_conversation(
                    user_id=user_id,
                    user_message=user_message,
                    assistant_response=response,
                    sources=sources
                )
            
            return {
                "response": response,
                "sources": sources,
                "memory_count": len(memory_context),
                "document_count": len(document_context),
                "timestamp": datetime.now().isoformat(),
                "user_profile_used": bool(user_profile)
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": f"I encountered an error: {str(e)}",
                "sources": [],
                "error": str(e)
            }
    
    def _build_context(
        self,
        user_message: str,
        memories: List[str],
        documents: List[str],
        user_profile: Dict
    ) -> str:
        """Build comprehensive context for the LLM"""
        context_parts = []
        
        # Add user profile context
        if user_profile:
            profile_str = "## User Profile\n"
            for key, value in user_profile.items():
                if key != "id":
                    profile_str += f"- {key}: {value}\n"
            context_parts.append(profile_str)
        
        # Add relevant memories
        if memories:
            memory_str = "## Relevant Memories\n"
            for i, memory in enumerate(memories[:3], 1):
                memory_str += f"{i}. {memory}\n"
            context_parts.append(memory_str)
        
        # Add document context
        if documents:
            doc_str = "## Relevant Document Information\n"
            for i, doc in enumerate(documents[:3], 1):
                doc_str += f"{i}. {doc}\n"
            context_parts.append(doc_str)
        
        return "\n".join(context_parts)
    
    async def generate_suggestion(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Generate personalized suggestions"""
        try:
            user_profile = {}
            if self.memory_db:
                user_profile = await self.memory_db.get_user_profile(user_id) or {}
            
            # Get recent conversations
            recent_convos = []
            if self.memory_db:
                recent_convos = await self.memory_db.get_recent_conversations(
                    user_id, limit=5
                ) or []
            
            suggestion = await self.llm.generate_suggestion(
                user_profile=user_profile,
                recent_conversations=recent_convos
            )
            
            return {
                "suggestion": suggestion,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating suggestion: {e}")
            return {"suggestion": "Keep learning and stay focused!"}
    
    async def extract_user_insights(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Extract insights about the user from conversations"""
        try:
            recent_convos = []
            if self.memory_db:
                recent_convos = await self.memory_db.get_recent_conversations(
                    user_id, limit=10
                ) or []
            
            if not recent_convos:
                return {"insights": "Start having conversations to build insights"}
            
            insights = await self.llm.extract_insights(recent_convos)
            
            return {
                "insights": insights,
                "conversation_count": len(recent_convos),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            return {"insights": "Unable to extract insights at this time"}
