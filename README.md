**English** | [Italiano](README.it.md)

# PitWall.AI_V2

A Virtual Race Engineer for Assetto Corsa Competizione (ACC). Leveraging LLMs to transform
telemetry and driver feedback into actionable car setup and race strategy advice. Designed to
bridge the gap between complex data and track performance for sim-racers. Developed for the AI &
Digital Innovation Specialist course.

> **v2** of the PitWall.AI web app: a migration from Streamlit to **Next.js + FastAPI**. It reuses
> the v1 domain logic (LLM client, ACC ranges, vision) behind a clean API, with a rich
> React UI.

## Current status
**Final exam passed on 15/07/2026**, with the demo running in demo mode. The **full build** is now
under way: taking PitWall from a demo to a product, with a real LLM underneath.

The LLM client is already implemented: a 4-section validated analysis, with retries and a model
cascade, switched on with `PITWALL_ALLOW_LIVE=1` + `PITWALL_DEMO_MODE=0` + the API key. The client
also contains a streaming chat for Gigi, which is not wired to any route yet. Every model call goes
through a daily and monthly **spending cap**. **The real LLM stays off by default** until it has
been stress-tested (see Roadmap).

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
    core/        # domain logic: agent, setup_params, vision_parser, demo, prompts,
                 # data/ (ACC catalogue and track guides)
    telemetria/  # shared memory di ACC: strutture, lettore, dizionario, registratore
    analisi/     # motore deterministico: ritmo e costanza (L2), curve (L3)
    tests/       # test_bundle (37), test_adattatori (81), test_analisi (57),
                 # test_sessions (50), test_observability (24), test_budget (31),
                 # test_telemetria (97), test_riferimenti (73), test_registratore (69),
                 # test_curve (62)
  scripts/       # image pipeline (photos, crops, maps) and track guide validator
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
| `/` | Dashboard |
| `/telemetry` | Telemetry |
| `/console` | Console (race engineer analysis) |
| `/setup` | Setup |
| `/lezioni` · `/lezioni/[slug]` | A Lezione con Gigi (lessons with Gigi) |
| `/crediti` | Image credits (Wikimedia Commons) |
| `/login` | Sign-in (Google or demo mode) |

### API
| Method | Route | What it does |
|---|---|---|
| GET | `/api/session` | Current session |
| POST | `/api/analysis` | Race engineer analysis |
| GET | `/api/setup-params` | Setup parameters and their ranges |
| POST | `/api/setup/from-image` | Reads a setup from a screenshot |
| GET | `/api/catalog` | Car and track catalogue |
| GET | `/api/catalog/car/{car_id}` | Single car sheet |
| GET | `/api/catalog/track/{track_id}` | Single track sheet |
| POST | `/api/sessions/import/setup` | Imports a setup saved in ACC |
| POST | `/api/sessions/import/results` | Imports an ACC results file (409 when it holds several cars) |
| GET | `/api/sessions` | Imported sessions |
| GET | `/api/sessions/{id}` | One session (session bundle) |
| GET | `/api/sessions/{id}/analisi` | Deterministic analysis report (no LLM) |
| DELETE | `/api/sessions/{id}` | Removes a session |
| GET | `/api/telemetria/stato` | Telemetry recorder status (attachment, current session) |
| POST | `/api/telemetria/avvia` · `/ferma` | Starts and stops the recorder |
| GET | `/api/telemetria/sessioni` | Telemetry recordings on disk |
| GET | `/api/telemetria/sessioni/{id}` | Metadata of one recording |
| GET | `/api/telemetria/sessioni/{id}/canali` | Requested channel series, with decimation |
| GET | `/api/telemetria/sessioni/{id}/curve` | Per-corner analysis: where time is lost, how much, what to do (deterministic) |
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
Health check: <http://localhost:8000/> · demo API: <http://localhost:8000/api/session>

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

### Tests
```bash
cd backend
./.venv/Scripts/python app/tests/test_observability.py   # logs and request id, offline
./.venv/Scripts/python app/tests/test_budget.py          # spending cap, offline (fake client)
```

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
Images come from Wikimedia Commons (~33 MB) and are **not in the repo**: `frontend/public/assets/`
is gitignored. After a clone the app still works, but car and track sheets have no photos and
`/crediti` reports the assets as not downloaded yet. The hand-picked selection is versioned; to
download it, from the repo root:
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
| `screenshot` | Setup, `POST /api/setup/from-image` | `PITWALL_BUDGET_SCREENSHOT_GIORNO=0.25` |
| `chat` | Gigi's chat (not wired) | `PITWALL_BUDGET_CHAT_GIORNO=0` |

On top of the three categories there is an overall **monthly** cap, `PITWALL_BUDGET_MESE=5.00`. The
day resets at midnight (server time). Once a cap is reached, the analysis answers from the cache with
`source: "fallback"` and the screenshot reading answers `429`. The real analysis branch also accepts
at most 4000 characters of question and 1000 of profile. When in doubt it counts high: a failed call
stays at its maximum cost, a model missing from the price list is charged at the most expensive
rate, and an unreadable spending record blocks calls.

## Roadmap
1. **Switch-on and stress test of the real LLM**, with the spending cap already in place.
2. **Track guides** for all 25 ACC circuits: sectors and corner by corner.
3. **Track maps**: 5 of 25 layouts verified. The other 20 still need replacing, and no page shows
   the maps yet.
4. **Catalogue batch 2**: 23 GT4, GT2, GTC and TCX cars.
5. **Per-car setup ranges** (INC-V2-003): changing car does not change the 49 parameters yet.
6. **Deployment**.

## Deployment
Platform **to be decided**. Keep in mind: images are not versioned, so a deployment starts without
photos until `apply_photos.py` is run.

## License
Released under the **MIT** license — see [LICENSE](LICENSE).
