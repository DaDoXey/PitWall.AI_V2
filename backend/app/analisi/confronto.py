"""analisi/confronto.py — «Sono migliorato?»: la sessione contro la precedente.

Scope chiuso con Edoardo il 05/10/2026:

- **Con chi.** La sessione precedente sulla **stessa pista e vettura**, dentro lo stesso
  gruppo: le tue con le tue, i riferimenti con i riferimenti, la demo con la sua «volta
  prima» (`bundle/demo_precedente.py`). Gigi non ti attribuisce mai i giri di un altro.
- **Che cosa.** Ritmo, curve, setup cambiato, gomme.
- **Condizioni diverse.** Si confronta e si dichiara: la differenza di temperatura della
  pista si dice da `SOGLIA_DICHIARA_C` in su, le gomme si confrontano solo entro
  `SOGLIA_GOMME_C`. Asciutto contro bagnato: nessun confronto, e lo si dice.
- **Come lo dice.** Un messaggio (il ritmo e la cosa più importante che è cambiata); le
  prove, riga per riga, escono con «Perché?».

**Le curve si confrontano giro migliore contro giro migliore**, sugli stessi tratti: quelli
del motore per la sessione di oggi (o, se oggi c'è un giro solo, quelli della precedente,
o quelli ricavati dal giro stesso). Così il confronto regge anche fra due sessioni da un
giro, dove le perdite medie per curva non esistono. I tratti si toccano l'uno con l'altro
e coprono tutto il giro: la somma delle differenze è la differenza sul giro.

**Cosa non fa.** Non dice che un click ha fatto guadagnare tempo: mette il setup cambiato
accanto al tempo, e basta. Non confronta quello che una delle due sessioni non ha
(canali, setup, pressioni): lo dichiara.
"""

from __future__ import annotations

import math
from datetime import datetime
from statistics import mean
from typing import Any, Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from app.analisi import aggancio as aggancio_mod
from app.analisi.curve import (
    POSIZIONE,
    PUNTI_GRIGLIA,
    TEMPO,
    VELOCITA,
    Curva,
    CurveNonCalcolabili,
    dividi_in_giri,
    giri_di_ritmo,
    su_distanza,
    trova_curve,
)
from app.analisi.motore import ReportAnalisi
from app.bundle.schema import SessionBundle
from app.core import riferimenti_fisica as rif
from app.core.setup_params import get_params_for_car

# Sotto questa differenza un tratto non si nomina (rumore), come nel debrief.
SOGLIA_TRATTO_MS = 50.0
# Sotto questa differenza il giro migliore è «lo stesso».
SOGLIA_GIRO_MS = 10
# Differenza di temperatura della pista: da qui si dichiara, oltre la seconda le gomme
# non si confrontano più.
SOGLIA_DICHIARA_C = 3.0
SOGLIA_GOMME_C = 5.0
# Sotto queste differenze una gomma che non cambia stato non si nomina.
SOGLIA_PRESSIONE_PSI = 0.2
SOGLIA_TEMPERATURA_C = 3.0
# Quante voci entrano nella prova, per curve e setup: il resto si conta.
VOCI_IN_PROVA = 6

RUOTE = ("FL", "FR", "RL", "RR")
NOMI_RUOTE = {"FL": "Ant.SX", "FR": "Ant.DX", "RL": "Post.SX", "RR": "Post.DX"}
_PRESSIONI_SETUP = {"tire_press_fl": "FL", "tire_press_fr": "FR", "tire_press_rl": "RL", "tire_press_rr": "RR"}
_STATI = {"ok": "in finestra", "bassa": "sotto la finestra", "alta": "sopra la finestra",
          "calda": "oltre la finestra di temperatura"}


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Precedente(_Base):
    id: str
    giorno: str | None = None          # «14/07/2026»
    demo: bool = False
    riferimento: bool = False


