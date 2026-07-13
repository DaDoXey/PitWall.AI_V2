"""POST /api/analysis — analisi di Gigi a 4 sezioni.

Replica get_console_analysis della v1: demo-cache (nessuna rete) o LLM reale gated,
con fallback alla cache. La chiave resta lato server (app.config).
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app import config
from app.core import demo_data as dd

# _DEMO_ROUTES è privato del modulo protetto ma è l'unica fonte di verità delle
# keyword: lo si legge (mai modificato) per capire se una domanda è nel perimetro
# della demo, senza duplicare la lista qui.
from app.core.demo_responses import _DEMO_ROUTES, is_demo_prompt, pick_demo_response

router = APIRouter()


def _in_scope(prompt: str) -> bool:
    """True se la domanda matcha una route della cache (o è il prompt demo canonico)."""
    p = (prompt or "").lower()
    return is_demo_prompt(prompt) or any(any(k in p for k in keys) for keys, _ in _DEMO_ROUTES)


def _off_topic_text() -> str:
    """Risposta onesta per domande fuori perimetro: niente default sul sovrasterzo
    (sembrerebbe un'allucinazione). Dati sessione letti da demo_data: coerenti
    per costruzione."""
    s = dd.SESSION
    return (
        f"Sono l'ingegnere di pista di questa sessione — {s['car']} a {s['track']}, "
        f"stint {s['stint'].lower()}, {s['laps']} giri — e analizzo solo i suoi dati.\n\n"
        "Chiedimi ad esempio di:\n"
        "- **gomme** e temperature\n"
        "- **pressioni** e finestra di lavoro\n"
        "- **freni**, staccate e bilanciamento\n"
        "- **carburante**, consumi e strategia\n"
        "- comportamento in curva: «l'auto scivola dietro», «va larga davanti»…"
    )

_REQUIRED = ["## Diagnosi", "## Causa Meccanica", "## Correzione Setup", "## Note Aggiuntive"]


class AnalysisRequest(BaseModel):
    prompt: str
    # Profilo pilota dal wizard "Conosci il pilota" (megaprompt #9, FASE 5).
    # Opzionale e usato SOLO nel ramo LLM reale: nel ramo demo/cache viene
    # ignorato, così il routing per keyword di pick_demo_response (protetto)
    # continua a vedere il prompt puro dell'utente.
    profile: str | None = None


def _context(prompt: str, profile: str | None = None) -> str:
    profile_line = f"{profile.strip()}\n\n" if profile and profile.strip() else ""
    return (
        f"Auto: {dd.SESSION['car']}\nTracciato: {dd.SESSION['track']}\n"
        f"Condizioni: {dd.SESSION['stint']}\n\n"
        f"{profile_line}"
        f"Telemetria (a caldo): temperature gomme max "
        f"FL {dd.TYRE_TEMP_MAX['fl']}°C, FR {dd.TYRE_TEMP_MAX['fr']}°C, "
        f"RL {dd.TYRE_TEMP_MAX['rl']}°C, RR {dd.TYRE_TEMP_MAX['rr']}°C; "
        f"pressioni a caldo {dd.HOT_PRESSURES}.\n\n"
        f"Feedback pilota: {prompt.strip()}"
    )


@router.post("/analysis")
def post_analysis(req: AnalysisRequest):
    prompt = req.prompt or ""

    # 1) demo-mode o prompt = scenario demo → cache (sempre, niente rete).
    #    Fuori perimetro (nessuna keyword) → redirect onesto, NON il default
    #    sovrasterzo della cache (blindatura anti-"allucinazione percepita").
    if config.demo_mode() or is_demo_prompt(prompt):
        source = "demo" if config.demo_mode() else "cache"
        text = pick_demo_response(prompt) if _in_scope(prompt) else _off_topic_text()
        return {"question": prompt, "text": text, "source": source}

    # 2) LLM reale con fallback alla cache
    api_key = config.ANTHROPIC_API_KEY
    if not api_key:
        return {"question": prompt, "text": pick_demo_response(prompt), "source": "fallback"}
    try:
        from app.core.agent import get_ai_response

        resp = get_ai_response(
            user_input=_context(prompt, req.profile), api_key=api_key,
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
