# PitWall.AI v2 — Architettura as-built

> **Stato documentato:** fine **megaprompt #2** ("redesign analogico da pit wall", FASI 1–12) ·
> `main == origin/main` a `ed18898` · redatto 10/07/2026.
> Completa i doc di planning `00`/`01`/`02` (che descrivono la *sorgente* v1 e la *decisione* di stack):
> questo file fotografa la v2 **com'è realmente costruita**. Per la cronologia → `PROMPT_LOG.md`;
> per i malfunzionamenti gravi → `INCIDENTS.md`.

## 1 · Stack & runtime
| Layer | Tech | Versione |
|---|---|---|
| Frontend | Next.js (App Router) / React | 15.5.20 / 19 |
| | TypeScript / Tailwind | 5.7 / 3.4 |
| | Recharts / Framer Motion | 2.15 / 11.15 |
| Backend | FastAPI / Uvicorn | 0.115 / 0.34 |
| | Anthropic SDK / Pandas / Pydantic | 0.113 / 3.0 / 2.10 |
| LLM (Gigi) | `claude-haiku-4-5` (env `LLM_MODEL`), fallback `claude-sonnet-4-6` | |

**Avvio dev:** `cd backend && ./.venv/Scripts/python -m uvicorn app.main:app --reload` (:8000) +
`cd frontend && npm run dev` (:3000). Health `GET :8000/` → `{status:"ok", demo_mode:true, live_allowed:false}`.

## 2 · Frontend (`frontend/src/`)
- **`app/layout.tsx`** — shell: font (Orbitron/Inter/JetBrains), `Sidebar` **sempre visibile** + `<main>` con `MotionProvider`.
  Reduced-motion centralizzato (`<MotionConfig reducedMotion="user">`).
- **`app/page.tsx`** — **Dashboard**: card sessione + card KPI (sparkline + min/max) + modal KPI (grafico ad
  assi/griglia/soglie), drag&drop con persistenza `localStorage` + resize. Cabla `GET /api/session`.
- **`app/console/page.tsx`** — **Engineer Console** (Gigi): chip scenari, input, 4 card d'analisi (markdown-lite),
  link → Setup. Cabla `POST /api/analysis` (demo-mode: cache con routing per keyword).
- **`app/telemetry/page.tsx`** — line chart temp + heatmap + 4 gauge a lancetta + tabella giro + cross-check. Cabla `GET /api/session`.
- **`app/setup/page.tsx`** — 5 tab / 49 slider ACC, input sessione (selettori + upload). Cabla `/api/setup-params`, `/session`, `/csv/parse`, `/setup/from-image`.
- **`app/login/page.tsx`** — card demo (nessuna auth reale; vedi INC-V2-004).
- **`components/ui/`**: `Sidebar`, `PageHeader`, `MotionProvider`, `CountUp`.
- **`components/charts/`**: `TempLineChart` (Recharts), `PressureGauge`/`TyreHeatmap`/`LapTable`/`Sparkline` (SVG a mano).
- **`lib/`**: `api.ts` (fetch client + `ApiError`), `theme.ts`, **`instrument.ts`** (token "analogici": STATE
  ok/warn/alarm/cold, INSTRUMENT grid/track/tick/ink, STROKE hairline/tick/needle, glow off), **`motion.ts`**
  (`fadeInUp`/`stagger`/`cardHover`, `EASE=[0.22,1,0.36,1]`, `DUR`), `telemetry.ts`, `console.ts`, `setup.ts`, `catalog.ts`.

## 3 · Backend (`backend/app/`)
- **`main.py`** — FastAPI, CORS, 5 router `/api`. **`config.py`** — env server-side + presidio chiave (flag demo/live).
- **`api/`**: `session.py`, `analysis.py`, `setup.py`, `csv.py`, `vision.py`.
- **`core/`** (⚠️ = protetto): ⚠️`agent.py`, ⚠️`csv_parser.py`, ⚠️`setup_params.py`, ⚠️`vision_parser.py`,
  `demo_data.py`, `demo_responses.py`, `prompts/*` (⚠️ system prompt v4), `data/car_setup_ranges.json`,
  `tests/test_parser.py` (**12/12**).

## 4 · Contratto API
- `GET /api/session` → `{ session, tyre_labels, temp{series,max,limit,scale}, pressure{hot,hot_window,hot_series,cold,cold_window,cold_amber_margin,avg_hot}, fuel_per_lap, laps, suggested_params }`.
- `POST /api/analysis` body `{prompt}` → `{question, text(4 sezioni md), source: demo|cache|api|fallback}`. In demo-mode: sempre cache, routing per keyword.
- `GET /api/setup-params?car&track` → 5 sezioni / 49 `Param{label,min,max,step,unit,default,tip}`.
- `POST /api/csv/parse` (multipart) → `CsvResult` (400 se CSV invalido).
- `POST /api/setup/from-image` (multipart) → `{params,summary}` (503 se manca la key server).

## 5 · Presidio API key
`ANTHROPIC_API_KEY` vive **solo lato server**. Con `PITWALL_ALLOW_LIVE=0` (default, e forzato sul deploy
pubblico) si serve la **cache demo** offline → la chiave non si consuma mai e non finisce nel bundle JS.
La LLM reale si abilita con `PITWALL_ALLOW_LIVE=1` + chiave nei secret del server.

## 6 · Invarianti dati demo (`core/demo_data.py`) — da preservare
Sorgente unica dei numeri per la coerenza cross-schermata:
- Sessione: Monza · BMW M4 GT3 · 8 giri · best 1:47.812 · ~3.2 L/giro. Caso didattico: **retrotreno scarico** (Post.DX 105°C).
- **temp max = ultimo valore serie** (88/90/95/105; limite 95°C). **Pressioni a caldo ultimo giro = gauge**.
- **Freddo vs caldo mai mescolati**; delta cold→hot ~**+2.5 psi**. Media a caldo 28.6; finestra caldo 28.5–30.0, freddo 26.0–27.0.

## 7 · Verifica
- Frontend: `npx tsc --noEmit` **0 err** + rotte `/ /console /telemetry /setup /login` **200**.
- Backend: `./.venv/Scripts/python app/tests/test_parser.py` → **12/12**.
- **Mai** `npm run build` con `npm run dev` attivo (corrompe `.next`).

## 8 · Deploy (previsto)
Frontend → **Vercel** (`NEXT_PUBLIC_API_BASE_URL`). Backend → **Render/Railway/Fly** (secret
`ANTHROPIC_API_KEY`, `PITWALL_ALLOW_LIVE`). CORS: il backend consente l'origine del frontend.

## 9 · Note aperte (vedi `INCIDENTS.md`)
Mojibake `track_nick` (INC-V2-002) · override `car_setup_ranges.json` no-op (INC-V2-003) · login espone
la Sidebar / auth-gate mancante (INC-V2-004) · fix drag&drop card estese (INC-V2-005, rework #8).
