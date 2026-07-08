"""app/config.py — configurazione backend (env server-side).

La ANTHROPIC_API_KEY vive SOLO qui (lato server): il frontend non la vede mai.
Flag `PITWALL_ALLOW_LIVE` replica il presidio della v1: in deploy pubblico la
demo-mode è forzata → nessuno può consumare la chiave. La LLM reale si abilita
solo con ALLOW_LIVE=1 + chiave nei secret del server.
"""

import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-haiku-4-5")

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("PITWALL_CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]


def allow_live() -> bool:
    """True se è consentito usare la LLM reale (default: no)."""
    return os.getenv("PITWALL_ALLOW_LIVE", "0").strip().lower() in ("1", "true", "yes", "on")


def demo_mode() -> bool:
    """True se si serve la cache demo (nessuna rete). Forzata in deploy pubblico."""
    if not allow_live():
        return True  # API key protetta
    return os.getenv("PITWALL_DEMO_MODE", "1").strip().lower() not in ("0", "false", "no", "off")
