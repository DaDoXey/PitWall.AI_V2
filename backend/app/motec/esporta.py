"""Da una sessione di PitWall a una coppia `.ld` + `.ldx` per MoTeC i2 (L5 · Fase 5).

Il verso opposto dell'import, deciso da Edoardo il 17/09: le registrazioni di PitWall
(shared memory, demo, import MoTeC) si aprono in MoTeC i2, **con dentro quello che
l'export di ACC non ha**: carburante, temperature al core, posizione in pista.

Scelte:

1. **I canali che ACC esporta tornano con il nome e l'unità di ACC** (SPEED in m/s,
   THROTTLE e BRAKE in %, SUS_TRAVEL in mm…): così il workspace di ACC per i2 li trova.
2. **I canali in più hanno un nome che non finge equivalenze**: `FUEL`, `TYRE_CORE_TEMP_LF`,
   `LAP_POSITION`, `STEER_INPUT` (normalizzato -1..1, non gradi), `GEAR_SM` (la marcia
   come la scrive la shared memory, senza riconvertirla a naso).
3. **Tutto a 100 Hz**, la frequenza a cui PitWall registra: niente ricampionamenti che
   inventano campioni.
4. **I passaggi sul traguardo vanno nel `.ldx`** come beacon in microsecondi, presi dai
   giri che il motore ha già ritagliato; `LAP_BEACON` resta a zero, come in ACC.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np

from app.analisi.curve import POSIZIONE, TEMPO, dividi_in_giri
from app.bundle.schema import SessionBundle
from app.motec.scrittura import CanaleDaScrivere, scrivi_ld, scrivi_ldx

FREQUENZA_HZ = 100

_RUOTE = {"FL": "LF", "FR": "RF", "RL": "LR", "RR": "RR"}

# canonico → (nome ACC, unità ACC, fattore)
_COME_ACC: dict[str, tuple[str, str, float]] = {
    "physics.speedKmh": ("SPEED", "m/s", 1 / 3.6),
    "physics.gas": ("THROTTLE", "%", 100.0),
    "physics.brake": ("BRAKE", "%", 100.0),
    "physics.rpms": ("RPMS", "1/min", 1.0),
}
for _c, _m in _RUOTE.items():
    _COME_ACC[f"physics.wheelPressure.{_c}"] = (f"TYRE_PRESS_{_m}", "..", 1.0)
    _COME_ACC[f"physics.brakeTemp.{_c}"] = (f"BRAKE_TEMP_{_m}", "C", 1.0)
    _COME_ACC[f"physics.suspensionTravel.{_c}"] = (f"SUS_TRAVEL_{_m}", "mm", 1000.0)

# canali che l'export di ACC non ha
_IN_PIU: dict[str, tuple[str, str, float]] = {
    "physics.fuel": ("FUEL", "..", 1.0),              # Kunos lo dichiara in kg, il gioco mostra litri
    "graphics.normalizedCarPosition": ("LAP_POSITION", "..", 1.0),
    "physics.steerAngle": ("STEER_INPUT", "..", 1.0),
    "physics.gear": ("GEAR_SM", "..", 1.0),
}
for _c, _m in _RUOTE.items():
    _IN_PIU[f"physics.tyreCoreTemp.{_c}"] = (f"TYRE_CORE_TEMP_{_m}", "C", 1.0)

# unità di ACC dei canali importati da MoTeC (`motec.*`), lette sui file veri
_UNITA_ACC = {
    "G_LAT": "m/s2", "G_LON": "m/s2", "ROTY": "rad/s", "STEERANGLE": "deg", "GEAR": "no",
    "TC": "..", "ABS": "..",
}
for _m in _RUOTE.values():
    _UNITA_ACC[f"WHEEL_SPEED_{_m}"] = "m/s"
    _UNITA_ACC[f"TYRE_TAIR_{_m}"] = "C"


class EsportazioneImpossibile(ValueError):
    """La sessione non ha ciò che serve per un file MoTeC."""


@dataclass
class Esportazione:
    nome_base: str               # senza estensione, nel formato dei nomi di ACC
    ld: bytes
    ldx: bytes
    canali: list[str]
    note: list[str] = field(default_factory=list)

    def zip(self) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(f"{self.nome_base}.ld", self.ld)
            z.writestr(f"{self.nome_base}.ldx", self.ldx)
        return buffer.getvalue()


def _pezzo(testo: str | None, predefinito: str) -> str:
    pulito = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in (testo or "").strip())
    return pulito.strip("_") or predefinito


def esporta(bundle: SessionBundle, canali: dict[str, np.ndarray]) -> Esportazione:
    if not canali or POSIZIONE not in canali or TEMPO not in canali:
        raise EsportazioneImpossibile("la sessione non ha i canali registrati")
    n = int(canali[TEMPO].size)
    if n < FREQUENZA_HZ:
        raise EsportazioneImpossibile("registrazione troppo corta per un file MoTeC")

    note: list[str] = []
    da_scrivere = [CanaleDaScrivere("LAP_BEACON", "..", FREQUENZA_HZ, np.zeros(n, np.float32))]
    for tabella in (_COME_ACC, _IN_PIU):
        for canonico, (nome, unita, fattore) in tabella.items():
            serie = canali.get(canonico)
            if serie is not None and serie.size == n:
                da_scrivere.append(CanaleDaScrivere(
                    nome, unita, FREQUENZA_HZ, np.asarray(serie, dtype=np.float64) * fattore))
    presenti = {c.nome for c in da_scrivere}
    for chiave in sorted(canali):
        if chiave.startswith("motec.") and canali[chiave].size == n:
            nome = chiave.removeprefix("motec.")
            if nome not in presenti:
                da_scrivere.append(CanaleDaScrivere(
                    nome, _UNITA_ACC.get(nome, ".."), FREQUENZA_HZ, canali[chiave]))
    if "physics.fuel" in canali:
        note.append("FUEL: il documento Kunos dichiara il serbatoio in kg, il gioco mostra litri")

    # passaggi sul traguardo dai giri ritagliati dal motore
    giri = dividi_in_giri(canali)
    # I beacon seguono i tempi UFFICIALI dei giri (al millesimo), non il campione a 100 Hz:
    # altrimenti il «Fastest Time» dichiarato e la distanza fra due beacon differirebbero
    # fino a 10 ms, e un lettore attento (il nostro) lo segnalerebbe. Ci si riaggancia al
    # campione solo dove un giro non ha tempo, o dove i due si allontanano.
    tempi_giro = {g.numero: g.tempo_ms for g in bundle.giri if g.tempo_ms}
    beacon_s: list[float] = []
    atteso: float | None = None
    for g in giri:
        campione = g.inizio / FREQUENZA_HZ
        inizio = atteso if atteso is not None and abs(atteso - campione) < 0.05 else campione
        # la partenza di un giro è un traguardo, salvo l'inizio di una registrazione a metà pista
        if g.inizio > 0 or g.completo:
            beacon_s.append(round(inizio, 6))
        tempo = tempi_giro.get(g.numero)
        atteso = inizio + tempo / 1000 if (tempo and g.completo) else None
    # l'ultimo giro chiuso sulla fine della registrazione (la demo) ha bisogno del suo traguardo
    if giri and giri[-1].completo and giri[-1].fine == n:
        beacon_s.append(round(atteso if atteso is not None else n / FREQUENZA_HZ, 6))
    beacon_s = sorted(set(beacon_s))
    tempi_bundle = {g.numero: g.tempo_ms for g in bundle.giri if g.tempo_ms and g.valido}
    migliore_ms, giro_migliore = None, None
    if tempi_bundle:
        numero, migliore_ms = min(tempi_bundle.items(), key=lambda kv: kv[1])
        giro = next((g for g in giri if g.numero == numero), None)
        if giro is not None:
            # ACC conta i tratti dal primo (prima del primo beacon = 0)
            giro_migliore = sum(1 for b in beacon_s if b <= giro.inizio / FREQUENZA_HZ + 1e-9)

    from app.core import catalog

    vettura = catalog.resolve_car(bundle.meta.car) if bundle.meta.car else None
    nome_vettura = catalog.display_name_car(vettura) if vettura else (bundle.meta.car or "")
    quando = bundle.meta.iniziata_il or bundle.meta.importato_il or datetime.now(timezone.utc)
    nome_base = (f"{_pezzo(bundle.meta.track, 'pista')}-{_pezzo(bundle.meta.car, 'vettura')}-0-"
                 f"{quando:%Y.%m.%d-%H.%M.%S}")
    ld = scrivi_ld(da_scrivere, vettura=nome_vettura, pista=bundle.meta.track or "",
                   data_ora=quando, pilota=bundle.meta.pilota or "")
    ldx = scrivi_ldx(beacon_s, migliore_ms, giro_migliore)
    return Esportazione(nome_base=nome_base, ld=ld, ldx=ldx,
                        canali=[c.nome for c in da_scrivere], note=note)
