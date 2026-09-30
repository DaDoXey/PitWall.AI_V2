"""bundle/adapters/acc_setup.py — dal setup salvato in ACC al bundle (L1 · Fase 2).

Legge un file di `Documents/Assetto Corsa Competizione/Setups/<auto>/<pista>/*.json`
e ne ricava un `Setup` canonico. Sostituisce l'inserimento a mano dei 49 slider e la
lettura da screenshot come via principale: il file è il dato esatto, lo screenshot
era una fotografia da interpretare.

**Cosa converte e cosa no** (decisione 7 del 14/09, «niente numeri inventati»):
- i valori di ACC sono **indici di click**. Si portano nel valore che il gioco mostra
  (psi, °, N/m…) solo con la tabella della vettura in `car_setup_ranges.json`
  (`setup_params.regole_vettura`), e solo per i parametri la cui regola è stata letta
  in gioco o viene da almeno due fonti concordi: il `ValoreSetup` dice quale (`fonte`).
  Tutto il resto resta in click, `unita="click"`, `verificato=False` (INC-V2-003);
- **camber**: si legge il click di `camber`, come tutti gli altri. Fino alla Entry #057
  si prendeva `staticCamber` (un float in gradi) come valore già verificato, ma non è
  quello che il gioco mostra: con il click 0 la BMW M4 mostra -4.0°, `staticCamber`
  dice -4.21. Resta nel grezzo;
- **altezze**: anteriore dal primo valore di `rideHeight`, posteriore dal **terzo**
  (Race Element e acc-setup-diff concordano; fino alla #057 si prendeva il secondo);
- tutto il resto del file resta comunque in `Setup.raw`, intatto.

**Assunzioni dichiarate.** Due mappature non sono deducibili con certezza dal file e
vengono annotate in `Setup.assunzioni`, così chi legge sa cosa è stato interpretato:
l'uso di `bumpStopRateUp` per l'unico parametro bumpstop dei 49, e il caster preso dal
lato sinistro. Si chiudono con un riscontro in gioco, non con una supposizione più
sicura di sé.

Struttura verificata il 14/09/2026 su 8 file reali (GT3, GT4, GT2, Challenge): stesse
chiavi, `drivetrain` minuscolo, array a 4 elementi in ordine **FL, FR, RL, RR**,
`brakeDuct` a 2 (anteriore, posteriore), `casterLF`/`casterRF`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.bundle.adapters.lettura import FileAccIllegibile, carica_json
from app.bundle.schema import Setup, ValoreSetup
from app.core.setup_params import click_in_reale, regole_vettura

# Ordine degli array a 4 elementi di ACC.
FL, FR, RL, RR = 0, 1, 2, 3

# chiave PitWall -> (percorso nel JSON di ACC, indice nell'array o None)
MAPPA: dict[str, tuple[tuple[str, ...], int | None]] = {
    # ── gomme ──
    "tire_press_fl": (("basicSetup", "tyres", "tyrePressure"), FL),
    "tire_press_fr": (("basicSetup", "tyres", "tyrePressure"), FR),
    "tire_press_rl": (("basicSetup", "tyres", "tyrePressure"), RL),
    "tire_press_rr": (("basicSetup", "tyres", "tyrePressure"), RR),
    "camber_fl": (("basicSetup", "alignment", "camber"), FL),
    "camber_fr": (("basicSetup", "alignment", "camber"), FR),
    "camber_rl": (("basicSetup", "alignment", "camber"), RL),
    "camber_rr": (("basicSetup", "alignment", "camber"), RR),
    "toe_fl": (("basicSetup", "alignment", "toe"), FL),
    "toe_fr": (("basicSetup", "alignment", "toe"), FR),
    "toe_rl": (("basicSetup", "alignment", "toe"), RL),
    "toe_rr": (("basicSetup", "alignment", "toe"), RR),
    "caster": (("basicSetup", "alignment", "casterLF"), None),
    # ── elettronica ──
    "tc1": (("basicSetup", "electronics", "tC1"), None),
    "tc2": (("basicSetup", "electronics", "tC2"), None),
    "abs": (("basicSetup", "electronics", "abs"), None),
    "ecu_map": (("basicSetup", "electronics", "eCUMap"), None),
    # ── meccanica ──
    "brake_bias": (("advancedSetup", "mechanicalBalance", "brakeBias"), None),
    "arb_front": (("advancedSetup", "mechanicalBalance", "aRBFront"), None),
    "arb_rear": (("advancedSetup", "mechanicalBalance", "aRBRear"), None),
    "wheel_rate_front": (("advancedSetup", "mechanicalBalance", "wheelRate"), FL),
    "wheel_rate_rear": (("advancedSetup", "mechanicalBalance", "wheelRate"), RL),
    "bumpstop_rate_front": (("advancedSetup", "mechanicalBalance", "bumpStopRateUp"), FL),
    "bumpstop_rate_rear": (("advancedSetup", "mechanicalBalance", "bumpStopRateUp"), RL),
    "bumpstop_range_front": (("advancedSetup", "mechanicalBalance", "bumpStopWindow"), FL),
    "bumpstop_range_rear": (("advancedSetup", "mechanicalBalance", "bumpStopWindow"), RL),
    "preload": (("advancedSetup", "drivetrain", "preload"), None),
    # ── ammortizzatori ──
    "bump_fl": (("advancedSetup", "dampers", "bumpSlow"), FL),
    "bump_fr": (("advancedSetup", "dampers", "bumpSlow"), FR),
    "bump_rl": (("advancedSetup", "dampers", "bumpSlow"), RL),
    "bump_rr": (("advancedSetup", "dampers", "bumpSlow"), RR),
    "fast_bump_fl": (("advancedSetup", "dampers", "bumpFast"), FL),
    "fast_bump_fr": (("advancedSetup", "dampers", "bumpFast"), FR),
    "fast_bump_rl": (("advancedSetup", "dampers", "bumpFast"), RL),
    "fast_bump_rr": (("advancedSetup", "dampers", "bumpFast"), RR),
    "rebound_fl": (("advancedSetup", "dampers", "reboundSlow"), FL),
    "rebound_fr": (("advancedSetup", "dampers", "reboundSlow"), FR),
    "rebound_rl": (("advancedSetup", "dampers", "reboundSlow"), RL),
    "rebound_rr": (("advancedSetup", "dampers", "reboundSlow"), RR),
    "fast_rebound_fl": (("advancedSetup", "dampers", "reboundFast"), FL),
    "fast_rebound_fr": (("advancedSetup", "dampers", "reboundFast"), FR),
    "fast_rebound_rl": (("advancedSetup", "dampers", "reboundFast"), RL),
    "fast_rebound_rr": (("advancedSetup", "dampers", "reboundFast"), RR),
    # ── aerodinamica ──
    "ride_height_front": (("advancedSetup", "aeroBalance", "rideHeight"), 0),
    "ride_height_rear": (("advancedSetup", "aeroBalance", "rideHeight"), 2),
    "splitter": (("advancedSetup", "aeroBalance", "splitter"), None),
    "wing": (("advancedSetup", "aeroBalance", "rearWing"), None),
    "brake_duct_front": (("advancedSetup", "aeroBalance", "brakeDuct"), 0),
    "brake_duct_rear": (("advancedSetup", "aeroBalance", "brakeDuct"), 1),
}

ASSUNZIONI = {
    "bumpstop": "bumpstop_rate_* letto da bumpStopRateUp; bumpStopRateDn resta solo "
                "nel grezzo (i 49 parametri hanno un valore solo per asse)",
    "caster": "caster preso da casterLF (sinistra); casterRF differiva in questo file",
}


class SetupAccError(ValueError):
    """Il file non è un setup di ACC utilizzabile."""


def _pesca(dati: dict[str, Any], percorso: tuple[str, ...]) -> Any:
    nodo: Any = dati
    for chiave in percorso:
        if not isinstance(nodo, dict) or chiave not in nodo:
            return None
        nodo = nodo[chiave]
    return nodo


def leggi_setup_acc(sorgente: str | Path | bytes, nome: str | None = None) -> Setup:
    """Legge un setup di ACC e lo porta nel formato canonico.

    Args:
        sorgente: percorso del file o i suoi byte.
        nome: nome da dare al setup; se assente si usa il nome del file senza estensione.

    Raises:
        SetupAccError: il file non è leggibile o non ha la forma di un setup ACC.
    """
    try:
        dati, nome_file = carica_json(sorgente)
    except FileAccIllegibile as e:
        raise SetupAccError(str(e)) from e

    if "basicSetup" not in dati and "advancedSetup" not in dati:
        raise SetupAccError(
            "non sembra un setup di ACC: mancano sia basicSetup che advancedSetup"
        )

    car = dati.get("carName")
    if isinstance(car, str):
        car = car.strip().lower() or None
    else:
        car = None
    regole = regole_vettura(car)

    valori: dict[str, ValoreSetup] = {}
    assunzioni: list[str] = []

    for chiave, (percorso, indice) in MAPPA.items():
        grezzo = _pesca(dati, percorso)
        if grezzo is None:
            continue
        if indice is not None:
            if not isinstance(grezzo, list) or len(grezzo) <= indice:
                continue
            grezzo = grezzo[indice]
        if isinstance(grezzo, bool) or not isinstance(grezzo, (int, float)):
            continue
        regola = regole.get(chiave)
        reale = click_in_reale(regola, grezzo) if regola else None
        if reale is None:
            valori[chiave] = ValoreSetup(raw=grezzo)
        else:
            valori[chiave] = ValoreSetup(
                raw=grezzo, reale=reale, unita=regola["unita"], verificato=True,
                fonte=regola["stato"],
            )

    # Assunzioni da dichiarare, solo quelle che riguardano questo file.
    if isinstance(_pesca(dati, ("advancedSetup", "mechanicalBalance", "bumpStopRateUp")), list):
        assunzioni.append(ASSUNZIONI["bumpstop"])
    sx = _pesca(dati, ("basicSetup", "alignment", "casterLF"))
    dx = _pesca(dati, ("basicSetup", "alignment", "casterRF"))
    if sx is not None and dx is not None and sx != dx:
        assunzioni.append(ASSUNZIONI["caster"])

    if not valori:
        raise SetupAccError("setup riconosciuto ma senza alcun parametro leggibile")

    if nome is None and nome_file:
        nome = Path(nome_file).stem

    return Setup(car=car, nome=nome, valori=valori, raw=dati, assunzioni=assunzioni)


# ─────────────────────────────────────────────
# Ritorno al file di ACC (Entry #058): i click modificati nella pagina Setup
# ─────────────────────────────────────────────
# Parametri che PitWall tiene per asse ma che ACC scrive per ruota (o per lato):
# la modifica va anche sull'altra posizione, spostata della stessa quantità, così un
# asse resta simmetrico se lo era e mantiene la sua differenza se non lo era.
GEMELLI: dict[str, tuple[tuple[str, ...], int | None]] = {
    "caster": (("basicSetup", "alignment", "casterRF"), None),
    "wheel_rate_front": (("advancedSetup", "mechanicalBalance", "wheelRate"), FR),
    "wheel_rate_rear": (("advancedSetup", "mechanicalBalance", "wheelRate"), RR),
    "bumpstop_rate_front": (("advancedSetup", "mechanicalBalance", "bumpStopRateUp"), FR),
    "bumpstop_rate_rear": (("advancedSetup", "mechanicalBalance", "bumpStopRateUp"), RR),
    "bumpstop_range_front": (("advancedSetup", "mechanicalBalance", "bumpStopWindow"), FR),
    "bumpstop_range_rear": (("advancedSetup", "mechanicalBalance", "bumpStopWindow"), RR),
}


def _scrivi(dati: dict[str, Any], percorso: tuple[str, ...], indice: int | None,
            valore: int) -> int | None:
    """Scrive `valore` nel punto indicato e torna quello che c'era (None se il punto non c'è)."""
    nodo = _pesca(dati, percorso[:-1])
    if not isinstance(nodo, dict) or percorso[-1] not in nodo:
        return None
    if indice is None:
        prima = nodo[percorso[-1]]
        nodo[percorso[-1]] = valore
        return prima if isinstance(prima, int) and not isinstance(prima, bool) else None
    lista = nodo[percorso[-1]]
    if not isinstance(lista, list) or len(lista) <= indice:
        return None
    prima = lista[indice]
    lista[indice] = valore
    return prima if isinstance(prima, int) and not isinstance(prima, bool) else None


def applica_click(raw: dict[str, Any], click: dict[str, int]) -> dict[str, Any]:
    """Il setup di ACC `raw` con i click nuovi, pronto da rimettere in Setups/.

    Tocca solo i punti dei parametri in `click`; tutto il resto del file (strategia,
    `bumpStopRateDn`, `staticCamber`…) resta com'è. Non modifica `raw`.

    Raises:
        SetupAccError: parametro sconosciuto, click non intero o negativo, o un punto
            che nel file non c'è (meglio fermarsi che scrivere un file diverso da ACC).
    """
    import copy

    dati = copy.deepcopy(raw)
    for chiave, nuovo in click.items():
        if chiave not in MAPPA:
            raise SetupAccError(f"parametro sconosciuto: {chiave}")
        if isinstance(nuovo, bool) or not isinstance(nuovo, int) or nuovo < 0:
            raise SetupAccError(f"{chiave}: il click deve essere un intero ≥ 0, non {nuovo!r}")
        percorso, indice = MAPPA[chiave]
        prima = _scrivi(dati, percorso, indice, nuovo)
        if prima is None:
            raise SetupAccError(f"{chiave}: nel file di ACC non c'è un valore intero da cambiare")
        gemello = GEMELLI.get(chiave)
        if gemello and nuovo != prima:
            altro = _pesca(dati, gemello[0])
            if gemello[1] is not None:
                altro = altro[gemello[1]] if isinstance(altro, list) and len(altro) > gemello[1] else None
            if isinstance(altro, int) and not isinstance(altro, bool):
                _scrivi(dati, gemello[0], gemello[1], max(0, altro + nuovo - prima))
    return dati
