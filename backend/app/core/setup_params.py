"""
setup_params.py — PitWall.AI
Definizione di tutti i parametri di setup ACC GT3, suddivisi per sezione.
Questo modulo è la fonte di verità per range, unità e descrizioni.
"""

# ─────────────────────────────────────────────
# STRUTTURA DATI
# Ogni parametro è un dict con:
#   label    : nome visualizzato in UI
#   min/max  : range valido in ACC (conservativo, car-agnostic)
#   step     : incremento slider
#   unit     : unità di misura
#   default  : valore di default (base aggressive setup)
#   tip      : breve descrizione per il tooltip novizi
# ─────────────────────────────────────────────

SETUP_SECTIONS = {

    # ══════════════════════════════════════════
    # TAB 1 — TYRES
    # ══════════════════════════════════════════
    "tyres": {
        "label": "Gomme",
        "params": {
            # Pressioni (freddo, psi)
            "tire_press_fl": {
                "label": "Pressione FL",
                "min": 20.0, "max": 35.0, "step": 0.1,
                "unit": "psi", "default": 26.5,
                "tip": "Pressione gonfiaggio anteriore sinistra. Misura a freddo in garage."
            },
            "tire_press_fr": {
                "label": "Pressione FR",
                "min": 20.0, "max": 35.0, "step": 0.1,
                "unit": "psi", "default": 26.5,
                "tip": "Pressione gonfiaggio anteriore destra."
            },
            "tire_press_rl": {
                "label": "Pressione RL",
                "min": 20.0, "max": 35.0, "step": 0.1,
                "unit": "psi", "default": 26.8,
                "tip": "Pressione gonfiaggio posteriore sinistra."
            },
            "tire_press_rr": {
                "label": "Pressione RR",
                "min": 20.0, "max": 35.0, "step": 0.1,
                "unit": "psi", "default": 26.8,
                "tip": "Pressione gonfiaggio posteriore destra."
            },
            # Camber (°, negativo = inclinazione verso l'interno)
            "camber_fl": {
                "label": "Camber FL",
                "min": -4.0, "max": -2.5, "step": 0.1,
                "unit": "°", "default": -3.0,
                "tip": "Inclinazione ruota anteriore sinistra. Valori più negativi aumentano il contatto in curva."
            },
            "camber_fr": {
                "label": "Camber FR",
                "min": -4.0, "max": -2.5, "step": 0.1,
                "unit": "°", "default": -3.0,
                "tip": "Inclinazione ruota anteriore destra."
            },
            "camber_rl": {
                "label": "Camber RL",
                "min": -3.0, "max": -1.5, "step": 0.1,
                "unit": "°", "default": -2.0,
                "tip": "Inclinazione ruota posteriore sinistra."
            },
            "camber_rr": {
                "label": "Camber RR",
                "min": -3.0, "max": -1.5, "step": 0.1,
                "unit": "°", "default": -2.0,
                "tip": "Inclinazione ruota posteriore destra."
            },
            # Toe (°, positivo = toe-out per anteriori, toe-in per posteriori)
            "toe_fl": {
                "label": "Toe FL",
                "min": -0.40, "max": 0.40, "step": 0.01,
                "unit": "°", "default": 0.06,
                "tip": "Angolo convergenza/divergenza anteriore sinistra."
            },
            "toe_fr": {
                "label": "Toe FR",
                "min": -0.40, "max": 0.40, "step": 0.01,
                "unit": "°", "default": 0.06,
                "tip": "Angolo convergenza/divergenza anteriore destra."
            },
            "toe_rl": {
                "label": "Toe RL",
                "min": -0.40, "max": 0.40, "step": 0.01,
                "unit": "°", "default": 0.16,
                "tip": "Convergenza posteriore sinistra. Valori positivi migliorano la stabilità."
            },
            "toe_rr": {
                "label": "Toe RR",
                "min": -0.40, "max": 0.40, "step": 0.01,
                "unit": "°", "default": 0.16,
                "tip": "Convergenza posteriore destra."
            },
            # Caster (solo anteriore)
            "caster": {
                "label": "Caster",
                "min": 5.0, "max": 14.0, "step": 0.1,
                "unit": "°", "default": 10.0,
                "tip": "Angolo di caster anteriore. Valori alti migliorano la stabilità in rettilineo."
            },
        }
    },

    # ══════════════════════════════════════════
    # TAB 2 — ELECTRONICS
    # ══════════════════════════════════════════
    "electronics": {
        "label": "Elettronica",
        "params": {
            "tc1": {
                "label": "TC1 (Traction Control)",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 4,
                "tip": "Controllo trazione principale. 0 = disattivato, 11 = massima assistenza."
            },
            "tc2": {
                "label": "TC2 (TC Cut)",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 4,
                "tip": "Controlla il taglio motore del TC. Agisce in combinazione con TC1."
            },
            "abs": {
                "label": "ABS",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 5,
                "tip": "Sistema antibloccaggio freni. 0 = off, 11 = massima assistenza."
            },
            "ecu_map": {
                "label": "ECU Map",
                "min": 1, "max": 8, "step": 1,
                "unit": "", "default": 1,
                "tip": "Mappatura motore. Map 1 = massima potenza. Map alte = minore consumo."
            },
            "brake_bias": {
                "label": "Brake Bias",
                "min": 46.0, "max": 68.0, "step": 0.2,
                "unit": "%", "default": 58.0,
                "tip": "Ripartizione frenata anteriore/posteriore. Valori alti = più frenata anteriore."
            },
        }
    },

    # ══════════════════════════════════════════
    # TAB 3 — MECHANICAL GRIP
    # ══════════════════════════════════════════
    "mechanical_grip": {
        "label": "Meccanica",
        "params": {
            "arb_front": {
                "label": "ARB Anteriore",
                "min": 0, "max": 10, "step": 1,
                "unit": "", "default": 5,
                "tip": "Barra antirollio anteriore. Valori alti = più rigidità in rollio = meno grip anteriore in curva."
            },
            "arb_rear": {
                "label": "ARB Posteriore",
                "min": 0, "max": 10, "step": 1,
                "unit": "", "default": 3,
                "tip": "Barra antirollio posteriore. Valori bassi = più grip posteriore in curva."
            },
            "wheel_rate_front": {
                "label": "Wheel Rate Ant.",
                "min": 70000, "max": 200000, "step": 1000,
                "unit": "N/m", "default": 120000,
                "tip": "Rigidità combinata molla + bumpstop anteriore. Valori bassi = più grip meccanico."
            },
            "wheel_rate_rear": {
                "label": "Wheel Rate Post.",
                "min": 70000, "max": 200000, "step": 1000,
                "unit": "N/m", "default": 130000,
                "tip": "Rigidità combinata molla + bumpstop posteriore."
            },
            "bumpstop_rate_front": {
                "label": "Bumpstop Rate Ant.",
                "min": 300, "max": 2000, "step": 100,
                "unit": "N/mm", "default": 900,
                "tip": "Rigidità del bumpstop anteriore. Valori bassi = comportamento più progressivo a fine corsa."
            },
            "bumpstop_rate_rear": {
                "label": "Bumpstop Rate Post.",
                "min": 300, "max": 2000, "step": 100,
                "unit": "N/mm", "default": 900,
                "tip": "Rigidità del bumpstop posteriore."
            },
            "bumpstop_range_front": {
                "label": "Bumpstop Range Ant.",
                "min": 0, "max": 80, "step": 1,
                "unit": "mm", "default": 30,
                "tip": "Escursione sospensione prima di toccare il bumpstop. Valori bassi = il bumpstop lavora prima."
            },
            "bumpstop_range_rear": {
                "label": "Bumpstop Range Post.",
                "min": 0, "max": 80, "step": 1,
                "unit": "mm", "default": 30,
                "tip": "Escursione sospensione posteriore prima di toccare il bumpstop."
            },
            "preload": {
                "label": "Precarico Differenziale",
                "min": 20, "max": 200, "step": 10,
                "unit": "Nm", "default": 60,
                "tip": "Resistenza minima del differenziale. Valori alti = più stabilità in accelerazione, meno rotazione."
            },
        }
    },

    # ══════════════════════════════════════════
    # TAB 4 — DAMPERS
    # ══════════════════════════════════════════
    "dampers": {
        "label": "Ammortizzatori",
        "params": {
            # ANTERIORE SINISTRO
            "bump_fl": {
                "label": "Bump FL",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 6,
                "tip": "Smorzamento compressione lenta ant. sinistra. Valori alti = compressione più lenta."
            },
            "fast_bump_fl": {
                "label": "Fast Bump FL",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 6,
                "tip": "Smorzamento compressione rapida ant. sinistra (buche/cordoli)."
            },
            "rebound_fl": {
                "label": "Rebound FL",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 6,
                "tip": "Smorzamento estensione lenta ant. sinistra."
            },
            "fast_rebound_fl": {
                "label": "Fast Rebound FL",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 6,
                "tip": "Smorzamento estensione rapida ant. sinistra."
            },
            # ANTERIORE DESTRO
            "bump_fr": {
                "label": "Bump FR",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 6,
                "tip": "Smorzamento compressione lenta ant. destra."
            },
            "fast_bump_fr": {
                "label": "Fast Bump FR",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 6,
                "tip": "Smorzamento compressione rapida ant. destra."
            },
            "rebound_fr": {
                "label": "Rebound FR",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 6,
                "tip": "Smorzamento estensione lenta ant. destra."
            },
            "fast_rebound_fr": {
                "label": "Fast Rebound FR",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 6,
                "tip": "Smorzamento estensione rapida ant. destra."
            },
            # POSTERIORE SINISTRO
            "bump_rl": {
                "label": "Bump RL",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 5,
                "tip": "Smorzamento compressione lenta post. sinistra."
            },
            "fast_bump_rl": {
                "label": "Fast Bump RL",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 5,
                "tip": "Smorzamento compressione rapida post. sinistra."
            },
            "rebound_rl": {
                "label": "Rebound RL",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 5,
                "tip": "Smorzamento estensione lenta post. sinistra."
            },
            "fast_rebound_rl": {
                "label": "Fast Rebound RL",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 5,
                "tip": "Smorzamento estensione rapida post. sinistra."
            },
            # POSTERIORE DESTRO
            "bump_rr": {
                "label": "Bump RR",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 5,
                "tip": "Smorzamento compressione lenta post. destra."
            },
            "fast_bump_rr": {
                "label": "Fast Bump RR",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 5,
                "tip": "Smorzamento compressione rapida post. destra."
            },
            "rebound_rr": {
                "label": "Rebound RR",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 5,
                "tip": "Smorzamento estensione lenta post. destra."
            },
            "fast_rebound_rr": {
                "label": "Fast Rebound RR",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 5,
                "tip": "Smorzamento estensione rapida post. destra."
            },
        }
    },

    # ══════════════════════════════════════════
    # TAB 5 — AERO
    # ══════════════════════════════════════════
    "aero": {
        "label": "Aerodinamica",
        "params": {
            "ride_height_front": {
                "label": "Ride Height Ant.",
                "min": 46, "max": 80, "step": 1,
                "unit": "mm", "default": 52,
                "tip": "Altezza da terra anteriore. Valori bassi = più deportanza, più rischio raschiamento."
            },
            "ride_height_rear": {
                "label": "Ride Height Post.",
                "min": 60, "max": 100, "step": 1,
                "unit": "mm", "default": 72,
                "tip": "Altezza da terra posteriore. Il rake (differenza ant/post) influisce sull'equilibrio aerodinamico."
            },
            "splitter": {
                "label": "Splitter",
                "min": 1, "max": 10, "step": 1,
                "unit": "", "default": 6,
                "tip": "Deportanza anteriore. Valori alti = più grip anteriore ad alta velocità."
            },
            "wing": {
                "label": "Ala Posteriore",
                "min": 0, "max": 11, "step": 1,
                "unit": "", "default": 5,
                "tip": "Livello di deportanza posteriore. Valori alti = più grip, più resistenza all'aria."
            },
            "brake_duct_front": {
                "label": "Brake Duct Ant.",
                "min": 0, "max": 6, "step": 1,
                "unit": "", "default": 3,
                "tip": "Apertura condotti freno anteriore. 0 = chiuso (meno raffreddamento), 6 = massimo flusso."
            },
            "brake_duct_rear": {
                "label": "Brake Duct Post.",
                "min": 0, "max": 6, "step": 1,
                "unit": "", "default": 2,
                "tip": "Apertura condotti freno posteriore."
            },
        }
    },
}