class RitmoConfronto(_Base):
    """Differenze = oggi − prima: negativo vuol dire più veloce oggi."""

    migliore_ms: int
    migliore_prima_ms: int
    delta_migliore_ms: int
    media_ms: int | None = None
    media_prima_ms: int | None = None
    delta_media_ms: int | None = None
    giri_di_ritmo: int = 0
    giri_di_ritmo_prima: int = 0


class TrattoConfronto(_Base):
    curva: int
    nome: str | None = None
    mappa: dict[str, float] | None = None
    tempo_ms: float
    tempo_prima_ms: float
    delta_ms: float


class ParametroCambiato(_Base):
    chiave: str
    etichetta: str
    sezione: str
    click: int | float
    click_prima: int | float
    delta_click: int | float
    valore: str | None = None          # «25.1 psi», solo con la tabella della vettura
    valore_prima: str | None = None


class RuotaConfronto(_Base):
    ruota: str
    pressione: float | None = None
    pressione_prima: float | None = None
    temperatura_max: float | None = None
    temperatura_max_prima: float | None = None
    stato: str | None = None           # ok · bassa · alta · calda
    stato_prima: str | None = None


class Confronto(_Base):
    precedente: Precedente | None = None
    # Perché non c'è un confronto, quando non c'è (nessuna precedente, asciutto/bagnato…).
    motivo: str | None = None
    ritmo: RitmoConfronto | None = None
    curve: list[TrattoConfronto] = Field(default_factory=list)
    setup: list[ParametroCambiato] = Field(default_factory=list)
    setup_confrontabile: bool = False
    gomme: list[RuotaConfronto] = Field(default_factory=list)
    gomme_confrontabili: bool = False
    condizioni: list[str] = Field(default_factory=list)
    messaggio: str = ""
    prova: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────
# formattazione
# ─────────────────────────────────────────────
def _mmss(ms: int) -> str:
    minuti, resto = divmod(ms, 60_000)
    return f"{minuti}:{resto // 1000:02d}.{resto % 1000:03d}"


def _s(ms: float) -> str:
    """Una differenza in secondi senza segno: «0.19 s» (155 ms → 0.16 s)."""
    centesimi = math.floor(abs(ms) / 10 + 0.5)
    return f"{centesimi // 100}.{centesimi % 100:02d} s"


def _s_segno(ms: float) -> str:
    return f"{'−' if ms < 0 else '+'}{_s(ms)}"


def _numero(v: float) -> str:
    return f"{v:g}"


def _segno(v: int | float) -> str:
    return f"{'+' if v > 0 else '−'}{_numero(abs(v))}"


# ─────────────────────────────────────────────
# quale sessione è «la precedente»
# ─────────────────────────────────────────────
def _quando(*valori: str | datetime | None) -> datetime | None:
    """Il primo istante leggibile, senza fuso: le date dei file MoTeC non lo portano."""
    for v in valori:
        if isinstance(v, str):
            try:
                v = datetime.fromisoformat(v)
            except ValueError:
                continue
        if isinstance(v, datetime):
            return v.replace(tzinfo=None)
    return None


def scegli_precedente(riassunti: Sequence[Any], id_sessione: str) -> Any | None:
    """Fra i riassunti dell'archivio, la sessione precedente a `id_sessione`.

    Stessa pista, stessa vettura, stesso gruppo (tue · riferimenti), iniziata prima: fra
    quelle, la più vicina. La demo non passa di qui: la sua precedente è generata.
    """
    ora = next((r for r in riassunti if r.id == id_sessione), None)
    if ora is None or ora.demo or not ora.car or not ora.track:
        return None
    quando_ora = _quando(ora.iniziata_il, ora.importato_il)
    if quando_ora is None:
        return None
    candidate = []
    for r in riassunti:
        if r.id == id_sessione or r.demo or r.car != ora.car or r.track != ora.track:
            continue
        if bool(r.riferimento) != bool(ora.riferimento) or not r.miglior_giro_ms:
            continue
        quando = _quando(r.iniziata_il, r.importato_il)
        if quando is not None and quando < quando_ora:
            candidate.append((quando, r))
    return max(candidate, key=lambda c: c[0])[1] if candidate else None


