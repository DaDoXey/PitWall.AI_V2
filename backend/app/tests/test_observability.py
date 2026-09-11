"""
test_observability.py — log del backend e request-id (MUST #1, Entry #026)

Controlla che ogni esito del ramo LLM lasci una riga di log con il suo motivo, che
il testo del pilota non ci finisca mai, e che il contratto delle API resti quello
di prima.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_observability.py

Non richiede pytest, ne' rete, ne' chiave: le risposte del modello sono sostituite,
e `call_claude` e' bloccata apposta, cosi' nessun caso puo' uscire su Internet per
errore. Scrive in una cartella temporanea, non in backend/logs/.
"""

import logging
import os
import pathlib
import shutil
import sys
import tempfile
from logging.handlers import RotatingFileHandler

# Forza output UTF-8 su console Windows (cp1252 non gestisce ✅ / box-drawing)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))  # -> backend/

from fastapi.testclient import TestClient  # noqa: E402

from app import budget, config, logging_config  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
import app.core.agent as agent  # noqa: E402
import app.core.vision_parser as vision_parser  # noqa: E402

# ---------------------------------------------------------------------------
# Utility di test minimale (stessa forma di test_parser.py)
# ---------------------------------------------------------------------------

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
# Preparazione: log in una cartella temporanea, rete bloccata, ambiente salvato
# ---------------------------------------------------------------------------

LOG_TMP = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_log_"))
logger = logging_config.setup_logging(LOG_TMP)
LOG_FILE = LOG_TMP / logging_config.LOG_FILE_NAME
budget.STATO_PATH = LOG_TMP / "llm_spesa.json"   # la spesa vera non si tocca

file_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]
console_handlers = [h for h in logger.handlers if type(h) is logging.StreamHandler]
livello_console = console_handlers[0].level if console_handlers else None
for h in console_handlers:          # i WARNING voluti dai test non sporcano l'output
    h.setLevel(logging.CRITICAL + 1)


def _rete_vietata(*args, **kwargs):
    raise AssertionError("test_observability: chiamata di rete non ammessa")


agent.call_claude = _rete_vietata
agent.log_incident = lambda *a, **k: None       # i registri veri non si toccano
agent.log_token_usage = lambda *a, **k: None

ENV_SALVATO = {k: os.environ.get(k) for k in ("PITWALL_ALLOW_LIVE", "PITWALL_DEMO_MODE")}
CHIAVE_SALVATA = config.ANTHROPIC_API_KEY
ORIGINALI = {
    "get_ai_response": agent.get_ai_response,
    "parse": vision_parser.parse_setup_from_image,
    "summary": vision_parser.summarize_parsed_setup,
}

MARCATORE = "MARCATORE-PRIVATO-7Q"
SEZIONI_OK = "\n".join(["## Diagnosi x", "## Causa Meccanica Probabile x",
                        "## Correzione Setup Consigliata x", "## Note Aggiuntive x"])

client = TestClient(fastapi_app, raise_server_exceptions=False)
_letto = 0


def nuove_righe() -> str:
    """Le righe scritte nel log dall'ultima lettura."""
    global _letto
    testo = LOG_FILE.read_text(encoding="utf-8")
    nuovo, _letto = testo[_letto:], len(testo)
    return nuovo


def modalita(live: bool) -> None:
    os.environ["PITWALL_ALLOW_LIVE"] = "1" if live else "0"
    os.environ["PITWALL_DEMO_MODE"] = "0" if live else "1"


def analisi(prompt: str, profile: str | None = None):
    r = client.post("/api/analysis", json={"prompt": prompt, "profile": profile})
    return r, r.json(), r.headers.get("x-request-id", ""), nuove_righe()


def riga_con(testo: str, parola: str) -> str:
    return next((l for l in testo.splitlines() if parola in l), testo.strip()[-300:])


