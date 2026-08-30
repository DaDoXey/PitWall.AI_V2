"""core/catalog.py — catalogo vetture e circuiti ACC (Lotto 1).

Sorgente di verità del CATALOGO: `data/cars.json` (31 GT3) e `data/tracks.json`
(25 circuiti). NON è un file protetto: i numeri della demo restano in
`demo_data.py`, qui vive solo l'anagrafica (identità, specifiche, didascalie,
riferimenti asset).

**Identità = slug.** L'app storicamente identifica auto e piste con il nome di
display ("BMW M4 GT3", "Monza"); il catalogo usa slug stabili (`bmw_m4_gt3`).
`resolve_car()` / `resolve_track()` fanno da ponte: normalizzano il testo e,
per i casi che la normalizzazione non copre, consultano ALIAS_* — così le
liste storiche di `catalog.ts` e `demo_data.SESSION` continuano a funzionare
senza che nessuno debba riscrivere le stringhe.

Nessun dato viene inventato: i campi incerti restano marcati nel JSON
(`confidence`, `da_verificare`) e vengono serviti così come sono.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).resolve().parent / "data"
_CARS_PATH = _DATA_DIR / "cars.json"
_TRACKS_PATH = _DATA_DIR / "tracks.json"

# Cache di modulo: i JSON sono statici, si leggono una volta sola.
_CARS_CACHE: list[dict[str, Any]] | None = None
_TRACKS_CACHE: list[dict[str, Any]] | None = None


# ─────────────────────────────────────────────
# ALIAS — nomi storici dell'app → slug del catalogo
# ─────────────────────────────────────────────
# Coprono i casi in cui la normalizzazione non basta perché il nome di display
# usato dall'app e quello del catalogo divergono davvero (non solo per
# maiuscole/accenti). Verificati uno a uno contro cars.json.
ALIAS_CARS: dict[str, str] = {
    # catalog.ts dice "Porsche 992 GT3 R", il catalogo "Porsche 911 GT3 R (992)"
    "porsche992gt3r": "porsche_992_gt3_r",
    "porsche991iigt3r": "porsche_911_ii_gt3_r_991",
    "porsche991gt3r": "porsche_911_gt3_r_991",
    # "Mercedes-AMG GT3 Evo" → brand "Mercedes-AMG" + model "AMG GT3 Evo"
    "mercedesamggt3evo": "mercedes_amg_gt3_evo",
    "mercedesamggt3": "mercedes_amg_gt3",
    # "Huracán GT3 EVO2" (maiuscole diverse dal catalogo "Evo2")
    "lamborghinihuracangt3evo2": "lamborghini_huracan_gt3_evo2",
    # Nome ACC storico della Jaguar (record ripulito: brand Jaguar, model Emil Frey G3)
    "emilfreyjaguarg3": "emil_frey_jaguar_gt3",
    "jaguaremilfreyg3": "emil_frey_jaguar_gt3",
}

ALIAS_TRACKS: dict[str, str] = {
    # Nomi brevi usati da catalog.ts / demo_data rispetto ai nomi ufficiali.
    "spafrancorchamps": "spa_francorchamps",
    "nurburgringgp": "nurburgring_gp",
    "nurburgring": "nurburgring_gp",
    "barcelona": "barcelona_catalunya",
    "mountpanorama": "mount_panorama",
    "paulricard": "paul_ricard",
    "brandshatch": "brands_hatch",
    "lagunaseca": "laguna_seca",
    "redbullring": "red_bull_ring",
    "doningtonpark": "donington_park",
    "oultonpark": "oulton_park",
    "watkinsglen": "watkins_glen",
    "valencia": "valencia_ricardo_tormo",
    "nordschleife": "nurburgring_nordschleife",
}


# Nome breve per selettori e intestazioni: i nomi ufficiali ("Autodromo
# Nazionale Monza") sono troppo lunghi per la UI e incoerenti col resto
# dell'app, che ha sempre detto "Monza". Mappa curata a mano — esplicita e
# verificabile, invece di uno stripping a regex dei prefissi. Chi non è qui
# usa il nome ufficiale.
SHORT_NAMES: dict[str, str] = {
    "monza": "Monza",
    "spa_francorchamps": "Spa-Francorchamps",
    "nurburgring_nordschleife": "Nordschleife",
    "nurburgring_gp": "Nürburgring GP",
    "barcelona_catalunya": "Barcelona",
    "brands_hatch": "Brands Hatch",
    "misano": "Misano",
    "paul_ricard": "Paul Ricard",
    "silverstone": "Silverstone",
    "zandvoort": "Zandvoort",
    "zolder": "Zolder",
    "imola": "Imola",
    "snetterton": "Snetterton",
    "mount_panorama": "Mount Panorama",
    "laguna_seca": "Laguna Seca",
    "suzuka": "Suzuka",
    "kyalami": "Kyalami",
    "indianapolis": "Indianapolis",
    "watkins_glen": "Watkins Glen",
    "cota": "COTA",
    "valencia_ricardo_tormo": "Valencia",
    "red_bull_ring": "Red Bull Ring",
    # Hungaroring, Oulton Park, Donington Park: nome ufficiale già breve.
}


def short_name_track(track: dict[str, Any]) -> str:
    """Etichetta breve per UI; fallback al nome ufficiale."""
    return SHORT_NAMES.get(track.get("id") or "", track.get("name") or "")


def _norm(s: str | None) -> str:
    """Chiave di confronto: solo lettere e cifre, minuscole, accenti appiattiti."""
    if not s:
        return ""
    s = (
        s.replace("á", "a").replace("à", "a").replace("é", "e").replace("è", "e")
        .replace("í", "i").replace("ì", "i").replace("ó", "o").replace("ò", "o")
        .replace("ú", "u").replace("ù", "u").replace("ü", "u").replace("ö", "o")
    )
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _load(path: Path, cache_name: str) -> list[dict[str, Any]]:
    """Carica un JSON del catalogo. Lista vuota se assente o malformato: il
    catalogo è un arricchimento, non deve mai far cadere l'API."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def all_cars() -> list[dict[str, Any]]:
    global _CARS_CACHE
    if _CARS_CACHE is None:
        _CARS_CACHE = _load(_CARS_PATH, "cars")
    return _CARS_CACHE


