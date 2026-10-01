"""
test_chat.py — la chat dal vivo di Gigi (Entry #061)

Controlla la rotta POST /api/sessions/{id}/chat: l'interruttore PITWALL_CHAT_LIVE, la
chiave, il tetto di spesa della categoria "chat", i limiti della conversazione (12
domande, 8 messaggi al modello), il contesto che arriva al modello (report, setup,
debrief, fase in ascolto, click della vettura) e il log senza il testo del pilota.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_chat.py

Non richiede pytest, ne' rete, ne' chiave: il client Anthropic e' sostituito da uno
finto che conta le chiamate, quindi nessun caso puo' spendere. Stato della spesa e log
in una cartella temporanea, non in backend/logs/. La sessione e' la DEMO.
"""

import logging
import os
import pathlib
import shutil
import sys
import tempfile
from types import SimpleNamespace

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))  # -> backend/

import anthropic  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import budget, config, logging_config  # noqa: E402
from app.api import chat  # noqa: E402
from app.bundle import demo  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
import app.core.agent as agent  # noqa: E402

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []


def test(name: str, passed: bool, detail: str = ""):
    line = f"{PASS if passed else FAIL}  {name}"
    if detail and not passed:
        line += f"\n        → {detail}"
    print(line)
    results.append((name, passed))


# ---------------------------------------------------------------------------
# Preparazione: cartella temporanea, client finto, ambiente salvato
# ---------------------------------------------------------------------------

TMP = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_chat_"))
logger = logging_config.setup_logging(TMP)
LOG_FILE = TMP / logging_config.LOG_FILE_NAME
for h in logger.handlers:
    if type(h) is logging.StreamHandler:
        h.setLevel(logging.CRITICAL + 1)       # i WARNING voluti non sporcano l'output

STATO_ORIGINALE = budget.STATO_PATH
budget.STATO_PATH = TMP / "llm_spesa.json"

VARIABILI = ["PITWALL_CHAT_LIVE", "PITWALL_ALLOW_LIVE", "PITWALL_DEMO_MODE",
             "PITWALL_BUDGET_CHAT_GIORNO", "PITWALL_BUDGET_MESE"]
ENV_SALVATO = {k: os.environ.get(k) for k in VARIABILI}
CHIAVE_SALVATA = config.ANTHROPIC_API_KEY
ORIGINALI = {"Anthropic": anthropic.Anthropic, "log_incident": agent.log_incident}

STREAM = []                                    # ogni chiamata "al modello" finisce qui


class _StreamFinto:
    def __init__(self):
        self.text_stream = iter(["Ciao ", "pilota"])

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return SimpleNamespace(usage=SimpleNamespace(
            input_tokens=3000, output_tokens=40,
            cache_creation_input_tokens=None, cache_read_input_tokens=None))


class AnthropicFinto:
    def __init__(self, **kwargs):
        self.messages = self

    def stream(self, **kwargs):
        STREAM.append(kwargs)
        return _StreamFinto()


anthropic.Anthropic = AnthropicFinto
agent.log_incident = lambda *a, **k: None      # i registri veri non si toccano


def prepara(live: str = "1", chiave: str = "chiave-finta", tetto: str = "0.10"):
    """Stato della spesa vuoto, interruttore, chiave e tetto richiesti."""
    if budget.STATO_PATH.exists():
        budget.STATO_PATH.unlink()
    os.environ["PITWALL_CHAT_LIVE"] = live
    os.environ["PITWALL_ALLOW_LIVE"] = "0"     # il live dell'analisi resta spento
    os.environ["PITWALL_DEMO_MODE"] = "1"
    os.environ["PITWALL_BUDGET_CHAT_GIORNO"] = tetto
    os.environ["PITWALL_BUDGET_MESE"] = "1.00"
    config.ANTHROPIC_API_KEY = chiave
    STREAM.clear()


SEGRETO = "sottosterzo-in-ingresso-alla-roggia"
URL = f"/api/sessions/{demo.DEMO_ID}/chat"
DOMANDA = [{"role": "user", "content": f"Perché ho {SEGRETO}?"}]


def scambi(n: int) -> list[dict]:
    """n domande del pilota con le risposte in mezzo: finisce con una domanda."""
    out = []
    for i in range(1, n + 1):
        out.append({"role": "user", "content": f"domanda {i}"})
        if i < n:
            out.append({"role": "assistant", "content": f"risposta {i}"})
    return out


client = TestClient(fastapi_app, raise_server_exceptions=False)

