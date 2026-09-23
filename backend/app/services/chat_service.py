"""
Orchestrates the full chat pipeline:

    message -> intent classification -> knowledge retrieval OR
    availability tool -> AI provider (only for knowledge) ->
    structured ChatResponse

This is where the hallucination-prevention design comes together:
- Availability intent never touches the AI provider at all.
- Knowledge intent only calls the AI provider when retrieval found
  something relevant; an empty retrieval result returns the fixed
  fallback message directly.
- Any AI provider failure is caught and converted into a safe,
  fixed error message -- the caller never sees a raw exception.
"""
from __future__ import annotations

import re
from datetime import date as date_cls

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import ChatRequest, ChatResponse, ConversationTurn, MessageRole, ResponseType
from app.services.ai_provider import AIProvider, AIProviderError
from app.services.groq_provider import GroqProvider
from app.services.intent import Intent, classify_intent, extract_availability_params
from app.services.knowledge_base import retrieve
from app.services.mock_provider import MockAIProvider
from app.tools.availability import AvailabilityValidationError, check_availability

logger = get_logger(__name__)

FALLBACK_MESSAGE = (
    "I'm sorry, I don't have enough information in the hotel knowledge base "
    "to answer that reliably. Please try asking about check-in/check-out, "
    "rooms, amenities, breakfast, parking, pets, or cancellation policy."
)
PROVIDER_ERROR_MESSAGE = "I'm having trouble processing that right now. Please try again."
AVAILABILITY_INFO_NEEDED_MESSAGE = (
    "I'd be happy to check availability! Could you tell me your check-in date, "
    "check-out date (YYYY-MM-DD), and number of guests? You can also use the "
    "availability form below."
)
INVALID_DATE_MESSAGE = (
    "Please provide a valid check-in and check-out date, with check-out after check-in."
)
AVAILABILITY_SERVICE_FAILURE_MESSAGE = (
    "I couldn't check room availability right now. Please try again in a moment."
)

_PRONOUN_PATTERN = re.compile(r"\b(it|its|it's|that|this|they|them|those|these)\b", re.IGNORECASE)

# Cache provider instances per AI_PROVIDER value so we don't reconstruct
# (or re-validate config for) a provider on every single request.
_provider_cache: dict[str, AIProvider] = {}


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    if settings.AI_PROVIDER not in _provider_cache:
        if settings.AI_PROVIDER == "groq":
            _provider_cache[settings.AI_PROVIDER] = GroqProvider(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL,
                max_context_turns=settings.MAX_CONTEXT_TURNS,
            )
        else:
            _provider_cache[settings.AI_PROVIDER] = MockAIProvider()
    return _provider_cache[settings.AI_PROVIDER]


def _build_retrieval_query(message: str, conversation: list[ConversationTurn]) -> str:
    """
    Deterministic, rule-based coreference handling: if the current
    message leans on a pronoun ("its timings?") and there is prior
    conversation, fold the guest's previous message into the retrieval
    query so we search for the right topic. This keeps context
    resolution explainable -- no LLM guesswork about what "it" means.
    """
    if not conversation or not _PRONOUN_PATTERN.search(message):
        return message

    previous_user_messages = [t.content for t in conversation if t.role == MessageRole.user]
    if not previous_user_messages:
        return message

    return f"{previous_user_messages[-1]} {message}"


def _handle_availability_intent(message: str, conversation: list[ConversationTurn]) -> ChatResponse:
    check_in_str, check_out_str, guests = extract_availability_params(message)

    if not (check_in_str and check_out_str and guests):
        logger.info("availability_intent_missing_params")
        return ChatResponse(message=AVAILABILITY_INFO_NEEDED_MESSAGE, type=ResponseType.availability)

    try:
        check_in = date_cls.fromisoformat(check_in_str)
        check_out = date_cls.fromisoformat(check_out_str)
    except ValueError:
        return ChatResponse(message=INVALID_DATE_MESSAGE, type=ResponseType.fallback)

    try:
        result = check_availability(check_in, check_out, guests)
        return ChatResponse(message=result.message, type=ResponseType.availability, availability=result)
    except AvailabilityValidationError as e:
        return ChatResponse(message=str(e), type=ResponseType.fallback)
    except Exception:  # pragma: no cover - defensive fallback
        logger.error("availability_lookup_failed_in_chat")
        return ChatResponse(message=AVAILABILITY_SERVICE_FAILURE_MESSAGE, type=ResponseType.error)


def _handle_knowledge_intent(message: str, conversation: list[ConversationTurn]) -> ChatResponse:
    query = _build_retrieval_query(message, conversation)
    # A single best match keeps replies focused. Returning several partial
    # keyword matches made the mock provider concatenate unrelated facts
    # (for example, room details followed by Wi-Fi information).
    context = retrieve(query, top_k=1)

    if not context:
        logger.info("no_kb_match_returning_fallback")
        return ChatResponse(message=FALLBACK_MESSAGE, type=ResponseType.fallback)

    provider = get_ai_provider()
    try:
        answer = provider.generate_response(message, context, conversation)
        return ChatResponse(
            message=answer,
            type=ResponseType.knowledge,
            sources=[snippet["source"] for snippet in context],
        )
    except AIProviderError as e:
        logger.error("ai_provider_failed error=%s", str(e))
        return ChatResponse(message=PROVIDER_ERROR_MESSAGE, type=ResponseType.error)


def handle_chat(payload: ChatRequest) -> ChatResponse:
    intent = classify_intent(payload.message)
    logger.info("intent_classified intent=%s", intent.value)

    if intent == Intent.AVAILABILITY:
        return _handle_availability_intent(payload.message, payload.conversation)
    return _handle_knowledge_intent(payload.message, payload.conversation)
