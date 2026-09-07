#!/usr/bin/env python3
"""
apply_maps.py — porta a disco i layout SCELTI A OCCHIO nel provino delle mappe

Perche' esiste:
    Gemello di apply_photos.py, per i tracciati. `build_maps_proof.py` genera il
    provino, Edoardo guarda i disegni e sceglie, e l'export e' `maps_choice.json`:
    la lista dei layout approvati. Questo script prende quell'export e lo porta a
    disco — nessuna ricerca, nessuna euristica, solo il download di quello che e'
    gia' stato approvato.

    Sostituisce i layout scaricati a suo tempo da fetch_assets.py, che erano
    scelti sul NOME DEL FILE ed erano in gran parte sbagliati (spa = rallycross,
    imola = 1992, kyalami = 1968, zandvoort = 1989).

Tre cose che qui NON si possono fare come per le foto:

    1. **SVG e raster si scaricano in modo diverso.** Per una foto si chiede
       sempre la miniatura scalata. Su un SVG `Special:FilePath?width=` non
       restituisce l'SVG ridotto: restituisce un PNG *renderizzato*, che salvato
       come `.svg` sarebbe un file rotto. Gli SVG si scaricano quindi interi (e
       sono leggeri: 13-80 KB), i raster come miniatura.

    2. **Il vecchio file va rimosso, non sovrascritto.** I layout a disco sono
       `.svg`, le scelte nuove sono quasi tutte `.png`. Lasciando entrambi, il
       manifest indicizza `{id}_map.png` e `{id}_map.svg` sotto lo stesso ruolo
       "map" e vince l'ultimo in ordine alfabetico — cioe' proprio il vecchio
       file sbagliato. Si cancella ogni `{id}_map.*` diverso da quello nuovo.

    3. **Anche i `_layout.svg` vanno via.** clean_maps.py li ha generati
       ripulendo le etichette DAI FILE VECCHI: se il file di partenza era il
       tracciato sbagliato, il suo layout ripulito e' sbagliato uguale. E per
       decisione del 03/09 le etichette sulle mappe nuove RESTANO, quindi quei
       file non servono piu' a nessuno.

Uso:
    python backend/scripts/apply_maps.py                    # applica backend/scripts/maps_choice.json
    python backend/scripts/apply_maps.py --dry-run          # dice cosa farebbe
    python backend/scripts/apply_maps.py --scelte ~/Downloads/maps_choice.json
    python backend/scripts/apply_maps.py --no-crediti       # non rigenera ATTRIBUTIONS.md

Alla fine richiama `apply_photos.py --no-download`, che e' il posto unico dove
si riscrivono `manifest.json` e `ATTRIBUTIONS.md` (foto + layout insieme).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_assets import OUT_DIR, _ROOT, scarica  # noqa: E402

_DATA_DIR = _ROOT / "backend" / "app" / "core" / "data"
SCELTE_DEFAULT = Path(__file__).resolve().parent / "maps_choice.json"
MAPS_REGISTRO = Path(__file__).resolve().parent / "maps.json"
TRACKS_DIR = OUT_DIR / "tracks"

# Come per le foto: l'originale non serve. Qui pero' la soglia conta il doppio,
# perche' fra i candidati c'e' un PNG da 18989x17338 px (Zandvoort) che a piena
# risoluzione sono decine di MB per una banda da 540x280.
THUMB_WIDTH = 1400


def titolo_a_nome(titolo_file: str) -> str:
    """Da "File:Imola 2009.svg" al nome usato negli URL: "Imola_2009.svg"."""
    return titolo_file.split(":", 1)[-1].replace(" ", "_")


def url_scaricabile(voce: dict, larghezza: int) -> tuple[str, str]:
    """(url, estensione) per una voce scelta.

    Si passa da Special:FilePath e non dall'`image_url` dell'export: e'
    l'indirizzo stabile, che continua a risolvere anche se il file viene
    spostato su un altro shard di upload.wikimedia.org (stessa scelta di
    apply_photos.py). Sugli SVG si omette `width`, vedi la nota in cima.
    """
    ext = titolo_a_nome(voce["titolo_file"]).rsplit(".", 1)[-1].lower()
    base = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
            + urllib.parse.quote(titolo_a_nome(voce["titolo_file"])))
    if ext == "svg":
        return base, ext
    return f"{base}?width={larghezza}", ext


def carica_scelte(percorso: Path) -> tuple[list[dict], list[str]]:
    dati = json.loads(percorso.read_text(encoding="utf-8"))
    return dati.get("mappe", []), (dati.get("_meta", {}) or {}).get("senza_mappa", [])


def main() -> None:
    ap = argparse.ArgumentParser(description="Applica maps_choice.json ai layout dei circuiti")
    ap.add_argument("--scelte", type=Path, default=SCELTE_DEFAULT,
                    help="export del provino (default: backend/scripts/maps_choice.json)")
    ap.add_argument("--dry-run", action="store_true", help="mostra le operazioni senza toccare i file")
    ap.add_argument("--width", type=int, default=THUMB_WIDTH, help="larghezza miniatura per i raster")
    ap.add_argument("--no-crediti", action="store_true", dest="no_crediti",
                    help="non richiamare apply_photos.py per manifest e attribuzioni")
    args = ap.parse_args()

    if not args.scelte.exists():
        sys.exit(f"manca {args.scelte} — esporta le scelte dal provino "
                 f"(_provino_mappe.html) e mettile li'.")

    scelte, senza_mappa = carica_scelte(args.scelte)
    noti = {t["id"] for t in json.loads((_DATA_DIR / "tracks.json").read_text(encoding="utf-8"))}

    # Guardia: un id sconosciuto scriverebbe un file che nessuna pagina cerchera'.
    orfani = [v["id"] for v in scelte if v["id"] not in noti]
    if orfani:
        sys.exit(f"ERRORE: id non presenti in tracks.json: {', '.join(orfani)}")

    # Stesso file per due circuiti = quasi sempre un errore di selezione.
    per_titolo: dict[str, list[str]] = {}
    for v in scelte:
        per_titolo.setdefault(v["titolo_file"], []).append(v["id"])
    for titolo, ids in per_titolo.items():
        if len(ids) > 1:
            print(f"ATTENZIONE: stessa mappa scelta per {', '.join(ids)} -> {titolo}")

    registro_nuovo: dict[str, dict] = {}
    TRACKS_DIR.mkdir(parents=True, exist_ok=True)

    for v in scelte:
        url, ext = url_scaricabile(v, args.width)
        dest = TRACKS_DIR / f"{v['id']}_map.{ext}"
        # Il vecchio layout puo' avere un'altra estensione (svg -> png): senza
        # questa pulizia resta a disco e il manifest ne indicizza due sotto lo
        # stesso ruolo, con la vecchia mappa sbagliata che vince per ordine.
        vecchie = [f for f in TRACKS_DIR.glob(f"{v['id']}_map.*") if f != dest]
        # I layout ripuliti da clean_maps.py derivano dai file VECCHI: se la
        # mappa cambia, quelli sono spazzatura.
        ripuliti = list(TRACKS_DIR.glob(f"{v['id']}_layout.svg"))

        print(f"[tracks] {v['id']} -> {dest.name}")
        if args.dry_run:
            print(f"    {url}")
            for f in vecchie + ripuliti:
                print(f"    rimuoverebbe {f.name}")
        else:
            scarica(url, dest)
            for f in vecchie + ripuliti:
                f.unlink()
                print(f"    rimosso {f.name}")
            print(f"    {dest.stat().st_size // 1024} KB")
            time.sleep(0.3)  # cortesia verso Commons

        registro_nuovo[v["id"]] = {
            "id": v["id"],
            "kind": "track",
            "role": "map",
            "file": dest.relative_to(_ROOT).as_posix(),
            "source_page": v.get("source_page", ""),
            "license": v.get("license", ""),
            "author": v.get("author", ""),
            # Lo sha1 identifica il file su Commons SOLO quando si e' scaricato
            # l'originale: sulle miniature scalate il byte a disco e' diverso da
            # quello di Commons, quindi non si scrive un valore che sarebbe una
            # bugia. E' anche il motivo per cui apply_photos --riscopri-mappe
            # deve conservare queste voci invece di ricostruirle da zero.
            "sha1": (hashlib.sha1(dest.read_bytes()).hexdigest()
                     if ext == "svg" and dest.exists() and not args.dry_run else None),
        }

    # Piste marcate "Nessuna adatta": la mappa vecchia (sbagliata) va via.
    # Meglio nessuna immagine che una falsa — stessa regola delle foto.
    for tid in senza_mappa:
        for f in list(TRACKS_DIR.glob(f"{tid}_map.*")) + list(TRACKS_DIR.glob(f"{tid}_layout.svg")):
            print(f"[tracks] {tid} - nessuna mappa adatta -> rimuovo {f.name}")
            if not args.dry_run:
                f.unlink()

    if args.dry_run:
        print("\n(dry-run: registro, manifest e attribuzioni non riscritti)")
        return

    # --- registro delle attribuzioni: si FONDE, non si sovrascrive.
    # maps.json copre tutti e 25 i layout; qui ne stiamo cambiando pochi, e
    # buttare le voci degli altri li farebbe sparire in silenzio da /crediti.
    esistenti: list[dict] = []
    if MAPS_REGISTRO.exists():
        esistenti = json.loads(MAPS_REGISTRO.read_text(encoding="utf-8"))
    fusi = {m["id"]: m for m in esistenti}
    fusi.update(registro_nuovo)
    for tid in senza_mappa:
        fusi.pop(tid, None)
    ordinato = [fusi[k] for k in sorted(fusi)]
    MAPS_REGISTRO.write_text(json.dumps(ordinato, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    print(f"\nScritto {MAPS_REGISTRO.name}: {len(ordinato)} layout "
          f"({len(registro_nuovo)} aggiornati adesso)")

    if args.no_crediti:
        print("Manifest e attribuzioni NON rigenerati (--no-crediti). "
              "Ricordati:  python backend/scripts/apply_photos.py --no-download")
        return

    # manifest.json e ATTRIBUTIONS.md si scrivono in un posto solo (foto +
    # layout insieme): si richiama quello, invece di riscrivere qui la stessa
    # logica e rischiare due versioni divergenti della tabella dei crediti.
    print("\nRigenero manifest e attribuzioni (apply_photos.py --no-download):")
    esito = subprocess.run([sys.executable, str(Path(__file__).parent / "apply_photos.py"),
                            "--no-download"], cwd=str(_ROOT))
    if esito.returncode != 0:
        sys.exit("apply_photos.py e' fallito: manifest e crediti NON sono aggiornati.")


if __name__ == "__main__":
    main()
