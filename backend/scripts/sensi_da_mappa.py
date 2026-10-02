#!/usr/bin/env python3
"""
sensi_da_mappa.py — il senso di ogni curva, ricavato dal DISEGNO della mappa (Entry #067)

Perche' esiste:
    «I sensi delle curve si leggono sulla mappa numerata, calcolando il verso di rotazione
    lungo la freccia»: la regola nata a Zandvoort e Imola (guida con sei sensi ribaltati) e
    ripetuta a Paul Ricard. A occhio e' lenta e si sbaglia: sulla mappa di Kyalami il senso
    di marcia sembrava antiorario e Wikipedia dice orario. Questo strumento lo calcola.

Cosa fa:
    legge una mappa PNG con la pista disegnata a tratto scuro (la mappa verificata dentro
    frontend/public/assets/tracks/), ne ricava la linea di mezzeria (assottigliamento di
    Zhang-Suen), la percorre nel verso della freccia di marcia e, per ogni curva numerata,
    misura di quanto gira il tracciato nei dintorni del numero: gradi e destra/sinistra.

    Le posizioni dei numeri sulla mappa si danno a mano (--etichette), guardando la mappa:
    lo strumento non legge i testi. Il verso di marcia si da' con un punto sul rettilineo
    del traguardo e la direzione della freccia rossa (--partenza x,y --verso dx,dy).

Uso (serve Pillow: `pip install -r backend/requirements-dev.txt`):
    python backend/scripts/sensi_da_mappa.py kyalami_map.png \\
        --partenza 745,505 --verso 1,-1 \\
        --etichette "1:903,392 2:1109,215 ..."

Limiti dichiarati: la misura e' sul disegno, non sulla pista vera. Una curva lunga si distribuisce
su piu' numeri; le pieghe lievi (sotto ~15 gradi) hanno un senso incerto e lo strumento le segnala.
Il risultato si accetta solo dopo aver guardato --salva-scheletro: ogni punto misurato (rosa =
destra, verde = sinistra) deve cadere sulla curva del SUO numero.
Affidabile solo sui PNG a tratto scuro (Kyalami). Sugli SVG le posizioni dei testi sono scostate
dalla curva e la misura sbaglia (Red Bull Ring, T4): li' i sensi si leggono a occhio sulla mappa.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ASSETS = Path(__file__).resolve().parents[2] / "frontend" / "public" / "assets" / "tracks"
PASSO = 4.0          # px fra due punti del percorso ricampionato
FINESTRA_PX = 36.0   # arco su cui si misura quanto gira la pista
# Quanto lontano dal numero si cerca il punto di massima curvatura. Era 70 px: a Kyalami il
# massimo vicino al «3» era la piega di Barbeque e quello vicino al «14» la Cheetah, e i due
# errori si compensavano nel conto 6 destre / 10 sinistre del sito ufficiale (02/10/2026).
# Il conto ufficiale quindi NON basta come controllo: si guarda sempre --salva-scheletro.
CERCA_PX = 25.0
INCERTA_GRADI = 15.0


# ── Mappe SVG: la mezzeria sta gia' dentro il file (un percorso chiuso) ──

def _token_svg(d):
    return re.findall(r"[MmLlHhVvCcSsZzQqTtAa]|-?\d*\.?\d+(?:e-?\d+)?", d)

def percorso_svg_d(d, n=12):
    tk = _token_svg(d); i = 0; pts = []; cur = np.zeros(2); start = np.zeros(2); cmd = None; last_c = None
    def num():
        nonlocal i
        v = float(tk[i]); i += 1; return v
    while i < len(tk):
        if re.match(r"[A-Za-z]", tk[i]):
            cmd = tk[i]; i += 1
            if cmd in "Zz":
                pts.append(start.copy()); cur = start.copy(); continue
        c = cmd
        if c in "Mm":
            p = np.array([num(), num()]); cur = cur + p if c == "m" else p; start = cur.copy(); pts.append(cur.copy()); cmd = "l" if c == "m" else "L"
        elif c in "Ll":
            p = np.array([num(), num()]); cur = cur + p if c == "l" else p; pts.append(cur.copy())
        elif c in "Hh":
            x = num(); cur = np.array([cur[0] + x if c == "h" else x, cur[1]]); pts.append(cur.copy())
        elif c in "Vv":
            y = num(); cur = np.array([cur[0], cur[1] + y if c == "v" else y]); pts.append(cur.copy())
        elif c in "Cc":
            p1 = np.array([num(), num()]); p2 = np.array([num(), num()]); p3 = np.array([num(), num()])
            if c == "c": p1, p2, p3 = cur + p1, cur + p2, cur + p3
            for t in np.linspace(0, 1, n + 1)[1:]:
                pts.append((1 - t) ** 3 * cur + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)
            cur = p3; last_c = p2
        elif c in "Ss":
            p2 = np.array([num(), num()]); p3 = np.array([num(), num()])
            if c == "s": p2, p3 = cur + p2, cur + p3
            p1 = 2 * cur - last_c if last_c is not None else cur
            for t in np.linspace(0, 1, n + 1)[1:]:
                pts.append((1 - t) ** 3 * cur + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)
            cur = p3; last_c = p2
        else:
            raise ValueError("comando non gestito " + c)
    return np.array(pts)


def leggi_svg(percorso: Path, id_percorso: str) -> tuple[np.ndarray, dict[int, tuple[float, float]]]:
    """La mezzeria (il percorso `id_percorso`) e le posizioni dei numeri (testi interi) di un SVG."""
    t = percorso.read_text(encoding="utf-8", errors="replace")
    blocco = re.search(r'<path[\s>](?:(?!/>).)*?\sid="%s"(?:(?!/>).)*/>' % re.escape(id_percorso), t, flags=re.S)
    if not blocco:
        sys.exit(f"nessun percorso con id «{id_percorso}» in {percorso.name}")
    d = re.search(r'\sd="([^"]*)"', blocco.group(0)).group(1)
    etichette = {}
    for m in re.finditer(r"<text[\s>][^>]*>(.*?)</text>", t, flags=re.S):
        s = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        xy = re.search(r'\sx="([^"]*)"\s+y="([^"]*)"', m.group(0))
        if s.isdigit() and xy:
            etichette[int(s)] = (float(xy.group(1)), float(xy.group(2)))
    return percorso_svg_d(d), etichette


def maschera_pista(percorso: Path, soglia: int, a_colori: bool = False,
                   escludi: tuple[int, int, int] | None = None) -> np.ndarray:
    """I pixel di pista. Di default sono i pixel scuri (pista a tratto nero); con `a_colori` ogni
    pixel non bianco (pista nera con tratteggi di settore colorati) e, con `escludi`, si scarta un
    colore (la corsia box)."""
    img = Image.open(percorso).convert("RGBA")
    sfondo = Image.new("RGBA", img.size, (255, 255, 255, 255))
    grigio = np.array(Image.alpha_composite(sfondo, img).convert("L"))
    rgb = np.array(Image.alpha_composite(sfondo, img).convert("RGB")).astype(int)
    if a_colori:
        inchiostro = rgb.min(axis=2) < 225
        if escludi is not None:
            vicino = np.abs(rgb - np.array(escludi)).max(axis=2) < 45
            inchiostro &= ~vicino
        return inchiostro
    scuro = grigio < soglia
    # Le frecce rosse di marcia stanno SOPRA la pista (sempre su un rettilineo): se si scartassero
    # spezzerebbero il tracciato. Si tengono: al massimo lasciano una codina, che si pota.
    rosso = (rgb[:, :, 0] > 150) & (rgb[:, :, 1] < 90) & (rgb[:, :, 2] < 90)
    return scuro | rosso


def _finestra_somma(m: np.ndarray, k: int) -> np.ndarray:
    """Somma dei valori in una finestra k×k centrata su ogni pixel (immagine integrale)."""
    r = k // 2
    p = np.pad(m.astype(np.int32), r + 1)
    ii = p.cumsum(axis=0).cumsum(axis=1)
    h, w = m.shape
    y0, x0 = np.arange(h), np.arange(w)
    return (ii[y0[:, None] + k, x0[None, :] + k] - ii[y0[:, None], x0[None, :] + k]
            - ii[y0[:, None] + k, x0[None, :]] + ii[y0[:, None], x0[None, :]])


def chiudi(m: np.ndarray, k: int) -> np.ndarray:
    """Chiusura morfologica: richiude le fessure bianche piu' strette di k pixel (le righe del
    traguardo e dei settori spezzano la pista in pezzi)."""
    if k <= 1:
        return m
    dilatato = _finestra_somma(m, k) > 0
    return _finestra_somma(dilatato, k) == k * k


def apri(m: np.ndarray, k: int) -> np.ndarray:
    """Apertura morfologica con un quadrato k×k: toglie i tratti piu' sottili di k pixel (testi,
    cerchi dei numeri, frecce sottili) e lascia la linea di pista, che e' piu' spessa."""
    if k <= 1:
        return m
    eroso = _finestra_somma(m, k) == k * k
    return _finestra_somma(eroso, k) > 0


def componente_piu_grande(m: np.ndarray) -> np.ndarray:
    h, w = m.shape
    visto = np.zeros_like(m, dtype=bool)
    migliore: list[tuple[int, int]] = []
    for y0, x0 in zip(*np.nonzero(m)):
        if visto[y0, x0]:
            continue
        coda = deque([(y0, x0)])
        visto[y0, x0] = True
        comp = []
        while coda:
            y, x = coda.popleft()
            comp.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not visto[ny, nx]:
                        visto[ny, nx] = True
                        coda.append((ny, nx))
        if len(comp) > len(migliore):
            migliore = comp
    out = np.zeros_like(m)
    for y, x in migliore:
        out[y, x] = True
    return out


def riempi_buchi(m: np.ndarray, massimo: int = 900) -> np.ndarray:
    """Riempie i buchi di sfondo piu' piccoli di `massimo` pixel (non toccano il bordo)."""
    h, w = m.shape
    visto = np.zeros_like(m, dtype=bool)
    out = m.copy()
    for y0, x0 in zip(*np.nonzero(~m)):
        if visto[y0, x0]:
            continue
        coda = deque([(y0, x0)])
        visto[y0, x0] = True
        comp, tocca_bordo = [], False
        while coda:
            y, x = coda.popleft()
            comp.append((y, x))
            if y in (0, h - 1) or x in (0, w - 1):
                tocca_bordo = True
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and not m[ny, nx] and not visto[ny, nx]:
                    visto[ny, nx] = True
                    coda.append((ny, nx))
        if not tocca_bordo and len(comp) < massimo:
            for y, x in comp:
                out[y, x] = True
    return out


