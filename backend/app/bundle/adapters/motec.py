"""Da un file MoTeC di ACC al «session bundle» (L5 · Fase 2).

Un `.ld` diventa una sessione come le altre: stessi canali canonici della shared
memory dove il significato coincide, stessa cartella della telemetria, stessa analisi.
Tutto ciò che il file non contiene e che si è dovuto ricavare o supporre finisce nelle
`assunzioni` del bundle, con il motivo.

Le decisioni del 17/09, una per una:

1. **La posizione in pista si ricava dalla velocità.** ACC non esporta né coordinate
   né posizione (verificato su 22 file di due fonti): la distanza si integra da `SPEED`
   e si **azzera a ogni passaggio sul traguardo**, così l'errore non si accumula da un
   giro all'altro. Sui file veri la distanza integrata sta entro circa il 2% della
   lunghezza ufficiale. I giri con testacoda, tagli o corsia box la sporcano: per
   questo la validità del giro — che MoTeC non porta — non si presume mai buona in
   silenzio.
2. **`TYRE_TAIR` non è la temperatura al core.** Resta un canale MoTeC con il suo nome,
   fuori dal giudizio contro la finestra Kunos (che è riferita al core).
3. **Il consumo compare sempre, con la sua fonte**: prima quello inserito dal pilota
   (litri a inizio e fine), poi il `fuelPerLap` salvato da ACC nel setup. MoTeC il
   carburante non lo esporta: nessun canale lo contiene.
4. **I file salvati da MoTeC i2 dopo un ritaglio** (niente beacon, canali di durate
   diverse) valgono **un giro**, se la distanza del ritaglio è quella della pista.

I canali il cui significato coincide con la shared memory prendono il nome canonico
(`physics.speedKmh`, `physics.wheelPressure.FL`…) con la conversione d'unità; gli altri
restano `motec.<NOME>` nelle loro unità, senza fingere un'equivalenza non verificata
(lo sterzo MoTeC è in gradi, quello della shared memory è normalizzato -1..1).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.analisi.curve import POSIZIONE, TEMPO, dividi_in_giri
from app.bundle.schema import (
    Canali,
    Fonte,
    FonteCarburante,
    Giro,
    Mescola,
    Meta,
    Piattaforma,
    SessionBundle,
    Setup,
)
from app.motec import RegistrazioneMotec

FREQUENZA_HZ = 100.0          # la stessa griglia del registratore della shared memory
# Distanza del ritaglio i2 vs lunghezza ufficiale della pista. La distanza integrata è
# sistematicamente corta (traiettoria vs mezzeria: mediana −0,9%, fino a −2,5% a Paul
# Ricard sui file veri del 17/09): 4% lascia margine a quell'effetto e scarta i mezzi giri.
TOLLERANZA_LUNGHEZZA = 0.04
# Un tratto senza traguardo di chiusura non è mai un giro completo: la sua posizione
# ricavata si ferma sotto la soglia di completezza di `dividi_in_giri` (0,95).
POSIZIONE_MASSIMA_PARZIALE = 0.94
POSIZIONE_MINIMA_PARZIALE = 0.06

_RUOTE = {"LF": "FL", "RF": "FR", "LR": "RL", "RR": "RR"}

# nome MoTeC → (nome canonico, fattore). Solo dove il significato è lo stesso.
_CANONICI: dict[str, tuple[str, float]] = {
    "SPEED": ("physics.speedKmh", 3.6),        # m/s → km/h
    "THROTTLE": ("physics.gas", 0.01),         # % → 0-1
    "BRAKE": ("physics.brake", 0.01),          # % → 0-1
    "RPMS": ("physics.rpms", 1.0),
}
for _m, _c in _RUOTE.items():
    _CANONICI[f"TYRE_PRESS_{_m}"] = (f"physics.wheelPressure.{_c}", 1.0)          # psi
    _CANONICI[f"BRAKE_TEMP_{_m}"] = (f"physics.brakeTemp.{_c}", 1.0)              # °C
    _CANONICI[f"SUS_TRAVEL_{_m}"] = (f"physics.suspensionTravel.{_c}", 0.001)     # mm → m

# Non si portano: sempre vuoti nei file di ACC, o non allineati al tempo.
_SCARTATI = {
    "LAP_BEACON": "sempre zero nei file di ACC: i giri vengono dal .ldx",
    "CLUTCH": "sempre zero nei file di ACC",
    "TIME": "non è un cronometro del giro (si azzera a metà giro in alcuni file)",
}
# Canali a gradini: si ricampionano tenendo il valore, mai interpolando (una marcia 3,4
# o un ABS «mezzo attivo» non esistono).
_A_GRADINI_PREFISSI = ("GEAR", "TC", "ABS", "BUMPSTOPUP_RIDE", "BUMPSTOPDN_RIDE")


class MotecNonConvertibile(ValueError):
    """Il file non permette di costruire una sessione onesta."""


@dataclass
class CarburanteManuale:
    """Litri nel serbatoio all'inizio e alla fine della registrazione, dal pilota."""

    inizio_l: float
    fine_l: float


