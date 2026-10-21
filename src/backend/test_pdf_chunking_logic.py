"""Unit-ish tests for PDFLoader chunking logic.

Note: Full PDF extraction requires a valid PDF file. These tests validate:
- chunker returns non-empty chunks when text is provided
- loader raises/handles errors for missing/corrupted PDFs.
"""

from pathlib import Path
import uuid

from src.memory.document_processor import PDFLoader


def test_chunk_text_basic():
    loader = PDFLoader(chunk_size=50, chunk_overlap=10)
    text = ("Sentence. " * 200).strip()
    chunks = loader._chunk_text(text)
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all("content" in c for c in chunks)


def test_load_pdf_missing_file_raises(tmp_path: Path):
    loader = PDFLoader()
    missing = tmp_path / f"missing_{uuid.uuid4().hex}.pdf"
    try:
        loader.load_pdf(str(missing))
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


def run_all():
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as d:
        tmp_path = Path(d)
        test_chunk_text_basic()
        test_load_pdf_missing_file_raises(tmp_path)
    print("OK")


if __name__ == "__main__":
    run_all()

