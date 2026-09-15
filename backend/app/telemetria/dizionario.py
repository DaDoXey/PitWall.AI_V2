"""Il dizionario dei canali: che cosa registriamo, e che cosa significa.

Richiesta di Edoardo (15/09): «tutti i parametri possibili e registrabili da ACC,
come già fa MoTeC, con una raccolta dati ordinata, schematizzata e chiara sotto ogni
punto di vista». Questo modulo è la parte «chiara»: ogni colonna registrata ha un
nome canonico stabile, un'unità con la sua provenienza, e la descrizione **ufficiale
di Kunos** (estratta dal documento, non scritta da noi).

Come si costruisce l'elenco:

* si parte dalle strutture di `strutture.py` — pagina fisica e pagina grafica;
* si scartano i campi che il documento marca «non usati da ACC»: sono zeri, e uno
  zero in un'analisi vale meno di un dato mancante dichiarato;
* si scartano le stringhe (i tempi in testo: esistono già in millisecondi) e le due
  tabelle delle **altre** vetture in pista (`carCoordinates`, `carID`): sono 240
  colonne che non parlano della macchina del pilota;
* gli array si aprono in colonne singole: `wheelPressure` → `physics.wheelPressure.FL`
  … `.RR`; i vettori → `.x .y .z`; i danni → per lato.

La pagina statica non genera canali: non cambia mai, e finisce nei metadati della
sessione.
"""

from __future__ import annotations

import ctypes
import json
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path

from app.telemetria.strutture import (
    CAMPI_NON_USATI,
    PAGINE,
    VERSIONE_STRUTTURA,
)

_DESCRIZIONI = (
    Path(__file__).resolve().parents[1] / "core" / "data" / "acc_campi_shared_memory.json"
)

RUOTE = ("FL", "FR", "RL", "RR")
ASSI = ("x", "y", "z")
LATI_DANNO = ("anteriore", "posteriore", "sinistra", "destra", "centro")

# Campi esclusi dai canali con la loro ragione: sta scritta qui, così nessuno deve
# indovinare perché una colonna non c'è.
ESCLUSI: dict[str, str] = {
    "carCoordinates": "posizione delle ALTRE vetture in pista (60x3): non è telemetria del pilota",
    "carID": "identificativi delle altre vetture (60): non è telemetria del pilota",
}

