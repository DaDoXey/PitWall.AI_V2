"""
test_gigi.py — Gigi sul report del motore (L4, fase 5 lato backend)

* il **contesto** che riceve il modello contiene i numeri del report, il setup, il
  racconto e la domanda — e resta **compatto** (poche centinaia di token);
* la **risposta dal motore** (live spento, sessione non demo) ha le 5 sezioni e cita
  solo ciò che il report dice;
* `/api/analysis` sceglie la fonte giusta: cache per la demo, motore per le altre
  sessioni, mai la storia di Monza su una sessione che non è Monza;
* le **risposte in cache** della demo hanno le 5 sezioni e numeri coerenti con il
  report della demo.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_gigi.py
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
sys.path.insert(0, str(BACKEND))

from app.analisi import analizza  # noqa: E402
from app.analisi.gigi import contesto, risposta_dal_motore  # noqa: E402
from app.bundle import demo  # noqa: E402
from app.bundle.schema import Fonte, Giro, Meta, Racconto, SessionBundle  # noqa: E402
from app.core import agent, demo_responses  # noqa: E402

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []
SEZIONI = agent.REQUIRED_SECTIONS


def test(name: str, passed: bool, detail: str = ""):
    status = PASS if passed else FAIL
    line = f"{status}  {name}"
    if detail and not passed:
        line += f"\n        → {detail}"
    print(line)
    results.append((name, passed))


def cinque_sezioni(testo: str) -> bool:
    posizioni = [testo.find(s) for s in SEZIONI]
    return all(p >= 0 for p in posizioni) and posizioni == sorted(posizioni)


# ---------------------------------------------------------------------------
print("\n─── Contratto ───")
test("G01 il contratto di Gigi ha 5 sezioni, con la Correzione di Guida",
     len(SEZIONI) == 5 and "## Correzione di Guida" in SEZIONI)
test("G02 il prompt v5 le chiede tutte e 5, nell'ordine",
     cinque_sezioni(agent.load_system_prompt()))
test("G03 il prompt cita la fonte Kunos e non parla più di CSV",
     "Kunos" in agent.load_system_prompt() and "CSV" not in agent.load_system_prompt())

# ---------------------------------------------------------------------------
print("\n─── Contesto per il modello ───")
bundle, canali, _ = demo.costruisci()
report = analizza(bundle, canali)
testo = contesto(report, bundle, "perché scivola dietro?", "Profilo pilota: amatore")
test("G04 il contesto porta il verdetto con prove e azioni",
     "[REPORT DEL MOTORE]" in testo and report.verdetto[0].titolo in testo
     and "prova:" in testo and "azione:" in testo)
test("G05 …il setup, il racconto, il profilo e la domanda",
     "[SETUP]" in testo and "[RACCONTO]" in testo and "[PROFILO PILOTA]" in testo
     and "perché scivola dietro?" in testo)
test("G06 …le finestre Kunos misurate",
     "finestra Kunos pressione 26.0-27.0 psi" in testo, testo[:600])
test("G07 resta compatto: sotto i 2000 token stimati",
     agent.estimate_tokens(testo) < 2000, f"~{agent.estimate_tokens(testo)} token")
test("G08 nessun canale grezzo nel contesto",
     "physics." not in testo and "graphics." not in testo)

# ---------------------------------------------------------------------------
print("\n─── Risposta dal motore ───")
dal_motore = risposta_dal_motore(report, bundle, "perché scivola dietro?")
test("G09 la risposta dal motore ha le 5 sezioni, in ordine", cinque_sezioni(dal_motore),
     dal_motore[:300])
test("G10 apre con la prima voce del verdetto", report.verdetto[0].titolo in dal_motore)
test("G11 dichiara di non venire da un modello", "senza modello linguistico" in dal_motore)

console = SessionBundle(
    meta=Meta(fonte=Fonte.MANUALE, piattaforma="playstation", car="ferrari_296_gt3",
              track="spa"),
    giri=[Giro(numero=i + 1, tempo_ms=t) for i, t in enumerate([139000, 138200, 138900])],
    racconto=Racconto(andamento="sottosterzo all'Eau Rouge", curve_critiche=["Eau Rouge"]),
)
report_console = analizza(console)
risposta_console = risposta_dal_motore(report_console, console)
test("G12 sessione da console: 5 sezioni anche senza telemetria",
     cinque_sezioni(risposta_console), risposta_console[:300])
test("G13 …dice che senza telemetria la causa meccanica non si dimostra",
     "Senza la telemetria" in risposta_console)
test("G14 …e riporta il racconto del pilota", "Eau Rouge" in risposta_console)
test("G15 …e non parla di Monza", "Monza" not in risposta_console)

# ---------------------------------------------------------------------------
print("\n─── Cache della demo ───")
for nome in ("DEMO_RESPONSE", "DEMO_UNDERSTEER", "DEMO_FUEL", "DEMO_TYRES", "DEMO_BRAKES"):
    test(f"G16 {nome}: 5 sezioni in ordine", cinque_sezioni(getattr(demo_responses, nome)))
tutte = "".join(getattr(demo_responses, n) for n in
                ("DEMO_RESPONSE", "DEMO_UNDERSTEER", "DEMO_FUEL", "DEMO_TYRES", "DEMO_BRAKES"))
test("G17 niente più limite a 95 °C né valori di setup inventati",
     "95°C" not in tutte and "58.0%" not in tutte and "60 → 75" not in tutte)
gomme = report.gomme_e_freni["gomme"]
test("G18 le medie di pressione posteriore della cache sono quelle del report",
     f"{gomme['pressione_media']['RL']:.1f} / {gomme['pressione_media']['RR']:.1f} psi"
     in demo_responses.DEMO_RESPONSE,
     f"{gomme['pressione_media']}")
quota = gomme["finestra_temperatura"]["sopra_pct"]["RR"]
test("G19 la quota della Post.DX oltre i 100 °C è quella del report",
     f"{quota:.0f}% del tempo" in demo_responses.DEMO_TYRES, f"{quota}")
test("G20 il calo dal giro 4 è quello del report",
     f"{report.degrado.pendenza_ms_giro:.0f} ms a giro" in demo_responses.DEMO_RESPONSE,
     f"{report.degrado.pendenza_ms_giro}")
suggerite = next(v.parametri for v in report.verdetto if v.parametri
                 and "pressione" in v.titolo)
test("G20b le correzioni di pressione della cache sono quelle suggerite dal motore",
     f"+{suggerite['tire_press_rl']} psi su Post.SX e +{suggerite['tire_press_rr']} psi su Post.DX"
     in demo_responses.DEMO_RESPONSE, f"{suggerite}")
freni = report.gomme_e_freni["freni"]["temperatura_massima"]
test("G21 le massime dei freni della cache sono quelle del report",
     f"{max(freni['FL'], freni['FR']):.0f} °C davanti e {max(freni['RL'], freni['RR']):.0f} °C dietro"
     in demo_responses.DEMO_BRAKES, f"{freni}")

# ---------------------------------------------------------------------------
print("\n─── /api/analysis sceglie la fonte ───")
radice = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_gigi_"))
salvati = {k: os.environ.get(k) for k in ("PITWALL_SESSIONS_DIR", "PITWALL_ALLOW_LIVE",
                                          "PITWALL_DEMO_MODE")}
os.environ["PITWALL_SESSIONS_DIR"] = str(radice)
os.environ["PITWALL_ALLOW_LIVE"] = "0"
os.environ["PITWALL_DEMO_MODE"] = "1"
try:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app as fastapi_app  # noqa: E402

    client = TestClient(fastapi_app, raise_server_exceptions=False)
    r = client.post("/api/analysis", json={"prompt": "gomme"}).json()
    test("G22 senza sessione si parla della demo, dalla cache",
         r["source"] == "demo" and r["text"] == demo_responses.DEMO_TYRES)
    r = client.post("/api/analysis", json={"prompt": "gomme", "session_id": demo.DEMO_ID}).json()
    test("G23 con la demo esplicita, stessa cosa", r["source"] == "demo")

    creata = client.post("/api/sessions/manuale", json={
        "piattaforma": "playstation", "car": "ferrari_296_gt3", "track": "spa",
        "giri": [{"numero": 1, "tempo_ms": 139000}, {"numero": 2, "tempo_ms": 138200}],
        "racconto": {"andamento": "sottosterzo all'Eau Rouge"},
    }).json()
    r = client.post("/api/analysis", json={"prompt": "gomme",
                                           "session_id": creata["id"]}).json()
    test("G24 su una sessione non demo, con il live spento, risponde il motore",
         r["source"] == "motore" and cinque_sezioni(r["text"]), str(r)[:200])
    test("G25 …e non racconta la storia di Monza",
         "Monza" not in r["text"] and "Post.DX" not in r["text"])
    test("G26 il contratto della risposta non cambia",
         set(r) == {"question", "text", "source"})
    test("G27 una sessione che non esiste dà 404",
         client.post("/api/analysis", json={
             "prompt": "x", "session_id": "20260101-000000-niente-0000"}).status_code == 404)
finally:
    for chiave, valore in salvati.items():
        if valore is None:
            os.environ.pop(chiave, None)
        else:
            os.environ[chiave] = valore
    shutil.rmtree(radice, ignore_errors=True)

# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Gigi allineato al report del motore")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
