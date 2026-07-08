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
frontend/    Next.js 15 (App Router) + TypeScript + Tailwind + Recharts + Framer Motion
  src/
    app/             # layout + pagine (dashboard, telemetry, console, setup, login)
    components/ui/   # Sidebar, PageHeader, (charts in arrivo)
    lib/             # api client, theme tokens
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

## Roadmap
Fase 0 scaffold (fatta) → 1 backend API → 2 shell+Dashboard → 3 Telemetria → 4 Console →
5 Setup → 6 estensioni (CSV/vision/auth/storico) → 7 polish + deploy + switch da Streamlit.

## Deploy (previsto)
Frontend su **Vercel**, backend su **Render/Railway/Fly** (free tier). Vedi i doc di planning.
