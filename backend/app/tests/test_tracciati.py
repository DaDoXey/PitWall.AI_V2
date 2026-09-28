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
                     "misano", "brands_hatch", "hungaroring", "paul_ricard",
                     "red_bull_ring"}

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

print("\n" + "=" * 60)
print("ANCORE DELLE CURVE — il file e il suo validatore")
print("=" * 60)

# Un file di ancore conforme, costruito sulla guida e sulla mappa vere di Monza:
# ogni variante qui sotto rompe UNA regola e deve essere respinta.
import copy  # noqa: E402

import numpy as np  # noqa: E402

from app.analisi import eventi_curva as ev  # noqa: E402
from app.analisi.curve import FRENO, GAS, POSIZIONE, TEMPO, VELOCITA  # noqa: E402
from app.core import ancore  # noqa: E402

guida_monza = cat.track_guide("monza")
mappa_monza = next(t for t in cat.all_tracks() if t["id"] == "monza")["assets"]["map"]
buone = {
    "id": "monza", "schema": ancore.SCHEMA, "sessione_origine": "sessione-di-prova",
    "vettura": "bmw_m4_gt3", "giro": 1, "tempo_giro_ms": 106190,
    "mappa_commons": mappa_monza["commons_file"], "creato_il": "2026-09-28",
    "ancore": [{"n": c["n"], "nome": c["nome"],
                "inizio": round(0.05 + 0.08 * i, 4), "metodo_inizio": "frenata",
                "apice": round(0.07 + 0.08 * i, 4), "metodo_apice": "minimo",
                "uscita": round(0.09 + 0.08 * i, 4), "metodo_uscita": "carico",
                "g_lat": None, "mappa": {"x": 0.5, "y": 0.5}}
               for i, c in enumerate(guida_monza["curve"])],
}


def respinte(modifica) -> list[str]:
    dati = copy.deepcopy(buone)
    modifica(dati)
    return ancore.valida_ancore(dati, guida_monza, mappa_monza, atteso_id="monza")


def _sposta(d, i, inizio):
    # sposta una curva intera, fasi comprese
    a = d["ancore"][i]
    a["inizio"] = inizio
    a["apice"] = round((inizio + 0.02) % 1, 4)
    a["uscita"] = round((inizio + 0.04) % 1, 4)


test("un file di ancore conforme passa il validatore",
     ancore.valida_ancore(buone, guida_monza, mappa_monza, atteso_id="monza") == [],
     f"{ancore.valida_ancore(buone, guida_monza, mappa_monza, atteso_id='monza')}")
test("manca un'ancora: respinto (ne serve una per curva della guida)",
     bool(respinte(lambda d: d["ancore"].pop())))
test("due curve fuori ordine lungo il giro: respinto",
     bool(respinte(lambda d: _sposta(d, 3, 0.01))))


def _t1_prima_del_traguardo(d):
    # la T1 prima della linea: gli inizi fanno UN salto all'indietro, ed e' lecito
    for i in range(len(d["ancore"])):
        _sposta(d, i, round((0.95 + 0.08 * i) % 1.0, 4))


def _apice_prima(d):
    a = d["ancore"][2]
    a["apice"] = round(a["inizio"] - 0.01, 4)


def _uscita_prima(d):
    a = d["ancore"][2]
    a["uscita"] = round(a["apice"] - 0.005, 4)


test("un solo salto all'indietro (T1 prima del traguardo) è ammesso",
     respinte(_t1_prima_del_traguardo) == [], f"{respinte(_t1_prima_del_traguardo)}")
test("due salti all'indietro: respinto",
     bool(respinte(lambda d: (_t1_prima_del_traguardo(d), _sposta(d, 6, 0.0)))))
test("apice prima dell'inizio: respinto (le fasi vanno in fila)", bool(respinte(_apice_prima)))
test("uscita prima dell'apice: respinto", bool(respinte(_uscita_prima)))
test("punto sulla mappa fuori dall'immagine: respinto",
     bool(respinte(lambda d: d["ancore"][0].update(mappa={"x": 1.2, "y": 0.5}))))
test("punto sulla mappa mancante: respinto",
     bool(respinte(lambda d: d["ancore"][0].update(mappa=None))))
