"""app/budget.py — tetto di spesa del ramo LLM (MUST #2 della PRR, Entry #028).

Ogni chiamata reale al modello passa di qui due volte:
    1. `prenota()` PRIMA della chiamata mette in conto il costo MASSIMO possibile:
       token di input stimati per eccesso (un token non e' mai piu' corto di un
       byte) e tutti i `max_tokens` di output. Se il tetto non lo regge solleva
       `BudgetEsaurito` e la chiamata non parte. Il tetto quindi non si supera
       mai, nemmeno con piu' richieste in contemporanea.
    2. `salda()` DOPO la chiamata sostituisce la prenotazione con il costo vero,
       letto da `message.usage`.

Categorie, una per modo di utilizzo:
    analisi     Console, POST /api/analysis (cascata haiku -> sonnet, fino a 4 chiamate)
    screenshot  Setup, POST /api/setup/from-image (una chiamata vision)
    chat        chat di Gigi (nessuna rotta la chiama ancora: tetto 0 di default)

Periodi: un tetto GIORNALIERO per categoria (giorno locale del server, si azzera a
mezzanotte) e un tetto MENSILE complessivo. Importi in dollari, la valuta in cui
Anthropic fattura. Valori nel .env, default in `DEFAULT_GIORNO` / `DEFAULT_MESE`.

Scelte prudenti, tutte per eccesso e mai per difetto:
    - una chiamata che fallisce resta conteggiata al massimo prenotato;
    - un modello che non sta nel listino si conta al listino piu' caro;
    - uno stato illeggibile blocca le chiamate invece di ripartire da zero;
    - un valore non valido nel .env vale 0, cioe' niente spesa.

Stato in backend/logs/llm_spesa.json (gitignorata), scritto in modo atomico.
Un solo processo uvicorn: il lucchetto e' un threading.Lock. Con piu' worker
servirebbe un lock su file.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app import config

log = logging.getLogger("pitwall.budget")

CATEGORIE = ("analisi", "screenshot", "chat")

# Dollari per milione di token (input, output). Verificati l'11/09/2026 sulla
# documentazione Anthropic: da aggiornare se cambia il listino.
PREZZI = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-4-6": (3.00, 15.00),
}
# Modello fuori listino (es. LLM_MODEL cambiato nel .env): listino piu' caro in circolazione.
PREZZO_FUORI_LISTINO = (10.00, 50.00)
# Moltiplicatori sul prezzo di input: scrittura in cache (5 minuti) e lettura.
CACHE_SCRITTURA, CACHE_LETTURA = 1.25, 0.10

# Token di un'immagine nel caso peggiore. Sonnet 4.6 riduce il lato lungo a 1568 px,
# che al limite vale ~1568 token; i modelli ad alta risoluzione arrivano a ~4784.
TOKEN_IMMAGINE = {"claude-sonnet-4-6": 1600, "claude-haiku-4-5": 1600}
TOKEN_IMMAGINE_FUORI_LISTINO = 5000
# Impaginazione del messaggio (ruoli, separatori) e istruzioni fisse brevi.
MARGINE_TOKEN = 200

DEFAULT_GIORNO = {"analisi": "0.50", "screenshot": "0.25", "chat": "0"}
DEFAULT_MESE = "5.00"

STATO_PATH: Path = config.LOG_DIR / "llm_spesa.json"

_lock = threading.Lock()


class SpesaRifiutata(RuntimeError):
    """La chiamata al modello non puo' partire."""


class BudgetEsaurito(SpesaRifiutata):
    """Il tetto giornaliero della categoria o quello mensile non regge la chiamata."""


class StatoSpesaIllegibile(SpesaRifiutata):
    """llm_spesa.json esiste ma non si legge: senza sapere quanto si e' speso non si spende."""


@dataclass(frozen=True)
class Prenotazione:
    categoria: str
    modello: str
    importo: float
    giorno: str
    mese: str


# ─────────────────────────────────────────────
# Tetti e costi
# ─────────────────────────────────────────────

