#!/usr/bin/env python3
"""
estrai_campi_acc.py — la descrizione ufficiale di ogni campo della shared memory

Perche' esiste:
    Il dizionario dei canali di PitWall deve dire, per ogni numero registrato, che
    cosa sia. Scrivere 200 descrizioni a mano significa scriverne qualcuna sbagliata:
    queste le scrive Kunos. Lo script legge le tre tabelle dei campi dal documento
    ufficiale («ACC Shared Memory Documentation v1.8.12») e le incrocia con le
    strutture di `app/telemetria/strutture.py`.

    L'incrocio e' il controllo vero: un campo descritto nel documento ma assente
    dalla struttura (o viceversa) vuol dire che la struttura e' sbagliata, ed e'
    esattamente l'errore che non si vedrebbe mai a schermo.

Come si usa:
    ./.venv/Scripts/python scripts/estrai_campi_acc.py <percorso del PDF>

Scrive `app/core/data/acc_campi_shared_memory.json`.
"""

from __future__ import annotations

import ctypes
import json
import re
import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.telemetria import strutture as s  # noqa: E402
from scripts.estrai_appendici_acc import testo_del_pdf  # noqa: E402

USCITA = BACKEND / "app" / "core" / "data" / "acc_campi_shared_memory.json"
FONTE = "ACC Shared Memory Documentation v1.8.12 — Kunos Simulazioni"

TIPI = r"(?:float|int|wchar_t|char|bool|unsigned|ACC_[A-Z_]+)"
CAMPO = re.compile(
    rf"(?P<tipo>{TIPI})\s+(?P<nome>\w+)\s*(?P<dim>(?:\s*\[\d+\])*)\s*"
    rf"(?P<desc>.*?)(?=\s{TIPI}\s+\w|$)",
    re.IGNORECASE | re.DOTALL,
)

SEZIONI = {
    "physics": ("SPageFilePhysics", "SPageFileGraphic"),
    "graphics": ("SPageFileGraphic", "SPageFileStatic"),
    "static": ("SPageFileStatic", "Enums"),
}


def pulisci(testo: str) -> str:
    testo = re.sub(r"(?:en-US|de-DE|en-GB)", " ", testo)
    testo = testo.replace("\\", "")
    return re.sub(r"\s+", " ", testo)


def descrizioni(testo: str, inizio: str, fine: str) -> dict[str, dict[str, str]]:
    i = testo.find(inizio)
    j = testo.find(fine, i + len(inizio))
    pezzo = pulisci(testo[i: j if j > 0 else len(testo)])
    fuori: dict[str, dict[str, str]] = {}
    for m in CAMPO.finditer(pezzo):
        nome = m.group("nome")
        desc = " ".join(m.group("desc").split()).strip(" .")
        fuori[nome] = {
            "tipo_documento": m.group("tipo").lower() + m.group("dim").replace(" ", ""),
            "descrizione": desc,
        }
    return fuori


def normalizza(nome: str) -> str:
    """I nomi divergono per maiuscole/minuscole fra documento e struttura."""
    return nome.lower()


# Refusi del documento: a sinistra il nostro nome, a destra come e' scritto nel PDF.
ALIAS = {
    "secondarydisplayindex": "secondarydisplyindex",
}