test("ancore prese su un'altra mappa: respinto (i punti vanno rifatti)",
     bool(respinte(lambda d: d.update(mappa_commons="Monza 1995.svg"))))
test("nome di curva diverso dalla guida: respinto (guida rinumerata)",
     bool(respinte(lambda d: d["ancore"][2].update(nome="Curva inventata"))))
test("inizio fuori da [0, 1): respinto",
     bool(respinte(lambda d: d["ancore"][0].update(inizio=1.0))))
test("metodo sconosciuto: respinto",
     bool(respinte(lambda d: d["ancore"][0].update(metodo_inizio="a occhio"))))
test("il file vecchio (schema 1, una sola posizione) è respinto",
     bool(respinte(lambda d: d.update(schema=1))))

for f in sorted(ancore.ANCORE_DIR.glob("*.json")) if ancore.ANCORE_DIR.exists() else []:
    mappa = next((t for t in cat.all_tracks() if t["id"] == f.stem), {}).get("assets", {}).get("map")
    errori = ancore.valida_ancore(json.loads(f.read_text(encoding="utf-8")),
                                  cat.track_guide(f.stem), mappa, atteso_id=f.stem)
    test(f"{f.stem}: le ancore a disco sono conformi", errori == [], f"{errori}")

print("\n" + "=" * 60)
print("ANCORE DELLE CURVE — le curve del giro e la proposta")
print("=" * 60)


def giro_sintetico(spostamento: float = 0.0, giri: int = 3, campioni: int = 6000,
                   tocco: bool = False) -> dict:
    """Tre giri uguali: un tornante a destra (0,20) con la staccata prima, un curvone a
    destra in pieno (0,45), una chicane sinistra-destra (0,70) con la staccata prima.
    G_LAT < 0 = destra, come in ACC. Con `tocco` c'è anche un colpetto di freno a metà
    rettilineo (0,12) che non toglie velocità."""
    x = (np.arange(campioni * giri) / campioni) % 1.0

    def gauss(centro: float, largo: float) -> np.ndarray:
        d = (x - centro - spostamento + 0.5) % 1.0 - 0.5
        return np.exp(-(d / largo) ** 2)

    v = 250 - 170 * gauss(0.20, 0.012) - 160 * gauss(0.70, 0.010) - 5 * gauss(0.45, 0.02)
    g = (-1.8 * gauss(0.20, 0.010) - 2.0 * gauss(0.45, 0.020)
         + 1.5 * gauss(0.694, 0.004) - 1.5 * gauss(0.708, 0.004))
    freno = ((gauss(0.185, 0.008) > 0.5) | (gauss(0.685, 0.008) > 0.5)).astype(float)
    if tocco:
        freno = np.maximum(freno, (gauss(0.12, 0.002) > 0.5).astype(float) * 0.3)
    dt = (5000 / campioni) / (v / 3.6)
    return {POSIZIONE: x, VELOCITA: v, ev.G_LAT: g, FRENO: freno, GAS: 1 - freno,
            TEMPO: np.cumsum(dt) * 1000}


canali = giro_sintetico()
prof = ev.profilo(canali, ev.giro_migliore(canali))
eventi = ev.trova_eventi(prof)
vicino = lambda pos: [e for e in eventi if abs(e.apice - pos) < 0.004]  # noqa: E731
riassunto = [(round(e.inizio, 4), e.metodo_inizio, round(e.apice, 4), e.direzione) for e in eventi]

# la staccata del tornante comincia dove il freno supera la soglia: 0,185 - 0,0067
test("il tornante: l'inizio è il punto di frenata, prima dell'apice",
     any(e.direzione == "destra" and e.frenata is not None and 0.176 <= e.inizio <= 0.181
         and e.metodo_apice == "minimo" for e in vicino(0.20)), f"{riassunto}")
test("il curvone in pieno: nessuna frenata, l'inizio è l'inserimento",
     any(e.direzione == "destra" and e.frenata is None and e.metodo_inizio == "inserimento"
         and e.inizio < e.apice for e in vicino(0.45)), f"{riassunto}")
