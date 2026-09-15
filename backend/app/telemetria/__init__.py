"""Telemetria live di ACC (L3 del rework dati).

`strutture` descrive le tre pagine di shared memory esattamente come le scrive il
gioco; `lettore` le aggancia e le legge. Nessun modulo di questo pacchetto fa
analisi: qui si raccoglie soltanto, e si dichiara quello che non si è potuto leggere.
"""

from app.telemetria.strutture import (
    ACC_RAIN_INTENSITY,
    ACC_SESSION_TYPE,
    ACC_STATUS,
    ACC_TRACK_GRIP_STATUS,
    CAMPI_NON_USATI,
    PAGINE,
    SPageFileGraphics,
    SPageFilePhysics,
    SPageFileStatic,
    VERSIONE_STRUTTURA,
)

__all__ = [
    "ACC_RAIN_INTENSITY",
    "ACC_SESSION_TYPE",
    "ACC_STATUS",
    "ACC_TRACK_GRIP_STATUS",
    "CAMPI_NON_USATI",
    "PAGINE",
    "SPageFileGraphics",
    "SPageFilePhysics",
    "SPageFileStatic",
    "VERSIONE_STRUTTURA",
]
