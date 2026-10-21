# TODO — Personal AI Memory Assistant (Production-ready)

## Step 1 — Fix chat pipeline + RAG wiring (Backend only)
- [x] Align LLM calls (chat route → LLMHandler method)
- [x] Ensure chat retrieval pulls:
  - [x] relevant memories (FAISS)
  - [ ] relevant PDF chunks (FAISS/doc store) 
- [x] Build context payload including sources
- [ ] Persist conversation + sources to SQLite
- [ ] Add logging + validation + error handling
- [ ] Add quick local validation tests (manual or lightweight script)


## Step 2 — Implement PDF upload + indexing endpoints
- [x] Add `/api/documents/upload` endpoint
- [x] Save uploaded PDF to disk
- [ ] Extract text + chunks (PyPDFLoader/PDFLoader)

- [ ] Store document metadata in SQLite
- [ ] Embed chunks and index them in FAISS with document metadata
- [ ] Add list/delete endpoints as needed
- [ ] Validation tests for end-to-end retrieval accuracy

## Step 3 — Streamlit UI updates (only after Step 1 & 2 verified)
- [ ] Implement PDF upload UI and retrieval visualization
- [ ] Add metrics: retrieved counts, similarity scores, latency
- [ ] Add clear memory + download DB

## Step 4 — Docs & portfolio claims
- [ ] Update README/ARCHITECTURE/schema
- [ ] Add architecture diagram and example flows

