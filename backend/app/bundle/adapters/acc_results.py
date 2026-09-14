"""bundle/adapters/acc_results.py — dai risultati di ACC al bundle (L1 · Fase 3).

Legge i file che ACC scrive a fine sessione in
`Documents/Assetto Corsa Competizione/Results/` e ne ricava un bundle con i giri.
Sono l'unica fonte a costo zero: il pilota non deve fare niente, il file c'è già.

**Due formati, non uno.** Verificati su file reali il 14/09/2026:

| | file del **gioco** | file del **server dedicato** |
|---|---|---|
| riconoscibile da | `sessionDef` | `trackName` |
| tipo sessione | numero (10 = gara) | stringa ("R") |
| tempo sul giro | `lapTime` | `laptime` |
| pilota del giro | `driverId` | `driverIndex` |
| validità | assente (solo `flags`) | `isValidForBest` |
| carburante | `fuel` | assente |
| circuito | **assente** | `trackName` |

Entrambi sono **UTF-16 LE senza BOM** (se ne occupa `lettura.py`).

**Quale macchina è la tua.** Il file contiene tutti i partecipanti (nel file reale
esaminato: 16). L'adattatore non tira a indovinare: se le vetture sono più d'una
bisogna dire quale (`car_id`) o chi sei (`player_id`); `elenca_partecipanti()`
serve proprio a far scegliere. Con una vettura sola la prende senza chiedere.

**Il carburante non è (sempre) il residuo.** Nel file reale esaminato `fuel` è
**costante su tutti i giri** di ogni vettura e diverso da vettura a vettura: ha
l'aria di essere il carburante di partenza, non quello rimasto a fine giro. Perciò
il consumo si calcola **solo se il valore effettivamente cala**, e quando non cala
il bundle lo dichiara in `assunzioni` invece di scrivere zero. Il consumo vero, giro
per giro, arriverà dal registratore della shared memory (L3).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.bundle.adapters.lettura import FileAccIllegibile, carica_json
from app.bundle.schema import (
    Condizioni,
    Fonte,
    Giro,
    Meta,
    SessionBundle,
    TipoSessione,
)

# Enum del Broadcasting SDK di ACC, riscontrato sul file reale `race.json` (10 = gara).
# I valori non previsti restano SCONOSCIUTO: meglio un «?» che un'etichetta sbagliata.
TIPI_NUMERICI: dict[int, TipoSessione] = {
    0: TipoSessione.PROVE,
    4: TipoSessione.QUALIFICA,
    9: TipoSessione.QUALIFICA,   # superpole
    10: TipoSessione.GARA,
    11: TipoSessione.HOTLAP,
    12: TipoSessione.HOTSTINT,
}

TIPI_TESTO: dict[str, TipoSessione] = {
    "FP": TipoSessione.PROVE,
    "P": TipoSessione.PROVE,
    "Q": TipoSessione.QUALIFICA,
    "R": TipoSessione.GARA,
    "HL": TipoSessione.HOTLAP,
    "HS": TipoSessione.HOTSTINT,
}

NOTA_CARBURANTE = (
    "carburante: nel file il valore non cala mai fra un giro e l'altro (sembra il "
    "carburante di partenza, non il residuo) → consumo per giro non calcolabile da "
    "qui; servirà il registratore della shared memory"
)
NOTA_CIRCUITO = (
    "circuito: il file del gioco non lo contiene → va indicato dal pilota o letto "
    "dalla shared memory"
)
NOTA_VALIDITA = (
    "validità dei giri: il file del gioco non la dichiara (c'è solo `flags`, campo "
    "di bit non documentato) → tutti i giri risultano validi finché non si legge "
    "quel campo con certezza"
)
NOTA_VETTURA = (
    "vettura: il file la indica con un id numerico (`carModel`) → lo slug del "
    "catalogo arriverà con la tabella di corrispondenza"
)


class ResultsAccError(ValueError):
    """Il file non è un risultato di ACC utilizzabile."""


@dataclass(frozen=True)
class Partecipante:
    """Una vettura presente nel file: serve a far scegliere «qual è la tua»."""

    car_id: int
    numero: int | None
    car_model: int | None
    pilota: str | None
    player_id: str | None
    giri: int


def _e_del_gioco(dati: dict[str, Any]) -> bool:
    return "sessionDef" in dati


def _righe_classifica(dati: dict[str, Any]) -> list[dict[str, Any]]:
    for contenitore in ("snapShot", "sessionResult"):
        nodo = dati.get(contenitore)
        if isinstance(nodo, dict):
            righe = nodo.get("leaderBoardLines")
            if isinstance(righe, list):
                return [r for r in righe if isinstance(r, dict)]
    return []


def _nome(driver: dict[str, Any]) -> str | None:
    pezzi = [str(driver.get(k, "")).strip() for k in ("firstName", "lastName")]
    nome = " ".join(p for p in pezzi if p)
    return nome or None


def _giri_grezzi(dati: dict[str, Any]) -> list[dict[str, Any]]:
    giri = dati.get("laps")
    if not isinstance(giri, list):
        raise ResultsAccError("il file non contiene l'elenco dei giri (`laps`)")
    return [g for g in giri if isinstance(g, dict) and "carId" in g]


def elenca_partecipanti(sorgente: str | Path | bytes) -> list[Partecipante]:
    """Le vetture presenti nel file, con quanti giri ha fatto ciascuna."""
    try:
        dati, _ = carica_json(sorgente)
    except FileAccIllegibile as e:
        raise ResultsAccError(str(e)) from e
    return _partecipanti(dati)


def _partecipanti(dati: dict[str, Any]) -> list[Partecipante]:
    giri = _giri_grezzi(dati)
    conteggio: dict[int, int] = {}
    for g in giri:
        conteggio[int(g["carId"])] = conteggio.get(int(g["carId"]), 0) + 1

    anagrafica: dict[int, dict[str, Any]] = {}
    for riga in _righe_classifica(dati):
        auto = riga.get("car")
        if isinstance(auto, dict) and "carId" in auto:
            anagrafica[int(auto["carId"])] = riga

    fuori: list[Partecipante] = []
    for car_id in sorted(conteggio):
        riga = anagrafica.get(car_id, {})
        auto = riga.get("car", {}) if isinstance(riga.get("car"), dict) else {}
        piloti = auto.get("drivers") if isinstance(auto.get("drivers"), list) else []
        primo = riga.get("currentDriver") if isinstance(riga.get("currentDriver"), dict) else None
        if primo is None and piloti and isinstance(piloti[0], dict):
            primo = piloti[0]
        fuori.append(Partecipante(
            car_id=car_id,
            numero=auto.get("raceNumber"),
            car_model=auto.get("carModel"),
            pilota=_nome(primo) if primo else None,
            player_id=str(primo.get("playerId")) if primo and primo.get("playerId") else None,
            giri=conteggio[car_id],
        ))
    return fuori


def _scegli_vettura(partecipanti: list[Partecipante], car_id: int | None,
                    player_id: str | None) -> Partecipante:
    if not partecipanti:
        raise ResultsAccError("nessuna vettura ha completato giri in questo file")

    if car_id is not None:
        for p in partecipanti:
            if p.car_id == car_id:
                return p
        raise ResultsAccError(
            f"carId {car_id} non presente: ci sono "
            + ", ".join(str(p.car_id) for p in partecipanti)
        )

    if player_id is not None:
        for p in partecipanti:
            if p.player_id == str(player_id):
                return p
        raise ResultsAccError(f"nessuna vettura del pilota {player_id} in questo file")

    if len(partecipanti) == 1:
        return partecipanti[0]

    elenco = ", ".join(
        f"{p.car_id} ({p.pilota or 'senza nome'}, {p.giri} giri)" for p in partecipanti[:8]
    )
    raise ResultsAccError(
        f"il file contiene {len(partecipanti)} vetture: indica quale con car_id "
        f"o chi sei con player_id. Presenti: {elenco}"
        + (" …" if len(partecipanti) > 8 else "")
    )


def _condizioni(dati: dict[str, Any], del_gioco: bool) -> Condizioni:
    c = Condizioni()
    stato = None
    if del_gioco:
        definizione = dati.get("sessionDef")
        if isinstance(definizione, dict):
            stato = definizione.get("trackStatus")
    if isinstance(stato, dict):
        def num(chiave: str) -> float | None:
            v = stato.get(chiave)
            return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

        c = Condizioni(
            grip_linea_ideale=num("idealLineGrip"),
            grip_fuori_linea=num("outsideLineGrip"),
            pioggia=num("wetLevel"),
        )
    bagnata = None
    for contenitore in ("snapShot", "sessionResult"):
        nodo = dati.get(contenitore)
        if isinstance(nodo, dict) and "isWetSession" in nodo:
            bagnata = bool(nodo["isWetSession"])
            break
    if bagnata is not None:
        c = c.model_copy(update={"pista_bagnata": bagnata})
    return c


def _tipo_sessione(dati: dict[str, Any], del_gioco: bool) -> TipoSessione:
    if del_gioco:
        definizione = dati.get("sessionDef")
        grezzo = definizione.get("sessionType") if isinstance(definizione, dict) else None
        if isinstance(grezzo, int) and not isinstance(grezzo, bool):
            return TIPI_NUMERICI.get(grezzo, TipoSessione.SCONOSCIUTO)
        return TipoSessione.SCONOSCIUTO
    grezzo = dati.get("sessionType")
    if isinstance(grezzo, str):
        # I server numerano le sessioni ripetute: "Q2", "FP1", "R2" → conta la lettera.
        etichetta = grezzo.strip().upper().rstrip("0123456789") or grezzo.strip().upper()
        return TIPI_TESTO.get(etichetta, TipoSessione.SCONOSCIUTO)
    if isinstance(grezzo, int) and not isinstance(grezzo, bool):
        return TIPI_NUMERICI.get(grezzo, TipoSessione.SCONOSCIUTO)
    return TipoSessione.SCONOSCIUTO


def leggi_results_acc(
    sorgente: str | Path | bytes,
    *,
    car_id: int | None = None,
    player_id: str | None = None,
    track: str | None = None,
) -> SessionBundle:
    """Legge un file di risultati di ACC e ne ricava il bundle di **una** vettura.

    Args:
        sorgente: percorso del file o i suoi byte.
        car_id: quale vettura leggere, quando il file ne contiene più d'una.
        player_id: in alternativa, l'id del pilota da cercare fra i partecipanti.
        track: circuito da attribuire alla sessione (il file del gioco non lo contiene).

    Raises:
        ResultsAccError: file illeggibile, senza giri, o vettura ambigua/assente.
    """
    try:
        dati, nome_file = carica_json(sorgente)
    except FileAccIllegibile as e:
        raise ResultsAccError(str(e)) from e

    del_gioco = _e_del_gioco(dati)
    if not del_gioco and "trackName" not in dati and "sessionResult" not in dati:
        raise ResultsAccError(
            "non sembra un file di risultati di ACC: mancano sia `sessionDef` "
            "che `trackName`/`sessionResult`"
        )

    partecipanti = _partecipanti(dati)
    mia = _scegli_vettura(partecipanti, car_id, player_id)

    campo_tempo = "lapTime" if del_gioco else "laptime"
    grezzi = [g for g in _giri_grezzi(dati) if int(g["carId"]) == mia.car_id]
    if any(g.get("timestampMS") is not None for g in grezzi):
        grezzi.sort(key=lambda g: g.get("timestampMS") or 0)

    assunzioni: list[str] = []
    giri: list[Giro] = []
    residuo_precedente: float | None = None
    carburante_mai_sceso = True
    ha_carburante = False

    for indice, g in enumerate(grezzi, start=1):
        tempo = g.get(campo_tempo)
        tempo_ms = int(tempo) if isinstance(tempo, (int, float)) and tempo > 0 else None

        splits = [int(s) for s in g.get("splits", [])
                  if isinstance(s, (int, float)) and s > 0][:3]

        residuo = g.get("fuel")
        residuo = float(residuo) if isinstance(residuo, (int, float)) and residuo >= 0 else None
        usato = None
        if residuo is not None:
            ha_carburante = True
            if residuo_precedente is not None and residuo_precedente > residuo:
                usato = round(residuo_precedente - residuo, 3)
                carburante_mai_sceso = False
            residuo_precedente = residuo

        valido = True
        if not del_gioco and "isValidForBest" in g:
            valido = bool(g["isValidForBest"])

        flags = g.get("flags")
        giri.append(Giro(
            numero=indice,
            tempo_ms=tempo_ms,
            splits_ms=splits,
            valido=valido,
            carburante_residuo_l=residuo,
            carburante_usato_l=usato,
            timestamp_ms=g.get("timestampMS"),
            flags_acc=int(flags) if isinstance(flags, int) and flags >= 0 else None,
        ))

    if not giri:
        raise ResultsAccError(f"la vettura {mia.car_id} non ha giri nel file")

    if ha_carburante and carburante_mai_sceso:
        assunzioni.append(NOTA_CARBURANTE)
    if del_gioco:
        assunzioni.append(NOTA_VALIDITA)
    if mia.car_model is not None:
        assunzioni.append(NOTA_VETTURA)

    pista = track or dati.get("trackName")
    if isinstance(pista, str):
        pista = pista.strip().lower() or None
    else:
        pista = None
    if pista is None:
        assunzioni.append(NOTA_CIRCUITO)

    durata = None
    definizione = dati.get("sessionDef")
    if isinstance(definizione, dict) and isinstance(definizione.get("sessionDuration"), (int, float)):
        durata = float(definizione["sessionDuration"])

    meta = Meta(
        fonte=Fonte.ACC_RESULTS,
        file_origine=nome_file,
        car_model_id=mia.car_model if isinstance(mia.car_model, int) else None,
        track=pista,
        pilota=mia.pilota,
        tipo_sessione=_tipo_sessione(dati, del_gioco),
        durata_s=durata,
        condizioni=_condizioni(dati, del_gioco),
    )
    return SessionBundle(meta=meta, giri=giri, assunzioni=assunzioni)
