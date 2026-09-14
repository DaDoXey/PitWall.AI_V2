"""
test_sessions.py — archivio dei bundle e rotte di import (L1 · Fase 4, Entry #032)

Controlla che una sessione importata si possa rileggere identica, che l'archivio non
si faccia raggirare da un id che arriva dalla rete, e che le rotte dicano cosa è
andato storto invece di rispondere 500.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_sessions.py

Non richiede pytest, né rete, né chiave: scrive in una cartella temporanea.
"""

import os
import pathlib
import shutil
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))  # -> backend/

# L'archivio va dirottato PRIMA di importare l'app: mai scrivere in backend/sessions/.
ARCHIVIO = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_sessioni_"))
os.environ["PITWALL_SESSIONS_DIR"] = str(ARCHIVIO)
os.environ["PITWALL_ALLOW_IMPORT"] = "1"

from fastapi.testclient import TestClient  # noqa: E402

from app.bundle import store  # noqa: E402
from app.bundle.adapters import leggi_results_acc, leggi_setup_acc  # noqa: E402
from app.bundle.schema import Fonte, Meta, SessionBundle  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

FIX = pathlib.Path(__file__).parent / "fixtures"
client = TestClient(fastapi_app)

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


def carica(nome_file: str, rotta: str, **campi):
    with open(FIX / nome_file, "rb") as f:
        return client.post(rotta, files={"file": (nome_file, f.read(), "application/json")},
                           data=campi)


print("\n" + "═" * 60)
print("TEST — archivio delle sessioni e rotte di import")
print("═" * 60 + "\n")

# ---------------------------------------------------------------------------
# 1. Archivio
# ---------------------------------------------------------------------------
setup = leggi_setup_acc(FIX / "acc_setup_gt3.json")
bundle_setup = SessionBundle(
    meta=Meta(fonte=Fonte.ACC_SETUP, car=setup.car, track="monza"), setup=setup)
id_setup = store.salva(bundle_setup)

test("S01 l'id dice data, pista e vettura a colpo d'occhio",
     "monza_bmw_m4_gt3" in id_setup and id_setup[:8].isdigit(), id_setup)
test("S02 il file finisce nella cartella indicata dall'ambiente",
     (ARCHIVIO / f"{id_setup}.json").is_file())

riletto = store.leggi(id_setup)
test("S03 il bundle riletto è identico a quello salvato",
     riletto.model_dump() == bundle_setup.model_dump())
test("S04 e il setup grezzo di ACC è ancora dentro",
     riletto.setup.raw["carName"] == "bmw_m4_gt3")

bundle_giri = leggi_results_acc(FIX / "acc_results_gioco_prove.json", track="monza")
id_giri = store.salva(bundle_giri)

r = store.riassunto(id_giri)
test("S05 il riassunto conta i giri e quelli validi", (r.giri, r.giri_validi) == (4, 4),
     f"{r.giri}/{r.giri_validi}")
test("S06 il riassunto riporta il miglior giro", r.miglior_giro_ms == 103134, str(r.miglior_giro_ms))
test("S07 il riassunto dice quante assunzioni ci sono", r.assunzioni == len(bundle_giri.assunzioni))
test("S08 il riassunto di un setup conta i parametri, non i giri",
     store.riassunto(id_setup).parametri_setup == 49)

elenco = store.elenca()
test("S09 l'elenco contiene entrambe le sessioni", len(elenco) == 2, str(len(elenco)))
test("S10 le sessioni sono ordinate dalla più recente",
     elenco[0].id >= elenco[1].id)
test("S11 il limite dell'elenco è rispettato", len(store.elenca(limite=1)) == 1)

# Un file rovinato non deve far sparire la lista
(ARCHIVIO / "20260101-000000-rotto-aaaa.json").write_text("{ questo non e' json",
                                                          encoding="utf-8")
test("S12 un file rovinato viene saltato, non fa saltare l'elenco",
     len(store.elenca()) == 2, str(len(store.elenca())))