def _nome_canale(nome: str) -> str:
    if nome in _CANONICI:
        return _CANONICI[nome][0]
    return f"motec.{nome}"


def _ricampiona(valori: np.ndarray, frequenza: int, t: np.ndarray, a_gradini: bool) -> np.ndarray:
    t_orig = np.arange(valori.size, dtype=np.float64) / frequenza
    if a_gradini:
        indici = np.clip(np.floor(t * frequenza).astype(np.int64), 0, valori.size - 1)
        return valori[indici]
    return np.interp(t, t_orig, valori)


def _lunghezza_ufficiale_m(pista: str | None) -> float | None:
    from app.core import catalog

    voce = catalog.resolve_track(pista) if pista else None
    km = voce.get("length_km") if voce else None
    return float(km) * 1000.0 if km else None


def _posizione(distanza: np.ndarray, confini: list[int], lunghezza_rif: float) -> np.ndarray:
    """Posizione normalizzata 0-1 dalla distanza, azzerata a ogni traguardo.

    `distanza` ha un punto in più dei campioni (la distanza alla fine dell'ultimo), così
    un traguardo può cadere esattamente sulla fine dei dati. `confini` sono gli indici
    dei passaggi sul traguardo. Fra due passaggi la posizione va esattamente da 0 a 1 (la
    distanza di quel giro fa da unità); prima del primo e dopo l'ultimo si usa la
    lunghezza di riferimento, e il tratto resta parziale.
    """
    n = distanza.size - 1
    posizione = np.empty(n, dtype=np.float64)
    if not confini:
        posizione[:] = np.clip(distanza[:n] / lunghezza_rif, 0.0, POSIZIONE_MASSIMA_PARZIALE)
        return posizione
    primo, ultimo = confini[0], confini[-1]
    posizione[:primo] = np.clip(1.0 - (distanza[primo] - distanza[:primo]) / lunghezza_rif,
                                POSIZIONE_MINIMA_PARZIALE, 0.999)
    for a, b in zip(confini, confini[1:]):
        tratto = distanza[a:b] - distanza[a]
        totale = distanza[b] - distanza[a]
        posizione[a:b] = tratto / totale if totale > 0 else 0.0
    posizione[ultimo:] = np.clip((distanza[ultimo:n] - distanza[ultimo]) / lunghezza_rif,
                                 0.0, POSIZIONE_MASSIMA_PARZIALE)
    return posizione


def _slug(registrazione: RegistrazioneMotec) -> tuple[str | None, str | None]:
    from app.core import catalog

    nome = registrazione.nome_file
    vettura = catalog.resolve_car(nome.vettura if nome else None) \
        or catalog.resolve_car(registrazione.ld.vettura or None)
    pista = catalog.resolve_track(nome.pista if nome else None) \
        or catalog.resolve_track(registrazione.ld.pista or None)
    return (vettura["id"] if vettura else None), (pista["id"] if pista else None)


def _fuel_per_lap(setup: Setup | None) -> float | None:
    if setup is None:
        return None
    strategia = (setup.raw.get("basicSetup") or {}).get("strategy") or {}
    valore = strategia.get("fuelPerLap")
    try:
        valore = float(valore)
    except (TypeError, ValueError):
        return None
    return valore if valore > 0 else None


