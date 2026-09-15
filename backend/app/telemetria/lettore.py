"""Aggancio e lettura delle pagine di shared memory di ACC.

Tre scelte che vale la pena spiegare, perche' sono quelle che fanno la differenza
fra un lettore che funziona e uno che mente:

1. **Si apre, non si crea.** `mmap` di Python, su Windows, *crea* la mappa se non
   esiste: agganciarsi cosi' a un gioco spento restituisce una pagina di zeri che
   sembra telemetria valida. Qui si chiama direttamente `OpenFileMappingW`, che
   esiste solo per aprire: se ACC non gira, l'aggancio fallisce e lo diciamo.
2. **La dimensione NON si puo' misurare, quindi si guarda chi scrive.** Windows
   arrotonda ogni sezione alla pagina da 4 KB: mappare 800 byte su una sezione da
   712 riesce lo stesso, e la coda legge zeri senza un solo errore. Tutte e tre le
   nostre pagine stanno in una pagina di memoria, quindi *nessun* controllo sulla
   dimensione puo' accorgersi di essere attaccato al gioco sbagliato (e' esattamente
   il caso del banco di prova su AC1). L'unica difesa vera e' l'identita' che il
   gioco dichiara nella pagina statica — `smVersion`, `acVersion`, `carModel` — che
   qui viene letta all'aggancio e riportata a chi decide se fidarsi.
3. **Niente campioni inventati.** La pagina fisica ha un `packetId` che il gioco
   incrementa a ogni passo: se non e' cambiato, il campione e' lo stesso di prima e
   `leggi_fisica()` restituisce `None`. Registrare due volte lo stesso istante
   falserebbe qualunque media.

Tutto in user-space: `OpenFileMappingW`/`MapViewOfFile` sono le stesse chiamate che
usano SimHub, Race Element e CrewChief. Nessun driver, nessun eseguibile da firmare.
"""

from __future__ import annotations

import ctypes
import logging
import sys
from dataclasses import dataclass, field
from typing import Any

from app.telemetria.strutture import (
    ACC_STATUS,
    CAMPI_NON_USATI,
    DIMENSIONI_ATTESE,
    PAGINE,
    VERSIONE_STRUTTURA,
)

log = logging.getLogger("pitwall.telemetria")

SU_WINDOWS = sys.platform == "win32"

# Costanti Win32 (winnt.h / memoryapi.h)
_FILE_MAP_READ = 0x0004
_ERRORE_FILE_NON_TROVATO = 2


class TelemetriaNonDisponibile(RuntimeError):
    """Il gioco non sta girando, o questo non e' Windows."""


@dataclass
class StatoAggancio:
    """Che cosa e' riuscito e che cosa no: si mostra al pilota, non si nasconde."""

    agganciato: bool
    pagine: dict[str, int] = field(default_factory=dict)      # nome -> byte mappati
    campi_non_letti: dict[str, list[str]] = field(default_factory=dict)
    versione_struttura: str = VERSIONE_STRUTTURA
    motivo: str | None = None
    # Identita' dichiarata dal gioco (pagina statica): e' l'unico modo di sapere
    # a che cosa ci siamo attaccati, visto che la dimensione non dice niente.
    versione_sm: str | None = None
    versione_gioco: str | None = None
    vettura: str | None = None
    pista: str | None = None


