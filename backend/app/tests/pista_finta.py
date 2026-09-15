"""Un tracciato finto, ma coerente: serve a provare l'analisi per curva.

ACC non c'è su questo PC (sta sulla PS5 di Edoardo) e non ci sarà: i canali veri non
si possono registrare. Però l'analisi per curva si può provare **meglio** che su dati
veri, perché qui si sa la risposta in anticipo: le curve stanno dove le ho messe, e la
differenza fra un giro e l'altro è quella che ho deciso io. Se il codice trova un
apice dove non c'è, o attribuisce alla curva 3 un decimo perso nella 2, il test cade.

Il modello è volutamente elementare — velocità che scende in modo lineare fino
all'apice e risale dopo — perché non deve somigliare alla fisica: deve essere
**esattamente prevedibile**. La guida vera la si prova in pista, non qui.
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


def genera(pista: PistaFinta, giri: list[GiroFinto]) -> dict[str, np.ndarray]:
    """Genera i canali di una sessione, nello stesso formato che scrive il registratore."""
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

    return {
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
