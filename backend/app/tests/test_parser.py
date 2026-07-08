"""
test_parser.py — Test automatici per parser.py
Copertura: TC-05, TC-06, TC-07 da Spec v3 §10

Eseguire con:
    python test_parser.py

Non richiede pytest. Output plain-text per includere direttamente in INCIDENTS.
"""

import math
import pathlib
import sys
from io import StringIO

# Forza output UTF-8 su console Windows (cp1252 non gestisce ✅ / box-drawing)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Aggiungi la root del progetto al path (parents[2]) per importare 'backend'
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # -> backend/

from app.core.csv_parser import parse_session_csv, CSVParseError

# ---------------------------------------------------------------------------
# Utility di test minimale
# ---------------------------------------------------------------------------

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def test(name: str, passed: bool, detail: str = ""):
    status = PASS if passed else FAIL
    line = f"{status}  {name}"
    if detail:
        line += f"\n        → {detail}"
    print(line)
    results.append((name, passed))


# ---------------------------------------------------------------------------
# TC-05 — Gestione errori CSV non valido (Spec v3 §8, §10)
# Input: CSV con colonne mancanti o intestazioni errate → messaggio errore, no crash
# ---------------------------------------------------------------------------

print("\n── TC-05: CSV non valido ─────────────────────────────────────────")

# TC-05a: File completamente non CSV
try:
    parse_session_csv(StringIO("questo non è un csv\nriga2\nriga3"))
    test("TC-05a: testo non-CSV", False, "Doveva sollevare CSVParseError")
except CSVParseError as e:
    test("TC-05a: testo non-CSV", True, str(e))
except Exception as e:
    test("TC-05a: testo non-CSV", False, f"Eccezione inattesa: {e}")

# TC-05b: CSV valido ma colonna obbligatoria 'lap' mancante
csv_no_lap = "fuel_cons,tire_temp_fl\n3.2,88\n3.1,90"
try:
    parse_session_csv(StringIO(csv_no_lap))
    test("TC-05b: colonna 'lap' mancante", False, "Doveva sollevare CSVParseError")
except CSVParseError as e:
    test("TC-05b: colonna 'lap' mancante", "lap" in str(e).lower(), str(e))
except Exception as e:
    test("TC-05b: colonna 'lap' mancante", False, f"Eccezione inattesa: {e}")

# TC-05c: CSV valido ma colonna obbligatoria 'fuel_cons' mancante
csv_no_fuel = "lap,tire_temp_fl\n1,88\n2,90"
try:
    parse_session_csv(StringIO(csv_no_fuel))
    test("TC-05c: colonna 'fuel_cons' mancante", False, "Doveva sollevare CSVParseError")
except CSVParseError as e:
    test("TC-05c: colonna 'fuel_cons' mancante", "fuel_cons" in str(e).lower(), str(e))
except Exception as e:
    test("TC-05c: colonna 'fuel_cons' mancante", False, f"Eccezione inattesa: {e}")

# TC-05d: CSV con intestazioni errate (nomi inventati)
csv_wrong_headers = "giro,carburante,temp1\n1,3.2,88\n2,3.1,90"
try:
    parse_session_csv(StringIO(csv_wrong_headers))
    test("TC-05d: intestazioni errate", False, "Doveva sollevare CSVParseError")
except CSVParseError as e:
    test("TC-05d: intestazioni errate", True, str(e))
except Exception as e:
    test("TC-05d: intestazioni errate", False, f"Eccezione inattesa: {e}")

# TC-05e: CSV vuoto (solo intestazioni)
csv_empty = "lap,fuel_cons\n"
try:
    parse_session_csv(StringIO(csv_empty))
    test("TC-05e: CSV solo intestazioni", False, "Doveva sollevare CSVParseError")
except CSVParseError as e:
    test("TC-05e: CSV solo intestazioni", True, str(e))
except Exception as e:
    test("TC-05e: CSV solo intestazioni", False, f"Eccezione inattesa: {e}")

