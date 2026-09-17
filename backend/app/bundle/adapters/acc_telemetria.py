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
    FonteCarburante,
    Giro,
    Mescola,
    Meta,
    Piattaforma,
    SessionBundle,
    TipoSessione,
)

CARBURANTE = "physics.fuel"
# Carburante usato dall'ultimo rifornimento: il documento lo dichiara in **litri**,
# mentre `physics.fuel` è dichiarato in kg (e il gioco mostra litri). Per il consumo
# si preferisce quello con l'unità scritta nero su bianco.
CARBURANTE_USATO = "graphics.usedFuel"
TEMP_ARIA = "physics.airTemp"
TEMP_PISTA = "physics.roadTemp"
ULTIMO_TEMPO = "graphics.iLastTime"
# «Last sector time in milliseconds»: la durata dell'ultimo settore chiuso. Si usa
# questo e non `iSplit` («Last split time»), che il documento non dice se sia
# cumulativo o per settore.
TEMPO_SETTORE = "graphics.lastSectorTime"
SETTORE = "graphics.currentSectorIndex"
GOMME_DA_PIOGGIA = "graphics.rainTyres"
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
SCARTO_SETTORI_MS = 100    # tre settori che non sommano al giro non sono quelli del giro
RITARDO_LETTURA = 2        # campioni dopo il cambio: ACC aggiorna il valore con un tick di ritardo


class TelemetriaNonConvertibile(ValueError):
    """La registrazione non contiene abbastanza per farne un bundle."""


def _giri(quanti: int) -> str:
    return "1 giro" if quanti == 1 else f"{quanti} giri"


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


def _mescola(canali: dict[str, np.ndarray], metadati: dict[str, Any]) -> tuple[Mescola | None, str | None]:
    """La mescola montata. Prima il canale (vale per tutta la sessione), poi il nome
    letto all'avvio della registrazione. Se cambia a metà, non se ne sceglie una."""
    serie = canali.get(GOMME_DA_PIOGGIA)
    if serie is not None and serie.size:
        valori = np.unique(np.asarray(serie).astype(np.int64))
        if valori.size > 1:
            return None, "mescola cambiata durante la registrazione: nessuna finestra applicata"
        return (Mescola.BAGNATO if int(valori[0]) else Mescola.ASCIUTTO), None
    nome = (metadati.get("mescola_iniziale") or "").lower()
    if "wet" in nome:
        return Mescola.BAGNATO, None
    if "dry" in nome:
        return Mescola.ASCIUTTO, None
    return None, "mescola non registrata: nessuna finestra applicata alle gomme"


def _leggi_dopo(serie: np.ndarray | None, indice: int) -> int | None:
    """Il valore pochi campioni dopo un cambio, se esiste ed è positivo."""
    if serie is None or indice >= serie.size:
        return None
    valore = int(serie[min(indice + RITARDO_LETTURA, serie.size - 1)])
    return valore if valore > 0 else None