for cattivo in ["../../../.env", "..", "con/slash", "MAIUSCOLE-000000-x-aaaa", "", "a" * 300]:
    if store.ID_VALIDO.match(cattivo):
        test(f"S13 id rifiutato: {cattivo!r}", False, "la regex lo ha accettato")
        break
else:
    test("S13 gli id storti (traversal compreso) non passano la validazione", True)

try:
    store.leggi("../../../.env")
    esito = "nessun errore"
except store.ArchivioError as e:
    esito = str(e)
test("S14 leggere un id di traversal alza ArchivioError", "non valido" in esito, esito)

try:
    store.leggi("20260101-000000-inesistente-bbbb")
    esito = "nessun errore"
except store.SessioneNonTrovata as e:
    esito = str(e)
test("S15 una sessione inesistente è distinta da un id storto", "non trovata" in esito, esito)

test("S16 nessun file temporaneo resta a terra dopo il salvataggio",
     not list(ARCHIVIO.glob("*.tmp")))

# ---------------------------------------------------------------------------
# 2. Rotte di import
# ---------------------------------------------------------------------------
resp = carica("acc_setup_gt3.json", "/api/sessions/import/setup", track="monza")
test("S17 POST import/setup risponde 200", resp.status_code == 200, resp.text[:200])
dati = resp.json() if resp.status_code == 200 else {}
test("S18 restituisce l'id della sessione creata", bool(dati.get("id")))
test("S19 dice quanti parametri ha letto e quanti in unità reali",
     (dati.get("parametri"), dati.get("parametri_in_unita_reali")) == (49, 4),
     str((dati.get("parametri"), dati.get("parametri_in_unita_reali"))))
test("S20 restituisce le assunzioni, invece di tacerle",
     len(dati.get("assunzioni", [])) == 3, str(dati.get("assunzioni")))
test("S21 il riassunto arriva già pronto per la lista",
     dati.get("riassunto", {}).get("track") == "monza")

resp = carica("acc_results_gioco_prove.json", "/api/sessions/import/results", track="monza")
test("S22 POST import/results con una sola vettura risponde 200",
     resp.status_code == 200, resp.text[:200])
test("S23 e conta i giri importati",
     resp.json().get("riassunto", {}).get("giri") == 4 if resp.status_code == 200 else False)

resp = carica("acc_results_gioco_gara.json", "/api/sessions/import/results")
test("S24 con più vetture risponde 409 invece di sceglierne una",
     resp.status_code == 409, f"{resp.status_code}: {resp.text[:150]}")
dettaglio = resp.json().get("detail", {}) if resp.status_code == 409 else {}
test("S25 il 409 porta con sé l'elenco dei partecipanti",
     len(dettaglio.get("partecipanti", [])) == 3, str(dettaglio)[:200])
test("S26 con pilota e numero, così il frontend può far scegliere",
     dettaglio.get("partecipanti", [{}])[0].get("pilota") == "Rob Rossi",
     str(dettaglio.get("partecipanti", [{}])[0]))

resp = carica("acc_results_gioco_gara.json", "/api/sessions/import/results", car_id=3)
test("S27 indicando car_id l'import va a buon fine",
     resp.status_code == 200 and resp.json()["riassunto"]["giri"] == 2,
     resp.text[:200])

resp = carica("acc_setup_gt3.json", "/api/sessions/import/results")
test("S28 un setup passato all'import dei risultati dà 400, non 500",
     resp.status_code == 400, f"{resp.status_code}: {resp.text[:150]}")

resp = carica("setup_rotto.json", "/api/sessions/import/setup")
test("S29 un file troncato dà 400 con il motivo",
     resp.status_code == 400 and "JSON" in resp.text, f"{resp.status_code}: {resp.text[:150]}")

resp = client.post("/api/sessions/import/setup",
                   files={"file": ("vuoto.json", b"", "application/json")})
test("S30 un file vuoto dà 400", resp.status_code == 400, f"{resp.status_code}")

resp = client.post("/api/sessions/import/setup",
                   files={"file": ("enorme.json", b"x" * (21 * 1024 * 1024), "application/json")})
