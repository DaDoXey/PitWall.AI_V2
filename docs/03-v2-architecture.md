# PitWall.AI v2 — Architettura as-built

> **Stato documentato:** 11/09/2026, dopo l'Entry #028 (tetto di spesa del ramo LLM) · build post-esame.
> Riallineato al codice l'11/09: la versione precedente fotografava il 10/07 (fine megaprompt #2, `ed18898`).
> Completa i doc di planning `00`/`01`/`02` (che descrivono la *sorgente* v1 e la *decisione* di stack):
> questo file fotografa la v2 **com'è realmente costruita**. Per la cronologia → `PROMPT_LOG.md`;
> per i malfunzionamenti gravi → `INCIDENTS.md`.

## 1 · Stack & runtime
| Layer | Tech | Versione |
|---|---|---|
| Frontend | Next.js (App Router) / React | 15.5.20 / 19.0 |
| | TypeScript / Tailwind | 5.7 / 3.4 |
| | Recharts / Framer Motion | 2.15 / 11.15 |
| Backend | Python / FastAPI / Uvicorn | 3.12 / 0.115 / 0.34 |
| | Anthropic SDK / Pandas / Pydantic | 0.113 / 3.0 / 2.10 |
| LLM (Gigi) | analisi: `claude-haiku-4-5` (env `LLM_MODEL`), fallback `claude-sonnet-4-6` · screenshot: `claude-sonnet-4-6` | |

**Avvio dev:** `cd backend && ./.venv/Scripts/python -m uvicorn app.main:app` (:8000, **senza `--reload`**:
HAZARD-V2-B) + `cd frontend && npm run dev` (:3000). Health `GET :8000/` →
`{status:"ok", demo_mode:true, live_allowed:false}`.

## 2 · Frontend (`frontend/src/`)
**Layout** (i route group non entrano negli URL):
- **`app/layout.tsx`** — root: font (Orbitron/Inter/JetBrains Mono), `globals.css`, `Providers` (Google OAuth + stato di accesso).
- **`app/(app)/layout.tsx`** — app "loggata": `AuthGate` (senza accesso → `/login`) → `Sidebar` + `<main>` con
  `MotionProvider` (`<MotionConfig reducedMotion="user">`); in più `OnboardingFlow` (wizard "Conosci il pilota" al
  primo accesso) e `GigiTour`.
- **`app/(auth)/layout.tsx`** — senza Sidebar, card centrata (fix INC-V2-004).

**Pagine:**
| Rotta | File | Cosa fa · API |
|---|---|---|
| `/` | `(app)/page.tsx` | **Dashboard**: card KPI con drag&drop, ordine e taglie in `localStorage` · `GET /api/session` |
| `/telemetry` | `(app)/telemetry/page.tsx` | **Telemetria**: grafici, heatmap, gauge, tabelle giro · `GET /api/session` |
| `/console` | `(app)/console/page.tsx` | **Console** di Gigi: domanda → analisi a 4 sezioni, con il profilo pilota del wizard · `POST /api/analysis` |
| `/setup` | `(app)/setup/page.tsx` | **Setup**: 5 tab / 49 slider ACC, selettori vettura/circuito, upload CSV e screenshot · `GET /api/catalog`, `/api/setup-params`, `/api/session`; `POST /api/csv/parse`, `/api/setup/from-image` |
| `/lezioni` · `/lezioni/[slug]` | `(app)/lezioni/…` | **A Lezione con Gigi**: indice e dettaglio, contenuti read-only da `lib/lessons.ts` |
| `/crediti` | `(app)/crediti/page.tsx` | Crediti delle immagini Wikimedia Commons: legge `public/assets/ATTRIBUTIONS.md` a build-time |
| `/login` | `(auth)/login/page.tsx` | Google Sign-In (popup) oppure modalità demo; profilo solo in `sessionStorage`, nessuna sessione server |

Le schede vettura/circuito (`SessionBriefing`) leggono `GET /api/catalog/car/{id}` e `/api/catalog/track/{id}`.

- **`components/ui/`**: `AlertsFeed`, `AuthGate`, `CountUp`, `GigiAdvice`, `GigiAvatar`, `GigiTour`, `HealthStatus`,
  `MotionProvider`, `NavIcons`, `OnboardingFlow`, `PageHeader`, `Providers`, `QuickNotes`, `SessionBriefing`,
  `SessionHealth`, `Sidebar`, `SidebarSection`, `Tabs`, `UserChip`.
