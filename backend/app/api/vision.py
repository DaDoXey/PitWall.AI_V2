"""POST /api/setup/from-image — lettura setup da screenshot ACC (core/vision_parser).

Richiede la chiave lato server; è una feature "reale" (non demo). In deploy pubblico
senza chiave risponde 503.
"""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app import config

router = APIRouter()


@router.post("/setup/from-image")
async def setup_from_image(file: UploadFile = File(...)):
    if not config.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY non configurata lato server")
    raw = await file.read()
    try:
        from app.core.vision_parser import parse_setup_from_image, summarize_parsed_setup

        result = parse_setup_from_image(raw, api_key=config.ANTHROPIC_API_KEY,
                                        media_type=file.content_type)
        result["summary"] = summarize_parsed_setup(result)
        return result
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Lettura screenshot fallita: {e}")
