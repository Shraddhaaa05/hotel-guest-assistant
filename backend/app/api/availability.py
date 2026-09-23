from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.models.schemas import AvailabilityRequest, AvailabilityResponse
from app.tools.availability import AvailabilityValidationError, check_availability

router = APIRouter(tags=["availability"])
logger = get_logger(__name__)


@router.post("/api/availability", response_model=AvailabilityResponse)
def get_availability(payload: AvailabilityRequest) -> AvailabilityResponse:
    """
    Deterministic room availability lookup. This endpoint never calls
    an LLM -- results come entirely from app.tools.availability.
    """
    try:
        result = check_availability(
            check_in=payload.checkIn,
            check_out=payload.checkOut,
            adults=payload.adults,
        )
        logger.info(
            "availability_checked check_in=%s check_out=%s adults=%s available=%s",
            payload.checkIn, payload.checkOut, payload.adults, result.available,
        )
        return result
    except AvailabilityValidationError as e:
        logger.warning("availability_validation_failed reason=%s", str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:  # pragma: no cover - defensive fallback
        logger.error("availability_lookup_failed error=%s", str(e))
        raise HTTPException(
            status_code=503,
            detail="I couldn't check room availability right now. Please try again in a moment.",
        ) from e
