#!/usr/bin/env python3
"""
estrai_appendici_acc.py — dalle appendici del documento ufficiale Kunos al file dati

Perche' esiste:
    Il PDF «ACC Shared Memory Documentation v1.8.12» (Kunos Simulazioni) non contiene
    solo la struttura delle tre pagine di memoria: le appendici 2-7 sono **tabelle di
    riferimento per vettura** che servono a leggere correttamente numeri che altrimenti
    sono indecifrabili —

      · Appendice 2  nome -> Kunos ID (lo slug che ACC scrive in `carName` e `carModel`)
      · Appendice 3  coefficiente della pressione freni (anteriore / posteriore)
      · Appendice 4  offset del brake bias (senza, il bias e' sbagliato di 5-22 punti)
      · Appendice 5  angolo di sterzo massimo (per dare un senso a steerAngle, -1..1)
      · Appendice 6  carModelId numerico -> vettura (i risultati dei SERVER usano questo)
      · Appendice 7  giri massimi del motore

    Ricopiarle a mano sarebbe 43 vetture x 6 colonne di occasioni di sbagliare. Questo
    script le legge dal PDF, le incrocia fra loro e le scrive in
    `app/core/data/acc_riferimenti_vetture.json`.

    L'appendice 1 (mainDisplayIndex: quale pagina del cruscotto mostra cosa) non viene
    estratta: non serve a nessuna analisi.

Come si usa:
    ./.venv/Scripts/python scripts/estrai_appendici_acc.py <percorso del PDF>

    Il PDF non sta nel repo (e' materiale di Kunos): si trova allegato alle
    implementazioni pubbliche della shared memory, p.es. nel repo PyAccSharedMemory.

Il metodo di lettura, in breve:
    Il testo estratto dal PDF conserva i marcatori di lingua (`en-US`, `de-DE`) che
    separano le celle della tabella. Il problema vero e' che i nomi delle vetture
    contengono numeri (l'anno) e che a volte il valore sta nella stessa cella del nome:
    si guarda allora quante celle di soli numeri seguono il nome, e solo se non bastano
    si prendono i numeri in coda al nome. Le sei appendici elencano le vetture nello
    stesso ordine: l'incrocio e' per posizione, e **ogni disaccordo fra i nomi viene
    stampato**, non risolto di nascosto.
"""

from __future__ import annotations

import json
import re
import sys
import zlib
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = Path(__file__).resolve().parents[1]
USCITA = BACKEND / "app" / "core" / "data" / "acc_riferimenti_vetture.json"
CATALOGO = BACKEND / "app" / "core" / "data" / "cars.json"

FONTE = "ACC Shared Memory Documentation v1.8.12 — Kunos Simulazioni, appendici 2-7"

MARKER = re.compile(r"(?:en-US|de-DE|en-GB)")
NUMERO = re.compile(r"-?\d+(?:\.\d+)?")
INTESTAZIONI = {
    "name", "carmodelid", "kunos id", "max rpm", "angle", "dash offset",
    "dash coefficient", "front", "rear", "middle engine", "front engine",
    "rear engine", "page 1", "page 2", "page 3", "page 4", "",
}
GRUPPI = re.compile(r"^(gt3\s*-?\s*20\d\d|gt4|challengers pack 20\d\d)$", re.I)
# I marcatori di lingua a volte spezzano un'intestazione a meta' («GT3 - | 2019»): i
# due pezzi non sono ne' vetture ne' valori. Nessun valore vero di queste tabelle
# somiglia a un anno (rpm 6450-9250, sterzo 180-450, bias negativo, id 0-61).
FRAMMENTI = re.compile(r"^(gt3\s*-?|gt4\s*-?|challengers pack|20[0-3]\d)$", re.I)


