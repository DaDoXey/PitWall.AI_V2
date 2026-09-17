"""
test_demo.py — la sessione DEMO come bundle, e le rotte di L4 (fasi 1-2)

La demo non è più un file di numeri: è una sessione generata, analizzata dallo stesso
motore delle sessioni vere. Qui si inchioda:
* che sia **deterministica** (stessi numeri a ogni generazione);
* che racconti **la storia di sempre** (Monza, BMW M4 GT3, retrotreno scarico che
  cuoce la Post.DX, giro migliore al quarto) e che il motore la **dimostri**;
* che si **ricrei da sola** quando manca e che **non si possa cancellare**;
* le rotte nuove: elenco con la demo, tracce sulla distanza, sessione manuale
  (il percorso console), soglie di riferimento.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_demo.py
"""

import json
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
sys.path.insert(0, str(BACKEND))

from app.analisi import analizza  # noqa: E402
from app.bundle import demo  # noqa: E402
from app.bundle.schema import Fonte, Mescola  # noqa: E402

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
# 1 · La demo come sessione
# ---------------------------------------------------------------------------
print("\n─── La sessione demo ───")

bundle, canali, metadati = demo.costruisci()
report = analizza(bundle, canali)
bundle_2, canali_2, _ = demo.costruisci()
report_2 = analizza(bundle_2, canali_2)

test("D01 deterministica: stessi tempi sul giro a ogni generazione",
     [g.tempo_ms for g in bundle.giri] == [g.tempo_ms for g in bundle_2.giri])
test("D02 …e stesso verdetto",
     [v.titolo for v in report.verdetto] == [v.titolo for v in report_2.verdetto])
test("D03 la fonte dice DEMO", bundle.meta.fonte is Fonte.DEMO)
test("D04 Monza, BMW M4 GT3, prove, asciutto",
     (bundle.meta.track, bundle.meta.car, bundle.meta.tipo_sessione.value, bundle.meta.mescola)
     == ("monza", "bmw_m4_gt3", "FP", Mescola.ASCIUTTO))
test("D05 dichiara di essere sintetica",
     any("SESSIONE DEMO SINTETICA" in a for a in bundle.assunzioni))
test("D06 otto giri, tutti validi, tutti con tre settori",
     len(bundle.giri) == 8 and all(g.valido and len(g.splits_ms) == 3 for g in bundle.giri),
     f"{[(g.numero, g.splits_ms) for g in bundle.giri]}")
test("D07 il giro migliore è il quarto, a 1:47.8",
     report.ritmo.miglior_giro_numero == 4 and 107_800 <= report.ritmo.miglior_giro_ms <= 107_830,
     f"{report.ritmo.miglior_giro_numero} {report.ritmo.miglior_giro_ms}")
test("D08 il consumo è 3,2 l a giro", report.carburante.consumo_medio_l_giro == 3.2,
     f"{report.carburante}")
test("D09 il setup è un file vero di ACC con i 49 parametri",
     bundle.setup is not None and len(bundle.setup.valori) == 49)
test("D10 il racconto del pilota c'è", report.ha_racconto)
test("D11 sette curve riconosciute", len(report.curve["curve"]) == 7,
     f"{len(report.curve['curve'])}")

titoli = [v.titolo for v in report.verdetto]
test("D12 la storia: posteriori sotto la finestra di pressione",
     any("Post.SX, Post.DX sotto la finestra di pressione" in t for t in titoli), f"{titoli}")
test("D13 …la Post.DX sopra la finestra di temperatura al core",
     any(t.startswith("Post.DX sopra la finestra di temperatura") for t in titoli), f"{titoli}")
test("D14 …e il ritmo che cala dal giro migliore in poi",
     any("cala con lo stint" in t for t in titoli) and report.degrado.dal_giro == 4
     and report.degrado.significativo,
     f"{report.degrado}")
test("D15 nessuna voce positiva nel verdetto",
     not any(p.titolo in titoli for p in report.cosa_regge))
