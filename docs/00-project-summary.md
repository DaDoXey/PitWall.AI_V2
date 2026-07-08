# PitWall.AI — Sunto completo del progetto (base per la migrazione)

> **Scopo di questo documento.** Fotografia dettagliata di TUTTO il progetto attuale
> (Streamlit), da usare come fondamenta per la **v2** (nuovo stack). Redatto il **08/07/2026**
> rivedendo l'intero codice. Da qui deriveremo la nuova documentazione e segneremo le nuove scelte.
> Stato attuale del codice: `main == restyle-ui == origin` a `d41aa5a`, `test_parser` 12/12.

---

## 1 · Cos'è PitWall.AI

**Virtual Race Engineer** per **Assetto Corsa Competizione (ACC), classe GT3**. Il pilota
descrive un problema di guida/setup in linguaggio naturale; l'app risponde come un ingegnere di
pista ("Gigi") con un'**analisi tecnica a 4 sezioni** (Diagnosi · Causa Meccanica · Correzione
Setup · Note), vincolata ai range reali di ACC. Attorno c'è un cruscotto che mostra la telemetria
di sessione (temperature/pressioni gomme, consumo) e un editor di setup completo.

- **Target:** sim-racer amatoriali/competitivi senza competenze avanzate di ingegneria.
- **Autore:** Edoardo Ferlito (progetto d'esame ITS ICT Academy Roma). Lingua: italiano.
- **Principio guida:** modifiche **incrementali** (mai un setup da zero), numeriche, dentro i range ACC.
- **Storia demo "blindata":** a **Monza**, la **BMW M4 GT3** surriscalda la **Post.DX (105°C)** per
  **pressioni posteriori troppo basse** → caso didattico "retrotreno scarico / sovrasterzo in trazione".

## 2 · Stack attuale & deploy

| Aspetto | Valore |
|---|---|
| Linguaggio | Python 3 |
| UI | **Streamlit 1.58** (web app) |
| LLM | **Anthropic** `anthropic==0.113`; default `claude-haiku-4-5`, fallback `claude-sonnet-4-6` |
| Grafici | **Plotly 6.8** (line chart + gauge); SVG inline fatti a mano (sparkline, heatmap, avatar) |
| Dati | **pandas 3.0** (parsing CSV); dati demo hardcoded |
| DB | **SQLite** (auth + storico sessioni predisposto) |
| Deploy | **Streamlit Community Cloud** su branch `main`; `.streamlit/config.toml` tema dark |
| Auth | Mock SQLite (dev) + **placeholder** Google OAuth (prod, non attivo) |

**Deps totali (`requirements.txt`):** streamlit, anthropic, python-dotenv, pandas, plotly. Molto snello.

## 3 · Architettura (mappa file)

```
app.py                    # entry Streamlit: load_dotenv → design system → gate auth → router
pages/login.py            # schermata login (mock quick-login + Google placeholder)
ui/                       # PACKAGE DI PRESENTAZIONE (restyle) — chiama la logica, non la riscrive
  router.py               # dispatch pagina via st.session_state["page"]
  nav.py                  # PAGES + icone + go_to() (no import delle pagine → niente cicli)
  sidebar.py              # logo, nav, box "sessione attiva", logout
  dashboard.py            # schermata 1
  telemetry.py            # schermata 2 (cuore visivo)
  console.py              # schermata 3 (Gigi, analisi 4 sezioni + demo-cache)
  setup_view.py           # schermata 4 (5 tab ACC di slider)
  demo_data.py            # ★ SORGENTE DATI DEMO UNICA (tutti i numeri coerenti)
  components.py           # builder SVG/HTML inline + token colore + font iframe
  flags.py                # feature-flag (demo_mode / live / inputs / screenshot)
  catalog.py              # liste auto/piste/condizioni (presentazione)
assets/                   # design system: css_loader.py, app.css, design_system.css, font base64
styles/login.css          # CSS dedicato al login
agent.py                  # ★ CLIENT LLM (system prompt v4, retry+fallback, logging)  [PROTETTO]
prompts/system_prompt_v4.txt   # ★ "cervello": ruolo, metodo 3 passi, range ACC, output 4 sez  [PROTETTO]
prompts/chat_system_prompt.txt # prompt chat "Gigi" (canale conversazionale)
modules/setup_params.py   # ★ range/default/unit dei 49 parametri ACC + override per-vettura  [PROTETTO-adiacente]
modules/vision_parser.py  # lettura setup da screenshot via Claude Vision (feature-flag, OFF)
backend/parser/csv_parser.py   # ★ parsing/validazione CSV sessione ACC (12/12 test)  [PROTETTO]
backend/database/manager.py    # SessionDatabase SQLite (storico sessioni, oggi non agganciato all'UI)
backend/tests/test_parser.py   # baseline test (deve restare 12/12)
db_auth.py, auth_config.py     # auth SQLite (users) + strategia dev/prod
data/car_setup_ranges.json     # override range per specifiche vetture
app_legacy.py             # MONOLITE originale (1529 righe) preservato VERBATIM, non importato dall'UI
```

**Flusso:** `app.py` inietta il design system (font base64 + token + tema), controlla
`st.session_state.authenticated` (redirect a `pages/login.py`), poi `ui/router.py` renderizza la
pagina scelta. Le pagine leggono i numeri da `ui/demo_data.py` e, per l'analisi, **chiamano**
`agent.get_ai_response` (o servono la cache demo). Nessuna pagina riscrive la logica protetta.

## 4 · Le 4 schermate (dettaglio funzionale)

### 4.1 Dashboard (`ui/dashboard.py`)
Hero "ultima sessione" (Monza · BMW M4 GT3 · 8 giri · best 1:47.812 · 3.2 L/giro) + 3 **card
metriche** (Temperatura gomme con sparkline+limite 95°C; Pressione media 28.6 psi con window-bar;
Consumo con sparkline) + card "Chiedi a Gigi". Bottoni nativi che navigano: Temp→Telemetria,
Pressione→Setup, Consumo/Gigi→Console. Le card sono HTML/SVG dentro `components.html` (iframe).

### 4.2 Telemetria (`ui/telemetry.py`) — cuore visivo
1. **Line chart Plotly**: temperatura 4 gomme su 8 giri + linea limite 95°C; toggle °C/°F e "smoothed".
2. **Heatmap SVG**: sagoma auto vista dall'alto, 4 riquadri-gomma colorati blu→rosso sul max stint.
3. **4 gauge Plotly**: pressioni a caldo, finestra verde 28.5–30.0 psi, badge "in finestra/bassa".
4. **Tabella giro-per-giro** ordinabile (consumo + 4 temp + 4 press a caldo).
5. **Proiezione giri rimanenti** (sola lettura: carburante residuo / consumo medio).
6. **Cross-check** deterministico (temp oltre limite, press fuori finestra, consumo stabile) + riuso
   della diagnosi di Gigi (nessuna nuova chiamata LLM).

### 4.3 Engineer Console (`ui/console.py`) — Gigi
Header Gigi (avatar SVG, "online") + toggle **Demo-mode** + 4 quick-chip (Sottosterzo, Carburante,
Gomme, Freni) + input libero con bottone **⚙ ANALIZZA** (dentro `st.form` → nessun submit su blur).
L'output a 4 sezioni viene **parsato** (`parse_sections`, robusto: sezione mancante = card degradata)
e reso come 4 card numerate; la "Correzione" è evidenziata come "SCHEDA SETUP". **Demo-mode** serve
sempre una **risposta cache** pre-validata: 5 scenari (`DEMO_RESPONSE`/UNDERSTEER/FUEL/TYRES/BRAKES)
scelti per keyword → la demo risponde davvero all'input **senza rete**. Con live-mode ON e API key
presente, chiama `agent.get_ai_response`; se l'output non ha le 4 sezioni → fallback alla cache.

### 4.4 Setup (`ui/setup_view.py`)
5 tab ACC (Gomme, Elettronica, Meccanica, Ammortizzatori, Aero) con **slider funzionali** per i **49
parametri**; range/default/unit/tooltip vengono da `modules.setup_params.get_params_for_car(car, track)`
(override per vettura da `data/car_setup_ranges.json`). Le **4 pressioni** si colorano vs finestra a
freddo (verde 26.0–27.0 / ambra ±0.6 / rosso). I parametri suggeriti da Gigi si evidenziano in rosso.
Dietro feature-flag (OFF in demo): selettori auto/pista/condizioni, upload CSV (→ `csv_parser`),
upload screenshot (→ `vision_parser`, stub "Prossimamente"). Rake calcolato e mostrato (informativo).

## 5 · Modello dati demo (`ui/demo_data.py`) — sorgente unica

Tutti i numeri della demo stanno **qui** per garantire coerenza cross-schermata. Elementi chiave:
- `SESSION`: Monza, BMW M4 GT3, 8 giri, best 1:47.812, 3.2 L/giro, 25.6 L totali.
- `TYRE_TEMP_SERIES` (8 valori/gomma); `TYRE_TEMP_MAX` derivato (**88/90/95/105**); limite 95°C.
- `HOT_PRESSURES` (a caldo, gauge): FL 29.0 / FR 29.2 / RL 28.2 / RR 28.0; finestra 28.5–30.0.
- `COLD_PRESSURES` (a freddo, garage): FL 26.5 / FR 26.5 / RL 25.7 / RR 25.5; finestra 26.0–27.0.
- `HOT_PRESS_SERIES`: pressioni a caldo giro-per-giro; **l'ultimo giro coincide con `HOT_PRESSURES`**
  (invariante verificata a import con `raise ValueError`).
- `PRESS_AVG_HOT` = 28.6; `FUEL_PER_LAP` (8 valori ~3.2); `SUGGESTED_PARAMS` (evidenziati nel Setup).
- **Invarianti di coerenza** (da preservare nella v2): temp max = ultimo valore serie; press a caldo
  ultimo giro = gauge; distinzione **freddo vs caldo** mai mescolata; delta cold→hot ~+2.5 psi.

## 6 · La logica di dominio (il valore da conservare)

### 6.1 `agent.py` — client LLM  [PROTETTO]
- `get_env_var` legge da `st.secrets` (Cloud) o `os.getenv` (locale).
- `get_ai_response`: prova `claude-haiku-4-5` poi fallback `claude-sonnet-4-6`, 1 retry ciascuno,
  timeout 30s, `max_tokens=2500`; **valida** che l'output contenga le 4 sezioni; logga token usage
  (ora in `try/except` — HOTFIX-5 M3) e incidenti. Restituisce testo o messaggio d'errore gentile.
- Contratto output: 4 sezioni Markdown `## Diagnosi / ## Causa Meccanica / ## Correzione Setup / ## Note Aggiuntive`.

### 6.2 `prompts/system_prompt_v4.txt` — il "cervello"  [PROTETTO]
Ruolo Senior Race Engineer GT3; **metodo obbligatorio a 3 passi** (Diagnosi→Causa→Correzione);
**range di sicurezza ACC completi** per ogni parametro (pressioni, camber, toe, caster, TC/ABS/ECU/
brake bias, ARB, wheel/bumpstop rate/range, precarico, dampers 0–11, ride height, splitter/wing/duct);
note tecniche (rake, dampers slow/fast, bumpstop, **pressioni freddo↔caldo**); **formato output a 4
sezioni** rigido; vincoli DO/DON'T (max 2–3 parametri per risposta, no parametri inesistenti, no giudizi
sul pilota, chiedi chiarimenti se vago). **Questo file è il know-how di dominio: va riusato tale e quale.**

