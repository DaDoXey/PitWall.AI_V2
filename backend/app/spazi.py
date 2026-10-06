"""spazi.py — uno spazio per ogni pilota, senza registrarsi (tabella di marcia, 2.2).

Online più persone usano lo stesso backend: ognuna deve vedere solo le proprie sessioni.
Non c'è (ancora) un accesso: il browser genera un **codice** lungo e casuale, lo conserva
e lo manda a ogni richiesta nell'intestazione `X-PitWall-Spazio`. Chi ha il codice ha lo
spazio: per questo è lungo, non si indovina, e non finisce mai in un indirizzo né nei log.

Sul disco ogni spazio è una cartella dentro `<archivio>/spazi/`, col nome ricavato dal
codice con un'impronta: chi guardasse il disco vedrebbe le cartelle, non i codici.

**La demo è di tutti**: resta nell'archivio comune, si legge da ogni spazio e nessuno la
può modificare.

**In locale non cambia niente.** Gli spazi si accendono con `PITWALL_SPAZI=1`; spenti
(il valore predefinito) tutto vive nell'archivio comune, come prima: il backend gira sul
PC del pilota e l'archivio è il suo.

Costruito per essere «adottato» da un accesso vero (pacchetto 3.4): basterà legare il
codice a un account, le cartelle restano dove sono.
"""

from __future__ import annotations

import hashlib
import os
import re
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

INTESTAZIONE = "x-pitwall-spazio"
# 32-64 caratteri fra lettere, cifre, `-` e `_`: il frontend ne genera 48 esadecimali
# (192 bit casuali). Più corto di 32 sarebbe indovinabile a tentativi.
CODICE_VALIDO = re.compile(r"[A-Za-z0-9_-]{32,64}")

_corrente: ContextVar[str | None] = ContextVar("pitwall_spazio", default=None)
_in_comune: ContextVar[bool] = ContextVar("pitwall_in_comune", default=False)


class SpazioMancante(ValueError):
    """Gli spazi sono accesi e la richiesta non dice di chi è."""


class LimiteSpazio(ValueError):
    """Lo spazio è pieno: non accetta altre sessioni."""


def attivi() -> bool:
    """Interruttore `PITWALL_SPAZI`: spento in locale, acceso dove gli utenti sono più d'uno."""
    return os.getenv("PITWALL_SPAZI", "0").strip().lower() in ("1", "true", "yes", "on")


def max_sessioni() -> int:
    return int(os.getenv("PITWALL_SPAZIO_MAX_SESSIONI", "20"))


def max_byte_file() -> int:
    return int(os.getenv("PITWALL_SPAZIO_MAX_FILE_MB", "60")) * 1024 * 1024


def imposta(codice: str | None):
    """Lo spazio della richiesta in corso. Torna il gettone per `ripristina`."""
    return _corrente.set(codice)


def ripristina(gettone) -> None:
    _corrente.reset(gettone)


def corrente() -> str | None:
    return _corrente.get()


@contextmanager
def comune():
    """Dentro questo blocco si lavora nell'archivio comune, qualunque sia lo spazio della
    richiesta: serve a creare e aggiornare la demo, che è di tutti."""
    gettone = _in_comune.set(True)
    try:
        yield
    finally:
        _in_comune.reset(gettone)


def in_comune() -> bool:
    return _in_comune.get()


def radice_comune() -> Path:
    """L'archivio di tutti: in locale è l'archivio e basta, online ci vive solo la demo."""
    grezzo = os.getenv("PITWALL_SESSIONS_DIR", "").strip()
    radice = Path(grezzo) if grezzo else Path(__file__).resolve().parents[1] / "sessions"
    radice.mkdir(parents=True, exist_ok=True)
    return radice


def _nome_cartella(codice: str) -> str:
    return hashlib.sha256(codice.encode("ascii")).hexdigest()[:40]


def radice(crea: bool = True) -> Path:
    """La cartella dove legge e scrive la richiesta in corso.

    Spazi spenti: l'archivio comune. Spazi accesi: la cartella dello spazio; senza
    codice è un errore, non un ripiego sull'archivio comune (sarebbe lo spazio di tutti).
    """
    if not attivi() or in_comune():
        return radice_comune()
    codice = corrente()
    if not codice:
        raise SpazioMancante("questa installazione ha uno spazio per ogni pilota: "
                             "la richiesta non dice di chi è")
    percorso = radice_comune() / "spazi" / _nome_cartella(codice)
    if crea:
        percorso.mkdir(parents=True, exist_ok=True)
    return percorso


def e_comune(id_sessione: str | None) -> bool:
    """Le sessioni di tutti: oggi solo la demo."""
    from app.bundle.demo import DEMO_ID

    return id_sessione == DEMO_ID


def radice_di(id_sessione: str | None, crea: bool = True) -> Path:
    """Dove sta una sessione: nell'archivio comune se è di tutti, altrimenti nello spazio."""
    return radice_comune() if e_comune(id_sessione) else radice(crea)


def assicura_demo() -> str:
    """La demo c'è ed è aggiornata, nell'archivio comune: da qualunque spazio la si chieda."""
    from app.bundle import demo

    with comune():
        return demo.assicura_demo()
