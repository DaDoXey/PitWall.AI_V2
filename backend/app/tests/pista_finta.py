"""Il banco di prova sintetico vive ora in `app/telemetria/banco.py`.

Si è spostato lì il 16/09/2026 perché lo usa anche la sessione DEMO (L4), che è
codice dell'app e non può dipendere dalla cartella dei test. Questo modulo resta
perché i test lo importano con questo nome.
"""

from app.telemetria.banco import (  # noqa: F401
    CurvaFinta,
    GiroFinto,
    PistaFinta,
    genera,
    pista_tre_curve,
)
