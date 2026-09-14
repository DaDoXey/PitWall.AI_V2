"""api/sessions.py — importare e consultare le sessioni (L1 · Fase 4).

Rotte:
- `POST /api/sessions/import/setup`   — un setup di ACC diventa una sessione
- `POST /api/sessions/import/results` — un file di risultati diventa una sessione
- `GET  /api/sessions`                — elenco, dalla più recente
- `GET  /api/sessions/{id}`           — il bundle intero
- `DELETE /api/sessions/{id}`         — rimuove una sessione

**Presidio.** Queste rotte scrivono su disco e non toccano né la chiave né la rete,
quindi NON passano dal presidio della demo-mode (che serve a proteggere la
ANTHROPIC_API_KEY): bloccarle in demo le renderebbe inutilizzabili proprio dove
servono, sul PC del pilota, dove il live è spento. Hanno un interruttore loro,
`PITWALL_ALLOW_IMPORT` (default **acceso**): sul deploy pubblico va messo a 0, così
la vetrina non accetta file da nessuno.

**Più vetture nel file.** Un file di risultati contiene tutti i partecipanti. Se non
si dice quale sia la propria, la rotta risponde **409** con l'elenco (`partecipanti`)
invece di sceglierne una a caso: è il frontend a far scegliere, poi richiama con
`car_id`.
"""

import logging
import os

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.bundle import store
from app.bundle.adapters import (
    ResultsAccError,
    SetupAccError,
    elenca_partecipanti,
    leggi_results_acc,
    leggi_setup_acc,
)
from app.bundle.schema import Fonte, Meta, SessionBundle

router = APIRouter()
log = logging.getLogger("pitwall.sessions")

# Un file di ACC sta in pochi KB: il tetto serve solo a non farsi riempire il disco.
MAX_BYTE = 20 * 1024 * 1024


def _import_consentito() -> bool:
    return os.getenv("PITWALL_ALLOW_IMPORT", "1").strip().lower() not in ("0", "false", "no", "off")


def _presidio() -> None:
    if not _import_consentito():
        log.warning("503: import richiesto ma PITWALL_ALLOW_IMPORT e' spento")
        raise HTTPException(status_code=503,
                            detail="Import delle sessioni disattivato su questa installazione")


async def _leggi_upload(file: UploadFile) -> bytes:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="File vuoto")
    if len(raw) > MAX_BYTE:
        raise HTTPException(status_code=413,
                            detail=f"File troppo grande (massimo {MAX_BYTE // (1024 * 1024)} MB)")
    return raw


@router.post("/sessions/import/setup")
async def importa_setup(
    file: UploadFile = File(...),
    track: str | None = Form(default=None),
    nome: str | None = Form(default=None),
):
    """Legge un setup salvato in ACC e lo archivia come sessione."""
    _presidio()
    raw = await _leggi_upload(file)
    try:
        setup = leggi_setup_acc(raw, nome=nome or (file.filename or "").removesuffix(".json") or None)
    except SetupAccError as e:
        log.warning("400: setup non importabile (%d byte): %s", len(raw), e)
        raise HTTPException(status_code=400, detail=str(e))

    bundle = SessionBundle(
        meta=Meta(fonte=Fonte.ACC_SETUP, car=setup.car, track=track,
                  file_origine=file.filename),
        setup=setup,
    )
    id_sessione = store.salva(bundle)
    reali, totali = setup.quanti_verificati()
    log.info("setup importato: %s (%s, %d parametri, %d in unità reali)",
             id_sessione, setup.car, totali, reali)
    return {
        "id": id_sessione,
        "riassunto": store.riassunto(id_sessione),
        "assunzioni": setup.assunzioni,
        "parametri": totali,
        "parametri_in_unita_reali": reali,
    }


@router.post("/sessions/import/results")
async def importa_risultati(
    file: UploadFile = File(...),
    car_id: int | None = Form(default=None),
    player_id: str | None = Form(default=None),
    track: str | None = Form(default=None),
):
    """Legge un file di risultati di ACC e lo archivia come sessione."""
    _presidio()
    raw = await _leggi_upload(file)

    if car_id is None and player_id is None:
        try:
            partecipanti = elenca_partecipanti(raw)
        except ResultsAccError as e:
            log.warning("400: risultati non importabili (%d byte): %s", len(raw), e)
            raise HTTPException(status_code=400, detail=str(e))
        if len(partecipanti) > 1:
            log.info("409: %d vetture nel file, serve scegliere", len(partecipanti))
            raise HTTPException(
                status_code=409,
                detail={
                    "messaggio": "Il file contiene più vetture: indica quale è la tua.",
                    "partecipanti": [p.__dict__ for p in partecipanti],
                },
            )

    try:
        bundle = leggi_results_acc(raw, car_id=car_id, player_id=player_id, track=track)
    except ResultsAccError as e:
        log.warning("400: risultati non importabili (%d byte): %s", len(raw), e)
        raise HTTPException(status_code=400, detail=str(e))

    bundle.meta.file_origine = file.filename
    id_sessione = store.salva(bundle)
    log.info("risultati importati: %s (%d giri, %d validi)",
             id_sessione, len(bundle.giri), len(bundle.giri_validi))
    return {
        "id": id_sessione,
        "riassunto": store.riassunto(id_sessione),
        "assunzioni": bundle.assunzioni,
    }


@router.get("/sessions")
async def elenco_sessioni(limite: int = 50):
    limite = max(1, min(limite, 200))
    return {"sessioni": store.elenca(limite)}


@router.get("/sessions/{id_sessione}")
async def leggi_sessione(id_sessione: str):
    try:
        return store.leggi(id_sessione)
    except store.SessioneNonTrovata:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    except store.ArchivioError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/sessions/{id_sessione}")
async def cancella_sessione(id_sessione: str):
    try:
        store.cancella(id_sessione)
    except store.SessioneNonTrovata:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    except store.ArchivioError as e:
        raise HTTPException(status_code=400, detail=str(e))
    log.info("sessione cancellata: %s", id_sessione)
    return {"cancellata": id_sessione}
