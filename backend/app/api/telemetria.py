"""api/telemetria.py — il registratore della shared memory, visto da fuori (L3 · Fase 2).

Rotte:
- `GET  /api/telemetria/stato`              — agganciato? sta registrando? quanto?
- `POST /api/telemetria/avvia`              — accende il registratore
- `POST /api/telemetria/ferma`              — lo spegne e chiude la sessione aperta
- `GET  /api/telemetria/sessioni`           — le registrazioni sul disco
- `GET  /api/telemetria/sessioni/{id}`      — i metadati di una registrazione
- `GET  /api/telemetria/sessioni/{id}/canali` — le serie, per nome, con decimazione
- `GET  /api/telemetria/sessioni/{id}/curve`  — l'analisi per curva (L3 · Fase 3)
- `POST /api/telemetria/sessioni/{id}/importa` — la registrazione diventa un session bundle
- `DELETE /api/telemetria/sessioni/{id}`    — cancella una registrazione

**Presidio.** Come per l'import di L1, queste rotte non toccano né la chiave né la
rete: vivono sul PC del pilota. L'interruttore è `PITWALL_ALLOW_RECORDER` (default
acceso); sul deploy pubblico va spento, così la vetrina non prova ad agganciarsi a
un gioco che lì non esiste.

**Perché `avvia` esiste, se il registratore parte da solo.** Perché il gioco può
partire dopo il backend, o il pilota può volerlo spegnere senza fermare l'app: la
partenza automatica è una comodità, non una gabbia.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import numpy as np
from fastapi import APIRouter, HTTPException, Query

from app.analisi.curve import CurveNonCalcolabili, analizza_curve
from app.bundle import demo, store
from app.bundle.adapters.acc_telemetria import (
    TelemetriaNonConvertibile,
    bundle_da_registrazione,
)
from app.telemetria import registratore as reg

router = APIRouter()
log = logging.getLogger("pitwall.telemetria")

# Stesso schema degli id dei bundle (data-ora-nome-esadecimali): validato prima di
# toccare il disco, perché un id arriva dalla rete.
ID_VALIDO = re.compile(r"^[0-9]{8}-[0-9]{6}-[a-z0-9_]{1,48}-[0-9a-f]{4}$")

_registratore: reg.Registratore | None = None


def registratore() -> reg.Registratore:
    """Un solo registratore per processo: due thread sulla stessa memoria non servono."""
    global _registratore
    if _registratore is None:
        _registratore = reg.Registratore()
    return _registratore


def _presidio() -> None:
    if not reg.abilitato():
        log.warning("503: telemetria richiesta ma PITWALL_ALLOW_RECORDER e' spento")
        raise HTTPException(
            status_code=503,
            detail="Registratore di telemetria disattivato su questa installazione",
        )


def _cartella(id_sessione: str) -> Path:
    if not ID_VALIDO.match(id_sessione or ""):
        raise HTTPException(status_code=400, detail=f"id non valido: {id_sessione!r}")
    radice = reg.cartella_telemetria().resolve()
    percorso = (radice / id_sessione).resolve()
    if percorso.parent != radice or not percorso.is_dir():
        raise HTTPException(status_code=404, detail="registrazione non trovata")
    return percorso


def _metadati(cartella: Path) -> dict:
    percorso = cartella / "sessione.json"
    if not percorso.exists():
        raise HTTPException(status_code=404, detail="registrazione senza metadati")
    dati = json.loads(percorso.read_text(encoding="utf-8"))
    dati["ha_canali"] = (cartella / "canali.npz").exists()
    return dati


@router.get("/telemetria/stato")
def stato():
    """Che cosa sta facendo il registratore, adesso."""
    return registratore().stato()


@router.post("/telemetria/avvia")
def avvia():
    _presidio()
    registratore().avvia()
    return registratore().stato()


@router.post("/telemetria/ferma")
def ferma():
    _presidio()
    id_chiuso = registratore().ferma()
    return {"fermato": True, "sessione_chiusa": id_chiuso, **registratore().stato()}


@router.get("/telemetria/sessioni")
def elenca(limite: int = Query(default=50, ge=1, le=500)):
    """Le registrazioni sul disco, dalla più recente."""
    radice = reg.cartella_telemetria()
    fuori = []
    for cartella in sorted(radice.iterdir(), reverse=True):
        if not cartella.is_dir() or not (cartella / "sessione.json").exists():
            continue
        dati = _metadati(cartella)
        # Le conversioni di un file MoTeC (L5) vivono qui per il formato dei canali, ma non
        # sono registrazioni da importare: sono già sessioni dell'archivio.
        if dati.get("fonte") == "motec":
            continue
        fuori.append({
            "id": dati.get("id", cartella.name),
            "inizio": dati.get("inizio"),
            "fine": dati.get("fine"),
            "vettura": dati.get("vettura"),
            "pista": dati.get("pista"),
            "tipo_sessione": dati.get("tipo_sessione"),
            "campioni": dati.get("campioni", 0),
            "frequenza_hz": dati.get("frequenza_hz"),
            "attendibile": dati.get("attendibile", True),
            "ha_canali": dati["ha_canali"],
            "canali_rimossi": dati.get("canali_rimossi", False),
        })
        if len(fuori) >= limite:
            break
    return {"sessioni": fuori, "totale": len(fuori),
            "cartella": str(radice), "tetto": reg.tetto_sessioni()}


@router.get("/telemetria/sessioni/{id_sessione}")
def dettaglio(id_sessione: str):
    return _metadati(_cartella(id_sessione))


@router.get("/telemetria/sessioni/{id_sessione}/canali")
def canali(
    id_sessione: str,
    nomi: str = Query(default="", description="nomi dei canali separati da virgola"),
    ogni: int = Query(default=1, ge=1, le=1000,
                      description="prende un campione ogni N (decimazione)"),
    massimo: int = Query(default=5000, ge=1, le=100_000),
):
    """Le serie richieste, decimate.

    Senza `nomi` non si restituisce tutto: 211 colonne per decine di migliaia di
    campioni non si mandano «per comodità» dentro una risposta JSON. Si chiede
    quello che serve.
    """
    cartella = _cartella(id_sessione)
    if not (cartella / "canali.npz").exists():
        raise HTTPException(
            status_code=409,
            detail="registrazione senza canali (consolidamento mancato o tetto applicato)",
        )
    richiesti = [n.strip() for n in nomi.split(",") if n.strip()]
    if not richiesti:
        raise HTTPException(status_code=400,
                            detail="specificare almeno un canale in `nomi`")

    serie = reg.leggi_canali(cartella)
    sconosciuti = [n for n in richiesti if n not in serie]
    if sconosciuti:
        raise HTTPException(status_code=404,
                            detail=f"canali sconosciuti: {sconosciuti}")

    fuori = {}
    for nome in richiesti:
        valori = serie[nome][::ogni][:massimo]
        fuori[nome] = [None if not np.isfinite(v) else float(v) for v in valori]
    return {
        "id": id_sessione,
        "ogni": ogni,
        "campioni": len(next(iter(fuori.values()))) if fuori else 0,
        "canali": fuori,
    }


@router.get("/telemetria/sessioni/{id_sessione}/curve")
def curve(
    id_sessione: str,
    punti: int = Query(default=2000, ge=200, le=20000,
                       description="risoluzione della griglia di posizione"),
    dettaglio: bool = Query(default=False,
                            description="includi la riga per ogni curva e ogni giro"),
):
    """L'analisi per curva: dove perdi, quanto, e cosa fare (L3 · Fase 3).

    Deterministica, nessun LLM, nessuna rete. Il `dettaglio` (curve × giri) si chiede
    apposta: su una sessione lunga sono centinaia di righe che a una schermata di
    riepilogo non servono.
    """
    cartella = _cartella(id_sessione)
    if not (cartella / "canali.npz").exists():
        raise HTTPException(status_code=409,
                            detail="registrazione senza canali: niente da analizzare")
    try:
        report = analizza_curve(reg.leggi_canali(cartella), punti=punti)
    except CurveNonCalcolabili as errore:
        # 422: la registrazione c'è, ma non permette questa analisi. Non è un 500, e
        # nemmeno un 404: è una risposta, e dice perché.
        raise HTTPException(status_code=422, detail=str(errore)) from errore

    fuori = report.come_json()
    if not dettaglio:
        fuori.pop("dettaglio")
    return fuori


@router.post("/telemetria/sessioni/{id_sessione}/importa")
def importa(id_sessione: str):
    """Trasforma una registrazione in un session bundle e la mette nell'archivio.

    Da qui in poi la sessione registrata vive dove vivono le altre: stesso elenco,
    stesso formato, stessa analisi. È il punto in cui L1 e L3 smettono di essere due
    mondi (L3 · Fase 4).
    """
    _presidio()
    if demo.e_demo(id_sessione):
        raise HTTPException(status_code=409,
                            detail="La demo è già nell'archivio delle sessioni")
    cartella = _cartella(id_sessione)
    if _metadati(cartella).get("fonte") == "motec":
        raise HTTPException(status_code=409,
                            detail="Conversione di un file MoTeC: è già una sessione dell'archivio")
    try:
        bundle, _canali = bundle_da_registrazione(cartella)
    except TelemetriaNonConvertibile as errore:
        raise HTTPException(status_code=422, detail=str(errore)) from errore
    id_bundle = store.salva(bundle)
    log.info("registrazione %s importata come bundle %s", id_sessione, id_bundle)
    return {
        "id_registrazione": id_sessione,
        "id_sessione": id_bundle,
        "giri": len(bundle.giri),
        "giri_con_tempo": len([g for g in bundle.giri if g.tempo_ms]),
        "assunzioni": bundle.assunzioni,
    }


@router.delete("/telemetria/sessioni/{id_sessione}")
def cancella(id_sessione: str):
    import shutil

    if demo.e_demo(id_sessione):
        raise HTTPException(status_code=403, detail="La registrazione demo non si cancella")
    cartella = _cartella(id_sessione)
    shutil.rmtree(cartella)
    log.info("registrazione cancellata: %s", id_sessione)
    return {"cancellata": id_sessione}
