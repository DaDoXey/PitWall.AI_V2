"""Scrittura di file `.ld` e `.ldx` con l'impaginazione di ACC (L5 · Fase 5).

Serve a portare le sessioni di PitWall dentro MoTeC i2. MoTeC i2 non è installato su
questo PC, quindi la compatibilità non si prova aprendo i file: si prova **riscrivendo i
file veri di ACC e confrontandoli byte per byte con gli originali** (sezione H di
`scripts/valida_motec.py`). Se lo scrittore rifà identico un file che i2 apre, i file
che scrive con la stessa impaginazione sono della stessa forma.

L'impaginazione, verificata sui 16 export nativi del 17/09 (uguale in tutti):

    0       intestazione, 1762 byte
    1762    evento (nome = pista), 1154 byte; a +1156 un u16 costante 0x2C48
    4918    pista, 1100 byte
    8020    vettura (nome esteso, peso a +192), 260 byte
    13384   metadati dei canali, 124 byte l'uno, in lista collegata
    dopo    i dati, un canale dopo l'altro

Costanti dell'intestazione uguali in tutti i file (significato in parte ignoto, e per
questo copiate e non inventate): `2, 0x4240, 0xF` a 64; seriale 8004, «ADL», versione
420, `0xADB0` a 70-85; `0x000C81A4` a 1502; `0x63` a 1644. A 86-93 quattro u16: numero
di canali (due volte), frequenza massima e minima — sui file veri 55, 55, 200, 20.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from app.motec.ld import DIMENSIONE_CANALE, DIMENSIONE_INTESTAZIONE, MARCATORE_LD

P_EVENTO = 1762
P_PISTA = 4918
P_VETTURA = 8020
P_META = 13384
_COSTANTE_DOPO_EVENTO = 0x2C48   # u16 a evento + 1156, uguale in tutti i file di ACC


# Come ACC chiede a i2 di mostrare i suoi canali (costanti su 16 file, salvo lo sterzo che
# dipende dalla vettura): limite alto, limite basso, decimali.
DISPLAY_ACC: dict[str, tuple[float, float, int]] = {
    "G_LAT": (0.0, 0.0, 2),
    "ROTY": (100.0, -100.0, 2),
    "SPEED": (0.0, 0.0, 1),
    "GEAR": (6.0, 0.0, 0),
}


@dataclass
class CanaleDaScrivere:
    nome: str            # max 32 byte
    unita: str           # max 8 byte: ACC la scrive nel campo che i parser chiamano «nome breve»
    frequenza_hz: int
    valori: np.ndarray   # scritti come float32, come fa ACC
    limite_alto: float | None = None     # None → tabella DISPLAY_ACC, altrimenti 0
    limite_basso: float | None = None
    decimali: int | None = None


def _b(testo: str | None, n: int) -> bytes:
    grezzo = (testo or "").encode("utf-8")[:n]
    return grezzo


def scrivi_ld(canali: list[CanaleDaScrivere], vettura: str, pista: str,
              data_ora: datetime, pilota: str = "", peso_kg: int = 0) -> bytes:
    """Un `.ld` con l'impaginazione di ACC. Tutti i canali in float32, scala 1."""
    if not canali:
        raise ValueError("serve almeno un canale")
    if len(canali) > 0xFFFF:
        raise ValueError("troppi canali per l'intestazione (u16)")
    frequenze = [int(c.frequenza_hz) for c in canali]
    if any(f <= 0 or f > 0xFFFF for f in frequenze):
        raise ValueError("frequenze fuori scala (1-65535 Hz)")

    p_dati = P_META + len(canali) * DIMENSIONE_CANALE
    testa = bytearray(P_META)   # intestazione + blocchi, tutto zero dove ACC scrive zero

    struct.pack_into("<I", testa, 0, MARCATORE_LD)
    struct.pack_into("<II", testa, 8, P_META, p_dati)
    struct.pack_into("<I", testa, 36, P_EVENTO)
    struct.pack_into("<HHH", testa, 64, 2, 0x4240, 0xF)
    struct.pack_into("<I8sHH", testa, 70, 8004, b"ADL", 420, 0xADB0)
    struct.pack_into("<HHHH", testa, 86, len(canali), len(canali), max(frequenze), min(frequenze))
    struct.pack_into("<16s", testa, 94, _b(data_ora.strftime("%d/%m/%Y"), 16))
    struct.pack_into("<16s", testa, 126, _b(data_ora.strftime("%H:%M:%S"), 16))
    struct.pack_into("<64s", testa, 158, _b(pilota, 64))
    struct.pack_into("<64s", testa, 222, _b(vettura, 64))
    struct.pack_into("<64s", testa, 350, _b(pista, 64))
    struct.pack_into("<I", testa, 1502, 0x000C81A4)
    testa[1644] = 0x63

    struct.pack_into("<64s64s1024sH", testa, P_EVENTO, _b(pista, 64), b"", b"", P_PISTA)
    struct.pack_into("<H", testa, P_EVENTO + 1156, _COSTANTE_DOPO_EVENTO)
    struct.pack_into("<64s1034xH", testa, P_PISTA, _b(pista, 64), P_VETTURA)
    struct.pack_into("<64s128xI32s32s", testa, P_VETTURA, _b(vettura, 64), max(0, int(peso_kg)), b"", b"")
    assert len(testa) == P_META and DIMENSIONE_INTESTAZIONE == P_EVENTO

    meta = bytearray()
    dati = bytearray()
    cursore = p_dati
    for i, c in enumerate(canali):
        valori = np.asarray(c.valori, dtype="<f4")
        grezzi = valori.tobytes()
        alto, basso, decimali = DISPLAY_ACC.get(c.nome, (0.0, 0.0, 0))
        alto = alto if c.limite_alto is None else c.limite_alto
        basso = basso if c.limite_basso is None else c.limite_basso
        decimali = decimali if c.decimali is None else c.decimali
        # massimo e minimo arrotondati come Python `round` (880 canali veri su 880)
        massimo = round(float(valori.max())) if valori.size else 0
        minimo = round(float(valori.min())) if valori.size else 0
        precedente = P_META + (i - 1) * DIMENSIONE_CANALE if i else 0
        successivo = P_META + (i + 1) * DIMENSIONE_CANALE if i < len(canali) - 1 else 0
        meta += struct.pack(
            "<IIIIHHHHhhhh32s8s12siiffI20x",
            precedente, successivo, cursore, len(grezzi) // 4, 0x2EE1 + i,
            7, 4, int(c.frequenza_hz), 0, 1, 1, 0,
            _b(c.nome, 32), _b(c.unita, 8), b"",
            massimo, minimo, alto, basso, decimali,
        )
        dati += grezzi
        cursore += len(grezzi)
    return bytes(testa + meta + dati)


