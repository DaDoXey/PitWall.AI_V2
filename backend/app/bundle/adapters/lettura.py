"""bundle/adapters/lettura.py — aprire i file di ACC senza farsi ingannare dai byte.

ACC scrive i suoi JSON in due codifiche diverse a seconda del file, e **non mette
il BOM**: i setup sono UTF-8, i risultati sono **UTF-16 little-endian senza BOM**
(il file comincia con `{\\x00`). Chi li apre come UTF-8 legge spazzatura e di solito
se ne accorge tardi, quindi il riconoscimento sta qui, in un posto solo, e guarda i
byte invece di fidarsi di un marcatore che non c'è.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileAccIllegibile(ValueError):
    """Il file non è un JSON di ACC leggibile (codifica o sintassi)."""


def decodifica(dati: bytes) -> str:
    """Restituisce il testo di un JSON di ACC, qualunque codifica abbia usato."""
    if dati[:2] in (b"\xff\xfe", b"\xfe\xff"):        # UTF-16 con BOM
        return dati.decode("utf-16")
    if dati[:3] == b"\xef\xbb\xbf":                    # UTF-8 con BOM
        return dati.decode("utf-8-sig")
    # Niente BOM: se i byte dispari sono nulli è UTF-16 LE travestito da UTF-8.
    testa = dati[:64]
    if testa and testa.count(b"\x00") >= len(testa) // 4:
        ordine = "utf-16-le" if dati[1:2] == b"\x00" else "utf-16-be"
        try:
            return dati.decode(ordine)
        except UnicodeDecodeError as e:
            raise FileAccIllegibile(f"sembra UTF-16 ma non si decodifica: {e}") from e
    try:
        return dati.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise FileAccIllegibile(f"codifica non riconosciuta: {e}") from e


def carica_json(sorgente: str | Path | bytes) -> tuple[dict[str, Any], str | None]:
    """Apre un file di ACC (percorso o byte) e ne restituisce (dati, nome file)."""
    nome: str | None = None
    if isinstance(sorgente, (str, Path)) and not isinstance(sorgente, bytes):
        percorso = Path(sorgente)
        nome = percorso.name
        try:
            dati = percorso.read_bytes()
        except OSError as e:
            raise FileAccIllegibile(f"file non leggibile: {e}") from e
    else:
        dati = bytes(sorgente)

    if not dati.strip():
        raise FileAccIllegibile("file vuoto")

    testo = decodifica(dati)
    try:
        letto = json.loads(testo)
    except json.JSONDecodeError as e:
        raise FileAccIllegibile(f"JSON non valido: {e}") from e
    if not isinstance(letto, dict):
        raise FileAccIllegibile("il file non contiene un oggetto JSON")
    return letto, nome
