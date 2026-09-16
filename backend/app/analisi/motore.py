"""analisi/motore.py — il motore di analisi (L2 del rework dati).

Prende un `SessionBundle` e produce un **report di numeri**, senza LLM: statistica
elementare su dati veri, ripetibile e verificabile a mano. È il pezzo che rende Gigi
credibile — lui riceverà solo questo report, non i dati grezzi, quindi non potrà
inventare cifre: le cita.

**Spietato con metodo** (decisione 3 del 14/09). Il verdetto ordina le perdite per
gravità, ognuna con **il numero che la dimostra** e **l'azione** che la chiude. Niente
consolazione, ma nemmeno accuse senza prova: se un dato non c'è, finisce in
`dati_mancanti` invece di essere stimato. Un'analisi che indovina è peggio di
un'analisi che tace.

**Cosa si può dire con i soli risultati di ACC** (L1): ritmo, giro teorico, settori,
costanza, degrado sullo stint, giri buttati. **Cosa no:** gomme, pressioni, freni,
traiettorie e consumo affidabile — arrivano con il registratore della shared memory
(L3). Il report lo dichiara, così nessuno scambia un silenzio per un «va tutto bene».
"""

from __future__ import annotations

import statistics
from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field

from app.bundle.schema import Giro, SessionBundle

# Sotto questa soglia una statistica non significa niente: meglio dirlo.
MIN_GIRI_COSTANZA = 3
MIN_GIRI_DEGRADO = 5
# Un giro oltre il +10% sul migliore non è ritmo: è un out lap, un rientro ai box, una
# bandiera o un fuoripista. Resta nei conteggi (e nei giri buttati) ma non entra in
# medie, settori, costanza e degrado, dove falserebbe tutto. Il riferimento è il giro
# **migliore**, non la mediana: su una sessione corta la mediana è già inquinata dagli
# out lap che vorremmo togliere.
FATTORE_ANOMALO = 1.10


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Ritmo(_Base):
    """Quanto vai, e quanto andresti mettendo insieme i tuoi settori migliori."""

    giri_validi: int
    miglior_giro_ms: int | None = None
    giro_teorico_ms: int | None = None
    lasciato_sul_tavolo_ms: int | None = None
    media_ms: int | None = None
    mediana_ms: int | None = None
    media_migliori_3_ms: int | None = None


class Settore(_Base):
    numero: int
    migliore_ms: int
    media_ms: int
    deviazione_ms: int
    perdita_media_ms: int          # media − migliore: dove lasci tempo ogni giro
    perdita_sul_giro_migliore_ms: int | None = None


class Costanza(_Base):
    """Il numero che nessuno ti dice: quanto assomigli a te stesso."""

    deviazione_ms: int | None = None
    coefficiente_variazione: float | None = None
    scarto_max_ms: int | None = None
    giri_entro_mezzo_secondo: int = 0
    percentuale_entro_mezzo_secondo: float | None = None
    giudizio: str | None = None


class Degrado(_Base):
    """Come si muove il tempo sul giro con il passare dello stint."""

    calcolabile: bool = False
    pendenza_ms_giro: float | None = None
    r_quadro: float | None = None
    giri_considerati: int = 0
    perdita_su_10_giri_ms: int | None = None
    motivo: str | None = None


class Carburante(_Base):
    calcolabile: bool = False
    consumo_medio_l_giro: float | None = None
    giri_misurati: int = 0
    motivo: str | None = None


class Perdita(_Base):
    """Una voce del verdetto: cosa perdi, quanto, come si dimostra, cosa fare."""

    titolo: str
    decimi: float | None = None
    prova: str
    azione: str
    gravita: float = Field(ge=0)


