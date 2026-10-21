import asyncio

import faiss
import numpy as np

from src.backend import main
from src.backend.routes import memory_routes
from src.llm.assistant import PersonalAIAssistant
from src.memory.vector_store import FAISSVectorStore


def test_vector_search_returns_filtered_results():
    class FakeEmbedder:
        def encode(self, texts, convert_to_numpy=True):
            return np.array([[1.0, 0.0]], dtype="float32")

    store = FAISSVectorStore.__new__(FAISSVectorStore)
    store.embedder = FakeEmbedder()
    store.index = faiss.IndexFlatL2(2)
    store.index.add(np.array([[1.0, 0.0]], dtype="float32"))
    store.metadata = [
        {
            "user_id": "test-user",
            "type": "learning",
            "content": "A remembered fact",
        }
    ]

    results = store.search(
        "A remembered fact",
        k=5,
        filters={"user_id": "test-user"},
    )

    assert len(results) == 1
    assert results[0]["content"] == "A remembered fact"


def test_memory_endpoint_awaits_storage_and_returns_id(monkeypatch):
    class FakeMemoryManager:
        async def add_memory(self, **values):
            self.values = values
            return 42

    manager = FakeMemoryManager()
    monkeypatch.setattr(main, "memory_manager", manager)

    result = asyncio.run(
        memory_routes.add_memory(
            memory_routes.MemoryRequest(
                user_id="test-user",
                content="A remembered fact",
                memory_type="note",
                metadata={"source": "test"},
            )
        )
    )

    assert result["success"] is True
    assert result["memory_id"] == 42
    assert manager.values["metadata"] == {"source": "test"}


def test_assistant_awaits_database_and_persists_chat():
    class FakeVectorStore:
        def search(self, *args, **kwargs):
            return []

        def search_documents(self, *args, **kwargs):
            return []

    class FakeDatabase:
        def __init__(self):
            self.saved = None

        async def get_user_profile(self, user_id):
            return {"name": "Test User"}

        async def add_conversation(self, **values):
            self.saved = values
            return True

    class FakeLLM:
        async def generate_response_with_context(self, **values):
            assert values["user_profile"] == {"name": "Test User"}
            return "A working response"

    database = FakeDatabase()
    assistant = PersonalAIAssistant(
        llm_handler=FakeLLM(),
        vector_store=FakeVectorStore(),
        memory_db=database,
    )

    result = asyncio.run(
        assistant.generate_response("test-user", "Hello")
    )

    assert result["response"] == "A working response"
    assert database.saved["user_message"] == "Hello"
