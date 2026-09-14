"""
test_bundle.py — il formato canonico «session bundle» (L1 · Fase 1, Entry #032)

Controlla che il contenitore faccia il suo unico mestiere: accettare ciò che ACC
scrive davvero, rifiutare ciò che non ha senso, e non perdere mai il dato grezzo.
In particolare la regola della decisione 7: un valore in unità reali esiste solo
se la conversione è dichiarata verificata, altrimenti si resta in click.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_bundle.py

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

from pydantic import ValidationError  # noqa: E402

from app.bundle import (  # noqa: E402
    SCHEMA_VERSION,
    BundleVersionError,
    Canali,
    Condizioni,
    Evento,
    Fonte,
    Giro,
    Meta,
    SessionBundle,
    Setup,
    TipoEvento,
    TipoSessione,
    ValoreSetup,
)

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


def alza(fn) -> str | None:
    """Esegue fn e restituisce il messaggio d'errore, o None se non ha alzato nulla."""
    try:
        fn()
    except (ValidationError, ValueError) as e:
        return str(e)
    return None


def bundle_minimo(**kw) -> SessionBundle:
    return SessionBundle(meta=Meta(fonte=Fonte.ACC_RESULTS, **kw))


print("\n" + "═" * 60)
print("TEST — session bundle (formato canonico)")
print("═" * 60 + "\n")

# ---------------------------------------------------------------------------
# 1. Versione del formato
# ---------------------------------------------------------------------------
b = bundle_minimo()
test("B01 il bundle nasce con la versione corrente", b.schema_version == SCHEMA_VERSION,
     f"trovato {b.schema_version}")

test("B02 un bundle vuoto è valido ma dichiara di non dire nulla",
     b.ha_dati_utili() is False)

riletto = SessionBundle.from_json(b.to_json())
test("B03 andata e ritorno in JSON senza perdite", riletto.model_dump() == b.model_dump())

msg = alza(lambda: SessionBundle.from_json(json.dumps({"schema_version": "9.0", "meta": {"fonte": "demo"}})))
test("B04 una versione maggiore diversa viene rifiutata con un messaggio chiaro",
     msg is not None and "9.0" in msg and SCHEMA_VERSION in msg, msg or "nessun errore")

msg = alza(lambda: SessionBundle.from_json(json.dumps({"meta": {"fonte": "demo"}})))
test("B05 un bundle senza versione viene rifiutato", msg is not None, "nessun errore")

try:
    SessionBundle.from_json(json.dumps({"schema_version": "1.7", "meta": {"fonte": "demo"}}))
    minore_ok = True
except BundleVersionError:
    minore_ok = False
test("B06 una versione minore più alta resta leggibile (1.7 con codice 1.0)", minore_ok)

# ---------------------------------------------------------------------------
# 2. Campi a sorpresa e slug
# ---------------------------------------------------------------------------
msg = alza(lambda: SessionBundle.model_validate(
    {"schema_version": SCHEMA_VERSION, "meta": {"fonte": "demo"}, "colpo_di_scena": 1}))
test("B07 un campo non previsto è un errore, non un silenzio",
     msg is not None and "colpo_di_scena" in msg, msg or "nessun errore")

m = Meta(fonte=Fonte.ACC_SETUP, car="  BMW_M4_GT3 ", track="Monza")
test("B08 gli slug di auto e pista sono normalizzati minuscoli e senza spazi",
     (m.car, m.track) == ("bmw_m4_gt3", "monza"), f"{m.car} / {m.track}")

test("B09 senza tipo sessione il bundle lo dichiara sconosciuto, non lo inventa",
     m.tipo_sessione is TipoSessione.SCONOSCIUTO)

msg = alza(lambda: Meta(fonte="telepatia"))
test("B10 una fonte inventata viene rifiutata", msg is not None, "nessun errore")

# ---------------------------------------------------------------------------
# 3. Giri — i tempi sono millisecondi, come li scrive ACC
# ---------------------------------------------------------------------------
g = Giro(numero=1, tempo_ms=105300, splits_ms=[25569, 39186, 35358],
         carburante_residuo_l=81.02)
test("B11 un giro reale di ACC (ms + 3 split + carburante residuo) è accettato",
     g.tempo_ms == 105300 and len(g.splits_ms) == 3)

test("B12 un giro è valido salvo prova contraria", g.valido is True)

msg = alza(lambda: Giro(numero=1, tempo_ms=0))
test("B13 un tempo sul giro nullo o negativo viene rifiutato", msg is not None)

msg = alza(lambda: Giro(numero=0))
test("B14 la numerazione dei giri parte da 1", msg is not None)

msg = alza(lambda: Giro(numero=1, splits_ms=[1000, 2000, 3000, 4000]))
test("B15 più di 3 split vengono rifiutati (ACC ne scrive 3)", msg is not None)

msg = alza(lambda: Giro(numero=1, splits_ms=[1000, -5, 3000]))
test("B16 uno split non positivo viene rifiutato", msg is not None)

msg = alza(lambda: SessionBundle(meta=Meta(fonte=Fonte.ACC_RESULTS),
                                 giri=[Giro(numero=2), Giro(numero=2)]))
test("B17 due giri con lo stesso numero vengono rifiutati",
     msg is not None and "stesso numero" in msg, msg or "nessun errore")

