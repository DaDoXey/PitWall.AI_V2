"""Un `.ld` e un `.ldx` costruiti a tavolino, con la struttura dei file veri di ACC.

I file veri (`kyxap/acc-all-in-one`, CC BY-NC-SA) non stanno nel repo. Qui si scrive
un file con la stessa impaginazione verificata il 17/09 — intestazione di 1762 byte,
evento → pista → vettura, metadati dei canali da 124 byte in lista collegata, dati in
coda — così i test sanno la risposta in anticipo e girano offline.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

import numpy as np

from app.motec.ld import DIMENSIONE_CANALE, DIMENSIONE_INTESTAZIONE


@dataclass
class CanaleFinto:
    nome: str
    unita: str
    frequenza: int
    valori: np.ndarray
    tipo: tuple[int, int] = (7, 4)
    offset: int = 0
    moltiplicatore: int = 1
    scala: int = 1
    decimali: int = 0


_NUMPY = {(7, 4): "<f4", (7, 2): "<f2", (3, 2): "<i2", (3, 4): "<i4", (8, 8): "<f8"}


def scrivi_ld(canali: list[CanaleFinto], vettura="M4 GT3", pista="monza",
              data="28/11/2023", ora="09:57:06", canali_dichiarati=None,
              peso=1257) -> bytes:
    p_evento = DIMENSIONE_INTESTAZIONE
    p_pista = p_evento + struct.calcsize("<64s64s1024sH")
    p_vettura = p_pista + struct.calcsize("<64s1034xH")
    p_meta = p_vettura + struct.calcsize("<64s128xI32s32s")
    p_dati = p_meta + len(canali) * DIMENSIONE_CANALE

    testa = bytearray(DIMENSIONE_INTESTAZIONE)
    struct.pack_into("<IIII", testa, 0, 0x40, 0, p_meta, p_dati)
    struct.pack_into("<I", testa, 36, p_evento)
    struct.pack_into("<HHH", testa, 64, 2, 0x4240, 0xF)
    dichiarati = len(canali) if canali_dichiarati is None else canali_dichiarati
    struct.pack_into("<I8sHHHH", testa, 70, 8004, b"ADL", 420, 0xADB0, dichiarati, dichiarati)
    struct.pack_into("<16s", testa, 94, data.encode())
    struct.pack_into("<16s", testa, 126, ora.encode())
    struct.pack_into("<64s", testa, 222, vettura.encode())
    struct.pack_into("<64s", testa, 350, pista.encode())

    corpo = bytearray()
    corpo += struct.pack("<64s64s1024sH", pista.encode(), b"", b"", p_pista)
    corpo += struct.pack("<64s1034xH", pista.encode(), p_vettura)
    corpo += struct.pack("<64s128xI32s32s", vettura.encode(), peso, b"", b"")

    meta, dati, cursore = bytearray(), bytearray(), p_dati
    for i, c in enumerate(canali):
        grezzi = np.asarray(c.valori).astype(_NUMPY[c.tipo]).tobytes()
        prec = p_meta + (i - 1) * DIMENSIONE_CANALE if i else 0
        succ = p_meta + (i + 1) * DIMENSIONE_CANALE if i < len(canali) - 1 else 0
        meta += struct.pack("<IIIIHHHHhhhh32s8s12s40x", prec, succ, cursore, len(c.valori),
                            0x2EE1 + i, c.tipo[0], c.tipo[1], c.frequenza, c.offset,
                            c.moltiplicatore, c.scala, c.decimali, c.nome.encode(),
                            c.nome[:8].encode(), c.unita.encode())
        dati += grezzi
        cursore += len(grezzi)
    return bytes(testa + corpo + meta + dati)


def scrivi_ldx(beacon_s: list[float], giri_totali: int | None = None,
               tempo_migliore: str | None = None, giro_migliore: int = 1) -> bytes:
    marker = "\n".join(
        f'     <Marker Version="100" ClassName="BCN" Name="{i + 1}, id=99" Flags="13" '
        f'Time="{t * 1_000_000:.17e}"/>' for i, t in enumerate(beacon_s))
    if giri_totali is None:
        giri_totali = len(beacon_s) + 1
    if tempo_migliore is None and len(beacon_s) > 1:
        migliore = min(b - a for a, b in zip(beacon_s, beacon_s[1:]))
        tempo_migliore = f"{int(migliore // 60)}:{migliore % 60:06.3f}"
    return f"""<?xml version="1.0"?>
<LDXFile Locale="English_United States.1252" DefaultLocale="C" Version="1.6">
 <Layers>
  <Layer>
   <MarkerBlock>
    <MarkerGroup Name="Beacons" Index="0">
{marker}
    </MarkerGroup>
   </MarkerBlock>
   <RangeBlock/>
  </Layer>
  <Details>
   <String Id="Total Laps" Value="{giri_totali}"/>
   <String Id="Fastest Time" Value="{tempo_migliore or ''}"/>
   <String Id="Fastest Lap" Value="{giro_migliore}"/>
  </Details>
 </Layers>
</LDXFile>
""".encode()
