#!/usr/bin/env python3
"""
build_anchors_proof.py — genera il PROVINO DELLE ANCORE delle curve

Perche' esiste:
    Il motore trova le curve dai minimi di velocita' e le numera da se': la sua
    «curva 4» non e' la T4 della guida (a Monza trova 6 minimi per 11 curve, a
    Zandvoort su un giro solo 10, 8 o 9 curve a seconda della sessione). Per
    agganciare la guida al verdetto serve sapere, una volta per pista, DOVE sta
    ogni curva della guida sul giro e sulla mappa. Nessuna euristica lo sa con
    certezza: lo decide Edoardo guardando il profilo, come per foto e mappe.

    Per ogni curva della guida si fissano (schema 2, dal 28/09/2026):
      - INIZIO: il punto di frenata, o l'inserimento se la curva e' in pieno —
        e' il clic di Edoardo, e vale esattamente dove clicca (niente aggancio
        automatico: nel primo provino spostava i suoi clic sul picco vicino);
      - APICE e USCITA: calcolati dalla telemetria, correggibili (Maiusc+clic,
        Alt+clic);
      - il punto sulla MAPPA verificata (serve allo zoom nell'aggancio in sessione).

    La proposta automatica viene da `app/analisi/eventi_curva` (curve dal carico
    laterale, frenata attribuita camminando all'indietro dall'apice). Le BOZZE di
    Edoardo (`%LOCALAPPDATA%\\PitWall\\ancore_bozze\\bozza_<id>.json`) si caricano
    sopra la proposta: quello che ha cliccato lui resta suo.

    Export: «Esporta ancore» (solo a lavoro completo) → `anchors_choice_<id>.json`,
    da passare ad `apply_anchors.py`; «Esporta bozza» (sempre) → `anchors_bozza_<id>.json`,
    da copiare nella cartella delle bozze per ripartire da li'.

Uso (dalla radice del repo, col Python del backend):
    backend/.venv/Scripts/python backend/scripts/build_anchors_proof.py
    backend/.venv/Scripts/python backend/scripts/build_anchors_proof.py --piste monza

    poi apri  http://localhost:3000/assets/_provino_ancore.html  (serve `npm run dev`)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_BACKEND = _ROOT / "backend"
sys.path.insert(0, str(_BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_BACKEND / ".env")     # PITWALL_SESSIONS_DIR: l'archivio sta fuori dal repo

import numpy as np  # noqa: E402

from app.analisi.curve import FRENO, GAS, MARCIA, VELOCITA, CurveNonCalcolabili  # noqa: E402
from app.analisi.eventi_curva import (  # noqa: E402
    SEGNO_DESTRA, SOGLIA_LOBO, come_json, g_lisciato, giro_migliore, profilo, proponi,
    trova_eventi,
)
from app.core import catalog as cat  # noqa: E402
from app.telemetria.registratore import cartella_telemetria, leggi_canali  # noqa: E402

OUT_DIR = _ROOT / "frontend" / "public" / "assets"
MAPPE_DIR = OUT_DIR / "tracks"
USCITA = OUT_DIR / "_provino_ancore.html"
BOZZE_DEFAULT = Path(os.path.expandvars(r"%LOCALAPPDATA%")) / "PitWall" / "ancore_bozze"

# Piste tenute fuori apposta, col motivo (decisioni di Edoardo).
RIMANDATE = {
    "spa_francorchamps": "numerazione secondo Coach Dave da rifare prima di ancorare (28/09/2026)",
}


def sessioni_di(pista: str) -> list[Path]:
    """Le cartelle di telemetria della pista, demo esclusa."""
    fuori = []
    for cartella in sorted(cartella_telemetria().iterdir()):
        meta_file = cartella / "sessione.json"
        if not (cartella / "canali.npz").exists() or not meta_file.exists():
            continue
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if meta.get("pista") == pista and not meta.get("demo"):
            fuori.append(cartella)
    return fuori


def _arrotonda(serie: np.ndarray, cifre: int = 2) -> list[float]:
    return [round(float(v), cifre) for v in serie]


def dati_pista(pista: str, bozze: Path) -> dict | None:
    track = next((t for t in cat.all_tracks() if t.get("id") == pista), None)
    guida = cat.track_guide(pista)
    mappa = ((track or {}).get("assets") or {}).get("map") or {}
    file_mappa = sorted(MAPPE_DIR.glob(f"{pista}_map.*"))
    if not track or not guida or mappa.get("status") != "verificata" or not file_mappa:
        print(f"  {pista}: salto (serve guida + mappa verificata a disco)")
        return None

    cartelle = sessioni_di(pista)
    if not cartelle:
        print(f"  {pista}: salto (nessuna sessione registrata)")
        return None
    profili = []
    for cartella in cartelle:
        meta = json.loads((cartella / "sessione.json").read_text(encoding="utf-8"))
        canali = leggi_canali(cartella)
        try:
            prof = profilo(canali, giro_migliore(canali))
        except CurveNonCalcolabili as e:
            print(f"  {pista}: {cartella.name} scartata ({e})")
            continue
        profili.append((cartella.name, meta, prof))
    if not profili:
        print(f"  {pista}: salto (nessuna sessione con un giro completo fuori dai box)")
        return None

    # la bozza di Edoardo decide la sessione di origine (le sue posizioni valgono su
    # QUEL giro); senza bozza, l'origine e' il giro piu' veloce fra le sessioni
    bozza = None
    file_bozza = bozze / f"bozza_{pista}.json"
    if file_bozza.exists():
        bozza = json.loads(file_bozza.read_text(encoding="utf-8"))
    profili.sort(key=lambda p: p[2]["tempo_ms"] or 10**9)
    if bozza and bozza.get("sessione_origine"):
        scelta = [p for p in profili if p[0] == bozza["sessione_origine"]]
        if not scelta:
            sys.exit(f"{pista}: la bozza e' stata fatta su {bozza['sessione_origine']}, "
                     f"che non e' piu' nell'archivio")
        profili.remove(scelta[0])
        profili.insert(0, scelta[0])
    nome, meta, prof = profili[0]
    serie = prof["serie"]
    eventi = trova_eventi(prof)
    curve = guida.get("curve") or []
    proposta = proponi(curve, eventi)
    g_liscio, scala = g_lisciato(prof)

    print(f"  {pista}: origine {nome} (giro {prof['giro']}, {prof['tempo_ms']/1000:.3f} s), "
          f"{len(eventi)} curve nel giro, {sum(1 for p in proposta if p['inizio'] is not None)}/"
          f"{len(curve)} proposte, {sum(1 for p in proposta if p['avviso'])} avvisi"
          + (f", bozza caricata ({file_bozza.name})" if bozza else ""))
    return {
        "id": pista,
        "nome": track.get("name", pista),
        "mappa_url": f"/assets/tracks/{file_mappa[0].name}",
        "mappa_commons": mappa.get("commons_file"),
        "curve": [{"n": c.get("n"), "nome": c.get("nome"), "direzione": c.get("direzione"),
                   "tipo": c.get("tipo")} for c in curve],
        "origine": {"sessione": nome, "vettura": meta.get("vettura"), "giro": prof["giro"],
                    "tempo_ms": prof["tempo_ms"]},
        "punti": prof["punti"],
        "velocita": _arrotonda(serie[VELOCITA], 1),
        "freno": _arrotonda(serie[FRENO]) if FRENO in serie else None,
        "gas": _arrotonda(serie[GAS]) if GAS in serie else None,
        "marcia": _arrotonda(serie[MARCIA], 0) if MARCIA in serie else None,
        "g_lat": _arrotonda(g_liscio) if g_liscio is not None else None,
        "g_scala": scala,
        "soglia_lobo": SOGLIA_LOBO,
        "segno_destra": SEGNO_DESTRA,
        "altre": [{"sessione": n, "tempo_ms": p["tempo_ms"],
                   "velocita": _arrotonda(p["serie"][VELOCITA], 1)} for n, _m, p in profili[1:]],
        "eventi": come_json(eventi),
        "proposta": proposta,
        "bozza": bozza,
    }


# ---------------------------------------------------------------- HTML

_CSS = """
:root{
  --bg:#0a0a0a; --panel:#111; --panel2:#1a1a1a; --line:#262626;
  --txt:#e8e8e8; --dim:#8a8a8a; --acc:#E8002D; --ok:#00C853; --warn:#FFB300;
  --placca:#f4f1e8; --dx:#4FC3F7; --sx:#FF8A65; --tua:#00C853; --prop:#E8002D;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);
     font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}