# ─────────────────────────────────────────────
# curve: giro migliore contro giro migliore
# ─────────────────────────────────────────────
def _profilo_migliore(canali: dict[str, np.ndarray] | None) -> tuple[dict[str, np.ndarray], int] | None:
    """Il giro migliore di ritmo sulla griglia di posizione, con il suo tempo."""
    if not canali or any(c not in canali for c in (POSIZIONE, VELOCITA, TEMPO)):
        return None
    completi = [g for g in dividi_in_giri(canali) if g.completo and not g.ai_box and g.tempo_ms]
    buoni, _, _ = giri_di_ritmo(completi)
    if not buoni:
        return None
    giro = min(buoni, key=lambda g: g.tempo_ms)
    try:
        return su_distanza(canali, giro, [VELOCITA, TEMPO]), int(giro.tempo_ms)
    except CurveNonCalcolabili:
        return None


def _tratti(report: ReportAnalisi | None) -> list[Curva]:
    return [Curva(numero=c["numero"], ingresso=c["ingresso"], apice=c["apice"], uscita=c["uscita"],
                  velocita_minima_riferimento=c["velocita_minima_riferimento"])
            for c in ((report.curve or {}).get("curve") or [])] if report else []


def _tempo_sul_tratto(profilo: dict[str, np.ndarray], tempo_giro_ms: int, tratto: Curva) -> float:
    tempo = profilo[TEMPO]
    inizio = int(tratto.ingresso * PUNTI_GRIGLIA) % PUNTI_GRIGLIA
    fine = int(tratto.uscita * PUNTI_GRIGLIA) % PUNTI_GRIGLIA
    durata = float(tempo[fine] - tempo[inizio])
    if durata <= 0:          # il tratto scavalca il traguardo (o è tutto il giro)
        durata += float(tempo_giro_ms)
    return durata


def _curve(report: ReportAnalisi, canali, report_prima: ReportAnalisi, canali_prima,
           demo: bool) -> tuple[list[TrattoConfronto], str | None]:
    ora, prima = _profilo_migliore(canali), _profilo_migliore(canali_prima)
    if ora is None or prima is None:
        dove = "in tutte e due" if ora is None and prima is None else ("oggi" if ora is None else "la volta prima")
        return [], f"curve non confrontabili: manca la telemetria {dove}"
    tratti = _tratti(report) or _tratti(report_prima) or trova_curve(ora[0][VELOCITA])
    if not tratti:
        return [], "curve non confrontabili: nessuna curva riconosciuta sul giro"
    agganciate = aggancio_mod.aggancia(report.track, tratti, demo=demo)
    nomi = agganciate.tratti if agganciate else {}
    punti = {}
    for c in (agganciate.curve if agganciate else []):
        if c.tratto is not None and c.tratto not in punti:
            punti[c.tratto] = c.mappa
    fuori = []
    for t in tratti:
        a = _tempo_sul_tratto(ora[0], ora[1], t)
        b = _tempo_sul_tratto(prima[0], prima[1], t)
        fuori.append(TrattoConfronto(curva=t.numero, nome=nomi.get(t.numero), mappa=punti.get(t.numero),
                                     tempo_ms=round(a, 1), tempo_prima_ms=round(b, 1),
                                     delta_ms=round(a - b, 1)))
    return fuori, None