class PaginaMappata:
    """Una delle tre pagine, aperta in sola lettura."""

    def __init__(self, nome: str, nome_mappa: str | None = None) -> None:
        if nome not in PAGINE:
            raise KeyError(f"pagina sconosciuta: {nome}")
        self.nome = nome
        nome_vero, self.struttura = PAGINE[nome]
        # I test (e un domani il banco di prova) puntano a mappe con un altro nome:
        # cosi' non si toccano mai quelle vere del gioco.
        self.nome_mappa = nome_mappa or nome_vero
        self.dimensione_attesa = DIMENSIONI_ATTESE[nome]
        self.byte_mappati = 0
        self._handle: int | None = None
        self._indirizzo: int | None = None

    # ── apertura ──

    def apri(self) -> None:
        if not SU_WINDOWS:
            raise TelemetriaNonDisponibile(
                "la shared memory di ACC esiste solo su Windows"
            )

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenFileMappingW.restype = ctypes.c_void_p
        k32.MapViewOfFile.restype = ctypes.c_void_p

        handle = k32.OpenFileMappingW(_FILE_MAP_READ, False, self.nome_mappa)
        if not handle:
            errore = ctypes.get_last_error()
            if errore == _ERRORE_FILE_NON_TROVATO:
                raise TelemetriaNonDisponibile(
                    f"{self.nome_mappa} non esiste: il gioco non sta girando"
                )
            raise TelemetriaNonDisponibile(
                f"{self.nome_mappa} non si apre (errore Windows {errore})"
            )

        # Si chiede la dimensione intera. Windows la concede quasi sempre, anche
        # quando la sezione e' piu' corta, perche' e' arrotondata alla pagina: non
        # e' una verifica, e' solo il caso in cui davvero non ci sta (sezioni oltre
        # i 4 KB). Se non ci sta, si mappa quel che c'e' e lo si dichiara.
        byte_mappati = self.dimensione_attesa
        indirizzo = k32.MapViewOfFile(
            ctypes.c_void_p(handle), _FILE_MAP_READ, 0, 0, byte_mappati
        )
        if not indirizzo:
            errore = ctypes.get_last_error()
            k32.CloseHandle(ctypes.c_void_p(handle))
            raise TelemetriaNonDisponibile(
                f"{self.nome_mappa} esiste ma non espone i {self.dimensione_attesa} "
                f"byte attesi (errore Windows {errore})"
            )

        self._handle = handle
        self._indirizzo = indirizzo
        self.byte_mappati = byte_mappati

        if byte_mappati < self.dimensione_attesa:
            log.warning(
                "pagina %s: mappati %d byte sui %d attesi, %d campi non leggibili",
                self.nome, byte_mappati, self.dimensione_attesa,
                len(self.campi_non_letti()),
            )

    # ── lettura ──

    def leggi(self) -> ctypes.Structure:
        """Copia i byte mappati in una struttura. La copia serve: il gioco scrive
        mentre noi leggiamo, e un campione deve essere coerente con se stesso."""
        if self._indirizzo is None:
            raise TelemetriaNonDisponibile(f"pagina {self.nome} non agganciata")
        pagina = self.struttura()
        ctypes.memmove(ctypes.byref(pagina), self._indirizzo, self.byte_mappati)
        return pagina

    def campi_non_letti(self) -> list[str]:
        """I campi che stanno oltre i byte mappati: valgono zero, e va detto."""
        if self.byte_mappati >= self.dimensione_attesa:
            return []
        fuori = []
        for nome_campo, _tipo in self.struttura._fields_:
            descrittore = getattr(self.struttura, nome_campo)
            if descrittore.offset + descrittore.size > self.byte_mappati:
                fuori.append(nome_campo)
        return fuori

    def chiudi(self) -> None:
        if not SU_WINDOWS:
            return
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        if self._indirizzo:
            k32.UnmapViewOfFile(ctypes.c_void_p(self._indirizzo))
        if self._handle:
            k32.CloseHandle(ctypes.c_void_p(self._handle))
        self._indirizzo = None
        self._handle = None
        self.byte_mappati = 0