def ripesca(pezzo: str, nome: str, nomi_struttura: set[str]) -> str:
    """Seconda passata per i campi che la prima non ha agganciato.

    Serve per i campi con tipo enum: nel documento si leggono come
    «ACC_SESSION_TYPE session See enums ACC_SESSION_TYPE», e una regola basata sul
    tipo li spezza nel punto sbagliato. Qui si cerca il nome del campo e si prende
    il testo fino al campo successivo, qualunque tipo abbia.
    """
    m = re.search(rf"\b{re.escape(nome)}\b", pezzo, re.IGNORECASE)
    if not m:
        return ""
    resto = pezzo[m.end():]
    fine = len(resto)
    for altro in nomi_struttura:
        if altro.lower() == nome.lower():
            continue
        a = re.search(rf"\b{re.escape(altro)}\b", resto, re.IGNORECASE)
        if a and a.start() < fine:
            fine = a.start()
    testo = " ".join(resto[:fine].split()).strip(" .")
    # via il tipo del campo successivo rimasto in coda, e le righe di tabella
    testo = re.sub(rf"\s*{TIPI}\s*$", "", testo, flags=re.IGNORECASE).strip()
    return testo


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Manca il percorso del PDF.")
    pdf = Path(sys.argv[1])
    if not pdf.exists():
        sys.exit(f"PDF non trovato: {pdf}")
    testo = testo_del_pdf(pdf)

    documento: dict[str, object] = {
        "fonte": FONTE,
        "estratto_il": date.today().isoformat(),
        "estratto_da": "backend/scripts/estrai_campi_acc.py",
        "nota": (
            "Descrizioni dei campi copiate dal documento ufficiale e incrociate con "
            "app/telemetria/strutture.py. `usato_da_acc` viene dalla lista "
            "CAMPI_NON_USATI, che a sua volta traduce le marcature «Not used / Not "
            "shown in ACC» del documento."
        ),
        "pagine": {},
    }

    tutto_bene = True
    for pagina, (inizio, fine) in SEZIONI.items():
        lette = descrizioni(testo, inizio, fine)
        per_nome = {normalizza(k): v for k, v in lette.items()}
        struttura = s.PAGINE[pagina][1]
        non_usati = s.CAMPI_NON_USATI.get(pagina, frozenset())
        i = testo.find(inizio)
        j = testo.find(fine, i + len(inizio))
        pezzo = pulisci(testo[i: j if j > 0 else len(testo)])
        nomi_struttura = {n for n, _ in struttura._fields_}

        campi = {}
        senza_descrizione = []
        for nome, _tipo in struttura._fields_:
            descrittore = getattr(struttura, nome)
            chiave = normalizza(nome)
            voce = per_nome.get(chiave) or per_nome.get(ALIAS.get(chiave, ""))
            if voce is None:
                ripescata = ripesca(pezzo, ALIAS.get(chiave, nome), nomi_struttura)
                if ripescata:
                    voce = {"tipo_documento": "", "descrizione": ripescata}
            if voce is None:
                senza_descrizione.append(nome)
            campi[nome] = {
                "offset": descrittore.offset,
                "byte": descrittore.size,
                "tipo_documento": (voce or {}).get("tipo_documento", ""),
                "descrizione": (voce or {}).get("descrizione", ""),
                "usato_da_acc": nome not in non_usati,
            }

        # «Solo nel documento» va ripulito dai residui della lettura: i nomi dei tipi
        # (le righe enum si leggono come «ACC_STATUS status»), la parola `int`/
        # `wchar_t` rimasta appesa, e i refusi noti del PDF. Quello che resta e' un
        # campo vero che manca dalla struttura: quello si', va guardato a mano.
        nella_struttura = {normalizza(n) for n, _ in struttura._fields_}
        rumore = set(ALIAS.values()) | {"int", "float", "wchar_t", "char", "bool"}
        solo_nel_documento = sorted(
            n for n in set(per_nome) - nella_struttura
            if n not in rumore and not n.startswith("acc_")
        )

        documento["pagine"][pagina] = {  # type: ignore[index]
            "mappa": s.PAGINE[pagina][0],
            "byte": ctypes.sizeof(struttura),
            "campi": campi,
        }
        print(f"  {pagina:9} {len(campi)} campi · "
              f"{len(campi) - len(senza_descrizione)} con descrizione ufficiale")
        if senza_descrizione:
            print(f"     senza descrizione: {senza_descrizione}")
        if solo_nel_documento:
            tutto_bene = False
            print(f"     !! nel documento ma non nella struttura: {solo_nel_documento}")

    USCITA.write_text(
        json.dumps(documento, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n  scritto {USCITA.relative_to(BACKEND)}")
    if not tutto_bene:
        print("  ATTENZIONE: differenze fra documento e struttura, da guardare a mano.")


if __name__ == "__main__":
    main()
