# PitWall.AI v2 — Strategia repo, struttura, API, roadmap

> Deciso l'08/07/2026. Una **repo nuova** (`pitwall-app`) con backend+frontend; la repo Streamlit
> attuale resta il deploy d'esame + fallback. Modalità: **l'utente crea la repo vuota su GitHub**,
> passa l'URL, **io preparo lo scaffold** e i file iniziali.

## Repo
- Nome proposto: **`pitwall-app`** (in alternativa `PitWall.AI-v2`).
- Una sola repo, due cartelle: `backend/` (FastAPI) + `frontend/` (Next.js). Monorepo semplice.
- La logica Python "protetta" viene **copiata** nella nuova repo (moduli stabili/congelati) sotto
  `backend/app/core/`, con il test del parser a garanzia (deve restare 12/12).

## Struttura proposta
```
pitwall-app/
├─ README.md
├─ docs/                      # qui migreranno 00/01/02 + nuova doc
├─ backend/
│  ├─ requirements.txt
│  ├─ .env.example            # ANTHROPIC_API_KEY, PITWALL_ALLOW_LIVE, LLM_MODEL, ...
│  └─ app/
│     ├─ main.py              # FastAPI app + CORS + include routers
│     ├─ config.py            # env server-side (no chiave nel client), flag demo/live
│     ├─ api/
│     │  ├─ analysis.py       # POST /api/analysis   (Gigi 4 sezioni: demo-cache o LLM)
│     │  ├─ session.py        # GET  /api/session    (dati demo telemetria + sessione)
│     │  ├─ setup.py          # GET  /api/setup-params?car&track
│     │  ├─ csv.py            # POST /api/csv/parse  (multipart)
│     │  └─ vision.py         # POST /api/setup/from-image (multipart, feature-flag)
│     ├─ core/                # ← RIUSO dalla v1 (adattato: niente import streamlit)
│     │  ├─ agent.py
│     │  ├─ csv_parser.py
│     │  ├─ setup_params.py   (+ data/car_setup_ranges.json)
│     │  ├─ vision_parser.py
│     │  ├─ demo_data.py      # numeri demo (invarianti §5 del summary)
│     │  ├─ demo_responses.py # 5 scenari cache (da ui/console.py)
│     │  └─ prompts/system_prompt_v4.txt (+ chat_system_prompt.txt)
│     └─ tests/test_parser.py # baseline 12/12
└─ frontend/
   ├─ package.json, tsconfig.json, tailwind.config.ts, next.config.js
   └─ app o src/
      ├─ app/                 # App Router: layout + pagine
      │  ├─ layout.tsx        # shell + sidebar + tema
      │  ├─ page.tsx          # Dashboard
      │  ├─ telemetry/page.tsx
      │  ├─ console/page.tsx
      │  ├─ setup/page.tsx
      │  └─ login/page.tsx
      ├─ components/
      │  ├─ charts/           # Gauge, Heatmap, Sparkline, TempLineChart, WindowBar
      │  └─ ui/               # Sidebar, Card, PageHeader, GigiAvatar, Toggle
      └─ lib/                 # apiClient.ts, types.ts, theme.ts (token cockpit)
```

## Superficie API (mappa 1:1 con le funzioni della v1)
| Endpoint | Metodo | Sorgente v1 | Ritorno |
|---|---|---|---|
| `/api/session` | GET | `ui/demo_data.py` | sessione + serie temp/press (hot&cold) + fuel + laps |
| `/api/analysis` | POST `{prompt}` | `ui/console.get_console_analysis` + `agent.get_ai_response` | testo 4 sezioni + `source` (demo/cache/api/fallback) |
| `/api/setup-params` | GET `?car&track` | `setup_params.get_params_for_car` | 5 sezioni × parametri (range/default/unit/tip) |
| `/api/csv/parse` | POST file | `csv_parser.parse_session_csv` | dict strutturato o 4xx `CSVParseError` |
| `/api/setup/from-image` | POST file | `vision_parser.parse_setup_from_image` | params riconosciuti (feature-flag) |

Auth: si parte **senza** (demo/mock) → poi Google via NextAuth quando si vuole (vedi §11 summary).
La demo-cache resta la spina dorsale offline (la demo non dipende dalla rete, come oggi).

## Deploy
- Frontend → **Vercel** (Next.js nativo, free). Variabile: `NEXT_PUBLIC_API_BASE_URL`.
- Backend → **Render/Railway/Fly** (uvicorn, free). Secret: `ANTHROPIC_API_KEY`, `PITWALL_ALLOW_LIVE`.
- CORS: il backend consente l'origine del frontend Vercel.

## Roadmap (fasi, ognuna verificabile)
0. **Scaffold** repo (backend+frontend), CI, README, `.env.example`. Parser test 12/12 in CI.
1. **Backend API**: `/session`, `/setup-params`, `/analysis` (prima solo demo-cache, poi LLM live gated).
2. **Frontend shell**: layout + sidebar + token tema + routing; **Dashboard** con dati da `/session`.
3. **Telemetria**: line chart (Recharts) + gauge/heatmap/sparkline (componenti SVG) + tabella + cross-check.
4. **Console**: analisi 4 card (parsing sezioni lato client) + chip + toggle demo/live → `/analysis`.
5. **Setup**: 49 parametri, 5 tab, slider, colore pressioni, evidenza suggeriti → `/setup-params`.
6. **Estensioni**: CSV upload, vision screenshot, auth reale, storico sessioni (thread-safe).
7. **Polish**: animazioni Framer Motion, responsive, deploy, e infine **switch** da Streamlit.

## Cosa mi serve da te per iniziare lo scaffold
1. Crea la repo **vuota** su GitHub (consiglio: **senza** README/.gitignore/licenza, così lo scaffold
   parte pulito): `pitwall-app`, visibilità a tua scelta.
2. Passami l'**URL** (es. `https://github.com/DaDoXey/pitwall-app`).
3. Io preparo lo scaffold in locale (cartella accanto a `PitWall.AI/`), lo collego alla remote e —
   con il tuo «ok push» — faccio il primo push (scaffold backend+frontend + questi doc in `docs/`).