class LettoreSharedMemory:
    """Le tre pagine insieme, con la deduplica dei campioni."""

    def __init__(self, nomi_mappa: dict[str, str] | None = None) -> None:
        self._pagine: dict[str, PaginaMappata] = {}
        self._ultimo_packet_id: int | None = None
        self._nomi_mappa = nomi_mappa or {}

    # ── ciclo di vita ──

    def aggancia(self) -> StatoAggancio:
        try:
            for nome in PAGINE:
                pagina = PaginaMappata(nome, self._nomi_mappa.get(nome))
                pagina.apri()
                self._pagine[nome] = pagina
        except TelemetriaNonDisponibile as errore:
            self.sgancia()
            return StatoAggancio(agganciato=False, motivo=str(errore))

        # Chi c'e' dall'altra parte? Lo dice solo la pagina statica. Serve a chi
        # registra per decidere se quei numeri sono di ACC o di un altro gioco.
        statica = self.leggi_statica()
        return StatoAggancio(
            agganciato=True,
            pagine={n: p.byte_mappati for n, p in self._pagine.items()},
            campi_non_letti={
                n: p.campi_non_letti()
                for n, p in self._pagine.items()
                if p.campi_non_letti()
            },
            versione_sm=statica.smVersion or None,
            versione_gioco=statica.acVersion or None,
            vettura=statica.carModel or None,
            pista=statica.track or None,
        )

    def sgancia(self) -> None:
        for pagina in self._pagine.values():
            pagina.chiudi()
        self._pagine.clear()
        self._ultimo_packet_id = None

    @property
    def agganciato(self) -> bool:
        return bool(self._pagine)

    # ── lettura ──

    def leggi_fisica(self, salta_duplicati: bool = True) -> ctypes.Structure | None:
        """Il campione fisico corrente, o None se il gioco non ne ha prodotto uno
        nuovo dall'ultima lettura."""
        pagina = self._pagine.get("physics")
        if pagina is None:
            raise TelemetriaNonDisponibile("fisica non agganciata")
        campione = pagina.leggi()
        if salta_duplicati and campione.packetId == self._ultimo_packet_id:
            return None
        self._ultimo_packet_id = campione.packetId
        return campione

    def leggi_grafica(self) -> ctypes.Structure:
        pagina = self._pagine.get("graphics")
        if pagina is None:
            raise TelemetriaNonDisponibile("grafica non agganciata")
        return pagina.leggi()

    def leggi_statica(self) -> ctypes.Structure:
        pagina = self._pagine.get("static")
        if pagina is None:
            raise TelemetriaNonDisponibile("statica non agganciata")
        return pagina.leggi()

    # ── stato del gioco ──

    def stato_gioco(self) -> ACC_STATUS:
        """OFF / REPLAY / LIVE / PAUSE. E' cio' che decide quando registrare."""
        grezzo = self.leggi_grafica().status
        try:
            return ACC_STATUS(grezzo)
        except ValueError:
            log.warning("stato di gioco sconosciuto: %r", grezzo)
            return ACC_STATUS.OFF

    def in_pista(self) -> bool:
        """Si registra solo qui: LIVE, e non nel replay."""
        return self.agganciato and self.stato_gioco() is ACC_STATUS.LIVE

    # ── conversione in dizionari ──

    def __enter__(self) -> "LettoreSharedMemory":
        stato = self.aggancia()
        if not stato.agganciato:
            raise TelemetriaNonDisponibile(stato.motivo or "aggancio fallito")
        return self

    def __exit__(self, *_esc: object) -> None:
        self.sgancia()


def pagina_a_dizionario(
    pagina: ctypes.Structure, nome_pagina: str, includi_non_usati: bool = False
) -> dict[str, Any]:
    """Struttura C -> dizionario Python, array compresi.

    I campi che il documento ufficiale marca «non usati da ACC» restano fuori per
    default: tenerli vorrebbe dire far finta che zero sia una misura.
    """
    non_usati = CAMPI_NON_USATI.get(nome_pagina, frozenset())
    fuori: dict[str, Any] = {}
    for nome_campo, _tipo in pagina._fields_:
        if not includi_non_usati and nome_campo in non_usati:
            continue
        valore = getattr(pagina, nome_campo)
        fuori[nome_campo] = _valore_python(valore)
    return fuori


def _valore_python(valore: Any) -> Any:
    """Gli array ctypes non sono liste: qui diventano liste (anche annidate)."""
    if isinstance(valore, (int, float, str, bytes, bool)) or valore is None:
        return valore
    if hasattr(valore, "__len__"):
        return [_valore_python(v) for v in valore]
    return valore
