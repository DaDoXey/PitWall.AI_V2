"""app.bundle — il formato canonico di una sessione e i suoi adattatori.

`schema.py` definisce il «session bundle» (L2 di `docs/04-rework-dati.md`);
gli adattatori leggono i file di ACC e producono bundle.
"""

from app.bundle.schema import (  # noqa: F401
    SCHEMA_VERSION,
    BundleVersionError,
    Canali,
    Condizioni,
    Evento,
    Fonte,
    Giro,
    Meta,
    SessionBundle,
    Setup,
    TipoEvento,
    TipoSessione,
    ValoreSetup,
)
