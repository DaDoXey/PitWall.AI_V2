"""bundle/schema.py — il «session bundle»: formato canonico di una sessione.

Fonte di verità del formato: `docs/04-rework-dati.md`. Questo modulo è **solo il
contenitore**: valida e trasporta, non calcola nulla. I numeri derivati (delta,
costanza, degrado, consumo) sono compito del motore di analisi (L2), che legge un
bundle e produce un report; gli adattatori (L1) leggono i file di ACC e producono
un bundle. In mezzo non passa altro.

**Regola del dato grezzo:** ciò che ACC scrive si conserva sempre così com'è
(`Setup.raw`, `ValoreSetup.raw`). La conversione in unità reali è un *di più*
dichiarato (`unita`, `verificato`): se la tabella di conversione di quella vettura
non è verificata, il valore resta in click e lo si dice, invece di mostrare un
numero inventato. È la decisione 7 del 14/09 (via d'uscita da INC-V2-003).

Struttura verificata su file **reali** il 14/09/2026 (vedi `tests/fixtures/`):
un setup ACC (`bmw_m4_gt3/monza`) e un file di risultati scritto dal gioco.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Versione del formato. Il numero principale si alza quando un bundle già scritto
# smette di essere leggibile così com'è; il secondo quando si aggiungono campi
# opzionali (un bundle 1.0 si legge ancora). I bundle salvati portano la versione con
# cui sono nati. 1.1 (16/09/2026): mescola, piattaforma, racconto del pilota.
SCHEMA_VERSION = "1.1"


class BundleVersionError(ValueError):
    """Bundle scritto da una versione del formato che questo codice non sa leggere."""


class Fonte(str, Enum):
    """Da dove arriva il bundle. Serve a sapere di quali campi ci si può fidare."""

    ACC_RESULTS = "acc_results"        # file di fine sessione scritto dal gioco
    ACC_SETUP = "acc_setup"            # file di setup salvato in garage
    ACC_SHARED_MEMORY = "acc_shm"      # registratore live (L3)
    MOTEC = "motec"                    # export .ld/.ldx (L5)
    DEMO = "demo"                      # sessione dimostrativa di PitWall
    MANUALE = "manuale"                # inserito a mano dal pilota


class Piattaforma(str, Enum):
    """Dove gioca il pilota. Decide da dove possono arrivare i dati: su PC i file e la
    shared memory di ACC, su console solo il setup e il racconto del pilota."""

    PC = "pc"
    PLAYSTATION = "playstation"
    XBOX = "xbox"


class Mescola(str, Enum):
    ASCIUTTO = "asciutto"
    BAGNATO = "bagnato"


class TipoSessione(str, Enum):
    PROVE = "FP"
    QUALIFICA = "Q"
    GARA = "R"
    HOTLAP = "HL"
    HOTSTINT = "HS"
    SCONOSCIUTO = "?"


class _Base(BaseModel):
    """Niente campi a sorpresa: un campo non previsto è un errore, non un silenzio."""

    model_config = ConfigDict(extra="forbid")


class Condizioni(_Base):
    """Condizioni della sessione. Tutto opzionale: ACC non le scrive sempre."""

    temp_aria_c: float | None = Field(default=None, ge=-20, le=60)
    temp_pista_c: float | None = Field(default=None, ge=-20, le=90)
    grip_linea_ideale: float | None = Field(default=None, ge=0, le=1)
    grip_fuori_linea: float | None = Field(default=None, ge=0, le=1)
    pioggia: float | None = Field(default=None, ge=0, le=1)
    pista_bagnata: bool | None = None


class Meta(_Base):
    """Chi, cosa, dove, quando. `car`/`track` sono slug del catalogo (`bmw_m4_gt3`)."""

    fonte: Fonte
    importato_il: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    file_origine: str | None = None

    car: str | None = None
    car_model_id: int | None = Field(default=None, ge=0)  # id numerico di ACC
    track: str | None = None
    pilota: str | None = None

    tipo_sessione: TipoSessione = TipoSessione.SCONOSCIUTO
    iniziata_il: datetime | None = None
    durata_s: float | None = Field(default=None, ge=0)
    condizioni: Condizioni = Field(default_factory=Condizioni)
    # Mescola montata: decide contro quale finestra si giudicano le gomme (la finestra
    # Kunos vale solo sull'asciutto). None = non nota, e allora non si giudica.
    mescola: Mescola | None = None
    piattaforma: Piattaforma | None = None

    @field_validator("car", "track")
    @classmethod
    def _slug_non_vuoto(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        return v or None


class Giro(_Base):
    """Un giro. I tempi sono in **millisecondi**, come li scrive ACC."""

    numero: int = Field(ge=1)
    tempo_ms: int | None = Field(default=None, gt=0)
    splits_ms: list[int] = Field(default_factory=list, max_length=3)
    valido: bool = True
    # Carburante: ACC scrive il **residuo** a fine giro; il consumo è la differenza
    # fra due giri consecutivi e lo calcola chi importa, non il modello.
    carburante_residuo_l: float | None = Field(default=None, ge=0)
    carburante_usato_l: float | None = Field(default=None, ge=0)
    in_pit: bool = False
    out_pit: bool = False
    set_gomme: int | None = Field(default=None, ge=0)
    timestamp_ms: float | None = Field(default=None, ge=0)
    # `flags` dei risultati di ACC: campo di bit non documentato (visti 0, 1, 4, 8,
    # 9, 1024). Si conserva perche' e' dato vero, ma NON si usa per decidere se un
    # giro e' valido: interpretarlo a naso vorrebbe dire scartare giri buoni.
    flags_acc: int | None = Field(default=None, ge=0)

    @field_validator("splits_ms")
    @classmethod
    def _splits_positivi(cls, v: list[int]) -> list[int]:
        if any(s <= 0 for s in v):
            raise ValueError("gli split devono essere millisecondi positivi")
        return v


class ValoreSetup(_Base):
    """Un parametro di setup.

    `raw` è ciò che c'è nel file di ACC e non si perde mai: di solito un indice di
    *click*, in qualche caso un valore fisico già calcolato dal gioco (il camber è
    in gradi). `reale`/`unita` compaiono solo quando la lettura è **verificata**.
    """

    raw: int | float | list[int] | list[float]
    reale: float | None = None
    unita: str = "click"
    verificato: bool = False

    @model_validator(mode="after")
    def _reale_solo_se_verificato(self) -> "ValoreSetup":
        if self.reale is not None and not self.verificato:
            raise ValueError(
                "un valore in unità reali va marcato verificato=True: "
                "senza tabella di conversione controllata si resta in click"
            )
        if self.verificato and self.unita == "click":
            raise ValueError("verificato=True richiede un'unità reale, non 'click'")
        return self


class Setup(_Base):
    """Il setup della sessione: valori normalizzati + il JSON originale intatto."""

    car: str | None = None
    nome: str | None = None
    valori: dict[str, ValoreSetup] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)
    # Interpretazioni che l'adattatore ha dovuto fare e che vanno dette, non nascoste
    # (es. l'ordine dell'array rideHeight di ACC, che il file non dichiara).
    assunzioni: list[str] = Field(default_factory=list)

    def quanti_verificati(self) -> tuple[int, int]:
        """(parametri in unità reali, totale) — per dirlo in chiaro nella UI."""
        return sum(1 for v in self.valori.values() if v.verificato), len(self.valori)


class TipoEvento(str, Enum):
    PIT = "pit"
    BANDIERA = "bandiera"
    PENALITA = "penalita"
    FUORIPISTA = "fuoripista"
    CONTATTO = "contatto"


class Evento(_Base):
    tipo: TipoEvento
    giro: int | None = Field(default=None, ge=1)
    timestamp_ms: float | None = Field(default=None, ge=0)
    nota: str | None = None


class Racconto(_Base):
    """Il pilota che racconta la sessione, con parole sue.

    È il dato principale di chi gioca su console, dove non esistono né i file né la
    shared memory di ACC: il motore di analisi non lo interpreta (non inventa numeri
    da un testo), lo passa a Gigi insieme al report. Ogni campo è una fase di guida,
    così il racconto arriva ordinato invece che come un paragrafo unico.
    """

    andamento: str | None = Field(default=None, max_length=2000)   # la sessione, dall'inizio alla fine
    frenata: str | None = Field(default=None, max_length=1000)
    ingresso: str | None = Field(default=None, max_length=1000)
    centro: str | None = Field(default=None, max_length=1000)
    uscita: str | None = Field(default=None, max_length=1000)
    gomme: str | None = Field(default=None, max_length=1000)
    curve_critiche: list[str] = Field(default_factory=list, max_length=12)
    note: str | None = Field(default=None, max_length=1000)

    def vuoto(self) -> bool:
        return not any([self.andamento, self.frenata, self.ingresso, self.centro,
                        self.uscita, self.gomme, self.curve_critiche, self.note])


class Canali(_Base):
    """Riferimento alle serie temporali (L3). Il bundle non le porta dentro di sé:
    i canali stanno in un file colonnare a parte, qui c'è solo come leggerlo."""

    frequenza_hz: float = Field(gt=0, le=1000)
    nomi: list[str] = Field(min_length=1)
    file: str                      # percorso relativo allo store
    indicizzati_su_distanza: bool = False
    campioni: int | None = Field(default=None, ge=0)