def testo_del_pdf(percorso: Path) -> str:
    """Estrae il testo dai flussi compressi del PDF. Niente dipendenze nuove."""
    grezzo = percorso.read_bytes()
    pezzi: list[str] = []
    for inizio_flusso in re.finditer(rb"stream\r?\n", grezzo):
        inizio = inizio_flusso.end()
        fine = grezzo.find(b"endstream", inizio)
        if fine < 0:
            continue
        try:
            dati = zlib.decompress(grezzo[inizio:fine])
        except zlib.error:
            continue
        if b"Tj" not in dati and b"TJ" not in dati:
            continue
        testo = []
        for pezzo in re.finditer(rb"\((?:\\.|[^\\()])*\)", dati):
            s = pezzo.group()[1:-1]
            s = s.replace(rb"\(", b"(").replace(rb"\)", b")").replace(rb"\\", b"\\")
            testo.append(s.decode("latin-1"))
        if testo:
            pezzi.append("".join(testo))
    return "\n".join(pezzi)


def sezione(testo: str, titolo: str, fine: str | None) -> str:
    i = testo.find(titolo)
    if i < 0:
        sys.exit(f"sezione non trovata nel PDF: {titolo}")
    inizio = i + len(titolo)
    # NB: la fine si cerca DOPO l'inizio — «see Appendix 4» compare molto prima.
    j = testo.find(fine, inizio) if fine else -1
    return testo[inizio: j if j > 0 else len(testo)]


def celle(sezione_testo: str) -> list[tuple[str, str | None]]:
    fuori: list[tuple[str, str | None]] = []
    gruppo: str | None = None
    for pezzo in MARKER.split(sezione_testo):
        cella = " ".join(pezzo.split())
        if cella.lower() in INTESTAZIONI:
            continue
        if GRUPPI.match(cella):
            gruppo = cella
            continue
        if FRAMMENTI.match(cella):
            continue
        fuori.append((cella, gruppo))
    return fuori


def leggi(sezione_testo: str, n_valori: int, slug: bool = False):
    """-> [(gruppo, nome, [valori])] nell'ordine del documento."""
    lista = celle(sezione_testo)
    if slug:
        def solo_valore(c: str) -> bool:
            return bool(re.fullmatch(r"[a-z0-9_]+", c))
    else:
        def solo_valore(c: str) -> bool:
            return bool(c) and bool(NUMERO.fullmatch(c.replace(" ", "")))

    fuori = []
    i = 0
    while i < len(lista):
        cella, gruppo = lista[i]
        if not cella or solo_valore(cella):
            i += 1
            continue
        seguenti: list[str] = []
        j = i + 1
        while j < len(lista) and len(seguenti) < n_valori and solo_valore(lista[j][0]):
            seguenti.append(lista[j][0])
            j += 1
        mancanti = n_valori - len(seguenti)
        nome = cella
        in_coda: list[str] = []
        if mancanti > 0 and not slug:
            numeri = NUMERO.findall(cella)
            in_coda = numeri[-mancanti:] if len(numeri) >= mancanti else []
            for n in in_coda:
                nome = nome[: nome.rfind(n)].strip()
        valori = in_coda + seguenti
        if valori:
            fuori.append((gruppo, nome, valori))
        i = j
    return fuori


