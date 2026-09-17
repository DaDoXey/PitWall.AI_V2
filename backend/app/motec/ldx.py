"""Lettura dei file `.ldx` (i giri) e del nome dei file MoTeC di ACC (L5 · Fase 1).

Il `.ldx` è un piccolo XML accanto al `.ld`. Dentro ci sono i **beacon**: gli istanti
in cui la vettura ha tagliato il traguardo, in **microsecondi** dall'inizio della
registrazione. Verificato sui 16 file veri del 17/09: in tutti, la distanza fra due
beacon consecutivi coincide al millesimo con il «Fastest Time» dichiarato nello
stesso file (Monza: 110,006 s − 0,024 s = 1:49.982).

**I giri si prendono da qui, non dal `.ld`.** Nei file di ACC il canale `LAP_BEACON`
è sempre zero, e il canale `TIME` non è un cronometro del giro: in alcuni file si
azzera a metà registrazione, in altri non si azzera mai (Misano arriva a 477 s).

Il tratto prima del primo beacon e quello dopo l'ultimo sono pezzi di giro (uscita e
rientro): il file li conta in «Total Laps», noi li teniamo come `parziale`.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

MICROSECONDI = 1_000_000
DIMENSIONE_MASSIMA = 1_000_000  # un .ldx vero pesa meno di 3 KB


class LdxNonValido(ValueError):
    """Il `.ldx` non si legge: si dice perché."""


@dataclass
class TrattoLdx:
    """Un tratto fra due passaggi sul traguardo (o fra un bordo e un passaggio)."""

    numero: int            # 0 = prima del primo beacon
    inizio_s: float
    fine_s: float
    parziale: bool         # True per uscita e rientro: non è un giro completo

    @property
    def durata_s(self) -> float:
        return self.fine_s - self.inizio_s


@dataclass
class FileLdx:
    beacon_s: list[float]
    giri_totali: int | None
    tempo_migliore: str | None
    giro_migliore: int | None
    avvertenze: list[str] = field(default_factory=list)
    # Il numero del primo beacon («2, id=99»): ACC usa il contatore dei giri della sessione.
    primo_beacon: int = 1

    def tratti(self, durata_registrazione_s: float) -> list[TrattoLdx]:
        """I tratti della registrazione. I giri completi sono quelli con `parziale=False`."""
        bordi = [0.0, *self.beacon_s, durata_registrazione_s]
        out = []
        for i, (a, b) in enumerate(zip(bordi, bordi[1:])):
            parziale = i == 0 or i == len(bordi) - 2
            out.append(TrattoLdx(numero=i, inizio_s=a, fine_s=b, parziale=parziale))
        return out

    @property
    def tempi_giro_s(self) -> list[float]:
        return [b - a for a, b in zip(self.beacon_s, self.beacon_s[1:])]


def tempo_in_secondi(testo: str) -> float | None:
    """«1:49.982» → 109.982; «48.711» → 48.711; altro → None."""
    m = re.fullmatch(r"\s*(?:(\d+):)?(\d+(?:\.\d+)?)\s*", testo or "")
    if not m:
        return None
    return int(m.group(1) or 0) * 60 + float(m.group(2))


def leggi_ldx(sorgente: str | Path | bytes) -> FileLdx:
    if isinstance(sorgente, (bytes, bytearray)):
        contenuto = bytes(sorgente)
    else:
        contenuto = Path(sorgente).read_bytes()
    if len(contenuto) > DIMENSIONE_MASSIMA:
        raise LdxNonValido(f".ldx di {len(contenuto)} byte: non plausibile")
    if b"<!DOCTYPE" in contenuto or b"<!ENTITY" in contenuto:
        raise LdxNonValido(".ldx con DTD o entità: rifiutato")
    try:
        radice = ET.fromstring(contenuto)
    except ET.ParseError as e:
        raise LdxNonValido(f"XML non valido: {e}") from e
    if radice.tag != "LDXFile":
        raise LdxNonValido(f"radice {radice.tag!r}, attesa 'LDXFile'")

    avvertenze: list[str] = []
    beacon: list[float] = []
    numeri: list[int] = []
    for m in radice.iter("Marker"):
        if m.get("ClassName") != "BCN":
            continue
        testa = (m.get("Name") or "").split(",")[0].strip()
        if testa.isdigit():
            numeri.append(int(testa))
        try:
            beacon.append(float(m.get("Time", "")) / MICROSECONDI)
        except ValueError:
            avvertenze.append(f"beacon con tempo non numerico: {m.get('Time')!r}")
    if beacon != sorted(beacon):
        avvertenze.append("beacon non in ordine di tempo: riordinati")
        beacon.sort()

    dettagli = {s.get("Id"): s.get("Value") for s in radice.iter("String")}

    def intero(chiave: str) -> int | None:
        try:
            return int(dettagli[chiave])
        except (KeyError, TypeError, ValueError):
            return None

    ldx = FileLdx(beacon_s=beacon, giri_totali=intero("Total Laps"),
                  tempo_migliore=dettagli.get("Fastest Time"),
                  giro_migliore=intero("Fastest Lap"), avvertenze=avvertenze,
                  primo_beacon=numeri[0] if numeri else 1)

    # Controprova: il giro più veloce misurato sui beacon deve essere quello dichiarato.
    dichiarato = tempo_in_secondi(ldx.tempo_migliore or "")
    if ldx.tempi_giro_s and dichiarato is not None:
        misurato = min(ldx.tempi_giro_s)
        if abs(misurato - dichiarato) > 0.0015:
            avvertenze.append(
                f"giro più veloce sui beacon {misurato:.3f} s, dichiarato "
                f"{ldx.tempo_migliore} ({dichiarato:.3f} s)")
    if ldx.giri_totali is not None and ldx.giri_totali != len(beacon) + 1:
        avvertenze.append(
            f"«Total Laps» {ldx.giri_totali}, ma {len(beacon)} beacon fanno "
            f"{len(beacon) + 1} tratti")
    return ldx


@dataclass
class NomeFileAcc:
    """Quello che ACC scrive nel nome: `<pista>-<vettura>-<n>-<aaaa.mm.gg-hh.mm.ss>.ld`.

    La vettura nel nome è lo **slug** (`bmw_m4_gt3`), mentre l'intestazione del `.ld`
    porta il nome esteso («M4 GT3»): per il catalogo serve il nome del file.
    Il numero centrale non è documentato e non si usa.
    """

    pista: str
    vettura: str
    numero: int
    data_ora: datetime


_NOME = re.compile(
    r"^(?P<pista>.+?)-(?P<vettura>[a-z0-9_]+)-(?P<numero>\d+)-"
    r"(?P<data>\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2})$")


def leggi_nome_file(nome: str) -> NomeFileAcc | None:
    m = _NOME.match(Path(nome).stem)
    if not m:
        return None
    try:
        quando = datetime.strptime(m.group("data"), "%Y.%m.%d-%H.%M.%S")
    except ValueError:
        return None
    return NomeFileAcc(pista=m.group("pista"), vettura=m.group("vettura"),
                       numero=int(m.group("numero")), data_ora=quando)
