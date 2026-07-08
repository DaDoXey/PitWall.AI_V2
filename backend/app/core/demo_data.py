"""ui/demo_data.py — SORGENTE DATI DEMO UNICA (Monza · BMW M4 GT3).

Tutti i numeri della demo "blindata" (Dashboard, Telemetria, Heatmap) leggono
DA QUI: un'unica fonte garantisce coerenza tra le schermate (requisito della
checklist pre-demo). Dati HARDCODED e coerenti con la storia:

    A Monza la BMW M4 GT3 surriscalda la posteriore destra (Post.DX) a causa
    delle pressioni basse al retrotreno.

DISTINZIONE PRESSIONI (obbligatoria, vedi SPEC_ERRATA.md):
  - COLD_PRESSURES  → pressioni a FREDDO, come da CSV/garage.
  - HOT_PRESSURES   → pressioni a CALDO, come mostrate sul display telemetria.
Le due NON sono equivalenti e non vanno mai mescolate.
"""

# ─────────────────────────────────────────────
# SESSIONE
# ─────────────────────────────────────────────
SESSION = {
    "track": "Monza",
    "track_nick": "Tempio della Velocità",
    "car": "BMW M4 GT3",
    "car_year": "2024",
    "laps": 8,
    "best_lap": "1:47.812",
    "stint": "Asciutto",
    "fuel_avg_per_lap": 3.2,   # L/giro
    "fuel_total": 25.6,        # L (= 8 × 3.2)
}

# Etichette gomme coerenti con la legenda telemetria.
TYRE_LABELS = {
    "fl": "Ant.SX",
    "fr": "Ant.DX",
    "rl": "Post.SX",
    "rr": "Post.DX",
}

# ─────────────────────────────────────────────
# TEMPERATURE GOMME — 8 giri (°C)
# Serie crescenti; la Post.DX (rr) sfora il limite finestra e arriva a 105°C.
# Il MAX di ogni serie (= ultimo valore) alimenta la heatmap: 88 / 90 / 95 / 105.
# ─────────────────────────────────────────────
TYRE_TEMP_SERIES = {
    "fl": [78, 80, 82, 83, 85, 86, 87, 88],
    "fr": [79, 81, 83, 85, 86, 88, 89, 90],
    "rl": [80, 83, 86, 88, 90, 92, 93, 95],
    "rr": [82, 86, 90, 94, 98, 101, 103, 105],
}

# Limite "finestra" temperatura (linea tratteggiata nel line chart).
TEMP_LIMIT = 95          # °C
TEMP_SCALE = (80, 105)   # scala colore heatmap (blu → rosso)

# Massimi per gomma (= valore heatmap). Derivati dalle serie per non divergere.
TYRE_TEMP_MAX = {pos: max(vals) for pos, vals in TYRE_TEMP_SERIES.items()}
# → {"fl": 88, "fr": 90, "rl": 95, "rr": 105}

# ─────────────────────────────────────────────
# PRESSIONI (psi)
# ─────────────────────────────────────────────
# A CALDO — display telemetria. Finestra ACC reale 28.5–30.0 psi (target 29.0,
# vedi prompts/system_prompt_v4.txt e INC-002). I valori a caldo sono SEMPRE
# superiori a quelli a freddo (+2.5–3.5 psi tipico): anteriori in finestra,
# posteriori sotto finestra → caso didattico "retrotreno scarico / sovrasterzo".
HOT_PRESSURES = {"fl": 29.0, "fr": 29.2, "rl": 28.2, "rr": 28.0}
HOT_PRESS_WINDOW = (28.5, 30.0)   # psi (finestra operativa GT3 a caldo)

# A FREDDO — riferimento CSV/garage (NON usato nei gauge "a caldo").
# Delta cold→hot uniforme a +2.5 psi (fisicamente realistico, vedi ERR-01/FASE 2.1):
#   ant. 26.5→29.0 (+2.5) / 26.5→29.2 (+2.7);  post. 25.7→28.2 (+2.5) / 25.5→28.0 (+2.5).
# I posteriori a freddo (25.7/25.5) sono SOTTO la finestra a freddo (26.0–27.0):
# rende esplicita la causa "pressioni retrotreno impostate troppo basse".
COLD_PRESSURES = {"fl": 26.5, "fr": 26.5, "rl": 25.7, "rr": 25.5}

# Finestra pressione a FREDDO ottimale (psi) — usata SOLO dal layer presentazionale
# del Setup per colorare i 4 valori pressione (verde in finestra, ambra entro il
# margine, rosso oltre). Allineata alla finestra a freddo documentata sopra
# (26.0–27.0): coerente con la storia demo (post. 25.7/25.5 = sotto finestra).
# Soglie tunable in un punto solo.
COLD_PRESS_WINDOW = (26.0, 27.0)      # psi (verde)
COLD_PRESS_AMBER_MARGIN = 0.6         # psi oltre il bordo → ambra; oltre ancora → rosso

# Pressione media (a caldo) per la card Dashboard.
# Coerente con i 4 gauge: media aritmetica dei 4 valori HOT.
PRESS_AVG_HOT = round(sum(HOT_PRESSURES.values()) / 4, 1)   # → 28.6

# Parametri evidenziati da Gigi nella correzione demo (rosso negli slider Setup).
# Coerenti con la DEMO_RESPONSE della console: pressioni posteriori + precarico.
SUGGESTED_PARAMS = {"tire_press_rl", "tire_press_rr", "preload"}

# Pressioni a CALDO per GIRO (psi) — salgono col riscaldamento gomma nel corso
# dello stint e terminano ESATTAMENTE sui valori HOT_PRESSURES (ultimo giro =
# valore mostrato dai gauge → coerenza garantita per costruzione, come TYRE_TEMP_MAX).
# Usate SOLO dalla tabella giro-per-giro della Telemetria; i gauge restano su HOT_PRESSURES.
HOT_PRESS_SERIES = {
    "fl": [28.2, 28.4, 28.6, 28.7, 28.8, 28.9, 29.0, 29.0],
    "fr": [28.3, 28.5, 28.7, 28.9, 29.0, 29.1, 29.2, 29.2],
    "rl": [27.4, 27.6, 27.8, 27.9, 28.0, 28.1, 28.2, 28.2],
    "rr": [27.2, 27.4, 27.6, 27.7, 27.8, 27.9, 28.0, 28.0],
}
# Coerenza: l'ultimo valore di ogni serie coincide con HOT_PRESSURES.
# Check esplicito (non `assert`: resta attivo anche con python -O).
if not all(HOT_PRESS_SERIES[p][-1] == HOT_PRESSURES[p] for p in HOT_PRESSURES):
    raise ValueError("demo_data: HOT_PRESS_SERIES non coerente con HOT_PRESSURES")

# ─────────────────────────────────────────────
# CARBURANTE — consumo per giro (L), "stabile" attorno a 3.2
# ─────────────────────────────────────────────
FUEL_PER_LAP = [3.2, 3.1, 3.3, 3.0, 3.2, 3.3, 3.2, 3.3]


def lap_axis():
    """Asse giri 1..N coerente con la lunghezza delle serie."""
    return list(range(1, SESSION["laps"] + 1))
