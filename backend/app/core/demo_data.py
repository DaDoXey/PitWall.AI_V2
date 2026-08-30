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
    # Anno del MODELLO, non della stagione: allineato al catalogo ACC
    # (data/cars.json → bmw_m4_gt3.year = 2021). Prima era "2024", che in
    # Dashboard finiva accanto alla scheda vettura del catalogo creando
    # un'incoerenza visibile ("· 2024" nell'header, "2021" nella card).
    "car_year": "2021",
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
# A CALDO — display telemetria. Finestra ACC v1.9 reale (dry DHF, tutte le classi
# GT) 26.0–27.0 psi (vedi SPEC_ERRATA.md ERR-02 e prompts/system_prompt_v4.txt).
# I valori a caldo sono SEMPRE superiori a quelli a freddo (~+1.5–2.0 psi tipico):
# anteriori in finestra, posteriori sotto → caso didattico "retrotreno scarico / sovrasterzo".
HOT_PRESSURES = {"fl": 26.5, "fr": 26.7, "rl": 25.7, "rr": 25.5}
HOT_PRESS_WINDOW = (26.0, 27.0)   # psi (finestra operativa GT a caldo, ACC v1.9)

# A FREDDO — riferimento CSV/garage (NON usato nei gauge "a caldo").
# Delta cold→hot uniforme a +1.5 psi (fisicamente realistico per ACC v1.9, vedi ERR-02):
#   ant. 25.0→26.5 / 25.2→26.7;  post. 24.2→25.7 / 24.0→25.5 (tutte +1.5).
# I posteriori a freddo (24.2/24.0) sono SOTTO la finestra a freddo (24.5–25.5):
# rende esplicita la causa "pressioni retrotreno impostate troppo basse".
COLD_PRESSURES = {"fl": 25.0, "fr": 25.2, "rl": 24.2, "rr": 24.0}

# Finestra pressione a FREDDO ottimale (psi) — usata SOLO dal layer presentazionale
# del Setup per colorare i 4 valori pressione (verde in finestra, ambra entro il
# margine, rosso oltre). Allineata alla finestra a freddo documentata sopra
# (24.5–25.5): coerente con la storia demo (post. 24.2/24.0 = sotto finestra).
# Soglie tunable in un punto solo.
COLD_PRESS_WINDOW = (24.5, 25.5)      # psi (verde)
COLD_PRESS_AMBER_MARGIN = 0.6         # psi oltre il bordo → ambra; oltre ancora → rosso

# Pressione media (a caldo) per la card Dashboard.
# Coerente con i 4 gauge: media aritmetica dei 4 valori HOT.
PRESS_AVG_HOT = round(sum(HOT_PRESSURES.values()) / 4, 1)   # → 26.1

# Parametri evidenziati da Gigi nella correzione demo (rosso negli slider Setup).
# Coerenti con la DEMO_RESPONSE della console: pressioni posteriori + precarico.
SUGGESTED_PARAMS = {"tire_press_rl", "tire_press_rr", "preload"}

# Pressioni a CALDO per GIRO (psi) — salgono col riscaldamento gomma nel corso
# dello stint e terminano ESATTAMENTE sui valori HOT_PRESSURES (ultimo giro =
# valore mostrato dai gauge → coerenza garantita per costruzione, come TYRE_TEMP_MAX).
# Usate SOLO dalla tabella giro-per-giro della Telemetria; i gauge restano su HOT_PRESSURES.
HOT_PRESS_SERIES = {
    "fl": [25.7, 25.9, 26.1, 26.2, 26.3, 26.4, 26.5, 26.5],
    "fr": [25.8, 26.0, 26.2, 26.4, 26.5, 26.6, 26.7, 26.7],
    "rl": [24.9, 25.1, 25.3, 25.4, 25.5, 25.6, 25.7, 25.7],
    "rr": [24.7, 24.9, 25.1, 25.2, 25.3, 25.4, 25.5, 25.5],
}
# Coerenza: l'ultimo valore di ogni serie coincide con HOT_PRESSURES.
# Check esplicito (non `assert`: resta attivo anche con python -O).
if not all(HOT_PRESS_SERIES[p][-1] == HOT_PRESSURES[p] for p in HOT_PRESSURES):
    raise ValueError("demo_data: HOT_PRESS_SERIES non coerente con HOT_PRESSURES")

# ─────────────────────────────────────────────
# CARBURANTE — consumo per giro (L), "stabile" attorno a 3.2
# ─────────────────────────────────────────────
FUEL_PER_LAP = [3.2, 3.1, 3.3, 3.0, 3.2, 3.3, 3.2, 3.3]

# ─────────────────────────────────────────────
# TEMPI SUL GIRO — 8 giri (secondi). Storia coerente con temp/consumo: out-lap più
# lento (gomme fredde, macchina carica), best a metà stint, poi degrado mentre la
# Post.DX surriscalda (coerente con TYRE_TEMP_SERIES rr → 105°C).
# Il minimo coincide ESATTAMENTE con SESSION["best_lap"] (stesso patto di coerenza
# di TYRE_TEMP_MAX / HOT_PRESS_SERIES).
# ─────────────────────────────────────────────
LAP_TIMES = [109.412, 108.301, 107.945, 107.812, 108.017, 108.523, 108.874, 109.156]


def _fmt_lap(sec: float) -> str:
    m = int(sec // 60)
    return f"{m}:{sec - m * 60:06.3f}"


# Coerenza: il giro più veloce coincide con SESSION["best_lap"] (check attivo anche con -O).
if _fmt_lap(min(LAP_TIMES)) != SESSION["best_lap"]:
    raise ValueError("demo_data: LAP_TIMES min non coerente con SESSION['best_lap']")


def lap_axis():
    """Asse giri 1..N coerente con la lunghezza delle serie."""
    return list(range(1, SESSION["laps"] + 1))
