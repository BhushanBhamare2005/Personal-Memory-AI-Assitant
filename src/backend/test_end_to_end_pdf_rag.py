"""End-to-end verification script for the RAG PDF workflow.

It performs:
1) Generates data/documents/test_rag_document.pdf automatically
2) Uploads the PDF to /api/documents/upload
3) Runs /api/documents/debug-search?q=<query>
4) Sends /api/chat/send with include_memories=false
5) Prints indexed chunk count, retrieved chunks, similarity scores, page numbers, citations, and LLM response.

Usage:
- Start backend: uvicorn src.backend.main:app --reload
- Run: python src/backend/test_end_to_end_pdf_rag.py

This script is intended to verify the RAG pipeline end-to-end.
"""

import argparse
import os
import json
import requests


def _escape_pdf_string(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def create_simple_pdf(path: str, pages: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Build a minimal PDF with one page per text entry.
    objects: list[bytes] = []

    def add_object(data: bytes) -> int:
        objects.append(data)
        return len(objects)

    font_obj = add_object(b"1 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")

    content_obj_nums = []
    for page_text in pages:
        escaped = _escape_pdf_string(page_text)
        content = (
            b"BT /F1 14 Tf 72 720 Td (" + escaped.encode("utf-8") + b") Tj ET\n"
        )
        content_obj = b"%d 0 obj << /Length %d >>\nstream\n" % (
            len(objects) + 1,
            len(content),
        ) + content + b"endstream\nendobj\n"
        content_obj_nums.append(add_object(content_obj))

    page_obj_nums = []
    pages_obj_num = 0
    for content_num in content_obj_nums:
        page_obj = b"%d 0 obj << /Type /Page /MediaBox [0 0 612 792] /Parent %d 0 R /Resources << /Font << /F1 1 0 R >> >> /Contents %d 0 R >> endobj\n" % (
            len(objects) + 1,
            0,
            content_num,
        )
        page_obj_nums.append(add_object(page_obj))

    pages_obj_num = add_object(
        b"%d 0 obj << /Type /Pages /Kids [" % (len(objects) + 1)
        + b" ".join([f"{num} 0 R".encode("utf-8") for num in page_obj_nums])
        + b"] /Count %d >> endobj\n" % len(page_obj_nums)
    )

    catalog_obj = add_object(
        b"%d 0 obj << /Type /Catalog /Pages %d 0 R >> endobj\n" % (len(objects) + 1, pages_obj_num)
    )

    # Fix page parent references now that pages_obj_num is known.
    fixed_objects: list[bytes] = []
    font_added = False
    content_index = 0
    page_index = 0
    for idx, obj in enumerate(objects, start=1):
        if idx == font_obj:
            fixed_objects.append(obj)
            font_added = True
        elif idx in page_obj_nums:
            page_count = page_obj_nums.index(idx)
            content_num = content_obj_nums[page_count]
            fixed_page_obj = b"%d 0 obj << /Type /Page /MediaBox [0 0 612 792] /Parent %d 0 R /Resources << /Font << /F1 1 0 R >> >> /Contents %d 0 R >> endobj\n" % (
                idx,
                pages_obj_num,
                content_num,
            )
            fixed_objects.append(fixed_page_obj)
        else:
            fixed_objects.append(obj)

    # Build xref table.
    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = b"".join(fixed_objects)
    xref_start = len(header) + len(body)
    xref_entries = [b"0000000000 65535 f \n"]
    offset = len(header)
    for obj in fixed_objects:
        xref_entries.append(f"{offset:010d} 00000 n \n".encode("utf-8"))
        offset += len(obj)

    xref = b"xref\n0 %d\n" % (len(fixed_objects) + 1)
    xref += b"".join(xref_entries)
    trailer = (
        b"trailer << /Size %d /Root %d 0 R >>\nstartxref\n%d\n"
        % (len(fixed_objects) + 1, catalog_obj, xref_start)
    ) + b"%%EOF\n"

    with open(path, "wb") as f:
        f.write(header)
        f.write(body)
        f.write(xref)
        f.write(trailer)


def pretty_print_upload(upload_json: dict) -> None:
    print(json.dumps(upload_json, indent=2))
    if upload_json.get("success"):
        print("Indexed chunks count:", upload_json.get("indexed", 0))
        for doc in upload_json.get("documents", []):
            print("Document:", doc.get("filename"))
            print("  stored_path:", doc.get("stored_path"))
            print("  chunk_count:", doc.get("chunk_count"))
            print("  indexed_chunks:", doc.get("indexed_chunks"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default="data/documents/test_rag_document.pdf")
    ap.add_argument(
        "--query",
        default="What method is used to prevent duplicate document indexing?",
    )
    ap.add_argument("--user_id", default="user_001")
    ap.add_argument("--api_base", default="http://localhost:8000/api")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        print(f"Creating test PDF at {args.pdf}")
        create_simple_pdf(
            args.pdf,
            [
                "MITAOE is located in Alandi, Pune.",
                "The Personal AI Memory Assistant uses LangChain and FAISS.",
                "The project stores document chunks with page-level metadata.",
                "SHA256 hashing is used to prevent duplicate document indexing.",
            ],
        )

    print("[A] Uploading PDF...")
    with open(args.pdf, "rb") as f:
        files = [("files", (os.path.basename(args.pdf), f, "application/pdf"))]
        resp = requests.post(
            f"{args.api_base}/documents/upload",
            params={"user_id": args.user_id},
            files=files,
            timeout=120,
        )

    print("Upload status:", resp.status_code)
    upload_json = resp.json()
    pretty_print_upload(upload_json)

    if not upload_json.get("success"):
        print("Upload failed; aborting end-to-end test.")
        return

    print("\n[B] Debug retrieval...")
    resp = requests.get(
        f"{args.api_base}/documents/debug-search",
        params={"q": args.query, "user_id": args.user_id},
        timeout=60,
    )
    print("Debug-search status:", resp.status_code)
    debug_json = resp.json()
    print(json.dumps(debug_json, indent=2))
    print("Retrieved chunks:", len(debug_json.get("chunks", [])))
    for chunk in debug_json.get("chunks", []):
        print("- page_number:", chunk.get("page_number"), "similarity_score:", chunk.get("similarity_score"))
        print("  text:", chunk.get("text"))

    print("\n[C] Chat answer (PDF-only) ...")
    resp = requests.post(
        f"{args.api_base}/chat/send",
        json={
            "user_id": args.user_id,
            "message": args.query,
            "include_memories": False,
        },
        timeout=120,
    )
    print("Chat status:", resp.status_code)
    chat_json = resp.json()
    print(json.dumps(chat_json, indent=2))

    print("\n[D] End-to-end test complete.")


if __name__ == "__main__":
    main()
