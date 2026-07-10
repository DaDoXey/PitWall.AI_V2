# PitWall.AI_V2

A Virtual Race Engineer for Assetto Corsa Competizione (ACC). Leveraging LLMs to transform
telemetry and driver feedback into actionable car setup and race strategy advice. Designed to
bridge the gap between complex data and track performance for sim-racers. Developed for the AI &
Digital Innovation Specialist course.

> **v2** della webapp PitWall.AI: migrazione da Streamlit a **Next.js + FastAPI**. Riusa la logica
> di dominio della v1 (client LLM, parser CSV, range ACC, vision) dietro un'API pulita, con una UI
> React ricca. La v1 Streamlit resta il deploy d'esame + fallback finché la v2 non è pronta.

## Struttura

```
backend/     FastAPI — riusa la logica Python della v1 in app/core/
  app/
    main.py          # FastAPI + CORS + routers
    config.py        # env server-side (API key MAI nel client), flag demo/live
    api/             # /api/session, /api/analysis, /api/setup-params, /api/csv/parse, /api/setup/from-image
    core/            # logica riusata: agent, csv_parser, setup_params, vision_parser, demo_data, prompts
    tests/           # test_parser (baseline 12/12)
frontend/    Next.js 15.5 (App Router) + TypeScript + Tailwind + Recharts + Framer Motion
  src/
    app/                 # layout + pagine (dashboard, telemetry, console, setup, login)
    components/ui/       # Sidebar, PageHeader, MotionProvider, CountUp
    components/charts/   # TempLineChart, PressureGauge, TyreHeatmap, LapTable, Sparkline
    lib/                 # api, theme, instrument (token "analogici"), motion, telemetry, console, setup, catalog
```

## Avvio in locale

### Backend (FastAPI, porta 8000)
```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env        # opzionale: la demo-mode gira anche senza chiave
uvicorn app.main:app --reload
```
Health check: <http://localhost:8000/> · API demo: <http://localhost:8000/api/session>

### Frontend (Next.js, porta 3000)
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```
Apri <http://localhost:3000> (la Dashboard legge `GET /api/session`).

## Presidio API key
La `ANTHROPIC_API_KEY` vive **solo nel backend**. Con `PITWALL_ALLOW_LIVE=0` (default) si serve la
**cache demo** (nessuna rete): la demo non consuma la chiave. La LLM reale si abilita con
`PITWALL_ALLOW_LIVE=1` + chiave nei secret del server.

## Stato attuale
Migrazione **feature-complete** (tutte le pagine cablate alle API) + **2 megaprompt di redesign**:
#1 estetico base, #2 "analogico da pit wall" (FASI 1–12, ✅ completo). Prossimo: **megaprompt #3**
(5 rework di rifinitura: Setup, LapTable, Sidebar, KPI stile MoTeC, fix drag&drop).
Cronologia iterazioni → `PROMPT_LOG.md` · malfunzionamenti gravi → `INCIDENTS.md`.

## Roadmap residua
Rework #4–#8 → auth reale (Google OAuth) → storico sessioni SQLite → deploy → switch da Streamlit.

## Deploy (previsto)
Frontend su **Vercel**, backend su **Render/Railway/Fly** (free tier). Vedi i doc di planning in `docs/`.