def scrivi_ldx(beacon_s: list[float], tempo_migliore_ms: int | None,
               giro_migliore: int | None, primo_beacon: int = 1) -> bytes:
    """Il `.ldx` come lo scrive ACC: beacon in microsecondi e tre dettagli.

    `primo_beacon`: ACC numera i beacon con il contatore dei giri della sessione (in un
    file di Hungaroring partono da 2), non da 1.
    """
    marker = "\n".join(
        f'     <Marker Version="100" ClassName="BCN" Name="{primo_beacon + i}, id=99" Flags="13" '
        f'Time="{float(round(t * 1_000_000)):.17e}"/>'  # microsecondi interi, come ACC
        for i, t in enumerate(beacon_s)
    )
    if tempo_migliore_ms:
        minuti, resto = divmod(int(tempo_migliore_ms), 60_000)
        migliore = f"{minuti}:{resto / 1000:06.3f}"
    else:
        migliore = ""
    return (
        '<?xml version="1.0"?>\n'
        '<LDXFile Locale="English_United States.1252" DefaultLocale="C" Version="1.6">\n'
        " <Layers>\n  <Layer>\n   <MarkerBlock>\n"
        '    <MarkerGroup Name="Beacons" Index="0">\n'
        f"{marker}\n"
        "    </MarkerGroup>\n   </MarkerBlock>\n   <RangeBlock/>\n  </Layer>\n"
        "  <Details>\n"
        f'   <String Id="Total Laps" Value="{len(beacon_s) + 1}"/>\n'
        f'   <String Id="Fastest Time" Value="{migliore}"/>\n'
        f'   <String Id="Fastest Lap" Value="{giro_migliore or ""}"/>\n'
        "  </Details>\n </Layers>\n</LDXFile>\n"
    ).encode("utf-8")
