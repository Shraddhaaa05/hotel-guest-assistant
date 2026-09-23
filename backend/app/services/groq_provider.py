"""
Groq AI provider.

Used when AI_PROVIDER=groq. Calls Groq's OpenAI-compatible chat
completions endpoint directly over HTTP (via httpx, already a
dependency) rather than pulling in a dedicated SDK -- keeps the
dependency footprint small for a demo-scale project.

The system prompt is the core hallucination guardrail: the model is
instructed to answer only from the supplied facts and to say so
explicitly when the facts don't cover the question.
"""
from __future__ import annotations

import httpx

from app.models.schemas import ConversationTurn
from app.services.ai_provider import AIProvider, AIProviderError

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT_TEMPLATE = (
    "You are a helpful, concise guest assistant for Grand Horizon Hotel. "
    "Answer only what the guest specifically asked, in one short response. "
    "Do not repeat the question or repeat your answer. Do not add unrelated "
    "amenities or extra facts. Use ONLY the facts listed below. "
    "Do not invent prices, policies, room availability, or any detail "
    "that is not present in the facts. If the facts do not fully answer "
    "the question, say plainly that you don't have that information and "
    "suggest the guest contact the front desk.\n\n"
    "FACTS:\n{facts}"
)


class GroqProvider(AIProvider):
    def __init__(self, api_key: str, model: str, max_context_turns: int = 4):
        self.api_key = api_key
        self.model = model
        self.max_context_turns = max_context_turns

    def generate_response(
        self,
        message: str,
        context: list[dict],
        history: list[ConversationTurn],
    ) -> str:
        if not self.api_key:
            raise AIProviderError(
                "AI_PROVIDER is set to 'groq' but GROQ_API_KEY is not configured."
            )

        facts = "\n".join(f"- {snippet['text']}" for snippet in context)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(facts=facts)

        messages = [{"role": "system", "content": system_prompt}]
        for turn in history[-self.max_context_turns:]:
            messages.append({"role": turn.role.value, "content": turn.content})
        messages.append({"role": "user", "content": message})

        try:
            response = httpx.post(
                GROQ_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 300,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPError as e:
            raise AIProviderError(f"Groq request failed: {e}") from e
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Unexpected Groq response shape: {e}") from e