# Unità, con la provenienza. «documento» = c'è scritto nel PDF ufficiale;
# «uso comune» = non è dichiarata, ma è nota e verificabile a schermo in gioco;
# tutto il resto resta «non dichiarata», che è una risposta onesta.
_UNITA: dict[str, tuple[str, str]] = {
    # pedali e comandi
    "gas": ("0-1", "documento"), "brake": ("0-1", "documento"),
    "clutch": ("0-1", "documento"), "steerAngle": ("-1..1", "documento"),
    "gear": ("marcia", "documento"), "rpm": ("giri/min", "documento"),
    "currentMaxRpm": ("giri/min", "documento"),
    # moto della vettura
    "speedKmh": ("km/h", "documento"), "velocity": ("m/s", "uso comune"),
    "localVelocity": ("m/s", "uso comune"), "accG": ("g", "uso comune"),
    "localAngularVel": ("rad/s", "uso comune"),
    "heading": ("rad", "uso comune"), "pitch": ("rad", "uso comune"),
    "roll": ("rad", "uso comune"),
    # gomme
    "wheelSlip": ("adimensionale", "documento"),
    "wheelPressure": ("psi", "uso comune"),
    "wheelAngularSpeed": ("rad/s", "documento"),
    "tyreCoreTemp": ("°C", "uso comune"), "tyreTemp": ("°C", "uso comune"),
    "slipRatio": ("rad", "documento"), "slipAngle": ("rad", "documento"),
    "suspensionTravel": ("m", "uso comune"),
    # freni
    "brakeTemp": ("°C", "uso comune"), "brakePressure": ("0-1", "uso comune"),
    "brakeBias": ("0-1 grezzo", "uso comune"),
    "padLife": ("mm", "uso comune"), "discLife": ("mm", "uso comune"),
    # motore, fluidi, ambiente
    "fuel": ("kg", "documento"), "waterTemp": ("°C", "uso comune"),
    "turboBoost": ("bar", "uso comune"), "airTemp": ("°C", "documento"),
    "roadTemp": ("°C", "documento"),
    "exhaustTemperature": ("°C", "uso comune"),
    "windSpeed": ("m/s", "documento"), "windDirection": ("rad", "documento"),
    # giro e sessione
    "normalizedCarPosition": ("0-1", "documento"),
    "distanceTraveled": ("m", "documento"),
    "iCurrentTime": ("ms", "documento"), "iLastTime": ("ms", "documento"),
    "iBestTime": ("ms", "documento"), "lastSectorTime": ("ms", "documento"),
    "iDeltaLapTime": ("ms", "documento"), "iEstimatedLapTime": ("ms", "documento"),
    "iSplit": ("ms", "documento"), "sessionTimeLeft": ("ms", "documento"),
    "driverStintTotalTimeLeft": ("ms", "documento"),
    "driverStintTimeLeft": ("ms", "documento"),
    "gapAhead": ("ms", "documento"), "gapBehind": ("ms", "documento"),
    "penaltyTime": ("s", "uso comune"), "Clock": ("s", "documento"),
    # carburante
    "fuelXLap": ("l", "documento"), "usedFuel": ("l", "documento"),
    "fuelEstimatedLaps": ("giri", "documento"), "mfdFuelToAdd": ("l", "documento"),
    "mfdTyrePressureLF": ("psi", "uso comune"),
    "mfdTyrePressureRF": ("psi", "uso comune"),
    "mfdTyrePressureLR": ("psi", "uso comune"),
    "mfdTyrePressureRR": ("psi", "uso comune"),
    # forza di ritorno
    "finalFF": ("-1..1", "uso comune"),
}

# Avvertenze che viaggiano insieme al dizionario: sono differenze note fra ciò che
# il documento dichiara e ciò che si vede in gioco.
AVVERTENZE = (
    "Il documento dichiara `fuel` in kg, mentre il gioco mostra il carburante in "
    "litri: da verificare a schermo prima di usarlo in un consumo.",
    "`brakeBias` e `brakePressure` sono grezzi: la conversione in valori da cruscotto "
    "richiede le tabelle per vettura (appendici 3 e 4) e non è ancora verificata.",
    "`steerAngle` è normalizzato -1..1: diventa gradi solo con l'angolo massimo della "
    "vettura (appendice 5), anch'esso da verificare.",
    "Le stringhe (tempi in testo, mescola, stato pista) non sono canali: i tempi "
    "esistono già in millisecondi, il resto finisce nei metadati della sessione.",
)


@dataclass(frozen=True)
class Canale:
    """Una colonna registrata."""

    nome: str                   # nome canonico: "physics.wheelPressure.FL"
    pagina: str                 # physics | graphics | pitwall
    campo: str                  # nome del campo ACC
    componente: str | None      # FL/FR/RL/RR, x/y/z, lato del danno…
    tipo: str                   # "f4" (float32) o "i4" (int32)
    unita: str
    unita_fonte: str            # documento | uso comune | non dichiarata | PitWall
    descrizione: str            # ufficiale Kunos, o nostra per i canali sintetici
    fonte: str = "ACC"          # ACC | PitWall


# Canali che ACC non scrive e che aggiungiamo noi. Uno solo, e per un motivo preciso:
# la shared memory non porta un orologio della registrazione. `iCurrentTime` azzera a
# ogni giro e `Clock` è l'ora del mondo di gioco; per sapere quanto tempo è passato fra
# due campioni — cioè per qualunque conto sul tempo — serve il nostro.
CANALI_SINTETICI: tuple[Canale, ...] = (
    Canale(
        nome="pitwall.tempo_ms", pagina="pitwall", campo="tempo_ms", componente=None,
        tipo="i4", unita="ms", unita_fonte="PitWall",
        descrizione=("Millisecondi trascorsi dall'inizio della registrazione, misurati "
                     "dal registratore di PitWall (orologio monotono, non l'ora di "
                     "gioco). Intero: nessun arrotondamento."),
        fonte="PitWall",
    ),
)


