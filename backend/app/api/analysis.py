"""POST /api/analysis — analisi di Gigi a 4 sezioni.

Replica get_console_analysis della v1: demo-cache (nessuna rete) o LLM reale gated,
con fallback alla cache. La chiave resta lato server (app.config).
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app import config
from app.core import demo_data as dd
from app.core.demo_responses import is_demo_prompt, pick_demo_response

router = APIRouter()

_REQUIRED = ["## Diagnosi", "## Causa Meccanica", "## Correzione Setup", "## Note Aggiuntive"]


class AnalysisRequest(BaseModel):
    prompt: str


def _context(prompt: str) -> str:
    return (
        f"Auto: {dd.SESSION['car']}\nTracciato: {dd.SESSION['track']}\n"
        f"Condizioni: {dd.SESSION['stint']}\n\n"
        f"Telemetria (a caldo): temperature gomme max "
        f"FL {dd.TYRE_TEMP_MAX['fl']}°C, FR {dd.TYRE_TEMP_MAX['fr']}°C, "
        f"RL {dd.TYRE_TEMP_MAX['rl']}°C, RR {dd.TYRE_TEMP_MAX['rr']}°C; "
        f"pressioni a caldo {dd.HOT_PRESSURES}.\n\n"
        f"Feedback pilota: {prompt.strip()}"
    )


@router.post("/analysis")
def post_analysis(req: AnalysisRequest):
    prompt = req.prompt or ""

    # 1) demo-mode o prompt = scenario demo → cache (sempre, niente rete)
    if config.demo_mode() or is_demo_prompt(prompt):
        source = "demo" if config.demo_mode() else "cache"
        return {"question": prompt, "text": pick_demo_response(prompt), "source": source}

    # 2) LLM reale con fallback alla cache
    api_key = config.ANTHROPIC_API_KEY
    if not api_key:
        return {"question": prompt, "text": pick_demo_response(prompt), "source": "fallback"}
    try:
        from app.core.agent import get_ai_response

        resp = get_ai_response(
            user_input=_context(prompt), api_key=api_key,
            auto=dd.SESSION["car"], tracciato=dd.SESSION["track"],
        )
        ok = all(s in (resp or "") for s in _REQUIRED)
        return {
            "question": prompt,
            "text": resp if ok else pick_demo_response(prompt),
            "source": "api" if ok else "fallback",
        }
    except Exception:
        return {"question": prompt, "text": pick_demo_response(prompt), "source": "fallback"}