def _importo_env(nome: str, default: str) -> float:
    grezzo = os.getenv(nome, default)
    try:
        valore = float(grezzo.strip().replace(",", "."))
    except (AttributeError, ValueError):
        valore = -1.0
    if valore < 0:
        log.error("%s=%r non e' un importo valido: vale 0, nessuna spesa consentita", nome, grezzo)
        return 0.0
    return valore


def tetto_giornaliero(categoria: str) -> float:
    return _importo_env(f"PITWALL_BUDGET_{categoria.upper()}_GIORNO", DEFAULT_GIORNO[categoria])


def tetto_mensile() -> float:
    return _importo_env("PITWALL_BUDGET_MESE", DEFAULT_MESE)


def _listino(modello: str) -> tuple[float, float]:
    return PREZZI.get(modello, PREZZO_FUORI_LISTINO)


def costo_massimo(modello: str, testo_input: str, max_output: int, immagini: int = 0) -> float:
    """Il costo piu' alto che la chiamata puo' avere, in dollari."""
    token_immagine = TOKEN_IMMAGINE.get(modello, TOKEN_IMMAGINE_FUORI_LISTINO)
    token_in = len(testo_input.encode("utf-8")) + immagini * token_immagine + MARGINE_TOKEN
    p_in, p_out = _listino(modello)
    return (token_in * p_in + max_output * p_out) / 1_000_000


def costo_reale(modello: str, usage) -> float:
    """Il costo di una risposta dal suo `usage`, in dollari."""
    p_in, p_out = _listino(modello)
    token_in = getattr(usage, "input_tokens", 0) or 0
    token_out = getattr(usage, "output_tokens", 0) or 0
    scritti = getattr(usage, "cache_creation_input_tokens", 0) or 0
    letti = getattr(usage, "cache_read_input_tokens", 0) or 0
    return (token_in * p_in + scritti * p_in * CACHE_SCRITTURA + letti * p_in * CACHE_LETTURA
            + token_out * p_out) / 1_000_000


# ─────────────────────────────────────────────
# Stato su disco
# ─────────────────────────────────────────────

def _oggi() -> tuple[str, str]:
    adesso = datetime.now()
    return adesso.strftime("%Y-%m-%d"), adesso.strftime("%Y-%m")


def _stato_vuoto(giorno: str, mese: str) -> dict:
    return {"giorno": giorno, "mese": mese,
            "spesa_giorno": {c: 0.0 for c in CATEGORIE},
            "chiamate_giorno": {c: 0 for c in CATEGORIE},
            "spesa_mese": 0.0}