# ─────────────────────────────────────────────
# setup
# ─────────────────────────────────────────────
def _valori(a, b) -> tuple[str | None, str | None]:
    """I due valori del gioco con gli stessi decimali («25.0 psi» accanto a «25.7 psi»)."""
    if not (a.verificato and b.verificato) or a.reale is None or b.reale is None or a.unita != b.unita:
        return None, None
    decimali = max(len(_numero(round(v.reale, 3)).partition(".")[2]) for v in (a, b))
    return tuple(f"{v.reale:.{decimali}f} {v.unita}".strip() for v in (a, b))


def _setup(bundle: SessionBundle, prima: SessionBundle) -> tuple[list[ParametroCambiato], str | None]:
    if not bundle.setup or not prima.setup:
        dove = "in tutte e due" if not bundle.setup and not prima.setup else ("oggi" if not bundle.setup else "la volta prima")
        return [], f"setup non confrontabile: manca {dove}"
    fuori: list[ParametroCambiato] = []
    for sezione in get_params_for_car(bundle.meta.car, bundle.meta.track).values():
        for chiave, parametro in sezione["params"].items():
            a, b = bundle.setup.valori.get(chiave), prima.setup.valori.get(chiave)
            if a is None or b is None or a.raw == b.raw:
                continue
            if isinstance(a.raw, list) or isinstance(b.raw, list):
                continue        # i 49 parametri sono numeri singoli; un elenco non si sottrae
            ruota = _PRESSIONI_SETUP.get(chiave)
            valore, valore_prima = _valori(a, b)
            fuori.append(ParametroCambiato(
                chiave=chiave,
                etichetta=f"Pressione {NOMI_RUOTE[ruota]}" if ruota else parametro["label"],
                sezione=sezione["label"],
                click=a.raw, click_prima=b.raw, delta_click=a.raw - b.raw,
                valore=valore, valore_prima=valore_prima,
            ))
    return fuori, None


def _parametro_testo(p: ParametroCambiato) -> str:
    testo = f"{p.etichetta} {_segno(p.delta_click)} click"
    if p.valore and p.valore_prima:
        # L'unità si scrive una volta sola: «24.7 → 25.1 psi».
        prima = p.valore_prima.rsplit(" ", 1)[0] if " " in p.valore_prima else p.valore_prima
        testo += f" ({prima} → {p.valore})"
    return testo


# ─────────────────────────────────────────────
# gomme e condizioni
# ─────────────────────────────────────────────
def _ruote(report: ReportAnalisi) -> dict[str, dict]:
    """Per ruota, sui giri di ritmo: pressione media, temperatura massima, stato."""
    ritmo = {g.numero for g in report.giri if g.di_ritmo}
    per_giro = [p for p in (report.gomme_e_freni or {}).get("per_giro") or [] if p.get("giro") in ritmo]
    p_min, p_max = rif.finestra_pressione_asciutto()
    _, t_max = rif.finestra_core_asciutto()
    fuori: dict[str, dict] = {}
    for r in RUOTE:
        pressioni = [p["pressione"][r] for p in per_giro if (p.get("pressione") or {}).get(r) is not None]
        temperature = [p["temperatura"][r] for p in per_giro if (p.get("temperatura") or {}).get(r) is not None]
        if not pressioni and not temperature:
            continue
        pressione = round(mean(pressioni), 1) if pressioni else None
        massima = round(max(temperature), 0) if temperature else None
        if massima is not None and massima > t_max:
            stato = "calda"
        elif pressione is not None and pressione < p_min:
            stato = "bassa"
        elif pressione is not None and pressione > p_max:
            stato = "alta"
        else:
            stato = "ok"
        fuori[r] = {"pressione": pressione, "temperatura": massima, "stato": stato}
    return fuori


