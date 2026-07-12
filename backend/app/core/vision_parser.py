"""
vision_parser.py — PitWall.AI
Parsing di screenshot del setup ACC tramite Claude Vision API.
Estrae automaticamente i parametri visibili nell'immagine.
"""

import re
import json
import base64
import anthropic
from pathlib import Path
from .setup_params import get_all_params_flat, validate_setup


# ─────────────────────────────────────────────
# PROMPT SPECIFICO PER LETTURA SCREENSHOT ACC
# ─────────────────────────────────────────────

VISION_SYSTEM_PROMPT = """Sei un sistema OCR specializzato nel riconoscimento di screenshot
del menu di setup di Assetto Corsa Competizione (ACC).

Il tuo unico compito è estrarre i valori numerici dei parametri di setup visibili
nell'immagine fornita e restituirli in formato JSON.

REGOLE OBBLIGATORIE:
1. Restituisci SOLO un oggetto JSON valido, nessun testo prima o dopo.
2. Usa ESATTAMENTE le chiavi seguenti (solo quelle visibili nell'immagine):
   Tyres: tire_press_fl, tire_press_fr, tire_press_rl, tire_press_rr,
           camber_fl, camber_fr, camber_rl, camber_rr,
           toe_fl, toe_fr, toe_rl, toe_rr, caster
   Electronics: tc1, tc2, abs, ecu_map, brake_bias
   Mechanical Grip: arb_front, arb_rear, wheel_rate_front, wheel_rate_rear,
                    bumpstop_rate_front, bumpstop_rate_rear,
                    bumpstop_range_front, bumpstop_range_rear, preload
   Dampers: bump_fl, fast_bump_fl, rebound_fl, fast_rebound_fl,
             bump_fr, fast_bump_fr, rebound_fr, fast_rebound_fr,
             bump_rl, fast_bump_rl, rebound_rl, fast_rebound_rl,
             bump_rr, fast_bump_rr, rebound_rr, fast_rebound_rr
   Aero: ride_height_front, ride_height_rear, splitter, wing,
         brake_duct_front, brake_duct_rear
3. Se un parametro non è visibile nell'immagine, NON includerlo nel JSON.
4. I valori devono essere numeri (float o int), non stringhe.
5. Se un valore è ambiguo o illeggibile, NON includerlo.

Esempio output atteso:
{"tc1": 4, "tc2": 3, "abs": 5, "tire_press_fl": 25.0, "camber_fl": -3.0}
"""


def image_to_base64(image_path: str) -> tuple[str, str]:
    """
    Converte un file immagine in base64 con media_type corretto.
    Restituisce (base64_data, media_type).
    """
    path = Path(image_path)
    suffix = path.suffix.lower()

    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }

    media_type = media_type_map.get(suffix, "image/png")

    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    return data, media_type


def parse_setup_from_image(
    image_source,  # path str oppure bytes (da Streamlit file_uploader)
    api_key: str,
    media_type: str | None = None,  # MIME dell'upload; usato solo se image_source è bytes
) -> dict:
    """
    Invia uno screenshot ACC all'API Claude Vision e restituisce
    un dizionario con i parametri riconosciuti.

    Parametri:
        image_source : path al file locale O bytes da st.file_uploader
        api_key      : Anthropic API key
        media_type   : MIME dell'immagine (es. UploadedFile.type di Streamlit);
                       usato solo con bytes, altrimenti default "image/png"

    Restituisce:
        {
          "params": dict,        # parametri estratti {chiave: valore}
          "validated": bool,     # True se tutti i valori sono nei range
          "errors": list[str],   # lista errori di validazione
          "raw_response": str,   # JSON grezzo restituito dall'LLM
        }
    """
    client = anthropic.Anthropic(api_key=api_key)

    # Gestione input: bytes da Streamlit o path su disco
    if isinstance(image_source, (bytes, bytearray)):
        image_data = base64.standard_b64encode(image_source).decode("utf-8")
        media_type = media_type or "image/png"  # MIME dell'upload se fornito, altrimenti default
    else:
        image_data, media_type = image_to_base64(image_source)

    # Chiamata API con Vision
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=VISION_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Analizza questa schermata di setup ACC ed estrai "
                            "tutti i parametri visibili come JSON."
                        ),
                    },
                ],
            }
        ],
    )

    raw_response = message.content[0].text.strip()

    # Pulizia JSON (rimuove eventuali backtick markdown)
    clean_json = re.sub(r"```(?:json)?|```", "", raw_response).strip()

    try:
        params = json.loads(clean_json)
    except json.JSONDecodeError:
        return {
            "params": {},
            "validated": False,
            "errors": ["Impossibile interpretare la risposta dell'AI. "
                       "Verifica la qualità dell'immagine."],
            "raw_response": raw_response,
        }

    # Conversione valori in tipi numerici corretti
    cleaned_params = {}
    for k, v in params.items():
        try:
            cleaned_params[k] = float(v) if "." in str(v) else int(v)
        except (ValueError, TypeError):
            pass  # scarta valori non numerici

    # Validazione range
    errors = validate_setup(cleaned_params)
    validated = len(errors) == 0

    return {
        "params": cleaned_params,
        "validated": validated,
        "errors": errors,
        "raw_response": raw_response,
    }


def summarize_parsed_setup(parsed: dict) -> str:
    """
    Genera un riepilogo testuale dei parametri riconosciuti,
    da mostrare all'utente prima della conferma.
    """
    flat = get_all_params_flat()
    params = parsed.get("params", {})

    if not params:
        return "⚠️ Nessun parametro riconosciuto nell'immagine."

    from .setup_params import SETUP_SECTIONS
    section_labels = {k: v["label"] for k, v in SETUP_SECTIONS.items()}
    grouped = {}

    for key, value in params.items():
        if key in flat:
            sec = flat[key]["section"]
            label = flat[key]["label"]
            unit = flat[key]["unit"]
            unit_str = f" {unit}" if unit else ""
            grouped.setdefault(sec, []).append(f"**{label}:** {value}{unit_str}")

    lines = [f"✅ **{len(params)} parametri riconosciuti:**\n"]
    for sec, items in grouped.items():
        lines.append(f"**{section_labels.get(sec, sec)}**")
        lines.extend([f"  - {item}" for item in items])
        lines.append("")

    if parsed.get("errors"):
        lines.append("⚠️ **Valori fuori range rilevati:**")
        for err in parsed["errors"]:
            lines.append(f"  - {err}")

    return "\n".join(lines)
