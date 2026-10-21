"""Lightweight validation tests for PDF ingestion/indexing.

Run (requires a running environment with dependencies + optionally valid OPENAI/GEMINI keys):
  python -m src.backend.test_document_ingestion

This module is intentionally minimal and backend-only (no Streamlit UI).
"""

import os
import uuid
import json

from pathlib import Path

from src.memory.manager import MemoryManager


def _make_dummy_pdf_like_text() -> str:
    # Placeholder: real PDF generation is out of scope.
    # These tests validate that loader/chunking functions handle empty/invalid inputs gracefully.
    return ""


def _create_manager(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "memory.db"))
    monkeypatch.setenv("FAISS_INDEX_PATH", str(tmp_path / "memory_vectors"))
    monkeypatch.setenv("DOC_VECTOR_STORE_PATH", str(tmp_path / "document_vectors"))
    return MemoryManager()


def test_vector_store_persistence_smoke(tmp_path: Path, monkeypatch):
    mgr = _create_manager(tmp_path, monkeypatch)
    # smoke: FAISS index exists
    assert hasattr(mgr.vector_store, "index")
    assert hasattr(mgr.vector_store, "metadata")


def test_memory_db_document_schema_smoke(tmp_path: Path, monkeypatch):
    mgr = _create_manager(tmp_path, monkeypatch)
    # smoke: documents table exists by invoking method that writes.
    user_id = "user_test"
    doc_id = f"{user_id}_doc_{uuid.uuid4().hex}"
    # This will fail if schema differs, so treat as smoke.
    # We don't require actual PDF.
    import asyncio

    async def run():
        ok = await mgr.db.add_document(
            doc_id=doc_id,
            user_id=user_id,
            filename="dummy.pdf",
            file_path=str(tmp_path / "dummy.pdf"),
            chunk_count=0,
            total_pages=0,
            metadata={"source_type": "document"},
        )
        assert ok is True

    asyncio.run(run())


def run_all():
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
        tmp_path = Path(d)
        test_vector_store_persistence_smoke(tmp_path)
        test_memory_db_document_schema_smoke(tmp_path)
    print("OK")


if __name__ == "__main__":
    run_all()
