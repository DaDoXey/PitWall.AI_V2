#!/usr/bin/env python3
"""
check_track_knowledge.py — controlla le guide dei tracciati consegnate

Perche' esiste:
    Le guide arrivano da Claude Desktop a blocchi di 5 circuiti. Il primo l'ho
    letto a mano, curva per curva: 38 curve, un errore trovato. Su tutti e 25 i
    circuiti sono ~450 curve, e leggerle tutte a mano ogni volta che arriva un
    blocco non e' un metodo, e' una speranza. Questo script fa i controlli che
    una macchina puo' fare davvero, e soprattutto dice a voce alta cosa NON
    puo' controllare, cosi' l'occhio umano si concentra li'.

    Non giudica il contenuto di guida: se un riferimento di frenata e' giusto
    lo sa solo chi ci ha girato. Controlla la COERENZA — che e' dove sono
    finiti gli errori veri.

Il controllo che conta davvero (lato gomma):
    In curva a destra si carica il lato SINISTRO, e viceversa. E' il campo che
    Gigi userebbe per interpretare le temperature: sbagliato, da una lettura
    ribaltata. Quando il testo dichiara il senso della curva il controllo e'
    esatto; quando NON lo dichiara nessuno puo' verificarlo, e lo script lo
    dice invece di far finta di niente (e' il caso in cui era passata
    inosservata "La Source, anteriore destro" su un tornante destro).

Uso:
    python backend/scripts/check_track_knowledge.py
    python backend/scripts/check_track_knowledge.py --solo spa_francorchamps
    python backend/scripts/check_track_knowledge.py --severita errori

Esce con codice 1 se trova almeno un ERRORE (utile in un eventuale controllo
automatico); i DA CONTROLLARE non fanno fallire nulla: sono lavoro per Edoardo.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _ROOT / "backend" / "app" / "core" / "data"
KNOW_DIR = _DATA_DIR / "tracks_knowledge"

TIPI = {"lenta", "media", "veloce"}
CONFIDENZE = {"alta", "media", "bassa"}
ORIGINI = {"fonte", "mestiere"}
STRESS = {"nullo", "basso", "medio", "medio-alto", "alto", "molto alto"}
RISCHI = {"basso", "medio", "alto"}

# Campi che ogni curva deve avere. Mancarne uno non e' un dettaglio: la scheda
# a schermo mostrera' un buco, e Gigi non avra' niente da dire su quella curva.
CAMPI_CURVA = ["n", "nome", "tipo", "marcia_indicativa", "riferimento_frenata",
               "insidia", "costo_errore", "sorpasso", "gomme", "freni",
               "track_limits", "differenza_gara_qualifica", "origine", "confidence"]

CAMPI_PISTA = ["id", "verifica_catalogo", "settori", "curve", "track_limits_generale",
               "pit", "traffico_multiclass", "meteo_e_luce", "gomme_e_freni_pista",
               "errore_del_principiante", "gt3_ref_lap_time", "gt3_fuel_per_lap_l",
               "chicche", "fonti"]

_DESTRA = re.compile(r"\b(a destra|destra|destro|tornante destro)\b", re.I)
_SINISTRA = re.compile(r"\b(a sinistra|sinistra|sinistro|tornante sinistro)\b", re.I)


class Esito:
    def __init__(self) -> None:
        self.errori: list[str] = []
        self.controlli: list[str] = []

    def errore(self, dove: str, testo: str) -> None:
        self.errori.append(f"{dove}: {testo}")

    def controlla(self, dove: str, testo: str) -> None:
        self.controlli.append(f"{dove}: {testo}")


def senso_dichiarato(curva: dict) -> str | None:
    """Destra o sinistra: dal campo `direzione` se c'e', altrimenti dal testo.

    Il campo esplicito e' la strada giusta e va chiesto nelle consegne future:
    con `direzione` il controllo del lato gomma diventa esatto su tutte le
    curve. Senza, si legge la prosa — e la prosa spesso il senso non lo dice
    proprio (La Source e' un tornante DESTRO, ma nessun campo di quella curva
    lo scrive, quindi nessun controllo automatico puo' accorgersene).

    Si guardano solo i campi descrittivi (nome, insidia, frenata, costo): NON
    `gomme.stress`, che e' proprio il campo da verificare — usarlo come fonte
    del senso renderebbe il controllo circolare e sempre verde.
    """
    esplicita = str(curva.get("direzione") or "").strip().lower()
    if esplicita in ("destra", "sinistra"):
        return esplicita

    testo = " ".join(str(curva.get(k) or "") for k in
                     ("nome", "insidia", "riferimento_frenata", "costo_errore"))
    d, s = bool(_DESTRA.search(testo)), bool(_SINISTRA.search(testo))
    if d and not s:
        return "destra"
    if s and not d:
        return "sinistra"
    return None          # non dichiarato, oppure ne nomina due (una sequenza)


def controlla_lato_gomma(cid: str, curva: dict, e: Esito) -> None:
    stress = str((curva.get("gomme") or {}).get("stress") or "")
    m = re.search(r"anteriore\s+(destro|sinistro)", stress, re.I)
    dove = f"{cid} T{curva.get('n')}"
    if not m:
        return                                   # stress generico ("basso", "tutte")
    lato = m.group(1).lower()
    senso = senso_dichiarato(curva)
    if senso is None:
        e.controlla(dove, f"lato gomma «anteriore {lato}» non verificabile: la curva "
                          f"non dichiara nel testo se gira a destra o a sinistra")
        return
    atteso = "sinistro" if senso == "destra" else "destro"
    if lato != atteso:
        e.errore(dove, f"curva a {senso} ma carico sull'anteriore {lato}: "
                       f"in curva a {senso} si carica l'anteriore {atteso}")


def controlla_curva(cid: str, curva: dict, e: Esito) -> None:
    dove = f"{cid} T{curva.get('n')}"
    for campo in CAMPI_CURVA:
        if campo not in curva:
            e.errore(dove, f"manca il campo `{campo}`")
    if curva.get("tipo") not in TIPI:
        e.errore(dove, f"tipo «{curva.get('tipo')}» fuori da {sorted(TIPI)}")
    if curva.get("confidence") not in CONFIDENZE:
        e.errore(dove, f"confidence «{curva.get('confidence')}» fuori da {sorted(CONFIDENZE)}")
    if curva.get("origine") not in ORIGINI:
        e.errore(dove, f"origine «{curva.get('origine')}» fuori da {sorted(ORIGINI)}")

    freni = (curva.get("freni") or {}).get("stress")
    if freni not in STRESS:
        e.controlla(dove, f"freni.stress «{freni}» non e' uno dei valori usati altrove "
                          f"({sorted(STRESS)}): vocabolario da uniformare")
    tl = (curva.get("track_limits") or {}).get("rischio")
    if tl not in RISCHI:
        e.controlla(dove, f"track_limits.rischio «{tl}» fuori da {sorted(RISCHI)}")

    sorp = curva.get("sorpasso") or {}
    if sorp.get("possibile") and not sorp.get("come"):
        e.errore(dove, "sorpasso dichiarato possibile ma `come` e' vuoto")
    if sorp.get("possibile") and not sorp.get("come_ci_si_difende"):
        e.controlla(dove, "sorpasso possibile ma non e' detto come ci si difende")

    controlla_lato_gomma(cid, curva, e)


def controlla_pista(percorso: Path, tracks: dict, e: Esito) -> None:
    dati = json.loads(percorso.read_text(encoding="utf-8"))
    cid = dati.get("id") or percorso.stem

    if cid not in tracks:
        e.errore(cid, f"id sconosciuto: non esiste in tracks.json")
        return
    if cid != percorso.stem:
        e.errore(cid, f"il file si chiama {percorso.name} ma dentro l'id e' «{cid}»")

    for campo in CAMPI_PISTA:
        if campo not in dati:
            e.errore(cid, f"manca la sezione `{campo}`")

    # --- curve: quante, numerate come, senza buchi
    curve = dati.get("curve") or []
    attese = tracks[cid].get("corners")
    if attese and len(curve) != attese:
        e.errore(cid, f"{len(curve)} curve descritte ma il catalogo ne dichiara {attese}")
    numeri = [c.get("n") for c in curve]
    if numeri != list(range(1, len(curve) + 1)):
        e.errore(cid, f"numerazione non contigua da 1: {numeri}")
    for curva in curve:
        controlla_curva(cid, curva, e)

    # --- settori
    settori = dati.get("settori") or []
    if len(settori) != 3:
        e.controlla(cid, f"{len(settori)} settori invece di 3")

    # --- impronta del catalogo
    vc = dati.get("verifica_catalogo") or {}
    if vc.get("lunghezza_confermata") is False:
        e.controlla(cid, f"lunghezza NON confermata dalle fonti: {vc.get('note')}")
    if vc.get("curve_confermate") is False:
        e.controlla(cid, f"numero di curve NON confermato: {vc.get('note')}")
    if not vc.get("fonte_lunghezza"):
        e.controlla(cid, "la lunghezza non ha un link di fonte")

    # --- numeri che finiscono nei calcoli
    for campo in ("gt3_ref_lap_time", "gt3_fuel_per_lap_l"):
        blocco = dati.get(campo) or {}
        if blocco.get("valore") is None:
            continue
        if blocco.get("origine") == "mestiere":
            if not blocco.get("confidence"):
                e.errore(cid, f"{campo}: stima senza `confidence`")
            if not blocco.get("nota"):
                e.errore(cid, f"{campo}: stima senza `nota` che dica che e' una stima")
    fuel = dati.get("gt3_fuel_per_lap_l") or {}
    if fuel.get("valore") is not None and fuel.get("origine") == "mestiere":
        stato = tracks[cid].get("fuel_status")
        if stato != "da_misurare":
            e.errore(cid, f"consumo stimato a mestiere ma tracks.json ha "
                          f"fuel_status=«{stato}»: deve restare `da_misurare` finche' "
                          f"non e' un numero misurato dai CSV")

    # --- pit e fonti
    pit = dati.get("pit") or {}
    if pit.get("lato_box") and not pit.get("fonte"):
        e.controlla(cid, f"pit.lato_box=«{pit['lato_box']}» senza fonte: "
                         f"da confermare sulla mappa che sceglieremo")
    fonti = dati.get("fonti") or []
    if not fonti:
        e.errore(cid, "nessuna fonte elencata")
    for u in fonti:
        if not str(u).startswith("http"):
            e.errore(cid, f"fonte non e' un link: {u}")

    for i, chicca in enumerate(dati.get("chicche") or [], 1):
        if not chicca.get("fonte"):
            e.controlla(cid, f"chicca {i} senza fonte")


def main() -> None:
    ap = argparse.ArgumentParser(description="Controlla le guide dei tracciati")
    ap.add_argument("--solo", help="controlla un solo circuito (id)")
    ap.add_argument("--severita", choices=["tutto", "errori"], default="tutto")
    args = ap.parse_args()

    tracks = {t["id"]: t for t in
              json.loads((_DATA_DIR / "tracks.json").read_text(encoding="utf-8"))}

    file = sorted(KNOW_DIR.glob("*.json"))
    if args.solo:
        file = [f for f in file if f.stem == args.solo]
        if not file:
            sys.exit(f"nessuna guida per «{args.solo}» in {KNOW_DIR}")

    e = Esito()
    for f in file:
        controlla_pista(f, tracks, e)

    presenti = {f.stem for f in KNOW_DIR.glob("*.json")}
    mancanti = [t for t in tracks if t not in presenti]

    print(f"Guide controllate: {len(file)} — {', '.join(f.stem for f in file)}\n")

    if e.errori:
        print(f"ERRORI ({len(e.errori)}) — vanno corretti nel file:")
        for r in e.errori:
            print(f"  · {r}")
        print()
    else:
        print("ERRORI: nessuno\n")

    if args.severita == "tutto" and e.controlli:
        print(f"DA CONTROLLARE A OCCHIO ({len(e.controlli)}) — la macchina non puo' decidere:")
        for r in e.controlli:
            print(f"  · {r}")
        print()

    if not args.solo:
        print(f"Guide ancora da consegnare: {len(mancanti)}/{len(tracks)}")
        print("  " + ", ".join(sorted(mancanti)))

    sys.exit(1 if e.errori else 0)


if __name__ == "__main__":
    main()
