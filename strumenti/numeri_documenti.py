"""strumenti/numeri_documenti.py — i numeri dei documenti li scrive il codice.

Il 05/10/2026 README e `docs/03` dicevano ancora «19 file, 1005 test» e una roadmap di
settembre: righe scritte a mano che nessuno aveva più toccato. Da qui in poi:

* **conteggi dei test**: vengono da `strumenti/numeri.json`, che `verifica.py` riscrive a
  ogni giro verde. Questo script li porta nei due README e in `docs/03`.
* **rotte dell'API**: ogni rotta del backend deve comparire nelle tabelle dei due README.
  Lo script non scrive le descrizioni (sono parole), ma dice quali rotte mancano.

    python strumenti/numeri_documenti.py             riscrive i conteggi, elenca le rotte mancanti
    python strumenti/numeri_documenti.py --controlla non scrive: esce con 1 se qualcosa è indietro
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

RADICE = Path(__file__).resolve().parents[1]
NUMERI = Path(__file__).resolve().parent / "numeri.json"
README = (RADICE / "README.md", RADICE / "README.it.md")
ARCHITETTURA = RADICE / "docs" / "03-v2-architecture.md"
API = RADICE / "backend" / "app" / "api"


def leggi(p: Path) -> tuple[str, bool]:
    testo = p.read_bytes().decode("utf-8")
    return testo.replace("\r\n", "\n"), "\r\n" in testo


def scrivi(p: Path, testo: str, crlf: bool) -> None:
    p.write_bytes((testo.replace("\n", "\r\n") if crlf else testo).encode("utf-8"))


def elenco_test(numeri: dict, intestazione: str) -> str:
    """Il commento dell'albero delle cartelle nei README, a capo ogni ~85 colonne."""
    voci = [f"{nome.removeprefix('test_').removesuffix('.py')} {n}" for nome, n in numeri["per_file"].items()]
    righe, riga = [], f"    tests/       # {intestazione}:"
    for i, voce in enumerate(voci):
        pezzo = f" {voce}" + ("," if i < len(voci) - 1 else "")
        if len(riga) + len(pezzo) > 92:
            righe.append(riga)
            riga = "                 #" + pezzo
        else:
            riga += pezzo
    righe.append(riga)
    return "\n".join(righe) + "\n"


def rotte_del_codice() -> list[tuple[str, str]]:
    rotte = []
    for file in sorted(API.glob("*.py")):
        for metodo, percorso in re.findall(r'@router\.(get|post|put|delete)\(\s*"([^"]+)"', file.read_text(encoding="utf-8")):
            rotte.append((metodo.upper(), "/api" + percorso))
    return rotte


def main() -> int:
    controlla = "--controlla" in sys.argv
    if not NUMERI.exists():
        print("manca strumenti/numeri.json: lancia prima strumenti/verifica.py")
        return 1
    numeri = json.loads(NUMERI.read_text(encoding="utf-8"))
    indietro: list[str] = []

    blocco = re.compile(r"    tests/       # .*?\n(?=  scripts/)", re.S)
    for p, intestazione in zip(README, (f"{numeri['test']} offline tests in {numeri['file']} files",
                                         f"{numeri['test']} test offline in {numeri['file']} file")):
        testo, crlf = leggi(p)
        nuovo, n = blocco.subn(lambda _: elenco_test(numeri, intestazione), testo)
        if n != 1:
            indietro.append(f"{p.name}: riga dei test non trovata")
        elif nuovo != testo:
            indietro.append(f"{p.name}: conteggio dei test")
            if not controlla:
                scrivi(p, nuovo, crlf)

    testo, crlf = leggi(ARCHITETTURA)
    nuovo = re.sub(r"\*\*`tests/`\*\*: \d+ file, \d+ test offline",
                   f"**`tests/`**: {numeri['file']} file, {numeri['test']} test offline", testo)
    nuovo = re.sub(r"Backend: \d+ file di test in `app/tests/`, \*\*\d+\*\* test",
                   f"Backend: {numeri['file']} file di test in `app/tests/`, **{numeri['test']}** test", nuovo)
    if nuovo != testo:
        indietro.append("docs/03: conteggio dei test")
        if not controlla:
            scrivi(ARCHITETTURA, nuovo, crlf)

    # Le rotte: ognuna deve comparire nei due README. I segnaposto ({id}, {id_sessione}…)
    # si confrontano senza guardare il nome fra le graffe.
    def norma(s: str) -> str:
        return re.sub(r"\{[^}]+\}", "{}", s)

    mancanti = []
    for p in README:
        testo = norma(leggi(p)[0])
        for metodo, percorso in rotte_del_codice():
            ultimo = "/" + percorso.rsplit("/", 1)[-1]
            # nelle tabelle due rotte sorelle stanno a volte su una riga («/avvia · /ferma»)
            if norma(percorso) not in testo and f"· `{ultimo}`" not in testo:
                mancanti.append(f"{p.name}: {metodo} {percorso}")

    if controlla:
        problemi = indietro + mancanti
        if problemi:
            print("documenti indietro: " + "; ".join(problemi[:6]) + (f" (+{len(problemi) - 6})" if len(problemi) > 6 else ""))
            return 1
        print(f"{numeri['test']} test in {numeri['file']} file e {len(rotte_del_codice())} rotte: i documenti sono allineati")
        return 0
    print("riscritti: " + ("; ".join(indietro) if indietro else "niente da riscrivere"))
    if mancanti:
        print("rotte che mancano nelle tabelle (la descrizione va scritta a mano):")
        for m in mancanti:
            print("  -", m)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