b = SessionBundle(meta=Meta(fonte=Fonte.ACC_RESULTS), giri=[
    Giro(numero=1, tempo_ms=110000),
    Giro(numero=2, tempo_ms=105300),
    Giro(numero=3, tempo_ms=104900, valido=False),   # taglio di pista
    Giro(numero=4),                                   # giro senza tempo (out lap)
])
test("B18 giri_validi tiene solo i giri validi e cronometrati", len(b.giri_validi) == 2,
     f"{len(b.giri_validi)}")
test("B19 un bundle con giri dichiara di avere dati utili", b.ha_dati_utili() is True)

# ---------------------------------------------------------------------------
# 4. Setup — la regola del dato grezzo (decisione 7 del 14/09)
# ---------------------------------------------------------------------------
v = ValoreSetup(raw=54)
test("B20 un valore di setup non convertito resta in click, senza valore reale",
     v.unita == "click" and v.reale is None and v.verificato is False)

msg = alza(lambda: ValoreSetup(raw=54, reale=25.7, unita="psi"))
test("B21 un valore in unità reali senza verifica viene rifiutato",
     msg is not None and "verificato" in msg, msg or "nessun errore")

msg = alza(lambda: ValoreSetup(raw=54, reale=25.7, verificato=True))
test("B22 verificato=True con unità 'click' viene rifiutato", msg is not None)

v = ValoreSetup(raw=54, reale=25.7, unita="psi", verificato=True)
test("B23 un valore convertito e verificato conserva comunque il grezzo",
     v.raw == 54 and v.reale == 25.7 and v.unita == "psi")

v = ValoreSetup(raw=[-4.2328, -4.2288, -1.8972, -1.8932])
test("B24 un parametro per ruota (camber) è accettato come lista", len(v.raw) == 4)

raw_acc = {"carName": "bmw_m4_gt3", "basicSetup": {"tyres": {"tyrePressure": [54, 61, 48, 54]}}}
s = Setup(car="bmw_m4_gt3", nome="Q2", raw=raw_acc, valori={
    "tyre_press_fl": ValoreSetup(raw=54, reale=25.7, unita="psi", verificato=True),
    "tyre_press_fr": ValoreSetup(raw=61, reale=26.4, unita="psi", verificato=True),
    "rear_wing": ValoreSetup(raw=1),
})
test("B25 il JSON originale di ACC resta intatto dentro il bundle",
     s.raw["basicSetup"]["tyres"]["tyrePressure"] == [54, 61, 48, 54])
test("B26 il setup sa dire quanti parametri sono in unità reali", s.quanti_verificati() == (2, 3),
     str(s.quanti_verificati()))
test("B27 un bundle con il solo setup ha già dati utili",
     SessionBundle(meta=Meta(fonte=Fonte.ACC_SETUP), setup=s).ha_dati_utili() is True)

# ---------------------------------------------------------------------------
# 5. Condizioni, eventi, canali
# ---------------------------------------------------------------------------
c = Condizioni(temp_aria_c=21.0, temp_pista_c=31.5, grip_linea_ideale=0.98, pista_bagnata=False)
test("B28 le condizioni reali di ACC (grip 0.98) sono accettate", c.grip_linea_ideale == 0.98)

msg = alza(lambda: Condizioni(grip_linea_ideale=1.4))
test("B29 un grip fuori da 0–1 viene rifiutato", msg is not None)

test("B30 le condizioni assenti restano vuote, non a zero",
     Condizioni().temp_aria_c is None)

e = Evento(tipo=TipoEvento.PIT, giro=12, nota="cambio gomme")
test("B31 un evento di pit è accettato", e.tipo is TipoEvento.PIT and e.giro == 12)

ch = Canali(frequenza_hz=50, nomi=["speed_kmh", "brake", "gas"], file="canali/001.parquet",
            indicizzati_su_distanza=True, campioni=180000)
test("B32 il riferimento ai canali (L3) descrive frequenza, nomi e file",
     ch.frequenza_hz == 50 and ch.indicizzati_su_distanza is True)

msg = alza(lambda: Canali(frequenza_hz=0, nomi=["speed_kmh"], file="x"))
test("B33 una frequenza nulla viene rifiutata", msg is not None)

msg = alza(lambda: Canali(frequenza_hz=50, nomi=[], file="x"))
test("B34 canali senza alcun nome vengono rifiutati", msg is not None)

# ---------------------------------------------------------------------------
# 6. Un bundle completo sopravvive al salvataggio
# ---------------------------------------------------------------------------
completo = SessionBundle(
    meta=Meta(fonte=Fonte.ACC_RESULTS, car="bmw_m4_gt3", track="monza",
              tipo_sessione=TipoSessione.QUALIFICA, pilota="Edoardo",
              durata_s=2400, condizioni=c),
    giri=[Giro(numero=1, tempo_ms=110000, splits_ms=[26000, 40000, 44000],
               carburante_residuo_l=81.0),
          Giro(numero=2, tempo_ms=105300, splits_ms=[25569, 39186, 35358],
               carburante_residuo_l=77.4, carburante_usato_l=3.6)],
    setup=s, eventi=[e], canali=ch,
)
riletto = SessionBundle.from_json(completo.to_json())
test("B35 un bundle completo torna identico dopo salvataggio e rilettura",
     riletto.model_dump() == completo.model_dump())
test("B36 dopo la rilettura il setup grezzo è ancora lì",
     riletto.setup.raw["carName"] == "bmw_m4_gt3")
test("B37 dopo la rilettura i tempi restano interi in millisecondi",
     riletto.giri[1].tempo_ms == 105300 and isinstance(riletto.giri[1].tempo_ms, int))

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Formato canonico conforme")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
