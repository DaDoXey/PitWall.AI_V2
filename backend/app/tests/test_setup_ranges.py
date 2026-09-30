"""
test_setup_ranges.py — la tabella dei click per vettura (Entry #057, INC-V2-003)

Controlla `data/car_setup_ranges.json` e la conversione in `core/setup_params.py`:
ogni regola dice da dove viene, una regola DA_VERIFICARE non si usa, e un click che
la regola non copre resta un click invece di diventare un numero inventato.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_setup_ranges.py

Non richiede pytest, né rete, né chiave.
"""

import json
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))  # -> backend/

from app.core.setup_params import (  # noqa: E402
    SETUP_SECTIONS,
    STATI_USABILI,
    click_in_reale,
    get_all_params_flat,
    get_params_for_car,
    regole_vettura,
)

DB = json.loads((BACKEND / "app" / "core" / "data" / "car_setup_ranges.json").read_text(encoding="utf-8"))

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []


def test(name: str, passed: bool, detail: str = ""):
    status = PASS if passed else FAIL
    line = f"{status}  {name}"
    if detail and not passed:
        line += f"\n        → {detail}"
    print(line)
    results.append((name, passed))


# ---------------------------------------------------------------------------
# 1. La tabella è in ordine
# ---------------------------------------------------------------------------
chiavi_49 = set(get_all_params_flat())
fonti_note = set(DB["_meta"]["fonti"])
stati_noti = set(DB["_meta"]["stati"])
tipi_noti = set(DB["_meta"]["tipi"])

test("R01 le chiavi delle vetture sono carName di ACC (minuscole, senza spazi)",
     all(k == k.lower() and " " not in k for k in DB["cars"]), str(list(DB["cars"])))

for car, voce in DB["cars"].items():
    params = voce["params"]
    test(f"R02 {car}: copre esattamente i 49 parametri di PitWall",
         set(params) == chiavi_49, str(set(params) ^ chiavi_49))
    test(f"R03 {car}: stato della vettura fra quelli dichiarati",
         voce["stato"] in stati_noti, voce["stato"])
    senza_fonti = [k for k, r in params.items() if not r.get("fonti")]
    test(f"R04 {car}: ogni regola dice da dove viene", not senza_fonti, str(senza_fonti))
    ignote = sorted({f for r in params.values() for f in r["fonti"]} - fonti_note)
    test(f"R05 {car}: ogni fonte citata è descritta in _meta", not ignote, str(ignote))
    tipi = sorted({r["tipo"] for r in params.values()} - tipi_noti)
    test(f"R06 {car}: solo tipi di regola conosciuti", not tipi, str(tipi))
    stati = sorted({r["stato"] for r in params.values() if "stato" in r} - stati_noti)
    test(f"R07 {car}: gli stati dei parametri sono fra quelli dichiarati", not stati, str(stati))
    usabili_con_una_fonte = [k for k, r in params.items()
                             if r.get("stato", voce["stato"]) == "fonti" and len(r["fonti"]) < 2]
    test(f"R08 {car}: una regola «fonti» ne ha almeno due",
         not usabili_con_una_fonte, str(usabili_con_una_fonte))
    unita_click = [k for k, r in params.items() if r["unita"] == "click"]
    test(f"R09 {car}: nessuna regola converte in «click»", not unita_click, str(unita_click))

# ---------------------------------------------------------------------------
# 2. BMW M4 GT3: le regole che si usano e quelle che no
# ---------------------------------------------------------------------------
bmw = regole_vettura("bmw_m4_gt3")
test("R10 BMW M4 GT3: 45 regole usabili", len(bmw) == 45, str(len(bmw)))
test("R11 caster, splitter e bumpstop rate restano fuori (DA_VERIFICARE)",
     not {"caster", "splitter", "bumpstop_rate_front", "bumpstop_rate_rear"} & set(bmw))
