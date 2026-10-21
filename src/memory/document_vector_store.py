"""Dedicated document vector store for PDF chunk retrieval.

Implements a LangChain FAISS vector store with:
- persist path: data/faiss_documents/
- save_local() / load_local()
- similarity_search_with_score()

This store is intentionally separated from the existing conversation memory
FAISSVectorStore used by src/memory/vector_store.py.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DocumentVectorStore:
    def __init__(
        self,
        persist_path: str = "data/faiss_documents",
        embedding_model_name: str = "all-MiniLM-L6-v2",
    ):
        # Imports are inside to keep startup light and avoid hard failures
        # if optional deps are missing.
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import SentenceTransformerEmbeddings

        self.FAISS = FAISS
        self.persist_path = persist_path
        os.makedirs(self.persist_path, exist_ok=True)

        self.embedding_model_name = embedding_model_name
        self.embeddings = SentenceTransformerEmbeddings(model_name=embedding_model_name)

        self.index = None
        self._load_if_exists()

    def _load_if_exists(self) -> None:
        try:
            index_file = os.path.join(self.persist_path, "index.faiss")
            store_file = os.path.join(self.persist_path, "index.pkl")
            if os.path.exists(index_file) and os.path.exists(store_file):
                self.index = self.FAISS.load_local(
                    self.persist_path, self.embeddings, allow_dangerous_deserialization=True
                )
                logger.info("Loaded document FAISS index from disk")
            else:
                logger.info("No existing document FAISS index found; will create on first add")
                self.index = None
        except Exception as e:
            logger.error(f"Failed to load document FAISS index: {e}")
            self.index = None

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> None:
        from langchain_core.documents import Document

        docs = [Document(page_content=t, metadata=m) for t, m in zip(texts, metadatas)]
        if self.index is None:
            self.index = self.FAISS.from_documents(docs, self.embeddings)
        else:
            self.index.add_documents(docs)

        self.save_local()

    def save_local(self) -> None:
        if self.index is None:
            return
        try:
            self.index.save_local(self.persist_path)
        except Exception as e:
            logger.error(f"Failed saving document FAISS index: {e}")

    def similarity_search_with_score(
        self, query: str, k: int = 5
    ) -> List[Tuple[Any, float]]:
        if self.index is None:
            return []
        return self.index.similarity_search_with_score(query, k=k)

    def __len__(self) -> int:
        if self.index is None:
            return 0
        try:
            return len(self.index.index_to_docstore_id)
        except Exception:
            return 0

