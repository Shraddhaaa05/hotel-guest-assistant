from datetime import date, timedelta

import pytest

from app.tools.availability import AvailabilityValidationError, check_availability

TODAY = date.today()
CHECK_IN = TODAY + timedelta(days=10)
CHECK_OUT = TODAY + timedelta(days=12)


# ---------------------------------------------------------------------------
# Unit tests directly against the pure function (no HTTP layer involved)
# ---------------------------------------------------------------------------

def test_valid_availability_request_returns_matching_rooms():
    result = check_availability(CHECK_IN, CHECK_OUT, adults=2)
    assert result.checkIn == CHECK_IN
    assert result.checkOut == CHECK_OUT
    assert result.guests == 2
    assert result.nights == 2
    # Every returned room must actually accommodate 2 adults.
    for room in result.rooms:
        assert room.capacity >= 2


def test_family_of_four_only_matches_family_suite():
    result = check_availability(CHECK_IN, CHECK_OUT, adults=4)
    for room in result.rooms:
        assert room.capacity >= 4
        assert room.name == "Family Suite"


def test_checkout_before_checkin_raises_validation_error():
    with pytest.raises(AvailabilityValidationError):
        check_availability(CHECK_OUT, CHECK_IN, adults=2)


def test_checkin_in_the_past_raises_validation_error():
    with pytest.raises(AvailabilityValidationError):
        check_availability(TODAY - timedelta(days=1), TODAY + timedelta(days=1), adults=2)


def test_too_many_guests_raises_validation_error():
    with pytest.raises(AvailabilityValidationError):
        check_availability(CHECK_IN, CHECK_OUT, adults=9)


def test_result_is_deterministic_across_calls():
    """Same inputs must always produce the same availability result."""
    result_1 = check_availability(CHECK_IN, CHECK_OUT, adults=2)
    result_2 = check_availability(CHECK_IN, CHECK_OUT, adults=2)
    assert [r.id for r in result_1.rooms] == [r.id for r in result_2.rooms]
    assert result_1.available == result_2.available


# ---------------------------------------------------------------------------
# HTTP-level tests against POST /api/availability
# ---------------------------------------------------------------------------

def test_availability_endpoint_happy_path(client):
    response = client.post(
        "/api/availability",
        json={
            "checkIn": CHECK_IN.isoformat(),
            "checkOut": CHECK_OUT.isoformat(),
            "adults": 2,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "rooms" in data
    assert data["guests"] == 2


def test_availability_endpoint_rejects_invalid_dates(client):
    response = client.post(
        "/api/availability",
        json={
            "checkIn": CHECK_OUT.isoformat(),
            "checkOut": CHECK_IN.isoformat(),  # checkout before checkin
            "adults": 2,
        },
    )
    assert response.status_code == 400
    assert "check-out" in response.json()["detail"].lower()


def test_availability_endpoint_rejects_invalid_guest_count(client):
    response = client.post(
        "/api/availability",
        json={
            "checkIn": CHECK_IN.isoformat(),
            "checkOut": CHECK_OUT.isoformat(),
            "adults": 0,
        },
    )
    # Pydantic field validation (ge=1) catches this before it reaches the tool.
    assert response.status_code == 422


def test_availability_endpoint_rejects_malformed_date(client):
    response = client.post(
        "/api/availability",
        json={
            "checkIn": "not-a-date",
            "checkOut": CHECK_OUT.isoformat(),
            "adults": 2,
        },
    )
    assert response.status_code == 422
