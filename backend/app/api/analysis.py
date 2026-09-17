"""POST /api/analysis — l'analisi di Gigi a 5 sezioni, su una sessione (L4).

Gigi parla di **una sessione dell'archivio** (`session_id`; senza, la DEMO) e riceve il
report del motore di analisi, il setup e il racconto del pilota (`analisi/gigi.py`).

Le fonti della risposta, sempre dichiarate in `source`:
* `demo` / `cache` — la sessione è la DEMO e il live è spento (o il prompt è quello
  canonico della demo): risposte pre-validate di `core/demo_responses.py`, niente rete;
* `motore` — la sessione NON è la demo e il modello non si può chiamare: le 5 sezioni
  composte dal report, senza modello. Prima si rispondeva con la storia di Monza
  qualunque sessione fosse aperta;
* `api` — il modello ha risposto con le 5 sezioni;
* `fallback` — il modello doveva rispondere e non l'ha fatto: si ripiega sulla cache
  (demo) o sul motore (altre sessioni), dicendo il motivo nel log.

Ogni esito lascia una riga in backend/logs/pitwall.log con la fonte e, quando si
ripiega, il motivo (Entry #026). Mai il testo del pilota: solo lunghezze.

Tetto di spesa (Entry #028): prima del ramo reale si controllano la lunghezza del
testo e il margine della categoria "analisi" di app.budget. La garanzia vera sta in
agent.call_claude, che prenota il costo massimo prima di ogni chiamata della cascata.
"""

import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import budget, config
from app.analisi import analizza
from app.analisi.gigi import contesto, risposta_dal_motore
from app.bundle import demo, store
from app.bundle.adapters import canali_del_bundle

# _DEMO_ROUTES è privato del modulo protetto ma è l'unica fonte di verità delle
# keyword: lo si legge (mai modificato) per capire se una domanda è nel perimetro
# della demo, senza duplicare la lista qui.
from app.core.demo_responses import _DEMO_ROUTES, is_demo_prompt, pick_demo_response

router = APIRouter()
log = logging.getLogger("pitwall.analysis")

# Testo con cui agent.py (protetto) risponde quando tutti i modelli della cascata
# hanno fallito. Letto e mai modificato, come _DEMO_ROUTES: serve solo a scrivere nel
# log PERCHE' si è finiti in fallback. I dettagli del guasto li scrive agent.py nel
# suo registro dei guasti (default backend/logs/llm_incidents.md).
_AGENT_TUTTI_FALLITI = "Servizio temporaneamente non disponibile"

_REQUIRED = ["## Diagnosi", "## Causa Meccanica", "## Correzione Setup",
             "## Correzione di Guida", "## Note Aggiuntive"]

# Lunghezze massime del ramo reale (Entry #028). Il profilo del wizard e' una riga da
# ~300 caratteri; una domanda del pilota sta ben sotto i 4000. Oltre, niente chiamata:
# riduce il caso peggiore del costo, e tiene l'input lontano dalla soglia degli 8000
# token stimati di agent.py, oltre la quale il contesto viene solo annotato nel log.
MAX_CARATTERI_PROMPT = 4000
MAX_CARATTERI_PROFILO = 1000


def _in_scope(prompt: str) -> bool:
    """True se la domanda matcha una route della cache (o è il prompt demo canonico)."""
    p = (prompt or "").lower()
    return is_demo_prompt(prompt) or any(any(k in p for k in keys) for keys, _ in _DEMO_ROUTES)


def _off_topic_text(report) -> str:
    """Risposta onesta per domande fuori perimetro sulla demo: niente default sul
    sovrasterzo (sembrerebbe un'allucinazione). I dati arrivano dal report della demo."""
    return (
        f"Sono l'ingegnere di pista di questa sessione — BMW M4 GT3 a Monza, prove su "
        f"pista asciutta, {report.giri_totali} giri — e analizzo solo i suoi dati.\n\n"
        "Chiedimi ad esempio di:\n"
        "- **gomme** e temperature\n"
        "- **pressioni** e finestra di lavoro\n"
        "- **freni**, staccate e bilanciamento\n"
        "- **carburante**, consumi e strategia\n"
        "- comportamento in curva: «l'auto scivola dietro», «va larga davanti»…"
    )


class AnalysisRequest(BaseModel):
    prompt: str
    # Profilo pilota dal wizard "Conosci il pilota" (megaprompt #9, FASE 5).
    # Opzionale e usato SOLO nel ramo LLM reale: nel ramo demo/cache viene
    # ignorato, così il routing per keyword di pick_demo_response (protetto)
    # continua a vedere il prompt puro dell'utente.
    profile: str | None = None
    # La sessione di cui si parla. Senza, la DEMO (L4).
    session_id: str | None = None


