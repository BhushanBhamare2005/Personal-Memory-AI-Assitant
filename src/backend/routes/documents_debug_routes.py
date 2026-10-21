"""Debug endpoints for document retrieval (RAG).

Must exist for Step 2.5 validation.
"""

import os
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/debug-search")
async def debug_search(q: str, user_id: str):
    """Semantic debug retrieval over PDF chunks.

    Returns:
    {
      query,
      chunks:[
        {text, document_name, page_number, chunk_id, similarity_score}
      ]
    }
    """
    try:
        from ..main import memory_manager

        # Dedicated document vector store (LangChain FAISS)
        doc_store = getattr(memory_manager, "document_vector_store", None)
        if doc_store is None:
            raise RuntimeError("Document vector store not initialized")

        results = doc_store.similarity_search_with_score(q, k=5)

        chunks: List[Dict[str, Any]] = []
        for doc, score in results:
            meta = doc.metadata or {}

            # If your store includes user scoping, filter here.
            if meta.get("user_id") and meta.get("user_id") != user_id:
                continue

            chunks.append(
                {
                    "text": doc.page_content,
                    "document_name": meta.get("document_name"),
                    "page_number": meta.get("page_number"),
                    "chunk_id": meta.get("chunk_id"),
                    "similarity_score": float(score),
                }
            )

        return {
            "query": q,
            "chunks": chunks,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

