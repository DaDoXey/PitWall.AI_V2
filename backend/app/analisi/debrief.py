"""analisi/debrief.py — il debrief di Gigi, fase per fase (Entry #059).

La Engineer Console racconta la sessione come la radio del muretto: i giri divisi in
**fasi** e, per ognuna, quello che Gigi ti direbbe con i numeri che lo provano. Tutto
dal report del motore, senza modello: le frasi sono composte qui, e ogni numero viene
da `ReportAnalisi` (giri, curve giro per giro, gomme giro per giro, degrado).

**Le fasi.** Si lavora sui giri di ritmo (fuori out lap, pit, giri buttati). I confini
sono **tagli**: il numero del giro con cui comincia una fase nuova.
- Automatici: prima del giro migliore («L'avvio»), il giro migliore («Il giro»), dopo
  («Il calo» se il motore dimostra un degrado, altrimenti «La tenuta»). Una fase senza
  giri non c'è.
- A mano: il pilota sposta i tagli sulla striscia dei giri; si salvano nel bundle
  (`SessionBundle.fasi_tagli`). Ogni fase prende il tipo dalla sua posizione rispetto
  al giro migliore, e quando più fasi hanno lo stesso tipo il nome dice i giri.

**Cosa non fa.** Non inventa cause: una curva entra in una fase solo se ci perdi
almeno `SOGLIA_CURVA_MS` in media su quei giri, una gomma solo se sta fuori dalla
finestra Kunos in quei giri. Senza canali (import da file dei risultati) le fasi
restano, ma parlano solo di tempi.
"""

from __future__ import annotations

import math
from statistics import mean
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.analisi.motore import GiroReport, ReportAnalisi
from app.core import riferimenti_fisica as rif

# Sotto questa perdita media in una fase, una curva non si nomina (rumore).
SOGLIA_CURVA_MS = 50.0
# Una curva «si prende il grosso» in una fase se lì c'è almeno questa quota della sua
# perdita di tutta la sessione.
QUOTA_GROSSO = 0.5
# Oltre questo scarto dal teorico il giro migliore non è «messo insieme tutto».
GIRO_COMPLETO_MS = 50
PUNTI_PER_FASE = 3

RUOTE = ("FL", "FR", "RL", "RR")
NOMI_RUOTE = {"FL": "Ant.SX", "FR": "Ant.DX", "RL": "Post.SX", "RR": "Post.DX"}

TipoFase = Literal["avvio", "giro", "calo", "tenuta"]
NOMI_TIPO = {"avvio": "L'avvio", "giro": "Il giro", "calo": "Il calo", "tenuta": "La tenuta"}


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PuntoFase(_Base):
    """Una curva dove in questa fase si perde tempo."""

    curva: int
    nome: str | None = None                 # dalla guida, se la pista è agganciata
    perdita_ms: float                       # media sui giri della fase
    mappa: dict[str, float] | None = None   # {x, y} normalizzati, se la pista è agganciata


class Fase(_Base):
    tipo: TipoFase
    nome: str
    giri: list[int]
    delta_medio_ms: int | None = None       # media dello scarto dal giro migliore
    messaggio: str                          # quello che Gigi dice alla radio
    prova: str                              # i numeri, in piccolo
    punti: list[PuntoFase] = Field(default_factory=list)
    # Argomenti per gli agganci alle altre sezioni: «gomme», «freni», «ritmo»,
    # «curva:7», «settore:3». Il frontend li trasforma in link.
    argomenti: list[str] = Field(default_factory=list)


class PrimaCosa(_Base):
    """La prima cosa da fare: la voce più grave del verdetto che tocca il setup."""

    titolo: str
    azione: str
    categoria: str
    parametri: dict[str, float | None] = Field(default_factory=dict)


class GiroStriscia(_Base):
    numero: int
    tempo_ms: int
    delta_ms: int
    migliore: bool


