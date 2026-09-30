"""scripts/accenti_guide.py — gli accenti veri nelle guide dei tracciati (Entry #055).

Perche' esiste:
    le guide arrivano scritte con gli accenti in apostrofo («e'», «piu'», «velocita'»,
    «perche'»), e a schermo si leggono cosi'. Questo script li converte nel carattere
    giusto, parola per parola, senza toccare altro: lavora sul testo del file (non
    ricarica e riscrive il JSON), quindi indentazione e ordine delle chiavi restano.

Regole:
    * solo le parole della tabella qui sotto, e solo se l'apostrofo non e' seguito da
      una lettera (le elisioni «l'uscita», «dell'Arie» non si toccano);
    * restano come sono «po'», l'imperativo «sta'», le elisioni davanti a un numero
      («all'80%») e le parole fra virgolette singole ('sicura', '2002-present');
    * una parola con l'apostrofo finale che non e' in tabella ferma lo script: si
      guarda il contesto e si decide, non si indovina.

Uso (dalla cartella backend/):
    ./.venv/Scripts/python scripts/accenti_guide.py          # converte
    ./.venv/Scripts/python scripts/accenti_guide.py --prova  # dice cosa cambierebbe
"""

from __future__ import annotations

import io
import json
import pathlib
import re
import sys

GUIDE = pathlib.Path(__file__).resolve().parents[1] / "app" / "core" / "data" / "tracks_knowledge"

# grave sulla e aperta e sulle altre vocali; acuto sulla e chiusa (perché, né, sé)
ACCENTI = {
    "e": "è", "E": "È", "cioe": "cioè",
    "piu": "più", "Piu": "Più", "giu": "giù",
    "gia": "già", "meta": "metà",
    "puo": "può", "pero": "però",
    "perche": "perché", "finche": "finché", "purche": "purché",
    "ne": "né", "se": "sé", "si": "sì",
    "cosi": "così", "Cosi": "Così", "li": "lì", "Li": "Lì",
    "da": "dà",
    "mori": "morì", "ospito": "ospitò", "negozio": "negoziò",
}
# -ità: velocità, stabilità, difficoltà, penalità, realtà…
FINALE_ITA = re.compile(r"^[A-Za-z]+it$|^[A-Za-z]*olt$|^realt$|^Realt$")

# lasciate apposta così (vedi le regole sopra)
RESTANO = {"po", "sta", "all", "dell", "abusare", "sicura", "present"}

PAROLA = re.compile(r"\b([A-Za-z]+)'(?![A-Za-zÀ-ÿ])")


def converti(testo: str) -> tuple[str, dict[str, int], list[str]]:
    contate: dict[str, int] = {}
    ignote: list[str] = []

    def sostituisci(m: re.Match[str]) -> str:
        w = m.group(1)
        if w in RESTANO:
            return m.group(0)
        if w in ACCENTI:
            nuova = ACCENTI[w]
        elif w.endswith("a") and FINALE_ITA.match(w[:-1]):
            nuova = w[:-1] + "à"
        else:
            ignote.append(w)
            return m.group(0)
        contate[w] = contate.get(w, 0) + 1
        return nuova

    return PAROLA.sub(sostituisci, testo), contate, ignote


def main() -> int:
    prova = "--prova" in sys.argv
    totale = 0
    problemi: list[str] = []
    for f in sorted(GUIDE.glob("*.json")):
        testo = io.open(f, encoding="utf-8").read()
        nuovo, contate, ignote = converti(testo)
        if ignote:
            problemi.append(f"{f.name}: parole non in tabella {sorted(set(ignote))}")
            continue
        json.loads(nuovo)  # il file deve restare JSON valido
        n = sum(contate.values())
        totale += n
        print(f"{f.name}: {n} accenti")
        if n and not prova:
            io.open(f, "w", encoding="utf-8", newline="").write(nuovo)
    if problemi:
        print("\n".join(["FERMO:"] + problemi))
        return 1
    print(f"totale {totale}{' (prova, nessun file scritto)' if prova else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
