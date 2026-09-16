"""Da una registrazione della shared memory al «session bundle» (L3 · Fase 4).

È il punto in cui i tre strati si incontrano: un file di risultati (L1), un setup
(L1) e una sessione registrata (L3) diventano lo **stesso** documento, e da lì in
poi il motore di analisi, le schermate e Gigi leggono una cosa sola. Era la
promessa del rework: la corrispondenza fra ciò che dice l'ingegnere e ciò che si
vede a schermo diventa **strutturale**, non da mantenere a mano.

Tre scelte che vale la pena dichiarare:

1. **Il tempo sul giro lo dice ACC, non il nostro cronometro.** La pagina grafica
   porta `iLastTime`: è il tempo ufficiale, lo stesso che finisce nei risultati e
   nei ranking. Il nostro `pitwall.tempo_ms` serve da controprova: se i due
   divergono di più di mezzo secondo, il bundle lo **dichiara** invece di scegliere
   di nascosto.
2. **Il carburante finalmente si misura.** Dai risultati di ACC il consumo non si
   ricava (il campo `fuel` è costante per giro, cfr. L1); qui si legge il serbatoio
   campione per campione, e la differenza fra l'inizio e la fine di un giro è il
   consumo vero di quel giro.
3. **I giri incompleti restano fuori dai tempi ma dentro il conteggio.** Il primo
   giro di una registrazione comincia quasi sempre a metà pista: non ha un tempo
   confrontabile, ma è successo, e sparire non deve.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from app.analisi.curve import (
    FRENO,
    GIRO_VALIDO,
    IN_PIT,
    POSIZIONE,
    TEMPO,
    dividi_in_giri,
)
from app.bundle.schema import (
    Canali,
    Condizioni,
    Evento,
    Fonte,
    Giro,
    Meta,
    SessionBundle,
    TipoSessione,
)

CARBURANTE = "physics.fuel"
TEMP_ARIA = "physics.airTemp"
TEMP_PISTA = "physics.roadTemp"
ULTIMO_TEMPO = "graphics.iLastTime"
SPLIT = "graphics.iSplit"
SETTORE = "graphics.currentSectorIndex"
SET_GOMME = "graphics.currentTyreSet"
PIOGGIA = "graphics.rainIntensity"
GRIP = "graphics.trackGripStatus"
GIALLA = "graphics.GlobalYellow"

# Da `ACC_SESSION_TYPE` (pagina grafica) al tipo del bundle.
_TIPI = {
    0: TipoSessione.PROVE, 1: TipoSessione.QUALIFICA, 2: TipoSessione.GARA,
    3: TipoSessione.HOTLAP, 7: TipoSessione.HOTSTINT, 8: TipoSessione.HOTSTINT,
}
_TIPI_TESTO = {
    "PRACTICE": TipoSessione.PROVE, "QUALIFY": TipoSessione.QUALIFICA,
    "RACE": TipoSessione.GARA, "HOTLAP": TipoSessione.HOTLAP,
    "HOTSTINT": TipoSessione.HOTSTINT, "HOTSTINTSUPERPOLE": TipoSessione.HOTSTINT,
}
# L'intensità di pioggia di ACC è un gradino da 0 (asciutto) a 5 (temporale).
_PIOGGIA = {0: 0.0, 1: 0.2, 2: 0.4, 3: 0.6, 4: 0.8, 5: 1.0}
# Il grip: 0 green … 6 flooded. Qui serve solo l'ordine, non una fisica.
_GRIP = {0: 0.80, 1: 0.90, 2: 1.00, 3: 0.70, 4: 0.60, 5: 0.45, 6: 0.30}

SCARTO_TEMPI_MS = 500      # oltre questo, i due cronometri non raccontano lo stesso giro


class TelemetriaNonConvertibile(ValueError):
    """La registrazione non contiene abbastanza per farne un bundle."""


def _media(serie: np.ndarray | None) -> float | None:
    if serie is None or serie.size == 0:
        return None
    valore = float(np.mean(serie))
    return valore if np.isfinite(valore) else None


def _condizioni(canali: dict[str, np.ndarray]) -> Condizioni:
    pioggia = None
    if PIOGGIA in canali and canali[PIOGGIA].size:
        pioggia = _PIOGGIA.get(int(np.median(canali[PIOGGIA])))
    grip = None
    if GRIP in canali and canali[GRIP].size:
        grip = _GRIP.get(int(np.median(canali[GRIP])))
    return Condizioni(
        temp_aria_c=_media(canali.get(TEMP_ARIA)),
        temp_pista_c=_media(canali.get(TEMP_PISTA)),
        grip_linea_ideale=grip,
        pioggia=pioggia,
        pista_bagnata=(pioggia is not None and pioggia > 0) or None,
    )


def _tipo_sessione(metadati: dict[str, Any]) -> TipoSessione:
    testo = (metadati.get("tipo_sessione") or "").upper()
    return _TIPI_TESTO.get(testo, TipoSessione.SCONOSCIUTO)


def bundle_da_canali(
    canali: dict[str, np.ndarray],
    metadati: dict[str, Any],
    file_canali: str = "canali.npz",
) -> SessionBundle:
    """Costruisce il bundle di una sessione registrata."""
    if POSIZIONE not in canali or TEMPO not in canali:
        raise TelemetriaNonConvertibile(
            f"servono almeno «{POSIZIONE}» e «{TEMPO}»"
        )

    assunzioni: list[str] = list(metadati.get("assunzioni") or [])
    giri_canali = dividi_in_giri(canali)
    if not giri_canali:
        raise TelemetriaNonConvertibile("nessun giro nella registrazione")

    ultimo_tempo = canali.get(ULTIMO_TEMPO)
    split = canali.get(SPLIT)
    settore = canali.get(SETTORE)
    carburante = canali.get(CARBURANTE)
    set_gomme = canali.get(SET_GOMME)
    in_pit = canali.get(IN_PIT)
    valido = canali.get(GIRO_VALIDO)

    giri: list[Giro] = []
    eventi: list[Evento] = []
    scarti: list[int] = []
    senza_tempo_ufficiale = 0

    for indice, giro in enumerate(giri_canali):
        inizio, fine = giro.inizio, giro.fine
        nostro = giro.tempo_ms

        # Il tempo ufficiale compare in `iLastTime` subito DOPO il traguardo, cioè
        # all'inizio del giro successivo: si legge lì.
        ufficiale = None
        if ultimo_tempo is not None and fine < ultimo_tempo.size:
            candidato = int(ultimo_tempo[min(fine + 2, ultimo_tempo.size - 1)])
            if candidato > 0:
                ufficiale = candidato

        tempo_ms = None
        if giro.completo:
            if ufficiale:
                tempo_ms = ufficiale
                if nostro and abs(nostro - ufficiale) > SCARTO_TEMPI_MS:
                    scarti.append(giro.numero)
            elif nostro:
                tempo_ms = nostro
                senza_tempo_ufficiale += 1

        splits: list[int] = []
        if split is not None and settore is not None:
            pezzo_settore = settore[inizio:fine]
            cambi = np.flatnonzero(np.diff(pezzo_settore) != 0) + 1
            for cambio in cambi[:3]:
                valore = int(split[inizio + int(cambio) + 1]) if inizio + int(cambio) + 1 < split.size else 0
                if valore > 0:
                    splits.append(valore)

        residuo = usato = None
        if carburante is not None and carburante.size > fine - 1:
            partenza = float(carburante[inizio])
            arrivo = float(carburante[fine - 1])
            residuo = round(arrivo, 3)
            if giro.completo and partenza - arrivo > 0:
                usato = round(partenza - arrivo, 3)

        ai_box = bool(in_pit[inizio:fine].max() > 0) if in_pit is not None else False
        giri.append(Giro(
            numero=giro.numero,
            tempo_ms=tempo_ms,
            splits_ms=splits[:3],
            valido=(bool(valido[inizio:fine].min() > 0) if valido is not None else True)
            and giro.completo,
            carburante_residuo_l=residuo,
            carburante_usato_l=usato,
            in_pit=ai_box,
            out_pit=ai_box and indice > 0,
            set_gomme=int(set_gomme[inizio]) if set_gomme is not None else None,
            timestamp_ms=float(canali[TEMPO][inizio]),
        ))
        if ai_box:
            eventi.append(Evento(tipo="pit", giro=giro.numero,
                                 timestamp_ms=float(canali[TEMPO][inizio]),
                                 nota="passaggio dalla corsia box"))

    # bandiere gialle: si segna l'inizio di ogni esposizione, non ogni campione
    if GIALLA in canali:
        gialla = canali[GIALLA]
        accensioni = np.flatnonzero(np.diff(gialla.astype(np.int32)) > 0) + 1
        for indice in accensioni[:20]:
            eventi.append(Evento(
                tipo="bandiera", timestamp_ms=float(canali[TEMPO][int(indice)]),
                nota="bandiera gialla esposta",
            ))

    incompleti = [g for g in giri_canali if not g.completo]
    if incompleti:
        assunzioni.append(
            f"{len(incompleti)} giri incompleti (registrazione iniziata o finita a metà "
            f"pista): contati, ma senza tempo confrontabile"
        )
    if scarti:
        assunzioni.append(
            f"giri {scarti}: il tempo ufficiale di ACC e il cronometro della "
            f"registrazione divergono di oltre mezzo secondo → si è tenuto quello di ACC"
        )
    if senza_tempo_ufficiale:
        assunzioni.append(
            f"{senza_tempo_ufficiale} giri senza tempo ufficiale nella pagina grafica → "
            f"tempo preso dal cronometro della registrazione"
        )
    if carburante is None:
        assunzioni.append("carburante non registrato: consumo per giro non calcolabile")
    if FRENO not in canali:
        assunzioni.append("canale del freno assente: niente punti di frenata")

    frequenza = float(metadati.get("frequenza_hz") or 0) or 100.0
    campioni = int(canali[POSIZIONE].size)
    meta = Meta(
        fonte=Fonte.ACC_SHARED_MEMORY,
        file_origine=metadati.get("id"),
        car=metadati.get("vettura"),
        track=metadati.get("pista"),
        pilota=metadati.get("pilota"),
        tipo_sessione=_tipo_sessione(metadati),
        durata_s=round(float(canali[TEMPO][-1]) / 1000.0, 1),
        condizioni=_condizioni(canali),
    )
    return SessionBundle(
        meta=meta,
        giri=giri,
        eventi=eventi,
        canali=Canali(
            frequenza_hz=frequenza,
            nomi=sorted(canali),
            file=file_canali,
            campioni=campioni,
        ),
        assunzioni=assunzioni,
    )


def canali_del_bundle(bundle: SessionBundle) -> dict[str, np.ndarray] | None:
    """I canali di un bundle registrato, se esistono ancora sul disco.

    Il bundle non porta i canali dentro di sé (sono decine di MB): porta il percorso,
    relativo alla cartella della telemetria. Se la registrazione è stata cancellata o
    alleggerita dal tetto dell'archivio, qui si torna `None` — e il report lo dirà,
    invece di far finta che i canali non fossero mai esistiti.
    """
    from app.telemetria.registratore import cartella_telemetria, leggi_canali

    if bundle.canali is None or bundle.meta.fonte is not Fonte.ACC_SHARED_MEMORY:
        return None
    cartella = (cartella_telemetria() / bundle.canali.file).parent
    if not (cartella / "canali.npz").exists() or not (cartella / "sessione.json").exists():
        return None
    return leggi_canali(cartella)


def bundle_da_registrazione(cartella: Path) -> tuple[SessionBundle, dict[str, np.ndarray]]:
    """Legge una registrazione dal disco e ne fa un bundle (con i suoi canali)."""
    from app.telemetria.registratore import leggi_canali   # import tardivo: niente cicli

    percorso = cartella / "sessione.json"
    if not percorso.exists():
        raise TelemetriaNonConvertibile(f"{cartella.name}: manca sessione.json")
    if not (cartella / "canali.npz").exists():
        raise TelemetriaNonConvertibile(f"{cartella.name}: mancano i canali")
    metadati = json.loads(percorso.read_text(encoding="utf-8"))
    canali = leggi_canali(cartella)
    bundle = bundle_da_canali(canali, metadati,
                              file_canali=f"{cartella.name}/canali.npz")
    return bundle, canali
