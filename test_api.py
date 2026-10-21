"""Smoke-test the running backend's health, memory, search, and chat endpoints."""

import json
import uuid

import requests


API_BASE_URL = "http://127.0.0.1:8000/api"
HEALTH_URL = "http://127.0.0.1:8000/health"
REQUEST_TIMEOUT = 120


def request_json(method: str, url: str, **kwargs):
    response = requests.request(
        method,
        url,
        timeout=REQUEST_TIMEOUT,
        **kwargs,
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    user_id = f"smoke_test_{uuid.uuid4().hex[:8]}"
    memory_content = "Smoke test memory: learning about AI and semantic search."

    try:
        health = request_json("GET", HEALTH_URL)
        print("Backend health:")
        print(json.dumps(health, indent=2))

        added = request_json(
            "POST",
            f"{API_BASE_URL}/memory/add",
            json={
                "user_id": user_id,
                "content": memory_content,
                "memory_type": "learning",
            },
        )
        if not added.get("success"):
            raise RuntimeError(f"Memory was not saved: {added}")
        print(f"Memory saved with id {added.get('memory_id')}.")

        search = request_json(
            "POST",
            f"{API_BASE_URL}/memory/search",
            json={
                "user_id": user_id,
                "query": "AI semantic search",
                "limit": 5,
            },
        )
        if not search.get("memories"):
            raise RuntimeError(f"Saved memory was not searchable: {search}")
        print(f"Memory search returned {search['count']} result(s).")

        chat = request_json(
            "POST",
            f"{API_BASE_URL}/chat/send",
            json={
                "user_id": user_id,
                "message": "What have I been learning?",
                "include_memories": True,
            },
        )
        if not chat.get("assistant_response"):
            raise RuntimeError(f"Chat returned no assistant response: {chat}")
        print("Chat response:")
        print(chat["assistant_response"])
        print("\nAll API smoke checks passed.")
        return 0
    except (requests.RequestException, ValueError, RuntimeError) as error:
        print(f"API smoke check failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
