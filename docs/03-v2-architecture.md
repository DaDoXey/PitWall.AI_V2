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
| `/` | `(app)/page.tsx` | **Dashboard** (L4): scheda sessione, verdetto, cosa regge, note sui dati, 7 KPI con drag&drop · report da `lib/sessione.tsx` (`GET /api/sessions/{id}/analisi`) |
| `/telemetry` | `(app)/telemetry/page.tsx` | **Telemetria** (L4): tab Giri, Curve, Gomme e freni · report + `GET /api/sessions/{id}/tracce` |
| `/console` | `(app)/console/page.tsx` | **Console** di Gigi sulla sessione aperta: analisi a 5 sezioni, con il profilo pilota · `POST /api/analysis` |
| `/setup` | `(app)/setup/page.tsx` | **Setup**: 5 tab / 49 slider ACC, parametri indicati dal verdetto, setup grezzo della sessione, upload screenshot · `GET /api/catalog`, `/api/setup-params`, `/api/sessions/{id}`; `POST /api/setup/from-image` |
| `/sessioni` | `(app)/sessioni/page.tsx` | **Sessioni** (L4): percorso PC (import file, registratore), percorso console (sessione manuale con racconto), archivio |
| `/lezioni` · `/lezioni/[slug]` | `(app)/lezioni/…` | **A Lezione con Gigi**: indice e dettaglio, contenuti read-only da `lib/lessons.ts` |
| `/crediti` | `(app)/crediti/page.tsx` | Crediti delle immagini Wikimedia Commons: legge `public/assets/ATTRIBUTIONS.md` a build-time |
| `/login` | `(auth)/login/page.tsx` | Google Sign-In (popup) oppure modalità demo; profilo solo in `sessionStorage`, nessuna sessione server |

Le schede vettura/circuito (`SessionBriefing`) leggono `GET /api/catalog/car/{id}` e `/api/catalog/track/{id}`.

- **`components/ui/`**: `AuthGate`, `CountUp`, `GigiAvatar`, `GigiTour`, `MotionProvider`, `NavIcons`,
  `OnboardingFlow` (5 passi, il primo è la piattaforma), `PageHeader`, `Providers`, `QuickNotes`, `SessionBriefing`,
  `Sidebar` (selettore di sessione + verdetto in una riga), `SidebarSection`, `Tabs`, `UserChip`, `Verdetto`.
- **`components/charts/`**: `AnalisiCurve`, `GiriSessione`, `GommeFreni`, `PressureGauge`, `Sparkline`.
- **`lib/`**: `api.ts` (fetch client tipizzato sul report + `ApiError`), **`sessione.tsx`** (sessione aperta e report
  condivisi da tutte le pagine), **`formato.ts`** (solo formattazione: nessun conto), `auth.tsx`, `profile.tsx`,
  `theme.ts`, **`instrument.ts`** (token "analogici"), **`motion.ts`**, `catalog.ts` (liste di fallback),
  `console.ts`, `lessons.ts`, `setup.ts`.
- **Regola L4**: i conti li fa il motore di analisi nel backend; il frontend mostra.
- Asset visivi in `public/assets/` (**gitignorata**, ~33 MB): si rigenerano con gli script di `backend/scripts/`.

## 3 · Backend (`backend/app/`)
- **`main.py`** — FastAPI, CORS, 6 router sotto `/api`, middleware request-id. **`config.py`** — env server-side +
  presidio chiave (flag demo/live), cartella dei log. **`logging_config.py`** — log rotante con request-id (Entry #026).
  **`budget.py`** — tetto di spesa del ramo LLM: prenotazione al costo massimo e saldo al reale, per categoria
  (analisi/screenshot/chat) e per mese (Entry #028).
- **`api/`**: `sessions.py` (archivio, import, sessione manuale, analisi, tracce, riferimenti), `telemetria.py`,
  `analysis.py`, `setup.py`, `vision.py`, `catalog.py`.
- **`bundle/`**: `schema.py` (session bundle 1.1), `store.py`, `adapters/` (setup, risultati, telemetria),
  `demo.py` (sessione DEMO generata). **`telemetria/`**: shared memory di ACC, registratore, `banco.py` sintetico.
  **`analisi/`**: `motore.py`, `curve.py`, `gomme.py`, `gigi.py`. Dettaglio in `docs/04-rework-dati.md`.
- **`core/`** (⚠️ = protetto): ⚠️`agent.py` (client LLM: analisi a 5 sezioni con cascata + `chat_with_gigi`, non
  collegata), ⚠️`setup_params.py` (+ ⚠️`data/car_setup_ranges.json`), ⚠️`vision_parser.py`,
  ⚠️`prompts/` (`system_prompt_v5.txt`, `chat_system_prompt.txt`), ⚠️`demo_responses.py`, `riferimenti_fisica.py`
  (+ `data/acc_riferimenti_fisica_v19.json` Kunos e `acc_riferimenti_community.json`), `riferimenti_acc.py`,
  `catalog.py` + `data/cars.json` (31 GT3) e `data/tracks.json` (25 circuiti), `data/tracks_knowledge/` (guide: 8 su 25, al 23/09).
- **`tests/`**: 14 file, 751 test offline (elenco nei README).
- **`backend/scripts/`** (fuori da `app/`): pipeline delle immagini (foto, ritagli, mappe, crediti) e validatore delle guide.
- **`backend/logs/`** (gitignorata): `pitwall.log`, `llm_spesa.json`, e i registri `llm_token_log.md` / `llm_incidents.md`
  scritti da `agent.py`.

## 4 · Contratto API
- `GET /` → health `{status, service, version, demo_mode, live_allowed}`.
- Sessioni, analisi, tracce, telemetria e riferimenti: tabella nei README, formato in `docs/04-rework-dati.md`.
- `POST /api/analysis` body `{prompt, profile?, session_id?}` → `{question, text (5 sezioni md), source:
  demo|cache|motore|api|fallback}`. Live spento: sulla DEMO la cache per keyword (fuori perimetro → reindirizzo), sulle
  altre sessioni la risposta composta dal motore (`motore`). Live: `fallback` senza chiave, a tetto di spesa o con
  testo oltre 4000/1000 caratteri — cache sulla DEMO, motore sulle altre.
- `GET /api/setup-params?car&track` (entrambi opzionali) → 5 sezioni / 49 `Param{label,min,max,step,unit,default,tip}`.
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

## 6 · La sessione DEMO (`bundle/demo.py`, dal 16/09/2026)
`core/demo_data.py` non esiste più: la demo è una sessione generata e analizzata dallo stesso motore delle altre.
- Monza · BMW M4 GT3 · 8 giri di prove su asciutto · best **1:47.820** al giro 4 · 3.2 l/giro (25.6 l).
- Storia: posteriori sotto la finestra Kunos (media 25.4 / 25.2 psi), Post.DX oltre i 100 °C al core per il 38% del
  tempo (105 °C a fine stint), calo di 352 ms a giro dal giro 4.
- I numeri della cache di Gigi (`demo_responses.py`) sono quelli del report della demo: lo verifica `test_gigi.py`.
- Si alza `VERSIONE_GENERATORE` quando cambia il generatore: all'avvio la demo si rigenera.

## 7 · Verifica
- Frontend: `npx tsc --noEmit` **0 err** + rotte `/ /console /telemetry /setup /sessioni /lezioni /crediti /login` **200**.
- Backend: 14 file di test in `app/tests/`, **751** test, tutti offline.
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
