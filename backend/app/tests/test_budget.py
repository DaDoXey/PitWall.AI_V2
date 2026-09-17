"""
test_budget.py — tetto di spesa del ramo LLM (MUST #2, Entry #028)

Controlla i conti (prenotazione al costo massimo, saldo al costo reale), i tetti
per categoria e per mese, il cambio di giorno e di mese, i casi prudenti (stato
illeggibile, importo non valido, richieste concorrenti), e che le tre chiamate
reali al modello (analisi, screenshot, chat) passino davvero dal tetto.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_budget.py

Non richiede pytest, ne' rete, ne' chiave: il client Anthropic e' sostituito da
uno finto che conta le chiamate, quindi nessun caso puo' spendere. Stato e log
in una cartella temporanea, non in backend/logs/.
"""

import logging
import os
import pathlib
import shutil
import sys
import tempfile
import threading
from logging.handlers import RotatingFileHandler
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
from app.main import app as fastapi_app  # noqa: E402
import app.core.agent as agent  # noqa: E402
import app.core.vision_parser as vision_parser  # noqa: E402

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

TMP = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_budget_"))
logger = logging_config.setup_logging(TMP)
LOG_FILE = TMP / logging_config.LOG_FILE_NAME
for h in logger.handlers:
    if type(h) is logging.StreamHandler:
        h.setLevel(logging.CRITICAL + 1)       # i WARNING voluti non sporcano l'output

STATO_ORIGINALE = budget.STATO_PATH
budget.STATO_PATH = TMP / "llm_spesa.json"
ODIERNO = budget._oggi
GIORNO = ["2026-09-11", "2026-09"]
budget._oggi = lambda: (GIORNO[0], GIORNO[1])

VARIABILI = ["PITWALL_ALLOW_LIVE", "PITWALL_DEMO_MODE", "PITWALL_BUDGET_MESE"] + [
    f"PITWALL_BUDGET_{c.upper()}_GIORNO" for c in budget.CATEGORIE]
ENV_SALVATO = {k: os.environ.get(k) for k in VARIABILI}
CHIAVE_SALVATA = config.ANTHROPIC_API_KEY
ORIGINALI = {"Anthropic": anthropic.Anthropic, "log_incident": agent.log_incident,
             "log_token_usage": agent.log_token_usage}

SEZIONI_OK = "\n".join(["## Diagnosi x", "## Causa Meccanica Probabile x",
                        "## Correzione Setup Consigliata x", "## Correzione di Guida x",
                        "## Note Aggiuntive x"])
CREATE = []                                    # ogni chiamata "al modello" finisce qui
RISPOSTE = []                                  # (testo, token_in, token_out) in coda; vuota = default


def _usage(token_in: int, token_out: int, scritti=None, letti=None):
    return SimpleNamespace(input_tokens=token_in, output_tokens=token_out,
                           cache_creation_input_tokens=scritti, cache_read_input_tokens=letti)


class _StreamFinto:
    def __init__(self):
        self.text_stream = iter(["Ciao ", "pilota"])

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return SimpleNamespace(usage=_usage(900, 40))


CLIENT = []                                    # argomenti con cui viene creato ogni client


class AnthropicFinto:
    def __init__(self, **kwargs):
        CLIENT.append(kwargs)
        self.messages = self

    def create(self, **kwargs):
        CREATE.append(kwargs)
        testo, token_in, token_out = RISPOSTE.pop(0) if RISPOSTE else (SEZIONI_OK, 2000, 800)
        return SimpleNamespace(content=[SimpleNamespace(text=testo)], usage=_usage(token_in, token_out))

    def stream(self, **kwargs):
        CREATE.append(kwargs)
        return _StreamFinto()


anthropic.Anthropic = AnthropicFinto           # vale per agent.py e vision_parser.py
agent.log_incident = lambda *a, **k: None      # i registri veri non si toccano
agent.log_token_usage = lambda *a, **k: None

_letto = 0


def nuove_righe() -> str:
    global _letto
    testo = LOG_FILE.read_text(encoding="utf-8")
    nuovo, _letto = testo[_letto:], len(testo)
    return nuovo


