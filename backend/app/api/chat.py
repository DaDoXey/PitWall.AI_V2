"""POST /api/sessions/{id}/chat — Gigi dal vivo alla radio della Console (Entry #061).

La conversazione con il modello, sulla sessione aperta. La risposta arriva in streaming
(testo semplice, pezzo per pezzo): è `agent.chat_with_gigi` (protetto, letto e mai
modificato), che passa dal tetto di spesa della categoria "chat".

Decisioni di Edoardo (30/09 e 01/10/2026):
* **interruttore suo**: `PITWALL_CHAT_LIVE=1` accende solo la chat. Rapporto completo e
  screenshot restano dove li mette `PITWALL_ALLOW_LIVE`; spenta di default (deploy
  pubblico: nessuno consuma la chiave);
* **limiti**: 12 domande del pilota a conversazione, gli ultimi 8 messaggi al modello,
  risposta di 800 token al massimo (`PITWALL_CHAT_MAX_TOKENS`, in agent.py);
* **contesto**: tutto quello che ha il Rapporto completo (report del motore, setup,
  racconto, profilo) più il debrief fase per fase, la fase che il pilota sta ascoltando
  e i click della vettura (`analisi/gigi.contesto_chat`).

Quando la chat non può rispondere lo dice con uno status e un `detail` già scritto per
il pilota: 503 spenta o senza chiave, 429 tetto di spesa finito, 409 conversazione piena.
Nel log mai il testo del pilota: solo lunghezze (decisione del 10/09).
"""

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app import budget, config
from app.analisi import analizza
from app.analisi.debrief import TagliNonValidi, debrief
from app.analisi.gigi import contesto_chat
from app.bundle import demo, store
from app.bundle.adapters import canali_del_bundle
from app.core.setup_params import regole_vettura

router = APIRouter()
log = logging.getLogger("pitwall.chat")

MAX_DOMANDE = 12              # domande del pilota in una conversazione
MAX_MESSAGGI_AL_MODELLO = 8   # la coda della conversazione che il modello rilegge
MAX_CARATTERI_DOMANDA = 1000
MAX_CARATTERI_PROFILO = 1000  # come nell'analisi (Entry #028)


class MessaggioChat(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)


class RichiestaChat(BaseModel):
    messages: list[MessaggioChat] = Field(min_length=1, max_length=4 * MAX_DOMANDE)
    fase: int | None = None        # indice della fase del debrief in ascolto
    profile: str | None = None


def _coda(messaggi: list[MessaggioChat]) -> list[dict]:
    """Gli ultimi messaggi per il modello: ruoli alternati, e si comincia dal pilota."""
    uniti: list[dict] = []
    for m in messaggi:
        if uniti and uniti[-1]["role"] == m.role:
            uniti[-1]["content"] += "\n" + m.content
        else:
            uniti.append({"role": m.role, "content": m.content})
    coda = uniti[-MAX_MESSAGGI_AL_MODELLO:]
    while coda and coda[0]["role"] != "user":
        coda.pop(0)
    return coda


@router.post("/sessions/{id_sessione}/chat")
def chat_sessione(id_sessione: str, corpo: RichiestaChat):
    if not config.chat_live() or not config.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="Gigi dal vivo è spento: usa le domande preparate.")

    ultimo = corpo.messages[-1]
    if ultimo.role != "user":
        raise HTTPException(status_code=422, detail="L'ultimo messaggio deve essere del pilota.")
    if len(ultimo.content) > MAX_CARATTERI_DOMANDA:
        raise HTTPException(status_code=422,
                            detail=f"Domanda troppo lunga: al massimo {MAX_CARATTERI_DOMANDA} caratteri.")
    if len(corpo.profile or "") > MAX_CARATTERI_PROFILO:
        raise HTTPException(status_code=422, detail="Profilo del pilota troppo lungo.")
    domande = sum(1 for m in corpo.messages if m.role == "user")
    if domande > MAX_DOMANDE:
        raise HTTPException(status_code=409,
                            detail=f"Conversazione piena ({MAX_DOMANDE} domande): aprine una nuova.")

    if demo.e_demo(id_sessione):
        demo.assicura_demo()
    try:
        bundle = store.leggi(id_sessione)
    except store.SessioneNonTrovata:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    except store.ArchivioError as e:
        raise HTTPException(status_code=400, detail=str(e))

    report = analizza(bundle, canali_del_bundle(bundle))
    try:
        fasi = debrief(report, bundle.fasi_tagli)
    except TagliNonValidi:
        fasi = debrief(report)
    contesto = contesto_chat(report, bundle, fasi, corpo.fase, corpo.profile,
                             regole_vettura(report.car))
    coda = _coda(corpo.messages)

    from app.core import agent

    # Lo stesso testo che agent.chat_with_gigi prenota: se il tetto non lo regge lo si
    # dice ora, con uno status. A streaming cominciato resterebbe solo il messaggio
    # generico di agent.py («problema di collegamento»), che al pilota direbbe il falso.
    da_prenotare = (agent.load_chat_system_prompt() + f"\n\n[CONTESTO SESSIONE]\n{contesto.strip()}"
                    + "".join(m["content"] for m in coda))
    if not budget.regge("chat", agent.CLAUDE_MODEL, da_prenotare, agent.CHAT_MAX_OUTPUT_TOKENS):
        log.warning("chat di %s: tetto di spesa raggiunto, nessuna chiamata", id_sessione)
        raise HTTPException(status_code=429,
                            detail="Per oggi il tetto di spesa della chat è finito: restano le domande preparate.")

    log.info("chat di %s: domanda %d di %d, %d caratteri, %d messaggi al modello, contesto %d caratteri",
             id_sessione, domande, MAX_DOMANDE, len(ultimo.content), len(coda), len(contesto))
    chat_with_gigi = agent.chat_with_gigi

    return StreamingResponse(
        chat_with_gigi(coda, api_key=config.ANTHROPIC_API_KEY, context=contesto),
        media_type="text/plain; charset=utf-8",
        # Niente buffer fra il modello e la pagina: il testo deve arrivare mentre si scrive.
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )
