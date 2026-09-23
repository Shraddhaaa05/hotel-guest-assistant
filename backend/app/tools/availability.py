"""
Deterministic availability tool.

This module is intentionally free of any AI/LLM code. It is a pure
function over the hotel's room data plus a small mock inventory rule.
The LLM is never allowed to produce availability numbers, prices, or
room lists -- those always come from here.

Mock inventory rule (documented, not hidden):
For each room, we simulate day-by-day bookings using a deterministic
hash of (room id, date). This gives repeatable, realistic-looking
availability without needing a real reservations database, which is
appropriate for a demo/assignment of this scope.
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta

from app.models.schemas import AvailabilityResponse, RoomAvailability
from app.services.knowledge_base import get_hotel_data


class AvailabilityValidationError(ValueError):
    """Raised when the caller supplies invalid availability inputs."""


def _is_room_booked_on_date(room_id: str, on_date: date) -> bool:
    """
    Deterministic mock "is this room's inventory exhausted on this date"
    check. Same room + same date always returns the same result, so the
    app behaves consistently across repeated requests -- useful for
    demos and for tests.
    """
    key = f"{room_id}:{on_date.isoformat()}"
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()
    # Roughly 1-in-4 chance a given room is sold out on a given date.
    return int(digest, 16) % 4 == 0


def _room_available_for_range(room_id: str, check_in: date, check_out: date) -> bool:
    current = check_in
    while current < check_out:
        if _is_room_booked_on_date(room_id, current):
            return False
        current += timedelta(days=1)
    return True


def check_availability(
    check_in: date, check_out: date, adults: int
) -> AvailabilityResponse:
    """
    The single source of truth for room availability. Deterministic,
    side-effect free, and independent of any LLM call.
    """
    today = date.today()

    if check_in < today:
        raise AvailabilityValidationError(
            "Check-in date cannot be in the past."
        )
    if check_out <= check_in:
        raise AvailabilityValidationError(
            "Check-out date must be after the check-in date."
        )
    if adults < 1 or adults > 8:
        raise AvailabilityValidationError(
            "Number of guests must be between 1 and 8."
        )

    nights = (check_out - check_in).days
    hotel_data = get_hotel_data()

    matching_rooms: list[RoomAvailability] = []
    for room in hotel_data["rooms"]:
        if room["maxAdults"] < adults:
            continue
        if not _room_available_for_range(room["id"], check_in, check_out):
            continue
        matching_rooms.append(
            RoomAvailability(
                id=room["id"],
                name=room["name"],
                bedConfig=room["bedConfig"],
                capacity=room["maxAdults"],
                pricePerNight=room["pricePerNight"],
                currency=room["currency"],
                amenities=room["amenities"],
            )
        )

    available = len(matching_rooms) > 0
    if available:
        message = (
            f"We found {len(matching_rooms)} room type(s) available for "
            f"{adults} guest(s) from {check_in.isoformat()} to {check_out.isoformat()}."
        )
    else:
        message = (
            f"Sorry, we don't have any rooms available for {adults} guest(s) "
            f"from {check_in.isoformat()} to {check_out.isoformat()}. "
            "Please try different dates or a smaller party size."
        )

    return AvailabilityResponse(
        available=available,
        checkIn=check_in,
        checkOut=check_out,
        guests=adults,
        nights=nights,
        rooms=matching_rooms,
        message=message,
    )
