#!/usr/bin/env python3
"""
build_crop_tool.py — genera il TOOL DI RITAGLIO delle foto (provino dei tagli)

Perche' esiste:
    La banda foto delle schede e' molto panoramica (540x128 = 4.2:1) mentre le
    foto di Commons stanno fra 1.2:1 e 2.7:1: con `object-cover` centrato si
    perde il 65-75% dell'altezza e capita che della vettura resti una fascia di
    carrozzeria, o del circuito solo un pezzo di asfalto. Quale sia la porzione
    GIUSTA da tenere non lo decide un algoritmo: dipende da dove sta il soggetto
    in quella singola foto.

    Questo script genera una pagina in cui si sceglie l'inquadratura a mano, una
    foto alla volta: si trascina il riquadro sulla foto intera, si zooma, e si
    vede di fianco l'anteprima esatta di come verra' nella card. L'export e'
    `crops.json`, che apply_photos.py copia fra gli asset e che la UI applica.

Uso:
    python backend/scripts/build_crop_tool.py
    poi apri  http://localhost:3000/assets/_ritaglio.html  (serve `npm run dev`)

L'uscita sta in frontend/public/assets/ (cartella gitignorata): la pagina e'
uno strumento di lavoro, non un pezzo dell'app. Il file che conta e' l'export
crops.json, che va in backend/scripts/ ed e' versionato.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
ASSETS = _ROOT / "frontend" / "public" / "assets"
CROPS = Path(__file__).resolve().parent / "crops.json"
USCITA = ASSETS / "_ritaglio.html"


def dimensioni(p: Path) -> tuple[int, int]:
    """Larghezza e altezza di un JPEG/PNG, senza dipendenze esterne.

    Servono al tool per disegnare il riquadro nelle coordinate della foto: si
    leggono qui una volta sola invece di aspettare l'onload di 53 immagini.
    """
    b = p.read_bytes()
    if b[:4] == b"\x89PNG":
        return struct.unpack(">II", b[16:24])
    i = 2
    while i < len(b) - 1:
        while b[i] != 0xFF:
            i += 1
        while b[i] == 0xFF:
            i += 1
        marcatore = b[i]
        i += 1
        if marcatore in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", b[i + 3:i + 7])
            return w, h
        i += struct.unpack(">H", b[i:i + 2])[0]
    return 0, 0


def raccogli() -> list[dict]:
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    voci = []
    for tipo, kind in (("cars", "car"), ("tracks", "track")):
        for ent_id, ruoli in sorted(manifest.get(tipo, {}).items()):
            if "photo" not in ruoli:
                continue
            f = ASSETS.parent / ruoli["photo"].lstrip("/")
            w, h = dimensioni(f)
            voci.append({"id": ent_id, "kind": kind, "src": ruoli["photo"], "w": w, "h": h})
    return voci


PAGINA = r"""<!doctype html>
<meta charset="utf-8">
<title>PitWall — ritaglio foto</title>
<style>
  :root{ --bg:#0a0a0a; --panel:#111; --panel2:#171717; --line:#282828;
         --txt:#e8e8e8; --dim:#8a8a8a; --acc:#E8002D; --ok:#00C853; }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);
       font:13px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif;
       user-select:none}
  header{position:sticky;top:0;z-index:10;background:var(--panel);
         border-bottom:1px solid var(--line);padding:10px 16px;
         display:flex;align-items:center;gap:12px;flex-wrap:wrap}
  .titolo{font-family:ui-monospace,monospace;font-size:15px;color:#fff;min-width:290px}
  .titolo .n{color:var(--acc)}
  button,select{background:var(--panel2);color:var(--txt);border:1px solid var(--line);
    border-radius:6px;padding:6px 11px;font:inherit;cursor:pointer}
  button:hover{border-color:#3d3d3d}
  button.p{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:600}
  button.ok{border-color:var(--ok);color:var(--ok)}
  .sp{flex:1}
  .cont{font-family:ui-monospace,monospace;color:var(--dim);font-size:12px}
  main{display:flex;gap:18px;padding:16px;align-items:flex-start}
  .palco{background:var(--panel);border:1px solid var(--line);border-radius:10px;
         padding:14px;position:relative}
  #tela{position:relative;cursor:grab;touch-action:none}
  #tela.trascino{cursor:grabbing}
  #tela img{display:block;border-radius:4px}
  #velo{position:absolute;inset:0;pointer-events:none}
  #riq{position:absolute;pointer-events:none;box-shadow:0 0 0 9999px rgba(0,0,0,.62);
       border:2px solid var(--acc);border-radius:2px}
  #riq::before,#riq::after{content:"";position:absolute;background:rgba(255,255,255,.28)}
  #riq::before{left:33.33%;right:33.33%;top:0;bottom:0;
    border-left:1px solid rgba(255,255,255,.28);border-right:1px solid rgba(255,255,255,.28);
    background:none}
  #riq::after{top:50%;left:0;right:0;height:1px}
  .lato{width:600px;display:flex;flex-direction:column;gap:14px}
  .scheda{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
  .scheda h2{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--acc);
    margin:0 0 10px;font-family:ui-monospace,monospace}
  .antep{width:540px;max-width:100%;overflow:hidden;position:relative;background:#000;
         border:1px solid var(--line);border-radius:8px 8px 0 0}
  .antep img{position:absolute;max-width:none;display:block}
  .finta{width:540px;max-width:100%;border:1px solid var(--line);border-top:0;
    border-radius:0 0 8px 8px;padding:10px 14px 14px;background:#141414}
  .finta .et{font-family:ui-monospace,monospace;font-size:9.5px;letter-spacing:.14em;
    color:var(--acc);text-transform:uppercase}
  .finta .nm{font-size:17px;margin-top:2px}
  .riga{display:flex;align-items:center;gap:10px;margin:9px 0}
  .riga label{width:96px;color:var(--dim);font-size:12px}
  input[type=range]{flex:1;accent-color:var(--acc)}
  .val{font-family:ui-monospace,monospace;width:66px;text-align:right;color:#fff}
  .aiuto{color:var(--dim);font-size:12px;line-height:1.7}
  .aiuto b{color:#ddd}
  kbd{background:#222;border:1px solid #333;border-radius:4px;padding:0 5px;
    font-family:ui-monospace,monospace;font-size:11px}
  .stato{font-family:ui-monospace,monospace;font-size:11px;color:var(--dim);margin-top:8px}
  .fatta{color:var(--ok)}
</style>

<header>
  <div class="titolo"><span class="n" id="pos">1/1</span> <span id="nome">—</span></div>
  <button id="prev">‹ indietro</button>
  <button id="next">avanti ›</button>
  <select id="salta"></select>
  <button id="segna" class="ok">✓ segna fatta</button>
  <button id="reset">⟲ reset</button>
  <div class="sp"></div>
  <div class="cont"><span id="fatte">0</span>/<span id="tot">0</span> fatte</div>
  <button id="imp">Importa crops.json</button>
  <input type="file" id="file" accept=".json,application/json" hidden>
  <button id="exp" class="p">Esporta crops.json</button>
</header>

<main>
  <div class="palco">
    <div id="tela"><img id="foto" alt=""><div id="riq"></div></div>
    <div class="stato" id="dati">—</div>
  </div>

  <div class="lato">
    <div class="scheda">
      <h2>Come verrà nella card</h2>
      <div class="antep" id="antep"><img id="pfoto" alt=""></div>
      <div class="finta">
        <div class="et" id="pet">LA VETTURA</div>
        <div class="nm" id="pnome">—</div>
      </div>
    </div>

    <div class="scheda">
      <h2>Regolazioni</h2>
      <div class="riga">
        <label for="zoom">Zoom</label>
        <input type="range" id="zoom" min="100" max="400" value="100">
        <div class="val" id="vzoom">1.00×</div>
      </div>
      <div class="riga">
        <label for="alt">Altezza banda</label>
        <input type="range" id="alt" min="96" max="280" step="4" value="128">
        <div class="val" id="valt">128 px</div>
      </div>
      <div class="aiuto" style="margin-top:6px">
        L'altezza vale per <b>tutte</b> le foto: è il formato della banda.
        540×<span id="altv">128</span> px.
      </div>
    </div>

    <div class="scheda">
      <h2>Comandi</h2>
      <div class="aiuto">
        <b>Trascina</b> sulla foto per spostare il riquadro · <b>rotella</b> per zoomare<br>
        <kbd>←</kbd> <kbd>→</kbd> foto precedente/successiva ·
        <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> spostamento fine<br>
        <kbd>+</kbd> <kbd>−</kbd> zoom · <kbd>R</kbd> reset ·
        <kbd>Spazio</kbd> segna fatta e vai avanti<br>
        Il lavoro si salva da solo nel browser: puoi chiudere e riprendere.
      </div>
    </div>
  </div>
</main>

<script>
const FOTO = __DATI__;
const INIZIALI = __CROPS__;
const CHIAVE = "pitwall_ritagli_v1";
const LARG = 540;                 // larghezza reale della card, riferimento fisso

let stato = {};                   // id -> {px, py, zoom, fatta}
let alt = 128;                    // altezza banda, comune a tutte
let i = 0;

// ---- persistenza -----------------------------------------------------------
function carica(){
  try{
    const g = JSON.parse(localStorage.getItem(CHIAVE) || "null");
    if(g && g.items){ stato = g.items; alt = g.band?.h || 128; return; }
  }catch(e){}
  if(INIZIALI && INIZIALI.items){
    for(const [id,v] of Object.entries(INIZIALI.items))
      stato[id] = {px:v.px ?? .5, py:v.py ?? .5, zoom:v.zoom ?? 1, fatta:true};
    alt = INIZIALI.band?.h || 128;
  }
}
function salva(){
  try{ localStorage.setItem(CHIAVE, JSON.stringify({band:{w:LARG,h:alt}, items:stato})); }catch(e){}
}
function s(id){
  if(!stato[id]) stato[id] = {px:.5, py:.5, zoom:1, fatta:false};
  return stato[id];
}

// ---- geometria -------------------------------------------------------------
// Regione della FOTO (in pixel sorgente) che finisce nella banda: ha lo stesso
// rapporto della banda, ridotta dallo zoom, posizionata dal punto (px,py).
function regione(f, st){
  const ar = LARG/alt, arF = f.w/f.h;
  let rw, rh;
  if(arF > ar){ rh = f.h/st.zoom; rw = rh*ar; }
  else        { rw = f.w/st.zoom; rh = rw/ar; }
  const left = st.px*(f.w-rw), top = st.py*(f.h-rh);
  return {rw, rh, left, top};
}
// Le stesse informazioni come percentuali CSS: cosi' la UI applica numeri
// gia' pronti (larghezza/altezza/offset dell'img dentro la banda) senza
// rifare i conti, e il risultato non dipende dalla larghezza dello schermo.
function css(f, st){
  const r = regione(f, st);
  return {
    w: +(100*f.w/r.rw).toFixed(3),
    h: +(100*f.h/r.rh).toFixed(3),
    l: +(-100*r.left/r.rw).toFixed(3),
    t: +(-100*r.top/r.rh).toFixed(3),
  };
}

// ---- disegno ---------------------------------------------------------------
const elTela=document.getElementById("tela"), elFoto=document.getElementById("foto"),
      elRiq=document.getElementById("riq"), elPre=document.getElementById("antep"),
      elPFoto=document.getElementById("pfoto");
let scala = 1;   // fattore foto->schermo nel palco

function disegna(){
  const f = FOTO[i], st = s(f.id);

  // 1. la foto intera nel palco, rimpicciolita per stare nello spazio
  const maxW = Math.min(880, window.innerWidth-680), maxH = window.innerHeight-230;
  scala = Math.min(maxW/f.w, maxH/f.h, 1);
  const dw = Math.round(f.w*scala), dh = Math.round(f.h*scala);
  elFoto.src = f.src; elFoto.style.width = dw+"px"; elFoto.style.height = dh+"px";
  elTela.style.width = dw+"px"; elTela.style.height = dh+"px";

  // 2. il riquadro, nelle stesse coordinate
  const r = regione(f, st);
  elRiq.style.left = Math.round(r.left*scala)+"px";
  elRiq.style.top = Math.round(r.top*scala)+"px";
  elRiq.style.width = Math.round(r.rw*scala)+"px";
  elRiq.style.height = Math.round(r.rh*scala)+"px";

  // 3. anteprima a dimensione reale, con lo stesso calcolo che fara' la UI
  const c = css(f, st);
  elPre.style.height = alt+"px";
  elPFoto.src = f.src;
  elPFoto.style.width = c.w+"%"; elPFoto.style.height = c.h+"%";
  elPFoto.style.left = c.l+"%";  elPFoto.style.top = c.t+"%";

  // 4. testi
  document.getElementById("pos").textContent = (i+1)+"/"+FOTO.length;
  document.getElementById("nome").textContent = f.id + (st.fatta ? "  ✓" : "");
  document.getElementById("nome").className = st.fatta ? "fatta" : "";
  document.getElementById("pet").textContent = f.kind==="car" ? "LA VETTURA" : "IL TRACCIATO";
  document.getElementById("pnome").textContent = f.id.replace(/_/g," ");
  document.getElementById("zoom").value = Math.round(st.zoom*100);
  document.getElementById("vzoom").textContent = st.zoom.toFixed(2)+"×";
  document.getElementById("alt").value = alt;
  document.getElementById("valt").textContent = alt+" px";
  document.getElementById("altv").textContent = alt;
  document.getElementById("salta").value = String(i);
  document.getElementById("fatte").textContent =
    Object.values(stato).filter(v=>v.fatta).length;
  document.getElementById("dati").textContent =
    `foto ${f.w}x${f.h} · regione ${Math.round(r.rw)}x${Math.round(r.rh)} px ` +
    `· centro ${(st.px*100).toFixed(0)}% ${(st.py*100).toFixed(0)}% · zoom ${st.zoom.toFixed(2)}×`;
  salva();
}

// ---- interazione -----------------------------------------------------------
function muovi(dxFoto, dyFoto){
  const f = FOTO[i], st = s(f.id), r = regione(f, st);
  // px e' la posizione del riquadro nello spazio che gli resta: si converte
  // lo spostamento in pixel-foto nella sua frazione, cosi' il trascinamento
  // segue il mouse 1:1 a qualunque zoom.
  const spazioX = f.w-r.rw, spazioY = f.h-r.rh;
  if(spazioX > 0) st.px = Math.min(1, Math.max(0, st.px + dxFoto/spazioX));
  if(spazioY > 0) st.py = Math.min(1, Math.max(0, st.py + dyFoto/spazioY));
  disegna();
}
let trascino = null;
elTela.addEventListener("pointerdown", e=>{
  trascino = {x:e.clientX, y:e.clientY};
  elTela.classList.add("trascino"); elTela.setPointerCapture(e.pointerId);
});
elTela.addEventListener("pointermove", e=>{
  if(!trascino) return;
  const dx = (e.clientX-trascino.x)/scala, dy = (e.clientY-trascino.y)/scala;
  trascino = {x:e.clientX, y:e.clientY};
  muovi(dx, dy);
});
["pointerup","pointercancel"].forEach(ev=>elTela.addEventListener(ev, ()=>{
  trascino = null; elTela.classList.remove("trascino");
}));
elTela.addEventListener("wheel", e=>{
  e.preventDefault();
  // Passo proporzionale al delta: un colpo secco di rotella deve muovere lo
  // zoom in modo percepibile, un trackpad deve restare fine.
  const k = Math.exp(-e.deltaY/420);
  zooma(Math.min(1.5, Math.max(1/1.5, k)));
}, {passive:false});

function zooma(k){
  const st = s(FOTO[i].id);
  st.zoom = Math.min(4, Math.max(1, st.zoom*k));
  disegna();
}
function vai(d){ i = (i+d+FOTO.length)%FOTO.length; disegna(); }

document.getElementById("prev").onclick = ()=>vai(-1);
document.getElementById("next").onclick = ()=>vai(1);
document.getElementById("reset").onclick = ()=>{
  stato[FOTO[i].id] = {px:.5, py:.5, zoom:1, fatta:false}; disegna();
};
document.getElementById("segna").onclick = ()=>{
  const st = s(FOTO[i].id); st.fatta = !st.fatta; disegna();
};
document.getElementById("zoom").oninput = e=>{
  s(FOTO[i].id).zoom = +e.target.value/100; disegna();
};
document.getElementById("alt").oninput = e=>{ alt = +e.target.value; disegna(); };
document.getElementById("salta").onchange = e=>{ i = +e.target.value; disegna(); };

addEventListener("keydown", e=>{
  if(e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
  const passo = e.shiftKey ? 40 : 12;   // in pixel-foto
  const k = {a:[-passo,0], d:[passo,0], w:[0,-passo], s:[0,passo]}[e.key.toLowerCase()];
  if(k){ e.preventDefault(); muovi(k[0], k[1]); return; }
  if(e.key === "ArrowLeft")  { vai(-1); }
  else if(e.key === "ArrowRight") { vai(1); }
  else if(e.key === "+" || e.key === "=") { zooma(1.1); }
  else if(e.key === "-") { zooma(1/1.1); }
  else if(e.key.toLowerCase() === "r") { document.getElementById("reset").click(); }
  else if(e.key === " ") { e.preventDefault(); s(FOTO[i].id).fatta = true; vai(1); }
});

// ---- import / export -------------------------------------------------------
document.getElementById("exp").onclick = ()=>{
  const items = {};
  for(const f of FOTO){
    const st = stato[f.id]; if(!st) continue;
    items[f.id] = {px:+st.px.toFixed(4), py:+st.py.toFixed(4),
                   zoom:+st.zoom.toFixed(3), ...css(f, st)};
  }
  const out = {band:{w:LARG, h:alt}, items};
  const b = new Blob([JSON.stringify(out, null, 2)], {type:"application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(b); a.download = "crops.json"; a.click();
  const mancanti = FOTO.filter(f=>!stato[f.id]?.fatta).map(f=>f.id);
  if(mancanti.length) alert("Esportate "+Object.keys(items).length+" voci.\n\n"+
    "Non ancora segnate come fatte ("+mancanti.length+"):\n"+mancanti.join("\n"));
};
document.getElementById("imp").onclick = ()=>document.getElementById("file").click();
document.getElementById("file").onchange = e=>{
  const f = e.target.files[0]; if(!f) return;
  const r = new FileReader();
  r.onload = ()=>{
    try{
      const g = JSON.parse(r.result);
      stato = {}; alt = g.band?.h || 128;
      for(const [id,v] of Object.entries(g.items||{}))
        stato[id] = {px:v.px ?? .5, py:v.py ?? .5, zoom:v.zoom ?? 1, fatta:true};
      disegna();
    }catch(err){ alert("File non leggibile: "+err.message); }
  };
  r.readAsText(f);
};

// ---- avvio -----------------------------------------------------------------
const sel = document.getElementById("salta");
FOTO.forEach((f,n)=>{
  const o = document.createElement("option");
  o.value = n; o.textContent = (f.kind==="car" ? "🚗 " : "🏁 ") + f.id;
  sel.appendChild(o);
});
document.getElementById("tot").textContent = FOTO.length;
carica();
addEventListener("resize", disegna);
disegna();
</script>
"""


def main() -> None:
    voci = raccogli()
    if not voci:
        raise SystemExit("Nessuna foto nel manifest: lancia prima apply_photos.py")
    crops = json.loads(CROPS.read_text(encoding="utf-8")) if CROPS.exists() else None
    html = (PAGINA
            .replace("__DATI__", json.dumps(voci, ensure_ascii=False))
            .replace("__CROPS__", json.dumps(crops, ensure_ascii=False) if crops else "null"))
    USCITA.write_text(html, encoding="utf-8")
    print(f"Scritto {USCITA} ({len(voci)} foto)")
    print("Apri:  http://localhost:3000/assets/_ritaglio.html")


if __name__ == "__main__":
    main()
