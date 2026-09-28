"""Le curve di un giro lette come le legge un pilota: inizio, apice, uscita.

Il motore (`curve.py`) vede solo i minimi di velocità. Per mettere le curve della guida
sul giro serve di più, e la telemetria MoTeC di ACC lo ha: il **freno** e
l'**accelerazione laterale** (`motec.G_LAT`).

Le fasi di una curva sono quelle standard (Driver61, «The 6 phases of a corner»):
frenata in rettilineo → inserimento → apice → uscita. Per l'ancora conta dove la curva
**comincia** (decisione di Edoardo del 28/09/2026, dopo il primo provino): nelle curve
con staccata è il **punto di frenata**, in quelle in pieno è l'**inserimento**, dove il
carico laterale sale. Apice e uscita vengono dopo, e si calcolano.

Il metodo segue quello documentato di assetto-mcp (docs/INTERNALS.md e PR #56):

1. **Le curve dal carico laterale**, non dai minimi di velocità: un curvone in pieno
   quasi non tocca la velocità ma carica la macchina di lato. Una curva è un tratto
   sopra la soglia girando da una parte sola; due tratti dello stesso senso restano
   **una curva** se fra loro il carico non scende sotto il 70% della soglia (la
   macchina non si è mai raddrizzata). Inserimento e uscita sono dove il carico passa
   la soglia la prima e l'ultima volta.
2. **La frenata si attribuisce camminando all'indietro** dall'apice fino all'uscita
   della curva precedente: ogni tratto di freno pesa per la velocità che ha tolto, e il
   punto di frenata è l'inizio del **primo** tratto che ha tolto almeno un quarto di
   quello più pesante. Così un tocco di pedale a metà rettilineo non diventa una
   staccata, e una staccata lunga non finisce attribuita alla curva sbagliata — che era
   l'errore del primo provino (a Monza e Zandvoort le grandi staccate venivano confuse).
3. **Due frenate nello stesso tratto di carico** sono due curve dello stesso senso
   attaccate: il tratto si divide nel punto più veloce fra i due minimi.

Il segno del carico dice il senso. Kunos non lo documenta; è verificato sui dati di
Monza, Zandvoort e Spa con curve dal senso indiscusso (Tarzan, La Source, Raidillon,
Parabolica a destra, Eau Rouge a sinistra): **G_LAT negativo = curva a destra**.

`proponi` abbina in ordine le curve della guida a quelle del giro (è una proposta per
il provino, non un verdetto); `verifica` riporta le ancore di una sessione su un'altra
della stessa pista.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np

from app.analisi.curve import (
    FRENO,
    GAS,
    MARCIA,
    PUNTI_GRIGLIA,
    VELOCITA,
    CurveNonCalcolabili,
    GiroCanali,
    _liscia,
    dividi_in_giri,
    su_distanza,
    trova_curve,
)

G_LAT = "motec.G_LAT"
SEGNO_DESTRA = -1          # G_LAT < 0 = curva a destra (verificato, vedi sopra)

TOLLERANZA = 0.01          # ±1% di giro per la verifica fra sessioni (decisa da Edoardo il 28/09)
SOGLIA_LOBO = 0.30         # la «soglia»: quota del carico laterale pieno sopra cui si è in curva
SOGLIA_PICCO = 0.40        # una curva conta se il suo picco arriva almeno qui
CONTINUITA = 0.70          # due tratti dello stesso senso si uniscono sopra il 70% della soglia
QUOTA_FRENATA = 0.25       # una frenata conta se toglie almeno 1/4 della più pesante
SOGLIA_FRENO = 0.05
LISCIATURA = 15            # punti di griglia (~0,75% di giro): toglie il rumore dei cordoli


@dataclass
class Evento:
    """Una curva del giro, con le sue fasi (posizioni 0-1)."""

    inizio: float              # punto di frenata, o inserimento se la curva è in pieno
    frenata: float | None      # inizio della staccata attribuita a questa curva
    inserimento: float         # dove il carico laterale supera la soglia
    apice: float               # minimo di velocità, o picco di carico se il minimo non c'è
    uscita: float              # dove il carico laterale torna sotto la soglia
    segno: int                 # +1 sinistra, -1 destra, 0 non noto
    picco_g: float             # carico laterale al picco, con segno
    posizione_picco: float | None
    minimo: bool               # c'è un minimo di velocità del motore dentro
    velocita_apice: float      # km/h
    velocita_frenata: float | None   # km/h all'inizio della staccata

    @property
    def direzione(self) -> str | None:
        if self.segno == 0:
            return None
        return "destra" if self.segno == SEGNO_DESTRA else "sinistra"

    @property
    def metodo_inizio(self) -> str:
        return "frenata" if self.frenata is not None else "inserimento"

    @property
    def metodo_apice(self) -> str:
        return "minimo" if self.minimo else "picco_g_lat"


def direzione_da_g(g: float) -> str | None:
    if g == 0:
        return None
    return "destra" if np.sign(g) == SEGNO_DESTRA else "sinistra"


# ── il giro ─────────────────────────────────────────────────────────────────


def giro_migliore(canali: dict[str, np.ndarray]) -> GiroCanali:
    """Il giro completo più veloce fuori dai box: è quello su cui si ancora."""
    giri = [g for g in dividi_in_giri(canali) if g.completo and not g.ai_box and g.tempo_ms]
    if not giri:
        raise CurveNonCalcolabili("nessun giro completo fuori dai box")
    return min(giri, key=lambda g: g.tempo_ms or 10**9)


def profilo(canali: dict[str, np.ndarray], giro: GiroCanali,
            punti: int = PUNTI_GRIGLIA) -> dict[str, Any]:
    """Il giro sulla griglia di posizione, con i canali che servono al provino."""
    nomi = [n for n in (VELOCITA, FRENO, GAS, MARCIA, G_LAT) if n in canali]
    serie = su_distanza(canali, giro, nomi, punti)
    if VELOCITA not in serie:
        raise CurveNonCalcolabili("manca la velocità")
    return {
        "punti": punti,
        "giro": giro.numero,
        "tempo_ms": giro.tempo_ms,
        "serie": serie,
        "curve_motore": trova_curve(serie[VELOCITA]),
    }


def g_lisciato(prof: dict[str, Any]) -> tuple[np.ndarray | None, float]:
    """Il carico laterale lisciato e la sua scala (98° percentile del modulo)."""
    g = prof["serie"].get(G_LAT)
    if g is None:
        return None, 1.0
    liscio = _liscia(np.asarray(g, dtype=np.float64), LISCIATURA)
    return liscio, float(np.percentile(np.abs(liscio), 98)) or 1.0


# ── le curve ────────────────────────────────────────────────────────────────


def _lobi(g: np.ndarray, scala: float) -> list[tuple[int, int, int]]:
    """Tratti sopra la soglia girando da una parte: (inserimento, uscita, picco)."""
    punti = g.size
    soglia = SOGLIA_LOBO * scala
    segni = np.sign(g) * (np.abs(g) >= soglia)
    lobi: list[list[int]] = []
    i = 0
    while i < punti:
        if segni[i] == 0:
            i += 1
            continue
        j = i
        while j + 1 < punti and segni[j + 1] == segni[i]:
            j += 1
        lobi.append([i, j])
        i = j + 1
    # stesso senso e la macchina non si è mai raddrizzata (il carico fra i due tratti
    # resta sopra il 70% della soglia, dalla stessa parte): è la stessa curva
    uniti: list[list[int]] = []
    for lobo in lobi:
        if uniti and np.sign(g[uniti[-1][0]]) == np.sign(g[lobo[0]]):
            fra = g[uniti[-1][1] + 1:lobo[0]] * np.sign(g[lobo[0]])
            if fra.size == 0 or float(fra.min()) >= CONTINUITA * soglia:
                uniti[-1][1] = lobo[1]
                continue
        uniti.append(lobo)
    fuori = []
    for inizio, fine in uniti:
        picco = inizio + int(np.argmax(np.abs(g[inizio:fine + 1])))
        if abs(g[picco]) >= SOGLIA_PICCO * scala and fine - inizio >= 2:
            fuori.append((inizio, fine, picco))
    return fuori


def _tratti_di_freno(freno: np.ndarray, da: int, a: int) -> list[tuple[int, int]]:
    """I tratti continui di freno premuto fra `da` e `a` (indici su un anello)."""
    punti = freno.size
    tratti: list[tuple[int, int]] = []
    k = da
    while k <= a:
        if freno[k % punti] > SOGLIA_FRENO:
            j = k
            while j + 1 <= a and freno[(j + 1) % punti] > SOGLIA_FRENO:
                j += 1
            tratti.append((k, j))
            k = j + 1
        else:
            k += 1
    return tratti


def punto_di_frenata(velocita: np.ndarray, freno: np.ndarray | None,
                     da: int, apice: int) -> int | None:
    """Dove comincia la staccata di una curva (indice), o None se non si frena.

    Si guarda solo fra l'uscita della curva precedente (`da`) e l'apice: ogni tratto di
    freno pesa per la velocità che ha tolto, e vince il PRIMO tratto che ha tolto almeno
    un quarto di quello più pesante (assetto-mcp, PR #56).
    """
    if freno is None or apice <= da:
        return None
    punti = velocita.size
    tratti = _tratti_di_freno(freno, da, apice)
    if not tratti:
        return None
    pesi = [max(0.0, float(velocita[s % punti] - velocita[e % punti])) for s, e in tratti]
    massimo = max(pesi)
    if massimo <= 0:
        return None
    for (s, _e), peso in zip(tratti, pesi):
        if peso >= QUOTA_FRENATA * massimo:
            return s
    return None


def trova_eventi(prof: dict[str, Any]) -> list[Evento]:
    """Le curve del giro, in ordine, con inizio, apice e uscita."""
    punti = prof["punti"]
    serie = prof["serie"]
    velocita = np.asarray(serie[VELOCITA], dtype=np.float64)
    freno = serie.get(FRENO)
    minimi = sorted(int(round(c.apice * punti)) % punti for c in prof["curve_motore"])
    g, scala = g_lisciato(prof)

    # (inserimento, uscita, apice, segno, picco) come indici sulla griglia
    grezzi: list[tuple[int, int, int, int, int, bool]] = []
    usati: set[int] = set()
    if g is not None:
        for inizio, fine, _picco in _lobi(g, scala):
            dentro = [m for m in minimi if inizio <= m <= fine]
            usati.update(dentro)
            tagli = [inizio]
            for m1, m2 in zip(dentro, dentro[1:]):
                tagli.append(m1 + int(np.argmax(velocita[m1:m2 + 1])))
            tagli.append(fine)
            pezzi = list(zip(tagli, tagli[1:])) if dentro else [(inizio, fine)]
            for k, (da, a) in enumerate(pezzi):
                picco = da + int(np.argmax(np.abs(g[da:a + 1])))
                apice = dentro[k] if dentro else picco
                grezzi.append((da, a, apice, int(np.sign(g[picco])), picco, bool(dentro)))
    # i minimi fuori da ogni tratto di carico (o tutti, se il canale manca): curve senza senso
    for m in minimi:
        if m not in usati:
            grezzi.append((m, m, m, 0, -1, True))
    grezzi.sort(key=lambda r: r[2])

    eventi: list[Evento] = []
    for i, (ins, usc, apice, segno, picco, minimo) in enumerate(grezzi):
        # si cammina all'indietro fino all'uscita della curva precedente (sull'anello:
        # per la prima curva, l'ultima del giro prima del traguardo)
        if i > 0:
            da = grezzi[i - 1][1] + 1
        else:
            da = (grezzi[-1][1] + 1 - punti) if len(grezzi) > 1 else apice - punti // 4
        fren = punto_di_frenata(velocita, freno, min(da, apice), apice)
        inizio = fren if fren is not None else ins
        eventi.append(Evento(
            inizio=(inizio % punti) / punti,
            frenata=None if fren is None else (fren % punti) / punti,
            inserimento=ins / punti,
            apice=apice / punti,
            uscita=usc / punti,
            segno=segno,
            picco_g=round(float(g[picco]), 3) if (g is not None and picco >= 0) else 0.0,
            posizione_picco=picco / punti if picco >= 0 else None,
            minimo=minimo,
            velocita_apice=round(float(velocita[apice]), 1),
            velocita_frenata=None if fren is None else round(float(velocita[fren % punti]), 1),
        ))
    return eventi


# ── la proposta ─────────────────────────────────────────────────────────────

_PUNTEGGIO_SENSO_GIUSTO = 3.0
_PUNTEGGIO_SENSO_IGNOTO = 1.0
_PUNTEGGIO_SENSO_SBAGLIATO = -0.5
_BONUS_TIPO = 0.5             # lenta ↔ curva con staccata, veloce ↔ curva in pieno
_SALTA_CURVA = -1.0           # curva della guida lasciata al click di Edoardo
_SALTA_EVENTO = -0.2          # curva del giro che la guida non numera


def _punteggio(curva: dict[str, Any], evento: Evento) -> float:
    senso = curva.get("direzione")
    if senso not in ("destra", "sinistra") or evento.direzione is None:
        voto = _PUNTEGGIO_SENSO_IGNOTO
    elif senso == evento.direzione:
        voto = _PUNTEGGIO_SENSO_GIUSTO
    else:
        voto = _PUNTEGGIO_SENSO_SBAGLIATO
    tipo = curva.get("tipo")
    if tipo == "lenta" and evento.frenata is not None:
        voto += _BONUS_TIPO
    elif tipo == "veloce" and evento.frenata is None:
        voto += _BONUS_TIPO
    return voto


def proponi(curve_guida: list[dict[str, Any]], eventi: list[Evento]) -> list[dict[str, Any]]:
    """Per ogni curva della guida, la curva del giro proposta (o nessuna).

    Allineamento in ordine (programmazione dinamica, come fra due sequenze): una curva
    della guida può restare senza abbinamento (la clicca Edoardo), una curva del giro
    può restare senza curva della guida. Un abbinamento col senso sbagliato è permesso
    ma porta un avviso: o è sbagliato l'abbinamento, o è sbagliata la guida.
    """
    n, m = len(curve_guida), len(eventi)
    tab = np.zeros((n + 1, m + 1))
    for i in range(1, n + 1):
        tab[i, 0] = i * _SALTA_CURVA
    for j in range(1, m + 1):
        tab[0, j] = j * _SALTA_EVENTO
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            tab[i, j] = max(
                tab[i - 1, j - 1] + _punteggio(curve_guida[i - 1], eventi[j - 1]),
                tab[i - 1, j] + _SALTA_CURVA,
                tab[i, j - 1] + _SALTA_EVENTO,
            )
    abbinati: dict[int, int] = {}
    i, j = n, m
    while i > 0 and j > 0:
        if np.isclose(tab[i, j], tab[i - 1, j - 1] + _punteggio(curve_guida[i - 1], eventi[j - 1])):
            abbinati[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif np.isclose(tab[i, j], tab[i - 1, j] + _SALTA_CURVA):
            i -= 1
        else:
            j -= 1

    proposta = []
    for i, curva in enumerate(curve_guida):
        voce: dict[str, Any] = {"n": curva.get("n"), "nome": curva.get("nome"),
                                "direzione": curva.get("direzione"), "tipo": curva.get("tipo"),
                                "evento": None, "inizio": None, "apice": None, "uscita": None,
                                "metodo_inizio": None, "metodo_apice": None, "avviso": None}
        if i in abbinati:
            e = eventi[abbinati[i]]
            voce.update(evento=abbinati[i], inizio=round(e.inizio, 4), apice=round(e.apice, 4),
                        uscita=round(e.uscita, 4), metodo_inizio=e.metodo_inizio,
                        metodo_apice=e.metodo_apice)
            if (curva.get("direzione") in ("destra", "sinistra") and e.direzione
                    and e.direzione != curva.get("direzione")):
                voce["avviso"] = (f"la guida dice «{curva.get('direzione')}», "
                                  f"l'accelerazione laterale dice «{e.direzione}»")
        proposta.append(voce)
    return proposta


# ── la verifica su un'altra sessione ───────────────────────────────────────


def _distanza(a: float, b: float) -> float:
    """Distanza sul giro, che è un anello."""
    d = abs(a - b) % 1.0
    return min(d, 1.0 - d)


def _tratto_di(posizione: float, curve_motore: list) -> Any | None:
    """Il tratto del motore che contiene la posizione (i tratti coprono tutto il giro)."""
    for c in curve_motore:
        ing, usc = c.ingresso, c.uscita
        dentro = ing <= posizione <= usc if ing <= usc else (posizione >= ing or posizione <= usc)
        if dentro:
            return c
    return None


def verifica(ancore: list[dict[str, Any]], origine: dict[str, Any],
             altra: dict[str, Any], tolleranza: float = TOLLERANZA) -> list[dict[str, Any]]:
    """Le ancore di `origine` riportate sul profilo di `altra` (stessa pista).

    Si controlla l'**apice** di ogni ancora, che è il punto che il motore conosce:
    (a) su `altra` c'è un apice (o un picco di carico) dello stesso senso entro
        `tolleranza`: è questo che dice se l'ancora regge;
    (b) SOLO INFORMATIVO (decisione del 28/09): il tratto del motore che lo contiene ha
        l'apice entro `tolleranza` da quello di `origine` — riconosciuto dall'apice, non
        dal numero. Su un giro solo il motore divide alcune curve in modo diverso da una
        sessione all'altra, quindi (b) può fallire anche con ancore giuste.
    """
    eventi_altra = trova_eventi(altra)
    esiti = []
    for a in ancore:
        pos = float(a["apice"])
        senso = a.get("direzione")
        candidati = []
        for e in eventi_altra:
            if senso in ("destra", "sinistra") and e.direzione not in (senso, None):
                continue
            punti_e = [e.apice] + ([e.posizione_picco] if e.posizione_picco is not None else [])
            candidati.append(min(_distanza(p, pos) for p in punti_e))
        scarto_punto = min((c for c in candidati if c <= tolleranza), default=None)

        t_orig = _tratto_di(pos, origine["curve_motore"])
        t_altra = _tratto_di(pos, altra["curve_motore"])
        scarto_apice = (_distanza(t_orig.apice, t_altra.apice)
                        if t_orig is not None and t_altra is not None else None)
        esiti.append({
            "n": a["n"],
            "nome": a.get("nome"),
            "apice": pos,
            "punto_ok": scarto_punto is not None,
            "scarto_punto": None if scarto_punto is None else round(scarto_punto, 4),
            "tratto_ok": scarto_apice is not None and scarto_apice <= tolleranza,
            "scarto_apice": None if scarto_apice is None else round(scarto_apice, 4),
        })
    return esiti


def come_json(eventi: list[Evento]) -> list[dict[str, Any]]:
    return [{**asdict(e), "direzione": e.direzione, "metodo_inizio": e.metodo_inizio,
             "metodo_apice": e.metodo_apice} for e in eventi]