### 6.3 `modules/setup_params.py` — 49 parametri ACC  [PROTETTO-adiacente]
5 sezioni × dict `{label,min,max,step,unit,default,tip}`. Funzioni: `get_all_params_flat`,
`validate_setup`, `format_setup_for_prompt`, `_load_car_db`/`_apply_param_overrides`,
`get_params_for_car(car,track)` (override da `data/car_setup_ranges.json`, fallback generico).

### 6.4 `backend/parser/csv_parser.py` — parsing CSV  [PROTETTO]
Schema: obbligatorie `lap,fuel_cons`; opzionali 4 press + 4 temp. Valida schema/tipi/range, estrae
medie e serie, ritorna dict strutturato o `CSVParseError`. Difensivo (12/12 test). NON fa chiamate LLM.

### 6.5 `modules/vision_parser.py` — setup da screenshot
Claude Vision (`VISION_SYSTEM_PROMPT`, OCR→JSON dei 49 parametri), poi validazione/clamp nei range.
Feature-flag OFF (stub "Prossimamente" in UI). Riusabile nella v2 come endpoint.

## 7 · Auth & sessione utente
- `pages/login.py`: hero + **Quick Login DEV** (Demo Pilot / Custom User) + bottone Google **placeholder**
  (non interattivo finché `is_oauth_configured()` è False). Al login pre-seed delle pressioni retro a
  freddo (coerenza storia). `db_auth.create_or_update_user` (upsert per email UNIQUE, preserva created_at).
