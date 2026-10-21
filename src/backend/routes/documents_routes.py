"""documents_routes.py

API endpoints for uploading PDFs and building a document RAG index.

Step 2 implementation notes:
- Upload endpoint extracts pages and chunks using PDFLoader.
- For Step 2.5, indexing must eventually go into the dedicated
  LangChain FAISS document vector store (data/faiss_documents/).

Note:
This module is currently focused on restoring correctness and
page-aware extraction. Dedicated vector indexing + SHA256 duplicate
prevention will be added in the next pass.
"""

import os
import uuid
import time
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_PDF_BYTES = int(os.getenv("MAX_PDF_BYTES", str(10 * 1024 * 1024)))  # default 10MB
ALLOWED_MIME_PREFIXES = ("application/pdf",)


class UploadResponse(BaseModel):
    success: bool
    user_id: str
    uploaded: int
    indexed: int
    documents: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    timestamp: str


class DocumentListResponse(BaseModel):
    success: bool
    user_id: str
    documents: List[Dict[str, Any]]
    timestamp: str


@router.post("/upload", response_model=UploadResponse)
async def upload_pdfs(
    user_id: str,
    files: List[UploadFile] = File(...),
):
    """Upload one or more PDFs, extract text into chunks, and index into FAISS."""
    try:
        from ..main import memory_manager

        os.makedirs(os.path.join("data", "documents"), exist_ok=True)

        uploaded_docs: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        indexed = 0

        for upload in files:
            start = time.time()
            try:
                if not upload.filename:
                    raise ValueError("Missing filename")

                filename = upload.filename
                if not filename.lower().endswith(".pdf"):
                    raise ValueError(f"Invalid file extension (must be .pdf): {filename}")

                content_type = (upload.content_type or "").lower()
                if content_type and not content_type.startswith(ALLOWED_MIME_PREFIXES[0]):
                    logger.warning(f"Unexpected content_type for {filename}: {content_type}")

                # Validate size + read bytes
                size = 0
                chunks: List[bytes] = []
                while True:
                    data = await upload.read(1024 * 1024)
                    if not data:
                        break
                    size += len(data)
                    if size > MAX_PDF_BYTES:
                        raise ValueError(
                            f"File too large ({size} bytes). Max allowed: {MAX_PDF_BYTES} bytes"
                        )
                    chunks.append(data)

                file_bytes = b"".join(chunks)

                # Create file id + storage path
                upload_timestamp = str(int(time.time()))
                ext = os.path.splitext(filename)[1]
                doc_uid = uuid.uuid4().hex
                doc_id = f"{user_id}_doc_{upload_timestamp}_{doc_uid}"

                stored_filename = f"{doc_id}{ext}"
                stored_path = os.path.join("data", "documents", stored_filename)

                # Save to disk
                with open(stored_path, "wb") as f:
                    f.write(file_bytes)

                document_name = os.path.basename(filename)

                # Extract chunks (page-aware)
                pdf_info = memory_manager.pdf_loader.load_pdf(
                    stored_path,
                    document_id=doc_id,
                    document_name=document_name,
                    upload_timestamp=upload_timestamp,
                    source_type="document",
                )

                chunks_list = pdf_info.get("chunks", [])
                total_pages = pdf_info.get("total_pages", 0)

                chunk_texts: List[str] = []
                chunk_metadata: List[Dict[str, Any]] = []

                for c in chunks_list:
                    chunk_id = c.get("chunk_id")
                    content = c.get("content")
                    page_number = c.get("page_number", -1)

                    if not content or not content.strip():
                        continue

                    chunk_texts.append(content)
                    chunk_metadata.append(
                        {
                            "user_id": user_id,
                            "type": "document",
                            "document_id": doc_id,
                            "document_name": c.get("document_name") or document_name,
                            "page_number": page_number,
                            "chunk_id": chunk_id,
                            "upload_timestamp": c.get("upload_timestamp"),
                            "source_type": "document",
                            "content": content,
                        }
                    )

                if not chunk_texts:
                    raise ValueError("No extractable text chunks found (empty PDF?)")

                # Persist document metadata in SQLite
                added = await memory_manager.db.add_document(
                    doc_id=doc_id,
                    user_id=user_id,
                    filename=pdf_info.get("filename"),
                    file_path=stored_path,
                    chunk_count=len(chunk_texts),
                    total_pages=total_pages,
                    metadata={"source_type": "document", "original_title": pdf_info.get("title")},
                )
                if not added:
                    raise RuntimeError("Failed to write document metadata to SQLite")

                # Index into the main memory store so this document can be retrieved by chat.
                idx_ids = memory_manager.vector_store.add_texts(
                    texts=chunk_texts,
                    metadata=chunk_metadata,
                )
                indexed += len(idx_ids)

                # Also index into the dedicated document FAISS store used by debug-search.
                try:
                    memory_manager.document_vector_store.add_texts(
                        texts=chunk_texts,
                        metadatas=chunk_metadata,
                    )
                except Exception as e:
                    logger.warning(f"Document vector store indexing failed: {e}")

                uploaded_docs.append(
                    {
                        "document_id": doc_id,
                        "filename": pdf_info.get("filename"),
                        "stored_path": stored_path,
                        "chunk_count": len(chunk_texts),
                        "total_pages": total_pages,
                        "indexed_chunks": len(idx_ids),
                        "upload_time_ms": int((time.time() - start) * 1000),
                    }
                )

            except Exception as e:
                logger.exception("PDF upload/indexing failed")
                errors.append(
                    {
                        "filename": getattr(upload, "filename", None),
                        "error": str(e),
                    }
                )

        return UploadResponse(
            success=True if not errors else False,
            user_id=user_id,
            uploaded=len(files),
            indexed=indexed,
            documents=uploaded_docs,
            errors=errors,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/{user_id}", response_model=DocumentListResponse)
async def list_documents(user_id: str):
    """List indexed documents for a user."""
    try:
        from ..main import memory_manager

        docs = await memory_manager.db.get_user_documents(user_id)
        return DocumentListResponse(
            success=True,
            user_id=user_id,
            documents=docs,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

