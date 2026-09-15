"""Il registratore: dalla shared memory ai canali su disco.

Decisioni di Edoardo del 15/09 che questo modulo mette in pratica:

* **tutti i parametri registrabili**, non una selezione (il dizionario dice quali e
  perché quei pochi restano fuori);
* **100 Hz** — ACC pubblica la fisica più in fretta, ma si è scelto di decimare per
  pesare meno sul disco; il dizionario dichiara la frequenza di ogni sessione;
* **automatico**, e con la performance come criterio: un thread che si sveglia 100
  volte al secondo per copiare ~800 byte di memoria mappata non è un lavoro, è una
  `memcpy`; niente processi separati, niente eseguibili da firmare.

Tre scelte di robustezza che vale la pena dichiarare:

1. **Si scrive a blocchi, non alla fine.** Ogni minuto il buffer va su disco in un
   blocco `.npz`. Se il gioco (o il PC) si pianta, si perde al massimo l'ultimo
   minuto, non la sessione; i blocchi rimasti si possono consolidare dopo.
2. **Due matrici, non una.** I canali interi (tempi in millisecondi, contatori) non
   passano per un float32: sopra i 16,7 milioni un float32 comincia ad arrotondare,
   e un tempo sul giro arrotondato è un dato falso. Interi e decimali vivono in due
   matrici separate, ricomposte per nome in lettura.
3. **Si registra solo in pista.** Stato LIVE: non il replay, non la pausa, non i
   menu. E se dall'altra parte non c'è ACC (la pagina statica lo dice), la sessione
   viene marcata come non attendibile invece di essere analizzata come se lo fosse.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from app.telemetria import dizionario
from app.telemetria.lettore import (
    LettoreSharedMemory,
    StatoAggancio,
    TelemetriaNonDisponibile,
)
from app.telemetria.strutture import ACC_SESSION_TYPE, VERSIONE_STRUTTURA

log = logging.getLogger("pitwall.telemetria")

FREQUENZA_PREDEFINITA = 100.0
SECONDI_PER_BLOCCO = 60.0
# Quanto si aspetta, fuori dallo stato LIVE, prima di considerare chiusa la sessione.
SECONDI_PRIMA_DI_CHIUDERE = 20.0


def abilitato() -> bool:
    """Interruttore `PITWALL_ALLOW_RECORDER`: acceso in locale, spento in vetrina."""
    return os.getenv("PITWALL_ALLOW_RECORDER", "1").strip().lower() in (
        "1", "true", "yes", "on",
    )


def cartella_telemetria() -> Path:
    """Dove finiscono i canali.

    Di default `<archivio sessioni>/telemetria`. **Vale la pena spostarla fuori da
    OneDrive** con `PITWALL_SESSIONS_DIR`: una sessione lunga sono centinaia di MB,
    e una cartella sincronizzata li manderebbe in rete uno per uno.
    """
    grezzo = os.getenv("PITWALL_SESSIONS_DIR", "").strip()
    radice = Path(grezzo) if grezzo else Path(__file__).resolve().parents[2] / "sessions"
    percorso = radice / "telemetria"
    percorso.mkdir(parents=True, exist_ok=True)
    return percorso


def _pezzo_leggibile(testo: str | None) -> str:
    testo = unicodedata.normalize("NFKD", testo or "").encode("ascii", "ignore").decode()
    testo = re.sub(r"[^a-z0-9]+", "_", testo.lower()).strip("_")
    return (testo or "sessione")[:48]


def nuovo_id(vettura: str | None, pista: str | None) -> str:
    """Stesso schema degli id dei bundle: data, nome leggibile, quattro esadecimali."""
    pezzi = "-".join(p for p in (_pezzo_leggibile(pista), _pezzo_leggibile(vettura)) if p)
    pezzi = _pezzo_leggibile(pezzi)
    quando = datetime.now(timezone.utc)
    return f"{quando.strftime('%Y%m%d-%H%M%S')}-{pezzi}-{uuid.uuid4().hex[:4]}"


@dataclass
class Sessione:
    """Una registrazione in corso."""

    id: str
    cartella: Path
    inizio: str
    vettura: str | None = None
    pista: str | None = None
    pilota: str | None = None
    tipo_sessione: str | None = None
    mescola_iniziale: str | None = None
    stato_pista_iniziale: str | None = None
    versione_sm: str | None = None
    versione_gioco: str | None = None
    attendibile: bool = True
    assunzioni: list[str] = field(default_factory=list)
    campioni: int = 0
    blocchi: int = 0
    duplicati_saltati: int = 0
    fine: str | None = None


class Registratore:
    """Legge la shared memory a frequenza fissa e scrive i canali a blocchi."""

    def __init__(
        self,
        frequenza_hz: float = FREQUENZA_PREDEFINITA,
        secondi_per_blocco: float = SECONDI_PER_BLOCCO,
        cartella: Path | None = None,
        nomi_mappa: dict[str, str] | None = None,
        secondi_prima_di_chiudere: float = SECONDI_PRIMA_DI_CHIUDERE,
    ) -> None:
        if frequenza_hz <= 0:
            raise ValueError("la frequenza dev'essere positiva")
        self.frequenza_hz = float(frequenza_hz)
        self.secondi_per_blocco = float(secondi_per_blocco)
        self.secondi_prima_di_chiudere = float(secondi_prima_di_chiudere)
        self._cartella = cartella
        self._lettore = LettoreSharedMemory(nomi_mappa)

        canali = dizionario.canali()
        self._colonne_f4 = [c.nome for c in canali if c.tipo == "f4"]
        self._colonne_i4 = [c.nome for c in canali if c.tipo == "i4"]
        self._estrattori = [(c.pagina, c.campo, c.componente, c.tipo) for c in canali]
        self._inizio_monotono: float | None = None

        self._buffer_f4: list[list[float]] = []
        self._buffer_i4: list[list[int]] = []
        self._sessione: Sessione | None = None
        self._ultimo_live = 0.0
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lucchetto = threading.Lock()

    # ── stato ──

    @property
    def sessione(self) -> Sessione | None:
        return self._sessione

    @property
    def in_registrazione(self) -> bool:
        return self._sessione is not None

    def stato(self) -> dict[str, Any]:
        """Lo stato da mostrare: niente di nascosto, nemmeno «non sto registrando»."""
        sessione = self._sessione
        return {
            "abilitato": abilitato(),
            "agganciato": self._lettore.agganciato,
            "in_registrazione": sessione is not None,
            "frequenza_hz": self.frequenza_hz,
            "colonne": len(self._estrattori),
            "sessione": (
                {
                    "id": sessione.id, "vettura": sessione.vettura,
                    "pista": sessione.pista, "campioni": sessione.campioni,
                    "blocchi": sessione.blocchi, "attendibile": sessione.attendibile,
                }
                if sessione
                else None
            ),
        }

    # ── ciclo di vita del thread ──

    def avvia(self) -> None:
        if not abilitato():
            log.info("registratore non abilitato (PITWALL_ALLOW_RECORDER)")
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._ciclo, name="pitwall-telemetria", daemon=True
        )
        self._thread.start()
        log.info("registratore avviato a %.0f Hz", self.frequenza_hz)

    def ferma(self) -> str | None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        with self._lucchetto:
            id_chiuso = self._chiudi_sessione()
        self._lettore.sgancia()
        return id_chiuso

    def _ciclo(self) -> None:
        intervallo = 1.0 / self.frequenza_hz
        prossimo = time.perf_counter()
        ultimo_tentativo = 0.0
        while not self._stop.is_set():
            if not self._lettore.agganciato:
                # Il gioco può partire dopo di noi: si ritenta, senza insistere.
                if time.perf_counter() - ultimo_tentativo > 2.0:
                    ultimo_tentativo = time.perf_counter()
                    stato = self._lettore.aggancia()
                    if not stato.agganciato:
                        self._stop.wait(2.0)
                        continue
                else:
                    self._stop.wait(0.5)
                    continue
            try:
                with self._lucchetto:
                    self.passo()
            except TelemetriaNonDisponibile as errore:
                log.warning("aggancio perso: %s", errore)
                with self._lucchetto:
                    self._chiudi_sessione()
                self._lettore.sgancia()
                continue
            prossimo += intervallo
            ritardo = prossimo - time.perf_counter()
            if ritardo > 0:
                self._stop.wait(ritardo)
            else:
                prossimo = time.perf_counter()  # eravamo in ritardo: si riparte da ora

    # ── un singolo passo (i test lo chiamano direttamente) ──

    def passo(self) -> bool:
        """Un campione. True se è stato registrato, False se non c'era niente da fare.

        È separato dal ciclo apposta: così la registrazione si può provare passo
        per passo, senza dipendere dal tempo che scorre.
        """
        adesso = time.monotonic()
        if not self._lettore.in_pista():
            if self._sessione and adesso - self._ultimo_live > self.secondi_prima_di_chiudere:
                self._chiudi_sessione()
            return False

        self._ultimo_live = adesso
        fisica = self._lettore.leggi_fisica()
        if fisica is None:
            if self._sessione:
                self._sessione.duplicati_saltati += 1
            return False
        grafica = self._lettore.leggi_grafica()

        if self._sessione is None:
            self._apri_sessione(grafica)

        if self._inizio_monotono is None:
            self._inizio_monotono = adesso
        sintetici = {"tempo_ms": int(round((adesso - self._inizio_monotono) * 1000))}

        riga_f4: list[float] = []
        riga_i4: list[int] = []
        pagine = {"physics": fisica, "graphics": grafica}
        for pagina, campo, componente, tipo in self._estrattori:
            if pagina == "pitwall":
                riga_i4.append(sintetici[campo]) if tipo == "i4" else riga_f4.append(
                    float(sintetici[campo]))
                continue
            valore = getattr(pagine[pagina], campo)
            if componente is not None:
                for pezzo in componente.split("."):
                    valore = valore[_indice(pezzo)]
            if tipo == "f4":
                riga_f4.append(float(valore))
            else:
                riga_i4.append(int(valore))
        self._buffer_f4.append(riga_f4)
        self._buffer_i4.append(riga_i4)

        sessione = self._sessione
        assert sessione is not None
        sessione.campioni += 1
        if len(self._buffer_f4) >= int(self.frequenza_hz * self.secondi_per_blocco):
            self._scrivi_blocco()
        return True

    # ── sessione ──

    def _apri_sessione(self, grafica: Any) -> None:
        # Qui siamo per forza agganciati: `passo()` ci arriva solo da `in_pista()`.
        stato: StatoAggancio = self._stato_corrente()
        id_sessione = nuovo_id(stato.vettura, stato.pista)
        cartella = (self._cartella or cartella_telemetria()) / id_sessione
        (cartella / "blocchi").mkdir(parents=True, exist_ok=True)

        try:
            tipo = ACC_SESSION_TYPE(grafica.session).name
        except ValueError:
            tipo = None

        sessione = Sessione(
            id=id_sessione,
            cartella=cartella,
            inizio=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            vettura=stato.vettura,
            pista=stato.pista,
            tipo_sessione=tipo,
            mescola_iniziale=(grafica.tyreCompound or None),
            stato_pista_iniziale=(grafica.trackStatus or None),
            versione_sm=stato.versione_sm,
            versione_gioco=stato.versione_gioco,
        )
        statica = self._lettore.leggi_statica()
        sessione.pilota = " ".join(
            p for p in (statica.playerName, statica.playerSurname) if p
        ) or None
        if not sessione.vettura:
            sessione.attendibile = False
            sessione.assunzioni.append(
                "la pagina statica non dichiara la vettura: sessione non attribuibile"
            )
        if tipo is None:
            sessione.assunzioni.append(
                f"tipo di sessione sconosciuto ({grafica.session})"
            )
        (cartella / "dizionario.json").write_text(
            json.dumps(dizionario.come_json(self.frequenza_hz),
                       ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._sessione = sessione
        self._inizio_monotono = None      # l'orologio dei canali parte con la sessione
        self._salva_metadati()
        log.info("registrazione avviata: %s (%s · %s)",
                 sessione.id, sessione.vettura, sessione.pista)

    def _stato_corrente(self) -> StatoAggancio:
        statica = self._lettore.leggi_statica()
        return StatoAggancio(
            agganciato=True,
            versione_sm=statica.smVersion or None,
            versione_gioco=statica.acVersion or None,
            vettura=statica.carModel or None,
            pista=statica.track or None,
        )

    def _chiudi_sessione(self) -> str | None:
        sessione = self._sessione
        if sessione is None:
            return None
        self._scrivi_blocco()
        sessione.fine = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._salva_metadati()
        consolida(sessione.cartella)
        applica_tetto(sessione.cartella.parent)
        log.info("registrazione chiusa: %s (%d campioni)",
                 sessione.id, sessione.campioni)
        self._sessione = None
        self._ultimo_live = 0.0
        return sessione.id

    def _scrivi_blocco(self) -> None:
        sessione = self._sessione
        if sessione is None or not self._buffer_f4:
            return
        sessione.blocchi += 1
        percorso = sessione.cartella / "blocchi" / f"blocco_{sessione.blocchi:04d}.npz"
        np.savez(
            percorso,
            f4=np.asarray(self._buffer_f4, dtype=np.float32),
            i4=np.asarray(self._buffer_i4, dtype=np.int32),
        )
        self._buffer_f4.clear()
        self._buffer_i4.clear()
        self._salva_metadati()

    def _salva_metadati(self) -> None:
        sessione = self._sessione
        if sessione is None:
            return
        dati = {
            "id": sessione.id,
            "inizio": sessione.inizio,
            "fine": sessione.fine,
            "vettura": sessione.vettura,
            "pista": sessione.pista,
            "pilota": sessione.pilota,
            "tipo_sessione": sessione.tipo_sessione,
            "mescola_iniziale": sessione.mescola_iniziale,
            "stato_pista_iniziale": sessione.stato_pista_iniziale,
            "versione_shared_memory": sessione.versione_sm,
            "versione_gioco": sessione.versione_gioco,
            "versione_struttura": VERSIONE_STRUTTURA,
            "frequenza_hz": self.frequenza_hz,
            "campioni": sessione.campioni,
            "blocchi": sessione.blocchi,
            "duplicati_saltati": sessione.duplicati_saltati,
            "attendibile": sessione.attendibile,
            "assunzioni": sessione.assunzioni,
            "colonne": {"f4": self._colonne_f4, "i4": self._colonne_i4},
        }
        percorso = sessione.cartella / "sessione.json"
        temporaneo = percorso.with_suffix(".json.tmp")
        temporaneo.write_text(
            json.dumps(dati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporaneo.replace(percorso)


def tetto_sessioni() -> int:
    """Quante sessioni conservano i canali grezzi. 0 = nessun tetto."""
    try:
        return max(0, int(os.getenv("PITWALL_TELEMETRIA_MAX_SESSIONI", "40")))
    except ValueError:
        return 40


def applica_tetto(radice: Path | None = None) -> list[str]:
    """Libera spazio senza cancellare la storia.

    Oltre il tetto, delle sessioni piu' vecchie si butta **solo** `canali.npz` —
    che e' tutto il peso — mentre metadati e dizionario restano, marcati
    `canali_rimossi`. Cosi' l'archivio non cresce all'infinito e nessuna sessione
    sparisce di nascosto: resta scritto che c'e' stata e cosa conteneva.
    """
    tetto = tetto_sessioni()
    if tetto <= 0:
        return []
    radice = radice or cartella_telemetria()
    # Ordine per data di scrittura dei canali, non per nome: il nome ha la
    # risoluzione del secondo, e due sessioni nello stesso secondo verrebbero
    # ordinate dai quattro esadecimali casuali — cioe' a caso.
    con_canali = sorted(
        (c for c in radice.iterdir() if c.is_dir() and (c / "canali.npz").exists()),
        key=lambda c: (c / "canali.npz").stat().st_mtime,
    )
    alleggerite = []
    for cartella in con_canali[: max(0, len(con_canali) - tetto)]:
        (cartella / "canali.npz").unlink()
        percorso = cartella / "sessione.json"
        if percorso.exists():
            dati = json.loads(percorso.read_text(encoding="utf-8"))
            dati["canali_rimossi"] = True
            dati["canali_rimossi_il"] = datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            )
            percorso.write_text(
                json.dumps(dati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        alleggerite.append(cartella.name)
        log.info("tetto archivio: rimossi i canali grezzi di %s", cartella.name)
    return alleggerite


def _indice(etichetta: str) -> int:
    if etichetta in dizionario.RUOTE:
        return dizionario.RUOTE.index(etichetta)
    if etichetta in dizionario.ASSI:
        return dizionario.ASSI.index(etichetta)
    if etichetta in dizionario.LATI_DANNO:
        return dizionario.LATI_DANNO.index(etichetta)
    return int(etichetta)


# ── consolidamento e lettura ────────────────────────────────────────────────


def consolida(cartella: Path) -> Path | None:
    """Unisce i blocchi in un solo `canali.npz` compresso e li cancella.

    Si può chiamare anche su una registrazione interrotta male: i blocchi rimasti
    sul disco sono già dati buoni, non vanno buttati.
    """
    blocchi = sorted((cartella / "blocchi").glob("blocco_*.npz"))
    if not blocchi:
        return None
    pezzi_f4, pezzi_i4 = [], []
    for percorso in blocchi:
        with np.load(percorso) as dati:
            pezzi_f4.append(dati["f4"])
            pezzi_i4.append(dati["i4"])
    uscita = cartella / "canali.npz"
    if uscita.exists():  # consolidamento ripetuto: si riparte da ciò che c'è già
        with np.load(uscita) as dati:
            pezzi_f4.insert(0, dati["f4"])
            pezzi_i4.insert(0, dati["i4"])
    np.savez_compressed(
        uscita,
        f4=np.concatenate(pezzi_f4),
        i4=np.concatenate(pezzi_i4),
    )
    for percorso in blocchi:
        percorso.unlink()
    try:
        (cartella / "blocchi").rmdir()
    except OSError:
        pass
    return uscita


def leggi_canali(cartella: Path) -> dict[str, np.ndarray]:
    """Rilegge i canali di una sessione, un dizionario nome -> serie."""
    meta = json.loads((cartella / "sessione.json").read_text(encoding="utf-8"))
    with np.load(cartella / "canali.npz") as dati:
        f4, i4 = dati["f4"], dati["i4"]
    fuori: dict[str, np.ndarray] = {}
    for indice, nome in enumerate(meta["colonne"]["f4"]):
        fuori[nome] = f4[:, indice]
    for indice, nome in enumerate(meta["colonne"]["i4"]):
        fuori[nome] = i4[:, indice]
    return fuori