class Debrief(_Base):
    fasi: list[Fase] = Field(default_factory=list)
    tagli: list[int] = Field(default_factory=list)
    tagli_automatici: list[int] = Field(default_factory=list)
    manuale: bool = False
    giri: list[GiroStriscia] = Field(default_factory=list)
    fuori_ritmo: list[int] = Field(default_factory=list)
    in_ballo_ms: int | None = None          # media dei giri di ritmo − giro migliore
    prima_cosa: PrimaCosa | None = None
    nota: str | None = None


class TagliNonValidi(ValueError):
    """I tagli chiesti non si possono applicare a questa sessione."""


# ─────────────────────────────────────────────
# formattazione
# ─────────────────────────────────────────────
def _mmss(ms: int) -> str:
    minuti, resto = divmod(ms, 60_000)
    return f"{minuti}:{resto // 1000:02d}.{resto % 1000:03d}"


def _s(ms: float) -> str:
    """Una perdita in secondi, come la dice un ingegnere: «0.17 s».

    Arrotonda al centesimo per eccesso sulla metà (155 ms → 0.16 s): il formato dei
    float da solo darebbe 0.15, per come 0.155 sta in binario.
    """
    centesimi = math.floor(abs(ms) / 10 + 0.5)
    return f"{'-' if ms < 0 else ''}{centesimi // 100}.{centesimi % 100:02d} s"


def _giri_testo(giri: list[int]) -> str:
    if len(giri) == 1:
        return f"G{giri[0]}"
    return f"G{giri[0]}–{giri[-1]}"


# ─────────────────────────────────────────────
# tagli
# ─────────────────────────────────────────────
def _giri_di_ritmo(report: ReportAnalisi) -> list[GiroReport]:
    return [g for g in report.giri if g.di_ritmo and g.tempo_ms]


def tagli_automatici(report: ReportAnalisi) -> list[int]:
    """Dove Gigi taglia da solo: al giro migliore e al giro dopo."""
    giri = [g.numero for g in _giri_di_ritmo(report)]
    migliore = report.ritmo.miglior_giro_numero
    if not giri or migliore not in giri:
        return []
    i = giri.index(migliore)
    tagli = []
    if i > 0:
        tagli.append(migliore)
    if i + 1 < len(giri):
        tagli.append(giri[i + 1])
    return tagli


def valida_tagli(report: ReportAnalisi, tagli: list[int]) -> list[int]:
    """Tagli in ordine e senza doppioni, solo su giri di ritmo e mai sul primo."""
    giri = [g.numero for g in _giri_di_ritmo(report)]
    if not giri:
        raise TagliNonValidi("la sessione non ha giri di ritmo da dividere in fasi")
    puliti = sorted(set(tagli))
    fuori = [t for t in puliti if t not in giri]
    if fuori:
        raise TagliNonValidi(f"giri che non sono di ritmo: {', '.join(map(str, fuori))}")
    if puliti and puliti[0] == giri[0]:
        raise TagliNonValidi(f"il giro {giri[0]} è il primo: una fase comincia già lì")
    return puliti


def _dividi(giri: list[int], tagli: list[int]) -> list[list[int]]:
    gruppi: list[list[int]] = []
    for n in giri:
        if not gruppi or n in tagli:
            gruppi.append([n])
        else:
            gruppi[-1].append(n)
    return gruppi


def _tipo(gruppo: list[int], migliore: int | None, degrado_dimostrato: bool) -> TipoFase:
    if migliore is None:
        return "tenuta"
    if migliore in gruppo:
        return "giro"
    if gruppo[-1] < migliore:
        return "avvio"
    return "calo" if degrado_dimostrato else "tenuta"