def all_tracks() -> list[dict[str, Any]]:
    global _TRACKS_CACHE
    if _TRACKS_CACHE is None:
        _TRACKS_CACHE = _load(_TRACKS_PATH, "tracks")
    return _TRACKS_CACHE


def display_name_car(car: dict[str, Any]) -> str:
    """Nome mostrato all'utente: 'BMW M4 GT3'. Evita il doppione quando il
    model ripete già il brand."""
    brand, model = (car.get("brand") or "").strip(), (car.get("model") or "").strip()
    if not brand:
        return model
    if _norm(model).startswith(_norm(brand)):
        return model
    return f"{brand} {model}".strip()


def display_names_by_id() -> dict[str, str]:
    """Nomi di display UNIVOCI, id → nome.

    Alcune vetture condividono lo stesso nome commerciale in annate diverse
    (Bentley Continental GT3 2015/2018, Nissan GT-R Nismo GT3 2015/2018).
    Servirle con lo stesso testo rende la seconda irraggiungibile — il valore
    inviato all'API sarebbe identico e `resolve_car` restituirebbe sempre la
    prima — oltre a produrre chiavi React duplicate. Dove il nome collide si
    aggiunge l'anno: "Bentley Continental GT3 (2018)". La forma con anno resta
    risolvibile perché gli id di quelle vetture terminano già con l'annata.
    """
    cars = all_cars()
    counts: dict[str, int] = {}
    for c in cars:
        n = display_name_car(c)
        counts[n] = counts.get(n, 0) + 1
    out: dict[str, str] = {}
    for c in cars:
        n = display_name_car(c)
        if counts[n] > 1 and c.get("year"):
            n = f"{n} ({c['year']})"
        out[c["id"]] = n
    return out


def _car_keys(car: dict[str, Any]) -> set[str]:
    """Tutte le chiavi normalizzate con cui una vettura può essere nominata."""
    keys = {
        _norm(car.get("id")),
        _norm(car.get("acc_car_id")),
        _norm(display_name_car(car)),
        _norm(car.get("model")),
    }
    # Forma disambiguata "Nome (2018)": è quella che la UI invia per le vetture
    # con nome duplicato, quindi deve risolvere.
    year = car.get("year")
    if year:
        keys.add(_norm(f"{display_name_car(car)} ({year})"))
    return keys - {""}


def _track_keys(track: dict[str, Any]) -> set[str]:
    return {
        _norm(track.get("id")),
        _norm(track.get("acc_track_id")),
        _norm(track.get("name")),
        _norm(track.get("nick")),
        _norm(short_name_track(track)),
    } - {""}


def resolve_car(name: str | None) -> dict[str, Any] | None:
    """Trova una vettura da slug, acc_car_id, nome di display o alias storico.
    None se non c'è corrispondenza (mai un match a caso)."""
    key = _norm(name)
    if not key:
        return None
    cars = all_cars()
    # L'alias punta allo slug "vero" (con underscore): va normalizzato come le
    # chiavi di confronto, altrimenti non aggancia mai.
    key = _norm(ALIAS_CARS.get(key, key))
    for c in cars:
        if key in _car_keys(c):
            return c
    return None


def resolve_track(name: str | None) -> dict[str, Any] | None:
    """Trova un circuito da slug, acc_track_id, nome ufficiale, soprannome o alias."""
    key = _norm(name)
    if not key:
        return None
    tracks = all_tracks()
    key = _norm(ALIAS_TRACKS.get(key, key))
    for t in tracks:
        if key in _track_keys(t):
            return t
    return None


def car_summary(car: dict[str, Any]) -> dict[str, Any]:
    """Vista compatta per i selettori: quel che serve a popolare una lista."""
    return {
        "id": car.get("id"),
        "display_name": display_names_by_id().get(car.get("id", ""), display_name_car(car)),
        "brand": car.get("brand"),
        "model": car.get("model"),
        "year": car.get("year"),
        "category": car.get("category"),
        "dlc": bool(car.get("dlc")),
        "dlc_pack": car.get("dlc_pack"),
    }


def track_summary(track: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": track.get("id"),
        "name": track.get("name"),
        "short_name": short_name_track(track),
        "nick": track.get("nick"),
        "country": track.get("country"),
        "length_km": track.get("length_km"),
        "corners": track.get("corners"),
        "downforce_level": track.get("downforce_level"),
        "dlc": bool(track.get("dlc")),
        "dlc_pack": track.get("dlc_pack"),
    }


def catalog_index() -> dict[str, Any]:
    """Indice completo per i selettori (liste compatte + conteggi)."""
    cars, tracks = all_cars(), all_tracks()
    categories: dict[str, int] = {}
    for c in cars:
        cat = c.get("category") or "n.d."
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "cars": [car_summary(c) for c in cars],
        "tracks": [track_summary(t) for t in tracks],
        "counts": {
            "cars": len(cars),
            "tracks": len(tracks),
            "by_category": categories,
        },
    }