- `auth_config.py`: strategia `dev` (mock) / `prod` (oauth da env `GOOGLE_CLIENT_ID/SECRET`, `STREAMLIT_ENV`).
- `backend/database/manager.py`: `SessionDatabase` SQLite per storico sessioni — **predisposto ma non
  agganciato** all'UI restyle (RF-04 futuro; nota thread-safety: connessione condivisa senza lock).

## 8 · Feature-flag & variabili d'ambiente (`ui/flags.py`, `.env.example`)
- `PITWALL_DEMO_MODE` (default ON): cache offline sempre → la demo non si rompe.
- `PITWALL_ALLOW_LIVE` (default 0): sul deploy pubblico la demo-mode è **forzata ON** → protegge la MIA
  API key da estranei. A 1 (locale/secrets) sblocca il toggle e la LLM reale.
- `PITWALL_SHOW_INPUTS` (0): mostra selettori/upload nel Setup. `FEATURE_SCREENSHOT` (0): vision reale.
- `LLM_MODEL`, `PITWALL_MAX_OUTPUT_TOKENS=2500`, `PITWALL_MAX_INPUT_TOKENS`, `PITWALL_CHAT_MAX_TOKENS`,
  `PITWALL_DB_PATH`, `PITWALL_PROMPT_LOG_PATH`, `PITWALL_INCIDENTS_PATH`, `ANTHROPIC_API_KEY`.