# ─────────────────────────────────────────────
# curve e gomme di una fase
# ─────────────────────────────────────────────
def _nomi_curve(report: ReportAnalisi) -> dict[int, dict]:
    """Motore → guida: il nome del tratto e il punto sulla mappa di ogni curva del motore.

    Come il pannello «La pista» (Entry #048): il nome è quello del tratto dell'aggancio
    («T11 Curva Alboreto»), il punto è la prima curva della guida di quel tratto.
    """
    aggancio = report.aggancio or {}
    tratti = aggancio.get("tratti") or {}
    curve_guida = aggancio.get("curve") or []
    out: dict[int, dict] = {}
    for chiave, nome in tratti.items():
        n = int(chiave)
        prima = next((g for g in curve_guida if g.get("tratto") == n), None)
        out[n] = {"nome": nome, "mappa": (prima or {}).get("mappa")}
    return out


def _punti(report: ReportAnalisi, giri: list[int]) -> list[PuntoFase]:
    dettaglio = (report.curve or {}).get("dettaglio") or []
    per_curva: dict[int, list[float]] = {}
    for d in dettaglio:
        if d["giro"] in giri:
            per_curva.setdefault(d["curva"], []).append(d["perdita_ms"])
    nomi = _nomi_curve(report)
    punti = [
        PuntoFase(curva=c, perdita_ms=round(mean(v), 1),
                  nome=(nomi.get(c) or {}).get("nome"), mappa=(nomi.get(c) or {}).get("mappa"))
        for c, v in per_curva.items() if mean(v) >= SOGLIA_CURVA_MS
    ]
    punti.sort(key=lambda p: p.perdita_ms, reverse=True)
    return punti[:PUNTI_PER_FASE]


def _quota_nella_fase(report: ReportAnalisi, curva: int, giri: list[int]) -> float:
    dettaglio = [d for d in (report.curve or {}).get("dettaglio") or [] if d["curva"] == curva]
    totale = sum(d["perdita_ms"] for d in dettaglio)
    if totale <= 0:
        return 0.0
    return sum(d["perdita_ms"] for d in dettaglio if d["giro"] in giri) / totale


def _nome_curva(p: PuntoFase) -> str:
    return p.nome or f"curva {p.curva}"


def _gomme_fuori(report: ReportAnalisi, giri: list[int]) -> list[str]:
    """Le ruote fuori dalla finestra Kunos in questi giri, dette come le dice Gigi."""
    gf = report.gomme_e_freni or {}
    if (gf.get("gomme") or {}).get("mescola") not in (None, "asciutto"):
        return []  # la finestra vale solo per l'asciutto
    per_giro = [p for p in gf.get("per_giro") or [] if p.get("giro") in giri]
    if not per_giro:
        return []
    p_min, p_max = rif.finestra_pressione_asciutto()
    _, t_max = rif.finestra_core_asciutto()
    frasi = []
    basse, alte = [], []
    for r in RUOTE:
        pressioni = [p["pressione"][r] for p in per_giro if (p.get("pressione") or {}).get(r) is not None]
        if pressioni and mean(pressioni) < p_min:
            basse.append((r, mean(pressioni)))
        elif pressioni and mean(pressioni) > p_max:
            alte.append((r, mean(pressioni)))
    for gruppo, dove in ((basse, "sotto"), (alte, "sopra")):
        if not gruppo:
            continue
        valori = [v for _, v in gruppo]
        if len(gruppo) == 4:
            frasi.append(f"tutte e quattro {dove} la finestra ({min(valori):.1f}–{max(valori):.1f} psi)")
        else:
            nomi = ", ".join(NOMI_RUOTE[r] for r, _ in gruppo)
            frasi.append(f"{nomi} {dove} la finestra ({' / '.join(f'{v:.1f}' for v in valori)} psi)")
    for r in RUOTE:
        temperature = [p["temperatura"][r] for p in per_giro if (p.get("temperatura") or {}).get(r) is not None]
        if temperature and max(temperature) > t_max:
            frasi.append(f"la {NOMI_RUOTE[r]} arriva a {max(temperature):.0f} °C")
    return frasi