chicane = sorted((e for e in eventi if 0.69 <= e.apice <= 0.71), key=lambda e: e.apice)
test("la chicane sono due curve di senso opposto",
     {e.direzione for e in chicane} >= {"destra", "sinistra"}, f"{riassunto}")
test("la staccata della chicane va alla sua prima parte, non alla seconda",
     [e.frenata is not None for e in chicane][:2] == [True, False], f"{riassunto}")
test("inizio ≤ apice ≤ uscita per ogni curva",
     all((e.apice - e.inizio) % 1 <= 0.25 and (e.uscita - e.apice) % 1 <= 0.25 for e in eventi),
     f"{[(e.inizio, e.apice, e.uscita) for e in eventi]}")

con_tocco = giro_sintetico(tocco=True)
eventi_tocco = ev.trova_eventi(ev.profilo(con_tocco, ev.giro_migliore(con_tocco)))
t_tocco = [e for e in eventi_tocco if abs(e.apice - 0.20) < 0.004]
test("un tocco di freno a metà rettilineo non diventa la staccata del tornante",
     bool(t_tocco) and 0.176 <= t_tocco[0].inizio <= 0.181,
     f"{[(e.inizio, e.apice) for e in t_tocco]}")

guida_sint = [{"n": 1, "nome": None, "direzione": "destra", "tipo": "lenta"},
              {"n": 2, "nome": None, "direzione": "destra", "tipo": "veloce"},
              {"n": 3, "nome": None, "direzione": "sinistra", "tipo": "lenta"},
              {"n": 4, "nome": None, "direzione": "destra", "tipo": "lenta"}]
proposta = ev.proponi(guida_sint, eventi)
test("la proposta abbina in ordine tutte e quattro le curve, senza avvisi",
     [p["inizio"] is not None and not p["avviso"] for p in proposta] == [True] * 4
     and [p["inizio"] for p in proposta] == sorted(p["inizio"] for p in proposta),
     f"{proposta}")
guida_sbagliata = copy.deepcopy(guida_sint)
guida_sbagliata[0]["direzione"] = "sinistra"
test("un senso sbagliato nella guida porta un avviso, non passa in silenzio",
     bool(ev.proponi(guida_sbagliata, eventi)[0]["avviso"]),
     f"{ev.proponi(guida_sbagliata, eventi)[0]}")

ancore_sint = [{"n": p["n"], "nome": None, "apice": p["apice"],
                "direzione": g["direzione"]} for p, g in zip(proposta, guida_sint)]
for spostamento, attese in ((0.002, True), (0.02, False)):
    altro = giro_sintetico(spostamento)
    esiti = ev.verifica(ancore_sint, prof, ev.profilo(altro, ev.giro_migliore(altro)))
    reggono = all(e["punto_ok"] and e["tratto_ok"] for e in esiti)
    test(f"verifica su un'altra sessione spostata di {spostamento:.1%} di giro: "
         f"{'reggono' if attese else 'non reggono'}",
         reggono == attese, f"{esiti}")

print("\n" + "=" * 60)
print("SENSI DELLE CURVE VERIFICATI (28/09/2026)")
print("=" * 60)

# Fissati con fonti scritte, mappa numerata e accelerazione laterale in ACC: a
# Zandvoort la guida ne aveva sei ribaltati (T5, T9, T10, T11, T12, T13), e la T13 era
# stata «corretta» il 18/09 nel verso sbagliato. Questo test esiste perché non succeda
# di nuovo in silenzio. La T1 di Imola è una leggera piega a destra (verificata in gioco).
SENSI_ZANDVOORT = ["destra", "destra", "sinistra", "destra", "sinistra", "destra", "destra",
                   "destra", "destra", "sinistra", "destra", "sinistra", "destra", "destra"]
sensi = [c.get("direzione") for c in (cat.track_guide("zandvoort") or {}).get("curve", [])]
test("zandvoort: i 14 sensi sono quelli verificati", sensi == SENSI_ZANDVOORT, f"{sensi}")
imola_t1 = ((cat.track_guide("imola") or {}).get("curve") or [{}])[0].get("direzione")
test("imola: la T1 è una piega a destra", imola_t1 == "destra", f"{imola_t1}")

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