test("D16 la costanza non viene rivendicata mentre il ritmo cala",
     not any(p.titolo.startswith("Costanza") for p in report.cosa_regge),
     f"{[p.titolo for p in report.cosa_regge]}")
freni = report.gomme_e_freni["freni"]["temperatura_massima"]
test("D17 freni realistici: picchi sotto i 700 °C davanti e i 500 °C dietro",
     max(freni["FL"], freni["FR"]) < 700 and max(freni["RL"], freni["RR"]) < 500, f"{freni}")

# ---------------------------------------------------------------------------
# 2 · Le rotte
# ---------------------------------------------------------------------------
print("\n─── Rotte ───")

radice = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_demo_"))
os.environ["PITWALL_SESSIONS_DIR"] = str(radice)
try:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app as fastapi_app  # noqa: E402

    client = TestClient(fastapi_app, raise_server_exceptions=False)

    elenco = client.get("/api/sessions").json()
    voce = next((s for s in elenco["sessioni"] if s["id"] == demo.DEMO_ID), None)
    test("D18 la demo compare nell'elenco anche in un archivio vuoto",
         voce is not None and voce["demo"] is True and elenco["demo_id"] == demo.DEMO_ID,
         f"{elenco}")
    test("D19 …con canali, racconto, mescola e piattaforma PC",
         voce and voce["ha_canali"] and voce["ha_racconto"] and voce["mescola"] == "asciutto")

    analisi = client.get(f"/api/sessions/{demo.DEMO_ID}/analisi")
    test("D20 l'analisi della demo passa dalla stessa rotta delle altre",
         analisi.status_code == 200 and analisi.json()["ha_canali"] is True, analisi.text[:200])

    test("D21 la demo non si cancella",
         client.delete(f"/api/sessions/{demo.DEMO_ID}").status_code == 403)
    test("D22 …nemmeno la sua registrazione",
         client.delete(f"/api/telemetria/sessioni/{demo.DEMO_ID}").status_code == 403)

    (radice / "telemetria" / demo.DEMO_ID / "canali.npz").unlink()
    ricreata = client.get(f"/api/sessions/{demo.DEMO_ID}/analisi").json()
    test("D23 se i canali spariscono, la demo si ricrea da sola",
         ricreata["ha_canali"] is True)

    percorso = radice / "telemetria" / demo.DEMO_ID / "sessione.json"
    vecchia = json.loads(percorso.read_text(encoding="utf-8"))
    vecchia["versione_generatore"] = "0"
    percorso.write_text(json.dumps(vecchia), encoding="utf-8")
    client.get("/api/sessions")
    test("D24 una demo di un generatore vecchio si rigenera",
         json.loads(percorso.read_text(encoding="utf-8"))["versione_generatore"]
         == demo.VERSIONE_GENERATORE)

    tracce = client.get(f"/api/sessions/{demo.DEMO_ID}/tracce",
                        params={"giri": "4,8", "punti": 500})
    corpo = tracce.json()
    test("D25 tracce di due giri sulla stessa griglia",
         tracce.status_code == 200 and len(corpo["giri"]) == 2
         and len(corpo["posizione"]) == 500
         and len(corpo["giri"][0]["canali"]["physics.speedKmh"]) == 500, tracce.text[:200])
    test("D26 …con le posizioni anche in metri (tracciato stimato ~5,8 km)",
         corpo["metri"] is not None and 5700 < corpo["lunghezza_stimata_m"] < 5900,
         f"{corpo.get('lunghezza_stimata_m')}")
    test("D27 …e il giro 8 più lento del 4 alla Parabolica (velocità minima)",
         min(corpo["giri"][1]["canali"]["physics.speedKmh"][400:])
         < min(corpo["giri"][0]["canali"]["physics.speedKmh"][400:]))
    test("D28 un canale non ammesso è rifiutato",
         client.get(f"/api/sessions/{demo.DEMO_ID}/tracce",
                    params={"giri": "4", "canali": "physics.fuel"}).status_code == 400)
    test("D29 più di quattro giri sono rifiutati",
         client.get(f"/api/sessions/{demo.DEMO_ID}/tracce",
                    params={"giri": "1,2,3,4,5"}).status_code == 400)
    test("D30 un giro che non esiste dà 404",
         client.get(f"/api/sessions/{demo.DEMO_ID}/tracce",
                    params={"giri": "40"}).status_code == 404)

    # ── il percorso console ──
    manuale = client.post("/api/sessions/manuale", json={
        "piattaforma": "playstation", "car": "bmw_m4_gt3", "track": "monza",
        "mescola": "asciutto",
        "giri": [{"numero": 1, "tempo_ms": 109000}, {"numero": 2, "tempo_ms": 108400},
                 {"numero": 3, "tempo_ms": 108600}],
        "setup": {"tire_press_rl": 48, "tire_press_rr": 54},
        "racconto": {"andamento": "scivola dietro in uscita dalle lente",
                     "curve_critiche": ["Ascari"]},
    })
    id_manuale = manuale.json().get("id")
    test("D31 una sessione da console si crea con tempi, setup e racconto",
         manuale.status_code == 200 and id_manuale, manuale.text[:200])
    analisi_manuale = client.get(f"/api/sessions/{id_manuale}/analisi").json()
    test("D32 …e si analizza con lo stesso motore",
         analisi_manuale["giri_totali"] == 3 and analisi_manuale["ha_racconto"]
         and analisi_manuale["ha_setup"] and analisi_manuale["ritmo"]["miglior_giro_ms"] == 108400,
         f"{analisi_manuale.get('ritmo')}")
    riassunto = next(s for s in client.get("/api/sessions").json()["sessioni"]
                     if s["id"] == id_manuale)
    test("D33 nell'elenco dice da che piattaforma arriva",
         riassunto["piattaforma"] == "playstation" and riassunto["demo"] is False)
    test("D34 una sessione senza canali non ha tracce (409, non 500)",
         client.get(f"/api/sessions/{id_manuale}/tracce",
                    params={"giri": "1"}).status_code == 409)
    test("D35 una sessione manuale vuota è rifiutata",
         client.post("/api/sessions/manuale",
                     json={"piattaforma": "xbox"}).status_code == 400)
    test("D36 una piattaforma che non esiste è rifiutata",
         client.post("/api/sessions/manuale",
                     json={"piattaforma": "gameboy", "racconto": {"note": "x"}}).status_code == 422)

    rif = client.get("/api/riferimenti/fisica").json()
    test("D37 le soglie arrivano separate: Kunos e community",
         rif["ufficiali"]["voci"]["pressione_gomme_asciutto"]["min"] == 26.0
         and all(v["stato"] == "da_confermare" for v in rif["community"]["voci"].values()))

    # ── il tetto dell'archivio non tocca la demo ──
    from app.telemetria import registratore as reg  # noqa: E402

    altra = radice / "telemetria" / "20260916-120000-prova-aaaa"
    altra.mkdir()
    (altra / "canali.npz").write_bytes(b"0")
    (altra / "sessione.json").write_text("{}", encoding="utf-8")
    os.environ["PITWALL_TELEMETRIA_MAX_SESSIONI"] = "1"
    alleggerite = reg.applica_tetto(radice / "telemetria")
    test("D38 il tetto dell'archivio non toglie i canali alla demo",
         demo.DEMO_ID not in alleggerite
         and (radice / "telemetria" / demo.DEMO_ID / "canali.npz").exists(), f"{alleggerite}")
finally:
    os.environ.pop("PITWALL_SESSIONS_DIR", None)
    os.environ.pop("PITWALL_TELEMETRIA_MAX_SESSIONI", None)
    shutil.rmtree(radice, ignore_errors=True)

# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Demo e rotte di L4 allineate")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