try:
    # -----------------------------------------------------------------------
    print("\n── Request-id e riga di accesso ──────────────────────────────────")
    # -----------------------------------------------------------------------
    r = client.get("/")
    rid = r.headers.get("x-request-id", "")
    righe = nuove_righe()
    test("T01 health: 200 e X-Request-ID generato (12 caratteri)",
         r.status_code == 200 and len(rid) == 12, f"status {r.status_code}, rid {rid!r}")
    test("T02 riga di accesso con lo stesso request-id",
         f"[{rid}]" in righe and "GET / -> 200" in righe, righe.strip())

    r = client.get("/", headers={"X-Request-ID": "prova-rid.01"})
    test("T03 request-id valido del client: riusato e scritto nel log",
         r.headers.get("x-request-id") == "prova-rid.01" and "[prova-rid.01]" in nuove_righe())

    r = client.get("/", headers={"X-Request-ID": "rid con spazi " + "x" * 80})
    nuove_righe()
    test("T04 request-id non valido del client: sostituito",
         len(r.headers.get("x-request-id", "")) == 12, r.headers.get("x-request-id", ""))

    # -----------------------------------------------------------------------
    print("\n── /api/analysis: ogni esito lascia fonte e motivo ───────────────")
    # -----------------------------------------------------------------------
    modalita(live=False)
    r, body, rid, righe = analisi(f"gomme {MARCATORE}", profile=f"pilota {MARCATORE}")
    test("T05 demo: source=demo e contratto invariato (question, text, source)",
         r.status_code == 200 and set(body) == {"question", "text", "source"}
         and body["source"] == "demo", str(body)[:200])
    test("T06 demo: riga con la fonte e il request-id della richiesta, anche dal thread "
         "dell'endpoint", f"[{rid}] pitwall.analysis" in righe and "source=demo" in righe,
         righe.strip())
    test("T07 privacy: ne' prompt ne' profilo nel log, solo lunghezza e presenza",
         MARCATORE not in righe and "caratteri" in righe and "profilo si" in righe,
         righe.strip())

    modalita(live=True)
    config.ANTHROPIC_API_KEY = ""
    r, body, rid, righe = analisi("sottosterzo in uscita")
    test("T08 live senza chiave: fallback + WARNING col motivo",
         body.get("source") == "fallback" and "WARNING" in righe
         and "ANTHROPIC_API_KEY assente" in righe, righe.strip())

    config.ANTHROPIC_API_KEY = "chiave-finta-mai-usata"
    # Fino all'Entry #027 questo caso mandava 33.000 caratteri e registrava l'eccezione
    # vera dell'`import streamlit`. Dall'Entry #028 un testo cosi' lungo si ferma prima.
    chiamate_agent = []
    agent.get_ai_response = lambda **kw: chiamate_agent.append(1) or SEZIONI_OK
    r, body, rid, righe = analisi(MARCATORE + " " + "a" * 33_000)
    test("T09 testo oltre il limite: fallback + WARNING col motivo, modello mai chiamato",
         body.get("source") == "fallback" and "WARNING" in righe and "oltre il limite" in righe
         and not chiamate_agent and MARCATORE not in righe, righe.strip())

    def _ramo_rotto(**kw):
        raise RuntimeError("guasto finto del ramo LLM")

    agent.get_ai_response = _ramo_rotto
    r, body, rid, righe = analisi(f"sottosterzo {MARCATORE}")
    test("T10 eccezione nel ramo LLM: fallback + ERROR con traceback, senza il testo del pilota",
         body.get("source") == "fallback" and "ERROR" in righe and "Traceback" in righe
         and "eccezione nel ramo LLM" in righe and MARCATORE not in righe,
         riga_con(righe, "Error"))

    agent.get_ai_response = lambda **kw: "risposta senza le sezioni"
    r, body, rid, righe = analisi("sottosterzo in uscita")
    test("T11 risposta senza le 4 sezioni: fallback + WARNING col motivo",
         body.get("source") == "fallback" and "WARNING" in righe
         and "senza le 4 sezioni" in righe, righe.strip())

    agent.get_ai_response = lambda **kw: "⚠️ Servizio temporaneamente non disponibile. Riprova tra poco."
    r, body, rid, righe = analisi("sottosterzo in uscita")
    test("T12 tutti i modelli falliti: fallback + WARNING che lo distingue",
         body.get("source") == "fallback" and "tutti i modelli della cascata" in righe,
         righe.strip())

    agent.get_ai_response = lambda **kw: SEZIONI_OK
    r, body, rid, righe = analisi("sottosterzo in uscita")
    test("T13 risposta valida: source=api + INFO con la durata",
         body.get("source") == "api" and body.get("text") == SEZIONI_OK
         and "INFO" in righe and "source=api in" in righe, righe.strip())
    agent.get_ai_response = ORIGINALI["get_ai_response"]

    # -----------------------------------------------------------------------
    print("\n── /api/setup/from-image ─────────────────────────────────────────")
    # -----------------------------------------------------------------------
    PNG = {"file": ("setup.png", b"\x89PNG finto", "image/png")}

    # Presidio (Entry #027): con la chiave presente, la demo-mode deve bastare a fermare
    # la chiamata. La spia conta le volte in cui si arriva al parser, cioe' al modello.
    chiamate_parser = []
    vision_parser.parse_setup_from_image = lambda *a, **k: chiamate_parser.append(1) or {}
    config.ANTHROPIC_API_KEY = "chiave-finta-mai-usata"

    modalita(live=False)
    r = client.post("/api/setup/from-image", files=PNG)
    righe = nuove_righe()
    test("T14 vision in demo-mode con la chiave: 503, WARNING, modello mai chiamato",
         r.status_code == 503 and "WARNING" in righe and "demo-mode" in righe
         and not chiamate_parser, f"status {r.status_code}, chiamate {len(chiamate_parser)}, "
         f"{righe.strip()}")

    os.environ["PITWALL_ALLOW_LIVE"] = "1"      # live consentito ma demo-mode lasciata a 1
    os.environ["PITWALL_DEMO_MODE"] = "1"
    r = client.post("/api/setup/from-image", files=PNG)
    righe = nuove_righe()
    test("T15 vision con ALLOW_LIVE=1 ma DEMO_MODE=1: 503, servono entrambi i flag",
         r.status_code == 503 and "demo-mode" in righe and not chiamate_parser,
         f"status {r.status_code}, chiamate {len(chiamate_parser)}")
    vision_parser.parse_setup_from_image = ORIGINALI["parse"]

    modalita(live=True)
    config.ANTHROPIC_API_KEY = ""
    r = client.post("/api/setup/from-image", files=PNG)
    righe = nuove_righe()
    test("T16 vision senza chiave: 503 + WARNING", r.status_code == 503 and "WARNING" in righe
         and "ANTHROPIC_API_KEY assente" in righe, righe.strip())

    config.ANTHROPIC_API_KEY = "chiave-finta-mai-usata"

    def _parser_rotto(*a, **k):
        raise RuntimeError("guasto finto del parser")

    vision_parser.parse_setup_from_image = _parser_rotto
    r = client.post("/api/setup/from-image", files=PNG)
    righe = nuove_righe()
    test("T17 vision guasta: 500 + ERROR con traceback e dimensione del file",
         r.status_code == 500 and "ERROR" in righe and "Traceback" in righe
         and "lettura screenshot fallita" in righe and "byte" in righe, righe.strip())

    vision_parser.parse_setup_from_image = lambda *a, **k: {"parametri": {}}
    vision_parser.summarize_parsed_setup = lambda r: "ok"
    r = client.post("/api/setup/from-image", files=PNG)
    righe = nuove_righe()
    test("T18 vision riuscita: 200 + INFO con la durata",
         r.status_code == 200 and "screenshot letto in" in righe, righe.strip())

    # -----------------------------------------------------------------------
    print("\n── Eccezione non gestita ─────────────────────────────────────────")
    # -----------------------------------------------------------------------
    def _boom():
        raise RuntimeError("boom di prova")

    fastapi_app.add_api_route("/__test_boom", _boom)
    r = client.get("/__test_boom")
    righe = nuove_righe()
    test("T19 eccezione non gestita: 500 + ERROR con traceback nel log",
         r.status_code == 500 and "eccezione non gestita" in righe and "Traceback" in righe,
         righe.strip()[-300:])

    # -----------------------------------------------------------------------
    print("\n── Configurazione ────────────────────────────────────────────────")
    # -----------------------------------------------------------------------
    test("T20 file rotante: un solo handler, 1 MB x 3 copie",
         len(file_handlers) == 1 and file_handlers[0].maxBytes == 1_000_000
         and file_handlers[0].backupCount == 3)
    test("T21 console solo da WARNING in su", livello_console == logging.WARNING,
         f"livello {livello_console}")
    test("T22 cartella di default = backend/logs/, ricavata dal file",
         config.LOG_DIR == BACKEND / "logs", str(config.LOG_DIR))

    from dotenv import dotenv_values
    env_file = BACKEND / ".env"
    sovrascritti = env_file.exists() and bool(
        {"PITWALL_PROMPT_LOG_PATH", "PITWALL_INCIDENTS_PATH"} & set(dotenv_values(env_file)))
    if sovrascritti:
        test("T23 registri di agent.py in backend/logs/ (saltato: il .env li imposta)", True)
    else:
        test("T23 registri di agent.py in backend/logs/, con agent.py intatto",
             agent.LOG_PATH == str(config.LOG_DIR / "llm_token_log.md")
             and agent.INCIDENT_PATH == str(config.LOG_DIR / "llm_incidents.md"),
             f"{agent.LOG_PATH} · {agent.INCIDENT_PATH}")

    logging.getLogger("pitwall.test").info("riga prima della rotazione")
    file_handlers[0].doRollover()
    test("T24 rotazione reale: nasce pitwall.log.1",
         (LOG_TMP / f"{logging_config.LOG_FILE_NAME}.1").exists())

finally:
    for k, v in ENV_SALVATO.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    config.ANTHROPIC_API_KEY = CHIAVE_SALVATA
    agent.get_ai_response = ORIGINALI["get_ai_response"]
    vision_parser.parse_setup_from_image = ORIGINALI["parse"]
    vision_parser.summarize_parsed_setup = ORIGINALI["summary"]
    for h in list(logger.handlers):
        logger.removeHandler(h)
        h.close()
    shutil.rmtree(LOG_TMP, ignore_errors=True)

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Log e request-id conformi")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
