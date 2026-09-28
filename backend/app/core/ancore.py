"""Le ancore delle curve: dove sta, sul giro e sulla mappa, ogni curva della guida.

Perché esistono. Il motore (`analisi/curve.py`) trova le curve dai minimi di velocità
e le numera da sé: le curve in pieno per lui non esistono, una chicane è un minimo solo
per due curve della guida, e su un giro solo il numero delle curve che trova cambia da
una sessione all'altra (Zandvoort, stessa auto e stesso giorno: 10, 8 e 9). La sua
«curva 4» quindi non è la T4 della guida, e non lo sarà mai per costruzione.

L'ancora è il ponte, fissato una volta per pista e confermato a occhio da Edoardo nel
provino: per ogni curva della guida tre posizioni sul giro (0-1, la stessa scala di
`graphics.normalizedCarPosition`) e il **punto sulla mappa verificata** (frazioni della
larghezza e dell'altezza dell'immagine) su cui zoomare. Le tre posizioni (schema 2, dal
28/09/2026, dopo il primo provino) sono le fasi della curva:

* **inizio**: dove la curva comincia per chi guida — il punto di frenata, o l'inserimento
  se la curva si fa in pieno. È il riferimento che conta (decisione di Edoardo);
* **apice**: il minimo di velocità, o il picco di carico laterale se il minimo non c'è;
* **uscita**: dove il carico laterale torna sotto la soglia. Un file per pista in
`data/tracks_anchors/<id>.json`, separato dalla guida: la guida è testo cercato sulle
fonti, le ancore sono misure prese sulla telemetria, e hanno vite diverse.

Qui ci sono solo il formato e il suo controllo: niente numpy, niente telemetria, così
lo può importare anche `scripts/check_track_knowledge.py`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"
ANCORE_DIR = DATA_DIR / "tracks_anchors"
GUIDE_DIR = DATA_DIR / "tracks_knowledge"

SCHEMA = 2

# Da dove viene ciascuna posizione: calcolata dalla telemetria, oppure cliccata da Edoardo.
METODI = {
    "inizio": {"frenata", "inserimento", "click"},
    "apice": {"minimo", "picco_g_lat", "click"},
    "uscita": {"carico", "click"},
}
FASI = ("inizio", "apice", "uscita")
MAX_FASE = 0.25     # fra inizio e apice, e fra apice e uscita, al massimo un quarto di giro

CAMPI = ["id", "schema", "sessione_origine", "vettura", "giro", "tempo_giro_ms",
         "mappa_commons", "creato_il", "ancore"]


def percorso(track_id: str) -> Path:
    return ANCORE_DIR / f"{track_id}.json"


def carica(track_id: str) -> dict[str, Any] | None:
    """Le ancore di una pista, o None se non ci sono."""
    try:
        dati = json.loads(percorso(track_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dati if isinstance(dati, dict) else None


def _numero(valore: Any) -> bool:
    return isinstance(valore, (int, float)) and not isinstance(valore, bool)


def valida_ancore(
    dati: dict[str, Any],
    guida: dict[str, Any] | None,
    mappa: dict[str, Any] | None,
    atteso_id: str | None = None,
) -> list[str]:
    """Gli errori di un file di ancore (lista vuota = conforme).

    `guida` è la guida della stessa pista, `mappa` il blocco `assets.map` della pista in
    `tracks.json`. Un'ancora vale solo se la guida e la mappa sono ancora quelle su cui è
    stata presa: se la guida viene rinumerata o la mappa sostituita, le ancore vanno
    rifatte, e questo controllo lo dice invece di lasciarle puntare nel posto sbagliato.
    """
    errori: list[str] = []
    for campo in CAMPI:
        if campo not in dati:
            errori.append(f"manca il campo `{campo}`")
    if errori:
        return errori

    if atteso_id is not None and dati["id"] != atteso_id:
        errori.append(f"il file è di «{atteso_id}» ma dentro l'id è «{dati['id']}»")
    if dati["schema"] != SCHEMA:
        errori.append(f"schema {dati['schema']!r}, atteso {SCHEMA}")
    if not str(dati["sessione_origine"] or "").strip():
        errori.append("`sessione_origine` vuota: non si sa da quale giro vengono le posizioni")

    # --- la mappa: deve essere quella verificata di oggi
    if not mappa or mappa.get("status") != "verificata":
        errori.append("la pista non ha una mappa verificata: le coordinate non hanno un disegno su cui stare")
    elif dati["mappa_commons"] != mappa.get("commons_file"):
        errori.append(f"ancore prese su «{dati['mappa_commons']}» ma la mappa verificata ora è "
                      f"«{mappa.get('commons_file')}»: i punti sulla mappa vanno rifatti")

    # --- la guida: stesse curve, stessi nomi, stesso ordine
    curve = (guida or {}).get("curve") or []
    if not curve:
        errori.append("la pista non ha una guida: non c'è niente da ancorare")
    ancore = dati["ancore"]
    if not isinstance(ancore, list):
        return errori + ["`ancore` non è una lista"]
    if curve and len(ancore) != len(curve):
        errori.append(f"{len(ancore)} ancore per {len(curve)} curve della guida: ne serve una per curva")
    numeri = [a.get("n") for a in ancore]
    if numeri != list(range(1, len(ancore) + 1)):
        errori.append(f"numerazione non contigua da 1: {numeri}")

    per_n = {c.get("n"): c for c in curve}
    posizioni: list[float] = []
    for a in ancore:
        dove = f"T{a.get('n')}"
        curva = per_n.get(a.get("n"))
        if curva is not None and a.get("nome") != curva.get("nome"):
            errori.append(f"{dove}: nome «{a.get('nome')}» ma nella guida è «{curva.get('nome')}» "
                          f"(guida rinumerata? le ancore vanno rifatte)")
        valide = True
        for fase in FASI:
            pos = a.get(fase)
            if not _numero(pos) or not 0.0 <= pos < 1.0:
                errori.append(f"{dove}: {fase} {pos!r} fuori da [0, 1)")
                valide = False
            metodo = a.get(f"metodo_{fase}")
            if metodo not in METODI[fase]:
                errori.append(f"{dove}: metodo_{fase} «{metodo}» fuori da {sorted(METODI[fase])}")
        if valide:
            posizioni.append(float(a["inizio"]))
            # le fasi in fila: inizio → apice → uscita (sull'anello, dentro un quarto di giro)
            for da, a_ in (("inizio", "apice"), ("apice", "uscita")):
                passo = (a[a_] - a[da]) % 1.0
                if passo > MAX_FASE:
                    errori.append(f"{dove}: {a_} ({a[a_]}) non viene dopo {da} ({a[da]})")
        punto = a.get("mappa")
        if not isinstance(punto, dict) or not all(
            _numero(punto.get(k)) and 0.0 <= punto[k] <= 1.0 for k in ("x", "y")
        ):
            errori.append(f"{dove}: punto sulla mappa {punto!r} non valido (x e y fra 0 e 1)")

    # --- l'ordine: gli inizi delle curve si incontrano in fila lungo il giro. È ammesso UN salto
    # all'indietro, per le piste in cui la T1 della guida sta prima della linea del
    # traguardo (il giro di ACC comincia alla linea, la guida dalla prima curva).
    if len(posizioni) == len(ancore) and len(posizioni) > 1:
        salti = sum(1 for p, q in zip(posizioni, posizioni[1:]) if q <= p)
        if not (salti == 0 or (salti == 1 and posizioni[-1] < posizioni[0])):
            errori.append(f"inizi delle curve non in ordine lungo il giro: {posizioni}")
    return errori