test("R12 ogni regola usabile porta il suo stato",
     all(r["stato"] in STATI_USABILI for r in bmw.values()))
test("R13 il carName si riconosce anche con spazi e maiuscole",
     len(regole_vettura("  BMW_M4_GT3 ")) == 45)
test("R14 vettura senza tabella → nessuna regola", regole_vettura("ferrari_296_gt3") == {})
test("R15 vettura assente → nessuna regola", regole_vettura(None) == {} and regole_vettura("") == {})

attesi = {  # click del setup di Monza 711b -> valore atteso dalle fonti
    ("tire_press_fr", 61): 26.4,
    ("toe_fl", 14): -0.06,
    ("toe_rl", 5): 0.05,
    ("ecu_map", 0): 1.0,
    ("brake_bias", 11): 51.8,
    ("wheel_rate_front", 1): 120000.0,
    ("wheel_rate_rear", 1): 105000.0,
    ("preload", 10): 120.0,
    ("ride_height_front", 4): 54.0,
    ("ride_height_rear", 0): 50.0,
    ("fast_rebound_rl", 30): 30.0,
}
sbagliati = {k: click_in_reale(bmw[k[0]], k[1]) for k, v in attesi.items()
             if click_in_reale(bmw[k[0]], k[1]) != v}
test("R16 i click del setup di Monza danno i valori delle fonti", not sbagliati, str(sbagliati))
test("R17 ripartizione di frenata: 0.3 per click (Race Element e simsource), non 0.2",
     click_in_reale(bmw["brake_bias"], 9) == 51.2)
test("R18 niente code di virgola mobile (20.3 + 0.1 × 57 = 26.0)",
     click_in_reale(bmw["tire_press_fl"], 57) == 26.0
     and repr(click_in_reale(bmw["toe_fl"], 7)) == "-0.13")

# ---------------------------------------------------------------------------
# 3. Un click che la regola non copre resta un click
# ---------------------------------------------------------------------------
test("R19 oltre l'ultimo valore di un elenco → None",
     click_in_reale(bmw["wheel_rate_front"], 6) is None
     and click_in_reale(bmw["wheel_rate_front"], 5) == 180000.0)
lineare_con_max = {"tipo": "lineare", "base": 0, "passo": 1, "click_max": 11}
test("R20 oltre click_max → None", click_in_reale(lineare_con_max, 12) is None
     and click_in_reale(lineare_con_max, 11) == 11)
test("R21 click_max null = nessun limite in alto noto (si converte)",
     click_in_reale(bmw["bump_fl"], 45) == 45.0)
test("R22 click negativo, decimale o booleano → None",
     click_in_reale(bmw["tc1"], -1) is None
     and click_in_reale(bmw["tc1"], 2.5) is None
     and click_in_reale(bmw["tc1"], True) is None)
test("R23 tipo di regola sconosciuto → None",
     click_in_reale({"tipo": "boh", "base": 0, "passo": 1}, 3) is None)

# ---------------------------------------------------------------------------
# 4. /api/setup-params non cambia (la pagina Setup si rifà nella #058)
# ---------------------------------------------------------------------------
test("R24 get_params_for_car restituisce i 49 generici, qualunque vettura",
     get_params_for_car("BMW M4 GT3", "Monza") == SETUP_SECTIONS
     and get_params_for_car() == SETUP_SECTIONS)
copia = get_params_for_car("x")
copia["tyres"]["params"]["tire_press_fl"]["min"] = -99
test("R25 …ed è una copia: modificarla non tocca SETUP_SECTIONS",
     SETUP_SECTIONS["tyres"]["params"]["tire_press_fl"]["min"] != -99)

# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
print()
print("═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if passed == total:
    print("✅ Tabella dei click in ordine")
else:
    print(f"❌ Test falliti ({total - passed}):")
    for name, ok in results:
        if not ok:
            print(f"   - {name}")
print("═" * 60)
sys.exit(0 if passed == total else 1)