class SessionBundle(_Base):
    """Una sessione, nel formato che tutto il resto dell'app consuma."""

    schema_version: str = SCHEMA_VERSION
    meta: Meta
    giri: list[Giro] = Field(default_factory=list)
    setup: Setup | None = None
    eventi: list[Evento] = Field(default_factory=list)
    canali: Canali | None = None
    racconto: Racconto | None = None
    # Ciò che l'import ha dovuto interpretare, o che il file non permette di sapere.
    # Va mostrato al pilota: un dato mancante dichiarato vale più di uno inventato.
    assunzioni: list[str] = Field(default_factory=list)

    @field_validator("giri")
    @classmethod
    def _giri_numerati_una_volta_sola(cls, v: list[Giro]) -> list[Giro]:
        numeri = [g.numero for g in v]
        if len(numeri) != len(set(numeri)):
            raise ValueError("due giri con lo stesso numero")
        return v

    # ── comodità di lettura (nessun calcolo di analisi: solo conteggi onesti) ──

    @property
    def giri_validi(self) -> list[Giro]:
        return [g for g in self.giri if g.valido and g.tempo_ms]

    def ha_dati_utili(self) -> bool:
        """Un bundle senza giri, senza setup e senza racconto non dice niente a nessuno."""
        return (bool(self.giri) or bool(self.setup and self.setup.valori)
                or bool(self.racconto and not self.racconto.vuoto()))

    def to_json(self, indent: int | None = 2) -> str:
        return self.model_dump_json(indent=indent, exclude_none=False)

    @classmethod
    def from_json(cls, testo: str | bytes) -> "SessionBundle":
        """Rilegge un bundle salvato, rifiutando le versioni che non sa leggere."""
        import json

        dati = json.loads(testo)
        versione = str(dati.get("schema_version", ""))
        if versione.split(".")[0] != SCHEMA_VERSION.split(".")[0]:
            raise BundleVersionError(
                f"bundle in formato {versione or '(assente)'}, "
                f"questo codice legge la {SCHEMA_VERSION}"
            )
        return cls.model_validate(dati)
