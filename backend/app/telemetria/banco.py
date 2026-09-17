"""Un tracciato finto, ma coerente: serve a provare l'analisi per curva.

ACC non c'è su questo PC (sta sulla PS5 di Edoardo) e non ci sarà: i canali veri non
si possono registrare. Però l'analisi per curva si può provare **meglio** che su dati
veri, perché qui si sa la risposta in anticipo: le curve stanno dove le ho messe, e la
differenza fra un giro e l'altro è quella che ho deciso io. Se il codice trova un
apice dove non c'è, o attribuisce alla curva 3 un decimo perso nella 2, il test cade.

Il modello è volutamente elementare — velocità che scende in modo lineare fino
all'apice e risale dopo — perché non deve somigliare alla fisica: deve essere
**esattamente prevedibile**. La guida vera la si prova in pista, non qui.

Lo usano i test (tramite `tests/pista_finta.py`) e la sessione DEMO (`bundle/demo.py`):
entrambi hanno bisogno di canali di cui si conosce la risposta.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class CurvaFinta:
    """Una curva: dove sta (metri dal traguardo) e quanto rallenta."""

    posizione_m: float
    velocita_minima_kmh: float
    frenata_m: float = 120.0        # quanto prima dell'apice comincia la frenata
    accelerazione_m: float = 200.0  # quanto dopo l'apice si torna alla velocità piena


@dataclass
class GiroFinto:
    """Un giro: le sue curve, eventualmente diverse da quelle di riferimento."""

    curve: list[CurvaFinta]
    valido: bool = True
    ai_box: bool = False


@dataclass
class PistaFinta:
    lunghezza_m: float = 3000.0
    velocita_massima_kmh: float = 220.0
    frequenza_hz: float = 100.0
    curve: list[CurvaFinta] = field(default_factory=list)

    def velocita(self, s: float, curve: list[CurvaFinta]) -> float:
        """Velocità (km/h) alla distanza s: la più bassa fra quelle imposte dalle curve."""
        v = self.velocita_massima_kmh
        for curva in curve:
            # distanza con segno dall'apice, tenendo conto dell'anello
            delta = (s - curva.posizione_m + self.lunghezza_m / 2) % self.lunghezza_m
            delta -= self.lunghezza_m / 2
            if -curva.frenata_m <= delta <= 0:
                quota = (delta + curva.frenata_m) / curva.frenata_m      # 0 -> 1
                v = min(v, self.velocita_massima_kmh
                        - quota * (self.velocita_massima_kmh - curva.velocita_minima_kmh))
            elif 0 < delta <= curva.accelerazione_m:
                quota = delta / curva.accelerazione_m
                v = min(v, curva.velocita_minima_kmh
                        + quota * (self.velocita_massima_kmh - curva.velocita_minima_kmh))
        return v


def genera(
    pista: PistaFinta,
    giri: list[GiroFinto],
    completo: bool = False,
    carburante_iniziale_l: float = 60.0,
    consumo_per_giro_l: float = 2.5,
    squilibrio_pressione_psi: float = 0.0,
    crescita_pressione_psi_giro: float = 0.0,
    pressioni: dict[str, float] | None = None,
    temperature_core: dict[str, float] | None = None,
    gomme_da_bagnato: bool = False,
    freni_c: tuple[float, float] = (380.0, 330.0),
) -> dict[str, np.ndarray]:
    """Genera i canali di una sessione, nello stesso formato che scrive il registratore.

    Con `completo=True` aggiunge i canali che servono al bundle e all'analisi di
    gomme e freni: carburante che cala, pressioni e temperature per ruota, freni,
    tempo ufficiale del giro precedente, settori, condizioni. Anche questi
    volutamente prevedibili: il consumo è esattamente `consumo_per_giro_l`, e lo
    squilibrio fra i lati è esattamente quello che si chiede.
    """
    dt = 1.0 / pista.frequenza_hz
    posizione: list[float] = []
    velocita: list[float] = []
    freno: list[float] = []
    gas: list[float] = []
    tempo_ms: list[int] = []
    validi: list[int] = []
    box: list[int] = []
    completati: list[int] = []
    sterzo: list[float] = []
    marcia: list[int] = []

    t = 0.0
    for indice, giro in enumerate(giri):
        s = 0.0
        while s < pista.lunghezza_m:
            v = pista.velocita(s, giro.curve)
            v_dopo = pista.velocita(min(s + v / 3.6 * dt, pista.lunghezza_m), giro.curve)
            posizione.append(s / pista.lunghezza_m)
            velocita.append(v)
            # freno e gas seguono il segno dell'accelerazione: niente di più, niente di meno
            differenza = v_dopo - v
            freno.append(1.0 if differenza < -0.05 else 0.0)
            gas.append(1.0 if differenza > 0.05 else (1.0 if differenza == 0 and
                                                      v >= pista.velocita_massima_kmh - 0.01
                                                      else 0.0))
            tempo_ms.append(int(round(t * 1000)))
            validi.append(1 if giro.valido else 0)
            box.append(1 if giro.ai_box else 0)
            completati.append(indice)
            sterzo.append(0.0 if v >= pista.velocita_massima_kmh - 0.01 else -0.4)
            marcia.append(3 if v < 120 else 6)
            s += v / 3.6 * dt
            t += dt

    canali = {
        "graphics.normalizedCarPosition": np.asarray(posizione, dtype=np.float32),
        "physics.speedKmh": np.asarray(velocita, dtype=np.float32),
        "physics.brake": np.asarray(freno, dtype=np.float32),
        "physics.gas": np.asarray(gas, dtype=np.float32),
        "physics.steerAngle": np.asarray(sterzo, dtype=np.float32),
        "physics.gear": np.asarray(marcia, dtype=np.int32),
        "pitwall.tempo_ms": np.asarray(tempo_ms, dtype=np.int32),
        "graphics.isValidLap": np.asarray(validi, dtype=np.int32),
        "graphics.isInPitLane": np.asarray(box, dtype=np.int32),
        "graphics.completedLaps": np.asarray(completati, dtype=np.int32),
    }
    if not completo:
        return canali

    # ── i canali che servono al bundle e all'analisi di gomme e freni ──
    numero_giro = np.asarray(completati, dtype=np.int32)
    quota = np.asarray(posizione, dtype=np.float64)          # 0-1 dentro il giro
    percorso = numero_giro + quota                            # giri percorsi, con la frazione

    canali["physics.fuel"] = np.asarray(
        carburante_iniziale_l - percorso * consumo_per_giro_l, dtype=np.float32)
    canali["graphics.usedFuel"] = np.asarray(percorso * consumo_per_giro_l, dtype=np.float32)
    canali["graphics.rainTyres"] = np.full(len(posizione), 1 if gomme_da_bagnato else 0,
                                           dtype=np.int32)
    canali["physics.airTemp"] = np.full(len(posizione), 24.0, dtype=np.float32)
    canali["physics.roadTemp"] = np.full(len(posizione), 31.0, dtype=np.float32)

    # pressioni: base uguale per tutti, più lo squilibrio chiesto sul lato sinistro
    # e la crescita per giro. Ogni ruota resta riconoscibile dal suo scostamento.
    # La base sta nella finestra Kunos (26-27 psi): un banco «pulito» non deve
    # generare voci di finestra da solo.
    base = 26.4
    # Gli scostamenti sono UGUALI fra sinistra e destra e diversi fra i due assi:
    # cosi' `squilibrio_pressione_psi` e' esattamente lo squilibrio sinistra-destra
    # che il test misurera', senza contributi nascosti del banco.
    scostamenti = {"FL": 0.10, "FR": 0.10, "RL": -0.05, "RR": -0.05}
    for ruota, scostamento in scostamenti.items():
        lato_sinistro = ruota in ("FL", "RL")
        # `pressioni` e `temperature_core` sostituiscono il valore di partenza di una
        # ruota: servono a mettere una gomma fuori finestra sapendo di quanto.
        partenza = pressioni[ruota] if pressioni and ruota in pressioni else base + scostamento
        valori = (partenza
                  + (squilibrio_pressione_psi if lato_sinistro else 0.0)
                  + percorso * crescita_pressione_psi_giro)
        canali[f"physics.wheelPressure.{ruota}"] = np.asarray(valori, dtype=np.float32)
        core = (temperature_core[ruota] if temperature_core and ruota in temperature_core
                else 82.0 + scostamento * 10)
        canali[f"physics.tyreCoreTemp.{ruota}"] = np.full(len(posizione), core, dtype=np.float32)
        canali[f"physics.brakeTemp.{ruota}"] = np.asarray(
            [freni_c[0] if ruota.startswith("F") else freni_c[1]] * len(posizione),
            dtype=np.float32)
        canali[f"physics.padLife.{ruota}"] = np.asarray(
            29.0 - percorso * 0.05, dtype=np.float32)
        canali[f"physics.discLife.{ruota}"] = np.asarray(
            32.0 - percorso * 0.02, dtype=np.float32)

    # tempo ufficiale del giro precedente, come lo espone ACC: cambia al traguardo
    dt = 1.0 / pista.frequenza_hz
    campioni_per_giro = [int(np.sum(numero_giro == n)) for n in range(len(giri))]
    ultimo = np.zeros(len(posizione), dtype=np.int32)
    inizio = 0
    for indice, quanti in enumerate(campioni_per_giro):
        if indice > 0:
            ultimo[inizio:inizio + quanti] = int(round(campioni_per_giro[indice - 1] * dt * 1000))
        inizio += quanti
    canali["graphics.iLastTime"] = ultimo

    # settori: tre parti uguali del giro, con lo split del settore appena chiuso
    settore = np.minimum((quota * 3).astype(np.int32), 2)
    canali["graphics.currentSectorIndex"] = settore.astype(np.int32)
    tempo = np.asarray(tempo_ms, dtype=np.int64)
    split = np.zeros(len(posizione), dtype=np.int32)
    for indice in range(1, len(posizione)):
        if settore[indice] != settore[indice - 1]:
            inizio_giro = int(np.flatnonzero(numero_giro == numero_giro[indice])[0])
            split[indice:] = int(tempo[indice] - tempo[inizio_giro])
    canali["graphics.iSplit"] = split

    # durata dell'ultimo settore chiuso, come `lastSectorTime`: cambia a ogni passaggio
    # di settore, traguardo compreso (dove chiude il terzo)
    durata = np.zeros(len(posizione), dtype=np.int32)
    ultimo_cambio = 0
    for indice in range(1, len(posizione)):
        if settore[indice] != settore[indice - 1]:
            durata[indice:] = int(tempo[indice] - tempo[ultimo_cambio])
            ultimo_cambio = indice
    canali["graphics.lastSectorTime"] = durata

    canali["graphics.currentTyreSet"] = np.ones(len(posizione), dtype=np.int32)
    canali["graphics.rainIntensity"] = np.zeros(len(posizione), dtype=np.int32)
    canali["graphics.trackGripStatus"] = np.full(len(posizione), 2, dtype=np.int32)
    canali["graphics.GlobalYellow"] = np.zeros(len(posizione), dtype=np.int32)
    return canali


def pista_tre_curve() -> PistaFinta:
    """Il riferimento usato dai test: 3 km, tre curve ben distinte."""
    return PistaFinta(
        lunghezza_m=3000.0,
        velocita_massima_kmh=220.0,
        curve=[
            CurvaFinta(posizione_m=600.0, velocita_minima_kmh=90.0),
            CurvaFinta(posizione_m=1500.0, velocita_minima_kmh=120.0),
            CurvaFinta(posizione_m=2400.0, velocita_minima_kmh=70.0),
        ],
    )
