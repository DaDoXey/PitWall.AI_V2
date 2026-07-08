# PitWall.AI v2 — Stack target (deciso)

> Deciso l'08/07/2026. Base: `00-project-summary.md`. Timing: sviluppo **in parallelo**,
> Streamlit resta il deploy d'esame + fallback fino allo switch.

## Decisione
- **Backend:** **FastAPI** (Python) che **riusa** la logica di dominio esistente (il valore del progetto).
- **Frontend:** **Next.js (App Router) + React + TypeScript + Tailwind CSS**.
- **Grafici:** **Recharts** (line chart, tabelle); **componenti SVG custom** per gauge/heatmap/sparkline
  (portati dai builder attuali in `ui/components.py`); **Framer Motion** per le animazioni.
- **Deploy (free tier):** **Vercel** (frontend) + **Render** o **Railway/Fly** (backend FastAPI).

## Perché (criteri)
| Criterio | Next.js + FastAPI | Streamlit (attuale) | FastAPI+HTMX (alternativa) |
|---|---|---|---|
| Controllo visivo / "ancora meglio" | ★★★ componenti + Framer Motion | ★ iframe, no-wildcard CSS, clipping | ★★ buono ma limitato su animazioni/interazione |
| Riuso logica Python | ★★★ (backend Python invariato) | — (già Python) | ★★★ |
| Grafici interattivi (gauge/heatmap live) | ★★★ | ★★ (Plotly + SVG stringati) | ★★ |
| Curva d'apprendimento (non-esperto) | ★★ (JS/TS da imparare, ma AI-assistito) | ★★★ | ★★★ |
| Ecosistema / supporto Claude Code | ★★★ | ★★ | ★★ |
| Deploy free | ★★★ Vercel+Render | ★★★ Streamlit Cloud | ★★ |

La UI attuale è già **fatta a mano in SVG** (gauge, heatmap, sparkline, avatar): in React diventano
**componenti riutilizzabili e animabili** quasi 1:1. Streamlit è il collo di bottiglia proprio sul
"wow" che vuoi; HTMX ridurrebbe il JS ma non regge lo stesso livello di grafica interattiva.

## Versioni indicative (da pinnare nello scaffold)
- Backend: Python 3.12, `fastapi`, `uvicorn[standard]`, `anthropic`, `pandas`, `python-dotenv`,
  `python-multipart` (upload), `pydantic` v2.
- Frontend: Node 20 LTS, Next.js 15, React 19, TypeScript 5, Tailwind 3, Recharts, Framer Motion.

## Presidio API key (invariante dalla v1)
La `ANTHROPIC_API_KEY` vive **solo lato backend**. Il frontend chiama la nostra API, mai Anthropic
direttamente. Flag `PITWALL_ALLOW_LIVE` (default 0) → in deploy pubblico si serve la **cache demo**
(stessi 5 scenari), la LLM reale si abilita solo con secret lato server. Nessuna chiave nel bundle JS.

## Token di design (dal tema attuale → Tailwind)
Cockpit dark: `--bg #0a0a0a`, surface `#111`, raised `#1a1a1a`, inset `#141414`, accent `#E8002D`,
ok `#00C853`, warn `#FFB300`, border `#222`/`#333`, testo `#FFF`/`#999`/`#666`. Font: Orbitron
(display), Inter (body), JetBrains Mono (mono). Diventano token in `tailwind.config` + CSS variables.