# ─────────────────────────────────────────────
# le frasi
# ─────────────────────────────────────────────
def _fase(report: ReportAnalisi, tipo: TipoFase, giri: list[int], nome: str,
          per_numero: dict[int, GiroReport]) -> Fase:
    delta = [per_numero[n].delta_migliore_ms for n in giri if per_numero[n].delta_migliore_ms is not None]
    delta_medio = round(mean(delta)) if delta else None
    punti = _punti(report, giri)
    # Nell'avvio le gomme stanno ancora salendo: fuori finestra è normale, non si dice.
    gomme = [] if tipo == "avvio" else _gomme_fuori(report, giri)
    argomenti: list[str] = []
    prove: list[str] = []
    frasi: list[str] = []

    if tipo == "giro":
        n = giri[0] if len(giri) == 1 else report.ritmo.miglior_giro_numero
        tempo = report.ritmo.miglior_giro_ms
        teorico = report.ritmo.lasciato_sul_tavolo_ms
        frasi.append(f"Questo è il giro: {_mmss(tempo)}, il {n}.")
        if teorico is not None and teorico <= GIRO_COMPLETO_MS:
            frasi.append(f"A {teorico} millesimi dal teorico: l'hai messo insieme tutto.")
        elif teorico is not None:
            peggiore = max(report.settori, key=lambda s: s.perdita_sul_giro_migliore_ms or 0, default=None)
            if peggiore and peggiore.perdita_sul_giro_migliore_ms:
                frasi.append(f"Al teorico mancano {_s(teorico)}: il grosso nel settore {peggiore.numero}.")
                argomenti.append(f"settore:{peggiore.numero}")
        prove.append(f"giro {n} · {_mmss(tempo)}")
        if teorico is not None:
            prove.append(f"teorico a {teorico} ms")
        altri = [per_numero[x].delta_migliore_ms for x in giri
                 if x != n and per_numero[x].delta_migliore_ms is not None]
        if altri:
            frasi.append(f"Intorno, gli altri giri a +{_s(mean(altri))} in media.")
        # Nel giro migliore i punti deboli sono quelli che restano: si dicono solo come prova.
        punti = []
        argomenti.append("ritmo")
    else:
        conta = len(giri)
        if tipo == "avvio":
            dall_inizio = giri[0] == min(per_numero)
            if conta == 1:
                frasi.append(f"Giro {giri[0]}: +{_s(delta_medio or 0)} dal tuo migliore.")
            elif dall_inizio and giri == sorted(per_numero)[:conta] and giri[-1] - giri[0] + 1 == conta:
                frasi.append(f"Nei primi {conta} giri sei a +{_s(delta_medio or 0)} dal tuo migliore.")
            else:
                frasi.append(f"Nei {conta} giri prima del migliore sei a +{_s(delta_medio or 0)} in media.")
        elif tipo == "calo":
            pendenza = report.degrado.pendenza_ms_giro
            frasi.append(f"Da qui cedi {pendenza:.0f} millesimi a giro."
                         if pendenza else f"Qui sei a +{_s(delta_medio or 0)} dal tuo migliore.")
            argomenti.append("ritmo")
            prove.append(f"degrado {pendenza:.0f} ms/giro dal giro {report.degrado.dal_giro} "
                         f"(R² {report.degrado.r_quadro:.2f})" if pendenza and report.degrado.r_quadro is not None else "")
        elif conta == 1:  # tenuta di un giro solo: non è ancora una tenuta
            frasi.append(f"Giro {giri[0]}: +{_s(delta_medio or 0)} dal tuo migliore.")
        else:  # tenuta
            frasi.append(f"Il ritmo tiene: +{_s(delta_medio or 0)} in media dal tuo migliore.")
        if punti:
            primo = punti[0]
            quota = _quota_nella_fase(report, primo.curva, giri)
            # «Il grosso» solo se la fase si prende più della sua parte: più della metà
            # della perdita di quella curva, e ben oltre la sua quota di giri.
            quota_giri = len(giri) / len(per_numero)
            if quota >= max(QUOTA_GROSSO, quota_giri + 0.2):
                frasi.append(f"Il grosso lo lasci in {_nome_curva(primo)}: {_s(primo.perdita_ms)} a giro qui.")
            else:
                frasi.append(f"Dove perdi di più: {_nome_curva(primo)}, {_s(primo.perdita_ms)} a giro.")
            for p in punti:
                argomenti.append(f"curva:{p.curva}")
        if gomme:
            frasi.append(gomme[0][0].upper() + gomme[0][1:] + ("; " + "; ".join(gomme[1:]) if len(gomme) > 1 else "") + ".")
            argomenti.append("gomme")
        prove.insert(0, f"{_giri_testo(giri)} · +{_s(delta_medio or 0)} in media dal migliore")
        prove.extend(f"{_nome_curva(p)} {_s(p.perdita_ms)}" for p in punti)

    return Fase(tipo=tipo, nome=nome, giri=giri, delta_medio_ms=delta_medio,
                messaggio=" ".join(frasi), prova=" · ".join(x for x in prove if x),
                punti=punti, argomenti=list(dict.fromkeys(argomenti)))


