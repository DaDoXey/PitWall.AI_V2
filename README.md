**English** | [Italiano](README.it.md)

# PitWall.AI_V2

A virtual race engineer for Assetto Corsa Competizione (ACC). It reads sessions from the game's
files and from MoTeC, works out where time is lost corner by corner and names the first thing to
change. The numbers come from a verifiable engine; a language model tells them over the radio.
Born in the AI & Digital Innovation Specialist course.

> **v2** of the PitWall.AI web app: a migration from Streamlit to **Next.js + FastAPI**. It reuses
> the v1 domain logic (LLM client, ACC ranges, vision) behind a clean API, with a rich
> React UI.

## Current status
**Final exam passed on 15/07/2026**, with the demo running in demo mode. The **full build** is now
under way: taking PitWall from a demo to a product, with a real LLM underneath.

The LLM client is already implemented: a 5-section validated analysis, with retries and a model
cascade, switched on with `PITWALL_ALLOW_LIVE=1` + `PITWALL_DEMO_MODE=0` + the API key. The client
also contains a streaming chat for Gigi, served by `POST /api/sessions/{id}/chat` behind its own
switch (`PITWALL_CHAT_LIVE=1`, off by default). Every model call goes
through a daily and monthly **spending cap**. **The real LLM stays off by default**: it is switched
on by choice, after the first stress test in September (see Roadmap).

Iteration history → `PROMPT_LOG.md` · serious malfunctions → `INCIDENTS.md` (both in Italian).

## Structure

```
backend/       FastAPI
  app/
    main.py      # app + CORS + routers under /api
    config.py    # server-side env (API key NEVER in the client), demo/live flags
    logging_config.py  # rotating log with a request id (backend/logs/)
    budget.py    # LLM spending cap, per category and per month
    api/         # endpoints (listed below)
    core/        # domain logic: agent, setup_params, vision_parser, demo answers, prompts,
                 # data/ (ACC catalogue, track guides, Kunos and community references)
    bundle/      # session bundle, adapters, archive, the generated DEMO session
    telemetria/  # ACC shared memory: structures, reader, dictionary, recorder, synthetic bench
    motec/       # MoTeC files: .ld/.ldx reader, writer with ACC's exact layout, session export
    analisi/     # deterministic engine: pace, consistency, corners, tyres and brakes; Gigi's context
    tests/       # 1276 offline tests in 23 files: adattatori 96, aggancio 37, analisi 61,
                 # analisi_l4 46, budget 31, bundle 37, chat 29, confronto 56, curve 75,
                 # debrief 39, demo 38, gigi 36, motec 43, motec_bundle 45, motec_export 17,
                 # observability 24, registratore 69, riferimenti 74, sessions 67,
                 # setup_ranges 40, telemetria 97, telemetria_bundle 50, tracciati 169
  scripts/       # image pipeline, track guide validator, MoTeC validation on real ACC files
strumenti/     one-command verification, commit guard, server start/stop, documentation figures
frontend/      Next.js 15.5 (App Router) + TypeScript + Tailwind + Recharts + Framer Motion
  src/
    app/         # layout + pages (listed below)
    components/  # UI and charts
    lib/         # API client, design tokens, page logic
docs/          # historical planning (00-02) and as-built V2 architecture (03)
```
Details in [`docs/03-v2-architecture.md`](docs/03-v2-architecture.md).
The ongoing data-logic rework (native ACC sources, canonical session bundle, analysis engine) is
specified in [`docs/04-rework-dati.md`](docs/04-rework-dati.md).

### Pages
| Route | Page |
|---|---|
| `/` | Dashboard: the verdict of the open session |
| `/telemetry` | Telemetry: laps, corners, tyres and brakes |
| `/console` | Console (race engineer analysis of the open session) |
| `/setup` | Setup (parameters flagged by the verdict) |
| `/sessioni` | Sessions: import (PC), manual session (console), archive |
| `/lezioni` · `/lezioni/[slug]` | A Lezione con Gigi (lessons with Gigi) |
| `/crediti` | Image credits (Wikimedia Commons) |
| `/login` | Sign-in (Google or demo mode) |

