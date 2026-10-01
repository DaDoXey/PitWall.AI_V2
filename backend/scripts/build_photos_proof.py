#!/usr/bin/env python3
"""
build_photos_proof.py — genera il PROVINO DELLE FOTO delle vetture senza foto

Perche' esiste:
    Le foto del Lotto 1 sono state scelte nel provino consegnato da Claude Desktop
    (`provino_foto_v3.html`), che non sta nel repo. Con il Lotto 2 (Entry #064, 23
    vetture: GT4, GT2, monomarca, TCX) serve di nuovo, e la regola non cambia: una
    foto la sceglie un occhio umano, mai il nome del file (era entrato un modellino
    BMW 1:32 al posto della M4 GT3). Questo script cerca i candidati su Wikimedia
    Commons e li mette a schermo come immagini; la scelta resta di Edoardo.

Cosa fa:
    per ogni vettura di `cars.json` che non ha una voce in `photos.json` (di default
    solo le classi del Lotto 2) interroga Commons — la categoria dichiarata in
    `assets.photo`, se esiste, e la ricerca libera con le chiavi qui sotto — e scrive
    una pagina con le miniature, la licenza e l'autore di ogni candidato. Entrano solo
    i file con una licenza accettata (`fetch_assets.LICENZE_OK`).

Uso (dalla radice del repo):
    python backend/scripts/build_photos_proof.py
    python backend/scripts/build_photos_proof.py --classi GT3      # le GT3 rimaste senza foto
    python backend/scripts/build_photos_proof.py --only porsche_935,ktm_xbow_gt2

    poi apri  http://localhost:3000/assets/_provino_foto_lotto2.html  (serve `npm run dev`)

L'export del provino e' `photos_lotto2.json`, con lo stesso schema di `photos.json`
(id, kind, image_url, source_page, license, author, width, descrizione_contenuto,
confidence, note): le sue voci si AGGIUNGONO a `photos.json`, poi `apply_photos.py`.
Le vetture marcate «Nessuna adatta» restano fuori: nessuna foto e' meglio di una falsa.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_assets import LICENZE_OK, OUT_DIR, _ROOT, api_get  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

_DATA_DIR = _ROOT / "backend" / "app" / "core" / "data"
PHOTOS = Path(__file__).resolve().parent / "photos.json"
USCITA = OUT_DIR / "_provino_foto_lotto2.html"

THUMB_WIDTH = 640          # miniatura del provino: basta per riconoscere la vettura
MAX_CANDIDATI = 30         # per vettura
CLASSI_DEFAULT = "GT4,GT2,GTC,TCX"

# Chiavi di ricerca in piu' rispetto a `assets.photo.commons_query`: su Commons la
# stessa vettura sta sotto nomi diversi (sigla del telaio, nome della serie).
RICERCHE: dict[str, list[str]] = {
    "alpine_a110_gt4": ["Alpine A110 GT4", "Alpine A110 GT4 racing"],
    "aston_martin_vantage_gt4": ["Aston Martin Vantage AMR GT4", "Aston Martin Vantage GT4 2019"],
    "audi_r8_lms_gt4": ["Audi R8 LMS GT4"],
    "bmw_m4_gt4": ["BMW M4 GT4", "BMW M4 GT4 F82"],
    "chevrolet_camaro_gt4r": ["Chevrolet Camaro GT4.R", "Camaro GT4"],
    "ginetta_g55_gt4": ["Ginetta G55 GT4", "Ginetta G55"],
    "ktm_xbow_gt4": ["KTM X-Bow GT4"],
    "maserati_granturismo_mc_gt4": ["Maserati GranTurismo MC GT4", "Maserati GT4"],
    "mclaren_570s_gt4": ["McLaren 570S GT4"],
    "mercedes_amg_gt4": ["Mercedes-AMG GT4"],
    "porsche_718_cayman_gt4_clubsport": ["Porsche 718 Cayman GT4 Clubsport", "Cayman GT4 Clubsport MR"],
    "porsche_911_gt3_cup_991": ["Porsche 911 GT3 Cup 991", "Porsche 991 GT3 Cup Carrera Cup"],
    "porsche_911_gt3_cup_992": ["Porsche 911 GT3 Cup 992", "Porsche 992 GT3 Cup Supercup"],
    "lamborghini_huracan_super_trofeo": ["Lamborghini Huracán Super Trofeo", "Huracan LP 620-2 Super Trofeo"],
    "lamborghini_huracan_super_trofeo_evo2": ["Lamborghini Huracán Super Trofeo EVO2", "Huracan Super Trofeo Evo2"],
    "ferrari_488_challenge_evo": ["Ferrari 488 Challenge Evo", "Ferrari 488 Challenge"],
    "bmw_m2_cs_racing": ["BMW M2 CS Racing", "BMW M2 Cup"],
    "audi_r8_lms_gt2": ["Audi R8 LMS GT2"],
    "ktm_xbow_gt2": ["KTM X-Bow GT2", "KTM X-Bow GTX"],
    "maserati_mc20_gt2": ["Maserati MC20 GT2", "Maserati GT2"],
    "mercedes_amg_gt2": ["Mercedes-AMG GT2"],
    "porsche_911_gt2_rs_clubsport_evo": ["Porsche 911 GT2 RS Clubsport", "Porsche 991 GT2 RS Clubsport"],
    "porsche_935": ["Porsche 935 2019", "Porsche 935 991"],
}


def _senza_tag(testo: str) -> str:
    # Commons a volte consegna i tag già codificati (&lt;a href…&gt;): prima si decodifica, poi si tolgono.
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(testo or ""))).strip()


def _licenza_ok(breve: str, codice: str) -> bool:
    breve = breve.lower().replace(" ", "-")
    return any(ok in codice.lower() or ok in breve for ok in LICENZE_OK)


def titoli_candidati(vettura: dict) -> list[str]:
    """Titoli 'File:…' da categoria e ricerca libera, senza doppioni, nell'ordine trovato."""
    titoli: list[str] = []
    foto = (vettura.get("assets") or {}).get("photo") or {}
    categoria = foto.get("commons_category")
    if categoria:
        try:
            d = api_get({"action": "query", "list": "categorymembers", "cmtitle": categoria,
                         "cmtype": "file", "cmlimit": "60"})
            titoli += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        except Exception as e:  # noqa: BLE001 — una categoria che non esiste non ferma il provino
            print(f"    categoria non risolta ({categoria}): {e}")
    ricerche = [foto.get("commons_query")] + RICERCHE.get(vettura["id"], [])
    for chiave in dict.fromkeys(r for r in ricerche if r):
        try:
            d = api_get({"action": "query", "list": "search", "srsearch": chiave,
                         "srnamespace": "6", "srlimit": "30"})
            titoli += [m["title"] for m in d.get("query", {}).get("search", [])]
        except Exception as e:  # noqa: BLE001
            print(f"    ricerca fallita ({chiave}): {e}")
    return [t for t in dict.fromkeys(titoli) if t.rsplit(".", 1)[-1].lower() in ("jpg", "jpeg", "png")]