def get_all_params_flat() -> dict:
    """
    Restituisce tutti i parametri in un dizionario piatto
    {param_key: {label, min, max, unit, default, tip, section}}
    Usato per costruire il contesto JSON da passare all'LLM.
    """
    flat = {}
    for section_key, section_data in SETUP_SECTIONS.items():
        for param_key, param_data in section_data["params"].items():
            flat[param_key] = {**param_data, "section": section_key}
    return flat


def validate_setup(setup: dict) -> list[str]:
    """
    Valida un dizionario di setup contro i range definiti.
    Restituisce lista di errori (lista vuota = setup valido).
    """
    errors = []
    flat = get_all_params_flat()
    for key, value in setup.items():
        if key not in flat:
            continue
        p = flat[key]
        if value < p["min"] or value > p["max"]:
            errors.append(
                f"{p['label']}: {value}{p['unit']} fuori range [{p['min']}–{p['max']}]"
            )
    return errors


def format_setup_for_prompt(setup: dict) -> str:
    """
    Formatta il dizionario setup come testo strutturato
    leggibile dall'LLM nel system prompt context.
    """
    flat = get_all_params_flat()
    sections_text = {}

    for key, value in setup.items():
        if key not in flat:
            continue
        p = flat[key]
        sec = p["section"]
        if sec not in sections_text:
            sections_text[sec] = []
        unit_str = f" {p['unit']}" if p["unit"] else ""
        sections_text[sec].append(f"  {p['label']}: {value}{unit_str}")

    lines = ["=== SETUP ATTUALE FORNITO DAL PILOTA ==="]
    section_labels = {k: v["label"] for k, v in SETUP_SECTIONS.items()}
    for sec, params_list in sections_text.items():
        lines.append(f"\n[{section_labels.get(sec, sec)}]")
        lines.extend(params_list)

    return "\n".join(lines)