class ReportAnalisi(_Base):
    car: str | None = None
    car_model_id: int | None = None
    track: str | None = None
    tipo_sessione: str
    giri_totali: int = 0
    giri_buttati: int = 0
    giri_di_ritmo: int = 0
    giri_esclusi_dal_ritmo: int = 0
    ritmo: Ritmo
    settori: list[Settore] = Field(default_factory=list)
    costanza: Costanza
    degrado: Degrado
    carburante: Carburante
    verdetto: list[Perdita] = Field(default_factory=list)
    dati_mancanti: list[str] = Field(default_factory=list)
    # Ciò che si può dire solo con i canali della shared memory (L3 · Fase 4).
    # Restano dizionari e non modelli: le loro forme vivono in `analisi/curve.py` e
    # `analisi/gomme.py`, e ricopiarle qui vorrebbe dire tenerle allineate a mano.
    curve: dict | None = None
    gomme_e_freni: dict | None = None
    ha_canali: bool = False


def _decimi(ms: float) -> float:
    return round(ms / 100.0, 1)


def _validi(bundle: SessionBundle) -> list[Giro]:
    return [g for g in bundle.giri_validi if g.tempo_ms]


def _da_ritmo(giri: Sequence[Giro]) -> list[Giro]:
    """Scarta i giri che non sono ritmo (out lap, pit, bandiere, fuoripista)."""
    tempi = [g.tempo_ms for g in giri if g.tempo_ms]
    if len(tempi) < 2:
        return list(giri)
    soglia = min(tempi) * FATTORE_ANOMALO
    puliti = [g for g in giri if g.tempo_ms and g.tempo_ms <= soglia]
    # Con meno di due giri di ritmo non resta niente da confrontare: si tiene tutto e
    # il report dichiara che non è stato possibile ripulire.
    return puliti if len(puliti) >= 2 else list(giri)


def _ritmo(giri: Sequence[Giro], settori: Sequence[Settore]) -> Ritmo:
    tempi = sorted(g.tempo_ms for g in giri if g.tempo_ms)
    if not tempi:
        return Ritmo(giri_validi=0)
    teorico = sum(s.migliore_ms for s in settori) if len(settori) == 3 else None
    # Il giro teorico non può essere più lento del migliore realmente girato: se
    # succede vuol dire che i settori non sono confrontabili, e allora si tace.
    if teorico is not None and teorico > tempi[0]:
        teorico = None
    return Ritmo(
        giri_validi=len(tempi),
        miglior_giro_ms=tempi[0],
        giro_teorico_ms=teorico,
        lasciato_sul_tavolo_ms=(tempi[0] - teorico) if teorico is not None else None,
        media_ms=round(statistics.fmean(tempi)),
        mediana_ms=round(statistics.median(tempi)),
        media_migliori_3_ms=round(statistics.fmean(tempi[:3])) if len(tempi) >= 3 else None,
    )


def _settori(giri: Sequence[Giro]) -> list[Settore]:
    completi = [g for g in giri if len(g.splits_ms) == 3]
    if len(completi) < 2:
        return []
    migliore_giro = min(completi, key=lambda g: g.tempo_ms or 10**9)
    fuori: list[Settore] = []
    for i in range(3):
        valori = [g.splits_ms[i] for g in completi]
        migliore = min(valori)
        media = statistics.fmean(valori)
        fuori.append(Settore(
            numero=i + 1,
            migliore_ms=migliore,
            media_ms=round(media),
            deviazione_ms=round(statistics.pstdev(valori)) if len(valori) > 1 else 0,
            perdita_media_ms=round(media - migliore),
            perdita_sul_giro_migliore_ms=migliore_giro.splits_ms[i] - migliore,
        ))
    return fuori


def _costanza(giri: Sequence[Giro]) -> Costanza:
    tempi = [g.tempo_ms for g in giri if g.tempo_ms]
    if len(tempi) < MIN_GIRI_COSTANZA:
        return Costanza(giudizio=f"servono almeno {MIN_GIRI_COSTANZA} giri validi")
    migliore = min(tempi)
    deviazione = statistics.pstdev(tempi)
    media = statistics.fmean(tempi)
    entro = sum(1 for t in tempi if t - migliore <= 500)
    cv = deviazione / media if media else None
    if deviazione < 300:
        giudizio = "da cronometro"
    elif deviazione < 700:
        giudizio = "solida"
    elif deviazione < 1500:
        giudizio = "ballerina: qui si perde più che nel giro secco"
    else:
        giudizio = "ogni giro è un giro diverso"
    return Costanza(
        deviazione_ms=round(deviazione),
        coefficiente_variazione=round(cv, 4) if cv is not None else None,
        scarto_max_ms=max(tempi) - migliore,
        giri_entro_mezzo_secondo=entro,
        percentuale_entro_mezzo_secondo=round(100 * entro / len(tempi), 1),
        giudizio=giudizio,
    )