test("S31 un file oltre il tetto dà 413, senza finire su disco",
     resp.status_code == 413, f"{resp.status_code}")

# ---------------------------------------------------------------------------
# 3. Consultazione
# ---------------------------------------------------------------------------
resp = client.get("/api/sessions")
test("S32 GET /api/sessions elenca le sessioni",
     resp.status_code == 200 and len(resp.json()["sessioni"]) >= 5,
     f"{resp.status_code}: {len(resp.json().get('sessioni', []))}")

primo = resp.json()["sessioni"][0]["id"]
resp = client.get(f"/api/sessions/{primo}")
test("S33 GET /api/sessions/{id} restituisce il bundle intero",
     resp.status_code == 200 and "schema_version" in resp.json(), resp.text[:150])

resp = client.get("/api/sessions/20260101-000000-inesistente-cccc")
test("S34 una sessione inesistente dà 404", resp.status_code == 404, str(resp.status_code))

resp = client.get("/api/sessions/id-storto")
test("S35 un id storto dà 400, non 404 e non 500", resp.status_code == 400, str(resp.status_code))

resp = client.delete(f"/api/sessions/{primo}")
test("S36 DELETE rimuove la sessione", resp.status_code == 200, resp.text[:150])
test("S37 e dopo non c'è più", client.get(f"/api/sessions/{primo}").status_code == 404)
test("S38 cancellarla due volte dà 404",
     client.delete(f"/api/sessions/{primo}").status_code == 404)

# ---------------------------------------------------------------------------
# 3b. Analisi della sessione (L2)
# ---------------------------------------------------------------------------
resp = carica("acc_results_gioco_prove.json", "/api/sessions/import/results", track="monza")
id_analisi = resp.json()["id"]

resp = client.get(f"/api/sessions/{id_analisi}/analisi")
test("S33b GET /api/sessions/{id}/analisi risponde 200", resp.status_code == 200,
     resp.text[:200])
rep = resp.json() if resp.status_code == 200 else {}
test("S33c il report porta il miglior giro della sessione",
     rep.get("ritmo", {}).get("miglior_giro_ms") == 103134,
     str(rep.get("ritmo")))
test("S33d e il verdetto con le sue voci", isinstance(rep.get("verdetto"), list))
test("S33e e dichiara i dati che non ha", len(rep.get("dati_mancanti", [])) >= 2,
     str(rep.get("dati_mancanti"))[:150])

test("S33f l'analisi di una sessione inesistente dà 404",
     client.get("/api/sessions/20260101-000000-inesistente-dddd/analisi").status_code == 404)
test("S33g e quella di un id storto dà 400",
     client.get("/api/sessions/storto/analisi").status_code == 400)

# ---------------------------------------------------------------------------
# 4. Interruttore dell'import (per il deploy vetrina)
# ---------------------------------------------------------------------------
os.environ["PITWALL_ALLOW_IMPORT"] = "0"
resp = carica("acc_setup_gt3.json", "/api/sessions/import/setup")
test("S39 con PITWALL_ALLOW_IMPORT=0 l'import risponde 503",
     resp.status_code == 503, f"{resp.status_code}: {resp.text[:120]}")
test("S40 ma la consultazione resta aperta", client.get("/api/sessions").status_code == 200)
os.environ["PITWALL_ALLOW_IMPORT"] = "1"

# ---------------------------------------------------------------------------
# 5. Le rotte di prima non si sono rotte
# ---------------------------------------------------------------------------
test("S41 GET /api/session (demo) risponde ancora", client.get("/api/session").status_code == 200)
test("S42 GET /api/setup-params risponde ancora", client.get("/api/setup-params").status_code == 200)
test("S43 GET /api/catalog risponde ancora", client.get("/api/catalog").status_code == 200)
test("S44 la rotta CSV eliminata resta 404", client.post("/api/csv/parse").status_code == 404)

shutil.rmtree(ARCHIVIO, ignore_errors=True)

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Archivio e rotte conformi")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
