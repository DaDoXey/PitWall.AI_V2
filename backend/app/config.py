"""app/config.py — configurazione backend (env server-side).

La ANTHROPIC_API_KEY vive SOLO qui (lato server): il frontend non la vede mai.
Flag `PITWALL_ALLOW_LIVE` replica il presidio della v1: in deploy pubblico la
demo-mode è forzata → nessuno può consumare la chiave. La LLM reale si abilita
solo con ALLOW_LIVE=1 + chiave nei secret del server.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Log (MUST #1, Entry #026) ──
# Percorso ricavato da questo file, non dalla cartella di avvio: backend/logs/ sta
# sempre nello stesso posto, da qualunque cartella parta uvicorn. Gitignorata.
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

# agent.py (protetto, non si tocca) scrive due registri markdown su percorsi presi
# dall'ambiente, con default RELATIVI alla cartella di avvio e omonimi dei documenti
# scritti a mano (PROMPT_LOG.md, INCIDENTS.md). Qui gli si da' un default assoluto in
# backend/logs/. setdefault: un valore nel .env vince sempre. Funziona perche'
# agent.py legge l'ambiente quando viene importato, e lo importano solo gli
# endpoint, cioe' dopo questo modulo.
os.environ.setdefault("PITWALL_PROMPT_LOG_PATH", str(LOG_DIR / "llm_token_log.md"))
os.environ.setdefault("PITWALL_INCIDENTS_PATH", str(LOG_DIR / "llm_incidents.md"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-haiku-4-5")

def origini(valore: str) -> list[str]:
    """Le origini del frontend, ridotte a schema + host (+ porta).

    Un'origine non ha percorso: `https://sito.app/login` o `https://sito.app/` non
    combaciano mai con quello che manda il browser, e il frontend resta muto senza un
    errore visibile (successo il 05/10/2026 al primo deploy). Qui il percorso si toglie.
    """
    from urllib.parse import urlsplit

    fuori: list[str] = []
    for pezzo in valore.split(","):
        pezzo = pezzo.strip()
        if not pezzo:
            continue
        parti = urlsplit(pezzo)
        origine = f"{parti.scheme}://{parti.netloc}" if parti.scheme and parti.netloc else pezzo.rstrip("/")
        if origine not in fuori:
            fuori.append(origine)
    return fuori


CORS_ORIGINS = origini(os.getenv("PITWALL_CORS_ORIGINS", "http://localhost:3000"))


def allow_live() -> bool:
    """True se è consentito usare la LLM reale (default: no)."""
    return os.getenv("PITWALL_ALLOW_LIVE", "0").strip().lower() in ("1", "true", "yes", "on")


def chat_live() -> bool:
    """True se la chat dal vivo di Gigi può chiamare il modello (Entry #061).

    Interruttore suo, separato da PITWALL_ALLOW_LIVE: accende solo la chat, mentre
    Rapporto completo e screenshot restano in demo-mode. Spento di default, quindi in
    deploy pubblico nessuno consuma la chiave; la spesa resta dentro il tetto "chat".
    """
    return os.getenv("PITWALL_CHAT_LIVE", "0").strip().lower() in ("1", "true", "yes", "on")


def demo_mode() -> bool:
    """True se si serve la cache demo (nessuna rete). Forzata in deploy pubblico."""
    if not allow_live():
        return True  # API key protetta
    return os.getenv("PITWALL_DEMO_MODE", "1").strip().lower() not in ("0", "false", "no", "off")
