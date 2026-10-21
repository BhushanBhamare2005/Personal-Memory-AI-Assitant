"""PDF Loader and Document Processing for RAG

Production goal (Step 2.5):
- Page-aware PDF extraction
- RecursiveCharacterTextSplitter chunking (chunk_size=1000, chunk_overlap=200)
- Chunk metadata: document_id, document_name, page_number, chunk_id, source_type, upload_timestamp

Note: This module only prepares chunks + metadata. Indexing + vector persistence
are handled by the dedicated document FAISS store and API layer.
"""

import os
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader

    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


class PDFLoader:
    """Load and process PDF documents with true page-aware chunking."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if not HAS_PYPDF:
            logger.warning("PyPDF not installed. PDF loading disabled.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Splitter is created lazily to avoid import cost if not using PDFs.
        self._splitter = None

    def _get_splitter(self):
        """Create LangChain RecursiveCharacterTextSplitter with required params."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def _clean_text(self, text: str) -> str:
        text = " ".join((text or "").split())
        text = text.replace("\x00", "")
        return text.strip()

    def _chunk_text(self, text: str) -> List[Dict[str, str]]:
        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            return []

        splitter = self._splitter
        if splitter is None:
            splitter = self._get_splitter()
            self._splitter = splitter

        return [
            {"content": document.page_content.strip()}
            for document in splitter.create_documents([cleaned_text])
            if document.page_content and document.page_content.strip()
        ]

    def load_pdf(
        self,
        file_path: str,
        document_id: Optional[str] = None,
        document_name: Optional[str] = None,
        upload_timestamp: Optional[str] = None,
        source_type: str = "document",
    ) -> Dict[str, Any]:
        """Extract pages and chunk per page.

        Returns
        - filename, file_path, title, total_pages, loaded_at
        - chunks: List[{content, page_number, chunk_id}]
        """
        try:
            if not HAS_PYPDF:
                raise RuntimeError("PyPDF not installed. Install with: pip install pypdf")

            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            document_id = document_id or file_path.stem
            document_name = document_name or file_path.name
            upload_timestamp = upload_timestamp or str(int(datetime.now().timestamp()))

            reader = PdfReader(file_path)
            total_pages = len(reader.pages)

            chunks: List[Dict[str, Any]] = []
            chunk_counter = 0

            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text() or ""
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num}: {e}")
                    page_text = ""

                page_text = self._clean_text(page_text)

                # Skip empty pages
                if not page_text.strip():
                    continue

                for chunk in self._chunk_text(page_text):
                    chunks.append(
                        {
                            "content": chunk["content"],
                            "page_number": page_num,
                            "chunk_id": chunk_counter,
                        }
                    )
                    chunk_counter += 1

            loaded_at = datetime.now().isoformat()
            return {
                "filename": file_path.name,
                "file_path": str(file_path),
                "title": file_path.stem,
                "total_pages": total_pages,
                "loaded_at": loaded_at,
                "chunks": [
                    {
                        **c,
                        "document_id": document_id,
                        "document_name": document_name,
                        "source_type": source_type,
                        "upload_timestamp": upload_timestamp,
                    }
                    for c in chunks
                ],
            }

        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            raise


class DocumentStore:
    """Lightweight in-memory document metadata store (legacy).

    Kept for compatibility with existing code paths.
    Production indexing uses SQLite documents table + dedicated FAISS.
    """

    def __init__(self):
        self.documents_dir = os.path.join("data", "documents")
        os.makedirs(self.documents_dir, exist_ok=True)
        self.metadata_file = os.path.join(self.documents_dir, "metadata.json")
        self.documents: Dict[str, Any] = {}
        self._load_metadata()

    def add_document(
        self,
        doc_id: str,
        filename: str,
        content_chunks: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None,
    ) -> bool:
        try:
            metadata = metadata or {}
            self.documents[doc_id] = {
                "id": doc_id,
                "filename": filename,
                "chunks": content_chunks,
                "chunk_count": len(content_chunks),
                "added_at": datetime.now().isoformat(),
                "metadata": metadata,
            }
            self._save_metadata()
            logger.info(f"Added document '{filename}' with {len(content_chunks)} chunks")
            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self.documents.get(doc_id)

    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        for _, doc in self.documents.items():
            if query_lower in doc.get("filename", "").lower():
                results.append(doc)
                continue
            for v in (doc.get("metadata") or {}).values():
                if query_lower in str(v).lower():
                    results.append(doc)
                    break
        return results

    def delete_document(self, doc_id: str) -> bool:
        try:
            if doc_id in self.documents:
                del self.documents[doc_id]
                self._save_metadata()
                logger.info(f"Deleted document {doc_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False

    def _save_metadata(self):
        import json

        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def _load_metadata(self):
        import json

        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                logger.info(f"Loaded {len(self.documents)} documents from metadata")
        except Exception as e:
            logger.warning(f"Could not load metadata: {e}")

    def __len__(self) -> int:
        return len(self.documents)


class RAGRetriever:
    """Legacy retriever wrapper (kept for imports).

    The Step 2.5 document retrieval uses a dedicated LangChain FAISS instance.
    """

    def __init__(self, vector_store, document_store: DocumentStore):
        self.vector_store = vector_store
        self.document_store = document_store

    async def retrieve(
        self,
        query: str,
        k: int = 5,
        user_id: str = None,
    ) -> List[Dict[str, Any]]:
        try:
            filters = {}
            if user_id:
                filters["user_id"] = user_id

            results = self.vector_store.search_documents(query, k=k, filters=filters)

            for result in results:
                doc_id = result.get("metadata", {}).get("document_id")
                if doc_id:
                    doc = self.document_store.get_document(doc_id)
                    if doc:
                        result["document"] = doc.get("filename")
                        result["document_metadata"] = doc.get("metadata")

            return results
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []

    async def rerank_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        return sorted(results, key=lambda x: x.get("similarity", 0), reverse=True)[:top_k]