def _descrivi(req: AnalysisRequest) -> str:
    """La richiesta come appare nel log: lunghezza e presenza, MAI il testo del
    pilota né il profilo (decisione del 10/09)."""
    profilo = "si" if req.profile and req.profile.strip() else "no"
    sessione = "demo" if not req.session_id or demo.e_demo(req.session_id) else "archivio"
    return f"prompt {len(req.prompt or '')} caratteri, profilo {profilo}, sessione {sessione}"


def _ms(inizio: float) -> float:
    return (time.perf_counter() - inizio) * 1000


def _sessione(id_sessione: str | None):
    """(bundle, report) della sessione chiesta, o della demo."""
    id_sessione = id_sessione or demo.DEMO_ID
    if demo.e_demo(id_sessione):
        demo.assicura_demo()
    try:
        bundle = store.leggi(id_sessione)
    except store.SessioneNonTrovata:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    except store.ArchivioError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return bundle, analizza(bundle, canali_del_bundle(bundle))


@router.post("/analysis")
def post_analysis(req: AnalysisRequest):
    prompt = req.prompt or ""
    bundle, report = _sessione(req.session_id)
    e_demo = bundle.meta.fonte.value == "demo"

    def ripiego() -> tuple[str, str]:
        """Il testo quando il modello non risponde: cache per la demo, motore per le altre."""
        if e_demo:
            return pick_demo_response(prompt), "fallback"
        return risposta_dal_motore(report, bundle, prompt), "fallback"

    # 1) live spento, o prompt = scenario demo.
    #    Demo: cache per keyword; fuori perimetro → redirect onesto, NON il default
    #    sovrasterzo della cache (blindatura anti-"allucinazione percepita").
    #    Altre sessioni: le 5 sezioni dal motore, senza modello.
    if config.demo_mode() or (e_demo and is_demo_prompt(prompt)):
        if e_demo:
            source = "demo" if config.demo_mode() else "cache"
            in_scope = _in_scope(prompt)
            text = pick_demo_response(prompt) if in_scope else _off_topic_text(report)
            log.info("source=%s, %s, %s", source,
                     "in perimetro" if in_scope else "fuori perimetro", _descrivi(req))
        else:
            source = "motore"
            text = risposta_dal_motore(report, bundle, prompt)
            log.info("source=motore: live spento, risposta dal report, %s", _descrivi(req))
        return {"question": prompt, "text": text, "source": source}

    # 2) LLM reale con ripiego
    api_key = config.ANTHROPIC_API_KEY
    if not api_key:
        log.warning("source=fallback: live consentito ma ANTHROPIC_API_KEY assente, %s",
                    _descrivi(req))
        text, source = ripiego()
        return {"question": prompt, "text": text, "source": source}

    if len(prompt) > MAX_CARATTERI_PROMPT or len(req.profile or "") > MAX_CARATTERI_PROFILO:
        log.warning("source=fallback: testo oltre il limite (%d/%d caratteri il prompt, %d/%d il "
                    "profilo), nessuna chiamata", len(prompt), MAX_CARATTERI_PROMPT,
                    len(req.profile or ""), MAX_CARATTERI_PROFILO)
        text, source = ripiego()
        return {"question": prompt, "text": text, "source": source}

    if not budget.disponibile("analisi"):
        log.warning("source=fallback: tetto di spesa dell'analisi raggiunto, nessuna chiamata, %s",
                    _descrivi(req))
        text, source = ripiego()
        return {"question": prompt, "text": text, "source": source}

    inizio = time.perf_counter()
    try:
        from app.core.agent import get_ai_response

        resp = get_ai_response(
            user_input=contesto(report, bundle, prompt, req.profile), api_key=api_key,
            auto=bundle.meta.car or "", tracciato=bundle.meta.track or "",
        )
    except Exception:
        log.exception("source=fallback: eccezione nel ramo LLM dopo %.0f ms, %s",
                      _ms(inizio), _descrivi(req))
        text, source = ripiego()
        return {"question": prompt, "text": text, "source": source}

    ok = all(s in (resp or "") for s in _REQUIRED)
    if ok:
        log.info("source=api in %.0f ms, risposta %d caratteri, %s",
                 _ms(inizio), len(resp), _descrivi(req))
        return {"question": prompt, "text": resp, "source": "api"}
    if _AGENT_TUTTI_FALLITI in (resp or ""):
        log.warning("source=fallback: tutti i modelli della cascata hanno fallito dopo %.0f ms "
                    "(dettagli nel registro guasti di agent.py), %s", _ms(inizio), _descrivi(req))
    else:
        log.warning("source=fallback: risposta senza le sezioni obbligatorie (%d caratteri) "
                    "dopo %.0f ms, %s", len(resp or ""), _ms(inizio), _descrivi(req))
    text, source = ripiego()
    return {"question": prompt, "text": text, "source": source}