def _settori(settore: np.ndarray | None, durate: np.ndarray | None, inizio: int,
             fine: int, tempo_ms: int | None) -> tuple[list[int], bool]:
    """(split del giro, terzo ricavato per differenza?).

    S1 e S2 si leggono al passaggio 0→1 e 1→2; S3 al traguardo, cioè nei primi
    campioni del giro dopo. Se il giro dopo non c'è (fine registrazione), il terzo è
    il tempo del giro meno i primi due — e lo si dice.
    """
    if settore is None or durate is None:
        return [], False
    pezzo = settore[inizio:fine]
    cambi = np.flatnonzero(np.diff(pezzo) != 0) + 1
    splits: list[int] = []
    for cambio in cambi[:2]:
        valore = _leggi_dopo(durate, inizio + int(cambio))
        if valore is None:
            return [], False
        splits.append(valore)
    if len(splits) < 2:
        return [], False
    terzo = _leggi_dopo(durate, fine) if fine < durate.size else None
    ricavato = False
    if terzo is None and tempo_ms:
        terzo = tempo_ms - sum(splits)
        ricavato = True
    if terzo is None or terzo <= 0:
        return [], False
    splits.append(terzo)
    if tempo_ms and abs(sum(splits) - tempo_ms) > SCARTO_SETTORI_MS:
        return [], False
    return splits, ricavato


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
    durate_settore = canali.get(TEMPO_SETTORE)
    settore = canali.get(SETTORE)
    carburante = canali.get(CARBURANTE)
    usato_serie = canali.get(CARBURANTE_USATO)
    set_gomme = canali.get(SET_GOMME)
    in_pit = canali.get(IN_PIT)
    valido = canali.get(GIRO_VALIDO)

    giri: list[Giro] = []
    eventi: list[Evento] = []
    scarti: list[int] = []
    senza_tempo_ufficiale = 0
    terzi_ricavati: list[int] = []
    senza_settori = 0
    consumo_da_serbatoio = False

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
        if giro.completo:
            splits, ricavato = _settori(settore, durate_settore, inizio, fine, tempo_ms)
            if ricavato:
                terzi_ricavati.append(giro.numero)
            if not splits and tempo_ms:
                senza_settori += 1

        residuo = usato = None
        if carburante is not None and carburante.size > fine - 1:
            residuo = round(float(carburante[fine - 1]), 3)
        if giro.completo:
            # Il giro finisce dove comincia il successivo: si misura fino al primo
            # campione del giro dopo, altrimenti si perde l'ultimo centesimo di giro.
            chiusura = min(fine, (usato_serie if usato_serie is not None else
                                  carburante if carburante is not None else
                                  canali[POSIZIONE]).size - 1)
            if usato_serie is not None:
                differenza = float(usato_serie[chiusura]) - float(usato_serie[inizio])
                if differenza > 0:
                    usato = round(differenza, 3)
            elif carburante is not None:
                differenza = float(carburante[inizio]) - float(carburante[chiusura])
                if differenza > 0:
                    usato = round(differenza, 3)
                    consumo_da_serbatoio = True

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
            f"{_giri(len(incompleti))} incompleti (registrazione iniziata o finita a metà "
            f"pista): contati, ma senza tempo confrontabile"
        )
    if scarti:
        assunzioni.append(
            f"giri {scarti}: il tempo ufficiale di ACC e il cronometro della "
            f"registrazione divergono di oltre mezzo secondo → si è tenuto quello di ACC"
        )
    if senza_tempo_ufficiale:
        assunzioni.append(
            f"{_giri(senza_tempo_ufficiale)} senza tempo ufficiale nella pagina grafica "
            f"(di solito l'ultimo: la registrazione finisce prima che ACC lo pubblichi) → "
            f"tempo preso dal cronometro della registrazione"
        )
    if carburante is None and usato_serie is None:
        assunzioni.append("carburante non registrato: consumo per giro non calcolabile")
    elif consumo_da_serbatoio:
        assunzioni.append(
            "consumo ricavato dal serbatoio (`fuel`), che il documento Kunos dichiara in kg "
            "mentre il gioco mostra litri: unità da verificare a schermo")
    if terzi_ricavati:
        assunzioni.append(
            f"giri {terzi_ricavati}: il terzo settore è ricavato per differenza dal tempo "
            f"sul giro (la registrazione finisce prima del traguardo successivo)")
    if senza_settori:
        assunzioni.append(
            f"{_giri(senza_settori)} senza settori leggibili (canale `lastSectorTime` assente "
            f"o settori che non sommano al tempo del giro)")
    if FRENO not in canali:
        assunzioni.append("canale del freno assente: niente punti di frenata")
    mescola, nota_mescola = _mescola(canali, metadati)
    if nota_mescola:
        assunzioni.append(nota_mescola)

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
        mescola=mescola,
        piattaforma=Piattaforma.PC,
    )
    return SessionBundle(
        meta=meta,
        giri=giri,
        carburante_fonte=(FonteCarburante.MISURATO
                          if any(g.carburante_usato_l is not None for g in giri) else None),
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

    if bundle.canali is None or bundle.meta.fonte not in (Fonte.ACC_SHARED_MEMORY, Fonte.DEMO,
                                                          Fonte.MOTEC):
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
