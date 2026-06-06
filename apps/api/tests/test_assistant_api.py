"""Assistant API tests — RBAC, ask round-trip, history, 404, validation."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

_VIEWER = {"X-Tenant-Id": "acme", "X-Role": "viewer"}


def test_requires_auth(db_client: TestClient) -> None:
    assert db_client.post("/assistant/ask", json={"question": "hi"}).status_code == 401
    assert db_client.get("/assistant/conversations").status_code == 401


def test_ask_returns_answer_and_persists(db_client: TestClient) -> None:
    resp = db_client.post(
        "/assistant/ask", headers=_VIEWER, json={"question": "How does onboarding work?"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"]["intent"] == "service"
    assert "confidence" in body["answer"]
    conversation_id = body["conversation_id"]

    # The conversation is now retrievable with the user + assistant messages.
    detail = db_client.get(
        f"/assistant/conversations/{conversation_id}", headers=_VIEWER
    )
    assert detail.status_code == 200
    messages = detail.json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]

    listed = db_client.get("/assistant/conversations", headers=_VIEWER).json()
    assert listed["conversations"][0]["id"] == conversation_id


def test_missing_conversation_404(db_client: TestClient) -> None:
    resp = db_client.get(
        f"/assistant/conversations/{uuid.uuid4()}", headers=_VIEWER
    )
    assert resp.status_code == 404


def test_blank_question_422(db_client: TestClient) -> None:
    resp = db_client.post("/assistant/ask", headers=_VIEWER, json={"question": ""})
    assert resp.status_code == 422