def azzera(**tetti):
    """Stato vuoto e tetti richiesti (default larghi)."""
    if budget.STATO_PATH.exists():
        budget.STATO_PATH.unlink()
    os.environ["PITWALL_BUDGET_ANALISI_GIORNO"] = str(tetti.get("analisi", 10))
    os.environ["PITWALL_BUDGET_SCREENSHOT_GIORNO"] = str(tetti.get("screenshot", 10))
    os.environ["PITWALL_BUDGET_CHAT_GIORNO"] = str(tetti.get("chat", 10))
    os.environ["PITWALL_BUDGET_MESE"] = str(tetti.get("mese", 100))
    GIORNO[:] = ["2026-09-11", "2026-09"]
    CREATE.clear()
    RISPOSTE.clear()
    nuove_righe()


def stato() -> dict:
    return budget._carica()


def circa(a: float, b: float) -> bool:
    return abs(a - b) < 1e-6


client = TestClient(fastapi_app, raise_server_exceptions=False)
PNG = {"file": ("setup.png", b"\x89PNG finto", "image/png")}

try:
    # -----------------------------------------------------------------------
    print("\n── Conti ─────────────────────────────────────────────────────────")
    # -----------------------------------------------------------------------
    atteso = ((1000 + budget.MARGINE_TOKEN) * 1.00 + 2500 * 5.00) / 1_000_000
    test("B01 costo massimo haiku: byte di input + margine a $1, max_tokens a $5 per milione",
         circa(budget.costo_massimo("claude-haiku-4-5", "a" * 1000, 2500), atteso))

    test("B02 per eccesso: si contano i byte, non i caratteri (una lettera accentata = 2)",
         circa(budget.costo_massimo("claude-haiku-4-5", "è" * 500, 0),
               budget.costo_massimo("claude-haiku-4-5", "a" * 1000, 0)))

    test("B03 modello fuori listino: conteggiato al listino piu' caro",
         budget.costo_massimo("claude-inventato", "a" * 1000, 100)
         > budget.costo_massimo("claude-sonnet-4-6", "a" * 1000, 100))

    test("B04 costo reale con la cache: scrittura x1,25 e lettura x0,10 sul prezzo di input",
         circa(budget.costo_reale("claude-sonnet-4-6", _usage(1000, 100, scritti=2000, letti=4000)),
               (1000 * 3 + 2000 * 3 * 1.25 + 4000 * 3 * 0.10 + 100 * 15) / 1_000_000))

    # -----------------------------------------------------------------------
    print("\n── Prenotazione e saldo ──────────────────────────────────────────")
    # -----------------------------------------------------------------------
    azzera()
    p = budget.prenota("analisi", "claude-haiku-4-5", "a" * 1000, 2500)
    s = stato()
    test("B05 prenota: su disco il costo massimo e una chiamata",
         circa(s["spesa_giorno"]["analisi"], round(p.importo, 6)) and s["chiamate_giorno"]["analisi"] == 1
         and circa(s["spesa_mese"], round(p.importo, 6)), str(s))

    budget.salda(p, _usage(1100, 900))
    s, righe = stato(), nuove_righe()
    reale = budget.costo_reale("claude-haiku-4-5", _usage(1100, 900))
    test("B06 salda: la prenotazione diventa il costo reale, giorno e mese",
         circa(s["spesa_giorno"]["analisi"], round(reale, 6)) and circa(s["spesa_mese"], round(reale, 6)),
         str(s))
    test("B07 salda: riga INFO con modello, token e costo (il modello che ha risposto arriva al log)",
         "INFO" in righe and "claude-haiku-4-5, 1100 token in, 900 out" in righe, righe.strip())

    azzera()
    p = budget.prenota("analisi", "claude-haiku-4-5", "a" * 1000, 2500)
    budget.salda(p, None)
    test("B08 risposta senza usage: resta il costo massimo + WARNING",
         circa(stato()["spesa_giorno"]["analisi"], round(p.importo, 6)) and "senza usage" in nuove_righe())

    # -----------------------------------------------------------------------
    print("\n── Tetti ─────────────────────────────────────────────────────────")
    # -----------------------------------------------------------------------
    massimo = budget.costo_massimo("claude-haiku-4-5", "a" * 1000, 2500)
    azzera(analisi=massimo * 1.5)
    budget.prenota("analisi", "claude-haiku-4-5", "a" * 1000, 2500)
    prima = stato()
    try:
        budget.prenota("analisi", "claude-haiku-4-5", "a" * 1000, 2500)
        rifiutata = False
    except budget.BudgetEsaurito:
        rifiutata = True
    test("B09 tetto giornaliero: la seconda prenotazione e' rifiutata e lo stato non cambia",
         rifiutata and stato() == prima, str(stato()))
    test("B10 rifiuto nel log: WARNING con importi e tetti", "RIFIUTATA" in nuove_righe())

    try:
        budget.prenota("screenshot", "claude-sonnet-4-6", "a" * 1000, 1000, immagini=1)
        indipendenti = True
    except budget.SpesaRifiutata:
        indipendenti = False
    test("B11 categorie indipendenti: analisi esaurita, lo screenshot passa", indipendenti)

    azzera(mese=massimo * 1.5)
    budget.prenota("screenshot", "claude-haiku-4-5", "a" * 1000, 2500)
    try:
        budget.prenota("analisi", "claude-haiku-4-5", "a" * 1000, 2500)
        mensile = False
    except budget.BudgetEsaurito:
        mensile = True
    test("B12 tetto mensile: blocca ogni categoria anche con il giornaliero libero", mensile)

    azzera()
    os.environ["PITWALL_BUDGET_ANALISI_GIORNO"] = "cinquanta"
    try:
        budget.prenota("analisi", "claude-haiku-4-5", "a", 10)
        invalido = False
    except budget.BudgetEsaurito:
        invalido = True
    test("B13 importo non valido nel .env: vale 0, nessuna spesa + ERROR",
         invalido and "non e' un importo valido" in nuove_righe())

    azzera()
    os.environ.pop("PITWALL_BUDGET_CHAT_GIORNO")
    test("B14 default: chat a $0 (non collegata), analisi $0,50, screenshot $0,25, mese $5",
         budget.tetto_giornaliero("chat") == 0 and not budget.disponibile("chat")
         and budget.tetto_giornaliero("analisi") >= 0 and budget.DEFAULT_GIORNO["analisi"] == "0.50"
         and budget.DEFAULT_GIORNO["screenshot"] == "0.25" and budget.DEFAULT_MESE == "5.00")

    # -----------------------------------------------------------------------
    print("\n── Periodi ───────────────────────────────────────────────────────")
    # -----------------------------------------------------------------------
    azzera()
    budget.salda(budget.prenota("analisi", "claude-haiku-4-5", "a", 10), _usage(100, 10))
    mese_prima = stato()["spesa_mese"]
    GIORNO[:] = ["2026-09-12", "2026-09"]
    s = stato()
    test("B15 giorno nuovo: spesa e chiamate del giorno azzerate, il mese resta",
         s["spesa_giorno"]["analisi"] == 0 and s["chiamate_giorno"]["analisi"] == 0
         and circa(s["spesa_mese"], mese_prima) and mese_prima > 0, str(s))

    GIORNO[:] = ["2026-10-01", "2026-10"]
    test("B16 mese nuovo: tutto azzerato", stato()["spesa_mese"] == 0)

    azzera()
    p = budget.prenota("analisi", "claude-haiku-4-5", "a" * 1000, 2500)
    GIORNO[:] = ["2026-09-12", "2026-09"]
    budget.salda(p, _usage(1100, 900))
    s = stato()
    test("B17 chiamata a cavallo di mezzanotte: il costo reale finisce nel giorno nuovo",
         circa(s["spesa_giorno"]["analisi"], round(reale, 6)) and circa(s["spesa_mese"], round(reale, 6)),
         str(s))

    # -----------------------------------------------------------------------
    print("\n── Casi prudenti ─────────────────────────────────────────────────")
    # -----------------------------------------------------------------------
    azzera()
    budget.STATO_PATH.write_text("{ non e' json", encoding="utf-8")
    try:
        budget.prenota("analisi", "claude-haiku-4-5", "a", 10)
        bloccato = False
    except budget.StatoSpesaIllegibile:
        bloccato = True
    p_finta = budget.Prenotazione("analisi", "claude-haiku-4-5", 0.01, GIORNO[0], GIORNO[1])
    try:
        budget.salda(p_finta, _usage(10, 10))
        salda_muto = True
    except Exception:  # noqa: BLE001
        salda_muto = False
    test("B18 stato illeggibile: prenota blocca, disponibile() dice no, salda non solleva",
         bloccato and not budget.disponibile("analisi") and salda_muto)

    azzera(analisi=massimo * 5.5)
    esiti = []

    def _prova():
        try:
            budget.prenota("analisi", "claude-haiku-4-5", "a" * 1000, 2500)
            esiti.append(True)
        except budget.BudgetEsaurito:
            esiti.append(False)

    fili = [threading.Thread(target=_prova) for _ in range(20)]
    for f in fili:
        f.start()
    for f in fili:
        f.join()
    test("B19 20 richieste insieme con un tetto che ne regge 5: passano esattamente 5",
         esiti.count(True) == 5 and stato()["spesa_giorno"]["analisi"] <= massimo * 5.5,
         f"passate {esiti.count(True)}, spesa {stato()['spesa_giorno']['analisi']}")

    # -----------------------------------------------------------------------
    print("\n── Le chiamate reali passano dal tetto ───────────────────────────")
    # -----------------------------------------------------------------------
    azzera()
    testo = agent.call_claude("sottosterzo in uscita", "chiave-finta", "claude-haiku-4-5")
    s = stato()
    test("B20 agent.call_claude: una chiamata, spesa = costo reale dell'usage",
         testo == SEZIONI_OK and len(CREATE) == 1
         and circa(s["spesa_giorno"]["analisi"], round(budget.costo_reale("claude-haiku-4-5", _usage(2000, 800)), 6)),
         f"{len(CREATE)} chiamate, {s}")

    azzera()
    RISPOSTE.extend([("incompleta", 2000, 2500), ("incompleta", 2000, 2500), (SEZIONI_OK, 2100, 900)])
    testo = agent.get_ai_response(user_input="sottosterzo", api_key="chiave-finta")
    atteso = (2 * budget.costo_reale("claude-haiku-4-5", _usage(2000, 2500))
              + budget.costo_reale("claude-sonnet-4-6", _usage(2100, 900)))
    test("B21 cascata haiku x2 -> sonnet: tre chiamate, spesa = somma dei tre costi reali",
         testo == SEZIONI_OK and [c["model"] for c in CREATE] == ["claude-haiku-4-5"] * 2 + ["claude-sonnet-4-6"]
         and abs(stato()["spesa_giorno"]["analisi"] - atteso) < 1e-5, f"{stato()} atteso {atteso}")

    test("B21b client di agent.py: timeout di PITWALL_LLM_TIMEOUT_S (90 s) e nessuna ripetizione dell'SDK (una prenotazione = "
         "una richiesta)", len(CLIENT) >= 3 and all(c.get("timeout") == agent.LLM_TIMEOUT_S and c.get("max_retries") == 0
                                                    for c in CLIENT[-3:]), str(CLIENT[-3:]))

    azzera(analisi=0)
    testo = agent.get_ai_response(user_input="sottosterzo", api_key="chiave-finta")
    test("B22 cascata a tetto esaurito: nessuna chiamata, agent risponde 'non disponibile'",
         not CREATE and "temporaneamente non disponibile" in testo, f"{len(CREATE)} chiamate")

    azzera()
    risultato = vision_parser.parse_setup_from_image(b"\x89PNG finto", api_key="chiave-finta",
                                                     media_type="image/png")
    RISPOSTE.clear()
    s = stato()
    test("B23 vision_parser: categoria screenshot, modello sonnet-4-6, saldo al reale",
         len(CREATE) == 1 and CREATE[0]["model"] == "claude-sonnet-4-6"
         and s["chiamate_giorno"]["screenshot"] == 1 and s["spesa_giorno"]["analisi"] == 0
         and circa(s["spesa_giorno"]["screenshot"],
                   round(budget.costo_reale("claude-sonnet-4-6", _usage(2000, 800)), 6)), str(s))

    azzera(chat=0)
    pezzi = list(agent.chat_with_gigi([{"role": "user", "content": "ciao"}], api_key="chiave-finta"))
    test("B24 chat a tetto 0: nessuna chiamata, messaggio d'errore della chat",
         not CREATE and len(pezzi) == 1 and "problema di collegamento" in pezzi[0], str(pezzi))

    azzera()
    pezzi = list(agent.chat_with_gigi([{"role": "user", "content": "ciao"}], api_key="chiave-finta"))
    test("B25 chat con margine: testo in streaming e saldo al reale, client con timeout 90 s e senza "
         "ripetizioni", "".join(pezzi) == "Ciao pilota" and len(CREATE) == 1
         and CLIENT[-1].get("timeout") == agent.LLM_TIMEOUT_S and CLIENT[-1].get("max_retries") == 0
         and circa(stato()["spesa_giorno"]["chat"],
                   round(budget.costo_reale(agent.CLAUDE_MODEL, _usage(900, 40)), 6)), str(stato()))

    # -----------------------------------------------------------------------
    print("\n── Endpoint in live ──────────────────────────────────────────────")
    # -----------------------------------------------------------------------
    os.environ["PITWALL_ALLOW_LIVE"], os.environ["PITWALL_DEMO_MODE"] = "1", "0"
    config.ANTHROPIC_API_KEY = "chiave-finta-mai-usata"

    azzera()
    r = client.post("/api/analysis", json={"prompt": "sottosterzo in uscita"})
    rid, righe = r.headers.get("x-request-id", ""), nuove_righe()
    test("B26 /api/analysis live: source=api, riga del costo con lo stesso request-id",
         r.json().get("source") == "api" and len(CREATE) == 1
         and f"[{rid}] pitwall.budget: analisi: claude-haiku-4-5" in righe, righe.strip())

    azzera(analisi=0)
    r = client.post("/api/analysis", json={"prompt": "sottosterzo in uscita"})
    righe = nuove_righe()
    test("B27 /api/analysis a tetto esaurito: fallback + WARNING col motivo, nessuna chiamata",
         r.json().get("source") == "fallback" and not CREATE
         and "tetto di spesa dell'analisi raggiunto" in righe, righe.strip())

    azzera(screenshot=0)
    r = client.post("/api/setup/from-image", files=PNG)
    righe = nuove_righe()
    test("B28 /api/setup/from-image a tetto esaurito: 429 col messaggio, nessuna chiamata",
         r.status_code == 429 and "Tetto di spesa" in r.json().get("detail", "") and not CREATE
         and "429" in righe, f"{r.status_code} {r.text} {righe.strip()}")

    azzera()
    budget.STATO_PATH.write_text("[]", encoding="utf-8")
    r = client.post("/api/setup/from-image", files=PNG)
    test("B29 /api/setup/from-image con stato illeggibile: 503, nessuna chiamata",
         r.status_code == 503 and not CREATE, f"{r.status_code} {r.text}")

    azzera()
    r = client.post("/api/setup/from-image", files=PNG)
    test("B30 /api/setup/from-image con margine: 200 e spesa registrata",
         r.status_code == 200 and len(CREATE) == 1 and stato()["chiamate_giorno"]["screenshot"] == 1,
         f"{r.status_code} {r.text[:200]}")

finally:
    for k, v in ENV_SALVATO.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    config.ANTHROPIC_API_KEY = CHIAVE_SALVATA
    anthropic.Anthropic = ORIGINALI["Anthropic"]
    agent.log_incident = ORIGINALI["log_incident"]
    agent.log_token_usage = ORIGINALI["log_token_usage"]
    budget.STATO_PATH = STATO_ORIGINALE
    budget._oggi = ODIERNO
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
    print("✅ Tetto di spesa conforme")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
