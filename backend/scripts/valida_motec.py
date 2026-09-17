"""valida_motec.py — il motore di PitWall sui file MoTeC veri di ACC (L5 · Fase 3).

Non è un test: i file veri non stanno nel repo (licenze, e non sono di Edoardo). Legge
quelli scaricati in `%LOCALAPPDATA%\\PitWall\\motec\\riferimenti` e scrive un resoconto
in Markdown con quello che torna, quello che non torna e quello che questi file non
permettono di verificare. Nessuna correzione automatica: ogni scostamento si discute.

Che cosa controlla:
    A  lettore        ogni file letto fino all'ultimo byte; giro = «Fastest Time» del .ldx
    B  distanza       distanza integrata sul giro vs lunghezza ufficiale del catalogo, e
                      dispersione fra file della stessa pista
    C  curve          giri di file diversi sulla stessa pista messi in fila: curve trovate
                      vs curve del catalogo, e di quanti metri si sposta lo stesso minimo
                      di velocità da un giro all'altro (misura l'errore della posizione
                      ricavata)
    D  gomme e freni  pressioni e temperature freni sui giri veri, contro Kunos e community
    E  setup          i setup JSON accanto ai file letti dall'adattatore
    F  motore         il verdetto sui giri veri: nessun crollo, voci plausibili
    G  non verificabile con questi file
    H  scrittore      gli export nativi di ACC riscritti da PitWall: identici byte per byte?

Uso (dalla cartella backend/):
    ./.venv/Scripts/python scripts/valida_motec.py
    ./.venv/Scripts/python scripts/valida_motec.py --uscita percorso/resoconto.md
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.analisi import analizza  # noqa: E402
from app.analisi.curve import (  # noqa: E402
    POSIZIONE,
    TEMPO,
    VELOCITA,
    CurveNonCalcolabili,
    analizza_curve,
    dividi_in_giri,
    su_distanza,
)
from app.bundle.adapters import SetupAccError, leggi_setup_acc  # noqa: E402
from app.bundle.adapters.motec import MotecNonConvertibile, bundle_da_motec  # noqa: E402
from app.core import catalog, riferimenti_fisica as rif  # noqa: E402
from app.motec import leggi_registrazione, tempo_in_secondi  # noqa: E402
from app.motec.scrittura import CanaleDaScrivere, scrivi_ld, scrivi_ldx  # noqa: E402

RUOTE = ("FL", "FR", "RL", "RR")


def _cartella_predefinita() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "PitWall" / "motec" / "riferimenti"


def _tabella(intestazione: list[str], righe: list[list]) -> list[str]:
    out = ["| " + " | ".join(intestazione) + " |", "|" + "---|" * len(intestazione)]
    out += ["| " + " | ".join("" if c is None else str(c) for c in r) + " |" for r in righe]
    return out


def _sessione_multigiro(voci: list[tuple[str, dict]]) -> dict[str, np.ndarray]:
    """I giri completi di più file in fila, come se fossero una sessione sola.

    Serve solo alla validazione: su un file c'è un giro, e l'analisi per curva ne vuole
    almeno due. Si tengono i canali comuni a tutti; il tempo riparte in continuità.
    """
    pezzi: list[dict[str, np.ndarray]] = []
    for _, canali in voci:
        giri = [g for g in dividi_in_giri(canali) if g.completo]
        for g in giri:
            pezzi.append({k: v[g.inizio:g.fine] for k, v in canali.items()})
    comuni = set.intersection(*(set(p) for p in pezzi))
    fuori: dict[str, np.ndarray] = {}
    for nome in comuni:
        if nome == TEMPO:
            continue
        fuori[nome] = np.concatenate([p[nome] for p in pezzi])
    n = fuori[POSIZIONE].size
    fuori[TEMPO] = (np.arange(n, dtype=np.float64) * 10.0).astype(np.float32)   # 100 Hz
    return fuori


def _spostamento_minimi(canali: dict[str, np.ndarray], report, lunghezza_m: float) -> list[float]:
    """Per ogni curva, quanto si sposta (m) il minimo di velocità fra i giri."""
    giri = [g for g in dividi_in_giri(canali) if g.completo]
    punti = 2000
    profili = [su_distanza(canali, g, [VELOCITA], punti)[VELOCITA] for g in giri]
    spostamenti = []
    for curva in report.curve:
        a = int(curva.ingresso * punti)
        b = int(curva.uscita * punti)
        if b <= a:
            continue
        posizioni = [(a + int(np.argmin(p[a:b]))) / punti * lunghezza_m for p in profili]
        spostamenti.append(max(posizioni) - min(posizioni))
    return spostamenti


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cartella", type=Path, default=_cartella_predefinita())
    parser.add_argument("--uscita", type=Path, default=None)
    args = parser.parse_args()
    uscita = args.uscita or args.cartella.parent / "validazione_motec.md"

    files = sorted(args.cartella.rglob("*.ld"))
    if not files:
        print(f"Nessun .ld in {args.cartella}")
        return 1

    righe: list[str] = [
        f"# Validazione MoTeC — {datetime.now():%d/%m/%Y %H:%M}",
        "",
        f"Cartella: `{args.cartella}` · {len(files)} file `.ld`. Generato da "
        "`backend/scripts/valida_motec.py`.",
        "",
    ]

    # ── A · lettore ──────────────────────────────────────────────────────────
    letti = []
    tab_a = []
    for p in files:
        try:
            reg = leggi_registrazione(p)
        except Exception as e:  # noqa: BLE001 — si riporta, non si crolla
            tab_a.append([p.name, "ERRORE", str(e), "", ""])
            continue
        ultimo = max(c._puntatore_dati + c.campioni * c.tipo[1] for c in reg.ld.canali)
        dichiarato = tempo_in_secondi(reg.ldx.tempo_migliore or "") if reg.ldx else None
        giri = reg.giri_completi
        coerente = (abs(giri[0].durata_s - dichiarato) < 0.0015
                    if giri and dichiarato else None)
        tab_a.append([p.name, len(reg.ld.canali), ultimo == len(reg.ld.contenuto),
                      "i2 (ritagliato)" if reg.ritagliata_in_i2 else "export ACC",
                      {True: "sì", False: "NO", None: "—"}[coerente]])
        letti.append((p, reg))
    righe += ["## A · Lettore", ""]
    righe += _tabella(["file", "canali", "letto fino all'ultimo byte", "origine",
                       "giro = Fastest Time"], tab_a)

    # ── conversione ──────────────────────────────────────────────────────────
    convertiti = []
    errori_conv = []
    for p, reg in letti:
        setup = None
        candidati = sorted(p.parent.glob("*_Q_*.json"))   # FRI3: il setup da qualifica
        if candidati:
            try:
                setup = leggi_setup_acc(candidati[0].read_bytes())
            except SetupAccError:
                setup = None
        try:
            bundle, canali, _ = bundle_da_motec(reg, setup=setup, nome_file=p.name)
        except MotecNonConvertibile as e:
            errori_conv.append(f"- `{p.name}`: {e}")
            continue
        convertiti.append((p, reg, bundle, canali))

    # ── B · distanza ─────────────────────────────────────────────────────────
    per_pista: dict[str, list[float]] = defaultdict(list)
    tab_b = []
    for p, reg, bundle, canali in convertiti:
        ufficiale = catalog.resolve_track(bundle.meta.track)
        lunghezza = ufficiale["length_km"] * 1000 if ufficiale else None
        giro = next(g for g in dividi_in_giri(canali) if g.completo)
        v = canali[VELOCITA][giro.inizio:giro.fine].astype(np.float64) / 3.6
        misurata = float(v.sum() / 100.0)
        per_pista[bundle.meta.track].append(misurata)
        scarto = (misurata - lunghezza) / lunghezza if lunghezza else None
        tab_b.append([p.name, bundle.meta.track, f"{misurata:.0f}",
                      f"{lunghezza:.0f}" if lunghezza else "—",
                      f"{scarto:+.1%}" if scarto is not None else "—"])
    scarti = [float(r[4].rstrip("%")) for r in tab_b if r[4] != "—"]
    righe += ["", "## B · Distanza integrata sul giro", ""]
    righe += _tabella(["file", "pista", "misurata (m)", "catalogo (m)", "scarto"], tab_b)
    if scarti:
        righe += ["", f"Scarto mediano {statistics.median(scarti):+.1f}%, da {min(scarti):+.1f}% a "
                      f"{max(scarti):+.1f}%."]
    ripetute = {k: v for k, v in per_pista.items() if len(v) > 1}
    if ripetute:
        righe += ["", "Stessa pista, file diversi (dispersione della distanza misurata):", ""]
        righe += [f"- {k}: {len(v)} giri, da {min(v):.0f} a {max(v):.0f} m "
                  f"(±{(max(v) - min(v)) / 2 / statistics.fmean(v):.2%})"
                  for k, v in sorted(ripetute.items())]

    # ── C · curve ────────────────────────────────────────────────────────────
    righe += ["", "## C · Curve su giri veri (file diversi della stessa pista in fila)", ""]
    gruppi: dict[str, list] = defaultdict(list)
    for p, reg, bundle, canali in convertiti:
        gruppi[bundle.meta.track].append((p.name, canali))
    tab_c = []
    for pista, voci in sorted(gruppi.items()):
        if len(voci) < 2:
            continue
        canali = _sessione_multigiro(voci)
        voce_cat = catalog.resolve_track(pista)
        try:
            report = analizza_curve(canali)
        except CurveNonCalcolabili as e:
            tab_c.append([pista, len(voci), "—", voce_cat.get("corners"), str(e), ""])
            continue
        lunghezza = report.lunghezza_stimata_m or voce_cat["length_km"] * 1000
        spost = _spostamento_minimi(canali, report, lunghezza)
        tab_c.append([
            pista, len(voci), len(report.curve), voce_cat.get("corners"),
            f"mediana {statistics.median(spost):.0f} m, massimo {max(spost):.0f} m" if spost else "—",
            ", ".join(f"{c.apice_m:.0f}" for c in report.curve if c.apice_m is not None),
        ])
    righe += _tabella(["pista", "giri", "curve trovate", "curve (catalogo)",
                       "spostamento del minimo di velocità fra i giri", "apici (m)"], tab_c)
    righe += ["", "Le curve «trovate» sono i minimi di velocità abbastanza profondi (15 km/h): "
                  "le curve in pieno o le esse percorse come una sola frenata non compaiono, "
                  "quindi il numero è atteso minore o uguale a quello del catalogo."]

    # ── D · gomme e freni ────────────────────────────────────────────────────
    p_min, p_max = rif.finestra_pressione_asciutto()
    tab_d = []
    for p, reg, bundle, canali in convertiti:
        maschera = np.zeros(canali[POSIZIONE].size, dtype=bool)
        for g in dividi_in_giri(canali):
            if g.completo:
                maschera[g.inizio:g.fine] = True
        pressioni = [canali[f"physics.wheelPressure.{r}"][maschera] for r in RUOTE]
        dentro = [float(np.mean((x >= p_min) & (x <= p_max))) for x in pressioni]
        freni = [float(canali[f"physics.brakeTemp.{r}"][maschera].max()) for r in RUOTE]
        tab_d.append([p.name, " / ".join(f"{float(x.mean()):.2f}" for x in pressioni),
                      " / ".join(f"{d:.0%}" for d in dentro),
                      f"{max(freni[:2]):.0f} / {max(freni[2:]):.0f}"])
    righe += ["", "## D · Gomme e freni sui giri veri", "",
              f"Finestra Kunos asciutto {p_min}-{p_max} psi. Freni: picco anteriore / posteriore "
              "(riferimento community da confermare: 650/450 °C consigliati, 700/500 picco).", ""]
    righe += _tabella(["file", "pressione media FL/FR/RL/RR (psi)", "tempo in finestra",
                       "picco freni ant/post (°C)"], tab_d)

    # ── E · setup ────────────────────────────────────────────────────────────
    setups = sorted(args.cartella.rglob("*.json"))
    tab_e = []
    for s in setups:
        try:
            st = leggi_setup_acc(s.read_bytes())
        except SetupAccError as e:
            tab_e.append([s.name, "ERRORE", str(e), "", ""])
            continue
        reali, totali = st.quanti_verificati()
        strategia = (st.raw.get("basicSetup") or {}).get("strategy") or {}
        tab_e.append([s.name, st.car, f"{reali}/{totali}",
                      f"{float(strategia.get('fuelPerLap', 0)):.2f}", len(st.assunzioni)])
    if tab_e:
        righe += ["", "## E · Setup JSON reali", ""]
        righe += _tabella(["file", "vettura", "parametri in unità reali", "fuelPerLap (l)",
                           "assunzioni"], tab_e)

    # ── F · motore ───────────────────────────────────────────────────────────
    righe += ["", "## F · Il motore sui giri veri", ""]
    crolli = 0
    for p, reg, bundle, canali in convertiti:
        try:
            report = analizza(bundle, canali)
        except Exception as e:  # noqa: BLE001
            crolli += 1
            righe.append(f"- `{p.name}`: **CROLLO** {type(e).__name__}: {e}")
            continue
        voci = "; ".join(v.titolo for v in report.verdetto[:3]) or "nessuna voce"
        righe.append(f"- `{p.name}` ({bundle.meta.car}, {bundle.meta.track}): {voci} · "
                     f"consumo {report.carburante.consumo_medio_l_giro or '—'} "
                     f"({report.carburante.fonte or 'nessuna fonte'})")
    if errori_conv:
        righe += ["", "Non convertiti:", *errori_conv]

    # ── G · non verificabile ─────────────────────────────────────────────────
    righe += ["", "## G · Non verificabile con questi file", "",
              "- **Degrado e costanza**: ogni file è un giro solo; servono stint di più giri.",
              "- **Consumo misurato**: MoTeC non esporta il carburante; qui c'è solo quello "
              "dichiarato nei setup.",
              "- **Settori**: non esportati da ACC in MoTeC.",
              "- **Temperatura al core**: `TYRE_TAIR` non è dichiarata come tale.",
              "- **Validità del giro e corsia box**: non esportate."]

    # ── H · scrittore ────────────────────────────────────────────────────────
    righe += ["", "## H · Lo scrittore di PitWall sui file veri", "",
              "Ogni export nativo (con i beacon) riletto e riscritto da `app/motec/scrittura.py`, "
              "poi confrontato byte per byte con l'originale.", ""]
    tab_h = []
    identici = 0
    nativi = [(p, reg) for p, reg in letti if reg.ldx and reg.ldx.beacon_s]
    for p, reg in nativi:
        ld = reg.ld
        canali_w = [CanaleDaScrivere(c.nome, c.unita, c.frequenza_hz, c.valori(), c.limite_alto,
                                     c.limite_basso, c.decimali_display) for c in ld.canali]
        nuovo_ld = scrivi_ld(canali_w, ld.vettura, ld.pista, ld.data_ora, ld.pilota,
                             ld.peso_vettura or 0)
        migliore = tempo_in_secondi(reg.ldx.tempo_migliore or "")
        nuovo_ldx = scrivi_ldx(reg.ldx.beacon_s,
                               int(round(migliore * 1000)) if migliore else None,
                               reg.ldx.giro_migliore, reg.ldx.primo_beacon)
        originale_ldx = p.with_suffix(".ldx").read_bytes()
        diversi = (sum(1 for a, b in zip(nuovo_ld, ld.contenuto) if a != b)
                   + abs(len(nuovo_ld) - len(ld.contenuto)))
        uguale = diversi == 0 and nuovo_ldx == originale_ldx
        identici += uguale
        tab_h.append([p.name, "sì" if diversi == 0 else f"NO ({diversi} byte)",
                      "sì" if nuovo_ldx == originale_ldx else "NO"])
    righe += _tabella(["file", ".ld identico", ".ldx identico"], tab_h)
    righe += ["", f"**{identici} su {len(nativi)} identici.** I file salvati da MoTeC i2 non si "
                  "confrontano: i2 li riscrive con un'impaginazione sua."]

    uscita.parent.mkdir(parents=True, exist_ok=True)
    uscita.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))
    print(f"\nResoconto scritto in {uscita}")
    return 1 if crolli else 0


if __name__ == "__main__":
    raise SystemExit(main())
