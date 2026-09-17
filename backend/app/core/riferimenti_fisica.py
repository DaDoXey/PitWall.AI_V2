"""core/riferimenti_fisica.py — le soglie di gomme e freni, divise per affidabilità.

Due file, due pesi (decisione del 16/09/2026):

* `data/acc_riferimenti_fisica_v19.json` — **fonte primaria**: il documento «Version
  1.9 - Physics notes» pubblicato da Kunos sul forum ufficiale. Sono le sole soglie
  contro cui il motore di analisi **giudica**, e anche lì con la prudenza che il
  documento stesso chiede (la finestra è «indicativa»).
* `data/acc_riferimenti_community.json` — valori che circolano fra piloti e coach,
  **da confermare**. Si mostrano con l'etichetta «community» accanto ai numeri, ma
  non entrano mai nel verdetto: un'analisi spietata su un numero sentito dire
  sarebbe spietata a caso.

Chi mostra una soglia deve poter dire da dove arriva: ogni voce porta la citazione e
l'indirizzo della fonte, e questo modulo li lascia passare così come sono.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATI = Path(__file__).resolve().parent / "data"
_UFFICIALI = _DATI / "acc_riferimenti_fisica_v19.json"
_COMMUNITY = _DATI / "acc_riferimenti_community.json"


@lru_cache(maxsize=1)
def ufficiali() -> dict[str, Any]:
    return json.loads(_UFFICIALI.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def community() -> dict[str, Any]:
    return json.loads(_COMMUNITY.read_text(encoding="utf-8"))


def voce(nome: str) -> dict[str, Any]:
    """Una voce ufficiale. KeyError se non esiste: una soglia sbagliata non si inventa."""
    return dict(ufficiali()["voci"][nome])


def finestra(nome: str) -> tuple[float, float]:
    """(min, max) di una voce ufficiale con un intervallo."""
    dati = voce(nome)
    return float(dati["min"]), float(dati["max"])


def finestra_pressione_asciutto() -> tuple[float, float]:
    return finestra("pressione_gomme_asciutto")


def finestra_core_asciutto() -> tuple[float, float]:
    return finestra("temperatura_core_gomme")


def citazione_fonte() -> str:
    """Una riga da mettere accanto a qualunque giudizio basato su queste soglie."""
    fonte = ufficiali()["fonte"]
    return (f"{fonte['editore']}, «{fonte['titolo']}» (ACC {fonte['versione_acc']}, "
            f"{fonte['pubblicato_il']})")


def come_json() -> dict[str, Any]:
    """Entrambi i file, separati, per le schermate: fonte primaria e community."""
    return {
        "ufficiali": ufficiali(),
        "community": community(),
    }
