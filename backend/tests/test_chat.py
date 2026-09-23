"""
End-to-end tests for POST /api/chat, running with AI_PROVIDER=mock
(the default), covering the scenarios called out in the assignment:
normal question, follow-up/context, availability via natural language,
and a hallucination-attempt question that must fall back safely.
"""


def test_chat_answers_known_faq_question(client):
    response = client.post(
        "/api/chat",
        json={"message": "Does the hotel have a swimming pool?", "conversation": []},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "knowledge"
    assert "pool" in data["message"].lower()
    assert len(data["sources"]) > 0


def test_chat_answers_breakfast_question(client):
    response = client.post(
        "/api/chat",
        json={"message": "Is breakfast included?", "conversation": []},
    )
    data = response.json()
    assert data["type"] == "knowledge"
    assert "breakfast" in data["message"].lower()


def test_chat_answers_room_suitability_question(client):
    response = client.post(
        "/api/chat",
        json={"message": "Which room is suitable for a family of four?", "conversation": []},
    )
    data = response.json()
    assert data["type"] == "knowledge"
    assert "family" in data["message"].lower() or "suite" in data["message"].lower()


def test_chat_answers_broad_plural_policies_question(client):
    """
    Regression test for a real bug found in manual testing: "what are
    the policies" (plural) previously fell back to the 'I don't have
    enough information' message because retrieval didn't normalize
    "policies" to "policy" before matching.
    """
    response = client.post(
        "/api/chat",
        json={"message": "what are the policies", "conversation": []},
    )
    data = response.json()
    assert data["type"] == "knowledge"


def test_chat_answers_policy_question(client):
    response = client.post(
        "/api/chat",
        json={"message": "What is the cancellation policy?", "conversation": []},
    )
    data = response.json()
    assert data["type"] == "knowledge"
    assert "cancel" in data["message"].lower() or "48 hours" in data["message"].lower()


def test_chat_follow_up_question_resolves_pronoun_via_context(client):
    """
    'Do you have a pool?' -> 'What are its timings?' must resolve
    'its' to the pool using the previous turn, without any LLM call
    (mock provider has no coreference ability of its own).
    """
    first = client.post(
        "/api/chat",
        json={"message": "Do you have a pool?", "conversation": []},
    ).json()

    conversation = [
        {"role": "user", "content": "Do you have a pool?"},
        {"role": "assistant", "content": first["message"]},
    ]
    follow_up = client.post(
        "/api/chat",
        json={"message": "What are its timings?", "conversation": conversation},
    )
    data = follow_up.json()
    assert data["type"] == "knowledge"
    assert "6:00 am" in data["message"].lower() or "9:00 pm" in data["message"].lower()


def test_chat_hallucination_attempt_falls_back_instead_of_inventing(client):
    """A question about something not in the knowledge base at all must
    never be answered by a guessed LLM response -- it must fall back."""
    response = client.post(
        "/api/chat",
        json={"message": "Do you have a helicopter landing pad?", "conversation": []},
    )
    data = response.json()
    assert data["type"] == "fallback"


def test_chat_ambiguous_question_still_gets_a_safe_response(client):
    response = client.post(
        "/api/chat",
        json={"message": "tell me about it", "conversation": []},
    )
    assert response.status_code == 200
    # No prior context to resolve "it" against -> should not crash, and
    # with nothing relevant retrieved, should fall back safely.
    data = response.json()
    assert data["type"] in ("fallback", "knowledge")


def test_chat_availability_via_natural_language_with_full_params(client):
    response = client.post(
        "/api/chat",
        json={
            "message": "Do you have rooms available for 3 guests from 2026-10-10 to 2026-10-12?",
            "conversation": [],
        },
    )
    data = response.json()
    assert data["type"] == "availability"
    assert data["availability"] is not None
    assert data["availability"]["guests"] == 3


def test_chat_availability_via_natural_language_missing_params_asks_for_more(client):
    response = client.post(
        "/api/chat",
        json={"message": "Is there any availability?", "conversation": []},
    )
    data = response.json()
    assert data["type"] == "availability"
    assert data["availability"] is None
    assert "check-in" in data["message"].lower() or "date" in data["message"].lower()


def test_chat_availability_via_natural_language_invalid_dates(client):
    response = client.post(
        "/api/chat",
        json={
            "message": "Rooms for 2 guests from 2026-10-12 to 2026-10-10?",
            "conversation": [],
        },
    )
    data = response.json()
    assert data["type"] == "fallback"


def test_chat_rejects_empty_message(client):
    response = client.post(
        "/api/chat",
        json={"message": "   ", "conversation": []},
    )
    assert response.status_code == 422


def test_chat_provider_failure_returns_safe_fallback_message(client, monkeypatch):
    """Simulate the AI provider throwing (e.g. network/model failure) and
    confirm the client gets a clean, fixed error message -- never a
    stack trace and never an invented answer."""
    from app.services import chat_service
    from app.services.ai_provider import AIProviderError

    class BrokenProvider:
        def generate_response(self, message, context, history):
            raise AIProviderError("simulated provider outage")

    monkeypatch.setattr(chat_service, "get_ai_provider", lambda: BrokenProvider())

    response = client.post(
        "/api/chat",
        json={"message": "Is breakfast included?", "conversation": []},
    )
    data = response.json()
    assert data["type"] == "error"
    assert "trouble" in data["message"].lower()
