"""POST /api/csv/parse — parsing/validazione CSV sessione ACC (core/csv_parser)."""

from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.csv_parser import CSVParseError, parse_session_csv

router = APIRouter()


@router.post("/csv/parse")
async def parse_csv(file: UploadFile = File(...)):
    raw = await file.read()
    try:
        return parse_session_csv(BytesIO(raw))
    except CSVParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001 — messaggio utente, non deve crashare
        raise HTTPException(status_code=400, detail=f"Impossibile leggere il CSV: {e}")
