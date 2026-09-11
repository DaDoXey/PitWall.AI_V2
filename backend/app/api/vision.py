"""POST /api/setup/from-image — lettura setup da screenshot ACC (core/vision_parser).

È una feature "reale" (non demo): non esiste una cache, ogni screenshot è una chiamata
a claude-sonnet-4-6. Per questo passa dallo stesso presidio della Console (Entry #027):
risponde 503 in demo-mode, cioè se non ci sono sia PITWALL_ALLOW_LIVE=1 sia
PITWALL_DEMO_MODE=0, e 503 se manca la chiave. Prima bastava la chiave, e con una
chiave nel .env ogni screenshot la consumava anche in demo.

Ogni esito, con la durata, lascia una riga in backend/logs/pitwall.log (Entry #026).
"""

import logging
import time

from fastapi import APIRouter, File, HTTPException, UploadFile

from app import config

router = APIRouter()
log = logging.getLogger("pitwall.vision")


@router.post("/setup/from-image")
async def setup_from_image(file: UploadFile = File(...)):
    # Il presidio viene prima di tutto, anche della chiave: in demo-mode nessuna rete.
    if config.demo_mode():
        log.warning("503: lettura screenshot richiesta in demo-mode (servono "
                    "PITWALL_ALLOW_LIVE=1 e PITWALL_DEMO_MODE=0)")
        raise HTTPException(status_code=503, detail="Lettura screenshot disattivata in demo-mode")
    if not config.ANTHROPIC_API_KEY:
        log.warning("503: lettura screenshot richiesta ma ANTHROPIC_API_KEY assente")
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY non configurata lato server")
    raw = await file.read()
    # %r sul tipo: arriva dal client, cosi' non puo' spezzare la riga di log.
    descrizione = f"{len(raw)} byte, tipo {file.content_type!r}"
    inizio = time.perf_counter()
    try:
        from app.core.vision_parser import parse_setup_from_image, summarize_parsed_setup

        result = parse_setup_from_image(raw, api_key=config.ANTHROPIC_API_KEY,
                                        media_type=file.content_type)
        result["summary"] = summarize_parsed_setup(result)
    except Exception as e:  # noqa: BLE001
        log.exception("500: lettura screenshot fallita dopo %.0f ms, %s",
                      (time.perf_counter() - inizio) * 1000, descrizione)
        raise HTTPException(status_code=500, detail=f"Lettura screenshot fallita: {e}")
    log.info("screenshot letto in %.0f ms, %s", (time.perf_counter() - inizio) * 1000, descrizione)
    return result
