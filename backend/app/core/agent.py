"""
agent.py — PitWall.AI v2
Client LLM con system prompt v4.
Compatibile con il contesto esteso (setup completo + dati sessione + feedback).
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import anthropic

# Tetto di spesa (MUST #2, Entry #028): ogni chiamata prenota il costo massimo prima e salda il reale dopo.
from app import budget

log = logging.getLogger("pitwall.agent")


# ─────────────────────────────────────────────
# COSTANTI
# ─────────────────────────────────────────────
PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt_v4.txt"
REQUIRED_SECTIONS = ["## Diagnosi", "## Causa Meccanica", "## Correzione Setup", "## Note Aggiuntive"]


def get_env_var(name: str, default: str = "") -> str:
    """Recupera una variabile d'ambiente (os.getenv) con valore di default."""
    return os.getenv(name, default)


# INC-001: 2500 è il minimo sicuro per l'output completo a 4 sezioni.
MAX_OUTPUT_TOKENS = int(get_env_var("PITWALL_MAX_OUTPUT_TOKENS", "2500"))
MAX_INPUT_TOKENS  = int(get_env_var("PITWALL_MAX_INPUT_TOKENS", "8000"))

LOG_PATH    = get_env_var("PITWALL_PROMPT_LOG_PATH", "PROMPT_LOG.md")
INCIDENT_PATH = get_env_var("PITWALL_INCIDENTS_PATH", "INCIDENTS.md")

CLAUDE_MODEL = get_env_var("LLM_MODEL", "claude-haiku-4-5")

# Client Anthropic (Entry #030, dallo stress test dell'Entry #029). Con 30 s sonnet andava in timeout
# gia' con una domanda normale (29,0 s) e l'SDK ripeteva da solo ogni timeout 2 volte: 3x il tempo e
# una sola prenotazione del tetto di spesa per tre richieste. 90 s coprono 2500 token di sonnet; zero
# ripetizioni dell'SDK perche' il secondo tentativo lo fa gia' la cascata, passando dal tetto.
LLM_TIMEOUT_S = float(get_env_var("PITWALL_LLM_TIMEOUT_S", "90"))
LLM_MAX_RETRIES = 0



def estimate_tokens(text: str) -> int:
    return len(text) // 4


def check_context_size(context: str) -> tuple[bool, int]:
    estimated = estimate_tokens(context)
    return estimated <= MAX_INPUT_TOKENS, estimated


def log_token_usage(
    input_tokens_estimate: int,
    output_max_tokens: int,
    model: str,
    auto: str,
    tracciato: str,
    log_path: str = LOG_PATH,
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (
        "# PitWall.AI — PROMPT LOG\n\n"
        "| Timestamp | Auto | Tracciato | Token In (stima) | Token Out Max | Modello |\n"
        "|---|---|---|---|---|---|\n"
    )
    line = (
        f"| {timestamp} | {auto} | {tracciato} "
        f"| ~{input_tokens_estimate} | {output_max_tokens} | {model} |\n"
    )
    if not os.path.exists(log_path):
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(header)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)


def log_incident(description: str, incident_path: str = INCIDENT_PATH) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (
        "# PitWall.AI — INCIDENTS LOG\n\n"
        "| Timestamp | Descrizione |\n"
        "|---|---|\n"
    )
    line = f"| {timestamp} | {description} |\n"
    if not os.path.exists(incident_path):
        with open(incident_path, "w", encoding="utf-8") as f:
            f.write(header)
    with open(incident_path, "a", encoding="utf-8") as f:
        f.write(line)


def load_system_prompt() -> str:
    """Carica il system prompt dal file. Fallback su stringa minima se file mancante."""
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "Sei PitWall.AI, un Race Engineer virtuale per ACC. "
            "Rispondi con 4 sezioni: ## Diagnosi, ## Causa Meccanica Probabile, "
            "## Correzione Setup Consigliata, ## Note Aggiuntive."
        )


def validate_output(response: str) -> bool:
    """
    Verifica che l'output LLM contenga le 4 sezioni obbligatorie.
    """
    return all(section in response for section in REQUIRED_SECTIONS)


def call_claude(user_input: str, api_key: str, model_name: str) -> str:
    """Chiamata a Claude con un modello specifico."""
    system_prompt = load_system_prompt()
    # Solleva budget.BudgetEsaurito se il tetto non regge: get_ai_response lo tratta come un modello fallito.
    prenotazione = budget.prenota("analisi", model_name, system_prompt + user_input, MAX_OUTPUT_TOKENS)
    client = anthropic.Anthropic(api_key=api_key, base_url="https://api.anthropic.com",
                                 timeout=LLM_TIMEOUT_S, max_retries=LLM_MAX_RETRIES)
    message = client.messages.create(

        model=model_name,
        max_tokens=MAX_OUTPUT_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_input}],
    )
    budget.salda(prenotazione, message.usage)
    return message.content[0].text


