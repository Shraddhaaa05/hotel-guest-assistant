import pytest

from app.services.ai_provider import AIProviderError
from app.services.groq_provider import GroqProvider
from app.services.mock_provider import MockAIProvider


def test_mock_provider_returns_snippet_text_directly():
    provider = MockAIProvider()
    context = [{"text": "Check-in is at 2:00 PM.", "source": "FAQ", "score": 3}]
    answer = provider.generate_response("What time is check-in?", context, [])
    assert answer == "Check-in is at 2:00 PM."


def test_mock_provider_combines_multiple_snippets():
    provider = MockAIProvider()
    context = [
        {"text": "Fact one.", "source": "A", "score": 3},
        {"text": "Fact two.", "source": "B", "score": 2},
    ]
    answer = provider.generate_response("question", context, [])
    assert "Fact one." in answer
    assert "Fact two." in answer


def test_mock_provider_never_fabricates_when_context_is_empty():
    provider = MockAIProvider()
    answer = provider.generate_response("anything", [], [])
    assert "don't have enough information" in answer.lower()


def test_groq_provider_raises_without_api_key():
    provider = GroqProvider(api_key="", model="llama-3.1-8b-instant")
    context = [{"text": "Some fact.", "source": "FAQ", "score": 1}]
    with pytest.raises(AIProviderError):
        provider.generate_response("question", context, [])
