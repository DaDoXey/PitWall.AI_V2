"""POST /api/setup/from-image — lettura setup da screenshot ACC (core/vision_parser).

Richiede la chiave lato server; è una feature "reale" (non demo). In deploy pubblico
senza chiave risponde 503.

Attenzione al costo: è l'unica chiamata reale al modello che NON passa dal flag
PITWALL_ALLOW_LIVE, le basta la chiave. Per questo ogni esito, con la durata, lascia
una riga in backend/logs/pitwall.log (Entry #026).
"""

import logging
import time

from fastapi import APIRouter, File, HTTPException, UploadFile

from app import config

router = APIRouter()
log = logging.getLogger("pitwall.vision")


@router.post("/setup/from-image")
async def setup_from_image(file: UploadFile = File(...)):
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