### API
| Method | Route | What it does |
|---|---|---|
| POST | `/api/analysis` | Race engineer analysis of a session (5 sections; `session_id`, default the DEMO) |
| GET | `/api/setup-params` | Setup parameters, with the click → in-game value rule of the car (`?car=`) |
| POST | `/api/setup/from-image` | Reads a setup from a screenshot (tested, currently used by no page) |
| GET | `/api/catalog` | Car and track catalogue |
| GET | `/api/catalog/car/{car_id}` | Single car sheet |
| GET | `/api/catalog/track/{track_id}` | Single track sheet |
| GET | `/api/catalog/track/{track_id}/guida` | Track guide: sectors and corner by corner |
| POST | `/api/sessions/import/setup` | Imports a setup saved in ACC |
| POST | `/api/sessions/import/results` | Imports an ACC results file (409 when it holds several cars) |
| POST | `/api/sessions/manuale` | Manual session (console players): lap times, setup, the driver's account |
| POST | `/api/sessions/import/motec` | Imports an ACC MoTeC export (.ld + .ldx, optional setup and fuel litres) as a session with channels |
| GET | `/api/sessions/{id}/export/motec` | The session as .ld + .ldx (zip) to open in MoTeC i2 |
| GET | `/api/sessions/{id}/debrief` | Gigi's debrief, phase by phase (engine only, no model) |
| PUT | `/api/sessions/{id}/debrief/tagli` | Phases cut by hand, saved in the session (`null` = Gigi's) |
| GET | `/api/sessions/{id}/confronto` | "Did I improve?": the session against the previous one on the same track and car (engine only, no model) |
| POST | `/api/sessions/{id}/chat` | Gigi live on the Console radio: streamed answer on the open session (needs `PITWALL_CHAT_LIVE=1`; 503 off, 429 cap reached, 409 conversation full) |
| POST | `/api/sessions/{id}/export/setup` | The session setup with the changed clicks, as a JSON file to load back into ACC |
| GET | `/api/sessions` | Stored sessions, DEMO included |
| GET | `/api/sessions/{id}` | One session (session bundle) |
| GET | `/api/sessions/{id}/analisi` | Deterministic analysis report (no LLM; adds corners, tyres and brakes when channels exist) |
| GET | `/api/sessions/{id}/tracce` | Channels of up to 4 laps on the same distance grid |
| GET | `/api/riferimenti/fisica` | Tyre and brake thresholds: Kunos (primary) and community (to be confirmed) |
| DELETE | `/api/sessions/{id}` | Removes a session (not the DEMO) |
| GET | `/api/telemetria/stato` | Telemetry recorder status (attachment, current session) |
| POST | `/api/telemetria/avvia` · `/ferma` | Starts and stops the recorder |
| GET | `/api/telemetria/sessioni` | Telemetry recordings on disk |
| GET | `/api/telemetria/sessioni/{id}` | Metadata of one recording |
| GET | `/api/telemetria/sessioni/{id}/canali` | Requested channel series, with decimation |
| GET | `/api/telemetria/sessioni/{id}/curve` | Per-corner analysis: where time is lost, how much, what to do (deterministic) |
| POST | `/api/telemetria/sessioni/{id}/importa` | Turns a recording into a stored session |
| DELETE | `/api/telemetria/sessioni/{id}` | Deletes a recording |

## Running locally

### Backend (FastAPI, port 8000)
```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env        # optional: without a key it runs in demo mode
python -m uvicorn app.main:app
```
Health check: <http://localhost:8000/> · sessions (DEMO included): <http://localhost:8000/api/sessions>

> **No `--reload`:** on Windows it keeps serving stale code after a backend change (HAZARD-V2-B in
> `INCIDENTS.md`). After touching the backend, stop it and start it again.

### Frontend (Next.js, port 3000)
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```
Open <http://localhost:3000>. Without a Google Client ID, sign in with **«Entra in modalità demo»**
(enter demo mode).

> **Never run `npm run build` while `npm run dev` is running:** it corrupts `.next` (HAZARD-V2-A).
> With the dev server up, use `npx tsc --noEmit` to type-check.

### Verification
One command, from the repository root, answers green or red:
```bash
python strumenti/verifica.py            # tests, types, docs; with the servers running also
                                        # pages, five browser journeys and screenshots
python strumenti/verifica.py --veloce   # no browser: the one GitHub runs on every push
```
Backend tests run offline and cost nothing. The other tools (server start/stop, commit guard,
documentation figures) are described in [`strumenti/`](strumenti/README.md) (in Italian).

### Logs
The backend writes to `backend/logs/` (gitignored):
- `pitwall.log`: application log, rotating (1 MB × 3), with a request id on every line that is also
  returned to the client in the `X-Request-ID` header. Warnings and errors show up in the console
  too. Every analysis logs its source and, when it falls back to the cache, the reason. What the
  driver writes is never logged, only its length. Every real model call leaves a line with the
  model, tokens and cost, or the reason the spending cap refused it.
- `llm_spesa.json`: today's spending per category and this month's total (see *Spending cap*).
- `llm_token_log.md` and `llm_incidents.md`: estimated tokens per call and failed calls, written by
  the LLM client when the real LLM is on.

### Images (photos and maps)
Images come from Wikimedia Commons and are **in the repo** (`frontend/public/assets/`, about 47 MB):
photos, verified track layouts, crops and credits. Authors and licences are in `ATTRIBUTIONS.md` and
on the `/crediti` page. The hand-picked selection is versioned separately; to rebuild the images
from it, from the repo root:
```bash
backend/.venv/Scripts/python backend/scripts/apply_photos.py   # photos (photos.json) + crops + credits
backend/.venv/Scripts/python backend/scripts/apply_maps.py     # track layouts (maps_choice.json)
```

## Environment variables and API key protection
Every variable, with its default, is documented in `backend/.env.example` and
`frontend/.env.local.example`.

The `ANTHROPIC_API_KEY` lives **only in the backend**. With `PITWALL_ALLOW_LIVE=0` (the default),
demo mode is forced whatever the other settings say: the **demo cache** is served, with no network
calls, and the key is never used. The real LLM requires **both** `PITWALL_ALLOW_LIVE=1` and
`PITWALL_DEMO_MODE=0`, plus the key in the server's secrets. The same protection applies to the
**screenshot setup reading**: in demo mode it answers `503` without calling the model.

### Spending cap
With the real LLM on, every model call **reserves its maximum cost** before it starts (input tokens
overestimated, plus every output token allowed) and, once the answer arrives, replaces it with the
**actual cost**. If the cap cannot cover the reservation, the call does not start: the cap holds
even with concurrent requests. Amounts are in dollars, the currency Anthropic bills in.

| Category | Use | Daily cap (default) |
|---|---|---|
| `analisi` | Console, `POST /api/analysis` | `PITWALL_BUDGET_ANALISI_GIORNO=0.50` |
| `screenshot` | `POST /api/setup/from-image` (used by no page) | `PITWALL_BUDGET_SCREENSHOT_GIORNO=0.25` |
| `chat` | Gigi live on the Console, `POST /api/sessions/{id}/chat` | `PITWALL_BUDGET_CHAT_GIORNO=0` |

On top of the three categories there is an overall **monthly** cap, `PITWALL_BUDGET_MESE=5.00`. The
day resets at midnight (server time). Once a cap is reached, the analysis answers from the cache with
`source: "fallback"` and the screenshot reading answers `429`. The real analysis branch also accepts
at most 4000 characters of question and 1000 of profile. When in doubt it counts high: a failed call
stays at its maximum cost, a model missing from the price list is charged at the most expensive
rate, and an unreadable spending record blocks calls.

## Roadmap
PitWall is a personal project that currently runs locally. The plan leads to two releases:

1. **Tooling and online showcase.** One-command verification, updated dependencies, write routes
   locked down, checks on other screens and browsers, first read-only deployment with the demo.
2. **Ready for the trial.** Landing page, a private space for each driver with no sign-up, usage
   counting, an entry path for drivers bringing their own sessions, click tables (today BMW M4 GT3
   and Ferrari 488 GT3 Evo, INC-V2-003).
3. **The trial.** Three to five ACC drivers use it on their own: do they reach the first analysis?
   do they come back? Meanwhile: optional Google sign-in, backups.
4. **First release:** free public beta, in Italian, on desktop.
5. **Second release:** English version (track guides stay in Italian).

Already done: model-free analysis engine, import from ACC files and MoTeC, 24 of 25 track guides and
22 of 25 maps, a 54-car catalogue, Gigi live under a spending cap, session-to-session comparison.

## Deployment
The showcase comes in two parts, both on free plans: the **frontend on Vercel** (the `frontend`
folder) and the **backend on Render**, described in [`render.yaml`](render.yaml) as a read-only
showcase: model, writes and recorder off, no API key, demo session only. The free backend goes to
sleep after fifteen minutes without visits: the frontend waits for it
(`NEXT_PUBLIC_ATTESA_ACCENSIONE_S`) and an external pinger keeps it awake during the day (`.github/workflows/sveglia.yml` is a daily check).

## License
Released under the **MIT** license — see [LICENSE](LICENSE).
