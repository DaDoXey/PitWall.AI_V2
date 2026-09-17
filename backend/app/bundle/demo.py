"""bundle/demo.py — la sessione DEMO, nello stesso formato di una sessione vera (L4).

Decisione del 16/09/2026: la demo **non è più un mucchio di numeri scritti a mano**
(`core/demo_data.py`), ma un session bundle con i suoi canali, generato da PitWall e
analizzato dallo **stesso motore** che analizza le sessioni vere. Così le schermate e
Gigi hanno un solo percorso di codice, e ogni cifra della demo è una cifra che il
motore sa dimostrare.

**La storia resta quella di sempre:** Monza, BMW M4 GT3, otto giri di prove su pista
asciutta. Le gomme partono fredde (si perde in uscita dalle varianti), il giro migliore
arriva al quarto, poi il retrotreno — pressioni basse — si surriscalda: la Post.DX
supera i 100 °C al core e il tempo si perde fra Lesmo, Ascari e Parabolica.

**Cosa è vero e cosa no, detto senza giri di parole:**

* i canali sono **sintetici**: vengono dal banco `telemetria/banco.py`, con curve nelle
  posizioni di Monza e perdite calibrate per ottenere i tempi della storia. Non sono una
  guida reale, e la sessione lo dichiara nelle assunzioni;
* il setup invece è un **file vero di ACC** (BMW M4 GT3, Monza), lo stesso usato nei
  test dell'adattatore;
* nel repository non c'è nessun canale: c'è questo generatore. Otto giri a 100 Hz sono
  qualche MB, e si creano da soli al primo avvio (o quando mancano), sempre uguali.

Numeri protetti: le cifre della demo erano in un file protetto; questa riscrittura è
stata sbloccata con «ok procedi su tutto» del 16/09/2026.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from app.telemetria.banco import CurvaFinta, GiroFinto, PistaFinta, genera

log = logging.getLogger("pitwall.demo")

# Id fisso: la data del 2000 la mette in fondo all'elenco, dopo le sessioni del pilota.
DEMO_ID = "20000101-000000-monza_bmw_m4_gt3_demo-d3e0"
# Si alza quando cambia qualcosa qui dentro: all'avvio la demo si rigenera.
VERSIONE_GENERATORE = "1"
FREQUENZA_HZ = 100.0

_SETUP = Path(__file__).resolve().parents[1] / "core" / "data" / "demo" / "setup_bmw_m4_gt3_monza.json"

# ── il tracciato: sette curve di Monza, posizioni in metri dal traguardo ──
# (nome, posizione, velocità minima km/h, metri di frenata, metri per tornare in piena)
_CURVE = (
    ("Variante del Rettifilo", 950.0, 72.0, 160.0, 950.0),
    ("Curva Biassono", 2000.0, 240.0, 70.0, 250.0),
    ("Variante della Roggia", 2550.0, 88.0, 140.0, 700.0),
    ("Lesmo 1", 3300.0, 175.0, 90.0, 250.0),
    ("Lesmo 2", 3650.0, 160.0, 90.0, 700.0),
    ("Ascari", 4450.0, 150.0, 130.0, 750.0),
    ("Parabolica", 5400.0, 175.0, 140.0, 1100.0),
)
LUNGHEZZA_M = 5793.0
# Calibrata perché il giro senza perdite duri 1:47.82 (script di calibrazione del 16/09).
VELOCITA_MASSIMA_KMH = 272.82

# ── la storia, giro per giro ──
# Km/h di velocità minima persi nelle curve indicate (peso per curva × intensità).
_GOMME_FREDDE = {"Variante del Rettifilo": 1.0, "Variante della Roggia": 1.0}
_RETROTRENO_COTTO = {"Ascari": 1.0, "Parabolica": 1.0, "Lesmo 2": 0.6}
_PERDITE = (
    (_GOMME_FREDDE, 6.589),      # giro 1 → 1:49.42
    (_GOMME_FREDDE, 2.090),      # giro 2 → 1:48.30
    (_GOMME_FREDDE, 0.558),      # giro 3 → 1:47.94
    ({}, 0.0),                   # giro 4 → 1:47.82, il migliore
    (_RETROTRENO_COTTO, 1.609),  # giro 5 → 1:48.01
    (_RETROTRENO_COTTO, 5.648),  # giro 6 → 1:48.52
    (_RETROTRENO_COTTO, 8.351),  # giro 7 → 1:48.87
    (_RETROTRENO_COTTO, 10.474), # giro 8 → 1:49.16
)
# Medie per giro, per ruota: pressione a caldo (psi) e temperatura al core (°C).
# Anteriori nella finestra Kunos (26-27 psi), posteriori sotto: è la causa della storia.
_PRESSIONI = {
    "FL": (26.0, 26.1, 26.2, 26.3, 26.4, 26.4, 26.5, 26.5),
    "FR": (26.1, 26.2, 26.3, 26.4, 26.5, 26.6, 26.7, 26.7),
    "RL": (24.9, 25.1, 25.3, 25.4, 25.5, 25.6, 25.7, 25.7),
    "RR": (24.7, 24.9, 25.1, 25.2, 25.3, 25.4, 25.5, 25.5),
}
_TEMPERATURE_CORE = {
    "FL": (78.0, 80.0, 82.0, 83.0, 85.0, 86.0, 87.0, 88.0),
    "FR": (79.0, 81.0, 83.0, 85.0, 86.0, 88.0, 89.0, 90.0),
    "RL": (80.0, 83.0, 86.0, 88.0, 90.0, 92.0, 93.0, 95.0),
    "RR": (82.0, 86.0, 90.0, 94.0, 98.0, 101.0, 103.0, 105.0),
}
_CONSUMO_L = (3.2, 3.1, 3.3, 3.0, 3.2, 3.3, 3.2, 3.3)
_CARBURANTE_INIZIALE_L = 30.0

_RACCONTO = {
    "andamento": ("Primi due giri a gomme fredde, poi il passo arriva al quarto giro. Dal "
                  "sesto la macchina scivola dietro in uscita e il tempo se ne va."),
    "uscita": "Negli ultimi giri il posteriore parte in uscita da Ascari e Parabolica.",
    "gomme": "Il posteriore destro sembra cotto a fine stint.",
    "curve_critiche": ["Ascari", "Parabolica", "Lesmo 2"],
}


def pista() -> PistaFinta:
    return PistaFinta(
        lunghezza_m=LUNGHEZZA_M,
        velocita_massima_kmh=VELOCITA_MASSIMA_KMH,
        frequenza_hz=FREQUENZA_HZ,
        curve=_curve({}),
    )


def _curve(perdite: dict[str, float]) -> list[CurvaFinta]:
    return [CurvaFinta(posizione_m=p, velocita_minima_kmh=v - perdite.get(nome, 0.0),
                       frenata_m=f, accelerazione_m=a)
            for nome, p, v, f, a in _CURVE]


def _giri() -> list[GiroFinto]:
    return [GiroFinto(curve=_curve({n: peso * k for n, peso in schema.items()}))
            for schema, k in _PERDITE]


def _freni(freno: np.ndarray, riposo: float, caldo: float) -> np.ndarray:
    """Temperatura dei dischi: sale in frenata, scende sul dritto. Primo ordine."""
    dt = 1.0 / FREQUENZA_HZ
    fuori = np.empty(freno.size, dtype=np.float32)
    t = riposo
    for i, pressione in enumerate(freno):
        if pressione > 0.05:
            t += (caldo - t) * 1.1 * dt
        else:
            t += (riposo - t) * 0.10 * dt
        fuori[i] = t
    return fuori


def canali() -> dict[str, np.ndarray]:
    """I canali della sessione demo. Deterministici: stessi valori a ogni chiamata."""
    canali = genera(pista(), _giri(), completo=True,
                    carburante_iniziale_l=_CARBURANTE_INIZIALE_L)
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
    canali["physics.fuel"] = np.asarray(_CARBURANTE_INIZIALE_L - usato, dtype=np.float32)

    # Freni: picchi attorno ai 640 °C davanti e 450 °C dietro. Una ruota per lato un
    # filo più calda: quattro serie identiche non le ha nessuna macchina.
    freno = canali["physics.brake"]
    anteriori = _freni(freno, riposo=300.0, caldo=645.0)
    posteriori = _freni(freno, riposo=250.0, caldo=455.0)
    canali["physics.brakeTemp.FL"] = anteriori
    canali["physics.brakeTemp.FR"] = anteriori + np.float32(8.0)
    canali["physics.brakeTemp.RL"] = posteriori
    canali["physics.brakeTemp.RR"] = posteriori + np.float32(5.0)
    return canali


def _metadati(canali: dict[str, np.ndarray]) -> dict:
    colonne_f4 = sorted(k for k, v in canali.items() if v.dtype == np.float32)
    colonne_i4 = sorted(k for k, v in canali.items() if v.dtype == np.int32)
    return {
        "id": DEMO_ID,
        "demo": True,
        "sintetica": True,
        "versione_generatore": VERSIONE_GENERATORE,
        "inizio": "2026-07-15T10:00:00+00:00",
        "fine": "2026-07-15T10:14:30+00:00",
        "vettura": "bmw_m4_gt3",
        "pista": "monza",
        "pilota": "Pilota demo",
        "tipo_sessione": "PRACTICE",
        "frequenza_hz": FREQUENZA_HZ,
        "mescola_iniziale": "dry_compound",
        "campioni": int(canali["pitwall.tempo_ms"].size),
        "attendibile": True,
        "colonne": {"f4": colonne_f4, "i4": colonne_i4},
        "assunzioni": [
            "SESSIONE DEMO SINTETICA: canali generati da PitWall su un tracciato di prova "
            "con le curve di Monza, non una guida reale. Il setup è un file vero di ACC.",
        ],
    }


def costruisci() -> tuple:
    """(bundle, canali, metadati) della demo, senza scrivere niente."""
    from app.bundle.adapters.acc_setup import leggi_setup_acc
    from app.bundle.adapters.acc_telemetria import bundle_da_canali
    from app.bundle.schema import Fonte, Racconto

    serie = canali()
    metadati = _metadati(serie)
    bundle = bundle_da_canali(serie, metadati, file_canali=f"{DEMO_ID}/canali.npz")
    bundle.meta.fonte = Fonte.DEMO
    bundle.meta.importato_il = datetime(2026, 9, 16, tzinfo=timezone.utc)
    bundle.meta.iniziata_il = datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc)
    bundle.meta.file_origine = "generatore della demo PitWall"
    bundle.setup = leggi_setup_acc(_SETUP, nome="Setup demo · Monza")
    bundle.racconto = Racconto(**_RACCONTO)
    return bundle, serie, metadati


def _aggiornata(cartella: Path) -> bool:
    percorso = cartella / "sessione.json"
    if not percorso.exists() or not (cartella / "canali.npz").exists():
        return False
    try:
        dati = json.loads(percorso.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return dati.get("versione_generatore") == VERSIONE_GENERATORE


def assicura_demo(forza: bool = False) -> str:
    """La demo esiste, è aggiornata ed è nell'archivio. Se no, la crea. Torna l'id."""
    from app.bundle import store
    from app.telemetria.registratore import cartella_telemetria

    cartella = cartella_telemetria() / DEMO_ID
    try:
        presente = store.leggi(DEMO_ID) is not None
    except store.ArchivioError:
        presente = False
    if presente and _aggiornata(cartella) and not forza:
        return DEMO_ID

    bundle, serie, metadati = costruisci()
    cartella.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cartella / "canali.npz",
        f4=np.column_stack([serie[c] for c in metadati["colonne"]["f4"]]).astype(np.float32),
        i4=np.column_stack([serie[c] for c in metadati["colonne"]["i4"]]).astype(np.int32),
    )
    (cartella / "sessione.json").write_text(
        json.dumps(metadati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    store.salva(bundle, DEMO_ID)
    log.info("sessione demo generata (%d campioni, generatore v%s)",
             metadati["campioni"], VERSIONE_GENERATORE)
    return DEMO_ID


def e_demo(id_sessione: str) -> bool:
    return id_sessione == DEMO_ID
