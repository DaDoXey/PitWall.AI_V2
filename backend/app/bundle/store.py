"""bundle/store.py — dove vivono i bundle importati.

Un archivio su disco, volutamente stupido: un file JSON per sessione dentro
`backend/sessions/` (o `PITWALL_SESSIONS_DIR`), niente database. È coerente con la
decisione 1 del 14/09 — **locale-first**, il backend gira sul PC del pilota — e
rende un bundle un oggetto che si può copiare, aprire con un editor e mandare via
mail senza esportare nulla.

**Nessun indice separato.** L'elenco si ricava leggendo i file: un indice sarebbe
una seconda verità da tenere allineata, e le sessioni sono poche e leggere (i canali
di L3 vivranno in file a parte, non dentro il bundle). Se un giorno diventeranno
tante, l'indice si aggiunge allora, non «per sicurezza» adesso.

**Gli id arrivano dalla rete**, quindi sono validati due volte: con una regex e poi
controllando che il percorso risolto stia davvero dentro la cartella dell'archivio.
Un `..` in un id non deve poter leggere il `.env`.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from app.bundle.schema import SessionBundle

ID_VALIDO = re.compile(r"^[0-9]{8}-[0-9]{6}-[a-z0-9_]{1,48}-[0-9a-f]{4}$")


class ArchivioError(ValueError):
    """Operazione non eseguibile sull'archivio delle sessioni."""


class SessioneNonTrovata(ArchivioError):
    """L'id non corrisponde a nessuna sessione archiviata."""


class Riassunto(BaseModel):
    """Quel tanto che basta per una lista, senza aprire tutto il bundle."""

    id: str
    fonte: str
    car: str | None = None
    car_model_id: int | None = None
    track: str | None = None
    tipo_sessione: str
    pilota: str | None = None
    giri: int = 0
    giri_validi: int = 0
    miglior_giro_ms: int | None = None
    ha_setup: bool = False
    parametri_setup: int = 0
    assunzioni: int = 0
    importato_il: str | None = None
    iniziata_il: str | None = None
    mescola: str | None = None
    piattaforma: str | None = None
    ha_canali: bool = False
    ha_racconto: bool = False
    demo: bool = False
    riferimento: bool = False
    ritaglio_i2: bool = False


def cartella() -> Path:
    """La cartella dell'archivio, creata alla prima occorrenza."""
    grezzo = os.getenv("PITWALL_SESSIONS_DIR", "").strip()
    radice = Path(grezzo) if grezzo else Path(__file__).resolve().parents[2] / "sessions"
    radice.mkdir(parents=True, exist_ok=True)
    return radice


def _pezzo_leggibile(bundle: SessionBundle) -> str:
    """Un frammento di nome che dica a colpo d'occhio di che sessione si tratta."""
    pezzi = [p for p in (bundle.meta.track, bundle.meta.car) if p]
    testo = "-".join(pezzi) if pezzi else "sessione"
    testo = unicodedata.normalize("NFKD", testo).encode("ascii", "ignore").decode()
    testo = re.sub(r"[^a-z0-9]+", "_", testo.lower()).strip("_")
    return (testo or "sessione")[:48]


def nuovo_id(bundle: SessionBundle) -> str:
    quando = bundle.meta.importato_il or datetime.now(timezone.utc)
    return (f"{quando.strftime('%Y%m%d-%H%M%S')}-{_pezzo_leggibile(bundle)}"
            f"-{uuid.uuid4().hex[:4]}")


def _percorso(id_sessione: str) -> Path:
    if not ID_VALIDO.match(id_sessione or ""):
        raise ArchivioError(f"id non valido: {id_sessione!r}")
    radice = cartella().resolve()
    percorso = (radice / f"{id_sessione}.json").resolve()
    # Cintura e bretelle: la regex già esclude i separatori, ma un id che esce dalla
    # cartella non deve poter arrivare al filesystem nemmeno per sbaglio.
    if percorso.parent != radice:
        raise ArchivioError(f"id non valido: {id_sessione!r}")
    return percorso


def salva(bundle: SessionBundle, id_sessione: str | None = None) -> str:
    """Scrive il bundle e restituisce il suo id. La scrittura è atomica."""
    id_sessione = id_sessione or nuovo_id(bundle)
    percorso = _percorso(id_sessione)
    temporaneo = percorso.with_suffix(".json.tmp")
    temporaneo.write_text(bundle.to_json(), encoding="utf-8")
    os.replace(temporaneo, percorso)   # o c'è il file vecchio, o quello nuovo: mai mezzo
    return id_sessione


def leggi(id_sessione: str) -> SessionBundle:
    percorso = _percorso(id_sessione)
    if not percorso.is_file():
        raise SessioneNonTrovata(f"sessione {id_sessione} non trovata")
    return SessionBundle.from_json(percorso.read_text(encoding="utf-8"))


def cancella(id_sessione: str) -> None:
    percorso = _percorso(id_sessione)
    if not percorso.is_file():
        raise SessioneNonTrovata(f"sessione {id_sessione} non trovata")
    percorso.unlink()


def _riassumi(id_sessione: str, bundle: SessionBundle) -> Riassunto:
    validi = bundle.giri_validi
    return Riassunto(
        id=id_sessione,
        fonte=bundle.meta.fonte.value,
        car=bundle.meta.car,
        car_model_id=bundle.meta.car_model_id,
        track=bundle.meta.track,
        tipo_sessione=bundle.meta.tipo_sessione.value,
        pilota=bundle.meta.pilota,
        giri=len(bundle.giri),
        giri_validi=len(validi),
        miglior_giro_ms=min((g.tempo_ms for g in validi if g.tempo_ms), default=None),
        ha_setup=bundle.setup is not None,
        parametri_setup=len(bundle.setup.valori) if bundle.setup else 0,
        assunzioni=len(bundle.assunzioni) + (len(bundle.setup.assunzioni) if bundle.setup else 0),
        importato_il=bundle.meta.importato_il.isoformat() if bundle.meta.importato_il else None,
        iniziata_il=bundle.meta.iniziata_il.isoformat() if bundle.meta.iniziata_il else None,
        mescola=bundle.meta.mescola.value if bundle.meta.mescola else None,
        piattaforma=bundle.meta.piattaforma.value if bundle.meta.piattaforma else None,
        ha_canali=bundle.canali is not None,
        ha_racconto=bool(bundle.racconto and not bundle.racconto.vuoto()),
        demo=bundle.meta.fonte.value == "demo",
        riferimento=bundle.meta.riferimento,
        ritaglio_i2=bundle.meta.ritaglio_i2,
    )


def riassunto(id_sessione: str) -> Riassunto:
    return _riassumi(id_sessione, leggi(id_sessione))


def elenca(limite: int | None = None) -> list[Riassunto]:
    """Le sessioni archiviate, dalla più recente. I file illeggibili si saltano."""
    file = sorted(cartella().glob("*.json"), key=lambda p: p.name, reverse=True)
    fuori: list[Riassunto] = []
    for percorso in file:
        if limite is not None and len(fuori) >= limite:
            break
        try:
            bundle = SessionBundle.from_json(percorso.read_text(encoding="utf-8"))
        except (ValueError, OSError, json.JSONDecodeError):
            # Un file rovinato non deve far sparire tutta la lista.
            continue
        fuori.append(_riassumi(percorso.stem, bundle))
    return fuori
