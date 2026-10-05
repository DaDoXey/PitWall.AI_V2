"""bundle/demo_precedente.py — «la volta prima» della demo (confronto fra sessioni).

Il confronto fra due sessioni sulla stessa pista e vettura (`analisi/confronto.py`) ha
bisogno di una sessione precedente. Sulla demo non c'è: questa è la sua, generata con lo
stesso banco e lo stesso tracciato di `bundle/demo.py`, datata il giorno prima.

**La storia, decisa con Edoardo il 05/10/2026 («setup e guida insieme»):** stessa pista,
stessa vettura, otto giri. La volta prima le posteriori erano ancora più basse (4 click
in meno a freddo, 0.4 psi a caldo), il giro migliore arrivava al terzo giro, il
retrotreno cedeva già dal quarto e la Post.DX finiva più calda. Alla Variante della
Roggia si passava più piano; alla Lesmo 1, invece, un filo più forte di oggi. Così il
confronto ha da dire su tutte e quattro le cose: ritmo, curve, setup, gomme.

**Cosa è vero e cosa no:** come la demo, i canali sono sintetici e la sessione lo
dichiara. Il setup è lo stesso file vero di ACC della demo, con le sole due pressioni
posteriori cambiate qui (e detto nelle assunzioni).

**Non è in archivio.** Non si apre, non compare negli elenchi, non si scrive sul disco:
esiste solo come termine di paragone della demo, costruita in memoria quando serve.

Numeri protetti come quelli della demo: scritti con l'«ok procedi» del 05/10/2026.
I numeri di `bundle/demo.py` non sono toccati.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache

import numpy as np

from app.bundle import demo
from app.telemetria.banco import CurvaFinta, GiroFinto, PistaFinta, genera

ID = "20000101-000000-monza_bmw_m4_gt3_demo_prima-d3e1"
INIZIATA_IL = datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc)   # il giorno prima della demo

# Km/h di velocità minima in più (o in meno) rispetto alla demo, a ogni giro: la guida
# di quel giorno. Alla Roggia più piano, alla Lesmo 1 un filo più forte.
_GUIDA = {"Variante della Roggia": -4.5, "Lesmo 1": 4.5}

_GOMME_FREDDE = {"Variante del Rettifilo": 1.0, "Variante della Roggia": 1.0}
_RETROTRENO_COTTO = {"Ascari": 1.0, "Parabolica": 1.0, "Lesmo 2": 0.6}
# (dove si perde, km/h persi): il migliore al terzo giro, poi il retrotreno cede.
_PERDITE = (
    (_GOMME_FREDDE, 7.2),
    (_GOMME_FREDDE, 2.6),
    ({}, 0.0),
    (_RETROTRENO_COTTO, 2.5),
    (_RETROTRENO_COTTO, 5.5),
    (_RETROTRENO_COTTO, 8.0),
    (_RETROTRENO_COTTO, 10.5),
    (_RETROTRENO_COTTO, 12.5),
)
# Pressioni a caldo (psi): anteriori come la demo, posteriori 0.4 psi sotto.
_PRESSIONI = {
    "FL": (26.0, 26.1, 26.2, 26.3, 26.4, 26.4, 26.5, 26.5),
    "FR": (26.1, 26.2, 26.3, 26.4, 26.5, 26.6, 26.7, 26.7),
    "RL": (24.5, 24.7, 24.9, 25.0, 25.1, 25.2, 25.3, 25.3),
    "RR": (24.3, 24.5, 24.7, 24.8, 24.9, 25.0, 25.1, 25.1),
}
_TEMPERATURE_CORE = {
    "FL": (78.0, 80.0, 82.0, 83.0, 85.0, 86.0, 87.0, 88.0),
    "FR": (79.0, 81.0, 83.0, 85.0, 86.0, 88.0, 89.0, 90.0),
    "RL": (81.0, 84.0, 88.0, 91.0, 93.0, 95.0, 96.0, 97.0),
    "RR": (83.0, 88.0, 93.0, 98.0, 102.0, 105.0, 107.0, 108.0),
}
_CONSUMO_L = (3.2, 3.1, 3.0, 3.2, 3.3, 3.2, 3.3, 3.3)
# Click a freddo delle posteriori nel file di setup: 4 in meno della demo (48 e 54).
_PRESSIONI_POSTERIORI_CLICK = (44, 50)


def _curve(perdite: dict[str, float]) -> list[CurvaFinta]:
    return [CurvaFinta(posizione_m=p, velocita_minima_kmh=v + _GUIDA.get(nome, 0.0) - perdite.get(nome, 0.0),
                       frenata_m=f, accelerazione_m=a)
            for nome, p, v, f, a in demo._CURVE]


def _canali() -> dict[str, np.ndarray]:
    pista = PistaFinta(lunghezza_m=demo.LUNGHEZZA_M, velocita_massima_kmh=demo.VELOCITA_MASSIMA_KMH,
                       frequenza_hz=demo.FREQUENZA_HZ, curve=_curve({}))
    giri = [GiroFinto(curve=_curve({n: peso * k for n, peso in schema.items()}))
            for schema, k in _PERDITE]
    canali = genera(pista, giri, completo=True, carburante_iniziale_l=demo._CARBURANTE_INIZIALE_L)
    giro = canali["graphics.completedLaps"].astype(np.int64)
    quota = canali["graphics.normalizedCarPosition"].astype(np.float64)

    for ruota in ("FL", "FR", "RL", "RR"):
        canali[f"physics.wheelPressure.{ruota}"] = np.asarray(
            np.take(_PRESSIONI[ruota], giro), dtype=np.float32)
        canali[f"physics.tyreCoreTemp.{ruota}"] = np.asarray(
            np.take(_TEMPERATURE_CORE[ruota], giro), dtype=np.float32)

    consumo = np.asarray(_CONSUMO_L)
    gia_usato = np.concatenate(([0.0], np.cumsum(consumo)))
    usato = gia_usato[giro] + consumo[giro] * quota
    canali["graphics.usedFuel"] = np.asarray(usato, dtype=np.float32)
    canali["physics.fuel"] = np.asarray(demo._CARBURANTE_INIZIALE_L - usato, dtype=np.float32)

    freno = canali["physics.brake"]
    anteriori = demo._freni(freno, riposo=300.0, caldo=645.0)
    posteriori = demo._freni(freno, riposo=250.0, caldo=455.0)
    canali["physics.brakeTemp.FL"] = anteriori
    canali["physics.brakeTemp.FR"] = anteriori + np.float32(8.0)
    canali["physics.brakeTemp.RL"] = posteriori
    canali["physics.brakeTemp.RR"] = posteriori + np.float32(5.0)
    return canali


def _setup():
    from app.bundle.adapters.acc_setup import leggi_setup_acc

    dati = json.loads(demo._SETUP.read_text(encoding="utf-8"))
    pressioni = dati["basicSetup"]["tyres"]["tyrePressure"]
    pressioni[2], pressioni[3] = _PRESSIONI_POSTERIORI_CLICK
    setup = leggi_setup_acc(json.dumps(dati).encode("utf-8"), nome="Setup demo · Monza · la volta prima")
    setup.assunzioni.append(
        "setup della demo con le sole pressioni posteriori cambiate dal generatore (4 click in meno)")
    return setup


@lru_cache(maxsize=1)
def costruisci() -> tuple:
    """(bundle, canali) della volta prima. In memoria: niente sul disco, sempre uguale."""
    from app.bundle.adapters.acc_telemetria import bundle_da_canali
    from app.bundle.schema import Fonte

    serie = _canali()
    metadati = dict(demo._metadati(serie), id=ID,
                    inizio="2026-07-14T10:00:00+00:00", fine="2026-07-14T10:14:30+00:00")
    bundle = bundle_da_canali(serie, metadati, file_canali=f"{ID}/canali.npz")
    bundle.meta.fonte = Fonte.DEMO
    bundle.meta.importato_il = datetime(2026, 10, 5, tzinfo=timezone.utc)
    bundle.meta.iniziata_il = INIZIATA_IL
    bundle.meta.file_origine = "generatore della demo PitWall (la volta prima)"
    bundle.setup = _setup()
    return bundle, serie
