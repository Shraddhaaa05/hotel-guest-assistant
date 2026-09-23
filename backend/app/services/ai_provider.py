"""
Abstract interface every AI provider must implement.

The chat service depends only on this interface, never on a concrete
provider. Swapping AI_PROVIDER=mock for AI_PROVIDER=groq (or adding a
new provider later) requires no changes outside this file's contract.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.schemas import ConversationTurn


class AIProviderError(Exception):
    """Raised when a provider cannot produce a response (timeout, missing key, API error)."""


class AIProvider(ABC):
    @abstractmethod
    def generate_response(
        self,
        message: str,
        context: list[dict],
        history: list[ConversationTurn],
    ) -> str:
        """
        Generate a natural-language answer to `message`, grounded ONLY
        in `context` (retrieved knowledge base snippets) and aware of
        `history` (recent conversation turns, for pronoun/follow-up
        continuity). Must raise AIProviderError on failure rather than
        returning a guessed answer.
        """
        raise NotImplementedError
