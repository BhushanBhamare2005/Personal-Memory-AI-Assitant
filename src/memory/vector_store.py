"""
FAISS-based Vector Store for efficient semantic search
"""
import os
import json
import logging
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import faiss
    from sentence_transformers import SentenceTransformer
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    logger.warning("FAISS not installed. Vector store functionality disabled.")


class FAISSVectorStore:
    """Vector store using FAISS for efficient semantic search"""
    
    def __init__(self, vector_dim: int = 384, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize FAISS vector store
        
        Args:
            vector_dim: Dimension of embeddings
            model_name: SentenceTransformer model to use
        """
        if not HAS_FAISS:
            raise RuntimeError("FAISS not installed. Install with: pip install faiss-cpu sentence-transformers")
        
        self.vector_dim = vector_dim
        self.model_name = model_name
        self.embedder = SentenceTransformer(model_name)
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(vector_dim)
        
        # Store metadata
        self.metadata = []
        self.store_path = os.getenv(
            "FAISS_INDEX_PATH",
            os.path.join("data", "vector_store"),
        )
        os.makedirs(self.store_path, exist_ok=True)
        
        # Load existing data if available
        self._load_from_disk()
        
        logger.info(f"FAISS Vector Store initialized with {len(self.metadata)} items")
    
    def add_texts(
        self,
        texts: List[str],
        metadata: List[Dict[str, Any]] = None,
        batch_size: int = 32
    ) -> List[int]:
        """
        Add texts to vector store
        
        Args:
            texts: List of text strings to add
            metadata: List of metadata dicts for each text
            batch_size: Batch size for embedding
            
        Returns:
            List of indices added
        """
        try:
            if metadata is None:
                metadata = [{"content": text} for text in texts]
            
            # Generate embeddings
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                batch_embeddings = self.embedder.encode(batch, convert_to_numpy=True)
                embeddings.extend(batch_embeddings)
            
            embeddings = np.array(embeddings).astype('float32')
            
            # Add to FAISS index
            start_idx = len(self.metadata)
            self.index.add(embeddings)
            
            # Add metadata
            for i, meta in enumerate(metadata):
                meta["index"] = start_idx + i
                meta["added_at"] = datetime.now().isoformat()
                self.metadata.append(meta)
            
            # Save to disk
            self._save_to_disk()
            
            logger.info(f"Added {len(texts)} texts to vector store")
            return list(range(start_idx, start_idx + len(texts)))
            
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {e}")
            return []
    
    def search(
        self,
        query: str,
        k: int = 5,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar texts
        
        Args:
            query: Query text
            k: Number of results to return
            filters: Optional filters for metadata
            
        Returns:
            List of results with content and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embedder.encode([query], convert_to_numpy=True).astype('float32')
            
            # Search FAISS index
            distances, indices = self.index.search(query_embedding, min(k * 2, len(self.metadata)))
            
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0:
                    continue
                    
                metadata = self.metadata[int(idx)]
                
                # Apply filters if provided
                if filters:
                    if not self._matches_filters(metadata, filters):
                        continue
                
                results.append({
                    "index": int(idx),
                    "content": metadata.get("content", ""),
                    "metadata": metadata,
                    "distance": float(dist),
                    "similarity": float(1 / (1 + dist))
                })
            
            return results[:k]
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def search_documents(
        self,
        query: str,
        k: int = 5,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents specifically
        
        Args:
            query: Query text
            k: Number of results to return
            filters: Optional filters for metadata
            
        Returns:
            List of document results
        """
        if filters is None:
            filters = {}
        filters["type"] = "document"
        
        return self.search(query, k, filters)
    
    def _matches_filters(self, metadata: Dict, filters: Dict) -> bool:
        """Check if metadata matches filters"""
        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def delete(self, indices: List[int]) -> bool:
        """
        Delete items by indices (requires index rebuild)
        
        Args:
            indices: List of indices to delete
            
        Returns:
            Success status
        """
        try:
            # Mark for deletion
            indices_set = set(indices)
            new_metadata = []
            new_embeddings = []
            
            for i, meta in enumerate(self.metadata):
                if i not in indices_set:
                    new_embeddings.append(meta)
                    new_metadata.append(meta)
            
            # Rebuild index
            self.metadata = new_metadata
            embeddings_array = np.array([
                self.embedder.encode([m.get("content", "")], convert_to_numpy=True)[0]
                for m in new_metadata
            ]).astype('float32')
            
            self.index = faiss.IndexFlatL2(self.vector_dim)
            if len(embeddings_array) > 0:
                self.index.add(embeddings_array)
            
            self._save_to_disk()
            logger.info(f"Deleted {len(indices)} items from vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from vector store: {e}")
            return False
    
    def _save_to_disk(self):
        """Save index and metadata to disk"""
        try:
            faiss.write_index(self.index, os.path.join(self.store_path, "faiss.index"))
            with open(os.path.join(self.store_path, "metadata.json"), "w") as f:
                json.dump(self.metadata, f)
            logger.debug("Vector store saved to disk")
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
    
    def _load_from_disk(self):
        """Load index and metadata from disk"""
        try:
            index_path = os.path.join(self.store_path, "faiss.index")
            metadata_path = os.path.join(self.store_path, "metadata.json")
            
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
                logger.debug("Loaded FAISS index from disk")
            
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    self.metadata = json.load(f)
                logger.debug(f"Loaded {len(self.metadata)} metadata items")
                
        except Exception as e:
            logger.warning(f"Could not load existing vector store: {e}")
    
    def __len__(self) -> int:
        """Get number of items in store"""
        return len(self.metadata)
    
    def clear(self):
        """Clear all data"""
        self.index = faiss.IndexFlatL2(self.vector_dim)
        self.metadata = []
        self._save_to_disk()
        logger.info("Vector store cleared")


class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding service"""
        self.model_name = model_name
        self.embedder = SentenceTransformer(model_name)
        self.vector_dim = self.embedder.get_sentence_embedding_dimension()
    
    def embed(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Embed texts to vectors
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for embedding
            
        Returns:
            Numpy array of embeddings
        """
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = self.embedder.encode(batch, convert_to_numpy=True)
            embeddings.extend(batch_embeddings)
        
        return np.array(embeddings).astype('float32')
    
    def embed_single(self, text: str) -> np.ndarray:
        """Embed single text"""
        return self.embedder.encode([text], convert_to_numpy=True).astype('float32')[0]
    
    def similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        embeddings = self.embedder.encode([text1, text2])
        from sklearn.metrics.pairwise import cosine_similarity
        return float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
