"""Banco di prova per la telemetria: mappe di memoria finte, con dentro pagine ACC.

Non è un test: è l'attrezzatura che i test usano. Sta in un modulo suo perché la
usano sia `test_telemetria.py` sia `test_registratore.py`, e importare un file di
test per riusarne una funzione lo farebbe **eseguire**.

I nomi delle mappe sono `pitwall_test_*`: le mappe vere del gioco non si toccano
mai, nemmeno quando ACC non sta girando.
"""

from __future__ import annotations

import ctypes
import pathlib
import sys

BACKEND = pathlib.Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.telemetria import strutture as s  # noqa: E402

NOMI_DI_PROVA = {
    "physics": "Local\\pitwall_test_physics",
    "graphics": "Local\\pitwall_test_graphics",
    "static": "Local\\pitwall_test_static",
}

_PAGE_READWRITE = 0x04
_FILE_MAP_WRITE = 0x0002
_INVALID_HANDLE = ctypes.c_void_p(-1)


class MappaFinta:
    """Crea una mappa con nome e ci scrive dentro dei byte: fa il posto del gioco."""

    def __init__(self, nome: str, contenuto: bytes) -> None:
        self.nome = nome
        self.dimensione = len(contenuto)
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateFileMappingW.restype = ctypes.c_void_p
        k32.MapViewOfFile.restype = ctypes.c_void_p
        self._k32 = k32
        self._handle = k32.CreateFileMappingW(
            _INVALID_HANDLE, None, _PAGE_READWRITE, 0, self.dimensione, nome
        )
        if not self._handle:
            raise OSError(f"CreateFileMappingW fallita: {ctypes.get_last_error()}")
        self._indirizzo = k32.MapViewOfFile(
            ctypes.c_void_p(self._handle), _FILE_MAP_WRITE, 0, 0, self.dimensione
        )
        if not self._indirizzo:
            raise OSError(f"MapViewOfFile fallita: {ctypes.get_last_error()}")
        self.scrivi(contenuto)

    def scrivi(self, contenuto: bytes) -> None:
        ctypes.memmove(self._indirizzo, contenuto, len(contenuto))

    def chiudi(self) -> None:
        self._k32.UnmapViewOfFile(ctypes.c_void_p(self._indirizzo))
        self._k32.CloseHandle(ctypes.c_void_p(self._handle))


def byte_di(struttura: ctypes.Structure) -> bytes:
    return bytes(memoryview(struttura).cast("B"))


def fisica_di_prova(packet_id: int = 7) -> s.SPageFilePhysics:
    p = s.SPageFilePhysics()
    p.packetId = packet_id
    p.gas = 0.5
    p.brake = 0.25
    p.fuel = 63.5
    p.gear = 4
    p.rpm = 7250
    p.speedKmh = 123.4
    p.steerAngle = -0.75
    for i, v in enumerate((27.5, 27.6, 27.1, 27.2)):
        p.wheelPressure[i] = v
    for i, v in enumerate((82.0, 83.5, 79.0, 80.5)):
        p.tyreCoreTemp[i] = v
    for i, v in enumerate((420.0, 425.0, 380.0, 385.0)):
        p.brakeTemp[i] = v
    p.brakeBias = 0.54
    p.waterTemp = 90.0
    return p


def grafica_di_prova(stato: int = 2, posizione: float = 0.375) -> s.SPageFileGraphics:
    g = s.SPageFileGraphics()
    g.packetId = 3
    g.status = stato
    g.session = 0
    g.currentTime = "1:48.123"
    g.iCurrentTime = 108123
    g.completedLaps = 5
    g.normalizedCarPosition = posizione
    g.tyreCompound = "dry_compound"
    g.isValidLap = 1
    return g


def statica_di_prova() -> s.SPageFileStatic:
    st = s.SPageFileStatic()
    st.smVersion = "1.8.12"
    st.acVersion = "1.10.2"
    st.carModel = "bmw_m4_gt3"
    st.track = "monza"
    st.playerName = "Edoardo"
    st.sectorCount = 3
    st.maxRpm = 7000
    st.maxFuel = 120.0
    st.dryTyresName = "DHE2020"
    st.wetTyresName = "WHE2020"
    return st