# ─────────────────────────────────────────────
# OVERRIDE PER VETTURA / CIRCUITO (DB JSON)
# I generici sopra restano il fallback: get_params_for_car() applica
# eventuali override da data/car_setup_ranges.json, senza mai inventare valori.
# ─────────────────────────────────────────────
import copy
import json
from pathlib import Path

_CAR_DB_PATH = Path(__file__).resolve().parent / "data" / "car_setup_ranges.json"
_CAR_DB_CACHE = None


def _load_car_db() -> dict:
    """Carica (una volta) il DB JSON degli override. {} se assente o malformato."""
    global _CAR_DB_CACHE
    if _CAR_DB_CACHE is None:
        try:
            with open(_CAR_DB_PATH, encoding="utf-8") as f:
                _CAR_DB_CACHE = json.load(f)
        except Exception:
            _CAR_DB_CACHE = {}
    return _CAR_DB_CACHE


# Campi numerici sovrascrivibili (gli altri come label/unit/tip restano dal generico)
_OVERRIDABLE_FIELDS = ("min", "max", "step", "default")


def _apply_param_overrides(sections: dict, overrides: dict) -> None:
    """
    Applica override flat {param_key: {min/max/step/default}} alle sezioni (in-place).
    Cerca il param_key nella sezione corretta; ignora chiavi sconosciute e _status.
    """
    for param_key, fields in (overrides or {}).items():
        if not isinstance(fields, dict):
            continue
        for section in sections.values():
            if param_key in section["params"]:
                target = section["params"][param_key]
                for fld in _OVERRIDABLE_FIELDS:
                    if fld in fields:
                        target[fld] = fields[fld]
                break


def get_params_for_car(car: str | None = None, track: str | None = None) -> dict:
    """
    Restituisce la struttura SETUP_SECTIONS (stessa forma) con applicati gli
    override per vettura e, se presente, per circuito. Fallback ai generici se
    la vettura non è nel DB. Non modifica mai SETUP_SECTIONS (deepcopy).
    """
    sections = copy.deepcopy(SETUP_SECTIONS)

    db = _load_car_db()
    car_entry = (db.get("cars", {}) or {}).get(car) if car else None
    if not car_entry:
        return sections  # nessun override: generici identici

    # Override a livello vettura
    _apply_param_overrides(sections, car_entry.get("params", {}))

    # Override a livello circuito (hanno priorità sui generici e su quelli vettura)
    if track:
        track_entry = (car_entry.get("tracks", {}) or {}).get(track)
        if track_entry:
            _apply_param_overrides(sections, track_entry.get("params", {}))

    return sections
