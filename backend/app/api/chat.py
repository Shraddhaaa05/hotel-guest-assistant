"""
Chat endpoint.

The endpoint itself stays thin -- all pipeline logic (intent
classification, retrieval, availability tool, AI provider dispatch,
fallback handling) lives in app.services.chat_service so it can be
unit-tested independently of HTTP.
"""
from fastapi import APIRouter

from app.core.logging import get_logger
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import handle_chat

router = APIRouter(tags=["chat"])
logger = get_logger(__name__)


@router.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    logger.info("chat_message_received length=%d", len(payload.message))
    return handle_chat(payload)