def risolvi(titoli: list[str]) -> list[dict]:
    """Miniatura, licenza e autore di ogni titolo; fuori quelli senza licenza accettata."""
    fuori: list[dict] = []
    for i in range(0, len(titoli), 40):
        d = api_get({"action": "query", "titles": "|".join(titoli[i:i + 40]), "prop": "imageinfo",
                     "iiprop": "url|size|mime|user|extmetadata", "iiurlwidth": str(THUMB_WIDTH)})
        pagine = {p["title"]: p for p in d.get("query", {}).get("pages", [])}
        alias = {r["from"]: r["to"] for r in d.get("query", {}).get("normalized", [])}
        for titolo in titoli[i:i + 40]:
            p = pagine.get(alias.get(titolo, titolo))
            if not p or p.get("missing") or not p.get("imageinfo"):
                continue
            ii = p["imageinfo"][0]
            em = ii.get("extmetadata", {})
            licenza = _senza_tag(em.get("LicenseShortName", {}).get("value", ""))
            if not _licenza_ok(licenza, _senza_tag(em.get("License", {}).get("value", ""))):
                continue
            if (ii.get("width") or 0) < 1000:      # troppo piccola per la card da 1400 px
                continue
            fuori.append({
                "titolo": p["title"],
                "thumb": (ii.get("thumburl") or ii.get("url", "")).split("?", 1)[0],
                "image_url": ii.get("url", ""),
                "source_page": ii.get("descriptionurl", ""),
                "license": licenza,
                "author": _senza_tag(em.get("Artist", {}).get("value", "")) or ii.get("user", ""),
                "width": ii.get("width"),
                "height": ii.get("height"),
                "descrizione": _senza_tag(em.get("ImageDescription", {}).get("value", ""))[:300],
                "data": _senza_tag(em.get("DateTimeOriginal", {}).get("value", ""))[:40],
            })
    return fuori