def get_ai_response(
    user_input: str,
    api_key: str,
    auto: str = "",
    tracciato: str = "",
) -> str:
    """
    Ottieni risposta da Claude con retry logic e fallback su altri modelli Anthropic.
    """
    anthropic_key = api_key

    # Contesto sovradimensionato: si annota e si prosegue (il tetto di spesa e' il vero freno).
    context_ok, estimated_tokens = check_context_size(user_input)
    if not context_ok:
        log.warning("contesto oltre il massimo: ~%d token stimati (max %d)",
                    estimated_tokens, MAX_INPUT_TOKENS)

    errors = []

    # Lista ordinata di modelli Anthropic da provare in cascata in caso di errori (es. 404).
    # Ridotta a 2 per contenere il numero massimo di chiamate sincrone (evita il freeze).
    models_to_try = [
        CLAUDE_MODEL,          # 1. Modello configurato (default claude-haiku-4-5)
        "claude-sonnet-4-6",   # 2. Fallback qualità superiore
    ]


    # Rimuove duplicati mantenendo l'ordine
    unique_models = []
    for m in models_to_try:
        if m not in unique_models:
            unique_models.append(m)

    for idx, model in enumerate(unique_models):
        try:
            # Primo tentativo con questo modello
            response = call_claude(user_input, anthropic_key, model)
            if validate_output(response):
                # M3: un errore di I/O del log NON deve invalidare una risposta già valida
                # (altrimenti finirebbe nel except sotto → fallback a pagamento inutile).
                try:
                    log_token_usage(estimated_tokens, MAX_OUTPUT_TOKENS, model, auto, tracciato)
                except Exception:
                    pass
                return response

            # Secondo tentativo (retry) con lo stesso modello
            response = call_claude(user_input, anthropic_key, model)
            if validate_output(response):
                try:
                    log_token_usage(estimated_tokens, MAX_OUTPUT_TOKENS, model, auto, tracciato)
                except Exception:
                    pass
                return response
            
            errors.append(f"Modello {model}: Output generato ma incompleto (sezioni mancanti).")
        except Exception as exc:
            errors.append(f"Modello {model} fallito: {exc}")
            log_incident(f"Errore chiamata Claude ({model}): {exc}")

    # I dettagli tecnici restano solo negli incident log (già registrati sopra),
    # non vengono esposti all'utente finale.
    log_incident(f"Tutti i modelli Anthropic hanno fallito. Dettagli: {'; '.join(errors)}")

    return "⚠️ Servizio temporaneamente non disponibile. Riprova tra poco."


# ─────────────────────────────────────────────
# CHAT GIGI (aggiunta — canale conversazionale, separato dall'analisi a 4 sezioni)
# ─────────────────────────────────────────────
CHAT_PROMPT_PATH = Path(__file__).parent / "prompts" / "chat_system_prompt.txt"
CHAT_MAX_OUTPUT_TOKENS = int(get_env_var("PITWALL_CHAT_MAX_TOKENS", "800"))


def load_chat_system_prompt() -> str:
    """Carica il system prompt conversazionale di Gigi. Fallback minimo se assente."""
    try:
        return CHAT_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "Sei Gigi, ingegnere di pista virtuale per ACC GT3. Rispondi in chat "
            "in modo breve, diretto e tecnico, restando nei range reali di ACC."
        )


def chat_with_gigi(messages: list, api_key: str, context: str = "", model_name: str | None = None):
    """
    Generatore: invia la cronologia chat a Claude in streaming e fa yield dei
    chunk di testo. NESSUNA validazione a 4 sezioni.

    Args:
        messages: lista [{"role": "user"|"assistant", "content": str}, ...].
        api_key:  ANTHROPIC_API_KEY.
        context:  blocco contesto opzionale (ultima analisi, setup, dati sessione).
        model_name: override modello; default CLAUDE_MODEL.
    """
    model = model_name or CLAUDE_MODEL
    system_prompt = load_chat_system_prompt()
    if context.strip():
        system_prompt += f"\n\n[CONTESTO SESSIONE]\n{context.strip()}"

    client = anthropic.Anthropic(api_key=api_key, base_url="https://api.anthropic.com",
                                 timeout=LLM_TIMEOUT_S, max_retries=LLM_MAX_RETRIES)
    try:
        prenotazione = budget.prenota(
            "chat", model, system_prompt + "".join(str(m.get("content", "")) for m in messages),
            CHAT_MAX_OUTPUT_TOKENS,
        )
        with client.messages.stream(
            model=model,
            max_tokens=CHAT_MAX_OUTPUT_TOKENS,
            system=system_prompt,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
            budget.salda(prenotazione, stream.get_final_message().usage)
    except Exception as exc:
        log_incident(f"Errore chat Gigi ({model}): {exc}")
        yield (
            "⚠️ Ops, problema di collegamento col muretto. "
            "Controlla la API key o riprova tra poco."
        )
