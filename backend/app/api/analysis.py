"""POST /api/analysis — analisi di Gigi a 4 sezioni.

Replica get_console_analysis della v1: demo-cache (nessuna rete) o LLM reale gated,
con fallback alla cache. La chiave resta lato server (app.config).

Ogni esito lascia una riga in backend/logs/pitwall.log con la fonte e, quando si
ripiega sulla cache, il motivo (Entry #026). Mai il testo del pilota: solo lunghezze.

Tetto di spesa (Entry #028): prima del ramo reale si controllano la lunghezza del
testo e il margine della categoria "analisi" di app.budget. La garanzia vera sta in
agent.call_claude, che prenota il costo massimo prima di ogni chiamata della cascata.
"""

import logging
import time

from fastapi import APIRouter
from pydantic import BaseModel

from app import budget, config
from app.core import demo_data as dd

# _DEMO_ROUTES è privato del modulo protetto ma è l'unica fonte di verità delle
# keyword: lo si legge (mai modificato) per capire se una domanda è nel perimetro
# della demo, senza duplicare la lista qui.
from app.core.demo_responses import _DEMO_ROUTES, is_demo_prompt, pick_demo_response

router = APIRouter()
log = logging.getLogger("pitwall.analysis")

# Testo con cui agent.py (protetto) risponde quando tutti i modelli della cascata
# hanno fallito. Letto e mai modificato, come _DEMO_ROUTES: serve solo a scrivere nel
# log PERCHE' si è finiti in fallback. I dettagli del guasto li scrive agent.py nel
# suo registro dei guasti (default backend/logs/llm_incidents.md).
_AGENT_TUTTI_FALLITI = "Servizio temporaneamente non disponibile"


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

# Lunghezze massime del ramo reale (Entry #028). Il profilo del wizard e' una riga da
# ~300 caratteri; una domanda del pilota sta ben sotto i 4000. Oltre, niente chiamata:
# riduce il caso peggiore del costo, e tiene l'input lontano dalla soglia degli 8000
# token stimati di agent.py, oltre la quale parte l'`import streamlit`.
MAX_CARATTERI_PROMPT = 4000
MAX_CARATTERI_PROFILO = 1000


class AnalysisRequest(BaseModel):
    prompt: str
    # Profilo pilota dal wizard "Conosci il pilota" (megaprompt #9, FASE 5).
    # Opzionale e usato SOLO nel ramo LLM reale: nel ramo demo/cache viene
    # ignorato, così il routing per keyword di pick_demo_response (protetto)
    # continua a vedere il prompt puro dell'utente.
    profile: str | None = None


def _descrivi(req: AnalysisRequest) -> str:
    """La richiesta come appare nel log: lunghezza e presenza, MAI il testo del
    pilota né il profilo (decisione del 10/09)."""
    profilo = "si" if req.profile and req.profile.strip() else "no"
    return f"prompt {len(req.prompt or '')} caratteri, profilo {profilo}"


def _ms(inizio: float) -> float:
    return (time.perf_counter() - inizio) * 1000


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
        in_scope = _in_scope(prompt)
        text = pick_demo_response(prompt) if in_scope else _off_topic_text()
        log.info("source=%s, %s, %s", source,
                 "in perimetro" if in_scope else "fuori perimetro", _descrivi(req))
        return {"question": prompt, "text": text, "source": source}

    # 2) LLM reale con fallback alla cache
    api_key = config.ANTHROPIC_API_KEY
    if not api_key:
        log.warning("source=fallback: live consentito ma ANTHROPIC_API_KEY assente, %s",
                    _descrivi(req))
        return {"question": prompt, "text": pick_demo_response(prompt), "source": "fallback"}

    if len(prompt) > MAX_CARATTERI_PROMPT or len(req.profile or "") > MAX_CARATTERI_PROFILO:
        log.warning("source=fallback: testo oltre il limite (%d/%d caratteri il prompt, %d/%d il "
                    "profilo), nessuna chiamata", len(prompt), MAX_CARATTERI_PROMPT,
                    len(req.profile or ""), MAX_CARATTERI_PROFILO)
        return {"question": prompt, "text": pick_demo_response(prompt), "source": "fallback"}

    if not budget.disponibile("analisi"):
        log.warning("source=fallback: tetto di spesa dell'analisi raggiunto, nessuna chiamata, %s",
                    _descrivi(req))
        return {"question": prompt, "text": pick_demo_response(prompt), "source": "fallback"}

    inizio = time.perf_counter()
    try:
        from app.core.agent import get_ai_response

        resp = get_ai_response(
            user_input=_context(prompt, req.profile), api_key=api_key,
            auto=dd.SESSION["car"], tracciato=dd.SESSION["track"],
        )
    except Exception:
        log.exception("source=fallback: eccezione nel ramo LLM dopo %.0f ms, %s",
                      _ms(inizio), _descrivi(req))
        return {"question": prompt, "text": pick_demo_response(prompt), "source": "fallback"}

    ok = all(s in (resp or "") for s in _REQUIRED)
    if ok:
        log.info("source=api in %.0f ms, risposta %d caratteri, %s",
                 _ms(inizio), len(resp), _descrivi(req))
    elif _AGENT_TUTTI_FALLITI in (resp or ""):
        log.warning("source=fallback: tutti i modelli della cascata hanno fallito dopo %.0f ms "
                    "(dettagli nel registro guasti di agent.py), %s", _ms(inizio), _descrivi(req))
    else:
        log.warning("source=fallback: risposta senza le 4 sezioni obbligatorie (%d caratteri) "
                    "dopo %.0f ms, %s", len(resp or ""), _ms(inizio), _descrivi(req))
    return {
        "question": prompt,
        "text": resp if ok else pick_demo_response(prompt),
        "source": "api" if ok else "fallback",
    }
