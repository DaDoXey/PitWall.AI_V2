#!/usr/bin/env python3
"""
apply_photos.py — applica la selezione foto VERIFICATA A OCCHIO di photos.json

Perche' esiste:
    fetch_assets.py risolve gli indizi di ricerca di cars.json/tracks.json
    contro l'API di Commons e sceglie da solo. La passata del 30/08 ha mostrato
    il limite del metodo: il punteggio di pertinenza giudicava dal NOME DEL FILE,
    non dal contenuto, e sono entrati un modellino BMW in scala 1:32, due 911
    stradali al posto delle GT3 R, il monumento di Snetterton e un tendone al
    posto di Laguna Seca. Nessun filtro testuale chiude davvero quel buco:
    l'ultimo giudice deve essere un occhio umano.

    Da li' il provino (provino_foto_v3.html): interroga Commons, mostra i
    candidati come immagini e lascia scegliere a mano; il suo export e'
    photos.json, cioe' la lista delle foto GUARDATE UNA PER UNA. Questo script
    prende quell'export e lo porta a disco: nessuna ricerca, nessuna euristica,
    solo il download di quello che e' gia' stato approvato.

    E' quindi il percorso normale per le foto. fetch_assets.py resta per i
    layout SVG dei circuiti e per pescare candidati nuovi (--dry-run) da dare
    in pasto al provino.

Uso:
    python backend/scripts/apply_photos.py                 # applica backend/scripts/photos.json
    python backend/scripts/apply_photos.py --dry-run       # dice cosa farebbe
    python backend/scripts/apply_photos.py --photos ~/Downloads/photos.json
    python backend/scripts/apply_photos.py --no-download --riscopri-mappe

Schema di una voce di photos.json (dall'export del provino):
    id, kind ("car"|"track"), image_url, source_page, license, author,
    width, descrizione_contenuto, confidence ("alta"|"media"|"bassa"), note

Le entita' ASSENTI da photos.json sono assenti apposta: sono quelle marcate
"Nessuna adatta" nel provino. La loro foto vecchia (sbagliata) viene RIMOSSA —
la regola del progetto e' che nessuna immagine e' meglio di una immagine falsa.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

# fetch_assets.py e' il gemello di questo script: si riusano il downloader (con
# lo User-Agent che Commons pretende) e il generatore di manifest, cosi' l'indice
# resta scritto in un posto solo.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_assets import OUT_DIR, _ROOT, api_get, scarica, scrivi_manifest  # noqa: E402

_DATA_DIR = _ROOT / "backend" / "app" / "core" / "data"
ATTRIB_FILE = OUT_DIR / "ATTRIBUTIONS.md"
PHOTOS_DEFAULT = Path(__file__).resolve().parent / "photos.json"

# I layout SVG dei circuiti non passano dal provino (li sceglie fetch_assets.py:
# per una mappa il nome del file basta a decidere). La loro attribuzione pero'
# vive nello stesso ATTRIBUTIONS.md, che questo script riscrive per intero:
# senza un elenco versionato andrebbe persa a ogni passata. maps.json e' quello
# elenco, ricostruibile dagli SVG a disco con --riscopri-mappe.
MAPS_DEFAULT = Path(__file__).resolve().parent / "maps.json"

# Ritagli scelti a mano nel tool (build_crop_tool.py): sorgente versionata qui,
# copia servita al frontend in public/assets/crops.json.
CROPS_FILE = Path(__file__).resolve().parent / "crops.json"

# Gli originali su Commons arrivano a 12-16 MB: per una card non servono. Si
# chiede la miniatura scalata, che sta in poche centinaia di KB. Sotto questa
# soglia MediaWiki restituisce l'originale invece di ingrandirlo.
THUMB_WIDTH = 1400

# Cartella di destinazione per tipo. Le chiavi sono i valori di "kind".
DIR_PER_KIND = {"car": "cars", "track": "tracks"}


def titolo_commons(source_page: str) -> str:
    """Da .../wiki/File:Foo_bar.jpg al titolo "File:Foo bar.jpg"."""
    frammento = source_page.rsplit("/wiki/", 1)[-1]
    return urllib.parse.unquote(frammento).replace("_", " ")


def url_miniatura(source_page: str, larghezza: int) -> str:
    """URL della versione scalata, via Special:FilePath.

    Si passa dal titolo del file e non da image_url perche' quell'URL punta
    all'originale a piena risoluzione (e in una delle due esportazioni portava
    pure i parametri di tracciamento utm_* di Commons). Special:FilePath e'
    l'indirizzo stabile: se un domani il file viene spostato su un altro shard
    di upload.wikimedia.org, continua a risolvere.
    """
    titolo = titolo_commons(source_page)
    nome = titolo.split(":", 1)[-1].replace(" ", "_")
    return ("https://commons.wikimedia.org/wiki/Special:FilePath/"
            + urllib.parse.quote(nome) + f"?width={larghezza}")


def estensione(source_page: str) -> str:
    return titolo_commons(source_page).rsplit(".", 1)[-1].lower()


def carica_id_catalogo() -> dict[str, set[str]]:
    """Id noti al catalogo, per intercettare voci orfane prima di scaricare."""
    noti: dict[str, set[str]] = {}
    for kind, nome in (("car", "cars.json"), ("track", "tracks.json")):
        percorso = _DATA_DIR / nome
        noti[kind] = set()
        if not percorso.exists():
            continue
        dati = json.loads(percorso.read_text(encoding="utf-8"))
        noti[kind] = {e["id"] for e in dati}
    return noti


def _testo(html: str) -> str:
    """Via i tag: extmetadata restituisce l'autore come frammento HTML."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def riscopri_mappe() -> list[dict]:
    """Ricostruisce l'attribuzione dei layout SVG dai file gia' a disco.

    Si interroga Commons con lo SHA-1 del file (list=allimages&aisha1): e'
    un'identificazione esatta, non una ricerca per nome — gli SVG vengono
    scaricati interi, quindi il byte a disco e' lo stesso byte di Commons.
    Serve per non perdere l'attribuzione delle mappe scaricate da
    fetch_assets.py, il cui registro non e' persistito da nessuna parte.
    """
    # Si PARTE dal registro esistente invece che da zero. La riscoperta per
    # sha1 funziona solo sui file scaricati interi (il byte a disco e' quello di
    # Commons); i raster sono miniature scalate, il loro sha1 non corrisponde a
    # nulla, e una ricostruzione da zero li cancellerebbe dai crediti senza dare
    # errore. Chi si riconosce aggiorna la propria voce, gli altri restano.
    esistenti: dict[str, dict] = {}
    if MAPS_DEFAULT.exists():
        esistenti = {m["id"]: m for m in
                     json.loads(MAPS_DEFAULT.read_text(encoding="utf-8"))}

    trovate: list[dict] = []
    for f in sorted((OUT_DIR / "tracks").glob("*_map.svg")):
        ent_id = f.stem[: -len("_map")]
        sha1 = hashlib.sha1(f.read_bytes()).hexdigest()
        dati = api_get({"action": "query", "list": "allimages", "aisha1": sha1,
                        "aiprop": "url|user|extmetadata"})
        imgs = dati.get("query", {}).get("allimages", [])
        if not imgs:
            print(f"[maps] {ent_id}: nessun file su Commons con questo sha1 — salto")
            continue
        img = imgs[0]
        em = img.get("extmetadata", {})
        autore = _testo(em.get("Artist", {}).get("value", "")) or img.get("user", "")
        trovate.append({
            "id": ent_id,
            "kind": "track",
            "role": "map",
            "source_page": img.get("descriptionurl", ""),
            "license": em.get("LicenseShortName", {}).get("value", ""),
            "author": autore,
            "sha1": sha1,
        })
        print(f"[maps] {ent_id}: {img.get('title')} ({trovate[-1]['license']})")
    fusi = {**esistenti, **{t['id']: t for t in trovate}}
    ordinato = [fusi[k] for k in sorted(fusi)]
    MAPS_DEFAULT.write_text(json.dumps(ordinato, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    print(f"Scritto {MAPS_DEFAULT} ({len(ordinato)} layout, "
          f"{len(trovate)} riconosciuti adesso per sha1)")
    return ordinato


def scrivi_attribuzioni(voci: list[dict], scoperte: dict[str, list[str]],
                        mappe: list[dict]) -> None:
    """ATTRIBUTIONS.md: foto dal provino + layout SVG da maps.json.

    Il file viene riscritto per intero a ogni passata, quindi deve contenere
    ANCHE i layout: sono asset di terzi sotto CC come le foto, e l'obbligo di
    attribuzione non sparisce perche' li ha scaricati un altro script.
    """
    righe = [
        "# Attribuzioni asset — PitWall.AI",
        "",
        "Generato automaticamente da `backend/scripts/apply_photos.py`. Non modificare a mano.",
        "",
        "Le foto di vetture e circuiti sono state scelte **una per una guardandole**",
        "(provino `provino_foto_v3.html`, export `backend/scripts/photos.json`); i layout",
        "SVG dei circuiti arrivano da `fetch_assets.py`. Tutto viene da Wikimedia Commons.",
        "",
        "Le licenze CC BY e CC BY-SA richiedono che autore e licenza siano visibili",
        "all'utente finale: questo file va reso raggiungibile dall'app (pagina /crediti),",
        "non solo dal repo.",
        "",
        "> I loghi dei costruttori non sono inclusi: sono marchi registrati e la ricerca",
        "> automatica restituiva l'oggetto sbagliato (per le Porsche il logo di 9ff, che",
        "> e' un'altra azienda). Servirebbe una fonte curata, non una ricerca.",
        "",
        # Sei colonne, in quest'ordine: la pagina /crediti le legge con una
        # regex ancorata a `$`. Aggiungerne una (era stata provata "Confidenza")
        # non da' errore: la tabella smette semplicemente di agganciare e la
        # pagina si mostra VUOTA. Se cambi qui, cambia anche
        # frontend/src/app/(app)/crediti/page.tsx.
        "| File | Entita' | Ruolo | Autore | Licenza | Pagina Commons |",
        "|---|---|---|---|---|---|",
    ]

    def riga(file: str, ent_id: str, ruolo: str, autore: str, licenza: str, pagina: str) -> str:
        # Le pipe dentro un campo spezzerebbero la tabella markdown.
        pulisci = lambda s: (s or "-").replace("|", "/").strip() or "-"  # noqa: E731
        # Le parentesi nell'URL vanno codificate: un titolo come
        # "File:Ferrari_296_GT3_(DSC02308).jpg" chiude il link in anticipo e la
        # riga non viene piu' riconosciuta dal parser di /crediti — sparisce
        # dalla pagina senza un errore. Erano 26 righe su 78.
        link = pagina.replace("(", "%28").replace(")", "%29")
        return (f"| `{file}` | {ent_id} | {ruolo} | {pulisci(autore)} | "
                f"{pulisci(licenza)} | [link]({link}) |")

    for v in sorted(voci, key=lambda x: (x["kind"], x["id"])):
        righe.append(riga(v["file"], v["id"], "photo", v.get("author"),
                          v.get("license"), v["source_page"]))
    for m in sorted(mappe, key=lambda x: x["id"]):
        # Il percorso arriva dal registro quando c'e' (lo scrive apply_maps.py):
        # i layout scelti a occhio nel provino sono spesso PNG, e l'estensione
        # ".svg" scritta a mano qui indicava nei crediti un file inesistente.
        percorso = m.get("file") or f"frontend/public/assets/tracks/{m['id']}_map.svg"
        righe.append(riga(percorso, m["id"], "map", m.get("author"),
                          m.get("license"), m["source_page"]))

    if any(scoperte.values()):
        righe += [
            "",
            "## Senza foto (volutamente)",
            "",
            "Nel provino non e' stato trovato nessun candidato che mostrasse davvero il",
            "soggetto giusto. Meglio nessuna immagine che una sbagliata: la UI regge il",
            "caso e non mostra la banda.",
            "",
            "| Entita' | Tipo |",
            "|---|---|",
        ]
        for kind, ids in scoperte.items():
            for i in sorted(ids):
                righe.append(f"| {i} | {kind} |")

    ATTRIB_FILE.parent.mkdir(parents=True, exist_ok=True)
    ATTRIB_FILE.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print(f"Scritto {ATTRIB_FILE}")


def pubblica_ritagli() -> None:
    """Copia i ritagli scelti a mano fra gli asset serviti dal frontend.

    L'originale sta in backend/scripts/ ed e' versionato (e' lavoro umano, non
    si rigenera); la copia in public/assets/ e' un artefatto come il manifest,
    e vive nella cartella gitignorata insieme alle immagini.
    """
    sorgente = CROPS_FILE
    if not sorgente.exists():
        print(f"NOTA: {sorgente.name} assente — le foto useranno il ritaglio centrato. "
              f"Generane uno con build_crop_tool.py.")
        return
    dati = json.loads(sorgente.read_text(encoding="utf-8"))
    dest = OUT_DIR / "crops.json"
    dest.write_text(json.dumps(dati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Scritto {dest} ({len(dati.get('items', {}))} ritagli, "
          f"banda {dati.get('band', {}).get('w')}x{dati.get('band', {}).get('h')})")


def main() -> None:
    p = argparse.ArgumentParser(description="Applica photos.json agli asset di PitWall.AI")
    p.add_argument("--photos", type=Path, default=PHOTOS_DEFAULT,
                   help="export del provino (default: backend/scripts/photos.json)")
    p.add_argument("--dry-run", action="store_true",
                   help="mostra le operazioni senza toccare i file")
    p.add_argument("--width", type=int, default=THUMB_WIDTH,
                   help="larghezza miniatura richiesta a Commons")
    p.add_argument("--only", type=str, default="", help="lista di id separati da virgola")
    p.add_argument("--no-download", action="store_true", dest="no_download",
                   help="non riscarica le foto gia' a disco: riscrive solo manifest "
                        "e attribuzioni")
    p.add_argument("--riscopri-mappe", action="store_true", dest="riscopri_mappe",
                   help="ricostruisce maps.json interrogando Commons con lo sha1 degli SVG")
    args = p.parse_args()
    solo = {s.strip() for s in args.only.split(",") if s.strip()}

    if args.riscopri_mappe and not args.dry_run:
        riscopri_mappe()

    mappe: list[dict] = []
    if MAPS_DEFAULT.exists():
        mappe = json.loads(MAPS_DEFAULT.read_text(encoding="utf-8"))
    else:
        print(f"NOTA: {MAPS_DEFAULT.name} assente — i layout SVG resteranno senza "
              f"attribuzione. Rigeneralo con --riscopri-mappe.")

    voci = json.loads(args.photos.read_text(encoding="utf-8"))
    noti = carica_id_catalogo()

    # Guardia: una voce con id sconosciuto scriverebbe un file che nessuna
    # pagina cerchera' mai. Si ferma prima di scaricare 50 immagini a vuoto.
    orfani = [v["id"] for v in voci if v["id"] not in noti.get(v["kind"], set())]
    if orfani:
        sys.exit(f"ERRORE: id non presenti nel catalogo: {', '.join(orfani)}")

    per_url: dict[str, list[str]] = {}
    for v in voci:
        per_url.setdefault(v["image_url"], []).append(v["id"])
    ripetuti = {u: ids for u, ids in per_url.items() if len(ids) > 1}
    if ripetuti:
        print("ATTENZIONE: stessa foto usata da piu' entita':")
        for u, ids in ripetuti.items():
            print(f"  {', '.join(ids)} -> {u}")

    registro: list[dict] = []
    for v in voci:
        if solo and v["id"] not in solo:
            continue
        tipo = DIR_PER_KIND[v["kind"]]
        ext = estensione(v["source_page"])
        dest = OUT_DIR / tipo / f"{v['id']}_photo.{ext}"
        url = url_miniatura(v["source_page"], args.width)

        # Le vecchie foto possono avere un'altra estensione (jpg -> png): senza
        # questa pulizia resterebbero a disco e il manifest ne indicizzerebbe due.
        dest.parent.mkdir(parents=True, exist_ok=True)
        vecchie = [f for f in dest.parent.glob(f"{v['id']}_photo.*") if f != dest]

        if args.no_download and dest.exists():
            registro.append({**v, "file": dest.relative_to(_ROOT).as_posix()})
            continue

        print(f"[{tipo}] {v['id']} - {v.get('confidence', '?')} -> {dest.name}")
        if args.dry_run:
            print(f"    {url}")
            for f in vecchie:
                print(f"    rimuoverebbe {f.name}")
        else:
            scarica(url, dest)
            for f in vecchie:
                f.unlink()
            print(f"    {dest.stat().st_size // 1024} KB")
            time.sleep(0.3)  # cortesia verso Commons

        registro.append({**v, "file": dest.relative_to(_ROOT).as_posix()})

    # Entita' senza foto approvata: la vecchia (sbagliata) va via.
    coperti = {v["id"] for v in voci}
    scoperte: dict[str, list[str]] = {"car": [], "track": []}
    for kind, tipo in DIR_PER_KIND.items():
        cartella = OUT_DIR / tipo
        for i in sorted(noti.get(kind, set()) - coperti):
            scoperte[kind].append(i)
            for f in cartella.glob(f"{i}_photo.*"):
                print(f"[{tipo}] {i} - nessuna foto approvata -> rimuovo {f.name}")
                if not args.dry_run:
                    f.unlink()

    if args.dry_run:
        print("\n(dry-run: manifest e attribuzioni non riscritti)")
        return

    scrivi_attribuzioni(registro, scoperte, mappe)
    scrivi_manifest()
    pubblica_ritagli()
    print(f"\nFatto: {len(registro)} foto applicate, "
          f"{sum(len(v) for v in scoperte.values())} entita' lasciate senza foto.")


if __name__ == "__main__":
    main()
