"""Analisi per curva: dai canali grezzi a «dove perdi, e quanto» (L3 · Fase 3).

Il pezzo che rende possibile il verdetto spietato. Tutto deterministico, niente LLM.

Le quattro idee, in ordine:

1. **I giri si ritagliano dalla posizione sul tracciato.** `normalizedCarPosition` va da
   0 a 1 e riparte: ogni salto all'indietro è una linea del traguardo. Un giro conta
   solo se la spazzata è completa (parte vicino a 0 e arriva vicino a 1): un out lap
   entrato dai box a metà pista non è confrontabile con niente.
2. **I canali si reindicizzano sulla distanza.** Confrontare due giri nel *tempo* non
   ha senso (uno è più lento, tutto scivola); confrontarli **sulla stessa posizione in
   pista** sì. Ogni giro viene ricampionato su una griglia fissa di posizione, e da lì
   in poi «curva 4» è la stessa curva per tutti i giri.
3. **Le curve si ricavano dai dati, non da una mappa.** Decisione 4 del rework: nessun
   dato a mano per 25 circuiti. Si prende il profilo di velocità **mediano** fra i
   giri buoni, si cercano i minimi abbastanza profondi, e ogni curva diventa il tratto
   fra il massimo di velocità che la precede e quello che la segue — così i tratti si
   toccano e coprono tutto il giro: nessun decimo può sparire fra due curve.
4. **La perdita si misura per tratto.** Per ogni curva e ogni giro si calcola il tempo
   impiegato a percorrerla; il riferimento è il **miglior tempo su quel tratto** fra i
   giri del pilota. La somma dei migliori è il giro teorico *per curva*, e la
   differenza dice, curva per curva, quanti decimi restano sul tavolo e perché.

**La lunghezza del tracciato non c'è** in nessuna pagina di ACC (`trackSplineLength` è
uno dei campi che il gioco non riempie): viene stimata integrando la velocità sul giro
migliore. È dichiarata come stima, e serve solo a esprimere le posizioni in metri —
nessun conto dipende dalla sua esattezza.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Any

import numpy as np

# Canali indispensabili: senza questi non si analizza niente.
POSIZIONE = "graphics.normalizedCarPosition"
TEMPO = "pitwall.tempo_ms"
VELOCITA = "physics.speedKmh"
FRENO = "physics.brake"
GAS = "physics.gas"
STERZO = "physics.steerAngle"
MARCIA = "physics.gear"
GIRI_COMPLETATI = "graphics.completedLaps"
GIRO_VALIDO = "graphics.isValidLap"
IN_PIT = "graphics.isInPitLane"

PUNTI_GRIGLIA = 2000          # ~2,5 m di risoluzione su un tracciato da 5 km
PROFONDITA_MINIMA_KMH = 15.0  # quanto deve scendere la velocità perché sia una curva
DISTANZA_MINIMA_FRA_CURVE = 0.012   # 1,2% del giro
SOGLIA_FRENO = 0.05
SOGLIA_GAS = 0.20


class CurveNonCalcolabili(ValueError):
    """Mancano i canali o i giri per dire qualcosa di vero."""


@dataclass
class GiroCanali:
    """Un giro ritagliato dai campioni."""

    numero: int
    inizio: int
    fine: int                 # estremo escluso
    tempo_ms: int | None
    completo: bool
    valido: bool
    ai_box: bool

    @property
    def campioni(self) -> int:
        return self.fine - self.inizio


@dataclass
class Curva:
    """Una curva ricavata dal profilo di velocità."""

    numero: int
    ingresso: float           # posizione normalizzata 0-1
    apice: float
    uscita: float
    velocita_minima_riferimento: float
    ingresso_m: float | None = None
    apice_m: float | None = None
    uscita_m: float | None = None


@dataclass
class CurvaGiro:
    """Come è andata una curva in un giro."""

    curva: int
    giro: int
    tempo_ms: float
    perdita_ms: float
    velocita_minima: float
    posizione_vmin: float
    punto_di_frenata: float | None
    punto_di_frenata_m: float | None
    riapertura_gas: float | None
    trail_braking: float      # quota del tratto con freno e gas insieme
    coasting: float           # quota del tratto senza né freno né gas


@dataclass
class RiepilogoCurva:
    """Il giudizio su una curva, su tutti i giri."""

    curva: int
    tempo_migliore_ms: float
    tempo_medio_ms: float
    perdita_media_ms: float
    perdita_totale_ms: float
    dispersione_frenata: float | None     # deviazione standard, in metri se nota
    dispersione_vmin: float               # deviazione standard della v-min, km/h
    velocita_minima_migliore: float
    velocita_minima_media: float
    giri_considerati: int


@dataclass
class VoceVerdetto:
    gravita: int
    titolo: str
    prova: str
    azione: str


@dataclass
class ReportCurve:
    giri: list[GiroCanali]
    curve: list[Curva]
    dettaglio: list[CurvaGiro]
    riepilogo: list[RiepilogoCurva]
    verdetto: list[VoceVerdetto]
    giro_di_riferimento: int | None
    perdita_totale_ms: float
    lunghezza_stimata_m: float | None
    dati_mancanti: list[str] = field(default_factory=list)

    def come_json(self) -> dict[str, Any]:
        return {
            "giri": [asdict(g) for g in self.giri],
            "curve": [asdict(c) for c in self.curve],
            "riepilogo": [asdict(r) for r in self.riepilogo],
            "dettaglio": [asdict(d) for d in self.dettaglio],
            "verdetto": [asdict(v) for v in self.verdetto],
            "giro_di_riferimento": self.giro_di_riferimento,
            "perdita_totale_ms": self.perdita_totale_ms,
            "lunghezza_stimata_m": self.lunghezza_stimata_m,
            "dati_mancanti": self.dati_mancanti,
        }


# ── 1 · i giri ──────────────────────────────────────────────────────────────


def dividi_in_giri(canali: dict[str, np.ndarray]) -> list[GiroCanali]:
    """Ritaglia i giri guardando dove la posizione sul tracciato torna indietro."""
    posizione = np.asarray(canali[POSIZIONE], dtype=np.float64)
    if posizione.size < 2:
        return []
    tempo = canali.get(TEMPO)
    valido = canali.get(GIRO_VALIDO)
    ai_box = canali.get(IN_PIT)

    # Un salto all'indietro «grosso» è la linea del traguardo; uno piccolo è rumore.
    tagli = np.flatnonzero(np.diff(posizione) < -0.5) + 1
    confini = [0, *tagli.tolist(), posizione.size]

    giri: list[GiroCanali] = []
    for numero, (inizio, fine) in enumerate(zip(confini, confini[1:]), start=1):
        if fine - inizio < 10:
            continue
        pezzo = posizione[inizio:fine]
        completo = bool(pezzo.min() < 0.05 and pezzo.max() > 0.95)
        tempo_ms = None
        if tempo is not None:
            tempo_ms = int(round(float(tempo[fine - 1]) - float(tempo[inizio])))
        giri.append(GiroCanali(
            numero=numero,
            inizio=int(inizio),
            fine=int(fine),
            tempo_ms=tempo_ms,
            completo=completo,
            valido=bool(valido[inizio:fine].min() > 0) if valido is not None else True,
            ai_box=bool(ai_box[inizio:fine].max() > 0) if ai_box is not None else False,
        ))
    return giri


# ── 2 · la griglia sulla distanza ───────────────────────────────────────────


def griglia(punti: int = PUNTI_GRIGLIA) -> np.ndarray:
    return np.linspace(0.0, 1.0, punti, endpoint=False)


def su_distanza(
    canali: dict[str, np.ndarray],
    giro: GiroCanali,
    nomi: list[str],
    punti: int = PUNTI_GRIGLIA,
) -> dict[str, np.ndarray]:
    """Ricampiona i canali di un giro sulla griglia di posizione.

    I campioni con posizione non crescente (auto ferma, rumore) vengono tolti: a
    `np.interp` serve un'ascissa monotona, e un campione fuori ordine sposterebbe un
    valore su una posizione in cui la macchina non era.
    """
    posizione = np.asarray(canali[POSIZIONE][giro.inizio:giro.fine], dtype=np.float64)
    tieni = np.concatenate(([True], np.diff(posizione) > 0))
    posizione = posizione[tieni]
    if posizione.size < 10:
        raise CurveNonCalcolabili(f"giro {giro.numero}: troppi pochi campioni utili")

    x = griglia(punti)
    fuori: dict[str, np.ndarray] = {}
    for nome in nomi:
        serie = canali.get(nome)
        if serie is None:
            continue
        valori = np.asarray(serie[giro.inizio:giro.fine], dtype=np.float64)[tieni]
        fuori[nome] = np.interp(x, posizione, valori)
    return fuori


def lunghezza_stimata(profilo: dict[str, np.ndarray], tempo_ms: int | None) -> float | None:
    """Lunghezza del tracciato, integrando la velocità sul giro.

    ACC non la pubblica: `trackSplineLength` è fra i campi che il gioco non riempie.
    Serve solo per esprimere le posizioni in metri.
    """
    velocita = profilo.get(VELOCITA)
    if velocita is None or tempo_ms is None or tempo_ms <= 0:
        return None
    media_ms = float(np.mean(velocita)) / 3.6      # m/s medi sulla griglia di posizione
    if not math.isfinite(media_ms) or media_ms <= 0:
        return None
    # Attenzione: la media sulla *posizione* non è la media sul tempo. La lunghezza si
    # ricava meglio dal tempo sul giro e dalla velocità media *temporale*, che qui si
    # ottiene pesando ogni tratto per il tempo che ci si impiega.
    pesi = 1.0 / np.maximum(velocita / 3.6, 0.5)
    quota = pesi / float(np.sum(pesi))
    velocita_media_temporale = float(np.sum((velocita / 3.6) * quota))
    return velocita_media_temporale * (tempo_ms / 1000.0)


# ── 3 · le curve ────────────────────────────────────────────────────────────


def _liscia(serie: np.ndarray, finestra: int) -> np.ndarray:
    """Media mobile circolare: il giro è un anello, non un segmento."""
    if finestra < 3:
        return serie
    nucleo = np.ones(finestra) / finestra
    esteso = np.concatenate([serie[-finestra:], serie, serie[:finestra]])
    lisciato = np.convolve(esteso, nucleo, mode="same")
    return lisciato[finestra:-finestra]


def _minimi_locali(serie: np.ndarray) -> list[int]:
    """Gli indici dei minimi, contando **una volta sola** i fondi piatti.

    Un curvone percorso a velocità costante ha decine di campioni tutti uguali: senza
    questo accorpamento diventerebbero decine di curve, o (peggio) nessuna.
    """
    punti = serie.size
    minimi: list[int] = []
    i = 0
    while i < punti:
        precedente = serie[(i - 1) % punti]
        # quanto dura il tratto piatto che comincia qui
        fine = i
        while fine + 1 < punti and serie[fine + 1] == serie[i]:
            fine += 1
        successivo = serie[(fine + 1) % punti]
        if precedente > serie[i] and successivo > serie[i]:
            minimi.append((i + fine) // 2)
        i = fine + 1
    return minimi


def _profondita(serie: np.ndarray, indice: int, obiettivo: float) -> float:
    """Di quanto risale il profilo ai due lati del minimo, prima di riscendere.

    È la «prominenza» del minimo: si cammina a destra e a sinistra (il giro è un
    anello) finché non si supera il valore di partenza di `obiettivo`, tenendo il
    massimo incontrato. Camminare invece di guardare una finestra fissa è ciò che
    permette di riconoscere anche le curve lunghe a velocità costante.
    """
    punti = serie.size
    valore = float(serie[indice])
    limite = punti // 2
    massimi = []
    for passo in (-1, 1):
        massimo = valore
        for k in range(1, limite + 1):
            corrente = float(serie[(indice + passo * k) % punti])
            if corrente < valore:
                break                      # c'è un minimo più profondo: ci pensa lui
            massimo = max(massimo, corrente)
            if massimo - valore >= obiettivo:
                break
        massimi.append(massimo)
    return min(massimi) - valore


def trova_curve(
    velocita_mediana: np.ndarray,
    profondita_minima: float = PROFONDITA_MINIMA_KMH,
    distanza_minima: float = DISTANZA_MINIMA_FRA_CURVE,
) -> list[Curva]:
    """Le curve sono i minimi abbastanza profondi del profilo di velocità."""
    punti = velocita_mediana.size
    lisciata = _liscia(velocita_mediana, max(3, punti // 200))
    finestra = max(3, int(punti * distanza_minima))

    candidati: list[int] = []
    for i in _minimi_locali(lisciata):
        if _profondita(lisciata, i, profondita_minima) >= profondita_minima:
            candidati.append(i)

    # minimi appiattiti: più indici con lo stesso valore, se ne tiene uno
    scelti: list[int] = []
    for i in candidati:
        if scelti and (i - scelti[-1]) < finestra:
            if lisciata[i] < lisciata[scelti[-1]]:
                scelti[-1] = i
            continue
        scelti.append(i)
    if len(scelti) > 1 and (scelti[0] + punti - scelti[-1]) < finestra:
        # primo e ultimo sono la stessa curva a cavallo del traguardo
        if lisciata[scelti[0]] < lisciata[scelti[-1]]:
            scelti.pop()
        else:
            scelti.pop(0)

    curve: list[Curva] = []
    for numero, apice in enumerate(scelti, start=1):
        precedente = scelti[numero - 2] if numero > 1 else scelti[-1] - punti
        successivo = scelti[numero] if numero < len(scelti) else scelti[0] + punti
        # ingresso e uscita: i massimi di velocità fra una curva e l'altra
        sinistra = range(precedente, apice + 1)
        destra = range(apice, successivo + 1)
        ingresso = (precedente + int(np.argmax(np.take(lisciata, sinistra, mode="wrap")))) % punti
        uscita = (apice + int(np.argmax(np.take(lisciata, destra, mode="wrap")))) % punti
        curve.append(Curva(
            numero=numero,
            ingresso=ingresso / punti,
            apice=apice / punti,
            uscita=uscita / punti,
            velocita_minima_riferimento=float(lisciata[apice]),
        ))
    return curve


# ── 4 · l'analisi ───────────────────────────────────────────────────────────


def _indici(curva: Curva, punti: int) -> tuple[int, int, int]:
    return (int(curva.ingresso * punti), int(curva.apice * punti),
            int(curva.uscita * punti))


def _tratto(inizio: int, fine: int, punti: int) -> np.ndarray:
    """Gli indici di un tratto, anche quando scavalca il traguardo."""
    if fine >= inizio:
        return np.arange(inizio, fine + 1)
    return np.concatenate([np.arange(inizio, punti), np.arange(0, fine + 1)])


def analizza_curve(
    canali: dict[str, np.ndarray], punti: int = PUNTI_GRIGLIA
) -> ReportCurve:
    """Il report per curva di una sessione registrata."""
    mancanti = [c for c in (POSIZIONE, VELOCITA, TEMPO) if c not in canali]
    if mancanti:
        raise CurveNonCalcolabili(f"canali mancanti: {mancanti}")

    dati_mancanti: list[str] = []
    for nome, nota in ((FRENO, "freno"), (GAS, "gas")):
        if nome not in canali:
            dati_mancanti.append(f"canale «{nota}» assente: le sue misure non ci sono")

    giri = dividi_in_giri(canali)
    buoni = [g for g in giri if g.completo and not g.ai_box and g.tempo_ms]
    if len(buoni) < 2:
        raise CurveNonCalcolabili(
            f"servono almeno 2 giri completi, ce ne sono {len(buoni)}"
        )

    nomi = [n for n in (VELOCITA, FRENO, GAS, STERZO, MARCIA, TEMPO) if n in canali]
    profili = {g.numero: su_distanza(canali, g, nomi, punti) for g in buoni}

    # Il profilo di riferimento è la MEDIANA fra i giri: un singolo giro storto (un
    # lungo, un traffico) sposterebbe le curve di tutta la sessione.
    velocita_mediana = np.median(
        np.vstack([profili[g.numero][VELOCITA] for g in buoni]), axis=0
    )
    curve = trova_curve(velocita_mediana)
    if not curve:
        raise CurveNonCalcolabili(
            "nessuna curva riconosciuta: il profilo di velocità è troppo piatto"
        )

    piu_veloce = min(buoni, key=lambda g: g.tempo_ms or 10**9)
    lunghezza = lunghezza_stimata(profili[piu_veloce.numero], piu_veloce.tempo_ms)
    if lunghezza:
        for curva in curve:
            curva.ingresso_m = round(curva.ingresso * lunghezza, 1)
            curva.apice_m = round(curva.apice * lunghezza, 1)
            curva.uscita_m = round(curva.uscita * lunghezza, 1)
    else:
        dati_mancanti.append(
            "lunghezza del tracciato non stimabile: le posizioni restano in quota di giro"
        )

    # tempi per tratto, giro per giro
    dettaglio: list[CurvaGiro] = []
    tempi: dict[int, dict[int, float]] = {c.numero: {} for c in curve}
    for giro in buoni:
        profilo = profili[giro.numero]
        tempo = profilo[TEMPO]
        for curva in curve:
            i_ing, _i_ap, i_usc = _indici(curva, punti)
            tratto = _tratto(i_ing, i_usc, punti)
            durata = float(tempo[tratto[-1]] - tempo[tratto[0]])
            if durata < 0:      # il tratto scavalca il traguardo
                durata += float(giro.tempo_ms or 0)
            tempi[curva.numero][giro.numero] = durata

            velocita = profilo[VELOCITA][tratto]
            indice_vmin = int(np.argmin(velocita))
            freno = profilo[FRENO][tratto] if FRENO in profilo else None
            gas = profilo[GAS][tratto] if GAS in profilo else None

            frenata = None
            if freno is not None:
                sopra = np.flatnonzero(freno[: indice_vmin + 1] > SOGLIA_FRENO)
                if sopra.size:
                    frenata = float(tratto[int(sopra[0])] % punti) / punti

            riapertura = None
            if gas is not None:
                sopra = np.flatnonzero(gas[indice_vmin:] > SOGLIA_GAS)
                if sopra.size:
                    riapertura = float(tratto[indice_vmin + int(sopra[0])] % punti) / punti

            insieme = quiete = 0.0
            if freno is not None and gas is not None:
                insieme = float(np.mean((freno > SOGLIA_FRENO) & (gas > SOGLIA_GAS)))
                quiete = float(np.mean((freno <= SOGLIA_FRENO) & (gas <= SOGLIA_GAS)))

            dettaglio.append(CurvaGiro(
                curva=curva.numero, giro=giro.numero,
                tempo_ms=round(durata, 1), perdita_ms=0.0,
                velocita_minima=round(float(velocita[indice_vmin]), 2),
                posizione_vmin=float(tratto[indice_vmin] % punti) / punti,
                punto_di_frenata=frenata,
                punto_di_frenata_m=(round(frenata * lunghezza, 1)
                                    if frenata is not None and lunghezza else None),
                riapertura_gas=riapertura,
                trail_braking=round(insieme, 4),
                coasting=round(quiete, 4),
            ))

    # perdita: rispetto al miglior tempo su QUEL tratto
    migliori = {n: min(v.values()) for n, v in tempi.items()}
    for voce in dettaglio:
        voce.perdita_ms = round(voce.tempo_ms - migliori[voce.curva], 1)

    riepilogo: list[RiepilogoCurva] = []
    for curva in curve:
        voci = [d for d in dettaglio if d.curva == curva.numero]
        durate = np.array([d.tempo_ms for d in voci])
        vmin = np.array([d.velocita_minima for d in voci])
        frenate = [d.punto_di_frenata for d in voci if d.punto_di_frenata is not None]
        dispersione_frenata = None
        if len(frenate) >= 2:
            dispersione = float(np.std(frenate))
            dispersione_frenata = round(
                dispersione * lunghezza if lunghezza else dispersione, 2
            )
        riepilogo.append(RiepilogoCurva(
            curva=curva.numero,
            tempo_migliore_ms=round(float(durate.min()), 1),
            tempo_medio_ms=round(float(durate.mean()), 1),
            perdita_media_ms=round(float(durate.mean() - durate.min()), 1),
            perdita_totale_ms=round(float(durate.sum() - durate.min() * durate.size), 1),
            dispersione_frenata=dispersione_frenata,
            dispersione_vmin=round(float(np.std(vmin)), 2),
            velocita_minima_migliore=round(float(vmin.max()), 2),
            velocita_minima_media=round(float(vmin.mean()), 2),
            giri_considerati=len(voci),
        ))

    verdetto = _verdetto(riepilogo, dettaglio, curve, lunghezza)
    return ReportCurve(
        giri=giri,
        curve=curve,
        dettaglio=dettaglio,
        riepilogo=riepilogo,
        verdetto=verdetto,
        giro_di_riferimento=piu_veloce.numero,
        perdita_totale_ms=round(sum(r.perdita_media_ms for r in riepilogo), 1),
        lunghezza_stimata_m=round(lunghezza, 1) if lunghezza else None,
        dati_mancanti=dati_mancanti,
    )


def _verdetto(
    riepilogo: list[RiepilogoCurva],
    dettaglio: list[CurvaGiro],
    curve: list[Curva],
    lunghezza: float | None,
) -> list[VoceVerdetto]:
    """Le perdite ordinate per gravità, ognuna col numero che la prova.

    Decisione 3 del rework: numeri nudi, zero consolazione, **sempre** con l'azione
    correttiva attaccata. Una voce senza azione qui non ci entra.
    """
    voci: list[VoceVerdetto] = []
    per_numero = {c.numero: c for c in curve}

    for riga in sorted(riepilogo, key=lambda r: r.perdita_media_ms, reverse=True):
        if riga.perdita_media_ms < 30:      # sotto i tre centesimi non è un problema
            continue
        curva = per_numero[riga.curva]
        dove = (f"curva {riga.curva} (apice al metro {curva.apice_m:.0f})"
                if curva.apice_m else f"curva {riga.curva}")
        voci.append(VoceVerdetto(
            gravita=len(voci) + 1,
            titolo=f"Perdi {riga.perdita_media_ms/1000:.2f} s a giro in {dove}",
            prova=(f"tempo migliore sul tratto {riga.tempo_migliore_ms/1000:.3f} s, "
                   f"medio {riga.tempo_medio_ms/1000:.3f} s "
                   f"su {riga.giri_considerati} giri"),
            azione=("Rifai il tuo giro migliore in questa curva: la differenza è tua, "
                    "non della macchina."),
        ))

    # costanza del punto di frenata
    for riga in sorted(
        (r for r in riepilogo if r.dispersione_frenata is not None),
        key=lambda r: r.dispersione_frenata or 0.0, reverse=True,
    )[:2]:
        soglia = 8.0 if lunghezza else 0.002
        if (riga.dispersione_frenata or 0) < soglia:
            continue
        unita = "m" if lunghezza else "di giro"
        voci.append(VoceVerdetto(
            gravita=len(voci) + 1,
            titolo=f"Frenata ballerina in curva {riga.curva}",
            prova=(f"il punto di frenata varia di {riga.dispersione_frenata} {unita} "
                   f"(deviazione standard su {riga.giri_considerati} giri)"),
            azione=("Scegli un riferimento fisso a bordo pista e frena sempre lì: "
                    "prima la ripetibilità, poi il ritardo della staccata."),
        ))

    # v-min: dove si perde velocità in mezzo alla curva
    for riga in sorted(riepilogo, key=lambda r: r.dispersione_vmin, reverse=True)[:1]:
        if riga.dispersione_vmin < 3.0:
            continue
        voci.append(VoceVerdetto(
            gravita=len(voci) + 1,
            titolo=f"Velocità minima incostante in curva {riga.curva}",
            prova=(f"v-min fra {riga.velocita_minima_media:.1f} km/h di media e "
                   f"{riga.velocita_minima_migliore:.1f} km/h nel giro migliore, "
                   f"deviazione {riga.dispersione_vmin:.1f} km/h"),
            azione=("Guarda l'ingresso: se la v-min cambia così tanto, stai variando "
                    "il punto di rilascio del freno."),
        ))

    # coasting: tempo speso senza né freno né gas
    peggiore = max(
        (d for d in dettaglio), key=lambda d: d.coasting, default=None
    )
    if peggiore is not None and peggiore.coasting > 0.25:
        voci.append(VoceVerdetto(
            gravita=len(voci) + 1,
            titolo=f"Troppo tempo in folle in curva {peggiore.curva}",
            prova=(f"nel giro {peggiore.giro} il {peggiore.coasting*100:.0f}% del tratto "
                   f"è senza freno e senza gas"),
            azione=("Passa dal freno al gas senza pause: il coasting è tempo regalato, "
                    "non stabilità."),
        ))
    return voci