def _carica() -> dict:
    """Lo stato del periodo corrente: azzera il giorno o il mese se sono cambiati."""
    giorno, mese = _oggi()
    if not STATO_PATH.exists():
        return _stato_vuoto(giorno, mese)
    try:
        stato = json.loads(STATO_PATH.read_text(encoding="utf-8"))
        for c in CATEGORIE:
            float(stato["spesa_giorno"][c])
            int(stato["chiamate_giorno"][c])
        float(stato["spesa_mese"])
        str(stato["giorno"]), str(stato["mese"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise StatoSpesaIllegibile(f"{STATO_PATH} illeggibile ({exc}): controllalo o cancellalo") from exc
    if stato["mese"] != mese:
        return _stato_vuoto(giorno, mese)
    if stato["giorno"] != giorno:
        nuovo = _stato_vuoto(giorno, mese)
        nuovo["spesa_mese"] = stato["spesa_mese"]
        return nuovo
    return stato


def _salva(stato: dict) -> None:
    STATO_PATH.parent.mkdir(parents=True, exist_ok=True)
    provvisorio = STATO_PATH.with_suffix(".tmp")
    provvisorio.write_text(json.dumps(stato, indent=2), encoding="utf-8")
    os.replace(provvisorio, STATO_PATH)


def _arrotonda(valore: float) -> float:
    return round(max(valore, 0.0), 6)


# ─────────────────────────────────────────────
# Interfaccia
# ─────────────────────────────────────────────

def disponibile(categoria: str) -> bool:
    """True se la categoria ha ancora margine oggi e nel mese. Controllo preventivo
    per scrivere nel log il motivo giusto: la garanzia vera sta in `prenota()`."""
    try:
        with _lock:
            stato = _carica()
    except StatoSpesaIllegibile:
        log.exception("stato della spesa illeggibile")
        return False
    return (stato["spesa_giorno"][categoria] < tetto_giornaliero(categoria)
            and stato["spesa_mese"] < tetto_mensile())


def prenota(categoria: str, modello: str, testo_input: str, max_output: int,
            immagini: int = 0) -> Prenotazione:
    """Mette in conto il costo massimo della chiamata, o solleva `SpesaRifiutata`."""
    if categoria not in CATEGORIE:
        raise ValueError(f"categoria di spesa sconosciuta: {categoria!r}")
    if modello not in PREZZI:
        log.warning("%s: modello %r fuori listino, conteggiato al listino piu' caro", categoria, modello)
    massimo = costo_massimo(modello, testo_input, max_output, immagini)
    tetto_g, tetto_m = tetto_giornaliero(categoria), tetto_mensile()
    with _lock:
        stato = _carica()
        speso_g, speso_m = stato["spesa_giorno"][categoria], stato["spesa_mese"]
        if speso_g + massimo > tetto_g or speso_m + massimo > tetto_m:
            log.warning("%s: chiamata a %s RIFIUTATA, servirebbero fino a $%.4f; oggi $%.4f su $%g, "
                        "mese $%.4f su $%g", categoria, modello, massimo, speso_g, tetto_g,
                        speso_m, tetto_m)
            raise BudgetEsaurito(f"tetto di spesa raggiunto per {categoria}")
        stato["spesa_giorno"][categoria] = _arrotonda(speso_g + massimo)
        stato["chiamate_giorno"][categoria] += 1
        stato["spesa_mese"] = _arrotonda(speso_m + massimo)
        _salva(stato)
    return Prenotazione(categoria, modello, massimo, stato["giorno"], stato["mese"])


def salda(prenotazione: Prenotazione, usage) -> None:
    """Sostituisce la prenotazione con il costo vero. Non solleva mai: la risposta
    del modello e' gia' arrivata, e un guasto qui non deve buttarla via."""
    p = prenotazione
    try:
        if usage is None:
            log.warning("%s: risposta di %s senza usage, resta il costo massimo $%.4f",
                        p.categoria, p.modello, p.importo)
            return
        reale = costo_reale(p.modello, usage)
        with _lock:
            stato = _carica()
            # Stesso periodo: si restituisce la differenza. Periodo cambiato nel mezzo
            # (mezzanotte): la prenotazione e' sparita con l'azzeramento, si aggiunge il reale.
            delta_g = reale - p.importo if stato["giorno"] == p.giorno else reale
            delta_m = reale - p.importo if stato["mese"] == p.mese else reale
            stato["spesa_giorno"][p.categoria] = _arrotonda(stato["spesa_giorno"][p.categoria] + delta_g)
            stato["spesa_mese"] = _arrotonda(stato["spesa_mese"] + delta_m)
            _salva(stato)
        log.info("%s: %s, %d token in, %d out, $%.4f (prenotati $%.4f); oggi $%.4f su $%g, "
                 "mese $%.4f su $%g", p.categoria, p.modello,
                 getattr(usage, "input_tokens", 0) or 0, getattr(usage, "output_tokens", 0) or 0,
                 reale, p.importo, stato["spesa_giorno"][p.categoria],
                 tetto_giornaliero(p.categoria), stato["spesa_mese"], tetto_mensile())
        if reale > p.importo:
            log.warning("%s: costo reale $%.4f oltre la prenotazione $%.4f, la stima per eccesso "
                        "non ha retto", p.categoria, reale, p.importo)
    except Exception:  # noqa: BLE001
        log.exception("%s: saldo della spesa non registrato, resta il costo massimo", p.categoria)
