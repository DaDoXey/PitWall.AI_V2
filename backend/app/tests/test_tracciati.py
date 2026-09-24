"""
test_tracciati.py — il catalogo dei circuiti con guida e mappa (sezione Tracciati)

Quel che si prova qui è la promessa fatta al pilota nella pagina Tracciati:

* la lista dei 25 circuiti dice, per ognuno, se ha una **guida** e se il suo
  **layout è stato verificato** — sono le due bandierine su cui la UI decide
  cosa mostrare;
* `mappa_verificata` è vero SOLO per i layout guardati a occhio nei provini
  (cinque il 07/09/2026, quattro il 23/09/2026), e per quelli il file esiste
  davvero a disco
  (una bandierina verde su un file mancante sarebbe peggio del file mancante);
* nessun layout non verificato è rimasto in `public/assets/tracks/`: la regola
  è «meglio nessuna mappa che una sbagliata», e finché il file sta lì prima o
  poi qualcuno lo mostra;
* la guida si serve sulla sua rotta, con 404 pulito per i circuiti che non ce
  l'hanno ancora (17 su 25), e ha la forma che la pagina si aspetta;
* le regole di contenuto già decise valgono per le guide a disco: numerazione
  senza buchi, nomi di curva mai inventati (assente = null, mai stringa vuota)
  e consigli di mestiere che dichiarano la propria confidence.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_tracciati.py
"""

import json
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402

from app.core import catalog as cat  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

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


REPO = BACKEND.parent
MAPPE_DIR = REPO / "frontend" / "public" / "assets" / "tracks"
GUIDE_DIR = BACKEND / "app" / "core" / "data" / "tracks_knowledge"

# I layout scelti a occhio nei provini: cinque il 07/09/2026 (blocco 1), quattro
# il 23/09/2026 (blocco 2), quattro il 24/09/2026 (blocco 3). Se un provino ne
# approva altri, questa lista cresce INSIEME a tracks.json: il test esiste proprio
# per non far divergere le due cose.
VERIFICATE_ATTESE = {"spa_francorchamps", "imola", "zandvoort", "zolder", "kyalami",
                     "monza", "silverstone", "nurburgring_gp", "barcelona_catalunya",
                     "misano", "brands_hatch", "hungaroring", "paul_ricard"}

print("\n" + "=" * 60)
print("CATALOGO DEI TRACCIATI — lista, bandierine, mappe")
print("=" * 60)

r = client.get("/api/catalog")
test("GET /api/catalog risponde 200", r.status_code == 200, f"status {r.status_code}")
indice = r.json()
tracks = indice.get("tracks", [])
test("la lista ha tutti e 25 i circuiti ACC", len(tracks) == 25, f"{len(tracks)}")

test(
    "ogni voce porta le due bandierine",
    all("ha_guida" in t and "mappa_verificata" in t for t in tracks),
    "manca ha_guida/mappa_verificata su qualche voce",
)

verificate = {t["id"] for t in tracks if t.get("mappa_verificata")}
test(
    "mappa_verificata solo per i layout approvati nei provini",
    verificate == VERIFICATE_ATTESE,
    f"attese {sorted(VERIFICATE_ATTESE)}, trovate {sorted(verificate)}",
)

mancanti = [tid for tid in verificate if not list(MAPPE_DIR.glob(f"{tid}_map.*"))]
test(
    "per ogni mappa verificata il file esiste a disco",
    not mancanti,
    f"bandierina verde ma file assente: {mancanti}",
)

a_disco = {p.name.rsplit("_map.", 1)[0] for p in MAPPE_DIR.glob("*_map.*")}
test(
    "nessun layout NON verificato è rimasto nel repo",
    a_disco <= VERIFICATE_ATTESE,
    f"da togliere: {sorted(a_disco - VERIFICATE_ATTESE)}",
)

manifest_path = REPO / "frontend" / "public" / "assets" / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
mappe_manifest = {k for k, v in manifest.get("tracks", {}).items() if "map" in v}
test(
    "il manifest indicizza esattamente le mappe verificate",
    mappe_manifest == VERIFICATE_ATTESE,
    f"manifest: {sorted(mappe_manifest)}",
)

print("\n" + "=" * 60)
print("SCHEDA DEL SINGOLO CIRCUITO")
print("=" * 60)

