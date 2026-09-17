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
# Da qui in su la costanza è una perdita («ballerina»); sotto è un punto fermo.
SOGLIA_COSTANZA_PERDITA_MS = 700
# Sotto questa pendenza (o con una regressione che non spiega niente) il ritmo tiene.
SOGLIA_DEGRADO_MS_GIRO = 30
R_QUADRO_MINIMO = 0.3
# Teorico e reale più vicini di così: il giro è stato messo insieme.
SOGLIA_TEORICO_MS = 100


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Ritmo(_Base):
    """Quanto vai, e quanto andresti mettendo insieme i tuoi settori migliori."""

    giri_validi: int
    miglior_giro_ms: int | None = None
    miglior_giro_numero: int | None = None
    giro_teorico_ms: int | None = None
    lasciato_sul_tavolo_ms: int | None = None
    # Su quanti giri (con tutti e tre gli split) è costruito il teorico, e se non c'è,
    # perché: un campo vuoto senza motivo sembrerebbe un «tutto bene».
    giri_per_teorico: int = 0
    motivo_teorico: str | None = None
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
    dal_giro: int | None = None      # primo giro della regressione (il migliore, se si può)
    perdita_su_10_giri_ms: int | None = None
    # Il calo è dimostrato (pendenza oltre soglia E regressione che spiega i dati): lo
    # decide il motore, le schermate lo mostrano senza rifare il conto.
    significativo: bool = False
    motivo: str | None = None


class Carburante(_Base):
    calcolabile: bool = False
    consumo_medio_l_giro: float | None = None
    giri_misurati: int = 0
    motivo: str | None = None
    # «misurato» | «manuale» | «setup»: il numero non si mostra mai senza la sua fonte.
    fonte: str | None = None


class Perdita(_Base):
    """Una voce del verdetto: cosa perdi, quanto, come si dimostra, cosa fare.

    Nel verdetto entrano **solo perdite**. Ciò che funziona va in `cosa_regge`: un
    elenco di problemi che si apre con «Costanza solida» non è un elenco di problemi.
    """

    titolo: str
    decimi: float | None = None
    prova: str
    azione: str
    gravita: float = Field(ge=0)
    # "tempo" = la gravità è un tempo perso (ms); "gomme" = scala convenzionale di
    # gomme e freni, dichiarata in analisi/gomme.py. "kunos" se il giudizio poggia su
    # una soglia del documento ufficiale.
    categoria: str = "tempo"
    fonte: str = "misura"
    # Parametri del setup toccati dalla voce → variazione consigliata (None = solo la
    # direzione). Vuoto per le voci di guida.
    parametri: dict[str, float | None] = Field(default_factory=dict)


class PuntoFermo(_Base):
    """Una cosa che regge, con il numero che lo dimostra. Niente complimenti a vuoto."""

    titolo: str
    prova: str


class GiroReport(_Base):
    """Un giro come lo mostrano le schermate: tempi e stato già decisi dal motore."""

    numero: int
    tempo_ms: int | None = None
    splits_ms: list[int] = Field(default_factory=list)
    valido: bool = True
    di_ritmo: bool = False
    migliore: bool = False
    delta_migliore_ms: int | None = None
    carburante_usato_l: float | None = None
    in_pit: bool = False


