"""Lettura dei file `.ld` di MoTeC scritti da ACC (L5 · Fase 1).

Kunos non documenta il formato. La struttura qui sotto viene da due letture
indipendenti del binario — `gotzl/ldparser` (Python, scritto proprio per i file di
ACC) e `afonso360/motec-i2` (Rust) — usate **solo come documentazione**: il codice
è nostro. Poi è stata verificata byte per byte sui 16 file veri scaricati il 17/09
(`kyxap/acc-all-in-one`, ACC 1.9.x): in tutti, l'ultimo byte di dati dell'ultimo
canale coincide con la fine del file, e la lista dei canali si chiude su se stessa
senza un puntatore fuori posto. È il controllo che conta: un offset sbagliato non
dà errore, dà numeri plausibili e falsi.

Quattro scelte che vale la pena spiegare:

1. **I canali si contano percorrendo la lista collegata** dei metadati, con un tetto e
   un controllo sui cicli. L'intestazione li dichiara a 86 e 88 (due u16: 55 e 55 nei
   file veri; letti in F1 per errore come un u32 da 3 604 535, corretto in F5) e se non
   tornano con la lista lo si dichiara.
2. **Ogni puntatore si controlla prima di seguirlo.** Un file troncato o corrotto
   produce un errore dichiarato (`FileMotecNonValido`), mai una lettura oltre la fine.
3. **Un canale di tipo sconosciuto non ferma il file.** Resta nell'elenco con il
   motivo per cui non si legge; gli altri si leggono.
4. **I dati si leggono solo quando servono**, e si leggono una volta.

**Unità e coda dei metadati (verificato in F5 su 880 canali):** ACC scrive l'unità nel
campo da 8 byte che i parser chiamano «nome breve», e lascia vuoto quello da 12. Gli
ultimi 40 byte portano massimo e minimo dei dati arrotondati (due i32), due limiti di
scala in float32 (diversi da zero solo per ROTY, GEAR, STEERANGLE) e i decimali di
visualizzazione.

La conversione dei valori grezzi è quella di `ldparser`:
`(grezzo / scala · 10^-decimali + offset) · moltiplicatore`. Nei file di ACC tutti i
canali sono float32 con scala 1, decimali 0, offset 0, moltiplicatore 1, quindi la
formula è l'identità: **su parametri diversi non è verificata su file veri**, e il
canale lo dichiara (`conversione_verificata`).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np

MARCATORE_LD = 0x40

# Intestazione: 1762 byte (nei file di ACC l'evento parte esattamente lì).
_OFF_META = 8          # u32, primo blocco di metadati dei canali
_OFF_DATI = 12         # u32, inizio dei dati
_OFF_EVENTO = 36       # u32
_OFF_SERIALE = 70      # u32
_OFF_DISPOSITIVO = 74  # 8 byte
_OFF_VERSIONE = 82     # u16
_OFF_N_CANALI = 86     # u16, ripetuto a 88; a 90 e 92 frequenza massima e minima
_OFF_DATA = 94         # 16 byte, «gg/mm/aaaa»
_OFF_ORA = 126         # 16 byte, «hh:mm:ss»
_OFF_PILOTA = 158      # 64 byte
_OFF_VETTURA = 222     # 64 byte
_OFF_PISTA = 350       # 64 byte
_OFF_SESSIONE = 1508   # 64 byte
_OFF_COMMENTO = 1572   # 64 byte
DIMENSIONE_INTESTAZIONE = 1762

# Evento → pista → vettura: blocchi collegati da puntatori a 16 bit.
_EVENTO = struct.Struct("<64s64s1024sH")
_PISTA = struct.Struct("<64s1034xH")
_VETTURA = struct.Struct("<64s128xI32s32s")

# Metadati di un canale: 124 byte (84 descritti + 40 di coda, come nei file di ACC).
_CANALE = struct.Struct("<IIIIHHHHhhhh32s8s12siiffI20x")
DIMENSIONE_CANALE = _CANALE.size

# (famiglia, byte) → tipo numpy. Solo float32 è verificato su file veri di ACC.
_TIPI: dict[tuple[int, int], str] = {
    (0, 2): "<i2", (3, 2): "<i2", (5, 2): "<i2",
    (0, 4): "<i4", (3, 4): "<i4", (5, 4): "<i4",
    (7, 2): "<f2",
    (7, 4): "<f4",
    (8, 8): "<f8",
}
TIPI_VERIFICATI = frozenset({(7, 4)})

MAX_CANALI = 4096


class FileMotecNonValido(ValueError):
    """Il file non è un `.ld` leggibile: si dice perché, non si indovina."""


def _testo(grezzo: bytes) -> str:
    return grezzo.split(b"\0", 1)[0].decode("utf-8", errors="replace").strip()


@dataclass
class CanaleLd:
    """Un canale come lo dichiara il file. I valori si chiedono con `valori()`."""

    nome: str
    nome_breve: str
    unita: str
    frequenza_hz: int
    campioni: int
    tipo: tuple[int, int]
    offset: int
    moltiplicatore: int
    scala: int
    decimali: int
    _puntatore_dati: int = field(repr=False)
    _file: "FileLd" = field(repr=False)
    leggibile: bool = True
    motivo: str | None = None
    _cache: np.ndarray | None = field(default=None, repr=False)
    # Dalla coda dei metadati: come MoTeC i2 deve mostrare il canale (F5).
    massimo_arrotondato: int = 0
    minimo_arrotondato: int = 0
    limite_alto: float = 0.0
    limite_basso: float = 0.0
    decimali_display: int = 0

    @property
    def durata_s(self) -> float:
        return self.campioni / self.frequenza_hz if self.frequenza_hz else 0.0

    @property
    def tipo_verificato(self) -> bool:
        return self.tipo in TIPI_VERIFICATI

    @property
    def conversione_verificata(self) -> bool:
        return (self.scala, self.decimali, self.offset, self.moltiplicatore) == (1, 0, 0, 1)

    def valori(self) -> np.ndarray:
        """I valori convertiti, in float64. Alza se il canale non è leggibile."""
        if not self.leggibile:
            raise FileMotecNonValido(f"canale {self.nome!r} non leggibile: {self.motivo}")
        if self._cache is None:
            grezzi = np.frombuffer(self._file.contenuto, dtype=_TIPI[self.tipo],
                                   count=self.campioni, offset=self._puntatore_dati)
            v = grezzi.astype(np.float64)
            if not self.conversione_verificata:
                v = (v / self.scala * 10.0 ** (-self.decimali) + self.offset) * self.moltiplicatore
            self._cache = v
        return self._cache


@dataclass
class FileLd:
    """Un file `.ld` letto e controllato."""

    percorso: Path | None
    contenuto: bytes = field(repr=False)
    pilota: str
    vettura: str
    pista: str
    data_ora: datetime | None
    sessione: str
    commento: str
    dispositivo: str
    versione_dispositivo: int
    seriale: int
    evento: str
    peso_vettura: int | None
    canali: list[CanaleLd]
    avvertenze: list[str] = field(default_factory=list)
    canali_dichiarati: int | None = None

    def canale(self, nome: str) -> CanaleLd | None:
        return next((c for c in self.canali if c.nome == nome), None)

    @property
    def nomi(self) -> list[str]:
        return [c.nome for c in self.canali]


def _dentro(contenuto: bytes, inizio: int, lunghezza: int, cosa: str) -> None:
    if inizio < 0 or inizio + lunghezza > len(contenuto):
        raise FileMotecNonValido(
            f"{cosa}: puntatore {inizio} + {lunghezza} byte oltre la fine del file "
            f"({len(contenuto)} byte)")


def _data_ora(data: str, ora: str) -> datetime | None:
    for formato in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(f"{data} {ora}", formato)
        except ValueError:
            continue
    return None


def leggi_ld(sorgente: str | Path | bytes) -> FileLd:
    """Legge un `.ld` da percorso o da byte. Alza `FileMotecNonValido` se non torna."""
    if isinstance(sorgente, (bytes, bytearray)):
        percorso, contenuto = None, bytes(sorgente)
    else:
        percorso = Path(sorgente)
        contenuto = percorso.read_bytes()

    if len(contenuto) < DIMENSIONE_INTESTAZIONE:
        raise FileMotecNonValido(
            f"file di {len(contenuto)} byte: l'intestazione da sola ne occupa "
            f"{DIMENSIONE_INTESTAZIONE}")
    marcatore = struct.unpack_from("<I", contenuto, 0)[0]
    if marcatore != MARCATORE_LD:
        raise FileMotecNonValido(
            f"marcatore iniziale {marcatore:#x}, atteso {MARCATORE_LD:#x}: non è un .ld")

    avvertenze: list[str] = []
    u32 = lambda off: struct.unpack_from("<I", contenuto, off)[0]  # noqa: E731
    stringa = lambda off, n: _testo(contenuto[off:off + n])  # noqa: E731

    data, ora = stringa(_OFF_DATA, 16), stringa(_OFF_ORA, 16)
    data_ora = _data_ora(data, ora)
    if data_ora is None:
        avvertenze.append(f"data e ora non interpretabili: {data!r} {ora!r}")

    # Evento → pista → vettura (facoltativi: un puntatore a zero vuol dire «assente»).
    evento, peso = "", None
    p_evento = u32(_OFF_EVENTO)
    if p_evento:
        _dentro(contenuto, p_evento, _EVENTO.size, "evento")
        nome_ev, _, _, p_pista = _EVENTO.unpack_from(contenuto, p_evento)
        evento = _testo(nome_ev)
        if p_pista:
            _dentro(contenuto, p_pista, _PISTA.size, "pista")
            _, p_vettura = _PISTA.unpack_from(contenuto, p_pista)
            if p_vettura:
                _dentro(contenuto, p_vettura, _VETTURA.size, "vettura")
                _, peso, _, _ = _VETTURA.unpack_from(contenuto, p_vettura)

    file_ld = FileLd(
        percorso=percorso, contenuto=contenuto,
        pilota=stringa(_OFF_PILOTA, 64), vettura=stringa(_OFF_VETTURA, 64),
        pista=stringa(_OFF_PISTA, 64), data_ora=data_ora,
        sessione=stringa(_OFF_SESSIONE, 64), commento=stringa(_OFF_COMMENTO, 64),
        dispositivo=stringa(_OFF_DISPOSITIVO, 8),
        versione_dispositivo=struct.unpack_from("<H", contenuto, _OFF_VERSIONE)[0],
        seriale=u32(_OFF_SERIALE), evento=evento, peso_vettura=peso,
        canali=[], avvertenze=avvertenze,
    )

    # La lista collegata dei canali.
    visti: set[int] = set()
    puntatore, precedente = u32(_OFF_META), 0
    while puntatore:
        if puntatore in visti:
            raise FileMotecNonValido(f"la lista dei canali torna su se stessa a {puntatore}")
        if len(visti) >= MAX_CANALI:
            raise FileMotecNonValido(f"più di {MAX_CANALI} canali: lista non plausibile")
        visti.add(puntatore)
        _dentro(contenuto, puntatore, DIMENSIONE_CANALE, "metadati di un canale")
        (prec, succ, p_dati, n, _contatore, famiglia, byte, freq,
         offset, molt, scala, dec, nome, breve, unita,
         i_max, i_min, l_alto, l_basso, dec_display) = _CANALE.unpack_from(contenuto, puntatore)
        # ACC mette l'unità nel campo da 8 byte e lascia vuoto quello da 12.
        unita_12, breve_8 = _testo(unita), _testo(breve)
        if prec != precedente:
            avvertenze.append(
                f"canale a {puntatore}: puntatore al precedente {prec}, atteso {precedente}")
        canale = CanaleLd(
            nome=_testo(nome), nome_breve=breve_8 if unita_12 else "",
            unita=unita_12 or breve_8,
            frequenza_hz=freq, campioni=n, tipo=(famiglia, byte), offset=offset,
            moltiplicatore=molt, scala=scala, decimali=dec,
            _puntatore_dati=p_dati, _file=file_ld,
            massimo_arrotondato=i_max, minimo_arrotondato=i_min,
            limite_alto=l_alto, limite_basso=l_basso, decimali_display=dec_display,
        )
        if (famiglia, byte) not in _TIPI:
            canale.leggibile, canale.motivo = False, f"tipo di dato sconosciuto {(famiglia, byte)}"
        elif freq == 0:
            canale.leggibile, canale.motivo = False, "frequenza di campionamento zero"
        elif scala == 0:
            canale.leggibile, canale.motivo = False, "scala zero: conversione impossibile"
        else:
            _dentro(contenuto, p_dati, n * byte, f"dati del canale {canale.nome!r}")
        file_ld.canali.append(canale)
        precedente, puntatore = puntatore, succ

    if not file_ld.canali:
        raise FileMotecNonValido("nessun canale nel file")
    file_ld.canali_dichiarati = struct.unpack_from("<H", contenuto, _OFF_N_CANALI)[0]
    if file_ld.canali_dichiarati != len(file_ld.canali):
        file_ld.avvertenze.append(
            f"l'intestazione dichiara {file_ld.canali_dichiarati} canali, la lista ne contiene "
            f"{len(file_ld.canali)}: vale la lista")
    non_verificati = sorted({c.nome for c in file_ld.canali
                             if c.leggibile and not (c.tipo_verificato and c.conversione_verificata)})
    if non_verificati:
        file_ld.avvertenze.append(
            "tipo o conversione mai visti nei file veri di ACC per: " + ", ".join(non_verificati))
    return file_ld