def zhang_suen(img: np.ndarray) -> np.ndarray:
    img = img.copy().astype(np.uint8)
    cambiato = True
    while cambiato:
        cambiato = False
        for passo in (0, 1):
            p = np.pad(img, 1)
            P2, P3, P4, P5 = p[:-2, 1:-1], p[:-2, 2:], p[1:-1, 2:], p[2:, 2:]
            P6, P7, P8, P9 = p[2:, 1:-1], p[2:, :-2], p[1:-1, :-2], p[:-2, :-2]
            vicini = [P2, P3, P4, P5, P6, P7, P8, P9]
            B = sum(v.astype(int) for v in vicini)
            seq = vicini + [P2]
            A = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(int) for i in range(8))
            if passo == 0:
                c = (P2 * P4 * P6 == 0) & (P4 * P6 * P8 == 0)
            else:
                c = (P2 * P4 * P8 == 0) & (P2 * P6 * P8 == 0)
            togli = (img == 1) & (B >= 2) & (B <= 6) & (A == 1) & c
            if togli.any():
                img[togli] = 0
                cambiato = True
    return img.astype(bool)


def percorso_ordinato(sk: np.ndarray) -> np.ndarray:
    """I pixel dello scheletro in ordine lungo l'anello, seguendo la direzione di marcia.

    Si pota prima ogni codina; poi si cammina scegliendo, fra i vicini non ancora visti, quello
    che meglio prosegue la direzione degli ultimi passi: cosi' agli incroci si resta sull'anello.
    """
    pts = {(y, x) for y, x in zip(*np.nonzero(sk))}

    def vicini(p):
        y, x = p
        return [(y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                if (dy or dx) and (y + dy, x + dx) in pts]

    for _ in range(120):
        code = [p for p in pts if len(vicini(p)) <= 1]
        if not code:
            break
        pts -= set(code)
    inizio = min(pts)
    ordine = [inizio]
    visti = {inizio}
    corrente = inizio
    while True:
        prossimi = [q for q in vicini(corrente) if q not in visti]
        if not prossimi:
            break
        if len(ordine) >= 8:
            ref = np.array(ordine[-1]) - np.array(ordine[-8])
            ref = ref / (np.linalg.norm(ref) or 1.0)
            prossimi.sort(key=lambda q: -float(np.dot(np.array(q) - np.array(corrente), ref)
                                              / (np.linalg.norm(np.array(q) - np.array(corrente)) or 1.0)))
        else:
            prossimi.sort(key=lambda q: abs(q[0] - corrente[0]) + abs(q[1] - corrente[1]))
        corrente = prossimi[0]
        ordine.append(corrente)
        visti.add(corrente)
    if len(ordine) < 0.9 * len(pts):
        print(f"ATTENZIONE: il percorso copre {len(ordine)} pixel su {len(pts)} dello scheletro: "
              f"l'anello non e' stato seguito per intero, i sensi vanno ricontrollati")
    return np.array([(x, y) for y, x in ordine], dtype=float)


def _uniforme(pt: np.ndarray, passo: float, chiuso: bool = True) -> np.ndarray:
    """Punti a distanza costante lungo la spezzata (anello chiuso se `chiuso`)."""
    q = np.vstack([pt, pt[:1]]) if chiuso else pt
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(q, axis=0).T))]
    nuovi = np.arange(0, d[-1], passo)
    return np.stack([np.interp(nuovi, d, q[:, 0]), np.interp(nuovi, d, q[:, 1])], axis=1)


