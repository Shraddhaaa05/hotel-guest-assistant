"""
Pydantic models shared across the API.

Keeping every request/response shape defined here (rather than scattered
across route files) makes the API contract easy to point to in an
interview and easy to keep frontend/backend in sync.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared enums
# ---------------------------------------------------------------------------

class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class ResponseType(str, Enum):
    knowledge = "knowledge"
    availability = "availability"
    fallback = "fallback"
    error = "error"


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

class AvailabilityRequest(BaseModel):
    checkIn: date
    checkOut: date
    adults: int = Field(..., ge=1, le=8)

    @field_validator("adults")
    @classmethod
    def adults_must_be_reasonable(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Number of guests must be at least 1.")
        return v


class RoomAvailability(BaseModel):
    id: str
    name: str
    bedConfig: str
    capacity: int
    pricePerNight: float
    currency: str
    amenities: list[str]


class AvailabilityResponse(BaseModel):
    available: bool
    checkIn: date
    checkOut: date
    guests: int
    nights: int
    rooms: list[RoomAvailability]
    message: str


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ConversationTurn(BaseModel):
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    conversation: list[ConversationTurn] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message must not be empty.")
        return v.strip()


class ChatResponse(BaseModel):
    message: str
    type: ResponseType
    sources: list[str] = Field(default_factory=list)
    availability: Optional[AvailabilityResponse] = None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    aiProvider: str