- **`components/charts/`**: `ChannelReport`, `LapChannelBars`, `LapDeltaChart`, `LapTable`, `LapTimesTable`,
  `PressureGauge`, `ScatterPlot`, `SetupRadar`, `Sparkline`, `StintCompare`, `TelemetryLanes`, `TyreHeatmap`,
  `TyreSnapshotGrid`.
- **`lib/`**: `api.ts` (fetch client + `ApiError`), `auth.tsx`, `profile.tsx`, `theme.ts`, **`instrument.ts`** (token
  "analogici": STATE ok/warn/alarm/cold, INSTRUMENT grid/track/tick/ink, STROKE hairline/tick/needle), **`motion.ts`**
  (`fadeInUp`/`stagger`/`cardHover`, `EASE`, `DUR`), `advice.ts`, `catalog.ts` (liste di fallback se il backend non
  risponde), `console.ts`, `crosscheck.ts`, `health.ts`, `lessons.ts`, `setup.ts`, `telemetry.ts`.
- Asset visivi in `public/assets/` (**gitignorata**, ~33 MB): si rigenerano con gli script di `backend/scripts/`.

## 3 · Backend (`backend/app/`)
- **`main.py`** — FastAPI, CORS, 6 router sotto `/api`, middleware request-id. **`config.py`** — env server-side +
  presidio chiave (flag demo/live), cartella dei log. **`logging_config.py`** — log rotante con request-id (Entry #026).
  **`budget.py`** — tetto di spesa del ramo LLM: prenotazione al costo massimo e saldo al reale, per categoria
  (analisi/screenshot/chat) e per mese (Entry #028).
- **`api/`**: `session.py`, `analysis.py`, `setup.py`, `csv.py`, `vision.py`, `catalog.py`.
- **`core/`** (⚠️ = protetto): ⚠️`agent.py` (client LLM: analisi con cascata + `chat_with_gigi`, non collegata),
  ⚠️`csv_parser.py`, ⚠️`setup_params.py` (+ ⚠️`data/car_setup_ranges.json`), ⚠️`vision_parser.py`,
  ⚠️`prompts/` (`system_prompt_v4.txt`, `chat_system_prompt.txt`), `demo_data.py` e `demo_responses.py` (⚠️ i numeri),
  `catalog.py` + `data/cars.json` (31 GT3) e `data/tracks.json` (25 circuiti), `data/tracks_knowledge/` (guide dei
  tracciati: 4 su 25).
- **`tests/`**: `test_parser.py`, `test_observability.py`, `test_budget.py`.
- **`backend/scripts/`** (fuori da `app/`): pipeline delle immagini (foto, ritagli, mappe, crediti) e validatore delle guide.
- **`backend/logs/`** (gitignorata): `pitwall.log`, `llm_spesa.json`, e i registri `llm_token_log.md` / `llm_incidents.md`
  scritti da `agent.py`.

## 4 · Contratto API
- `GET /` → health `{status, service, version, demo_mode, live_allowed}`.
- `GET /api/session` → `{ session, tyre_labels, temp{series,max,limit,scale}, pressure{hot,hot_window,hot_series,cold,cold_window,cold_amber_margin,avg_hot}, fuel_per_lap, lap_times, laps, suggested_params }`.
- `POST /api/analysis` body `{prompt, profile?}` → `{question, text (4 sezioni md), source: demo|cache|api|fallback}`.
  In demo-mode: sempre cache, routing per keyword, domande fuori perimetro → risposta di reindirizzo. In live:
  `fallback` anche senza chiave, a tetto di spesa raggiunto o con testo oltre 4000/1000 caratteri (prompt/profilo).
- `GET /api/setup-params?car&track` (entrambi opzionali) → 5 sezioni / 49 `Param{label,min,max,step,unit,default,tip}`.
- `POST /api/csv/parse` (multipart) → `CsvResult` (400 se CSV invalido).
- `POST /api/setup/from-image` (multipart) → `{params,summary,…}` (503 in demo-mode, 503 se manca la key server,
  429 a tetto di spesa raggiunto, 500 se la lettura fallisce).
- `GET /api/catalog` → indice di vetture e circuiti · `GET /api/catalog/car/{car_id}` e `/api/catalog/track/{track_id}`
  → scheda completa (accettano slug, id ACC, nome o alias; 404 se non trovati).
- Ogni risposta porta l'header `X-Request-ID`.

## 5 · Presidio API key
`ANTHROPIC_API_KEY` vive **solo lato server**. Con `PITWALL_ALLOW_LIVE=0` (default, e forzato sul deploy
pubblico) si serve la **cache demo** offline → la chiave non si consuma mai e non finisce nel bundle JS.
La LLM reale si abilita con `PITWALL_ALLOW_LIVE=1` + `PITWALL_DEMO_MODE=0` + chiave nei secret del server; lo
stesso presidio vale per la lettura screenshot (Entry #027).
Acceso il live, ogni chiamata passa da `budget.prenota()` / `budget.salda()` (agganci in `agent.py` e
`vision_parser.py`): tetti `PITWALL_BUDGET_{ANALISI,SCREENSHOT,CHAT}_GIORNO` + `PITWALL_BUDGET_MESE`.

## 6 · Invarianti dati demo (`core/demo_data.py`) — da preservare
Sorgente unica dei numeri per la coerenza cross-schermata:
- Sessione: Monza · BMW M4 GT3 (modello 2021) · 8 giri · best **1:47.812** (= minimo di `LAP_TIMES`, controllato
  all'import) · ~3.2 L/giro (25.6 L totali). Caso didattico: **retrotreno scarico** (Post.DX a 105°C).
- **Temp max = ultimo valore della serie** (88/90/95/105°C; limite 95°C; scala heatmap 80–105).
- **Pressioni a caldo = ultimo giro di `HOT_PRESS_SERIES` = gauge** (controllato all'import): 26.5/26.7/25.7/25.5 psi,
  media 26.1; finestra a caldo **26.0–27.0**.
- **Pressioni a freddo**: 25.0/25.2/24.2/24.0 psi; finestra a freddo **24.5–25.5** (margine ambra 0.6). I posteriori
  stanno sotto finestra: è la causa della storia demo.
- **Freddo e caldo mai mescolati**; delta freddo→caldo **+1.5 psi** uniforme. Stessi valori in
  `prompts/system_prompt_v4.txt` e `prompts/chat_system_prompt.txt` (vedi `SPEC_ERRATA.md` ERR-02).
- Parametri suggeriti da Gigi (evidenziati negli slider): `tire_press_rl`, `tire_press_rr`, `preload`.

## 7 · Verifica
- Frontend: `npx tsc --noEmit` **0 err** + rotte `/ /console /telemetry /setup /lezioni /crediti /login` **200**.
- Backend: `./.venv/Scripts/python app/tests/test_parser.py` → **12/12** · `test_observability.py` → **24/24** ·
  `test_budget.py` → **30/30** (tutti offline).
- **Mai** `npm run build` con `npm run dev` attivo (corrompe `.next`, HAZARD-V2-A).

## 8 · Deploy (da decidere)
Nessun workflow nel repo. L'ipotesi dei doc di planning era frontend → **Vercel**, backend → **Render/Railway/Fly**.
- Frontend: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_GOOGLE_CLIENT_ID`.
- Backend: secret `ANTHROPIC_API_KEY`, `PITWALL_ALLOW_LIVE`, `PITWALL_DEMO_MODE`, `PITWALL_BUDGET_*`,
  `PITWALL_CORS_ORIGINS` (origine del frontend).
- Da tenere presente: le immagini non sono versionate (serve `apply_photos.py`); su un disco effimero
  `backend/logs/llm_spesa.json` si perde a ogni riavvio, e con lui la spesa del giorno e del mese.

## 9 · Note aperte (vedi `INCIDENTS.md`)
- **Unico incidente aperto:** INC-V2-003, override di `car_setup_ranges.json` no-op (la vettura non cambia i 49 parametri).
- LLM reale **mai acceso**: manca lo stress test.
- `chat_with_gigi()` non è collegata a nessuna rotta né a una UI.
- `api/vision.py` è `async` ma chiama il parser sincrono: blocca l'event loop per tutta la chiamata al modello.
- `agent.py:134` ha ancora `import streamlit` (non installato): dall'Entry #028 non è raggiungibile dall'API.
- Tetto di spesa: il lucchetto è per un solo processo (con più worker servirebbe un lock su file).
- Mappe dei circuiti: 5 layout su 25 verificati, nessuna pagina le mostra.