def _degrado(giri: Sequence[Giro]) -> Degrado:
    tempi = [g.tempo_ms for g in giri if g.tempo_ms]
    if len(tempi) < MIN_GIRI_DEGRADO:
        return Degrado(motivo=f"servono almeno {MIN_GIRI_DEGRADO} giri di ritmo consecutivi",
                       giri_considerati=len(tempi))
    n = len(tempi)
    xs = list(range(n))
    media_x = statistics.fmean(xs)
    media_y = statistics.fmean(tempi)
    sxy = sum((x - media_x) * (y - media_y) for x, y in zip(xs, tempi))
    sxx = sum((x - media_x) ** 2 for x in xs)
    if sxx == 0:
        return Degrado(motivo="giri non ordinabili", giri_considerati=n)
    pendenza = sxy / sxx
    syy = sum((y - media_y) ** 2 for y in tempi)
    r2 = (sxy * sxy) / (sxx * syy) if syy else 0.0
    return Degrado(
        calcolabile=True,
        pendenza_ms_giro=round(pendenza, 1),
        r_quadro=round(r2, 3),
        giri_considerati=n,
        perdita_su_10_giri_ms=round(pendenza * 10),
    )


def _carburante(giri: Sequence[Giro]) -> Carburante:
    consumi = [g.carburante_usato_l for g in giri if g.carburante_usato_l is not None]
    if not consumi:
        return Carburante(motivo="i risultati di ACC non danno un residuo che cala giro "
                                 "per giro; servirà il registratore della shared memory")
    return Carburante(calcolabile=True,
                      consumo_medio_l_giro=round(statistics.fmean(consumi), 2),
                      giri_misurati=len(consumi))