def ricampiona(pt: np.ndarray, passo: float) -> np.ndarray:
    """Un anello a passo costante e levigato.

    Prima si porta la spezzata a passo uniforme (in un SVG i rettilinei hanno due punti e le curve
    cento: una media mobile sui punti grezzi li mescolerebbe), poi si leviga (la scalettatura dei
    pixel di uno scheletro, le spigolosita' delle curve di Bezier), poi si ricampiona al passo voluto."""
    fine = _uniforme(pt, 1.0 if passo >= 2.0 else passo / 2.0)
    k = max(5, int(round(passo * 2.5 / (1.0 if passo >= 2.0 else passo / 2.0))) | 1)
    ker = np.ones(k) / k
    xs = np.convolve(np.pad(fine[:, 0], k // 2, mode="wrap"), ker, mode="valid")
    ys = np.convolve(np.pad(fine[:, 1], k // 2, mode="wrap"), ker, mode="valid")
    return _uniforme(np.stack([xs, ys], axis=1), passo)


def orienta(p: np.ndarray, partenza: tuple[float, float], verso: tuple[float, float]) -> np.ndarray:
    i = int(np.argmin(np.hypot(p[:, 0] - partenza[0], p[:, 1] - partenza[1])))
    t = p[(i + 3) % len(p)] - p[(i - 3) % len(p)]
    return p if float(np.dot(t, verso)) > 0 else p[::-1].copy()


def variazioni_di_direzione(p: np.ndarray) -> np.ndarray:
    """Quanto gira la tangente fra un punto e il successivo (gradi, + = orario con y verso il basso).

    Si sommano variazioni piccole e ognuna ridotta in (-180, 180]: cosi' non conta dove cade il
    punto di giunzione dell'anello, e un tornante da 180 gradi non si confonde con -180."""
    d = np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)
    a = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    var = np.roll(a, -1) - a
    return (var + 180.0) % 360.0 - 180.0


def curve_per_etichetta(p: np.ndarray, etichette: dict[int, tuple[float, float]],
                        finestra: float = FINESTRA_PX, raggio: float = CERCA_PX,
                        passo: float = PASSO) -> list[dict]:
    n = len(p)
    var = variazioni_di_direzione(p)
    cum = np.r_[0.0, np.cumsum(np.r_[var, var])]          # somme cumulate su due giri: finestre circolari
    mezza = int(round(finestra / passo / 2))
    cerca = int(round(raggio / passo))
    risultati = []
    for num, (x, y) in sorted(etichette.items()):
        i0 = int(np.argmin(np.hypot(p[:, 0] - x, p[:, 1] - y)))
        migliore = (0.0, i0)
        for k in range(-cerca, cerca + 1):
            i = (i0 + k) % n
            a = (i - mezza) % n
            delta = float(cum[a + 2 * mezza] - cum[a])
            if abs(delta) > abs(migliore[0]):
                migliore = (delta, i)
        gradi, i = migliore
        risultati.append({
            "n": num, "gradi": round(abs(gradi)), "senso": "destra" if gradi > 0 else "sinistra",
            "incerta": abs(gradi) < INCERTA_GRADI, "punto": tuple(map(round, p[i])),
        })
    return risultati


def giro_totale(p: np.ndarray) -> str:
    """Il senso dell'anello dalla sua area con segno (formula di Gauss); y verso il basso: positivo = orario."""
    x, y = p[:, 0], p[:, 1]
    area = 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
    return "orario" if area > 0 else "antiorario"


def main() -> None:
    ap = argparse.ArgumentParser(description="Senso di marcia e senso di ogni curva da una mappa (PNG o SVG)")
    ap.add_argument("mappa", help="nome del file in frontend/public/assets/tracks/ o percorso (.png o .svg)")
    ap.add_argument("--partenza", required=True, help="x,y di un punto sul rettilineo del traguardo")
    ap.add_argument("--verso", required=True, help="dx,dy della freccia di marcia (y verso il basso)")
    ap.add_argument("--etichette", default="auto",
                    help='«1:903,392 2:1109,215 …» posizione di ogni numero; «auto» legge i testi numerici di un SVG')
    ap.add_argument("--svg-id", help="SVG: id del percorso che e' la mezzeria della pista (un anello chiuso)")
    ap.add_argument("--soglia", type=int, default=90, help="PNG: grigio sotto cui un pixel e' pista (default 90)")
    ap.add_argument("--a-colori", action="store_true",
                    help="PNG: pista nera con tratteggi di settore colorati: ogni pixel non bianco e' pista")
    ap.add_argument("--escludi-colore", help="PNG: r,g,b di un colore da scartare (di solito la corsia box)")
    ap.add_argument("--apertura", type=int, default=0,
                    help="PNG: toglie i tratti piu' sottili di N pixel (testi, cerchi): 0 = no")
    ap.add_argument("--chiusura", type=int, default=0,
                    help="PNG: richiude le fessure bianche piu' strette di N pixel (traguardo, settori): 0 = no")
    ap.add_argument("--finestra", type=float, help="arco su cui si misura quanto gira la pista (default: 1,5% del giro)")
    ap.add_argument("--raggio", type=float, help="quanto lontano dal numero si cerca la curva (default: 3,5% del giro)")
    ap.add_argument("--salva-scheletro", type=Path, help="PNG: scrive un'immagine con la mezzeria e i punti misurati")
    a = ap.parse_args()

    percorso = Path(a.mappa) if Path(a.mappa).exists() else ASSETS / a.mappa
    partenza = tuple(float(v) for v in a.partenza.split(","))
    verso = tuple(float(v) for v in a.verso.split(","))

    if percorso.suffix.lower() == ".svg":
        if not a.svg_id:
            sys.exit("per un SVG serve --svg-id (l'id del percorso della mezzeria)")
        grezzo, da_svg = leggi_svg(percorso, a.svg_id)
        lunghezza = float(np.sum(np.hypot(*np.diff(grezzo, axis=0).T)))
        passo = lunghezza / 1200.0
        p = ricampiona(grezzo[:-1] if np.allclose(grezzo[0], grezzo[-1]) else grezzo, passo)
        print(f"mezzeria SVG «{a.svg_id}»: {len(p)} punti, giro di {round(lunghezza)} unita'")
    else:
        da_svg, passo = {}, PASSO
        escludi = tuple(int(v) for v in a.escludi_colore.split(",")) if a.escludi_colore else None
        m = riempi_buchi(componente_piu_grande(
            chiudi(apri(maschera_pista(percorso, a.soglia, a.a_colori, escludi), a.apertura), a.chiusura)))
        sk = zhang_suen(m)
        p = ricampiona(percorso_ordinato(sk), passo)
        lunghezza = len(p) * passo
        print(f"pista: {int(m.sum())} pixel nella componente piu' grande; mezzeria {len(p)} punti, giro di {round(lunghezza)} px")

    if a.etichette == "auto":
        if not da_svg:
            sys.exit("«--etichette auto» vale solo per gli SVG con i numeri come testi")
        etichette = da_svg
    else:
        etichette = {}
        for voce in a.etichette.split():
            n, xy = voce.split(":")
            x, y = xy.split(",")
            etichette[int(n)] = (float(x), float(y))

    finestra = a.finestra if a.finestra is not None else (0.015 * lunghezza if percorso.suffix.lower() == ".svg" else FINESTRA_PX)
    raggio = a.raggio if a.raggio is not None else (0.035 * lunghezza if percorso.suffix.lower() == ".svg" else CERCA_PX)
    p = orienta(p, partenza, verso)
    print("senso di marcia lungo la freccia:", giro_totale(p))
    risultati = curve_per_etichetta(p, etichette, finestra, raggio, passo)
    print(f"\n{'T':>3} {'senso':<9} {'gradi':>5}  note")
    for r in risultati:
        print(f"{r['n']:>3} {r['senso']:<9} {r['gradi']:>5}  {'piega lieve: senso incerto' if r['incerta'] else ''}")
    destre = sum(1 for r in risultati if r["senso"] == "destra")
    print(f"\n{destre} a destra,{len(risultati) - destre} a sinistra (da confrontare con la fonte, se ne dice il conto)")

    if a.salva_scheletro and percorso.suffix.lower() != ".svg":
        base = Image.open(percorso).convert("RGBA")
        img = Image.alpha_composite(Image.new("RGBA", base.size, (255, 255, 255, 255)), base).convert("RGB")
        px = img.load()
        for x, y in p:
            if 0 <= int(x) < img.width and 0 <= int(y) < img.height:
                px[int(x), int(y)] = (0, 160, 255)
        for r in risultati:
            x, y = r["punto"]
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    if 0 <= x + dx < img.width and 0 <= y + dy < img.height:
                        px[x + dx, y + dy] = (255, 0, 200) if r["senso"] == "destra" else (0, 200, 0)
        img.save(a.salva_scheletro)
        print("immagine di controllo:", a.salva_scheletro)


if __name__ == "__main__":
    main()
