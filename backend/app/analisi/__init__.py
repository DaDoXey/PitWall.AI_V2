"""app.analisi — il motore di analisi (L2): da un session bundle a un report di numeri.

Deterministico e senza LLM: è la fonte delle cifre che Gigi cita.
"""

from app.analisi.motore import (  # noqa: F401
    Carburante,
    Costanza,
    Degrado,
    Perdita,
    ReportAnalisi,
    Ritmo,
    Settore,
    analizza,
)