header{position:sticky;top:0;z-index:5;display:flex;gap:10px;align-items:center;flex-wrap:wrap;
       padding:10px 18px;background:#0d0d0d;border-bottom:1px solid var(--line)}
header h1{font-size:16px;margin:0;letter-spacing:.3px}
header h1 span{color:var(--acc)}
select,button{background:var(--panel2);color:var(--txt);border:1px solid var(--line);
       border-radius:6px;padding:6px 10px;font:inherit;cursor:pointer}
button.primary{background:var(--acc);border-color:var(--acc);color:#fff}
button:disabled{opacity:.4;cursor:not-allowed}
.stat{color:var(--dim)} .stat b{color:var(--txt)}
#manca{color:var(--warn);font-size:12px;flex-basis:100%}
main{padding:14px 18px}
.note{color:var(--dim);max-width:1250px;margin:0 0 12px}
.note kbd{background:#222;border:1px solid #333;border-radius:3px;padding:0 4px;color:var(--txt)}
.grid{display:grid;grid-template-columns:minmax(0,1fr) 500px;gap:16px;align-items:start}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:6px;background:#0c0c0c}
svg text{font:11px sans-serif;fill:var(--dim)}
.zoom{display:flex;gap:6px;align-items:center;margin-bottom:8px;flex-wrap:wrap}
.zoom button.on{border-color:var(--acc);color:#fff}
.placca{background:var(--placca);border-radius:6px;padding:10px}
.vista{position:relative;overflow:hidden;cursor:crosshair;touch-action:none;margin:0 auto}
.vista.trascina{cursor:grabbing}
.tela{position:relative;transform-origin:0 0}
.tela img{width:100%;height:auto;display:block;user-select:none;-webkit-user-drag:none;pointer-events:none}
.pin{position:absolute;width:22px;height:22px;border-radius:50%;
     transform:translate(-50%,-50%) scale(var(--inv,1));
     background:var(--acc);color:#fff;font:bold 11px/22px sans-serif;text-align:center;
     pointer-events:none;box-shadow:0 0 0 2px #fff}
.pin.sel{background:#111;box-shadow:0 0 0 3px var(--warn)}
.mapbar{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-bottom:6px;font-size:12px}
.mapbar .stat{margin-left:auto}
#mapSel{font-size:13px;margin-bottom:6px}
#pannelloMappa{position:sticky;top:96px}
#pannelloMappa.grande{position:fixed;inset:10px;z-index:50;overflow:auto;background:#111}
table{width:100%;border-collapse:collapse;margin-top:12px}
th,td{padding:5px 6px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:500;font-size:12px}
tr{cursor:pointer} tr.sel{background:#1f1a10}
td.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.dx{color:var(--dx)} .sx{color:var(--sx)}
.badge{display:inline-block;padding:0 6px;border-radius:4px;font-size:11px;border:1px solid var(--line);white-space:nowrap}
.b-tua{color:var(--tua);border-color:var(--tua)} .b-conf{color:var(--ok);border-color:var(--ok)}
.b-prop{color:var(--warn);border-color:var(--warn)} .b-ric{color:#ff5a5a;border-color:#ff5a5a}
.b-no{color:var(--dim)} .avv{color:var(--warn);font-size:12px}
.legenda{color:var(--dim);font-size:12px;margin-top:6px}
.sel-info{margin-top:8px;font-size:13px}
"""

_JS = r"""
const DATI = __DATI__;
const $ = s => document.querySelector(s);
const CHIAVE = id => "pw_ancore2_" + id;       // schema 2: la chiave del primo provino resta intatta
let pista = DATI[0].id, sel = 1, zoom = 2;
const stato = {};

function D(){ return DATI.find(d => d.id === pista); }
const r4 = x => Math.round(x * 10000) / 10000;
const avanti = (da, a) => ((a - da) % 1 + 1) % 1;        // distanza sul giro da `da` ad `a`

// la prima curva del giro il cui apice viene dopo `x`: da lì si prendono apice e uscita
function curvaDopo(d, x){
  let meglio = null;
  for(const e of d.eventi){
    const dist = avanti(x, e.apice);
    if(dist <= 0.25 && (!meglio || dist < meglio.dist)) meglio = {dist, e};
  }
  return meglio ? meglio.e : null;
}

function daProposta(p){
  return {inizio: p.inizio, metodo_inizio: p.metodo_inizio, apice: p.apice, metodo_apice: p.metodo_apice,
          uscita: p.uscita, metodo_uscita: p.uscita != null ? "carico" : null,
          mappa: null, stato: p.inizio != null ? "proposta" : "vuota"};
}

function statoIniziale(d){
  const s = {};
  for(const p of d.proposta) s[p.n] = daProposta(p);
  for(const b of (d.bozza && d.bozza.ancore) || []){
    const a = s[b.n] || (s[b.n] = daProposta({}));
    if(b.stato === "tua" || b.stato === "confermata"){
      if(b.inizio != null){
        a.inizio = b.inizio; a.metodo_inizio = b.metodo_inizio || "click";
        const e = curvaDopo(d, b.inizio);
        if(e){ a.apice = e.apice; a.metodo_apice = e.metodo_apice; a.uscita = e.uscita; a.metodo_uscita = "carico"; }
      }
      for(const f of ["apice", "uscita"]) if(b[f] != null){ a[f] = b[f]; a["metodo_" + f] = b["metodo_" + f] || "click"; }
      a.stato = b.stato;
    } else if(b.stato === "da_riconfermare"){
      a.stato = "da_riconfermare"; a.vecchio = b.valore_vecchio; a.nota = b.nota;
    }
    if(b.mappa) a.mappa = b.mappa;
  }
  return s;
}
function carica(d){
  let s = null;
  try { s = JSON.parse(localStorage.getItem(CHIAVE(d.id)) || "null"); } catch(e) {}
  stato[d.id] = s || statoIniziale(d);
}
function salva(){ try { localStorage.setItem(CHIAVE(pista), JSON.stringify(stato[pista])); } catch(e) {} }
DATI.forEach(carica);

function gA(d, pos){
  if(!d.g_lat || pos == null) return null;
  return d.g_lat[Math.round(pos * d.punti) % d.punti];
}
function sensoMisurato(d, pos){
  const g = gA(d, pos); if(g == null) return null;
  if(Math.abs(g) < d.soglia_lobo * d.g_scala) return {senso: "debole", g};
  return {senso: Math.sign(g) === d.segno_destra ? "destra" : "sinistra", g};
}
const completa = a => a && (a.stato === "tua" || a.stato === "confermata")
                        && a.inizio != null && a.apice != null && a.uscita != null && a.mappa;

// ── il profilo ─────────────────────────────────────────────────────────────
const H_V = 230, H_P = 46, H_G = 120, H_M = 44, GAP = 16, PAD_L = 48;
function disegnaProfilo(){
  const d = D(), s = stato[d.id];
  const W = Math.round(($(".scroll").clientWidth - 2) * zoom);
  const y0P = H_V + GAP, y0G = y0P + H_P + GAP, y0M = y0G + H_G + GAP;
  const H = y0M + H_M + 22;
  const X = p => PAD_L + p * (W - PAD_L - 10);
  const n = d.punti;
  const vMax = Math.max(...d.velocita, ...d.altre.flatMap(a => a.velocita)) * 1.05;
  const yV = v => 10 + (1 - v / vMax) * (H_V - 10);
  const gMax = d.g_lat ? Math.max(...d.g_lat.map(Math.abs)) * 1.1 : 1;
  const yG = g => y0G + H_G / 2 - (g / gMax) * (H_G / 2);
  const yP = v => y0P + H_P - v * H_P;
  const yM = m => y0M + H_M - (m / 7) * H_M;
  const linea = (arr, y) => arr.map((v, i) => (i ? "L" : "M") + X(i / n).toFixed(1) + " " + y(v).toFixed(1)).join("");
  let svg = `<svg width="${W}" height="${H}" id="prof">`;
  // la curva selezionata: fascia da inizio a uscita
  const a0 = s[sel];
  if(a0 && a0.inizio != null && a0.uscita != null){
    const fascia = (p, q) => `<rect x="${X(p)}" y="0" width="${Math.max(1, X(q) - X(p))}" height="${H-20}" fill="rgba(255,179,0,.08)"/>`;
    svg += a0.uscita >= a0.inizio ? fascia(a0.inizio, a0.uscita) : fascia(a0.inizio, 1) + fascia(0, a0.uscita);
  }
  for(let k = 0; k <= 20; k++){
    const x = X(k / 20);
    svg += `<line x1="${x}" x2="${x}" y1="0" y2="${H-20}" stroke="${k % 2 ? "#141414" : "#1e1e1e"}"/>`;
    if(k % 2 === 0) svg += `<text x="${x-8}" y="${H-5}">${(k/20).toFixed(1)}</text>`;
  }
  for(const v of [100, 200, 300]) if(v < vMax) svg += `<text x="4" y="${yV(v)+4}">${v} km/h</text><line x1="${PAD_L}" x2="${W}" y1="${yV(v)}" y2="${yV(v)}" stroke="#1c1c1c"/>`;
  for(const a of d.altre) svg += `<path d="${linea(a.velocita, yV)}" fill="none" stroke="#555" stroke-width="1"/>`;
  svg += `<path d="${linea(d.velocita, yV)}" fill="none" stroke="#e8e8e8" stroke-width="1.4"/>`;
  // pedali
  svg += `<text x="4" y="${y0P+12}">pedali</text>`;
  if(d.freno) svg += `<path d="${linea(d.freno, yP)}" fill="none" stroke="#E8002D" stroke-width="1.2"/>`;
  if(d.gas) svg += `<path d="${linea(d.gas, yP)}" fill="none" stroke="#00C853" stroke-width="1"/>`;
  // carico laterale
  svg += `<text x="4" y="${y0G+12}">G lat</text><line x1="${PAD_L}" x2="${W}" y1="${yG(0)}" y2="${yG(0)}" stroke="#333"/>`;
  if(d.g_lat){
    const soglia = d.soglia_lobo * d.g_scala;
    for(const q of [soglia, -soglia]) svg += `<line x1="${PAD_L}" x2="${W}" y1="${yG(q)}" y2="${yG(q)}" stroke="#262626" stroke-dasharray="3 3"/>`;
    const dx = d.g_lat.map(g => Math.sign(g) === d.segno_destra ? g : 0);
    const sx = d.g_lat.map(g => Math.sign(g) === d.segno_destra ? 0 : g);
    svg += `<path d="${linea(dx, yG)}L${X(1)} ${yG(0)}L${X(0)} ${yG(0)}Z" fill="rgba(79,195,247,.35)"/>`;
    svg += `<path d="${linea(sx, yG)}L${X(1)} ${yG(0)}L${X(0)} ${yG(0)}Z" fill="rgba(255,138,101,.35)"/>`;
    svg += `<path d="${linea(d.g_lat, yG)}" fill="none" stroke="#bbb" stroke-width="1"/>`;
  } else {
    svg += `<text x="${PAD_L+10}" y="${y0G+H_G/2}">accelerazione laterale assente in questa sessione</text>`;
  }
  if(d.marcia){
    svg += `<text x="4" y="${y0M+12}">marcia</text>`;
    svg += `<path d="${linea(d.marcia, yM)}" fill="none" stroke="#7CB342" stroke-width="1"/>`;
  }
  // le curve riconosciute nel giro: triangolo all'apice (colore = senso), tacca rossa alla frenata
  for(const e of d.eventi){
    const c = e.direzione === "destra" ? "#4FC3F7" : e.direzione === "sinistra" ? "#FF8A65" : "#888";
    svg += `<path d="M${X(e.apice)-4} ${y0G-3}L${X(e.apice)+4} ${y0G-3}L${X(e.apice)} ${y0G+4}Z" fill="${c}"/>`;
    if(e.frenata != null) svg += `<line x1="${X(e.frenata)}" x2="${X(e.frenata)}" y1="${y0P}" y2="${y0P+H_P}" stroke="#ff6b6b" stroke-width="2"/>`;
  }
  // le ancore
  for(const c of d.curve){
    const a = s[c.n]; if(!a) continue;
    const on = c.n === sel;
    const mia = a.stato === "tua" || a.stato === "confermata";
    const col = on ? "#FFB300" : mia ? "#00C853" : a.stato === "da_riconfermare" ? "#ff5a5a" : "#E8002D";
    if(a.vecchio != null && on){
      const xv = X(a.vecchio);
      svg += `<line x1="${xv}" x2="${xv}" y1="0" y2="${H-20}" stroke="#777" stroke-dasharray="1 3"/><text x="${xv+3}" y="${H-24}">prima</text>`;
    }
    if(a.inizio != null){
      const x = X(a.inizio);
      svg += `<line x1="${x}" x2="${x}" y1="0" y2="${H-20}" stroke="${col}" stroke-width="${on?2:1.2}" stroke-dasharray="${mia?"":"5 3"}"/>`;
      svg += `<text x="${x+3}" y="${on?24:12}" style="fill:${col};font-weight:bold">T${c.n}</text>`;
    }
    if(a.apice != null){
      const i = Math.round(a.apice * n) % n, x = X(a.apice), y = yV(d.velocita[i]);
      svg += `<path d="M${x} ${y-6}L${x+5} ${y}L${x} ${y+6}L${x-5} ${y}Z" fill="none" stroke="${col}" stroke-width="${on?2:1}"/>`;
    }
    if(a.uscita != null && on){
      const x = X(a.uscita);
      svg += `<line x1="${x}" x2="${x}" y1="0" y2="${H-20}" stroke="${col}" stroke-width="1" stroke-dasharray="2 4"/><text x="${x+3}" y="36" style="fill:${col}">uscita</text>`;
    }
  }
  svg += `</svg>`;
  $(".scroll").innerHTML = svg;
  $("#prof").addEventListener("click", ev => {
    const r = ev.currentTarget.getBoundingClientRect();
    const pos = (ev.clientX - r.left - PAD_L) / (W - PAD_L - 10);
    if(pos < 0 || pos >= 1) return;
    clicProfilo(r4(pos), ev.shiftKey ? "apice" : ev.altKey ? "uscita" : "inizio");
  });
}

function clicProfilo(pos, fase){
  const d = D(), s = stato[d.id];
  const a = s[sel] || (s[sel] = daProposta({}));
  if(fase === "inizio"){
    a.inizio = pos; a.metodo_inizio = "click";
    // apice e uscita seguono l'inizio, salvo che tu li abbia cliccati e stiano ancora dopo
    const e = curvaDopo(d, pos);
    if(!(a.metodo_apice === "click" && avanti(pos, a.apice) <= 0.25) && e){ a.apice = e.apice; a.metodo_apice = e.metodo_apice; }
    if(!(a.metodo_uscita === "click" && avanti(a.apice ?? pos, a.uscita) <= 0.25) && e){ a.uscita = e.uscita; a.metodo_uscita = "carico"; }
  } else {
    a[fase] = pos; a["metodo_" + fase] = "click";
  }
  a.stato = "tua"; delete a.vecchio;
  salva(); render();
}

// ── la mappa ───────────────────────────────────────────────────────────────
// Zoom e spostamento: rotella = zoom intorno al puntatore, trascinare = spostarsi,
// clic senza trascinare = punto della curva selezionata. Il punto si calcola sul
// rettangolo VERO dell'immagine (già trasformato), quindi resta una frazione della
// mappa intera qualunque sia lo zoom.
const mv = {k: 1, tx: 0, ty: 0};
let presa = null;
function vistaTela(){ return [$("#vista"), $("#tela")]; }
function limita(){
  const [vista, tela] = vistaTela();
  const W = vista.clientWidth, H = vista.clientHeight;
  mv.k = Math.min(16, Math.max(1, mv.k));
  mv.tx = Math.min(0, Math.max(W - W * mv.k, mv.tx));
  mv.ty = Math.min(0, Math.max(H - H * mv.k, mv.ty));
}
function applica(){
  const [, tela] = vistaTela();
  limita();
  tela.style.transform = `translate(${mv.tx}px, ${mv.ty}px) scale(${mv.k})`;
  tela.style.setProperty("--inv", 1 / mv.k);
  $("#zoomMappa").textContent = `${mv.k.toFixed(1)}×`;
}
function zoomIntorno(fattore, cx, cy){
  const k2 = Math.min(16, Math.max(1, mv.k * fattore));
  mv.tx = cx - (cx - mv.tx) * (k2 / mv.k);
  mv.ty = cy - (cy - mv.ty) * (k2 / mv.k);
  mv.k = k2; applica();
}
function adatta(){
  // la tela è larga quanto il pannello, ma mai più alta dello schermo
  const [vista, tela] = vistaTela();
  const img = tela.querySelector("img");
  if(!img || !img.naturalWidth) return;
  const box = $("#mappa").clientWidth - 20;
  const ri = img.getBoundingClientRect();
  const rapporto = ri.height / ri.width || 1;     // uguale a qualunque zoom
  const altezzaMax = window.innerHeight - ($("#pannelloMappa").classList.contains("grande") ? 120 : 260);
  const larghezza = Math.min(box, altezzaMax / rapporto);
  vista.style.width = tela.style.width = `${larghezza}px`;
  vista.style.height = `${larghezza * rapporto}px`;
  mv.k = 1; mv.tx = 0; mv.ty = 0; applica();
}
function mettiPunto(ev){
  const img = $("#tela img"), r = img.getBoundingClientRect();
  const x = (ev.clientX - r.left) / r.width, y = (ev.clientY - r.top) / r.height;
  if(x < 0 || x > 1 || y < 0 || y > 1) return;
  const a = stato[pista][sel] || (stato[pista][sel] = daProposta({}));
  a.mappa = {x: r4(x), y: r4(y)};
  salva();
  if($("#avanza").checked){
    const prossima = D().curve.find(c => c.n > sel && !(stato[pista][c.n] || {}).mappa);
    if(prossima) sel = prossima.n;
  }
  render();
}
function disegnaMappa(){
  const d = D(), s = stato[d.id];
  const box = $("#mappa");
  if(box.dataset.url !== d.mappa_url){
    box.dataset.url = d.mappa_url;
    box.innerHTML = `<div class="vista" id="vista"><div class="tela" id="tela"><img src="${d.mappa_url}" alt=""></div></div>`;
    $("#tela img").addEventListener("load", adatta);
    const vista = $("#vista");
    vista.addEventListener("wheel", ev => {
      ev.preventDefault();
      const r = vista.getBoundingClientRect();
      zoomIntorno(ev.deltaY < 0 ? 1.25 : 0.8, ev.clientX - r.left, ev.clientY - r.top);
    }, {passive: false});
    vista.addEventListener("pointerdown", ev => {
      if(ev.button !== 0) return;
      presa = {x: ev.clientX, y: ev.clientY, tx: mv.tx, ty: mv.ty, mosso: false};
      vista.setPointerCapture(ev.pointerId);
    });
    vista.addEventListener("pointermove", ev => {
      if(!presa) return;
      const dx = ev.clientX - presa.x, dy = ev.clientY - presa.y;
      if(!presa.mosso && Math.hypot(dx, dy) < 5) return;
      presa.mosso = true; vista.classList.add("trascina");
      mv.tx = presa.tx + dx; mv.ty = presa.ty + dy; applica();
    });
    vista.addEventListener("pointerup", ev => {
      if(!presa) return;
      const cliccato = !presa.mosso;
      presa = null; vista.classList.remove("trascina");
      if(cliccato) mettiPunto(ev);
    });
    mv.k = 1; mv.tx = 0; mv.ty = 0;
  }
  const tela = $("#tela");
  tela.querySelectorAll(".pin").forEach(p => p.remove());
  for(const c of d.curve){
    const a = s[c.n]; if(!a || !a.mappa) continue;
    const pin = document.createElement("div");
    pin.className = "pin" + (c.n === sel ? " sel" : "");
    pin.textContent = c.n;
    pin.style.left = `${a.mappa.x * 100}%`;
    pin.style.top = `${a.mappa.y * 100}%`;
    tela.appendChild(pin);
  }
  const c = d.curve.find(c => c.n === sel), a = s[sel] || {};
  $("#mapSel").innerHTML = c ? `Punto sulla mappa per <b>T${c.n}</b> ${c.nome ?? ""} ${a.mappa ? "— già messo (un altro clic lo sposta)" : "— da mettere"}` : "";
}

// ── la tabella ─────────────────────────────────────────────────────────────
const BADGE = {tua: ["b-tua", "tua"], confermata: ["b-conf", "confermata"], proposta: ["b-prop", "proposta"],
               da_riconfermare: ["b-ric", "da riconfermare"], vuota: ["b-no", "da cliccare"]};
function disegnaTabella(){
  const d = D(), s = stato[d.id];
  const cl = x => x === "destra" ? "dx" : x === "sinistra" ? "sx" : "";
  const f = (v, m) => v != null ? `${v.toFixed(4)}<br><span class="stat">${m ?? ""}</span>` : "—";
  let righe = "";
  for(const c of d.curve){
    const a = s[c.n] || {};
    const mis = sensoMisurato(d, a.apice);
    const avvisi = [];
    if(mis && c.direzione && mis.senso !== "debole" && mis.senso !== c.direzione)
      avvisi.push(`guida «${c.direzione}», all'apice il carico dice «${mis.senso}»`);
    if(mis && mis.senso === "debole") avvisi.push("carico laterale debole all'apice");
    if(a.stato === "da_riconfermare") avvisi.push(`prima avevi confermato ${a.vecchio} (${a.nota})`);
    const [bc, bt] = BADGE[a.stato] || BADGE.vuota;
    const conferma = (a.stato === "proposta" || a.stato === "da_riconfermare") && a.inizio != null;
    righe += `<tr data-n="${c.n}" class="${c.n === sel ? "sel" : ""}">
      <td><b>T${c.n}</b></td><td>${c.nome ?? "<i>senza nome</i>"}<br><span class="stat">${c.tipo ?? ""}</span></td>
      <td class="${cl(c.direzione)}">${c.direzione ?? "—"}</td>
      <td class="${cl(mis && mis.senso)}">${mis ? mis.senso + "<br><span class='stat'>" + mis.g.toFixed(2) + "</span>" : "—"}</td>
      <td class="num">${f(a.inizio, a.metodo_inizio)}</td><td class="num">${f(a.apice, a.metodo_apice)}</td>
      <td class="num">${f(a.uscita, a.metodo_uscita)}</td>
      <td><span class="badge ${bc}">${bt}</span></td><td>${a.mappa ? "✓" : "—"}</td>
      <td>${conferma ? `<button class="conf" data-n="${c.n}">Conferma</button>` : ""}
          <button class="azz" data-n="${c.n}">Proposta</button>
          ${avvisi.map(t => `<div class="avv">⚠ ${t}</div>`).join("")}</td></tr>`;
  }
  $("#tab").innerHTML = `<table><tr><th>curva</th><th>nome</th><th>senso guida</th><th>senso all'apice</th>
    <th>inizio</th><th>apice</th><th>uscita</th><th>stato</th><th>mappa</th><th></th></tr>${righe}</table>`;
}

function elenco(nn){ return nn.length ? nn.map(n => "T" + n).join(", ") : ""; }
function contatori(){
  const d = D(), s = stato[d.id];
  const fatte = d.curve.filter(c => completa(s[c.n])).length;
  $("#cDone").textContent = fatte; $("#cTot").textContent = d.curve.length;
  $("#btnExport").disabled = fatte !== d.curve.length;
  const daConf = d.curve.filter(c => !["tua", "confermata"].includes((s[c.n] || {}).stato)).map(c => c.n);
  const senzaMappa = d.curve.filter(c => !(s[c.n] || {}).mappa).map(c => c.n);
  const parti = [];
  if(daConf.length) parti.push(`da confermare o cliccare: ${elenco(daConf)}`);
  if(senzaMappa.length) parti.push(`punto sulla mappa mancante: ${elenco(senzaMappa)}`);
  $("#manca").textContent = parti.length ? "Per esportare le ancore mancano — " + parti.join(" · ") : "Tutto pronto: puoi esportare le ancore.";
  const o = d.origine;
  $("#origine").innerHTML = `Giro di origine: <b>${o.sessione}</b> · ${o.vettura ?? "vettura ?"} · giro ${o.giro} ·
    ${(o.tempo_ms/1000).toFixed(3)} s · altre sessioni in grigio: ${d.altre.length}` +
    (d.bozza ? ` · <b>bozza caricata</b>: ${d.bozza.ancore.filter(b => b.stato === "tua").length} curve tue` : "");
  const c = d.curve.find(c => c.n === sel), a = s[sel] || {};
  $("#selInfo").innerHTML = c ? `Selezionata: <b>T${c.n}</b> ${c.nome ?? ""} — clic = inizio · <kbd>Maiusc</kbd>+clic = apice · <kbd>Alt</kbd>+clic = uscita · clic sulla mappa = punto mappa` : "";
}

function render(){
  disegnaProfilo(); disegnaMappa(); disegnaTabella(); contatori();
  document.querySelectorAll(".zoom button[data-z]").forEach(b => b.classList.toggle("on", +b.dataset.z === zoom));
}

// ── export ─────────────────────────────────────────────────────────────────
function esporta(bozza){
  const d = D(), s = stato[d.id];
  const out = {
    _meta: {generato_da: "_provino_ancore.html", bozza,
            nota: bozza ? "Lavoro non finito: si ricarica copiandolo in %LOCALAPPDATA%\\PitWall\\ancore_bozze\\bozza_" + d.id + ".json"
                        : "Ancore complete, confermate a occhio curva per curva: da applicare con apply_anchors.py"},
    id: d.id, sessione_origine: d.origine.sessione, vettura: d.origine.vettura,
    giro: d.origine.giro, tempo_giro_ms: d.origine.tempo_ms, mappa_commons: d.mappa_commons,
    ancore: d.curve.map(c => {
      const a = s[c.n] || {};
      const g = gA(d, a.apice);
      const voce = {n: c.n, nome: c.nome, inizio: a.inizio ?? null, metodo_inizio: a.metodo_inizio ?? null,
                    apice: a.apice ?? null, metodo_apice: a.metodo_apice ?? null,
                    uscita: a.uscita ?? null, metodo_uscita: a.metodo_uscita ?? null,
                    g_lat: g == null ? null : Math.round(g * 100) / 100, mappa: a.mappa ?? null,
                    stato: a.stato ?? "vuota"};
      if(a.vecchio != null){ voce.valore_vecchio = a.vecchio; voce.nota = a.nota; }
      return voce;
    })
  };
  const blob = new Blob([JSON.stringify(out, null, 2)], {type: "application/json"});
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = bozza ? `anchors_bozza_${d.id}.json` : `anchors_choice_${d.id}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

// ── eventi della pagina ────────────────────────────────────────────────────
$("#pista").innerHTML = DATI.map(d => `<option value="${d.id}">${d.nome}</option>`).join("");
$("#pista").addEventListener("change", e => { pista = e.target.value; sel = 1; $("#mappa").dataset.url = ""; render(); });
document.querySelectorAll(".zoom button[data-z]").forEach(b => b.addEventListener("click", () => { zoom = +b.dataset.z; render(); }));
$("#tab").addEventListener("click", e => {
  const conf = e.target.closest(".conf"), azz = e.target.closest(".azz");
  if(conf){ const a = stato[pista][+conf.dataset.n]; a.stato = "confermata"; delete a.vecchio; salva(); render(); return; }
  if(azz){
    const n = +azz.dataset.n, p = D().proposta.find(p => p.n === n);
    const vecchia = stato[pista][n] || {};
    stato[pista][n] = {...daProposta(p), mappa: vecchia.mappa || null};
    salva(); render(); return;
  }
  const tr = e.target.closest("tr[data-n]");
  if(tr){ sel = +tr.dataset.n; render(); }
});
document.addEventListener("keydown", e => {
  const d = D();
  if(e.target.tagName === "SELECT") return;
  if(e.key === "ArrowDown" && sel < d.curve.length){ sel++; render(); e.preventDefault(); }
  if(e.key === "ArrowUp" && sel > 1){ sel--; render(); e.preventDefault(); }
});
$("#btnConfAll").addEventListener("click", () => {
  const d = D(), s = stato[d.id];
  for(const c of d.curve){
    const a = s[c.n]; if(!a || a.stato !== "proposta" || a.inizio == null) continue;
    const mis = sensoMisurato(d, a.apice);
    if(mis && c.direzione && mis.senso === c.direzione) a.stato = "confermata";
  }
  salva(); render();
});
$("#btnReset").addEventListener("click", () => {
  try { localStorage.removeItem(CHIAVE(pista)); } catch(e) {}
  stato[pista] = statoIniziale(D()); render();
});
$("#btnExport").addEventListener("click", () => esporta(false));
$("#btnBozza").addEventListener("click", () => esporta(true));
$("#mapPiu").addEventListener("click", () => { const v = $("#vista"); zoomIntorno(1.5, v.clientWidth / 2, v.clientHeight / 2); });
$("#mapMeno").addEventListener("click", () => { const v = $("#vista"); zoomIntorno(1 / 1.5, v.clientWidth / 2, v.clientHeight / 2); });
$("#mapAdatta").addEventListener("click", adatta);
function mappaGrande(accesa){
  const p = $("#pannelloMappa");
  p.classList.toggle("grande", accesa);
  $("#mapGrande").textContent = accesa ? "Chiudi mappa grande (Esc)" : "Mappa grande";
  requestAnimationFrame(adatta);
}
$("#mapGrande").addEventListener("click", () => mappaGrande(!$("#pannelloMappa").classList.contains("grande")));
document.addEventListener("keydown", e => { if(e.key === "Escape") mappaGrande(false); });
window.addEventListener("resize", () => { disegnaProfilo(); adatta(); });
render();
"""


def scrivi_html(dati: list[dict], bozze: Path) -> None:
    corpo = _JS.replace("__DATI__", json.dumps(dati, ensure_ascii=False))
    rimandate = "; ".join(f"<b>{k}</b>: {v}" for k, v in RIMANDATE.items())
    pagina = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>PitWall.AI — Provino ancore</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>PitWall<span>.</span>AI — Provino ancore</h1>
  <select id="pista"></select>
  <span class="stat">complete <b id="cDone">0</b> / <b id="cTot">0</b></span>
  <button id="btnConfAll">Conferma le proposte col senso giusto</button>
  <button id="btnReset">Ricarica bozza e proposte</button>
  <button id="btnBozza">Esporta bozza</button>
  <button class="primary" id="btnExport">Esporta ancore</button>
  <span id="manca"></span>
</header>
<main>
  <p class="note">
    Per ogni curva della guida: <b>inizio</b> (clic sul profilo: il punto di frenata, o l'inserimento se la
    curva si fa in pieno), <b>apice</b> e <b>uscita</b> (calcolati; <kbd>Maiusc</kbd>+clic e <kbd>Alt</kbd>+clic
    per correggerli) e il <b>punto sulla mappa</b> (clic sulla placca). Seleziona la curva nella tabella o con
    <kbd>↑</kbd> <kbd>↓</kbd>. Il clic vale <b>esattamente</b> dove clicchi.
    <br>Linee: <span style="color:#00C853">verde piena = tua o confermata</span> ·
    <span style="color:#E8002D">rossa tratteggiata = proposta</span> ·
    <span style="color:#ff5a5a">rosa = da riconfermare</span> · rombo = apice · gialla = selezionata (la fascia va
    da inizio a uscita). Nei pedali: <span style="color:#E8002D">freno</span>,
    <span style="color:#00C853">gas</span>, tacca rossa = punto di frenata trovato. Nel carico laterale:
    <span class="dx">azzurro = destra</span>, <span class="sx">arancio = sinistra</span>, triangoli = apici trovati.
    <br>Le tue correzioni del primo provino sono caricate dalla bozza: i punti che avevi <b>cliccato</b> sono
    tuoi; quelli che avevi solo confermato dalla proposta vecchia (che salvava l'apice) sono <b>da riconfermare</b>.
    <br>«Esporta bozza» salva il lavoro a metà: per ripartire da lì copialo in
    <code>{bozze}</code> come <code>bozza_&lt;pista&gt;.json</code>. Piste tenute fuori: {rimandate}.
  </p>
  <div class="grid">
    <div class="panel">
      <div class="zoom">zoom
        <button data-z="1">1×</button><button data-z="2">2×</button>
        <button data-z="4">4×</button><button data-z="8">8×</button>
      </div>
      <div class="scroll"></div>
      <div class="legenda" id="origine"></div>
      <div class="sel-info" id="selInfo"></div>
      <div id="tab"></div>
    </div>
    <div class="panel" id="pannelloMappa">
      <div class="mapbar">
        <button id="mapPiu">+</button><button id="mapMeno">−</button><button id="mapAdatta">Adatta</button>
        <button id="mapGrande">Mappa grande</button>
        <span class="stat">zoom <b id="zoomMappa">1.0×</b> · rotella = zoom · trascina = sposta · clic = punto</span>
      </div>
      <div id="mapSel"></div>
      <div class="placca" id="mappa"></div>
      <label class="legenda"><input type="checkbox" id="avanza" checked>
        dopo il clic sulla mappa passa alla curva successiva senza punto</label>
    </div>
  </div>
</main>
<script>{corpo}</script>
</body>
</html>
"""
    USCITA.parent.mkdir(parents=True, exist_ok=True)
    USCITA.write_text(pagina, encoding="utf-8")


def piste_idonee() -> list[str]:
    return [i for i in sorted(cat.track_ids_with_guide()) if i not in RIMANDATE]


def main() -> None:
    ap = argparse.ArgumentParser(description="Genera il provino delle ancore delle curve")
    ap.add_argument("--piste", nargs="*", help="solo queste piste (default: tutte le idonee)")
    ap.add_argument("--bozze", type=Path, default=BOZZE_DEFAULT,
                    help=f"cartella delle bozze di Edoardo (default {BOZZE_DEFAULT})")
    args = ap.parse_args()

    piste = args.piste or piste_idonee()
    print("Costruisco il provino delle ancore:")
    dati = [d for d in (dati_pista(p, args.bozze) for p in piste) if d]
    if not dati:
        sys.exit("nessuna pista idonea: servono guida, mappa verificata e un giro completo registrato")
    scrivi_html(dati, args.bozze)
    print(f"\nScritto {USCITA.relative_to(_ROOT)} — {len(dati)} piste")
    print("Apri:  http://localhost:3000/assets/_provino_ancore.html")


if __name__ == "__main__":
    main()