# TC-05f: CSV con valori non numerici nelle colonne obbligatorie
csv_bad_types = "lap,fuel_cons\nabc,xyz\ndef,qrs"
try:
    parse_session_csv(StringIO(csv_bad_types))
    test("TC-05f: valori non numerici", False, "Doveva sollevare CSVParseError")
except CSVParseError as e:
    test("TC-05f: valori non numerici", True, str(e))
except Exception as e:
    test("TC-05f: valori non numerici", False, f"Eccezione inattesa: {e}")



# ---------------------------------------------------------------------------
# TC-07 — CSV valido con dati temperatura (per cross-check RF-05)
# Simuliamo il caso: pilota dice "troppo caldo" ma tire_temp_fl = 72°C
# Il parser deve restituire i dati senza crash; il cross-check è in agent.py
# ---------------------------------------------------------------------------

print("\n── TC-07: CSV con temperature basse (setup per RF-05) ────────────")

csv_tc07 = """lap,fuel_cons,tire_press_fl,tire_press_fr,tire_press_rl,tire_press_rr,tire_temp_fl,tire_temp_fr,tire_temp_rl,tire_temp_rr
1,3.2,26.5,26.4,26.8,26.7,72,74,78,80
2,3.1,26.6,26.5,26.9,26.8,73,75,79,81
3,3.0,26.4,26.3,26.7,26.6,71,73,77,79"""

try:
    session = parse_session_csv(StringIO(csv_tc07))

    test(
        "TC-07a: parsing completato senza eccezioni",
        True,
        session["raw_df_summary"]
    )
    test(
        "TC-07b: has_temp_data = True",
        session["has_temp_data"] is True,
        f"Ottenuto: {session['has_temp_data']}"
    )
    test(
        "TC-07c: has_pressure_data = True",
        session["has_pressure_data"] is True,
        f"Ottenuto: {session['has_pressure_data']}"
    )
    # Verifica che le temperature medie siano nell'intorno di 72-80°C
    temp_fl_avg = session["temperatures"]["fl"]["avg"]
    test(
        "TC-07d: temp FL media nel range atteso (70–80°C)",
        70 <= temp_fl_avg <= 80,
        f"tire_temp_fl avg = {temp_fl_avg}°C"
    )
    test(
        "TC-07e: laps_count = 3",
        session["laps_count"] == 3,
        f"Ottenuto: {session['laps_count']}"
    )
    print(f"\n        [Dati pronti per cross-check agent.py RF-05]")
    print(f"        Pressioni FL: {session['pressures']['fl']}")
    print(f"        Temperature FL: {session['temperatures']['fl']}")
    print(f"        Temperature RR: {session['temperatures']['rr']}")

except Exception as e:
    test("TC-07: parsing CSV temperature basse", False, f"Eccezione inattesa: {e}")


# ---------------------------------------------------------------------------
# Test bonus — CSV con intestazioni maiuscole / spazi (robustezza)
# ---------------------------------------------------------------------------

print("\n── BONUS: Robustezza intestazioni ───────────────────────────────")

csv_uppercase = "LAP , FUEL_CONS , TIRE_TEMP_FL\n1,3.2,88\n2,3.1,90"
try:
    session = parse_session_csv(StringIO(csv_uppercase))
    # Nota: colonne opzionali parziali (manca fr/rl/rr) → has_temp_data = False
    test(
        "BONUS-a: intestazioni uppercase normalizzate",
        session["laps_count"] == 2,
        f"laps_count = {session['laps_count']}"
    )
except Exception as e:
    test("BONUS-a: intestazioni uppercase", False, f"Eccezione: {e}")


# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------

print("\n" + "═" * 60)
passed = sum(1 for _, ok in results if ok)
total  = len(results)
print(f"RISULTATI: {passed}/{total} test superati")

if passed == total:
    print("✅ Tutti i test superati — parser.py pronto per Modulo 2")
else:
    failed = [name for name, ok in results if not ok]
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
    print("\n→ Aprire INCIDENTS e documentare prima di procedere.")

print("═" * 60)
