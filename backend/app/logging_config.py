"""app/logging_config.py — log del backend, con un request-id per richiesta.

Perche' esiste (MUST #1 della PRR, Entry #026):
    Il ramo LLM falliva in silenzio in piu' punti: `api/analysis.py` inghiottiva
    ogni eccezione e ripiegava sulla cache senza una riga, la chiave mancante
    mandava in fallback senza dirlo, e un errore della lettura screenshot
    arrivava al client come 500 senza lasciare niente sul server.

Cosa fa:
    - logger `pitwall` e figli (`pitwall.http`, `pitwall.analysis`, ...);
    - file rotante `backend/logs/pitwall.log`, 1 MB x 3 copie, da livello INFO;
    - in console solo WARNING ed ERROR, per non coprire le righe di uvicorn;
    - in ogni riga il request-id della richiesta HTTP in corso (`-` fuori da una
      richiesta), che il middleware di main.py imposta e rimanda al client
      nell'header `X-Request-ID`.

Cosa NON registra: il testo che il pilota scrive e il suo profilo. Solo
lunghezze e presenza (decisione del 10/09): il log serve a diagnosticare, non a
conservare quello che scrivono i piloti.
"""

from __future__ import annotations

import contextvars
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app import config

LOG_FILE_NAME = "pitwall.log"
MAX_BYTES = 1_000_000
BACKUP_COUNT = 3
FORMATO = "%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s"

# Request-id della richiesta in corso. Un ContextVar e non una globale: richieste
# concorrenti hanno ciascuna il proprio valore, e Starlette lo porta anche nel
# thread in cui girano gli endpoint sincroni (verificato dal test).
request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    """Mette il request-id nel record. Sta sugli handler e non sul logger: i filtri
    di un logger non si applicano ai record che arrivano dai logger figli."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()
        return True


def setup_logging(log_dir: Path | None = None) -> logging.Logger:
    """Configura il logger `pitwall`.

    Richiamarla sostituisce gli handler invece di aggiungerne: nessuna riga
    doppia, e i test possono puntarla su una cartella temporanea.
    """
    cartella = Path(log_dir) if log_dir else config.LOG_DIR
    cartella.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("pitwall")
    for vecchio in list(logger.handlers):
        logger.removeHandler(vecchio)
        vecchio.close()

    formato = logging.Formatter(FORMATO)
    su_file = RotatingFileHandler(cartella / LOG_FILE_NAME, maxBytes=MAX_BYTES,
                                  backupCount=BACKUP_COUNT, encoding="utf-8")
    su_file.setLevel(logging.INFO)
    in_console = logging.StreamHandler()
    in_console.setLevel(logging.WARNING)
    for handler in (su_file, in_console):
        handler.setFormatter(formato)
        handler.addFilter(_RequestIdFilter())
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    # Niente propagazione al root: se qualcuno mette un handler sul root, ogni
    # riga uscirebbe due volte.
    logger.propagate = False
    return logger
