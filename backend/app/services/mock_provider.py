"""
Mock AI provider.

Used when AI_PROVIDER=mock (the default). Makes no network calls and
requires no API key, so the whole application runs locally out of the
box. It composes a response directly from the retrieved knowledge base
snippets -- since it never generates text beyond what retrieval found,
it is hallucination-proof by construction.
"""
from __future__ import annotations

from app.models.schemas import ConversationTurn
from app.services.ai_provider import AIProvider


class MockAIProvider(AIProvider):
    def generate_response(
        self,
        message: str,
        context: list[dict],
        history: list[ConversationTurn],
    ) -> str:
        # chat_service guarantees context is non-empty before calling a
        # provider, but we guard defensively anyway.
        if not context:
            return (
                "I'm sorry, I don't have enough information in the hotel "
                "knowledge base to answer that reliably."
            )

        if len(context) == 1:
            return context[0]["text"]

        # Multiple relevant snippets: join them into one coherent answer.
        return " ".join(snippet["text"] for snippet in context)