## 9 · Vincoli & guardrail (validi anche per la v2)
- **File protetti** (fonte di verità): `agent.py`, `csv_parser.py`, i due system prompt,
  `setup_params.py`, logica gauge/fuel, i **numeri** di `demo_data.py`. Regola: STOP gate + «ok procedi».
- **Demo-mode protegge la API key** sul deploy pubblico: la v2 dovrà avere lo stesso presidio
  (chiave solo lato server, mai esposta al client; rate-limit/allowlist per la LLM reale).
- **Coerenza numeri** cross-schermata (invarianti §5): da mantenere per costruzione.
- Git: niente commit/push senza «ok push»; tooling `.claude/` locale.

## 10 · Cosa TENERE vs cosa RIFARE nella v2

**Da tenere (riuso diretto, è il valore):**
- `system_prompt_v4.txt` (+ chat prompt) — know-how di dominio.
- `agent.py` (client LLM, contratto 4 sezioni, retry/fallback/validazione).
- `csv_parser.py` (parser testato 12/12) e `setup_params.py` (49 param + override) + `car_setup_ranges.json`.
- `vision_parser.py` (screenshot→params).
- Il **modello dati demo** e le sue invarianti (§5) — diventeranno il seed/fixtures dell'API.
- Le risposte cache demo (5 scenari) — utili per la demo offline anche nella v2.

**Da rifare (è la parte che frena e che vogliamo "ancora meglio"):**
- **Tutto lo strato di presentazione Streamlit**: iframe `components.html`, HTML/SVG inline stringati,
  font base64, il fight col CSS (no wildcard) e col clipping degli iframe. Qui nasce la nuova UI.
- Navigazione/stato via `st.session_state` → stato applicativo vero (routing client + store).
- Gauge/heatmap/sparkline fatti a mano in stringhe → **componenti** riutilizzabili e animati.

## 11 · Domande aperte per la v2 (da decidere nel planning)
- Deploy: dove gira il backend Python e il frontend? (free tier: Vercel + Render/Railway/Fly).
- Autenticazione reale (Google OAuth) ora o dopo?
- Storico sessioni SQLite: agganciarlo davvero (multi-utente → risolvere thread-safety)?
- Import dati reali (CSV/telemetria) come feature di primo piano vs demo-mode?
- Grado di "wow" visivo desiderato (animazioni, 3D della vettura, live telemetry feel).

---

*Prossimo documento: `01-target-stack.md` (scelta stack motivata) e `02-repo-strategy.md` (repo nuova).*
