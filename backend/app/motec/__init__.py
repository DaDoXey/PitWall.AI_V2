"""File MoTeC esportati da ACC (L5 del rework dati).

`ld` legge il binario dei canali, `ldx` i passaggi sul traguardo e il nome del file.
`leggi_registrazione` mette insieme i due e fa le controprove fra l'uno e l'altro.
Come in `app/telemetria`, nessun modulo di questo pacchetto fa analisi: qui si legge
soltanto, e si dichiara quello che non torna.

Contesto (decisioni del 17/09): Edoardo gioca su PS5 e l'export MoTeC esiste solo su
ACC per PC, quindi questi file non sono mai suoi. Servono a validare il motore su
canali veri di ACC e come giri di riferimento.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.motec.ld import CanaleLd, FileLd, FileMotecNonValido, leggi_ld
from app.motec.ldx import (
    FileLdx,
    LdxNonValido,
    NomeFileAcc,
    TrattoLdx,
    leggi_ldx,
    leggi_nome_file,
    tempo_in_secondi,
)

# Scarto massimo fra la durata dei canali e la registrazione: un campione alla
# frequenza più bassa vista nei file di ACC (20 Hz) più un margine.
TOLLERANZA_DURATA_S = 0.1


@dataclass
class RegistrazioneMotec:
    ld: FileLd
    ldx: FileLdx | None
    nome_file: NomeFileAcc | None
    durata_s: float
    avvertenze: list[str] = field(default_factory=list)
    # Canali che durano più degli altri: succede nei file salvati da MoTeC i2 dopo aver
    # ritagliato un giro (verificato il 17/09 su 6 file: i canali principali coprono il
    # giro, `EN_*` e `TIME` l'intera sessione). Non sono allineati al taglio.
    canali_lunghi: list[str] = field(default_factory=list)

    @property
    def tratti(self) -> list[TrattoLdx]:
        return self.ldx.tratti(self.durata_s) if self.ldx else []

    @property
    def giri_completi(self) -> list[TrattoLdx]:
        return [t for t in self.tratti if not t.parziale]

    @property
    def ritagliata_in_i2(self) -> bool:
        """Salvata da MoTeC i2 dopo un ritaglio: niente beacon, e canali di durate diverse."""
        return bool(self.canali_lunghi) and not (self.ldx and self.ldx.beacon_s)


def registrazione_da_byte(ld: bytes, ldx: bytes | None, nome_file: str | None = None
                          ) -> RegistrazioneMotec:
    """Come `leggi_registrazione`, ma da byte già in memoria (upload)."""
    file_ld = leggi_ld(ld)
    avvertenze = list(file_ld.avvertenze)

    leggibili = [c for c in file_ld.canali if c.leggibile]
    durate = [c.durata_s for c in leggibili]
    durata = min(durate) if durate else 0.0
    lunghi = [c.nome for c in leggibili if c.durata_s - durata > TOLLERANZA_DURATA_S]
    if lunghi:
        avvertenze.append(
            f"i canali coprono durate diverse: da {durata:.2f} a {max(durate):.2f} s")

    file_ldx = None
    if ldx is not None:
        file_ldx = leggi_ldx(ldx)
        avvertenze.extend(file_ldx.avvertenze)
        fuori = [b for b in file_ldx.beacon_s if b > durata + TOLLERANZA_DURATA_S]
        if fuori:
            avvertenze.append(
                f"{len(fuori)} beacon oltre la fine dei canali ({durata:.2f} s): scartati")
            file_ldx.beacon_s = [b for b in file_ldx.beacon_s if b not in fuori]
        if not file_ldx.beacon_s:
            avvertenze.append("nessun passaggio sul traguardo: nessun giro completo")
    else:
        avvertenze.append("manca il .ldx: i giri non si conoscono")

    return RegistrazioneMotec(ld=file_ld, ldx=file_ldx,
                              nome_file=leggi_nome_file(nome_file) if nome_file else None,
                              durata_s=durata, avvertenze=avvertenze, canali_lunghi=lunghi)


def leggi_registrazione(percorso_ld: str | Path) -> RegistrazioneMotec:
    """Legge `x.ld` e, se c'è, `x.ldx` accanto. Senza `.ldx` i giri non si conoscono
    e lo si dichiara: non si ricostruiscono da canali che in ACC non li portano."""
    percorso_ld = Path(percorso_ld)
    percorso_ldx = percorso_ld.with_suffix(".ldx")
    ldx = percorso_ldx.read_bytes() if percorso_ldx.exists() else None
    registrazione = registrazione_da_byte(percorso_ld.read_bytes(), ldx, percorso_ld.name)
    registrazione.ld.percorso = percorso_ld
    return registrazione


__all__ = [
    "CanaleLd", "FileLd", "FileLdx", "FileMotecNonValido", "LdxNonValido", "NomeFileAcc",
    "RegistrazioneMotec", "TrattoLdx", "leggi_ld", "leggi_ldx", "leggi_nome_file",
    "leggi_registrazione", "registrazione_da_byte", "tempo_in_secondi",
]