_CSS = """
*{box-sizing:border-box}body{margin:0;background:#0b0b0c;color:#e8e8e8;font:14px/1.45 system-ui,Segoe UI,sans-serif}
header{position:sticky;top:0;z-index:5;display:flex;gap:16px;align-items:center;padding:12px 20px;background:#111;border-bottom:1px solid #2a2a2a}
h1{font-size:16px;margin:0;flex:1}h1 span{color:#e8002d}.stat{color:#9a9a9a}.stat b{color:#fff}
button,select{background:#1a1a1a;color:#e8e8e8;border:1px solid #333;border-radius:6px;padding:7px 12px;font:inherit;cursor:pointer}
button.primary{background:#e8002d;border-color:#e8002d;color:#fff;font-weight:600}
main{padding:18px 20px 80px;max-width:1500px;margin:0 auto}.note{color:#9a9a9a;max-width:1000px}
section{margin-top:26px;border-top:1px solid #2a2a2a;padding-top:14px}
section h2{font-size:17px;margin:0 0 2px}section .sub{color:#9a9a9a;font-size:12px;margin-bottom:10px}
.griglia{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.carta{background:#141414;border:2px solid #262626;border-radius:10px;overflow:hidden;cursor:pointer;display:flex;flex-direction:column}
.carta.scelta{border-color:#22c55e;box-shadow:0 0 0 2px #22c55e55}
.carta img{width:100%;aspect-ratio:3/2;object-fit:cover;background:#000;display:block}
.carta .t{padding:8px 10px;font-size:11.5px;color:#bdbdbd;word-break:break-word}
.carta .t b{display:block;color:#fff;font-weight:600;margin-bottom:3px}
.carta .t a{color:#7aa7ff}.riga{display:flex;gap:10px;align-items:center;margin-top:10px;flex-wrap:wrap}
.riga input[type=text]{flex:1;min-width:260px;background:#101010;border:1px solid #333;border-radius:6px;color:#fff;padding:7px 10px;font:inherit}
.nessuna.attiva{background:#7a1a1a;border-color:#a33}.fatto h2::after{content:" ✓";color:#22c55e}.senza h2::after{content:" — senza foto";color:#f59e0b}
#lb{position:fixed;inset:0;background:#000d;display:none;align-items:center;justify-content:center;z-index:20;cursor:zoom-out}
#lb img{max-width:96vw;max-height:92vh}
"""

