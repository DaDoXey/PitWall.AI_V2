"""app/main.py — FastAPI entry point.

Avvio (dalla cartella backend/):
    python -m uvicorn app.main:app

Niente --reload: su Windows serve codice vecchio dopo una modifica al backend
(HAZARD-V2-B in INCIDENTS.md). Dopo aver toccato il backend, riavvialo a mano.
"""

import logging
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.api import analysis, catalog, sessions, setup, telemetria, vision
from app.logging_config import request_id, setup_logging
from app.telemetria import registratore as telemetria_reg

setup_logging()
log = logging.getLogger("pitwall.http")

app = FastAPI(title="PitWall.AI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for _router in (sessions.router, analysis.router, setup.router,
                vision.router, catalog.router, telemetria.router):
    app.include_router(_router, prefix="/api")

# Un request-id arrivato dal client si riusa solo se e' innocuo: finisce dentro ogni
# riga di log, e un valore arbitrario potrebbe fingere righe che non esistono.
_RID_VALIDO = re.compile(r"[A-Za-z0-9._-]{1,64}")


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Request-id e durata di ogni richiesta; traccia delle eccezioni non gestite."""
    ricevuto = request.headers.get("x-request-id", "")
    rid = ricevuto if _RID_VALIDO.fullmatch(ricevuto) else uuid.uuid4().hex[:12]
    token = request_id.set(rid)
    inizio = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("%s %s -> eccezione non gestita dopo %.0f ms",
                      request.method, request.url.path, (time.perf_counter() - inizio) * 1000)
        raise
    else:
        response.headers["X-Request-ID"] = rid
        log.info("%s %s -> %d in %.0f ms", request.method, request.url.path,
                 response.status_code, (time.perf_counter() - inizio) * 1000)
        return response
    finally:
        request_id.reset(token)


@app.on_event("startup")
def prepara_demo():
    """La sessione DEMO nello stesso archivio delle altre (L4). Se manca o è di una
    versione vecchia del generatore, si ricrea: qualche secondo, una volta sola."""
    from app.bundle.demo import assicura_demo

    try:
        assicura_demo()
    except Exception:   # una demo che non si crea non deve impedire all'app di partire
        log.exception("sessione demo non creata")


@app.on_event("startup")
def avvia_registratore():
    """Il registratore della telemetria parte col backend (decisione 5 del 15/09).

    Attrito zero: il pilota accende il gioco e basta. Il thread, finche' ACC non
    c'e', ritenta ogni due secondi e non fa nient'altro. Sul deploy vetrina
    `PITWALL_ALLOW_RECORDER=0` lo tiene spento.
    """
    if telemetria_reg.abilitato():
        telemetria.registratore().avvia()


@app.on_event("shutdown")
def ferma_registratore():
    """Spegnendo il backend si chiude la sessione aperta, invece di perderla."""
    if telemetria_reg.abilitato():
        telemetria.registratore().ferma()


@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "PitWall.AI API",
        "version": "0.1.0",
        "demo_mode": config.demo_mode(),
        "live_allowed": config.allow_live(),
        "recorder_allowed": telemetria_reg.abilitato(),
    }