def _verdetto(ritmo: Ritmo, settori: list[Settore], costanza: Costanza,
              degrado: Degrado, giri_totali: int, buttati: int) -> list[Perdita]:
    voci: list[Perdita] = []

    if ritmo.lasciato_sul_tavolo_ms and ritmo.lasciato_sul_tavolo_ms > 0:
        d = _decimi(ritmo.lasciato_sul_tavolo_ms)
        voci.append(Perdita(
            titolo="Non hai mai messo insieme il giro",
            decimi=d,
            prova=f"miglior giro {_mmss(ritmo.miglior_giro_ms)}, giro teorico "
                  f"{_mmss(ritmo.giro_teorico_ms)}: {d} decimi di differenza",
            azione="i settori li sai già fare, singolarmente: servono giri completi, "
                   "non un altro tentativo di eroismo in un punto solo",
            gravita=float(ritmo.lasciato_sul_tavolo_ms),
        ))

    if settori:
        peggiore = max(settori, key=lambda s: s.perdita_media_ms)
        if peggiore.perdita_media_ms > 0:
            d = _decimi(peggiore.perdita_media_ms)
            voci.append(Perdita(
                titolo=f"Settore {peggiore.numero}: è lì che se ne va il tempo",
                decimi=d,
                prova=f"media {_sec(peggiore.media_ms)} contro il tuo migliore "
                      f"{_sec(peggiore.migliore_ms)}: {d} decimi di media ogni giro, "
                      f"con una dispersione di {_decimi(peggiore.deviazione_ms)} decimi",
                azione=f"lavora il settore {peggiore.numero} da solo, con un riferimento "
                       f"fisso di frenata, finché la media non scende verso il tuo migliore",
                gravita=float(peggiore.perdita_media_ms) * 1.2,
            ))

    if costanza.deviazione_ms is not None and costanza.scarto_max_ms is not None:
        if costanza.deviazione_ms >= 300:
            d = _decimi(costanza.deviazione_ms)
            voci.append(Perdita(
                titolo=f"Costanza {costanza.giudizio}",
                decimi=d,
                prova=f"deviazione {d} decimi, dal migliore al peggiore "
                      f"{_decimi(costanza.scarto_max_ms)} decimi, solo "
                      f"{costanza.percentuale_entro_mezzo_secondo}% dei giri entro mezzo "
                      f"secondo dal tuo migliore",
                azione="in gara la media conta più del picco: punta a un ritmo che sai "
                       "ripetere, non al giro che ti riesce una volta su dieci",
                gravita=float(costanza.deviazione_ms) * 1.1,
            ))

    if buttati:
        quota = 100 * buttati / giri_totali if giri_totali else 0
        voci.append(Perdita(
            titolo=f"{buttati} giri su {giri_totali} buttati",
            decimi=None,
            prova=f"{quota:.0f}% dei giri non validi: tempo in pista speso per niente",
            azione="in qualifica un giro invalidato vale zero: molla il giro appena "
                   "tagli, invece di finirlo",
            gravita=200.0 * buttati,
        ))

    if degrado.calcolabile and degrado.pendenza_ms_giro and degrado.pendenza_ms_giro > 30:
        if (degrado.r_quadro or 0) >= 0.3:
            d = _decimi(degrado.perdita_su_10_giri_ms or 0)
            voci.append(Perdita(
                titolo="Il ritmo cala con lo stint",
                decimi=d,
                prova=f"{degrado.pendenza_ms_giro:.0f} ms persi ogni giro su "
                      f"{degrado.giri_considerati} giri (R² {degrado.r_quadro}): "
                      f"{d} decimi in dieci giri",
                azione="gomme o gestione: confronta la pressione a fine stint e prova a "
                       "essere più dolce in uscita nei primi giri",
                gravita=float(degrado.perdita_su_10_giri_ms or 0) * 0.8,
            ))

    voci.sort(key=lambda v: v.gravita, reverse=True)
    return voci


def _mmss(ms: int | None) -> str:
    if ms is None:
        return "—"
    minuti, resto = divmod(ms, 60_000)
    return f"{minuti}:{resto // 1000:02d}.{resto % 1000:03d}"


def _sec(ms: int | None) -> str:
    return "—" if ms is None else f"{ms / 1000:.3f}"


def _dai_canali(canali: dict) -> tuple[dict | None, dict | None, list[Perdita], list[str]]:
    """Ciò che solo la telemetria può dire: curve, gomme, freni.

    Import tardivi e di proposito: chi analizza un file di risultati non deve
    caricare numpy per niente, e il motore di L2 resta utilizzabile anche senza
    canali — che è esattamente la situazione di chi importa un file dal gioco.
    """
    from app.analisi.curve import CurveNonCalcolabili, analizza_curve
    from app.analisi.gomme import analizza_gomme_e_freni, indice_giri
    from app.analisi.curve import dividi_in_giri

    note: list[str] = []
    voci: list[Perdita] = []

    curve = None
    try:
        report_curve = analizza_curve(canali)
    except CurveNonCalcolabili as errore:
        note.append(f"analisi per curva non possibile: {errore}")
    except (KeyError, ValueError) as errore:      # canali storti: si dice, non si crolla
        note.append(f"analisi per curva fallita: {errore}")
    else:
        curve = report_curve.come_json()
        note.extend(report_curve.dati_mancanti)
        for voce in report_curve.verdetto:
            # La gravità di una curva è il tempo che costa: stessa scala delle altre
            # voci del verdetto, così l'ordinamento confronta cose confrontabili.
            perdita = next((r.perdita_media_ms for r in report_curve.riepilogo
                            if f"curva {r.curva}" in voce.titolo), 0.0)
            voci.append(Perdita(
                titolo=voce.titolo,
                decimi=_decimi(perdita) if perdita else None,
                prova=voce.prova,
                azione=voce.azione,
                gravita=float(perdita) if perdita else 80.0,
            ))

    gomme = None
    try:
        report_gomme = analizza_gomme_e_freni(
            canali, indice_giri(canali, dividi_in_giri(canali))
        )
    except (KeyError, ValueError) as errore:
        note.append(f"analisi di gomme e freni fallita: {errore}")
    else:
        gomme = report_gomme.come_json()
        note.extend(report_gomme.dati_mancanti)
        voci.extend(Perdita(titolo=v.titolo, prova=v.prova, azione=v.azione,
                            gravita=v.gravita) for v in report_gomme.voci)
    return curve, gomme, voci, note