def _mescola_dal_setup(setup: Setup | None) -> Mescola | None:
    if setup is None:
        return None
    gomme = (setup.raw.get("basicSetup") or {}).get("tyres") or {}
    return {0: Mescola.ASCIUTTO, 1: Mescola.BAGNATO}.get(gomme.get("tyreCompound"))


def bundle_da_motec(
    registrazione: RegistrazioneMotec,
    file_canali: str = "canali.npz",
    setup: Setup | None = None,
    carburante: CarburanteManuale | None = None,
    mescola: Mescola | None = None,
    riferimento: bool = True,
    nome_file: str | None = None,
) -> tuple[SessionBundle, dict[str, np.ndarray], dict[str, Any]]:
    """(bundle, canali sulla griglia a 100 Hz, metadati per `sessione.json`)."""
    ld = registrazione.ld
    assunzioni: list[str] = []
    velocita = ld.canale("SPEED")
    if velocita is None or not velocita.leggibile:
        raise MotecNonConvertibile("manca il canale SPEED: senza velocità non c'è posizione")

    vettura, pista = _slug(registrazione)
    durata = registrazione.durata_s
    n = int(np.floor(durata * FREQUENZA_HZ))
    if n < 100:
        raise MotecNonConvertibile(f"registrazione di {durata:.2f} s: troppo corta")
    t = np.arange(n, dtype=np.float64) / FREQUENZA_HZ

    # ── i canali sulla griglia comune ────────────────────────────────────────
    canali: dict[str, np.ndarray] = {}
    esclusi: list[str] = []
    for c in ld.canali:
        if c.nome in _SCARTATI:
            continue
        if not c.leggibile:
            esclusi.append(f"{c.nome} ({c.motivo})")
            continue
        if c.nome in registrazione.canali_lunghi:
            esclusi.append(c.nome)
            continue
        a_gradini = c.nome.startswith(_A_GRADINI_PREFISSI)
        valori = _ricampiona(c.valori(), c.frequenza_hz, t, a_gradini)
        fattore = _CANONICI[c.nome][1] if c.nome in _CANONICI else 1.0
        canali[_nome_canale(c.nome)] = (valori * fattore).astype(
            np.int32 if a_gradini else np.float32)
    if registrazione.canali_lunghi:
        assunzioni.append(
            f"canali più lunghi del giro ritagliato, non allineati al taglio e quindi "
            f"esclusi: {', '.join(registrazione.canali_lunghi)}")
    altri = [e for e in esclusi if e not in registrazione.canali_lunghi]
    if altri:
        assunzioni.append(f"canali non leggibili: {', '.join(altri)}")

    # ── distanza, giri e posizione ───────────────────────────────────────────
    v_ms = _ricampiona(velocita.valori(), velocita.frequenza_hz, t, False)
    # n + 1 punti: la distanza all'inizio di ogni campione, più quella alla fine dei dati
    distanza = np.concatenate(([0.0], np.cumsum(v_ms) / FREQUENZA_HZ))
    lunghezza_ufficiale = _lunghezza_ufficiale_m(pista)

    beacon = registrazione.ldx.beacon_s if registrazione.ldx else []
    # un beacon a 0 (registrazione che parte sul traguardo) è un confine valido
    confini = sorted({i for b in beacon if 0 <= (i := int(round(b * FREQUENZA_HZ))) <= n})
    tempi_beacon_ms = {
        (int(round(a * FREQUENZA_HZ)), int(round(b * FREQUENZA_HZ))): int(round((b - a) * 1000))
        for a, b in zip(beacon, beacon[1:])
    }

    if len(confini) >= 2:
        distanze_giro = [distanza[b] - distanza[a] for a, b in zip(confini, confini[1:])]
        lunghezza_rif = float(np.median(distanze_giro))
        posizione = _posizione(distanza, confini, lunghezza_rif)
    elif registrazione.ritagliata_in_i2:
        # Un giro ritagliato in i2: vale come giro solo se la distanza è quella della pista.
        percorsa = float(distanza[n])
        if lunghezza_ufficiale is None:
            raise MotecNonConvertibile(
                "file ritagliato in MoTeC i2 senza passaggi sul traguardo, e pista non nel "
                "catalogo: impossibile dire se il ritaglio è un giro intero")
        scarto = abs(percorsa - lunghezza_ufficiale) / lunghezza_ufficiale
        if scarto > TOLLERANZA_LUNGHEZZA:
            raise MotecNonConvertibile(
                f"file ritagliato in MoTeC i2: {percorsa:.0f} m percorsi contro {lunghezza_ufficiale:.0f} m "
                f"della pista ({scarto:.1%}): non è un giro intero")
        posizione = np.clip(distanza[:n] / percorsa, 0.0, 0.999)
        posizione[0] = 0.0
        confini = [0, n]
        tempi_beacon_ms[(0, n)] = int(round(durata * 1000))
        lunghezza_rif = percorsa
        assunzioni.append(
            f"file salvato da MoTeC i2 dopo un ritaglio (niente passaggi sul traguardo): il "
            f"ritaglio vale come un giro perché la distanza percorsa ({percorsa:.0f} m) è "
            f"entro il {TOLLERANZA_LUNGHEZZA:.0%} della lunghezza ufficiale "
            f"({lunghezza_ufficiale:.0f} m); tempo del giro = durata del ritaglio, al campione")
    elif len(confini) == 1:
        lunghezza_rif = lunghezza_ufficiale or float(distanza[n])
        posizione = _posizione(distanza, confini, lunghezza_rif)
        assunzioni.append("un solo passaggio sul traguardo: nessun giro completo")
    else:
        raise MotecNonConvertibile(
            "nessun passaggio sul traguardo nel .ldx (o .ldx assente): i giri non si "
            "conoscono, e MoTeC non li porta in nessun canale")

    canali[POSIZIONE] = posizione.astype(np.float32)
    canali[TEMPO] = (t * 1000.0).astype(np.float32)
    assunzioni.append(
        f"posizione in pista ricavata integrando la velocità (ACC non esporta coordinate "
        f"in MoTeC), azzerata a ogni traguardo; giro di riferimento {lunghezza_rif:.0f} m"
        + (f", ufficiale {lunghezza_ufficiale:.0f} m" if lunghezza_ufficiale else ""))

    # ── i giri del bundle ────────────────────────────────────────────────────
    ritagliati = dividi_in_giri(canali)
    giri: list[Giro] = []
    for g in ritagliati:
        tempo_ms = None
        if g.completo:
            tempo_ms = tempi_beacon_ms.get((g.inizio, g.fine), g.tempo_ms)
        giri.append(Giro(numero=g.numero, tempo_ms=tempo_ms, valido=g.completo,
                         timestamp_ms=float(canali[TEMPO][g.inizio])))
    completi = [g for g, r in zip(giri, ritagliati) if r.completo]
    if not completi:
        raise MotecNonConvertibile("nessun giro completo nella registrazione")
    assunzioni.append(
        "validità del giro, corsia box e settori non sono nei file MoTeC di ACC: i giri "
        "completi sono considerati validi, e un giro con taglio o testacoda va scartato a occhio")

    # ── carburante: manuale, poi setup ───────────────────────────────────────
    fonte_carburante = None
    if carburante is not None:
        consumato = carburante.inizio_l - carburante.fine_l
        if consumato <= 0:
            raise MotecNonConvertibile(
                f"carburante: {carburante.inizio_l} l all'inizio e {carburante.fine_l} l alla "
                f"fine non fanno un consumo")
        totale_m = float(distanza[n])
        residuo = carburante.inizio_l
        for giro, r in zip(giri, ritagliati):
            quota = float(distanza[r.fine] - distanza[r.inizio]) / totale_m
            usato = consumato * quota
            residuo -= usato
            if r.completo:
                giro.carburante_usato_l = round(usato, 3)
            giro.carburante_residuo_l = round(max(residuo, 0.0), 3)
        fonte_carburante = FonteCarburante.MANUALE
        assunzioni.append(
            f"consumo inserito dal pilota ({consumato:.2f} l in tutta la registrazione), "
            f"ripartito sui giri in proporzione alla distanza: è una media, non giro per giro")
    elif (per_giro := _fuel_per_lap(setup)) is not None:
        for giro in completi:
            giro.carburante_usato_l = round(per_giro, 3)
        fonte_carburante = FonteCarburante.SETUP
        assunzioni.append(
            f"consumo dal setup: {per_giro:.2f} l/giro, il valore che ACC salva nella strategia "
            f"(non misurato su questa registrazione)")
    else:
        assunzioni.append(
            "consumo non calcolabile: MoTeC non esporta il carburante; inserisci i litri a "
            "inizio e fine, o importa il setup usato")

    # ── mescola e temperature ────────────────────────────────────────────────
    # Senza mescola lo dice già l'analisi delle gomme: qui non si ripete.
    mescola = mescola or _mescola_dal_setup(setup)
    if any(k.startswith("motec.TYRE_TAIR_") for k in canali):
        assunzioni.append(
            "temperature gomme: MoTeC esporta `TYRE_TAIR`, che non è dichiarato come "
            "temperatura al core → mostrate a parte, fuori dal giudizio contro la finestra Kunos")

    avvertenze = registrazione.avvertenze
    if registrazione.ritagliata_in_i2:
        # già spiegate sopra, in positivo: il ritaglio è un giro
        avvertenze = [a for a in avvertenze if not a.startswith(
            ("i canali coprono durate diverse", "nessun passaggio sul traguardo"))]
    assunzioni.extend(avvertenze)
    meta = Meta(
        fonte=Fonte.MOTEC,
        file_origine=nome_file or (ld.percorso.name if ld.percorso else None),
        car=vettura,
        track=pista,
        pilota=ld.pilota or None,
        iniziata_il=ld.data_ora,
        durata_s=round(durata, 1),
        mescola=mescola,
        piattaforma=Piattaforma.PC,
        riferimento=riferimento,
        ritaglio_i2=bool(registrazione.ritagliata_in_i2),
    )
    bundle = SessionBundle(
        meta=meta,
        giri=giri,
        setup=setup,
        canali=Canali(frequenza_hz=FREQUENZA_HZ, nomi=sorted(canali), file=file_canali,
                      campioni=n),
        carburante_fonte=fonte_carburante,
        assunzioni=assunzioni,
    )
    colonne_f4 = sorted(k for k, v in canali.items() if v.dtype == np.float32)
    colonne_i4 = sorted(k for k, v in canali.items() if v.dtype == np.int32)
    metadati = {
        "fonte": "motec",
        "riferimento": riferimento,
        "vettura": vettura,
        "pista": pista,
        "pilota": ld.pilota or None,
        "frequenza_hz": FREQUENZA_HZ,
        "campioni": n,
        "attendibile": True,
        "colonne": {"f4": colonne_f4, "i4": colonne_i4},
        "assunzioni": assunzioni,
        "motec": {
            "vettura_intestazione": ld.vettura or None,
            "pista_intestazione": ld.pista or None,
            "ritagliata_in_i2": registrazione.ritagliata_in_i2,
            "beacon_s": beacon,
        },
    }
    return bundle, canali, metadati


def salva_registrazione(cartella: Path, canali: dict[str, np.ndarray],
                        metadati: dict[str, Any]) -> None:
    """Scrive `canali.npz` e `sessione.json` nel formato del registratore."""
    cartella.mkdir(parents=True, exist_ok=True)
    f4, i4 = metadati["colonne"]["f4"], metadati["colonne"]["i4"]
    n = metadati["campioni"]
    np.savez_compressed(
        cartella / "canali.npz",
        f4=(np.column_stack([canali[c] for c in f4]).astype(np.float32) if f4
            else np.zeros((n, 0), np.float32)),
        i4=(np.column_stack([canali[c] for c in i4]).astype(np.int32) if i4
            else np.zeros((n, 0), np.int32)),
    )
    (cartella / "sessione.json").write_text(
        json.dumps(metadati, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