def _condizioni(bundle: SessionBundle, prima: SessionBundle) -> tuple[list[str], float | None]:
    """Quello che era diverso, detto; e la differenza di temperatura della pista se nota."""
    righe: list[str] = []
    a, b = bundle.meta.condizioni, prima.meta.condizioni
    delta_pista = None
    if a.temp_pista_c is not None and b.temp_pista_c is not None:
        delta_pista = a.temp_pista_c - b.temp_pista_c
        if abs(delta_pista) >= SOGLIA_DICHIARA_C:
            righe.append(f"pista {abs(delta_pista):.0f} °C più {'calda' if delta_pista > 0 else 'fredda'} "
                         f"della volta prima ({a.temp_pista_c:.0f} contro {b.temp_pista_c:.0f} °C)")
    else:
        righe.append("temperatura della pista non registrata "
                     f"{'in nessuna delle due' if a.temp_pista_c is None and b.temp_pista_c is None else 'in una delle due'}"
                     ": le condizioni potevano essere diverse")
    if a.temp_aria_c is not None and b.temp_aria_c is not None and abs(a.temp_aria_c - b.temp_aria_c) >= SOGLIA_DICHIARA_C:
        delta = a.temp_aria_c - b.temp_aria_c
        righe.append(f"aria {abs(delta):.0f} °C più {'calda' if delta > 0 else 'fredda'} della volta prima")
    if bundle.meta.riferimento:
        righe.append("sessioni di riferimento: possono essere di piloti diversi")
    return righe, delta_pista


def _gomme(report: ReportAnalisi, report_prima: ReportAnalisi,
           delta_pista: float | None) -> tuple[list[RuotaConfronto], str | None]:
    if delta_pista is not None and abs(delta_pista) > SOGLIA_GOMME_C:
        return [], (f"gomme non confrontate: fra le due sessioni la pista cambia di "
                    f"{abs(delta_pista):.0f} °C (oltre {SOGLIA_GOMME_C:.0f} °C le pressioni si spostano da sole)")
    ora, prima = _ruote(report), _ruote(report_prima)
    if not ora or not prima:
        dove = "in tutte e due" if not ora and not prima else ("oggi" if not ora else "la volta prima")
        return [], f"gomme non confrontabili: mancano pressioni e temperature {dove}"
    return [RuotaConfronto(
        ruota=r,
        pressione=ora[r]["pressione"], pressione_prima=prima[r]["pressione"],
        temperatura_max=ora[r]["temperatura"], temperatura_max_prima=prima[r]["temperatura"],
        stato=ora[r]["stato"], stato_prima=prima[r]["stato"],
    ) for r in RUOTE if r in ora and r in prima], None


def _ruota_testo(g: RuotaConfronto) -> str | None:
    pezzi = []
    if (g.pressione is not None and g.pressione_prima is not None
            and round(abs(g.pressione - g.pressione_prima), 1) >= SOGLIA_PRESSIONE_PSI):
        pezzi.append(f"{g.pressione_prima:.1f} → {g.pressione:.1f} psi")
    if (g.temperatura_max is not None and g.temperatura_max_prima is not None
            and abs(g.temperatura_max - g.temperatura_max_prima) >= SOGLIA_TEMPERATURA_C):
        pezzi.append(f"{g.temperatura_max_prima:.0f} → {g.temperatura_max:.0f} °C al core")
    if not pezzi and g.stato == g.stato_prima:
        return None
    if g.stato == g.stato_prima:
        stato = "sempre in finestra" if g.stato == "ok" else f"ancora {_STATI[g.stato]}"
    else:
        stato = f"prima {_STATI[g.stato_prima]}, ora {_STATI[g.stato]}"
    return f"{NOMI_RUOTE[g.ruota]} {' · '.join(pezzi)} ({stato})".replace("  ", " ")


# ─────────────────────────────────────────────
# il confronto
# ─────────────────────────────────────────────
def _nome(t: TrattoConfronto) -> str:
    return t.nome or f"curva {t.curva}"


def _giorno(bundle: SessionBundle) -> str | None:
    quando = _quando(bundle.meta.iniziata_il, bundle.meta.importato_il)
    return quando.strftime("%d/%m/%Y") if quando else None