# Nordschleife: nessuna guida e nessun layout verificato — il caso «scheda
# onesta e basta», che deve restare servibile come tutti gli altri. E' il
# circuito parcheggiato per ultimo nell'ordine delle guide, quindi resta
# senza guida piu' a lungo di tutti (prima era Silverstone, che dal blocco 2
# la guida ce l'ha).
r = client.get("/api/catalog/track/nurburgring_nordschleife")
test("GET /api/catalog/track/nurburgring_nordschleife risponde 200", r.status_code == 200, f"status {r.status_code}")
nords = r.json() if r.status_code == 200 else {}
test(
    "la scheda porta le bandierine e il nome breve",
    nords.get("short_name") == "Nordschleife"
    and nords.get("ha_guida") is False
    and nords.get("mappa_verificata") is False,
    f"short_name={nords.get('short_name')} ha_guida={nords.get('ha_guida')} "
    f"mappa={nords.get('mappa_verificata')}",
)

# Kyalami: layout verificato (blocco 1), guida ancora no. Le due bandierine
# sono indipendenti e la scheda deve saperlo dire. (Fino al 23/09 il caso era
# rovesciato su Monza, guida si' e layout no: col provino del blocco 2 anche
# Monza ha la mappa.)
r = client.get("/api/catalog/track/kyalami")
kyalami = r.json() if r.status_code == 200 else {}
test(
    "Kyalami ha il layout verificato ma non ancora la guida",
    kyalami.get("ha_guida") is False and kyalami.get("mappa_verificata") is True,
    f"ha_guida={kyalami.get('ha_guida')} mappa={kyalami.get('mappa_verificata')}",
)

r = client.get("/api/catalog/track/Spa-Francorchamps")
test(
    "la scheda si risolve anche dal nome di display",
    r.status_code == 200 and r.json().get("id") == "spa_francorchamps",
    f"status {r.status_code}",
)
spa = r.json() if r.status_code == 200 else {}
test(
    "Spa ha guida e layout verificato",
    spa.get("ha_guida") is True and spa.get("mappa_verificata") is True,
    f"{spa.get('ha_guida')} / {spa.get('mappa_verificata')}",
)

print("\n" + "=" * 60)
print("LA GUIDA DEL TRACCIATO")
print("=" * 60)

guide_a_disco = {p.stem for p in GUIDE_DIR.glob("*.json")}
test(
    "le guide a disco sono quelle dichiarate dal catalogo",
    guide_a_disco == {t["id"] for t in tracks if t.get("ha_guida")},
    f"disco {sorted(guide_a_disco)}",
)

r = client.get("/api/catalog/track/zolder/guida")
test("GET .../zolder/guida risponde 200", r.status_code == 200, f"status {r.status_code}")
guida = r.json() if r.status_code == 200 else {}
test("la guida è quella del circuito chiesto", guida.get("id") == "zolder", f"{guida.get('id')}")
test(
    "la guida ha settori e curve, non un guscio vuoto",
    isinstance(guida.get("settori"), list)
    and isinstance(guida.get("curve"), list)
    and len(guida.get("curve") or []) > 0,
    f"settori={len(guida.get('settori') or [])} curve={len(guida.get('curve') or [])}",
)

r = client.get("/api/catalog/track/nurburgring_nordschleife/guida")
test(
    "un circuito senza guida dà 404, non un finto contenuto",
    r.status_code == 404,
    f"status {r.status_code}",
)

r = client.get("/api/catalog/track/circuito_che_non_esiste/guida")
test("un circuito fuori catalogo dà 404", r.status_code == 404, f"status {r.status_code}")

print("\n" + "=" * 60)
print("REGOLE DI CONTENUTO DELLE GUIDE (valgono per tutte quelle a disco)")
print("=" * 60)

for tid in sorted(guide_a_disco):
    g = cat.track_guide(tid)
    curve = (g or {}).get("curve") or []
    test(f"{tid}: la guida si carica e ha curve", bool(curve), "nessuna curva")

    numerate = [c.get("n") for c in curve]
    test(
        f"{tid}: le curve sono numerate senza buchi né doppioni",
        numerate == list(range(1, len(curve) + 1)),
        f"{numerate}",
    )

    nomi_vuoti = [c.get("n") for c in curve if c.get("nome") == ""]
    test(
        f"{tid}: nessun nome di curva inventato (assente = null, mai stringa vuota)",
        not nomi_vuoti,
        f"curve con nome vuoto: {nomi_vuoti}",
    )

    senza_conf = [
        c.get("n") for c in curve if c.get("origine") == "mestiere" and not c.get("confidence")
    ]
    test(
        f"{tid}: i consigli di mestiere dichiarano la loro confidence",
        not senza_conf,
        f"curve senza confidence: {senza_conf}",
    )

passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "=" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Catalogo dei tracciati e guide conformi")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("=" * 60)
sys.exit(1 if failed else 0)
