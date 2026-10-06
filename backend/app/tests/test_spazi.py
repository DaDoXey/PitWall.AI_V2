"""
test_spazi.py — uno spazio per ogni pilota, senza registrarsi (tabella di marcia, 2.2)

Due piloti usano lo stesso backend: nessuno dei due deve poter vedere, aprire, analizzare,
esportare, modificare o cancellare le sessioni dell'altro. La demo è di tutti e nessuno
la tocca. Uno spazio pieno lo dice, invece di accettare file all'infinito.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_spazi.py

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
ARCHIVIO = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_spazi_"))
os.environ["PITWALL_SESSIONS_DIR"] = str(ARCHIVIO)
os.environ["PITWALL_ALLOW_IMPORT"] = "1"
os.environ["PITWALL_ALLOW_RECORDER"] = "0"
os.environ["PITWALL_SPAZI"] = "1"
os.environ["PITWALL_SPAZIO_MAX_SESSIONI"] = "3"

import numpy as np  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import spazi  # noqa: E402
from app.bundle import demo  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.tests.motec_finto import CanaleFinto, scrivi_ld, scrivi_ldx  # noqa: E402

FIX = pathlib.Path(__file__).parent / "fixtures"

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


ANNA = {"X-PitWall-Spazio": "a" * 48}
BRUNO = {"X-PitWall-Spazio": "b" * 48}
CARLA = {"X-PitWall-Spazio": "c" * 48}

# Uno stint MoTeC finto, come in test_motec_bundle: 1 s di uscita, 3 giri da 60 s, 2 s di rientro.
NOME_LD = "monza-bmw_m4_gt3-5-2023.06.30-15.58.56.ld"


def _stint() -> tuple[bytes, bytes]:
    durata = 1.0 + 3 * 60.0 + 2.0

    def profilo(t):
        fase = ((t - 1.0) % 60.0) / 60.0
        v = np.full_like(t, 60.0)
        for centro in (0.2, 0.5, 0.8):
            v -= 35.0 * np.exp(-((fase - centro) / 0.03) ** 2)
        return v

    t60 = np.arange(int(durata * 60)) / 60
    t20 = np.arange(int(durata * 20)) / 20
    canali = [
        CanaleFinto("LAP_BEACON", "..", 100, np.zeros(int(durata * 100), np.float32)),
        CanaleFinto("SPEED", "m/s", 60, profilo(t60).astype(np.float32)),
        CanaleFinto("THROTTLE", "%", 60, np.full(t60.size, 80.0, np.float32)),
        CanaleFinto("BRAKE", "%", 60, np.where(profilo(t60) < 40, 100.0, 0.0).astype(np.float32)),
        CanaleFinto("STEERANGLE", "deg", 60, np.full(t60.size, -12.5, np.float32)),
        CanaleFinto("GEAR", "no", 20, np.where(profilo(t20) < 40, 2.0, 5.0).astype(np.float32)),
        CanaleFinto("TIME", "..", 50, (np.arange(int(durata * 50)) / 50 % 37).astype(np.float32)),
    ]
    return scrivi_ld(canali, vettura="M4 GT3", pista="monza"), scrivi_ldx([1.0 + k * 60.0 for k in range(4)])


LD, LDX = _stint()


def carica(chi: dict, nome_file: str = "acc_setup_gt3.json", rotta: str = "/api/sessions/import/setup",
           **campi):
    with open(FIX / nome_file, "rb") as f:
        return client.post(rotta, files={"file": (nome_file, f.read(), "application/json")},
                           data=campi, headers=chi)


def ids(chi: dict | None) -> list[str]:
    r = client.get("/api/sessions", headers=chi or {})
    return [s["id"] for s in r.json()["sessioni"]] if r.status_code == 200 else []


print("\n" + "═" * 60)
print("TEST — uno spazio per ogni pilota")
print("═" * 60 + "\n")

# Il `with` fa girare l'avvio dell'app: la demo si crea lì, come online.
with TestClient(fastapi_app) as client:
    # -----------------------------------------------------------------------
    # 1. Senza codice, e con un codice malfatto
    # -----------------------------------------------------------------------
    test("Z01 lo stato dice che gli spazi sono accesi", client.get("/").json().get("spazi") is True)
    r = client.get("/api/sessions")
    test("Z02 l'elenco senza codice risponde 400, non l'archivio di tutti",
         r.status_code == 400, f"{r.status_code} {r.text[:120]}")
    r = carica({})
    test("Z03 un import senza codice risponde 400", r.status_code == 400, f"{r.status_code} {r.text[:120]}")
    for cattivo, perche in (("corto", "troppo corto"), ("../" * 12, "con un percorso"),
                            ("a" * 65, "troppo lungo"), ("è" * 40, "con lettere accentate")):
        try:
            codice = client.get("/api/sessions", headers={"X-PitWall-Spazio": cattivo}).status_code
        except UnicodeEncodeError:
            codice = 400   # il client stesso rifiuta un'intestazione non ASCII
        test(f"Z04 un codice {perche} è rifiutato", codice == 400, str(codice))
    test("Z05 il catalogo, che non è di nessuno, risponde anche senza codice",
         client.get("/api/catalog").status_code == 200)

    # -----------------------------------------------------------------------
    # 2. Ognuno vede il suo, e la demo
    # -----------------------------------------------------------------------
    test("Z06 uno spazio nuovo contiene solo la demo", ids(ANNA) == [demo.DEMO_ID], str(ids(ANNA)))
    r = carica(ANNA, track="monza")
    test("Z07 Anna carica un setup", r.status_code == 200, r.text[:200])
    di_anna = r.json()["id"]
    test("Z08 Anna lo vede nel suo elenco, con la demo",
         set(ids(ANNA)) == {di_anna, demo.DEMO_ID}, str(ids(ANNA)))
    test("Z09 Bruno non lo vede: nel suo elenco c'è solo la demo",
         ids(BRUNO) == [demo.DEMO_ID], str(ids(BRUNO)))
    test("Z10 sul disco la sessione di Anna sta nella cartella del suo spazio",
         len(list((ARCHIVIO / "spazi").glob(f"*/{di_anna}.json"))) == 1
         and not (ARCHIVIO / f"{di_anna}.json").exists())
    test("Z11 il nome della cartella non è il codice",
         not any(ANNA["X-PitWall-Spazio"] in p.name for p in (ARCHIVIO / "spazi").iterdir()))

    # -----------------------------------------------------------------------
    # 3. Bruno conosce l'id di Anna: non gli serve a niente
    # -----------------------------------------------------------------------
    letture = [
        ("la sessione", "get", f"/api/sessions/{di_anna}", None),
        ("l'analisi", "get", f"/api/sessions/{di_anna}/analisi", None),
        ("il debrief", "get", f"/api/sessions/{di_anna}/debrief", None),
        ("il confronto", "get", f"/api/sessions/{di_anna}/confronto", None),
        ("le tracce", "get", f"/api/sessions/{di_anna}/tracce?giri=1,2", None),
        ("l'export MoTeC", "get", f"/api/sessions/{di_anna}/export/motec", None),
        ("l'export del setup", "post", f"/api/sessions/{di_anna}/export/setup", {"click": {}}),
        ("i tagli del debrief", "put", f"/api/sessions/{di_anna}/debrief/tagli", {"tagli": None}),
        ("la chat", "post", f"/api/sessions/{di_anna}/chat", {"messages": [{"role": "user", "content": "Dove perdo?"}]}),
        ("l'analisi di Gigi", "post", "/api/analysis", {"session_id": di_anna, "prompt": "analisi"}),
    ]
    for cosa, metodo, rotta, corpo in letture:
        r = client.request(metodo, rotta, json=corpo, headers=BRUNO)
        # 404 «non trovata» (o 503 dove il modello è spento): mai i dati, mai un 200.
        test(f"Z12 Bruno non raggiunge {cosa} di Anna", r.status_code in (404, 503),
             f"{r.status_code} {r.text[:120]}")
        test(f"Z13 e la risposta su {cosa} non nomina la vettura di Anna",
             "ferrari" not in r.text.lower() and "wing" not in r.text.lower(), r.text[:120])
    r = client.delete(f"/api/sessions/{di_anna}", headers=BRUNO)
    test("Z14 Bruno non può cancellare la sessione di Anna", r.status_code == 404, f"{r.status_code}")
    test("Z15 e infatti è ancora lì", client.get(f"/api/sessions/{di_anna}", headers=ANNA).status_code == 200)
    r = client.get(f"/api/sessions/{di_anna}", headers=ANNA)
    test("Z16 Anna invece la apre", r.status_code == 200 and r.json().get("meta", r.json()).get("track", "monza"))

    # -----------------------------------------------------------------------
    # 4. La demo è di tutti e nessuno la tocca
    # -----------------------------------------------------------------------
    for nome, chi in (("Anna", ANNA), ("Bruno", BRUNO)):
        test(f"Z17 {nome} apre la demo", client.get(f"/api/sessions/{demo.DEMO_ID}", headers=chi).status_code == 200)
        test(f"Z18 {nome} ne ha l'analisi",
             client.get(f"/api/sessions/{demo.DEMO_ID}/analisi", headers=chi).status_code == 200)
        r = client.get(f"/api/sessions/{demo.DEMO_ID}/tracce?giri=1,2", headers=chi)
        test(f"Z19 {nome} ne ha le tracce (i canali stanno nell'archivio comune)",
             r.status_code == 200, f"{r.status_code} {r.text[:120]}")
        r = client.get(f"/api/telemetria/sessioni/{demo.DEMO_ID}/canali?nomi=physics.speedKmh&ogni=500",
                       headers=chi)
        test(f"Z19b {nome} legge i canali della registrazione demo", r.status_code == 200,
             f"{r.status_code} {r.text[:120]}")
        test(f"Z20 {nome} non la può cancellare",
             client.delete(f"/api/sessions/{demo.DEMO_ID}", headers=chi).status_code == 403)
        r = client.put(f"/api/sessions/{demo.DEMO_ID}/debrief/tagli", json={"tagli": None}, headers=chi)
        test(f"Z21 {nome} non ne può cambiare i tagli", r.status_code == 403, f"{r.status_code} {r.text[:120]}")
    test("Z22 la demo sta nell'archivio comune, una volta sola",
         (ARCHIVIO / f"{demo.DEMO_ID}.json").exists()
         and not list((ARCHIVIO / "spazi").glob(f"*/{demo.DEMO_ID}.json")))

    # -----------------------------------------------------------------------
    # 5. Limiti dello spazio
    # -----------------------------------------------------------------------
    carica(ANNA, track="monza")
    r = carica(ANNA, track="monza")
    test("Z23 Anna arriva a tre sessioni (il tetto di questa prova)", r.status_code == 200
         and len(ids(ANNA)) == 4, f"{r.status_code} {len(ids(ANNA))}")
    r = carica(ANNA, track="monza")
    test("Z24 la quarta è rifiutata con 409", r.status_code == 409, f"{r.status_code} {r.text[:160]}")
    test("Z25 e il messaggio dice cosa fare", "cancellane una" in r.text, r.text[:160])
    test("Z26 lo spazio pieno di Anna non ferma Bruno", carica(BRUNO, track="monza").status_code == 200)
    test("Z27 Anna ne cancella una", client.delete(f"/api/sessions/{di_anna}", headers=ANNA).status_code == 200)
    test("Z28 e ora può caricarne un'altra", carica(ANNA, track="monza").status_code == 200)
    test("Z29 la demo non conta nel tetto: Bruno ne ha una sua più la demo", len(ids(BRUNO)) == 2)

    os.environ["PITWALL_SPAZIO_MAX_FILE_MB"] = "0"
    r = carica(BRUNO, track="monza")
    test("Z30 un file oltre il tetto dello spazio è rifiutato con 413", r.status_code == 413,
         f"{r.status_code} {r.text[:120]}")
    os.environ["PITWALL_SPAZIO_MAX_FILE_MB"] = "60"

    # -----------------------------------------------------------------------
    # 5b. Un file MoTeC: i canali vanno su disco a parte, e devono stare nello spazio
    # -----------------------------------------------------------------------
    r = client.post("/api/sessions/import/motec",
                    files={"ld": (NOME_LD, LD, "application/octet-stream"),
                           "ldx": (NOME_LD + "x", LDX, "application/xml")}, headers=CARLA)
    test("Z40 Carla carica uno stint MoTeC", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
    di_carla = r.json().get("id", "") if r.status_code == 200 else ""
    canali_carla = list((ARCHIVIO / "spazi").glob("*/telemetria/*/canali.npz"))
    test("Z41 i canali stanno nella cartella dello spazio di Carla, non in quella comune",
         len(canali_carla) == 1
         and [p.name for p in (ARCHIVIO / "telemetria").iterdir()] == [demo.DEMO_ID],
         f"{canali_carla} | comune: {[p.name for p in (ARCHIVIO / 'telemetria').iterdir()]}")
    r = client.get(f"/api/sessions/{di_carla}/tracce?giri=2,3", headers=CARLA)
    test("Z42 Carla legge le tracce dei suoi giri", r.status_code == 200, f"{r.status_code} {r.text[:160]}")
    r = client.get(f"/api/sessions/{di_carla}/tracce?giri=2,3", headers=BRUNO)
    test("Z43 Bruno no", r.status_code == 404, f"{r.status_code} {r.text[:160]}")
    registrazione = canali_carla[0].parent.name if canali_carla else "x"
    r = client.get(f"/api/telemetria/sessioni/{registrazione}/canali?nomi=physics.speedKmh&ogni=500",
                   headers=BRUNO)
    test("Z44 e nemmeno passando dalla rotta dei canali, con l'id della registrazione",
         r.status_code == 404, f"{r.status_code} {r.text[:160]}")
    test("Z45 Carla cancella la sessione e i canali se ne vanno con lei",
         client.delete(f"/api/sessions/{di_carla}", headers=CARLA).status_code == 200
         and not list((ARCHIVIO / "spazi").glob("*/telemetria/*/canali.npz")))

    # -----------------------------------------------------------------------
    # 6. Lo stesso codice da un altro browser ritrova lo spazio
    # -----------------------------------------------------------------------
    altrove = {"X-PitWall-Spazio": ANNA["X-PitWall-Spazio"], "User-Agent": "un altro browser"}
    test("Z31 con il codice di Anna, da un altro browser, si ritrovano le sue sessioni",
         ids(altrove) == ids(ANNA) and len(ids(altrove)) == 4)

    # -----------------------------------------------------------------------
    # 7. Spazi spenti: tutto come prima
    # -----------------------------------------------------------------------
    os.environ["PITWALL_SPAZI"] = "0"
    test("Z32 a spazi spenti lo stato lo dice", client.get("/").json().get("spazi") is False)
    r = client.get("/api/sessions")
    test("Z33 a spazi spenti l'elenco risponde senza codice, dall'archivio comune",
         r.status_code == 200 and [s["id"] for s in r.json()["sessioni"]] == [demo.DEMO_ID], r.text[:160])
    r = carica({}, track="monza")
    test("Z34 e un import senza codice finisce nell'archivio comune",
         r.status_code == 200 and (ARCHIVIO / f"{r.json()['id']}.json").exists(), r.text[:160])
    test("Z35 un codice mandato a spazi spenti è ignorato, non un errore",
         client.get("/api/sessions", headers={"X-PitWall-Spazio": "corto"}).status_code == 200)
    os.environ["PITWALL_SPAZI"] = "1"

test("Z36 fuori da una richiesta non resta nessuno spazio impostato", spazi.corrente() is None)

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
    print("✅ Gli spazi tengono separati i piloti")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
