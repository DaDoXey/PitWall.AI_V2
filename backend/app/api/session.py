"""GET /api/session — dati demo di sessione + telemetria (sorgente: core/demo_data)."""

from fastapi import APIRouter

from app.core import demo_data as dd

router = APIRouter()


@router.get("/session")
def get_session():
    return {
        "session": dd.SESSION,
        "tyre_labels": dd.TYRE_LABELS,
        "temp": {
            "series": dd.TYRE_TEMP_SERIES,
            "max": dd.TYRE_TEMP_MAX,
            "limit": dd.TEMP_LIMIT,
            "scale": list(dd.TEMP_SCALE),
        },
        "pressure": {
            "hot": dd.HOT_PRESSURES,
            "hot_window": list(dd.HOT_PRESS_WINDOW),
            "hot_series": dd.HOT_PRESS_SERIES,
            "cold": dd.COLD_PRESSURES,
            "cold_window": list(dd.COLD_PRESS_WINDOW),
            "cold_amber_margin": dd.COLD_PRESS_AMBER_MARGIN,
            "avg_hot": dd.PRESS_AVG_HOT,
        },
        "fuel_per_lap": dd.FUEL_PER_LAP,
        "lap_times": dd.LAP_TIMES,
        "laps": dd.lap_axis(),
        "suggested_params": sorted(dd.SUGGESTED_PARAMS),
    }