def confronta(bundle: SessionBundle, report: ReportAnalisi, canali: dict | None,
              prima: SessionBundle, report_prima: ReportAnalisi, canali_prima: dict | None,
              id_prima: str) -> Confronto:
    """La sessione (`bundle`) contro la precedente (`prima`). Nessun modello, nessuna spesa."""
    e_demo = bundle.meta.fonte.value == "demo"
    precedente = Precedente(id=id_prima, giorno=_giorno(prima), demo=e_demo,
                            riferimento=bundle.meta.riferimento)
    quando = f" del {precedente.giorno}" if precedente.giorno else ""

    if report.mescola and report_prima.mescola and report.mescola != report_prima.mescola:
        return Confronto(precedente=precedente, motivo=(
            f"Non le confronto: oggi eri sull'{report.mescola}, la volta prima{quando} sul "
            f"{report_prima.mescola}. Sono due piste diverse."
            if report.mescola == "asciutto" else
            f"Non le confronto: oggi eri sul {report.mescola}, la volta prima{quando} sull'"
            f"{report_prima.mescola}. Sono due piste diverse."))
    if report.ritmo.miglior_giro_ms is None or report_prima.ritmo.miglior_giro_ms is None:
        return Confronto(precedente=precedente,
                         motivo="Non le confronto: in una delle due sessioni non c'è un giro con il tempo.")

    # ── ritmo ──
    ritmo = RitmoConfronto(
        migliore_ms=report.ritmo.miglior_giro_ms, migliore_prima_ms=report_prima.ritmo.miglior_giro_ms,
        delta_migliore_ms=report.ritmo.miglior_giro_ms - report_prima.ritmo.miglior_giro_ms,
        giri_di_ritmo=report.giri_di_ritmo, giri_di_ritmo_prima=report_prima.giri_di_ritmo,
    )
    # La media ha senso solo con almeno due giri di ritmo per parte: con uno è il giro stesso.
    if (report.giri_di_ritmo >= 2 and report_prima.giri_di_ritmo >= 2
            and report.ritmo.media_ms is not None and report_prima.ritmo.media_ms is not None):
        ritmo.media_ms, ritmo.media_prima_ms = report.ritmo.media_ms, report_prima.ritmo.media_ms
        ritmo.delta_media_ms = report.ritmo.media_ms - report_prima.ritmo.media_ms

    curve, nota_curve = _curve(report, canali, report_prima, canali_prima, e_demo)
    setup, nota_setup = _setup(bundle, prima)
    condizioni, delta_pista = _condizioni(bundle, prima)
    gomme, nota_gomme = _gomme(report, report_prima, delta_pista)

    # ── il messaggio: il ritmo, e la cosa più importante che è cambiata ──
    d = ritmo.delta_migliore_ms
    rispetto = "della sessione precedente" if precedente.riferimento else "della volta prima"
    tempi = f"{_mmss(ritmo.migliore_ms)} contro {_mmss(ritmo.migliore_prima_ms)}"
    if abs(d) < SOGLIA_GIRO_MS:
        frasi = [f"Sei lì: il giro migliore è lo stesso {rispetto} ({tempi})."]
    elif d < 0:
        frasi = [f"Sì: il giro migliore è {_s(d)} più veloce {rispetto} ({tempi})."]
    else:
        frasi = [f"No: il giro migliore è {_s(d)} più lento {rispetto} ({tempi})."]
    if ritmo.delta_media_ms is not None and abs(ritmo.delta_media_ms) >= SOGLIA_GIRO_MS:
        m = ritmo.delta_media_ms
        stessa_direzione = (m < 0) == (d < 0) and abs(d) >= SOGLIA_GIRO_MS
        frasi.append(f"{'Anche in' if stessa_direzione else 'In'} media "
                     f"{'guadagni' if m < 0 else 'perdi'} {_s(m)} a giro.")

    guadagni = sorted((t for t in curve if t.delta_ms <= -SOGLIA_TRATTO_MS), key=lambda t: t.delta_ms)
    perdite = sorted((t for t in curve if t.delta_ms >= SOGLIA_TRATTO_MS), key=lambda t: -t.delta_ms)
    if guadagni or perdite:
        # Prima il tratto che spiega il risultato; se non c'è, quello che va contro.
        principali, altri = (guadagni, perdite) if (d < 0 and guadagni) or not perdite else (perdite, guadagni)
        primo = principali[0]
        verbo = "guadagni" if primo.delta_ms < 0 else "lasci"
        frase = f"Il grosso lo {verbo} in {_nome(primo)}: {_s(primo.delta_ms)}"
        if altri:
            contro = "lasci" if altri[0].delta_ms > 0 else "riprendi"
            frase += f"; in {_nome(altri[0])} ne {contro} {_s(altri[0].delta_ms)}"
        frasi.append(frase + ".")
    elif setup:
        frasi.append(f"Nel setup {'è cambiato un parametro' if len(setup) == 1 else f'sono cambiati {len(setup)} parametri'}.")

    # ── la prova, riga per riga ──
    prova = [f"giro migliore {_mmss(ritmo.migliore_ms)} · prima {_mmss(ritmo.migliore_prima_ms)} "
             f"({_s_segno(d)})"]
    if ritmo.delta_media_ms is not None:
        prova.append(f"media {_mmss(ritmo.media_ms)} · prima {_mmss(ritmo.media_prima_ms)} "
                     f"({_s_segno(ritmo.delta_media_ms)}) · {ritmo.giri_di_ritmo} e "
                     f"{ritmo.giri_di_ritmo_prima} giri di ritmo")
    else:
        prova.append(f"media non confrontata: {ritmo.giri_di_ritmo} e {ritmo.giri_di_ritmo_prima} "
                     "giri di ritmo, ne servono almeno 2 per parte")
    if nota_curve:
        prova.append(nota_curve)
    else:
        mosse = sorted(guadagni + perdite, key=lambda t: -abs(t.delta_ms))
        if mosse:
            riga = " · ".join(f"{_nome(t)} {_s_segno(t.delta_ms)}" for t in mosse[:VOCI_IN_PROVA])
            if len(mosse) > VOCI_IN_PROVA:
                riga += f" · e altre {len(mosse) - VOCI_IN_PROVA}"
            prova.append(f"curve, giro migliore contro giro migliore: {riga}")
        else:
            prova.append(f"curve, giro migliore contro giro migliore: nessuna cambia di più di {_s(SOGLIA_TRATTO_MS)}")
    if nota_setup:
        prova.append(nota_setup)
    elif setup:
        riga = " · ".join(_parametro_testo(p) for p in setup[:VOCI_IN_PROVA])
        if len(setup) > VOCI_IN_PROVA:
            riga += f" · e altri {len(setup) - VOCI_IN_PROVA} parametri"
        prova.append(f"setup, {len(setup)} {'parametro cambiato' if len(setup) == 1 else 'parametri cambiati'}: {riga}")
    else:
        prova.append("setup: identico alla volta prima")
    if nota_gomme:
        prova.append(nota_gomme)
    else:
        righe = [x for x in (_ruota_testo(g) for g in gomme) if x]
        prova.append("gomme: " + (" · ".join(righe) if righe else "pressioni e temperature come la volta prima"))
    prova.extend(condizioni)
    prova.append(f"confronto con la sessione{quando}"
                 + (" (demo)" if e_demo else " (riferimento)" if precedente.riferimento else ""))

    return Confronto(
        precedente=precedente, ritmo=ritmo, curve=curve,
        setup=setup, setup_confrontabile=nota_setup is None,
        gomme=gomme, gomme_confrontabili=nota_gomme is None,
        condizioni=condizioni, messaggio=" ".join(frasi), prova=prova,
    )