def analizza(bundle: SessionBundle, canali: dict | None = None) -> ReportAnalisi:
    """Il report deterministico di una sessione. Nessuna rete, nessun modello.

    Con i `canali` di una registrazione (L3) il report cresce invece di cambiare: si
    aggiungono l'analisi per curva, gomme e freni, e le loro voci entrano **nello
    stesso verdetto**, ordinate per gravità insieme alle altre. Un solo elenco di
    priorità: è la differenza fra un cruscotto e un ingegnere.
    """
    tutti = [g for g in bundle.giri if g.tempo_ms]
    validi = _validi(bundle)
    ritmici = _da_ritmo(validi)

    settori = _settori(ritmici)
    ritmo = _ritmo(ritmici, settori)
    costanza = _costanza(ritmici)
    degrado = _degrado(ritmici)
    carburante = _carburante(bundle.giri)

    buttati = len([g for g in bundle.giri if not g.valido])

    mancanti = list(bundle.assunzioni)
    if bundle.setup and bundle.setup.assunzioni:
        mancanti.extend(bundle.setup.assunzioni)
    if not settori:
        mancanti.append("settori: i giri non hanno tutti e tre gli split → niente giro "
                        "teorico né analisi per settore")
    if len(validi) - len(ritmici):
        mancanti.append(
            f"{len(validi) - len(ritmici)} giri esclusi dalle statistiche di ritmo perché "
            f"oltre il +10% sul migliore (out lap, rientri, bandiere): restano contati "
            f"nei giri totali")
    if not carburante.calcolabile and carburante.motivo:
        mancanti.append(f"carburante: {carburante.motivo}")
    if not canali:
        mancanti.append("gomme, pressioni, freni e traiettorie: non sono nei risultati "
                        "di ACC → arrivano con il registratore della shared memory")
    if bundle.setup is None:
        mancanti.append("setup: nessun setup collegato a questa sessione → le correzioni "
                        "restano generiche")

    curve = gomme_e_freni = None
    voci_canali: list[Perdita] = []
    if canali:
        curve, gomme_e_freni, voci_canali, note = _dai_canali(canali)
        mancanti.extend(note)
    else:
        mancanti.append(
            "canali della shared memory non collegati a questa sessione → niente "
            "analisi per curva, gomme, freni"
        )

    verdetto = _verdetto(ritmo, settori, costanza, degrado,
                         len(tutti) or len(bundle.giri), buttati)
    verdetto.extend(voci_canali)
    verdetto.sort(key=lambda v: v.gravita, reverse=True)

    return ReportAnalisi(
        curve=curve,
        gomme_e_freni=gomme_e_freni,
        ha_canali=bool(canali),
        giri_di_ritmo=len(ritmici),
        giri_esclusi_dal_ritmo=len(validi) - len(ritmici),
        car=bundle.meta.car,
        car_model_id=bundle.meta.car_model_id,
        track=bundle.meta.track,
        tipo_sessione=bundle.meta.tipo_sessione.value,
        giri_totali=len(bundle.giri),
        giri_buttati=buttati,
        ritmo=ritmo,
        settori=settori,
        costanza=costanza,
        degrado=degrado,
        carburante=carburante,
        verdetto=verdetto,
        dati_mancanti=mancanti,
    )