try:
    # -----------------------------------------------------------------------
    print("\n── Interruttore e chiave ─────────────────────────────────────────")
    # -----------------------------------------------------------------------
    prepara(live="0")
    r = client.post(URL, json={"messages": DOMANDA})
    test("C01 chat spenta (PITWALL_CHAT_LIVE=0): 503, nessuna chiamata al modello",
         r.status_code == 503 and not STREAM, f"{r.status_code} {r.text[:120]}")
    test("C02 salute: chat_live falso con l'interruttore spento",
         client.get("/").json().get("chat_live") is False)

    prepara(chiave="")
    r = client.post(URL, json={"messages": DOMANDA})
    test("C03 interruttore acceso ma chiave assente: 503, nessuna chiamata",
         r.status_code == 503 and not STREAM, f"{r.status_code}")
    test("C04 salute: chat_live falso senza chiave",
         client.get("/").json().get("chat_live") is False)

    os.environ["PITWALL_ALLOW_LIVE"] = "1"
    os.environ["PITWALL_DEMO_MODE"] = "0"
    prepara(live="0")
    os.environ["PITWALL_ALLOW_LIVE"] = "1"
    os.environ["PITWALL_DEMO_MODE"] = "0"
    r = client.post(URL, json={"messages": DOMANDA})
    test("C05 il live dell'analisi NON accende la chat: 503 con ALLOW_LIVE=1 e CHAT_LIVE=0",
         r.status_code == 503 and not STREAM, f"{r.status_code}")

    # -----------------------------------------------------------------------
    print("\n── Risposta dal vivo ─────────────────────────────────────────────")
    # -----------------------------------------------------------------------
    prepara()
    salute = client.get("/").json()
    test("C06 salute: chat_live vero, demo_mode ancora vero (l'analisi resta in demo)",
         salute.get("chat_live") is True and salute.get("demo_mode") is True, str(salute))

    r = client.post(URL, json={"messages": DOMANDA, "fase": 0, "profile": "pilota prudente in frenata"})
    test("C07 chat accesa: 200, testo in streaming, una chiamata al modello",
         r.status_code == 200 and r.text == "Ciao pilota" and len(STREAM) == 1
         and r.headers["content-type"].startswith("text/plain"),
         f"{r.status_code} {r.text[:120]} chiamate {len(STREAM)}")
    chiamata = STREAM[0] if STREAM else {}
    sistema = chiamata.get("system", "")
    test("C08 al modello: 800 token al massimo e la domanda del pilota come ultimo messaggio",
         chiamata.get("max_tokens") == 800 and chiamata.get("messages") == DOMANDA,
         str({k: chiamata.get(k) for k in ("max_tokens", "messages")}))
    test("C09 contesto: report del motore, setup, profilo, debrief, fase in ascolto",
         all(b in sistema for b in ("[CONTESTO SESSIONE]", "[REPORT DEL MOTORE]", "[SETUP]",
                                    "[PROFILO PILOTA]", "pilota prudente in frenata",
                                    "[DEBRIEF", "il pilota sta ascoltando la fase 1,")),
         sistema[-600:])
    test("C10 contesto: i click della BMW (un click di pressione = 0.1 psi)",
         "[CLICK DELLA VETTURA]" in sistema and "tire_press_fl=0.1 psi" in sistema, sistema[-400:])
    test("C11 contesto senza [DOMANDA]: le domande sono i messaggi", "[DOMANDA]" not in sistema)
    spesa = budget._carica()
    atteso = (3000 * 1.00 + 40 * 5.00) / 1_000_000
    test("C12 la spesa va nella categoria chat, al costo reale; analisi a zero",
         abs(spesa["spesa_giorno"]["chat"] - atteso) < 1e-9 and spesa["spesa_giorno"]["analisi"] == 0,
         str(spesa["spesa_giorno"]))
    test("C13 nel log la domanda non c'è: solo lunghezze",
         SEGRETO not in LOG_FILE.read_text(encoding="utf-8")
         and "chat di" in LOG_FILE.read_text(encoding="utf-8"))

    prepara()
    r = client.post(URL, json={"messages": DOMANDA, "fase": 99})
    test("C14 fase fuori dalle fasi: si risponde lo stesso, senza dire quale fase ascolta",
         r.status_code == 200 and STREAM and "il pilota sta ascoltando la fase" not in STREAM[0]["system"])

    # -----------------------------------------------------------------------
    print("\n── Il contesto dice da dove vengono i numeri ─────────────────────")
    # -----------------------------------------------------------------------
    from app.analisi import analizza
    from app.analisi.debrief import debrief
    from app.analisi.gigi import contesto_chat
    from app.bundle import store
    from app.bundle.adapters import canali_del_bundle
    from app.bundle.schema import FonteCarburante, TipoSessione

    bundle = store.leggi(demo.DEMO_ID)
    canali = canali_del_bundle(bundle)
    report = analizza(bundle, canali)
    testo = contesto_chat(report, bundle, debrief(report))
    test("C15 demo: consumo «misurato su 8 giri» e tipo di sessione FP",
         "l/giro misurato su 8 giri" in testo and "sessione FP" in testo)

    bundle.carburante_fonte = FonteCarburante.SETUP
    bundle.meta.tipo_sessione = TipoSessione.SCONOSCIUTO
    report = analizza(bundle, canali)
    testo = contesto_chat(report, bundle, debrief(report))
    test("C16 consumo dal setup: il contesto dice che è una stima, NON una misura",
         "fuelPerLap" in testo and "NON una misura" in testo and "misurato su" not in testo)
    test("C17 sessione di tipo sconosciuto: «non indicato», mai «sessione ?»",
         "tipo di sessione non indicato" in testo and "sessione ?" not in testo)

    bundle.carburante_fonte = FonteCarburante.MANUALE
    report = analizza(bundle, canali)
    test("C18 consumo scritto dal pilota: il contesto dice che non è misurato giro per giro",
         "NON misurata giro per giro" in contesto_chat(report, bundle, debrief(report)))

    # -----------------------------------------------------------------------
    print("\n── Tetto di spesa ────────────────────────────────────────────────")
    # -----------------------------------------------------------------------
    prepara(tetto="0")
    r = client.post(URL, json={"messages": DOMANDA})
    test("C19 tetto della chat a 0: 429 con il motivo, nessuna chiamata",
         r.status_code == 429 and not STREAM and "tetto" in r.json().get("detail", ""),
         f"{r.status_code} {r.text[:120]}")

    prepara(tetto="0.10")
    n, ultima = 0, None
    while n < 200:
        ultima = client.post(URL, json={"messages": DOMANDA})
        if ultima.status_code != 200:
            break
        n += 1
    test("C20 tetto a $0,10: dopo un po' di risposte arriva il 429, e la spesa resta sotto il tetto",
         0 < n < 200 and ultima.status_code == 429 and budget._carica()["spesa_giorno"]["chat"] <= 0.10,
         f"risposte {n}, ultimo {ultima.status_code}, spesa {budget._carica()['spesa_giorno']['chat']}")
    test("C21 ogni risposta data era vera: mai il messaggio di guasto di agent.py al posto del 429",
         len(STREAM) == n, f"chiamate {len(STREAM)}, risposte {n}")

    # -----------------------------------------------------------------------
    print("\n── Limiti della conversazione ────────────────────────────────────")
    # -----------------------------------------------------------------------
    prepara()
    r = client.post(URL, json={"messages": scambi(chat.MAX_DOMANDE)})
    test("C22 dodicesima domanda: ancora 200", r.status_code == 200, f"{r.status_code}")
    al_modello = STREAM[0]["messages"] if STREAM else []
    test("C23 al modello solo la coda: al massimo 8 messaggi, il primo del pilota, l'ultimo la domanda",
         0 < len(al_modello) <= chat.MAX_MESSAGGI_AL_MODELLO and al_modello[0]["role"] == "user"
         and al_modello[-1] == {"role": "user", "content": "domanda 12"},
         str([(m["role"], m["content"]) for m in al_modello]))

    prepara()
    r = client.post(URL, json={"messages": scambi(chat.MAX_DOMANDE + 1)})
    test("C24 tredicesima domanda: 409 «conversazione piena», nessuna chiamata",
         r.status_code == 409 and not STREAM, f"{r.status_code}")

    r = client.post(URL, json={"messages": DOMANDA + [{"role": "assistant", "content": "ecco"}]})
    test("C25 ultimo messaggio non del pilota: 422, nessuna chiamata",
         r.status_code == 422 and not STREAM, f"{r.status_code}")

    r = client.post(URL, json={"messages": [{"role": "user", "content": "a" * (chat.MAX_CARATTERI_DOMANDA + 1)}]})
    test("C26 domanda oltre i 1000 caratteri: 422, nessuna chiamata",
         r.status_code == 422 and not STREAM, f"{r.status_code}")

    r = client.post(URL, json={"messages": []})
    test("C27 nessun messaggio: 422", r.status_code == 422 and not STREAM, f"{r.status_code}")

    r = client.post(URL, json={"messages": [
        {"role": "user", "content": "prima"}, {"role": "user", "content": "seconda"}]})
    test("C28 due messaggi di fila del pilota: al modello ne arriva uno solo, uniti",
         r.status_code == 200 and STREAM and STREAM[0]["messages"] == [
             {"role": "user", "content": "prima\nseconda"}],
         str(STREAM[0]["messages"] if STREAM else r.status_code))

    prepara()
    r = client.post("/api/sessions/20200101-000000-monza_bmw_m4_gt3-0000/chat", json={"messages": DOMANDA})
    test("C29 sessione che non esiste: 404, nessuna chiamata",
         r.status_code == 404 and not STREAM, f"{r.status_code}")

finally:
    for k, v in ENV_SALVATO.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    config.ANTHROPIC_API_KEY = CHIAVE_SALVATA
    anthropic.Anthropic = ORIGINALI["Anthropic"]
    agent.log_incident = ORIGINALI["log_incident"]
    budget.STATO_PATH = STATO_ORIGINALE
    for h in list(logger.handlers):
        logger.removeHandler(h)
        h.close()
    shutil.rmtree(TMP, ignore_errors=True)

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Chat dal vivo conforme")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
