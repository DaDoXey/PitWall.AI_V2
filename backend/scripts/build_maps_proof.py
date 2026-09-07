#!/usr/bin/env python3
"""
build_maps_proof.py — genera il PROVINO DELLE MAPPE dei circuiti

Perche' esiste:
    Stessa storia delle foto, un giro dopo. I 25 layout scaricati da
    fetch_assets.py sono stati scelti sul NOME DEL FILE, e il risultato e' che
    `spa` era il tracciato di rallycross, `imola` il 1992 pre-Tamburello,
    `kyalami` il 1968, `zandvoort` il 1989. Su un circuito la trappola e'
    persino peggiore che su una vettura: due layout dello stesso autodromo a
    trent'anni di distanza hanno lo stesso nome, lo stesso stile di disegno e
    la stessa dimensione del file, e differiscono per un tratto di pista. Non
    esiste euristica testuale che li separi: l'ultimo giudice deve essere un
    occhio umano che guarda il disegno.

    Da qui il provino: Claude Desktop (che ha la ricerca web) consegna
    `maps_candidates.json` — 3-5 candidati per pista, con prova e rischio
    scritti a parole, mai una scelta secca. Questo script li risolve contro
    l'API di Commons, li mette a schermo come immagini vere affiancate, e
    lascia scegliere a mano. Il suo export e' `maps_choice.json`, cioe' la lista
    dei layout GUARDATI UNO PER UNO.

Cosa aggiunge rispetto a quello che consegna Claude Desktop:
    1. Le IMMAGINI. Nel suo ambiente Commons non e' raggiungibile, quindi
       `url_file` arriva null ovunque e i candidati sono giudicati solo su
       titolo e categoria. Qui gli URL si risolvono davvero (`iiurlwidth`,
       lo stesso meccanismo che apply_photos.py usa per le foto).
    2. LICENZA e AUTORE, presi da `extmetadata`: nella consegna sono spesso
       null perche' non ha potuto aprire le pagine. Servono per i crediti.
    3. IL RESTO DELLA CATEGORIA. I suoi candidati sono un punto di partenza,
       non un recinto: la categoria vera di Commons viene letta per intero e i
       file che lui non ha elencato compaiono in fondo, ripiegati. Serve
       davvero: su Kyalami il report dava UN solo candidato moderno, la
       categoria ne contiene altri ("Kyalami 16.png", "Kyalami 2016.png").
    4. La PLACCA CHIARA. I file sono a tratto scuro su fondo trasparente: su
       tema scuro sarebbero illeggibili. Il provino li mostra gia' come li
       vedra' la UI, appoggiati su una placca avorio.

Uso:
    python backend/scripts/build_maps_proof.py
    python backend/scripts/build_maps_proof.py --candidati ~/Downloads/maps_candidates.json
    python backend/scripts/build_maps_proof.py --no-categoria   # solo i candidati proposti

    poi apri  http://localhost:3000/assets/_provino_mappe.html  (serve `npm run dev`)

L'export del provino e' `maps_choice.json`:
    id, titolo_file, image_url, source_page, license, author, width, height,
    format, note   +  _meta.senza_mappa (le piste lasciate apposta scoperte)

NON si chiama `maps.json`: quel nome e' gia' preso dal REGISTRO delle
attribuzioni dei layout (id, kind, role, source_page, license, author, sha1)
che apply_photos.py legge per scrivere ATTRIBUTIONS.md. Due file con lo stesso
nome e schema diverso avrebbero svuotato la pagina /crediti senza un errore —
esattamente la trappola gia' pagata una volta con la regex a 6 colonne.
`maps_choice.json` e' la SCELTA UMANA (il gemello di photos.json); `maps.json`
resta il registro rigenerato da chi porta i file a disco.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

# fetch_assets.py e' la casa degli helper di Commons (User-Agent che l'API
# pretende, throttling di cortesia, percorsi ancorati alla radice del repo).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_assets import OUT_DIR, _ROOT, api_get  # noqa: E402

_DATA_DIR = _ROOT / "backend" / "app" / "core" / "data"
CANDIDATI_DEFAULT = Path(__file__).resolve().parent / "maps_candidates.json"
USCITA = OUT_DIR / "_provino_mappe.html"

# Larghezza della miniatura chiesta a Commons. Le foto stavano bene a 1400 px
# perche' erano riquadri da 260 px in griglia; qui si giudica un TRACCIATO, e
# la differenza fra due layout puo' essere una singola chicane: la miniatura
# deve reggere l'ingrandimento a tutto schermo.
THUMB_WIDTH = 1000

# I titoli arrivano dentro un campo di prosa ("File:A.png / File:B.png",
# "File:X.png (redirect: File:Y.png)"): si estraggono tutti, si risolvono e si
# deduplicano sul titolo canonico restituito da Commons.
_TITOLO_RE = re.compile(r"File:[^/,()]+?\.(?:svg|png|jpe?g|gif)", re.I)

# Estensioni che quasi mai sono una planimetria: nella categoria "circuit maps"
# finiscono anche foto aeree e scansioni. Non si scartano (le guarda lui), ma
# si segnalano, perche' altrimenti fanno rumore in fondo alla lista.
_PROBABILE_FOTO = {".jpg", ".jpeg", ".gif"}


def _senza_tag(testo: str) -> str:
    """extmetadata restituisce autore e descrizione come frammenti HTML."""
    testo = re.sub(r"<[^>]+>", "", testo or "")
    return html.unescape(testo).strip()


def _pulisci_thumb(url: str) -> str:
    """Toglie i parametri utm_* che Commons appende alle miniature.

    Stessa ragione per cui apply_photos.py preferisce Special:FilePath: quei
    parametri finiscono nel file salvato e in ATTRIBUTIONS.md, dove non
    servono a nessuno.
    """
    return url.split("?", 1)[0] if url else url


def estrai_titoli(campo: str) -> list[str]:
    return [t.strip() for t in _TITOLO_RE.findall(campo or "")]


def info_file(titoli: list[str]) -> dict[str, dict]:
    """Risolve una lista di titoli in un colpo solo (l'API ne accetta 50).

    Restituisce una mappa titolo-richiesto -> dati, seguendo normalizzazioni e
    redirect: tre dei "candidati" di Zandvoort sono lo stesso file sotto nomi
    diversi, e senza questo passaggio comparirebbero tre volte.
    """
    fuori: dict[str, dict] = {}
    for i in range(0, len(titoli), 40):
        blocco = titoli[i:i + 40]
        d = api_get({
            "action": "query",
            "titles": "|".join(blocco),
            "redirects": 1,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|user|extmetadata",
            "iiurlwidth": THUMB_WIDTH,
        })
        q = d.get("query", {})
        alias = {r["from"]: r["to"] for r in q.get("normalized", [])}
        alias.update({r["from"]: r["to"] for r in q.get("redirects", [])})
        pagine = {p["title"]: p for p in q.get("pages", [])}

        for chiesto in blocco:
            canonico = chiesto
            # normalized e redirects possono concatenarsi (nome grezzo ->
            # normalizzato -> destinazione del redirect).
            for _ in range(3):
                if canonico in alias:
                    canonico = alias[canonico]
                else:
                    break
            p = pagine.get(canonico)
            if p is None or p.get("missing") or not p.get("imageinfo"):
                fuori[chiesto] = {"titolo": canonico, "mancante": True}
                continue
            ii = p["imageinfo"][0]
            em = ii.get("extmetadata", {})
            fuori[chiesto] = {
                "titolo": canonico,
                "mancante": False,
                "thumb": _pulisci_thumb(ii.get("thumburl") or ii.get("url", "")),
                "originale": ii.get("url", ""),
                "pagina": ii.get("descriptionurl", ""),
                "width": ii.get("width"),
                "height": ii.get("height"),
                "mime": ii.get("mime", ""),
                "licenza": _senza_tag(em.get("LicenseShortName", {}).get("value", "")),
                "autore": _senza_tag(em.get("Artist", {}).get("value", "")) or ii.get("user", ""),
                "descrizione": _senza_tag(em.get("ImageDescription", {}).get("value", ""))[:400],
            }
    return fuori


def categoria_di(titoli: list[str]) -> str | None:
    """La categoria "<circuito> circuit maps", chiesta ai file stessi.

    Le categorie scritte in tracks.json ("Category:Maps of ...") in gran parte
    NON esistono su Commons: erano indizi di ricerca, non nomi verificati. Un
    file che sappiamo esistere e' una fonte piu' affidabile di un nome dedotto.
    """
    if not titoli:
        return None
    d = api_get({"action": "query", "titles": "|".join(titoli[:10]),
                 "prop": "categories", "cllimit": "200"})
    conteggio: dict[str, int] = {}
    for p in d.get("query", {}).get("pages", []):
        for c in p.get("categories", []):
            nome = c["title"]
            if re.search(r"circuit maps$|^Category:Maps of ", nome, re.I):
                conteggio[nome] = conteggio.get(nome, 0) + 1
    if not conteggio:
        return None
    return max(conteggio, key=lambda k: conteggio[k])


def membri_categoria(categoria: str) -> list[str]:
    d = api_get({"action": "query", "list": "categorymembers",
                 "cmtitle": categoria, "cmtype": "file", "cmlimit": "200"})
    return [m["title"] for m in d.get("query", {}).get("categorymembers", [])]


def impronta_tracks() -> dict[str, dict]:
    """Lunghezza e numero di curve dal catalogo: e' il metro di paragone.

    Serve a schermo accanto ai candidati, perche' quasi tutti gli errori del
    giro precedente si sarebbero visti confrontando il disegno con questi due
    numeri.
    """
    dati = json.loads((_DATA_DIR / "tracks.json").read_text(encoding="utf-8"))
    return {t["id"]: t for t in dati}


def raccogli(candidati: dict, con_categoria: bool) -> list[dict]:
    tracks = impronta_tracks()
    fuori = []

    for circuito in candidati["circuiti"]:
        cid = circuito["id"]
        print(f"  {cid} ...", flush=True)

        proposti: list[tuple[str, dict]] = []   # (titolo, meta di Desktop)
        for cand in circuito["candidati"]:
            for titolo in estrai_titoli(cand["titolo_file"]):
                proposti.append((titolo, cand))

        info = info_file([t for t, _ in proposti])

        voci: list[dict] = []
        visti: set[str] = set()
        for titolo, cand in proposti:
            dato = info.get(titolo, {})
            canonico = dato.get("titolo", titolo)
            if canonico in visti:
                continue          # tre nomi, un file solo (Zandvoort)
            visti.add(canonico)
            voci.append({
                "titolo": canonico,
                "chiesto_come": titolo if titolo != canonico else None,
                "proposto": True,
                "mancante": dato.get("mancante", True),
                **{k: v for k, v in dato.items() if k not in ("titolo", "mancante")},
                "match": cand.get("corrisponde_ad_acc"),
                "anno": cand.get("anno"),
                "layout_dichiarato": cand.get("layout_dichiarato"),
                "prova": cand.get("prova"),
                "rischio": cand.get("rischio"),
                "licenza_desktop": cand.get("licenza"),
            })

        categoria = None
        if con_categoria:
            categoria = categoria_di([v["titolo"] for v in voci if not v["mancante"]])
            if categoria:
                altri = [t for t in membri_categoria(categoria) if t not in visti]
                info_altri = info_file(altri)
                for titolo in altri:
                    dato = info_altri.get(titolo, {})
                    if dato.get("mancante", True):
                        continue
                    est = Path(titolo).suffix.lower()
                    voci.append({
                        "titolo": dato["titolo"],
                        "chiesto_come": None,
                        "proposto": False,
                        "mancante": False,
                        **{k: v for k, v in dato.items() if k not in ("titolo", "mancante")},
                        "match": None,
                        "anno": None,
                        "layout_dichiarato": None,
                        "prova": None,
                        "rischio": ("Probabilmente una foto o una scansione, non una planimetria."
                                    if est in _PROBABILE_FOTO else None),
                        "licenza_desktop": None,
                    })

        t = tracks.get(cid, {})
        fuori.append({
            "id": cid,
            "nome": t.get("name", cid),
            "length_km": t.get("length_km"),
            "corners": t.get("corners"),
            "corners_confidence": t.get("corners_confidence"),
            "layout_da_cercare": circuito.get("layout_da_cercare"),
            "note": circuito.get("note"),
            "categoria": categoria,
            "candidati": voci,
        })
    return fuori


# ---------------------------------------------------------------- HTML

_CSS = """
:root{
  --bg:#0a0a0a; --panel:#111; --panel2:#1a1a1a; --line:#262626;
  --txt:#e8e8e8; --dim:#8a8a8a; --acc:#E8002D; --ok:#00C853; --warn:#FFB300;
  --placca:#f4f1e8;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);
     font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}
header{position:sticky;top:0;z-index:20;background:var(--panel);
       border-bottom:1px solid var(--line);padding:14px 20px;
       display:flex;gap:16px;align-items:center;flex-wrap:wrap}
h1{font-size:15px;margin:0;letter-spacing:.14em;text-transform:uppercase;font-weight:600}
h1 span{color:var(--acc)}
.stat{font-family:ui-monospace,"JetBrains Mono",monospace;font-size:12px;color:var(--dim)}
.stat b{color:var(--txt)}
button{background:var(--panel2);color:var(--txt);border:1px solid var(--line);
       padding:7px 14px;border-radius:3px;cursor:pointer;font-size:13px}
button:hover{border-color:var(--acc)}
button.primary{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:600}
main{padding:20px;max-width:1600px;margin:0 auto}
.note{color:var(--dim);font-size:12px;margin:0 0 16px;max-width:110ch}
.note b{color:var(--txt)}
.track{border:1px solid var(--line);background:var(--panel);border-radius:4px;
       margin-bottom:18px;overflow:hidden}
.thead{padding:12px 16px;display:flex;gap:14px;align-items:center;cursor:pointer;
       background:var(--panel2)}
.thead:hover{background:#1f1f1f}
.tid{font-family:ui-monospace,"JetBrains Mono",monospace;font-size:14px}
.tname{color:var(--dim);font-size:12px;flex:1}
.badge{font-size:10px;letter-spacing:.1em;text-transform:uppercase;
       padding:3px 8px;border-radius:2px;border:1px solid var(--line);color:var(--dim);
       white-space:nowrap}
.badge.done{color:var(--ok);border-color:var(--ok)}
.badge.none{color:var(--warn);border-color:var(--warn)}
.badge.trap{color:var(--acc);border-color:var(--acc)}
.badge.dubbio{color:var(--warn);border-color:var(--warn)}
.badge.extra{color:#6a8caf;border-color:#33475c}
.tbody{display:none;padding:16px;border-top:1px solid var(--line)}
.track.open .tbody{display:block}
.impronta{font-family:ui-monospace,monospace;font-size:12px;color:var(--dim);
          border:1px solid var(--line);border-radius:3px;padding:10px 12px;margin-bottom:12px}
.impronta b{color:var(--txt)}
.cerca{color:var(--txt);font-size:13px;margin:8px 0 4px}
.avviso{border-left:2px solid var(--warn);padding:8px 12px;margin:10px 0;
        color:var(--warn);font-size:12.5px;background:#1a1408}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px;margin-top:14px}
.card{border:2px solid var(--line);border-radius:3px;overflow:hidden;
      background:var(--panel2);transition:border-color .12s;display:flex;flex-direction:column}
.card:hover{border-color:#555}
.card.sel{border-color:var(--ok)}
.card.trap{border-color:#3a1119}
.plate{background:var(--placca);padding:10px;cursor:zoom-in;position:relative}
.plate img{width:100%;height:230px;object-fit:contain;display:block}
.plate .zoomhint{position:absolute;right:8px;bottom:8px;font-size:10px;color:#666;
                 background:#fff9;padding:2px 6px;border-radius:2px;pointer-events:none}
.body{padding:10px 11px;font-size:11.5px;color:var(--dim);line-height:1.5;flex:1;
      display:flex;flex-direction:column;gap:6px}
.body .tit{color:var(--txt);font-family:ui-monospace,monospace;font-size:11px;word-break:break-word}
.body .lic{font-family:ui-monospace,monospace;font-size:10.5px}
.body .prova{color:#b9c7b9}
.body .rischio{color:var(--warn)}
.body .rischio.grave{color:var(--acc)}
.pick{margin-top:auto;display:flex;gap:6px;padding-top:6px}
.pick button{flex:1;font-size:12px;padding:6px 8px}
.altri{margin-top:18px;border-top:1px dashed var(--line);padding-top:12px}
.altri>summary{cursor:pointer;color:var(--dim);font-size:12.5px;list-style:none}
.altri>summary:hover{color:var(--txt)}
.chosen{border:1px solid var(--ok);border-radius:3px;padding:10px 12px;margin-bottom:12px;
        background:#04140a;font-size:12.5px;display:flex;gap:12px;align-items:center}
.chosen img{width:120px;height:70px;object-fit:contain;background:var(--placca);
            border-radius:2px;padding:4px}
.chosen .info{flex:1;color:var(--dim)}
.chosen .info b{color:var(--txt)}
a{color:var(--acc)}
#lb{position:fixed;inset:0;background:#000d;z-index:50;display:none;
    align-items:center;justify-content:center;padding:28px;cursor:zoom-out}
#lb.on{display:flex}
#lb img{max-width:96vw;max-height:88vh;background:var(--placca);padding:16px;border-radius:3px}
#lb .cap{position:fixed;bottom:10px;left:0;right:0;text-align:center;color:var(--dim);
         font-size:12px;font-family:ui-monospace,monospace}
.track.hide{display:none}
select{background:var(--panel2);color:var(--txt);border:1px solid var(--line);
       padding:7px 10px;border-radius:3px;font-size:13px}
"""

_JS = r"""
const DATI = __DATI__;
const KEY = "pitwall_maps_choice_v1";
let scelte = {};
try { scelte = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch(e) { scelte = {}; }

// Le sezioni aperte sopravvivono al render: scegliere una carta ricostruisce
// la pagina, e senza questo insieme ogni click richiuderebbe tutto il resto.
const aperte = new Set();

const $ = s => document.querySelector(s);
const esc = s => (s==null?"":String(s)).replace(/[&<>"]/g, c =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

function salva(){ try{ localStorage.setItem(KEY, JSON.stringify(scelte)); }catch(e){} }

function conta(){
  const tot = DATI.length;
  const fatte = DATI.filter(t => scelte[t.id] && scelte[t.id].scelta === "file").length;
  const nulle = DATI.filter(t => scelte[t.id] && scelte[t.id].scelta === "nessuna").length;
  $("#cDone").textContent = fatte; $("#cTot").textContent = tot; $("#cNone").textContent = nulle;
}

function badgeMatch(c){
  if(c.match === "no")       return '<span class="badge trap">trappola</span>';
  if(c.match === "dubbio")   return '<span class="badge dubbio">dubbio</span>';
  if(c.match === "probabile")return '<span class="badge">probabile</span>';
  if(!c.proposto)            return '<span class="badge extra">dalla categoria</span>';
  return "";
}

function cardHTML(t, c, i){
  const sel = scelte[t.id] && scelte[t.id].titolo_file === c.titolo;
  const dim = c.width ? `${c.width}&times;${c.height}` : "";
  const fmt = (c.mime||"").split("/").pop().replace("svg+xml","svg");
  return `
  <div class="card ${sel?"sel":""} ${c.match==="no"?"trap":""}" data-t="${esc(t.id)}" data-i="${i}">
    <div class="plate" data-zoom="${esc(c.originale||c.thumb)}" data-cap="${esc(c.titolo)}">
      <img loading="lazy" src="${esc(c.thumb)}" alt="${esc(c.titolo)}">
      <span class="zoomhint">clicca per ingrandire</span>
    </div>
    <div class="body">
      <div>${badgeMatch(c)} ${c.anno?`<span class="badge">${esc(c.anno)}</span>`:""}</div>
      <div class="tit">${esc(c.titolo.replace(/^File:/,""))}</div>
      <div class="lic">${esc(fmt)} · ${dim} · ${esc(c.licenza||"licenza da leggere")}<br>
           ${esc((c.autore||"autore ignoto").slice(0,70))}</div>
      ${c.layout_dichiarato?`<div>Layout dichiarato: ${esc(c.layout_dichiarato)}</div>`:""}
      ${c.prova?`<div class="prova">${esc(c.prova)}</div>`:""}
      ${c.rischio?`<div class="rischio ${c.match==="no"?"grave":""}">${esc(c.rischio)}</div>`:""}
      <div class="pick">
        <button class="btnSel">${sel?"scelta ✓":"scegli questa"}</button>
        <a href="${esc(c.pagina)}" target="_blank" rel="noopener"><button>pagina</button></a>
      </div>
    </div>
  </div>`;
}

function chosenHTML(t){
  const s = scelte[t.id];
  if(!s) return "";
  if(s.scelta === "nessuna")
    return `<div class="chosen"><div class="info"><b>Nessuna adatta.</b>
      Il circuito resta senza mappa: meglio nessuna immagine che una sbagliata.</div>
      <button class="btnUndo">annulla</button></div>`;
  return `<div class="chosen"><img src="${esc(s.thumb)}" alt="">
    <div class="info"><b>${esc(s.titolo_file.replace(/^File:/,""))}</b><br>
    ${esc(s.license||"?")} · ${esc((s.author||"?").slice(0,60))}</div>
    <button class="btnUndo">annulla</button></div>`;
}

function render(){
  const filt = $("#filt").value;
  $("#list").innerHTML = DATI.map(t => {
    const fatta = !!scelte[t.id];
    const nascosta = (filt === "work" && fatta);
    const proposti = t.candidati.filter(c => c.proposto && !c.mancante);
    const extra    = t.candidati.filter(c => !c.proposto);
    const idxOf = c => t.candidati.indexOf(c);
    return `
    <div class="track ${nascosta?"hide":""} ${aperte.has(t.id)?"open":""}" data-t="${esc(t.id)}">
      <div class="thead">
        <span class="tid">${esc(t.id)}</span>
        <span class="tname">${esc(t.nome)}</span>
        ${fatta ? (scelte[t.id].scelta==="nessuna"
            ? '<span class="badge none">nessuna</span>'
            : '<span class="badge done">scelta</span>')
          : `<span class="badge">${proposti.length} proposti · ${extra.length} in categoria</span>`}
      </div>
      <div class="tbody">
        ${chosenHTML(t)}
        <div class="impronta">
          impronta catalogo: <b>${t.length_km} km</b> · <b>${t.corners} curve</b>
          (confidenza ${esc(t.corners_confidence)})
          ${t.categoria?`<br>categoria Commons: <b>${esc(t.categoria)}</b>`:""}
        </div>
        ${t.layout_da_cercare?`<div class="cerca"><b>Da cercare:</b> ${esc(t.layout_da_cercare)}</div>`:""}
        ${t.note?`<div class="avviso">${esc(t.note)}</div>`:""}
        <div class="grid">${proposti.map(c => cardHTML(t,c,idxOf(c))).join("")}</div>
        <div style="margin-top:14px">
          <button class="btnNone">Nessuna adatta per ${esc(t.id)}</button>
        </div>
        ${extra.length?`
        <details class="altri">
          <summary>Altri ${extra.length} file della categoria — non proposti da Claude Desktop</summary>
          <div class="grid">${extra.map(c => cardHTML(t,c,idxOf(c))).join("")}</div>
        </details>`:""}
      </div>
    </div>`;
  }).join("");
  conta();
}

document.addEventListener("click", e => {
  const plate = e.target.closest(".plate");
  if(plate){
    $("#lb img").src = plate.dataset.zoom;
    $("#lb .cap").textContent = plate.dataset.cap;
    $("#lb").classList.add("on");
    return;
  }
  if(e.target.closest("#lb")){ $("#lb").classList.remove("on"); return; }

  const head = e.target.closest(".thead");
  if(head){
    const box = head.parentElement;
    box.classList.toggle("open");
    if(box.classList.contains("open")) aperte.add(box.dataset.t);
    else aperte.delete(box.dataset.t);
    return;
  }

  const bSel = e.target.closest(".btnSel");
  if(bSel){
    const card = bSel.closest(".card");
    const t = DATI.find(x => x.id === card.dataset.t);
    const c = t.candidati[+card.dataset.i];
    scelte[t.id] = {
      id: t.id, scelta: "file", titolo_file: c.titolo,
      image_url: c.originale, thumb: c.thumb, source_page: c.pagina,
      license: c.licenza, author: c.autore,
      width: c.width, height: c.height,
      format: (c.mime||"").split("/").pop().replace("svg+xml","svg"),
      note: c.proposto ? "scelto a occhio nel provino (candidato Claude Desktop)"
                       : "scelto a occhio nel provino (pescato dalla categoria)"
    };
    aperte.add(t.id); salva(); render();
    return;
  }

  const bNone = e.target.closest(".btnNone");
  if(bNone){
    const t = bNone.closest(".track").dataset.t;
    scelte[t] = { id: t, scelta: "nessuna" };
    aperte.add(t); salva(); render();
    return;
  }

  const bUndo = e.target.closest(".btnUndo");
  if(bUndo){
    const t = bUndo.closest(".track").dataset.t;
    delete scelte[t]; aperte.add(t); salva(); render();
    return;
  }
});

document.addEventListener("keydown", e => {
  if(e.key === "Escape") $("#lb").classList.remove("on");
});

$("#filt").addEventListener("change", render);

$("#btnExport").addEventListener("click", () => {
  const voci = DATI.filter(t => scelte[t.id] && scelte[t.id].scelta === "file")
                   .map(t => { const s = {...scelte[t.id]}; delete s.thumb; delete s.scelta; return s; });
  const scartati = DATI.filter(t => scelte[t.id] && scelte[t.id].scelta === "nessuna").map(t => t.id);
  const out = {
    _meta: {
      generato_da: "_provino_mappe.html",
      nota: "Layout scelti guardando l'immagine, uno per uno. Le piste assenti da `mappe` sono assenti apposta: vedi `senza_mappa`.",
      senza_mappa: scartati
    },
    mappe: voci
  };
  const blob = new Blob([JSON.stringify(out, null, 2)], {type:"application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = "maps_choice.json"; a.click();
  URL.revokeObjectURL(a.href);
});

render();
"""


def scrivi_html(dati: list[dict]) -> None:
    corpo = _JS.replace("__DATI__", json.dumps(dati, ensure_ascii=False))
    n_cand = sum(len(t["candidati"]) for t in dati)
    pagina = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>PitWall.AI — Provino mappe</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>PitWall<span>.</span>AI — Provino mappe</h1>
  <span class="stat">scelte <b id="cDone">0</b> / <b id="cTot">0</b> ·
        senza mappa <b id="cNone">0</b></span>
  <select id="filt">
    <option value="all">Mostra tutte</option>
    <option value="work">Mostra solo da scegliere</option>
  </select>
  <button class="primary" id="btnExport">Esporta maps_choice.json</button>
</header>
<main>
  <p class="note">
    {n_cand} candidati risolti su Wikimedia Commons per {len(dati)} circuiti.
    Sotto ogni disegno c'e' quello che <b>Claude Desktop</b> ha scritto a parole
    (prova e rischio): l'ha giudicato senza vedere l'immagine, quindi vale come
    indizio, <b>non come verdetto</b>. Le carte marcate <span class="badge trap">trappola</span>
    sono elencate apposta perche' tu le riconosca e le scarti.
    <br>Confronta sempre il disegno con l'<b>impronta del catalogo</b> (km e numero di curve)
    scritta in cima. Clicca l'immagine per ingrandirla a tutto schermo: fra due layout
    dello stesso autodromo la differenza puo' essere una singola chicane.
    <br>Le mappe sono a tratto scuro: qui stanno su <b>placca avorio</b>, come le vedrai
    nella scheda del circuito. Se nessuna va bene usa <i>Nessuna adatta</i> — il circuito
    resta senza mappa, che e' sempre meglio di una mappa falsa.
    <br>Le scelte restano nel browser (localStorage): puoi chiudere e riprendere.
  </p>
  <div id="list"></div>
</main>
<div id="lb"><img alt=""><div class="cap"></div></div>
<script>{corpo}</script>
</body>
</html>
"""
    USCITA.parent.mkdir(parents=True, exist_ok=True)
    USCITA.write_text(pagina, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Genera il provino delle mappe dei circuiti")
    ap.add_argument("--candidati", type=Path, default=CANDIDATI_DEFAULT,
                    help="consegna di Claude Desktop (default: backend/scripts/maps_candidates.json)")
    ap.add_argument("--no-categoria", action="store_true",
                    help="non pescare gli altri file della categoria Commons")
    args = ap.parse_args()

    if not args.candidati.exists():
        sys.exit(f"manca {args.candidati}")

    candidati = json.loads(args.candidati.read_text(encoding="utf-8"))
    print(f"Risolvo i candidati su Commons ({args.candidati.name}):")
    dati = raccogli(candidati, con_categoria=not args.no_categoria)

    mancanti = [(t["id"], c["titolo"]) for t in dati for c in t["candidati"] if c["mancante"]]
    if mancanti:
        print("\n  ATTENZIONE — titoli che su Commons non esistono:")
        for cid, tit in mancanti:
            print(f"    {cid}: {tit}")

    scrivi_html(dati)
    tot = sum(len(t["candidati"]) for t in dati)
    print(f"\nScritto {USCITA.relative_to(_ROOT)} — {tot} candidati su {len(dati)} circuiti")
    print("Apri:  http://localhost:3000/assets/_provino_mappe.html")


if __name__ == "__main__":
    main()
