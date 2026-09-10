**English** | [Italiano](README.it.md)

# PitWall.AI_V2

A Virtual Race Engineer for Assetto Corsa Competizione (ACC). Leveraging LLMs to transform
telemetry and driver feedback into actionable car setup and race strategy advice. Designed to
bridge the gap between complex data and track performance for sim-racers. Developed for the AI &
Digital Innovation Specialist course.

> **v2** of the PitWall.AI web app: a migration from Streamlit to **Next.js + FastAPI**. It reuses
> the v1 domain logic (LLM client, CSV parser, ACC ranges, vision) behind a clean API, with a rich
> React UI.

## Current status
**Final exam passed on 15/07/2026**, with the demo running in demo mode. The **full build** is now
under way: taking PitWall from a demo to a product, with a real LLM underneath.

The LLM client is already implemented (4-section validated analysis, with retries and a model
cascade, plus Gigi's chat) and is switched on with `PITWALL_ALLOW_LIVE=1` + `PITWALL_DEMO_MODE=0` +
the API key. **It stays off by default** until observability and a cost model are in place (see
Roadmap).

Iteration history → `PROMPT_LOG.md` · serious malfunctions → `INCIDENTS.md` (both in Italian).

## Structure

```
backend/       FastAPI
  app/
    main.py      # app + CORS + routers under /api
    config.py    # server-side env (API key NEVER in the client), demo/live flags
    api/         # endpoints (listed below)
    core/        # domain logic: agent, csv_parser, setup_params, vision_parser, demo, prompts,
                 # data/ (ACC catalogue and track guides)
    tests/       # test_parser (baseline 12/12)
  scripts/       # image pipeline (photos, crops, maps) and track guide validator
frontend/      Next.js 15.5 (App Router) + TypeScript + Tailwind + Recharts + Framer Motion
  src/
    app/         # layout + pages (listed below)
    components/  # UI and charts
    lib/         # API client, design tokens, page logic
docs/          # historical planning (00-02) and as-built V2 architecture (03)
```
Details in [`docs/03-v2-architecture.md`](docs/03-v2-architecture.md).

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
| POST | `/api/csv/parse` | Telemetry CSV import |
| POST | `/api/setup/from-image` | Reads a setup from a screenshot |
| GET | `/api/catalog` | Car and track catalogue |
| GET | `/api/catalog/car/{car_id}` | Single car sheet |
| GET | `/api/catalog/track/{track_id}` | Single track sheet |

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
./.venv/Scripts/python app/tests/test_parser.py    # baseline 12/12
```

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
`PITWALL_DEMO_MODE=0`, plus the key in the server's secrets.

## Roadmap
1. **Observability of the LLM path**: levelled logging to a dedicated location. Today a failure on
   the real path leaves no trace.
2. **Cost model** before switching it on: the model cascade multiplies spending exactly when
   something fails, and has no cap.
3. **Switch-on and stress test of the real LLM.**
4. **Track guides** for all 25 ACC circuits: sectors and corner by corner.
5. **Track maps**: 5 of 25 layouts verified. The other 20 still need replacing, and no page shows
   the maps yet.
6. **Catalogue batch 2**: 23 GT4, GT2, GTC and TCX cars.
7. **Per-car setup ranges** (INC-V2-003): changing car does not change the 49 parameters yet.
8. **Deployment**.

## Deployment
Platform **to be decided**. Keep in mind: images are not versioned, so a deployment starts without
photos until `apply_photos.py` is run.

## License
Released under the **MIT** license — see [LICENSE](LICENSE).
