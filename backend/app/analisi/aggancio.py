"""L'aggancio della guida in sessione: quale curva della guida sta in quale tratto del motore.

Il motore (`curve.py`) divide il giro in tratti dai minimi di velocità e li numera da sé
(C1, C2…): la sua «curva 5» a Monza è la Variante Ascari intera, T8-T10 della guida. Le
**ancore** (`core/ancore.py`, confermate a occhio da Edoardo) dicono dove sta ogni curva
della guida sul giro, nella stessa scala 0-1 del motore. Da qui una regola sola:

**una curva della guida appartiene al tratto del motore che ne contiene l'apice.**

Un tratto può contenere più curve della guida (una chicane, una esse, una curva in pieno
che il motore non vede come minimo e che quindi finisce nel tratto dopo): si mostrano
tutte lì. Un tratto può anche non contenerne nessuna.

Il nome di un tratto è l'intervallo delle curve più i loro nomi distinti, senza le fasi
«(ingresso)», «(centro)», «(uscita)»: «T8-T10 Variante Ascari», «T1-T3 Variante del
Rettifilo · Curva Grande». Una curva sola tiene il nome intero; una senza nome resta «T9».

Niente numpy e niente telemetria: le curve del motore arrivano come oggetti con
`numero`, `ingresso`, `uscita` (quelli di `curve.Curva`), così il modulo si prova da sé.
La **demo** non si aggancia: il suo circuito è generato e le curve non cadono dove sono
in pista (la Parabolica a 0,934 invece di 0,8975).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Protocol

from app.core import ancore as ancore_mod
from app.core import catalog

NOTA_DEMO = ("Sulla demo la guida non si aggancia: il circuito è generato, e le sue curve "
             "non cadono dove sono sulla pista vera.")

# Le fasi di una stessa curva, scritte fra parentesi in coda al nome nella guida.
_FASE = re.compile(r"\s*\((ingresso|entrata|centro|uscita)\)\s*$", re.IGNORECASE)


class TrattoMotore(Protocol):
    numero: int
    ingresso: float
    uscita: float


@dataclass
class CurvaAgganciata:
    """Una curva della guida, con la sua ancora e il tratto del motore che la contiene."""

    n: int
    nome: str | None
    inizio: float
    apice: float
    uscita: float
    mappa: dict[str, float] | None
    tratto: int | None = None


@dataclass
class Aggancio:
    pista: str
    curve: list[CurvaAgganciata]
    # Numero del tratto del motore → il suo nome secondo la guida (solo i tratti che
    # contengono almeno una curva della guida).
    tratti: dict[int, str] = field(default_factory=dict)
    # Perché l'aggancio è vuoto, quando lo è per scelta (la demo).
    nota: str | None = None

    def come_json(self) -> dict[str, Any]:
        return {
            "pista": self.pista,
            "curve": [asdict(c) for c in self.curve],
            # Le chiavi JSON sono stringhe: il frontend le rilegge come numeri.
            "tratti": {str(k): v for k, v in self.tratti.items()},
            "nota": self.nota,
        }


def dentro(posizione: float, tratto: TrattoMotore) -> bool:
    """La posizione (0-1) cade nel tratto? Il tratto può scavalcare il traguardo."""
    inizio, fine = tratto.ingresso, tratto.uscita
    if inizio <= fine:
        return inizio <= posizione < fine
    return posizione >= inizio or posizione < fine


def tratto_di(posizione: float, tratti: Iterable[TrattoMotore]) -> int | None:
    for tratto in tratti:
        if dentro(posizione, tratto):
            return tratto.numero
    return None


def etichetta(curve: list[CurvaAgganciata]) -> str | None:
    """Il nome di un gruppo di curve della guida, come lo legge il pilota."""
    if not curve:
        return None
    curve = sorted(curve, key=lambda c: c.n)
    if len(curve) == 1:
        c = curve[0]
        return f"T{c.n} {c.nome}" if c.nome else f"T{c.n}"
    numeri = [c.n for c in curve]
    contigue = numeri == list(range(numeri[0], numeri[-1] + 1))
    sigla = f"T{numeri[0]}-T{numeri[-1]}" if contigue else ", ".join(f"T{n}" for n in numeri)
    nomi: list[str] = []
    for c in curve:
        if c.nome:
            base = _FASE.sub("", c.nome).strip()
            if base and base not in nomi:
                nomi.append(base)
    return f"{sigla} {' · '.join(nomi)}" if nomi else sigla


def curve_della_pista(track_id: str | None) -> list[CurvaAgganciata] | None:
    """Le curve della guida con le loro ancore, o None se la pista non è ancorata."""
    if not track_id:
        return None
    dati = ancore_mod.carica(track_id)
    if not dati or not isinstance(dati.get("ancore"), list):
        return None
    guida = catalog.track_guide(track_id) or {}
    nomi = {c.get("n"): c.get("nome") for c in guida.get("curve") or [] if isinstance(c, dict)}
    fuori: list[CurvaAgganciata] = []
    for a in dati["ancore"]:
        n = a.get("n")
        # La guida è la fonte del nome; l'ancora ne porta una copia presa al provino.
        nome = nomi[n] if n in nomi else a.get("nome")
        fuori.append(CurvaAgganciata(
            n=n, nome=nome, inizio=float(a["inizio"]), apice=float(a["apice"]),
            uscita=float(a["uscita"]), mappa=a.get("mappa"),
        ))
    return sorted(fuori, key=lambda c: c.n)


def aggancia(track_id: str | None, tratti: list[TrattoMotore] | None,
             demo: bool = False) -> Aggancio | None:
    """L'aggancio di una sessione. `tratti` None = niente analisi per curva (un giro solo):
    le curve della guida ci sono lo stesso, senza tratto, e bastano al grafico del confronto."""
    curve = curve_della_pista(track_id)
    if not curve:
        return None
    if demo:
        return Aggancio(pista=track_id or "", curve=[], nota=NOTA_DEMO)
    if tratti:
        for c in curve:
            c.tratto = tratto_di(c.apice, tratti)
    per_tratto: dict[int, list[CurvaAgganciata]] = {}
    for c in curve:
        if c.tratto is not None:
            per_tratto.setdefault(c.tratto, []).append(c)
    nomi = {numero: etichetta(gruppo) for numero, gruppo in per_tratto.items()}
    return Aggancio(pista=track_id or "", curve=curve,
                    tratti={k: v for k, v in sorted(nomi.items()) if v})
