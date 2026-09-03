#!/usr/bin/env python3
"""
fetch_assets.py — risolutore asset Wikimedia Commons per PitWall.AI

Perche' esiste:
    cars.json e tracks.json NON contengono URL diretti alle immagini. Contengono
    "commons_query" e "commons_category", cioe' indizi di ricerca. Gli URL diretti
    scritti a mano invecchiano male (i file su Commons vengono rinominati, spostati
    e cancellati) e non sono verificabili in fase di stesura: il risultato sarebbe
    una lista di link morti travestita da dato certo.

    Questo script risolve gli indizi contro l'API di Commons *al momento
    dell'esecuzione*, ti mostra i candidati, scarica quelli che approvi e scrive
    ATTRIBUTIONS.md con autore e licenza di ogni file. Cosi' l'attribuzione
    richiesta dalle licenze CC non e' un buon proposito ma un artefatto generato.

Uso:
    python fetch_assets.py --dry-run              # elenca i candidati, non scarica
    python fetch_assets.py --interactive          # chiede conferma per ogni asset
    python fetch_assets.py --auto                 # prende il primo candidato valido
    python fetch_assets.py --only monza,bmw_m4_gt3

Requisiti:
    pip install requests

NOTA: lo script non e' stato eseguito contro l'API live in fase di stesura
(ambiente senza accesso a commons.wikimedia.org). Fai una prima passata con
--dry-run e segnala eventuali scostamenti nello schema di risposta.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"

# Wikimedia richiede uno User-Agent identificativo e blocca le richieste anonime
# massive. Identifichiamo il progetto con la sua repo pubblica: è un contatto
# raggiungibile senza esporre l'email personale dell'autore.
UA = "PitWall.AI-asset-fetcher/1.0 (https://github.com/DaDoXey/PitWall.AI_V2)"

# HTTP con la sola stdlib: lo script è uno strumento di build, non runtime
# dell'API, e non deve aggiungere `requests` alle dipendenze del server.
# (urllib è anche il modo affidabile di leggere byte grezzi su Windows —
# lezione di INC-V2-002.)
TIMEOUT = 30

# Licenze accettate senza discussione. Tutto il resto viene segnalato e saltato
# in modalita' --auto (in --interactive decidi tu caso per caso).
LICENZE_OK = {
    "cc0", "cc-zero", "publicdomain", "pd", "pd-textlogo", "pd-shape",
    "cc-by-2.0", "cc-by-3.0", "cc-by-4.0",
    "cc-by-sa-2.0", "cc-by-sa-3.0", "cc-by-sa-4.0",
}

# Percorsi ancorati alla radice del repo (lo script vive in backend/scripts/),
# così funziona da qualunque cwd.
_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = _ROOT / "frontend" / "public" / "assets"
ATTRIB_FILE = _ROOT / "frontend" / "public" / "assets" / "ATTRIBUTIONS.md"
_DATA_DIR = _ROOT / "backend" / "app" / "core" / "data"


def _http_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        # Commons risponde JSON UTF-8: si decodifica esplicitamente, mai
        # affidandosi al default della piattaforma.
        return json.loads(resp.read().decode("utf-8"))


def api_get(params: dict) -> dict:
    params = {**params, "format": "json", "formatversion": "2"}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    data = _http_json(url)
    time.sleep(0.4)  # cortesia verso l'API, non superare ~1 req/s
    return data


# Larghezza della miniatura richiesta a Commons per le immagini raster: gli
# originali arrivano a 12-16 MB, la versione scalata sta in poche centinaia di
# KB ed è più che sufficiente per una card. Gli SVG si scaricano interi.
THUMB_WIDTH = 1400

# Parole che, nel nome file, segnalano contenuto NON pertinente alla vettura da
# corsa (versioni stradali, musei, saloni) o layout storici di un circuito.
RUMORE = {"museum", "museo", "concept", "prototype", "1922", "1955", "1939", "oval"}


def _tokens(testo: str) -> set[str]:
    """Parole significative (>=2 caratteri) di una stringa, minuscole."""
    return {w for w in re.split(r"[^a-z0-9]+", testo.lower()) if len(w) >= 2}


def punteggio(titolo: str, attesi: set[str], obbligatori: set[str]) -> int:
    """Quanto un file Commons somiglia a ciò che cerchiamo.

    -1 = da scartare. La ricerca full-text di Commons restituisce parecchio
    rumore (per "Ferrari 296 GT3" tornano foto di piloti e saloni), e prendere
    il primo risultato valido per licenza significa pubblicare l'immagine
    sbagliata: la M4 stradale al posto della M4 GT3. Meglio nessuna immagine
    che una scorretta.
    """
    t = _tokens(titolo)
    # I token obbligatori discriminano la variante da corsa: senza "gt3" nel
    # nome, "BMW M4" è quasi sempre la vettura stradale.
    if obbligatori and not obbligatori.issubset(t):
        return -1
    if t & RUMORE:
        return -1
    return len(attesi & t)


def cerca_candidati(query: str, categoria: str | None, formato: str, limite: int = 6) -> list[str]:
    """Restituisce nomi file ('File:...') ordinati per rilevanza."""
    estensioni = {"svg": ["svg"], "jpg": ["jpg", "jpeg", "png"], "png": ["png", "jpg"]}
    ext_ok = estensioni.get(formato, ["jpg", "png", "svg"])

    titoli: list[str] = []

    # 1) prima la categoria, se dichiarata: piu' precisa della ricerca libera
    if categoria:
        try:
            dati = api_get({
                "action": "query", "list": "categorymembers",
                "cmtitle": categoria, "cmtype": "file", "cmlimit": limite * 3,
            })
            titoli += [m["title"] for m in dati.get("query", {}).get("categorymembers", [])]
        except Exception as e:
            print(f"    [!] categoria '{categoria}' non risolta: {e}")

    # 2) fallback: ricerca full-text nel namespace File
    if len(titoli) < limite:
        try:
            dati = api_get({
                "action": "query", "list": "search",
                "srsearch": query, "srnamespace": "6", "srlimit": limite * 3,
            })
            titoli += [m["title"] for m in dati.get("query", {}).get("search", [])]
        except Exception as e:
            print(f"    [!] ricerca '{query}' fallita: {e}")

    filtrati = [t for t in dict.fromkeys(titoli)
                if t.rsplit(".", 1)[-1].lower() in ext_ok]

    # Ordinamento per pertinenza: la ricerca di Commons ordina per rilevanza
    # testuale, non per "è davvero questa vettura". Chi ha punteggio -1 esce.
    attesi = _tokens(query)
    obbligatori = {c for c in ("gt3", "gt4", "gt2") if c in attesi}
    con_voto = [(punteggio(t, attesi, obbligatori), t) for t in filtrati]
    con_voto = [(p, t) for p, t in con_voto if p >= 0]
    con_voto.sort(key=lambda x: -x[0])
    return [t for _, t in con_voto[:limite]]


def info_file(titolo: str) -> dict | None:
    """Metadati di licenza e URL diretto per un file Commons."""
    # iiurlwidth chiede a Commons una versione RIDIMENSIONATA: gli originali
    # arrivano a 12-16 MB, inservibili in pagina. Si scarica la miniatura a
    # THUMB_WIDTH px invece di ridimensionare in locale (nessuna dipendenza
    # grafica) — per gli SVG resta l'originale, che è vettoriale e leggero.
    dati = api_get({
        "action": "query", "titles": titolo, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size|mime", "iiurlwidth": str(THUMB_WIDTH),
    })
    pagine = dati.get("query", {}).get("pages", [])
    if not pagine or "imageinfo" not in pagine[0]:
        return None
    ii = pagine[0]["imageinfo"][0]
    meta = ii.get("extmetadata", {})

    def campo(k: str) -> str:
        return re.sub(r"<[^>]+>", "", str(meta.get(k, {}).get("value", ""))).strip()

    is_svg = (ii.get("mime") or "") == "image/svg+xml"
    return {
        "titolo": titolo,
        # URL da scaricare: originale per gli SVG, miniatura scalata per i raster.
        "url": ii.get("url") if is_svg else (ii.get("thumburl") or ii.get("url")),
        "url_originale": ii.get("url"),
        "scalato": bool(ii.get("thumburl")) and not is_svg,
        "pagina": ii.get("descriptionurl"),
        "mime": ii.get("mime"),
        "byte": ii.get("size"),
        "larghezza": ii.get("width"),
        "altezza": ii.get("height"),
        "licenza": campo("LicenseShortName") or campo("License"),
        "licenza_code": campo("License").lower(),
        "autore": campo("Artist") or "sconosciuto",
        "fonte": campo("Credit") or "Wikimedia Commons",
    }


def licenza_accettabile(info: dict) -> bool:
    code = (info.get("licenza_code") or "").lower()
    breve = (info.get("licenza") or "").lower().replace(" ", "-")
    return any(ok in code or ok in breve for ok in LICENZE_OK)


def scarica(url: str, destinazione: Path) -> None:
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        destinazione.write_bytes(resp.read())


# Ruoli che NON si risolvono da Commons. I loghi dei costruttori sono
# trademark: o mancano del tutto (13 marchi su 31 senza candidati), o la
# ricerca restituisce l'oggetto sbagliato — nella passata del 30/08:
# "3-BMW.svg" (un disegno di vettura), l'Aston Martin del 1920 e "9ff_logo.svg"
# per le Porsche, che è un'azienda diversa. Un logo errato è un errore fattuale
# mostrato all'utente: meglio nessun logo. Servirebbe una fonte curata
# (press kit ufficiali), non una ricerca automatica.
RUOLI_ESCLUSI = {"logo"}


def elabora(entita: list[dict], tipo: str, args, registro: list[dict]) -> None:
    for ent in entita:
        if args.only and ent["id"] not in args.only:
            continue
        for ruolo, spec in ent.get("assets", {}).items():
            if ruolo in RUOLI_ESCLUSI:
                continue
            query = spec.get("commons_query")
            if not query:
                continue
            print(f"\n[{tipo}] {ent['id']} · {ruolo}")
            candidati = cerca_candidati(query, spec.get("commons_category"),
                                        spec.get("preferred_format", "jpg"))
            if not candidati:
                print("    NESSUN CANDIDATO — da risolvere a mano")
                registro.append({"entita": ent["id"], "ruolo": ruolo, "esito": "nessun_candidato"})
                continue

            scelto = None
            for idx, titolo in enumerate(candidati):
                info = info_file(titolo)
                if not info:
                    continue
                ok = licenza_accettabile(info)
                marchio = "OK " if ok else "?? "
                nota = f" -> scala a {THUMB_WIDTH}px" if info.get("scalato") else ""
                print(f"    {marchio}[{idx}] {titolo}  ({info['licenza']}, "
                      f"{info['larghezza']}x{info['altezza']}, "
                      f"{(info['byte'] or 0)//1024} KB{nota})")
                if args.dry_run:
                    continue
                if args.auto and ok and scelto is None:
                    scelto = info
                elif args.interactive:
                    risposta = input("       usare questo? [s/N/q] ").strip().lower()
                    if risposta == "q":
                        return
                    if risposta == "s":
                        scelto = info
                        break

            if args.dry_run or scelto is None:
                if not args.dry_run:
                    print("    SALTATO — nessun candidato con licenza accettabile")
                    registro.append({"entita": ent["id"], "ruolo": ruolo, "esito": "licenza_non_idonea"})
                continue

            ext = scelto["titolo"].rsplit(".", 1)[-1].lower()
            dest = OUT_DIR / tipo / f"{ent['id']}_{ruolo}.{ext}"
            scarica(scelto["url"], dest)
            print(f"    -> {dest}")
            registro.append({
                "entita": ent["id"], "ruolo": ruolo, "esito": "scaricato",
                # Percorso RELATIVO alla radice del repo: ATTRIBUTIONS.md è un
                # file versionato e mostrato in pagina, non deve contenere la
                # home dell'autore.
                "file": dest.relative_to(_ROOT).as_posix(), **scelto,
            })


def scrivi_manifest() -> None:
    """Indice degli asset presenti su disco, per il frontend.

    Serve perché l'estensione varia (jpg/png/svg) e la copertura è parziale:
    senza indice la UI dovrebbe tentare una URL e gestire il 404. Si ricava
    dalla cartella, non dal registro dell'ultima esecuzione, così resta
    corretto anche dopo passate parziali (--only).
    """
    manifest: dict[str, dict[str, str]] = {"cars": {}, "tracks": {}}
    for tipo in ("cars", "tracks"):
        d = OUT_DIR / tipo
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if not f.is_file():
                continue
            nome = f.stem  # "{id}_{ruolo}"
            if "_" not in nome:
                continue
            ent_id, _, ruolo = nome.rpartition("_")
            manifest[tipo].setdefault(ent_id, {})[ruolo] = f"/assets/{tipo}/{f.name}"

    dest = OUT_DIR / "manifest.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    n = sum(len(v) for tipo in manifest.values() for v in tipo.values())
    print(f"Scritto {dest} ({n} asset)")


def scrivi_attribuzioni(registro: list[dict]) -> None:
    righe = [
        "# Attribuzioni asset — PitWall.AI",
        "",
        "Generato automaticamente da `fetch_assets.py`. Non modificare a mano.",
        "",
        "Tutti gli asset provengono da Wikimedia Commons. Le licenze CC BY e CC BY-SA",
        "richiedono che autore e licenza siano visibili all'utente finale: questo file",
        "va reso raggiungibile dall'app (pagina crediti o footer), non solo dal repo.",
        "",
        "> I loghi dei costruttori restano marchi registrati dei rispettivi titolari",
        "> anche quando il file immagine e' di pubblico dominio. L'uso qui e' puramente",
        "> identificativo del veicolo. Per un progetto commerciale, verifica con un",
        "> consulente: questo file non e' un parere legale.",
        "",
        "| File | Entita' | Ruolo | Autore | Licenza | Pagina Commons |",
        "|---|---|---|---|---|---|",
    ]
    for r in registro:
        if r.get("esito") != "scaricato":
            continue
        righe.append(
            f"| `{r['file']}` | {r['entita']} | {r['ruolo']} | {r['autore']} | "
            f"{r['licenza']} | [link]({r['pagina']}) |"
        )

    mancanti = [r for r in registro if r.get("esito") != "scaricato"]
    if mancanti:
        righe += ["", "## Da risolvere a mano", "",
                  "| Entita' | Ruolo | Motivo |", "|---|---|---|"]
        for r in mancanti:
            righe.append(f"| {r['entita']} | {r['ruolo']} | {r['esito']} |")

    ATTRIB_FILE.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print(f"\nScritto {ATTRIB_FILE}")


def main() -> None:
    p = argparse.ArgumentParser(description="Risolve gli asset Commons di PitWall.AI")
    p.add_argument("--dry-run", action="store_true", help="elenca i candidati senza scaricare")
    p.add_argument("--auto", action="store_true", help="prende il primo candidato con licenza valida")
    p.add_argument("--interactive", action="store_true", help="chiede conferma per ogni asset")
    p.add_argument("--only", type=str, default="", help="lista di id separati da virgola")
    p.add_argument("--manifest-only", action="store_true",
                   help="rigenera solo manifest.json dagli asset già su disco")
    p.add_argument("--cars", type=Path, default=_DATA_DIR / "cars.json")
    p.add_argument("--tracks", type=Path, default=_DATA_DIR / "tracks.json")
    args = p.parse_args()

    if args.manifest_only:
        scrivi_manifest()
        return

    if not (args.dry_run or args.auto or args.interactive):
        p.error("scegli una modalita': --dry-run, --auto, --interactive o --manifest-only")

    args.only = {s.strip() for s in args.only.split(",") if s.strip()}

    registro: list[dict] = []
    if args.cars.exists():
        elabora(json.loads(args.cars.read_text(encoding="utf-8")), "cars", args, registro)
    if args.tracks.exists():
        elabora(json.loads(args.tracks.read_text(encoding="utf-8")), "tracks", args, registro)

    if not args.dry_run:
        scrivi_attribuzioni(registro)
        scrivi_manifest()


if __name__ == "__main__":
    main()