_JS = r"""
const DATI = __DATI__;
const CHIAVE = "pw_provino_foto_lotto2";
let stato = {};
try { stato = JSON.parse(localStorage.getItem(CHIAVE) || "{}"); } catch (e) { stato = {}; }
const salva = () => { try { localStorage.setItem(CHIAVE, JSON.stringify(stato)); } catch (e) {} conta(); };
const lista = document.getElementById("list");
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function disegna() {
  const filtro = document.getElementById("filt").value;
  lista.innerHTML = "";
  for (const v of DATI) {
    const s = stato[v.id] || {};
    const fatto = s.scelta !== undefined && s.scelta !== null;
    if (filtro === "work" && (fatto || s.nessuna)) continue;
    const sez = document.createElement("section");
    sez.className = fatto ? "fatto" : s.nessuna ? "senza" : "";
    sez.innerHTML = `<h2>${esc(v.nome)}</h2><div class="sub">${esc(v.classe)} · ${esc(v.anno)} · ${v.candidati.length} candidati · <code>${esc(v.id)}</code></div>`;
    const g = document.createElement("div");
    g.className = "griglia";
    v.candidati.forEach((c, i) => {
      const carta = document.createElement("div");
      carta.className = "carta" + (s.scelta === i ? " scelta" : "");
      carta.innerHTML = `<img loading="lazy" src="${esc(c.thumb)}" alt="">
        <div class="t"><b>${esc(c.titolo.replace(/^File:/, ""))}</b>${esc(c.license)} · ${esc(c.author).slice(0, 60)} · ${c.width}×${c.height}${c.data ? " · " + esc(c.data) : ""}
        <br>${esc(c.descrizione).slice(0, 160)}<br><a href="${esc(c.source_page)}" target="_blank" rel="noopener">pagina su Commons</a> · <a href="#" data-zoom="${esc(c.thumb)}">ingrandisci</a></div>`;
      carta.addEventListener("click", (e) => {
        if (e.target.tagName === "A") {
          if (e.target.dataset.zoom) { e.preventDefault(); zoom(e.target.dataset.zoom); }
          return;
        }
        stato[v.id] = { ...(stato[v.id] || {}), scelta: s.scelta === i ? null : i, nessuna: false };
        salva(); disegna();
      });
      g.appendChild(carta);
    });
    sez.appendChild(g);
    const riga = document.createElement("div");
    riga.className = "riga";
    riga.innerHTML = `<button class="nessuna${s.nessuna ? " attiva" : ""}">Nessuna adatta</button>
      <input type="text" placeholder="Nota (facoltativa): cosa si vede, perché questa" value="${esc(s.nota || "")}">`;
    riga.querySelector("button").addEventListener("click", () => {
      stato[v.id] = { ...(stato[v.id] || {}), scelta: null, nessuna: !s.nessuna };
      salva(); disegna();
    });
    riga.querySelector("input").addEventListener("change", (e) => {
      stato[v.id] = { ...(stato[v.id] || {}), nota: e.target.value };
      salva();
    });
    sez.appendChild(riga);
    lista.appendChild(sez);
  }
  conta();
}

function conta() {
  const scelte = DATI.filter((v) => stato[v.id] && stato[v.id].scelta !== undefined && stato[v.id].scelta !== null).length;
  const senza = DATI.filter((v) => stato[v.id] && stato[v.id].nessuna).length;
  document.getElementById("cDone").textContent = scelte;
  document.getElementById("cTot").textContent = DATI.length;
  document.getElementById("cNone").textContent = senza;
}

function zoom(src) {
  const lb = document.getElementById("lb");
  lb.querySelector("img").src = src.replace(/\/\d+px-/, "/1600px-");
  lb.style.display = "flex";
}
document.getElementById("lb").addEventListener("click", (e) => { e.currentTarget.style.display = "none"; });
document.getElementById("filt").addEventListener("change", disegna);
document.getElementById("btnExport").addEventListener("click", () => {
  const oggi = new Date().toISOString().slice(0, 10);
  const voci = [];
  for (const v of DATI) {
    const s = stato[v.id];
    if (!s || s.scelta === undefined || s.scelta === null) continue;
    const c = v.candidati[s.scelta];
    voci.push({ id: v.id, kind: "car", image_url: c.image_url, source_page: c.source_page, license: c.license,
      author: c.author, width: c.width, descrizione_contenuto: s.nota || c.descrizione || c.titolo,
      confidence: "alta", note: "verificata visivamente il " + oggi + " (provino Lotto 2)" });
  }
  const senza = DATI.filter((v) => stato[v.id] && stato[v.id].nessuna).map((v) => v.id);
  const nonViste = DATI.filter((v) => !stato[v.id] || ((stato[v.id].scelta === undefined || stato[v.id].scelta === null) && !stato[v.id].nessuna)).map((v) => v.id);
  const blob = new Blob([JSON.stringify({ _meta: { esportato_il: oggi, senza_foto: senza, non_viste: nonViste }, foto: voci }, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "photos_lotto2.json";
  a.click();
});
disegna();
"""


