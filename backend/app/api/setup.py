"""GET /api/setup-params — 5 sezioni × 49 parametri ACC con override per vettura/circuito."""

from fastapi import APIRouter

from app.core.setup_params import get_params_for_car

router = APIRouter()


@router.get("/setup-params")
def get_setup_params(car: str | None = None, track: str | None = None):
    return get_params_for_car(car, track)