def normalizza(nome: str) -> str:
    return re.sub(r"[^a-z0-9]", "", nome.lower())


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip().splitlines()[-1] + "\n\nManca il percorso del PDF.")
    pdf = Path(sys.argv[1])
    if not pdf.exists():
        sys.exit(f"PDF non trovato: {pdf}")

    testo = testo_del_pdf(pdf)
    appendici = {
        "slug": leggi(sezione(testo, "Appendix 2  carModel", "Appendix 3"), 1, slug=True),
        "freni": leggi(sezione(testo, "Appendix 3  brakePressure", "Appendix 4"), 2),
        "bias": leggi(sezione(testo, "Appendix 4  brakeBias", "Appendix 5"), 1),
        "sterzo": leggi(sezione(testo, "Appendix 5  Max Steering Angle", "Appendix 6"), 1),
        "id": leggi(sezione(testo, "Appendix 6  CarModelId", "Appendix 7"), 1),
        "rpm": leggi(sezione(testo, "Appendix 7  Max RPM", None), 1),
    }
    for nome, dati in appendici.items():
        print(f"  appendice {nome:7} {len(dati)} vetture")
    lunghezze = {len(d) for d in appendici.values()}
    if len(lunghezze) != 1:
        sys.exit(f"le appendici non hanno lo stesso numero di vetture: {lunghezze}")

    vetture = []
    divergenze = []
    for i, (gruppo, nome, valore) in enumerate(appendici["slug"]):
        nomi = {normalizza(app[i][1]) for app in appendici.values()}
        if len(nomi) > 1:
            divergenze.append({"acc_car_id": valore[0], "nomi": sorted(nomi)})
        vetture.append({
            "acc_car_id": valore[0],
            "nome_documento": nome,
            "gruppo": gruppo,
            "car_model_id": int(appendici["id"][i][2][0]),
            "brake_bias_offset": int(appendici["bias"][i][2][0]),
            "brake_pressure_coeff_front": float(appendici["freni"][i][2][0]),
            "brake_pressure_coeff_rear": float(appendici["freni"][i][2][1]),
            "max_steering_angle_deg": int(appendici["sterzo"][i][2][0]),
            "max_rpm": int(appendici["rpm"][i][2][0]),
        })

    if divergenze:
        print("\n  nomi che non coincidono fra le appendici (refusi del documento):")
        for d in divergenze:
            print(f"    {d['acc_car_id']}: {d['nomi']}")

    # Incrocio col catalogo del progetto: cosa copriamo e cosa no.
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    con_riferimenti = {v["acc_car_id"] for v in vetture}
    senza = sorted(
        c["acc_car_id"] for c in catalogo if c["acc_car_id"] not in con_riferimenti
    )

    documento = {
        "fonte": FONTE,
        "estratto_il": date.today().isoformat(),
        "estratto_da": "backend/scripts/estrai_appendici_acc.py",
        "avvertenze": [
            "Il documento si ferma alla versione 1.8.12: le vetture uscite dopo "
            "(GT3 2023, Ford Mustang GT3, GT2 pack) NON hanno riferimenti qui. "
            "Vanno dichiarate mancanti, mai stimate.",
            "brake_bias_offset e brake_pressure_coeff sono le tabelle del documento; "
            "l'aritmetica esatta per arrivare al valore mostrato sul cruscotto NON e' "
            "scritta nel documento. Finche' non e' verificata in gioco, PitWall "
            "conserva il valore grezzo e non converte (decisione 7 del rework).",
            "max_steering_angle_deg e' l'angolo totale lock-to-lock dichiarato dal "
            "documento; la conversione di steerAngle (-1..1) in gradi resta da "
            "verificare a schermo.",
        ],
        "conversioni": {
            "brake_bias": {"stato": "da_verificare_in_gioco",
                           "nota": "offset per vettura, da sommare al valore mostrato"},
            "brake_pressure": {"stato": "da_verificare_in_gioco",
                               "nota": "coefficiente per vettura, anteriore e posteriore"},
            "steer_angle": {"stato": "da_verificare_in_gioco",
                            "nota": "angolo massimo lock-to-lock in gradi"},
            "max_rpm": {"stato": "verificato_nel_documento",
                        "nota": "giri massimi del motore, valore diretto"},
        },
        "divergenze_di_nome_nel_documento": divergenze,
        "vetture_del_catalogo_senza_riferimenti": senza,
        "vetture": vetture,
    }
    USCITA.write_text(
        json.dumps(documento, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\n  {len(vetture)} vetture scritte in {USCITA.relative_to(BACKEND)}")
    print(f"  vetture del catalogo senza riferimenti: {len(senza)} -> {senza}")


if __name__ == "__main__":
    main()