def scrivi_html(dati: list[dict]) -> None:
    corpo = _JS.replace("__DATI__", json.dumps(dati, ensure_ascii=False))
    n = sum(len(v["candidati"]) for v in dati)
    pagina = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>PitWall.AI — Provino foto · Lotto 2</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>PitWall<span>.</span>AI — Provino foto · Lotto 2</h1>
  <span class="stat">scelte <b id="cDone">0</b> / <b id="cTot">0</b> · senza foto <b id="cNone">0</b></span>
  <select id="filt">
    <option value="all">Mostra tutte</option>
    <option value="work">Mostra solo da scegliere</option>
  </select>
  <button class="primary" id="btnExport">Esporta photos_lotto2.json</button>
</header>
<main>
  <p class="note">
    {n} candidati trovati su Wikimedia Commons per {len(dati)} vetture, tutti con una licenza libera.
    Li ha pescati una ricerca per nome: <b>il nome del file non prova niente</b>, guarda la foto.
    Deve essere la <b>versione da corsa giusta</b> (la GT4, non la stradale; la 992 Cup, non la 991),
    possibilmente in pista e intera nell'inquadratura. Clicca una foto per sceglierla (di nuovo per
    toglierla), «ingrandisci» per vederla grande. Se nessuna va bene usa <i>Nessuna adatta</i>: la
    vettura resta senza foto, che è sempre meglio di una foto sbagliata.
    <br>Le scelte restano nel browser: puoi chiudere e riprendere. Alla fine premi «Esporta».
  </p>
  <div id="list"></div>
</main>
<div id="lb"><img alt=""></div>
<script>{corpo}</script>
</body>
</html>
"""
    USCITA.parent.mkdir(parents=True, exist_ok=True)
    USCITA.write_text(pagina, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Genera il provino delle foto delle vetture senza foto")
    ap.add_argument("--classi", default=CLASSI_DEFAULT, help=f"classi da cercare (default {CLASSI_DEFAULT})")
    ap.add_argument("--only", default="", help="lista di id separati da virgola")
    args = ap.parse_args()

    vetture = json.loads((_DATA_DIR / "cars.json").read_text(encoding="utf-8"))
    con_foto = {v["id"] for v in json.loads(PHOTOS.read_text(encoding="utf-8")) if v.get("kind") == "car"}
    classi = {c.strip() for c in args.classi.split(",") if c.strip()}
    solo = {c.strip() for c in args.only.split(",") if c.strip()}
    scelte = [v for v in vetture if v["id"] not in con_foto
              and (v["id"] in solo if solo else v.get("category") in classi)]

    dati = []
    for v in scelte:
        nome = f"{v['brand']} {v['model']}"
        print(f"{nome}…")
        candidati = risolvi(titoli_candidati(v)[:MAX_CANDIDATI * 2])[:MAX_CANDIDATI]
        print(f"    {len(candidati)} candidati")
        dati.append({"id": v["id"], "nome": nome, "classe": v.get("category"), "anno": v.get("year"),
                     "candidati": candidati})

    scrivi_html(dati)
    vuote = [d["nome"] for d in dati if not d["candidati"]]
    print(f"\n{sum(len(d['candidati']) for d in dati)} candidati per {len(dati)} vetture → {USCITA}")
    if vuote:
        print("senza nessun candidato:", ", ".join(vuote))


if __name__ == "__main__":
    main()