class ReportAnalisi(_Base):
    car: str | None = None
    car_model_id: int | None = None
    track: str | None = None
    tipo_sessione: str
    fonte: str | None = None
    mescola: str | None = None
    giri_totali: int = 0
    giri_buttati: int = 0
    giri_di_ritmo: int = 0
    giri_esclusi_dal_ritmo: int = 0
    giri: list[GiroReport] = Field(default_factory=list)
    ritmo: Ritmo
    settori: list[Settore] = Field(default_factory=list)
    costanza: Costanza
    degrado: Degrado
    carburante: Carburante
    verdetto: list[Perdita] = Field(default_factory=list)
    cosa_regge: list[PuntoFermo] = Field(default_factory=list)
    dati_mancanti: list[str] = Field(default_factory=list)
    ha_setup: bool = False
    ha_racconto: bool = False
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
        return Ritmo(giri_validi=0, motivo_teorico="nessun giro valido con un tempo")
    migliore = min((g for g in giri if g.tempo_ms), key=lambda g: g.tempo_ms)
    completi = len([g for g in giri if len(g.splits_ms) == 3])
    teorico = sum(s.migliore_ms for s in settori) if len(settori) == 3 else None
    motivo = None
    if teorico is None:
        motivo = (f"servono almeno 2 giri di ritmo con tutti e tre gli split, "
                  f"ce ne sono {completi}")
    # Il giro teorico non può essere più lento del migliore realmente girato: se
    # succede vuol dire che i settori non sono confrontabili, e allora si tace — ma
    # dicendo perché.
    elif teorico > tempi[0]:
        motivo = (f"la somma dei settori migliori ({_mmss(teorico)}) è più lenta del giro "
                  f"migliore ({_mmss(tempi[0])}): il giro migliore non ha gli split, i "
                  f"settori non sono confrontabili")
        teorico = None
    return Ritmo(
        giri_validi=len(tempi),
        miglior_giro_ms=tempi[0],
        miglior_giro_numero=migliore.numero,
        giro_teorico_ms=teorico,
        giri_per_teorico=completi if teorico is not None else 0,
        motivo_teorico=motivo,
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
    """Il calo del ritmo **dopo** che le gomme sono entrate in temperatura.

    La regressione parte dal giro migliore: i giri prima sono quasi sempre giri di
    riscaldamento, più lenti, e una retta tirata su tutto lo stint vedrebbe una «U» e
    concluderebbe che non c'è nessun calo. Se dal migliore in poi non restano abbastanza
    giri (il migliore è verso la fine), si usa tutto lo stint e lo si dichiara.
    """
    ordinati = sorted((g for g in giri if g.tempo_ms), key=lambda g: g.numero)
    if len(ordinati) < MIN_GIRI_DEGRADO:
        return Degrado(motivo=f"servono almeno {MIN_GIRI_DEGRADO} giri di ritmo consecutivi",
                       giri_considerati=len(ordinati))
    indice_migliore = min(range(len(ordinati)), key=lambda i: ordinati[i].tempo_ms)
    dal_migliore = ordinati[indice_migliore:]
    usati = dal_migliore if len(dal_migliore) >= MIN_GIRI_DEGRADO else ordinati
    tempi = [g.tempo_ms for g in usati]
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
        dal_giro=usati[0].numero,
        perdita_su_10_giri_ms=round(pendenza * 10),
        significativo=pendenza > SOGLIA_DEGRADO_MS_GIRO and r2 >= R_QUADRO_MINIMO,
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

    # Sotto un decimo la differenza fra teorico e reale è la risoluzione dei cronometri
    # (i settori arrivano al centesimo), non un giro lasciato per strada.
    if ritmo.lasciato_sul_tavolo_ms and ritmo.lasciato_sul_tavolo_ms >= SOGLIA_TEORICO_MS:
        d = _decimi(ritmo.lasciato_sul_tavolo_ms)
        voci.append(Perdita(
            titolo="Non hai mai messo insieme il giro",
            decimi=d,
            prova=f"miglior giro {_mmss(ritmo.miglior_giro_ms)}, giro teorico "
                  f"{_mmss(ritmo.giro_teorico_ms)}: {d} decimi di differenza",
            azione="I settori li sai già fare, singolarmente: servono giri completi, "
                   "non un altro tentativo di eroismo in un punto solo.",
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
                azione=f"Lavora il settore {peggiore.numero} da solo, con un riferimento "
                       f"fisso di frenata, finché la media non scende verso il tuo migliore.",
                gravita=float(peggiore.perdita_media_ms) * 1.2,
            ))

    if costanza.deviazione_ms is not None and costanza.scarto_max_ms is not None:
        # Solo la costanza che costa entra nel verdetto: «solida» e «da cronometro»
        # vanno in `cosa_regge` (vedi `_cosa_regge`).
        if costanza.deviazione_ms >= SOGLIA_COSTANZA_PERDITA_MS:
            d = _decimi(costanza.deviazione_ms)
            voci.append(Perdita(
                titolo=f"Costanza {costanza.giudizio}",
                decimi=d,
                prova=f"deviazione {d} decimi, dal migliore al peggiore "
                      f"{_decimi(costanza.scarto_max_ms)} decimi, solo "
                      f"{costanza.percentuale_entro_mezzo_secondo}% dei giri entro mezzo "
                      f"secondo dal tuo migliore"
                      + (f"; una parte della dispersione è il ritmo che migliora "
                         f"({degrado.pendenza_ms_giro:+.0f} ms a giro)"
                         if _miglioramento_dimostrato(degrado) else ""),
                azione="In gara la media conta più del picco: punta a un ritmo che sai "
                       "ripetere, non al giro che ti riesce una volta su dieci.",
                gravita=float(costanza.deviazione_ms) * 1.1,
            ))

    if buttati:
        quota = 100 * buttati / giri_totali if giri_totali else 0
        voci.append(Perdita(
            titolo=(f"1 giro su {giri_totali} buttato" if buttati == 1
                    else f"{buttati} giri su {giri_totali} buttati"),
            decimi=None,
            prova=f"{quota:.0f}% dei giri non validi: tempo in pista speso per niente",
            azione="In qualifica un giro invalidato vale zero: molla il giro appena "
                   "tagli, invece di finirlo.",
            gravita=200.0 * buttati,
        ))

    if (degrado.calcolabile and degrado.pendenza_ms_giro
            and degrado.pendenza_ms_giro > SOGLIA_DEGRADO_MS_GIRO):
        if (degrado.r_quadro or 0) >= R_QUADRO_MINIMO:
            # Stessa scala delle altre voci di tempo: quanto costa **in media a giro**
            # sui giri misurati (pendenza × (n-1)/2), non una proiezione su dieci giri.
            media_a_giro = degrado.pendenza_ms_giro * (degrado.giri_considerati - 1) / 2
            dieci = _decimi(degrado.perdita_su_10_giri_ms or 0)
            voci.append(Perdita(
                titolo="Il ritmo cala con lo stint",
                decimi=_decimi(media_a_giro),
                prova=f"{degrado.pendenza_ms_giro:.0f} ms persi ogni giro su "
                      f"{degrado.giri_considerati} giri dal giro {degrado.dal_giro} "
                      f"(R² {degrado.r_quadro}): {_decimi(media_a_giro)} decimi a giro in "
                      f"media su questi giri, {dieci} decimi se continua per dieci",
                azione=(f"Gomme o gestione: il calo parte dal giro {degrado.dal_giro}. "
                        f"Guarda pressioni e temperature di quei giri (Telemetria, Gomme e "
                        f"freni) e, in guida, sii più progressivo in uscita per non "
                        f"consumare il posteriore."),
                gravita=round(media_a_giro, 1),
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


def _carburante_motivo(bundle: SessionBundle) -> str:
    if not bundle.giri:
        return "nessun giro nella sessione"
    if bundle.meta.fonte.value == "acc_results":
        return ("i risultati di ACC non danno un residuo che cala giro per giro; serve il "
                "registratore della shared memory")
    return "nessun giro con un consumo misurato"


def _dai_canali(canali: dict, mescola: str | None
                ) -> tuple[dict | None, dict | None, list[Perdita], list[PuntoFermo], list[str]]:
    """Ciò che solo la telemetria può dire: curve, gomme, freni.

    Import tardivi e di proposito: chi analizza un file di risultati non deve
    caricare numpy per niente, e il motore di L2 resta utilizzabile anche senza
    canali — che è esattamente la situazione di chi importa un file dal gioco.
    """
    from app.analisi.curve import CurveNonCalcolabili, analizza_curve, dividi_in_giri
    from app.analisi.gomme import analizza_gomme_e_freni

    note: list[str] = []
    voci: list[Perdita] = []
    fermi: list[PuntoFermo] = []

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
            # La gravità di una curva è il tempo che costa a giro: stessa scala delle
            # altre voci di tempo, così l'ordinamento confronta cose confrontabili.
            # Le voci derivate (frenata, v-min, coasting) spiegano il *come* di una
            # perdita già in elenco: pesano un filo meno, così vengono dopo di lei.
            perdita = voce.perdita_ms
            principale = voce.titolo.startswith("Perdi ")
            voci.append(Perdita(
                titolo=voce.titolo,
                decimi=_decimi(perdita) if perdita and principale else None,
                prova=voce.prova,
                azione=voce.azione,
                gravita=(float(perdita) * (1.0 if principale else 0.9)) if perdita else 80.0,
            ))

    gomme = None
    try:
        giri = dividi_in_giri(canali) if "graphics.normalizedCarPosition" in canali else None
        report_gomme = analizza_gomme_e_freni(canali, giri=giri, mescola=mescola)
    except (KeyError, ValueError) as errore:
        note.append(f"analisi di gomme e freni fallita: {errore}")
    else:
        gomme = report_gomme.come_json()
        note.extend(report_gomme.dati_mancanti)
        voci.extend(Perdita(titolo=v.titolo, prova=v.prova, azione=v.azione,
                            gravita=v.gravita, categoria="gomme", fonte=v.fonte,
                            parametri=dict(v.parametri))
                    for v in report_gomme.voci)
        fermi.extend(PuntoFermo(**p) for p in report_gomme.punti_fermi)
    return curve, gomme, voci, fermi, note


def _miglioramento_dimostrato(degrado: Degrado) -> bool:
    """Il tempo scende giro dopo giro, e la retta lo spiega: l'opposto del degrado."""
    return bool(degrado.calcolabile and degrado.pendenza_ms_giro is not None
                and degrado.pendenza_ms_giro < -SOGLIA_DEGRADO_MS_GIRO
                and (degrado.r_quadro or 0) >= R_QUADRO_MINIMO)


def _cosa_regge(ritmo: Ritmo, costanza: Costanza, degrado: Degrado, giri_totali: int,
                buttati: int) -> list[PuntoFermo]:
    """Ciò che funziona, dimostrato. Nessuna voce senza il suo numero."""
    fermi: list[PuntoFermo] = []
    if (ritmo.lasciato_sul_tavolo_ms is not None
            and ritmo.lasciato_sul_tavolo_ms < SOGLIA_TEORICO_MS):
        fermi.append(PuntoFermo(
            titolo="Il giro l'hai messo insieme",
            prova=(f"miglior giro {_mmss(ritmo.miglior_giro_ms)}, giro teorico "
                   f"{_mmss(ritmo.giro_teorico_ms)}: {ritmo.lasciato_sul_tavolo_ms} ms di "
                   f"differenza su {ritmo.giri_per_teorico} giri con tutti i settori"),
        ))
    degrado_dimostrato = bool(
        degrado.calcolabile and degrado.pendenza_ms_giro is not None
        and degrado.pendenza_ms_giro > SOGLIA_DEGRADO_MS_GIRO
        and (degrado.r_quadro or 0) >= R_QUADRO_MINIMO)
    # Con un calo dimostrato la dispersione dei tempi è spiegata dal calo: rivendicare
    # la costanza come punto di forza vorrebbe dire contraddire il verdetto.
    if (not degrado_dimostrato and costanza.deviazione_ms is not None
            and costanza.deviazione_ms < SOGLIA_COSTANZA_PERDITA_MS):
        fermi.append(PuntoFermo(
            titolo=f"Costanza {costanza.giudizio}",
            prova=(f"deviazione {_decimi(costanza.deviazione_ms)} decimi, "
                   f"{costanza.percentuale_entro_mezzo_secondo}% dei giri entro mezzo "
                   f"secondo dal migliore"),
        ))
    miglioramento = _miglioramento_dimostrato(degrado)
    if miglioramento:
        fermi.append(PuntoFermo(
            titolo="Il ritmo migliora giro dopo giro",
            prova=(f"{degrado.pendenza_ms_giro:+.0f} ms a giro su {degrado.giri_considerati} "
                   f"giri (R² {degrado.r_quadro})"),
        ))
    elif degrado.calcolabile and degrado.pendenza_ms_giro is not None and (
            degrado.pendenza_ms_giro <= SOGLIA_DEGRADO_MS_GIRO
            or (degrado.r_quadro or 0) < R_QUADRO_MINIMO):
        fermi.append(PuntoFermo(
            titolo="Il ritmo tiene sullo stint",
            prova=(f"{degrado.pendenza_ms_giro:+.0f} ms a giro su "
                   f"{degrado.giri_considerati} giri (R² {degrado.r_quadro}): "
                   f"nessun calo che si possa dimostrare"),
        ))
    if giri_totali >= MIN_GIRI_COSTANZA and buttati == 0:
        fermi.append(PuntoFermo(
            titolo="Nessun giro buttato",
            prova=f"{giri_totali} giri su {giri_totali} validi",
        ))
    return fermi


def _giri_report(bundle: SessionBundle, ritmici: Sequence[Giro],
                 migliore_ms: int | None) -> list[GiroReport]:
    di_ritmo = {g.numero for g in ritmici}
    return [
        GiroReport(
            numero=g.numero,
            tempo_ms=g.tempo_ms,
            splits_ms=list(g.splits_ms),
            valido=g.valido,
            di_ritmo=g.numero in di_ritmo,
            migliore=bool(g.tempo_ms and g.valido and g.tempo_ms == migliore_ms),
            delta_migliore_ms=(g.tempo_ms - migliore_ms
                               if g.tempo_ms and migliore_ms else None),
            carburante_usato_l=g.carburante_usato_l,
            in_pit=g.in_pit,
        )
        for g in sorted(bundle.giri, key=lambda g: g.numero)
    ]


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
    if not carburante.calcolabile:
        carburante.motivo = _carburante_motivo(bundle)
    elif bundle.carburante_fonte is not None:
        carburante.fonte = bundle.carburante_fonte.value
    elif bundle.meta.fonte.value in ("acc_shm", "demo"):
        # bundle scritti prima dello schema 1.2: dalla shared memory il consumo è misurato
        carburante.fonte = "misurato"

    # Buttato = un giro FINITO e invalidato. L'uscita dai box e il rientro (senza tempo,
    # perché cominciano o finiscono a metà pista) sono giri contati, non errori del pilota:
    # prima finivano qui e il verdetto diceva «1 giri su 1 buttati» su un hotlap pulito
    # (14 file MoTeC veri su 22, validazione L5 del 17/09).
    buttati = len([g for g in bundle.giri if not g.valido and g.tempo_ms])
    mescola = bundle.meta.mescola.value if bundle.meta.mescola else None

    mancanti = list(bundle.assunzioni)
    if bundle.setup and bundle.setup.assunzioni:
        mancanti.extend(bundle.setup.assunzioni)
    if not bundle.giri:
        mancanti.append("nessun giro nella sessione: niente ritmo, costanza né degrado")
    elif ritmo.giro_teorico_ms is None and ritmo.motivo_teorico:
        mancanti.append(f"settori e giro teorico non calcolabili: {ritmo.motivo_teorico}")
    if len(validi) - len(ritmici):
        mancanti.append(
            f"{len(validi) - len(ritmici)} giri esclusi dalle statistiche di ritmo perché "
            f"oltre il +10% sul migliore (out lap, rientri, bandiere): restano contati "
            f"nei giri totali")
    if bundle.giri and not carburante.calcolabile and carburante.motivo:
        mancanti.append(f"carburante: {carburante.motivo}")
    if bundle.setup is None:
        mancanti.append("setup: nessun setup collegato a questa sessione → le correzioni "
                        "restano generiche")

    curve = gomme_e_freni = None
    voci_canali: list[Perdita] = []
    fermi_canali: list[PuntoFermo] = []
    if canali:
        curve, gomme_e_freni, voci_canali, fermi_canali, note = _dai_canali(canali, mescola)
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

    cosa_regge = _cosa_regge(ritmo, costanza, degrado, len(bundle.giri), buttati) + fermi_canali

    return ReportAnalisi(
        curve=curve,
        gomme_e_freni=gomme_e_freni,
        ha_canali=bool(canali),
        giri_di_ritmo=len(ritmici),
        giri_esclusi_dal_ritmo=len(validi) - len(ritmici),
        giri=_giri_report(bundle, ritmici, ritmo.miglior_giro_ms),
        car=bundle.meta.car,
        car_model_id=bundle.meta.car_model_id,
        track=bundle.meta.track,
        tipo_sessione=bundle.meta.tipo_sessione.value,
        fonte=bundle.meta.fonte.value,
        mescola=mescola,
        giri_totali=len(bundle.giri),
        giri_buttati=buttati,
        ritmo=ritmo,
        settori=settori,
        costanza=costanza,
        degrado=degrado,
        carburante=carburante,
        verdetto=verdetto,
        cosa_regge=cosa_regge,
        dati_mancanti=mancanti,
        ha_setup=bool(bundle.setup and bundle.setup.valori),
        ha_racconto=bool(bundle.racconto and not bundle.racconto.vuoto()),
    )