def _prima_cosa(report: ReportAnalisi) -> PrimaCosa | None:
    con_setup = [v for v in report.verdetto if any(x is not None for x in v.parametri.values())]
    voce = con_setup[0] if con_setup else (report.verdetto[0] if report.verdetto else None)
    if voce is None:
        return None
    return PrimaCosa(titolo=voce.titolo, azione=voce.azione, categoria=voce.categoria,
                     parametri=dict(voce.parametri))


def debrief(report: ReportAnalisi, tagli: list[int] | None = None) -> Debrief:
    """Il debrief della sessione. `tagli` None = le fasi di Gigi (automatiche).

    Raises:
        TagliNonValidi: tagli su giri che non sono di ritmo, o sul primo giro.
    """
    ritmo = _giri_di_ritmo(report)
    per_numero = {g.numero: g for g in ritmo}
    automatici = tagli_automatici(report)
    manuale = tagli is not None
    usati = valida_tagli(report, tagli) if manuale else automatici
    fuori = [g.numero for g in report.giri if g.tempo_ms and not g.di_ritmo]

    striscia = [GiroStriscia(numero=g.numero, tempo_ms=g.tempo_ms, delta_ms=g.delta_migliore_ms or 0,
                             migliore=g.migliore) for g in ritmo]
    in_ballo = None
    if report.ritmo.media_ms is not None and report.ritmo.miglior_giro_ms is not None:
        in_ballo = report.ritmo.media_ms - report.ritmo.miglior_giro_ms

    if not ritmo:
        return Debrief(tagli=[], tagli_automatici=[], manuale=False, fuori_ritmo=fuori,
                       prima_cosa=_prima_cosa(report),
                       nota="Nessun giro di ritmo: non c'è una sessione da raccontare fase per fase.")

    gruppi = _dividi([g.numero for g in ritmo], usati)
    migliore = report.ritmo.miglior_giro_numero
    dimostrato = bool(report.degrado.significativo)
    tipi = [_tipo(g, migliore, dimostrato) for g in gruppi]
    fasi = []
    for gruppo, tipo in zip(gruppi, tipi):
        doppio = tipi.count(tipo) > 1
        nome = f"{NOMI_TIPO[tipo]} · {_giri_testo(gruppo)}" if doppio else NOMI_TIPO[tipo]
        fasi.append(_fase(report, tipo, gruppo, nome, per_numero))

    nota = None
    if not report.ha_canali:
        nota = "Senza la telemetria le fasi parlano solo di tempi: curve e gomme arrivano con i canali."
    return Debrief(fasi=fasi, tagli=usati, tagli_automatici=automatici, manuale=manuale,
                   giri=striscia, fuori_ritmo=fuori, in_ballo_ms=in_ballo,
                   prima_cosa=_prima_cosa(report), nota=nota)