def _componenti(campo: str, tipo_ctypes: type) -> list[tuple[str | None, type]]:
    """Apre un campo in componenti: scalare, 4 ruote, vettore, danni, matrice 4x3."""
    if not hasattr(tipo_ctypes, "_length_"):
        return [(None, tipo_ctypes)]

    lunghezza = tipo_ctypes._length_
    interno = tipo_ctypes._type_

    if hasattr(interno, "_length_"):  # matrice, es. tyreContactPoint[4][3]
        fuori: list[tuple[str | None, type]] = []
        for i in range(lunghezza):
            etichetta_esterna = RUOTE[i] if lunghezza == 4 else str(i)
            for j in range(interno._length_):
                etichetta_interna = ASSI[j] if interno._length_ == 3 else str(j)
                fuori.append((f"{etichetta_esterna}.{etichetta_interna}", interno._type_))
        return fuori

    if lunghezza == 4:
        etichette = list(RUOTE)
    elif lunghezza == 3:
        etichette = list(ASSI)
    elif lunghezza == 5 and campo == "carDamage":
        etichette = list(LATI_DANNO)
    else:
        etichette = [str(i) for i in range(lunghezza)]
    return [(e, interno) for e in etichette]


def _tipo_numpy(tipo_ctypes: type) -> str | None:
    if tipo_ctypes is ctypes.c_float:
        return "f4"
    if tipo_ctypes is ctypes.c_int32:
        return "i4"
    return None  # stringhe e resto: non sono canali


@lru_cache(maxsize=1)
def _descrizioni_ufficiali() -> dict[str, dict[str, dict]]:
    if not _DESCRIZIONI.exists():
        return {}
    dati = json.loads(_DESCRIZIONI.read_text(encoding="utf-8"))
    return {p: v["campi"] for p, v in dati["pagine"].items()}


@lru_cache(maxsize=1)
def canali() -> tuple[Canale, ...]:
    """L'elenco completo delle colonne registrate, nell'ordine di scrittura."""
    descrizioni = _descrizioni_ufficiali()
    fuori: list[Canale] = list(CANALI_SINTETICI)
    for pagina in ("physics", "graphics"):
        struttura = PAGINE[pagina][1]
        non_usati = CAMPI_NON_USATI.get(pagina, frozenset())
        descr_pagina = descrizioni.get(pagina, {})
        for campo, tipo_ctypes in struttura._fields_:
            if campo in non_usati or campo in ESCLUSI:
                continue
            unita, fonte = _UNITA.get(campo, ("non dichiarata", "non dichiarata"))
            descrizione = (descr_pagina.get(campo) or {}).get("descrizione", "")
            for componente, tipo_base in _componenti(campo, tipo_ctypes):
                tipo = _tipo_numpy(tipo_base)
                if tipo is None:
                    continue
                nome = f"{pagina}.{campo}"
                if componente:
                    nome += f".{componente}"
                fuori.append(Canale(
                    nome=nome, pagina=pagina, campo=campo, componente=componente,
                    tipo=tipo, unita=unita, unita_fonte=fonte,
                    descrizione=descrizione,
                ))
    return tuple(fuori)


def nomi() -> tuple[str, ...]:
    return tuple(c.nome for c in canali())


def come_json(frequenza_hz: float) -> dict:
    """Il dizionario da scrivere accanto ai canali di ogni sessione."""
    return {
        "versione_struttura": VERSIONE_STRUTTURA,
        "fonte": "ACC Shared Memory Documentation v1.8.12 — Kunos Simulazioni",
        "frequenza_hz": frequenza_hz,
        "colonne": len(canali()),
        "avvertenze": list(AVVERTENZE),
        "esclusi": dict(ESCLUSI),
        "canali": [asdict(c) for c in canali()],
    }
