# PROMPT_LOG — PitWall.AI **v2** (Next.js + FastAPI)
**Corso:** AI Projects Development — ITS ICT Academy Roma
**Autore:** Ferlito Edoardo
**Aperto:** 10/07/2026 (retro-compilato dal git log della v2)
**Repo:** github.com/DaDoXey/PitWall.AI_V2 · locale in `OneDrive/Desktop/PitWall.AI_V2`

> Continuazione del `PROMPT_LOG` della v1 (Streamlit). La **v2** migra a **Next.js 15.5 /
> React 19 / FastAPI**, riusando *tale e quale* la logica Python protetta della v1 nel backend.
> Questo file è il **registro di lavoro** della v2: ogni iterazione, richiesta e intervento va
> annotato qui. (I dettagli storici della v1 restano nel `PROMPT_LOG.md` della cartella `PitWall.AI/`.)

---

## Come usare questo file

Per ogni iterazione (megaprompt, FASE, fix o richiesta dell'utente) crea una nuova entry con:
- **Data e contesto** — quando e perché sei intervenuto (quale richiesta dell'utente).
- **Catalogo messaggi** — i prompt/richieste ricevuti in quell'iterazione (utile per la tracciabilità d'esame).
- **Modifica apportata** — cosa hai cambiato (diff concettuale + file toccati), su quale/i commit.
- **Motivazione** — il problema che stavi risolvendo.
- **Risultato osservato** — cosa è cambiato a schermo / nell'output.
- **Verifica** — `npx tsc --noEmit` (0 err) + rotte toccate 200; backend `test_parser` **12/12**.
- **File protetti** — dichiarare esplicitamente «nessuno toccato» o l'ok gate ricevuto.
- **Decisione** — mantenuto / modificato ulteriormente / rollback.

### Guardrail fissi (validi per ogni entry)
1. **File protetti** (STOP gate + «ok procedi»): `backend/app/core/*` (`agent.py`, `csv_parser.py`,
   `setup_params.py`, `vision_parser.py`), system prompt (`prompts/*`), **numeri** demo
   (`demo_data.py`/`demo_responses.py`), `car_setup_ranges.json`, logica gauge/carburante.
   L'UI li **chiama**, non li riscrive. Si lavora **solo** in `frontend/src/` (+ `globals.css`).
2. **Demo-mode** protegge la API key (solo server; `PITWALL_ALLOW_LIVE=0` sul deploy). Nessun endpoint nuovo.
3. **Verifica ad ogni FASE**: `npx tsc --noEmit` 0 err + rotte 200 · backend `test_parser` 12/12.
   **Gotcha:** mai `npm run build` con `npm run dev` attivo (corrompe `.next`) → con dev usa solo `tsc --noEmit`.
4. **Git**: nessun `commit`/`push` senza **«ok push»** esplicito; un commit per unità logica; `main` allineato a `origin`.
5. **Report mai committati** (`*_REPORT.md` gitignorato). Tooling `.claude/` locale, non si pusha.
6. **Metodo**: una cosa alla volta con **verifica a schermo** prima di procedere; esporre il piano e attendere ok.

### Contesto tecnico rapido (per non ri-derivarlo)
- **Stack:** Next.js 15.5.20 (App Router) · React 19 · TS 5.7 · Tailwind 3.4 · Recharts 2.15 · Framer Motion 11.15.
  Backend FastAPI 0.115 / Uvicorn (invariato, fuori scope UI).
- **LLM di Gigi:** default `claude-haiku-4-5` (env `LLM_MODEL`), fallback `claude-sonnet-4-6`. In demo-mode risponde la cache.
- **Agente di sviluppo:** Claude Code (`claude-opus-4-8`).
- **Avvio dev:** `cd backend && ./.venv/Scripts/python -m uvicorn app.main:app --reload` (:8000) +
  `cd frontend && npm run dev` (:3000). Health `GET :8000/` → `{status:"ok", demo_mode:true}`.
- **Token estetici:** `frontend/src/lib/instrument.ts` (STATE ok/warn/alarm/cold, INSTRUMENT grid/track/tick/ink,
  STROKE hairline/tick/needle, glow off) · `frontend/src/lib/motion.ts` (durate/easing approvati). **Riusare, non reinventare.**

---

## Entry #001 — Scaffolding v2: migrazione Streamlit → Next.js + FastAPI

| Campo | Valore |
|---|---|
| Data | 08/07/2026 |
| Agente dev | Claude Code (`claude-opus-4-8`) |
| Area | Bootstrap monorepo (backend + frontend) |
| Commit | `0ec539d` (initial), `336ec6a` (scaffold), `acd8a44` (Next 15.1.3→15.5.20) |
| Contesto | Avvio della v2: nuova base tecnica, riuso della logica Python protetta della v1 |

**Modifica:** Creato monorepo v2. **Backend FastAPI** (`backend/app/`): `main.py` (CORS + 5 router `/api`),
`config.py` (env server-side + presidio chiave), `core/` con la logica protetta portata dalla v1
(`agent.py`, `csv_parser.py`, `setup_params.py`, `vision_parser.py`, prompt system v4, `car_setup_ranges.json`,
`demo_data.py`, `demo_responses.py`, `tests/test_parser.py`). **Frontend Next.js** (App Router) con
Tailwind + token colore. Bump di sicurezza Next `15.1.3 → 15.5.20` (CVE-2025-66478) + `package-lock`.

**Motivazione:** Superare i limiti di presentazione di Streamlit (v1) con un frontend web moderno,
mantenendo intatta la logica di dominio ACC già validata.

**Risultato osservato:** Backend servito su :8000 (`/` health ok, demo-mode ON), frontend su :3000. Contratto API definito.

**Verifica:** `test_parser` 12/12; scaffold frontend compilante.

**File protetti:** portati verbatim dalla v1 nel `core/` (nessuna riscrittura della logica).

**Decisione:** ☑ Mantenuto.

---

## Entry #002 — Build feature-complete: Telemetria · Console · Setup · Dashboard/Login

| Campo | Valore |
|---|---|
| Data | 08–09/07/2026 |
| Agente dev | Claude Code (`claude-opus-4-8`) |
| Area | Le 5 pagine cablate agli endpoint reali |
| Commit | `54ca455` (F3 telemetria), `ad46479` (F4 console), `1e01fe5` (F5 setup), `3fce763` (dashboard/login), `2ec4a92` (F7 input sessione), `5e117ac` (F6 Gigi→Setup) |
| Contesto | Portare tutte le schermate della v1 sulla nuova UI, agganciate alle API FastAPI |

**Modifica:**
- **F3 · Telemetria** (`app/telemetry/page.tsx`): line chart temp gomme (Recharts), 4 gauge pressioni,
  heatmap SVG, tabella giro-per-giro, cross-check di coerenza. Cabla `GET /api/session`.
- **F4 · Engineer Console** (`app/console/page.tsx`): chip scenari, input, 4 card d'analisi (markdown-lite),
  link → Setup. Cabla `POST /api/analysis` (in demo-mode: cache con routing per keyword).
- **F5 · Setup** (`app/setup/page.tsx`): 5 tab ACC / 49 slider da `GET /api/setup-params`.
- **F7 · Input sessione**: selettori Auto/Tracciato/Condizioni + upload CSV (`/api/csv/parse`) e
  screenshot (`/api/setup/from-image`, richiede key server).
- **F6 · Console↔Setup**: `suggested_params` di Gigi evidenziati negli slider.
- Rifinitura pagine grezze Dashboard (`app/page.tsx`, `GET /api/session`) e Login (presentazionale, nessuna auth reale).

**Motivazione:** Raggiungere la parità di funzioni con la v1 sulla nuova architettura.

**Risultato osservato:** Migrazione **feature-complete** su tutte le pagine; dati coerenti cross-schermata
(temp max = ultimo valore serie; pressioni a caldo = gauge; freddo/caldo mai mescolati).

**Verifica:** `tsc --noEmit` 0 err; rotte `/ /console /telemetry /setup /login` 200; `test_parser` 12/12.

**File protetti:** nessuno toccato (solo chiamati via API).

**Decisione:** ☑ Mantenuto.

---

## Entry #003 — Motion F8–F9: fondamenta animazioni + micro-interazioni

| Campo | Valore |
|---|---|
| Data | 09/07/2026 |
| Agente dev | Claude Code (`claude-opus-4-8`) |
| Area | `lib/motion.ts` + animazioni cross-vista |
| Commit | `95360f8` (F8 1/2), `be70558` (F8 2/2), `bbeae9a` (F9) |
| Contesto | Dare vita alle schermate con un vocabolario di motion centralizzato |

**Modifica:** Creato `frontend/src/lib/motion.ts` (`fadeInUp`, `staggerContainer`, `cardHover`,
`EASE=[0.22,1,0.36,1]`, `DUR={fast .2, base .4, slow .9}`) + `MotionProvider` + `CountUp`.
Micro-animazioni su Console/Telemetria/Setup e Sparkline responsive (F8); motion su Login, Sidebar
(indicatore `layoutId`), PageHeader e grafici SVG — gauge sweep, sparkline draw-on, heatmap stagger (F9).
Reduced-motion centralizzato (`<MotionConfig reducedMotion="user">`), con degrado allo stato finale.

**Motivazione:** Resa "premium" e coerente delle transizioni senza toccare i singoli componenti a mano.

**Risultato osservato:** Entrate animate uniformi in tutte le pagine.
**Nota (feedback successivo, NMP-1):** durate percepite **troppo lente** → target di rework verso
`fast ≈0.12 / base ≈0.22 / slow ≈0.45` (centralizzato nei `DUR`).

**Verifica:** `tsc --noEmit` 0 err; rotte 200.

**File protetti:** nessuno toccato.

**Decisione:** ☑ Mantenuto (durate da velocizzare in un giro successivo).

---

## Entry #004 — MEGAPROMPT #1: redesign estetico base (F2–F8)

| Campo | Valore |
|---|---|
| Data | 10/07/2026 |
| Agente dev | Claude Code (`claude-opus-4-8`) |
| Area | Redesign estetico trasversale (base) |
| Commit | `1203404` (redesign F2–F8), `a2ba247` (chore: gitignore tooling `.claude/` + `*.tsbuildinfo`) |
| Contesto | Primo megaprompt di redesign generato da Claude Desktop sul dossier `MEGAPROMPT_STATE_REPORT.md` |

**Modifica:** Passata estetica di base su tutte le schermate (design system: sfondi `#0a0a0a`/`#111`/`#1a1a1a`,
accento `#E8002D`, ok `#00C853`, warn `#FFB300`, bordi `#222`/`#333`, testo `#999`/`#666`; font
Orbitron/Inter/JetBrains Mono). Igiene git: ignorati il tooling locale `.claude/` e `*.tsbuildinfo`,
untrack di `.session-cache-nudged`.

**Motivazione:** Alzare la qualità visiva complessiva prima della rifinitura "analogica" (megaprompt #2).

**Risultato osservato:** Base estetica coerente; predisposto il terreno per il redesign strumentale.

**Verifica:** `tsc --noEmit` 0 err; rotte 200.

**File protetti:** nessuno toccato.

**Decisione:** ☑ Mantenuto → confluito nel megaprompt #2.

---

## Entry #005 — MEGAPROMPT #2: redesign "analogico da pit wall" (FASI 1–12) ✅ COMPLETO

| Campo | Valore |
|---|---|
| Data | 10/07/2026 |
| Agente dev | Claude Code (`claude-opus-4-8`) |
| Area | Resa "strumento reale" (MoTeC-like) cross-vista |
| Commit | `9fc4310` (FASE 1–2), `2dcfb54` (FASE 3–11), `d848e8f` (FASE 12) — **`main == origin/main`** |
| Contesto | Secondo megaprompt: meno glow/saturazione/animazione, **colore = solo stato**, grigi per griglia/assi |

**Direttiva trasversale:** rendere l'app un **strumento analogico da muretto** (MoTeC i2), togliendo
glow e saturazione, usando il colore solo per comunicare lo stato e i grigi per griglia/assi/tick.

**Modifica (per FASE):**
- **F1–F2** — `lib/instrument.ts`: token unici (STATE ok/warn/alarm/cold, INSTRUMENT grid/track/tick/ink,
  STROKE hairline/tick/needle, glow spento). **Gauge pressioni → a lancetta** con tacche.
- **F3–F11** — resa analogica cross-vista: **LapTable** pulita (rimosse mini data-bar, numeri colorati per
  soglia); **TempLineChart** linee sottili no-glow, legenda spaziata; **Heatmap** rettangolo semplice, ruote
  centrate; **GigiAvatar** cuffia mono-linea; **Sidebar** badge demo + 2 shortcut + riga consiglio;
  **Sparkline** statica (fix bug gradient); **Card KPI** con min/max; **Drag&drop** con feedback +
  persistenza `localStorage` + resize card; **KpiModal** con grafico ad assi/griglia/marker/soglie +
  "Riferimenti" + "Nota di Gigi".
- **F12** — Setup: scrollbar dropdown in palette + slider più definiti (thumb accent, traccia più marcata).

**Motivazione:** Feedback dell'utente: la resa era troppo "videogioco". Obiettivo = credibilità da strumento professionale.

**Risultato osservato:** Look strumentale coerente su tutte le viste; il colore ora "significa" (stato gomme/pressioni).

**Verifica:** `tsc --noEmit` 0 err; rotte `/ /console /telemetry /setup /login` 200; `test_parser` 12/12.

**File protetti:** nessuno toccato (solo `frontend/src/` + `globals.css`).

**Decisione:** ☑ Mantenuto, **committato e pushato** (previo «ok push»). Megaprompt #2 chiuso.

---

## ▸ Prossimo: MEGAPROMPT #3 — 5 rework di rifinitura (APERTO)

> Dossier di dettaglio in `REDESIGN_REWORK_REPORT.md` (gitignorato). **Input primario = SCREENSHOT**
> che l'utente allegherà: il "cosa non va" preciso si legge nelle immagini. Lavoro previsto a FASI.

| # | Area | File | Nodo |
|---|------|------|------|
| **#4** | Schermata **Setup** nel suo insieme | `app/setup/page.tsx`, `globals.css` | Layout/gerarchia/densità dei selettori e 49 slider da rivedere |
| **#5** | **LapTable** giro-per-giro | `components/charts/LapTable.tsx` | Pulita ma "spoglia" → più data-logger (header raggruppati, hover) |
| **#6** | **Sidebar** | `components/ui/Sidebar.tsx` | Troppo vuota → nota reale di Gigi (`/api/analysis`), mini-metriche |
| **#7** | **KPI/grafici Dashboard** stile MoTeC + ingrandibili | `app/page.tsx`, `Sparkline.tsx` | Rework di **maggior valore** |
| **#8** | **Fix DnD card estese** | `app/page.tsx` | Bug diagnosticato: riordino su indice array ≠ posizione visiva con `col-span-2` → DnD su posizione puntatore o `dnd-kit` |

_(Aggiungere qui sotto le entry man mano che i rework vengono affrontati.)_

---

<!-- TEMPLATE — copia e incolla per ogni nuova entry

## Entry #XXX — [titolo breve]

| Campo | Valore |
|---|---|
| Data | GG/MM/AAAA |
| Agente dev | Claude Code (claude-opus-4-8) |
| Area | [pagina/componente o megaprompt/FASE] |
| Commit | [hash o "non ancora committato"] |
| Contesto | [es. "REWORK #7 — grafici KPI da avvicinare a MoTeC"] |

**Catalogo messaggi:**
1. [prompt/richiesta ricevuti in questa iterazione]

**Modifica:**            [diff concettuale + file toccati]
**Motivazione:**         [problema risolto]
**Risultato osservato:** [cosa cambia a schermo]
**Verifica:**            tsc --noEmit 0 err · rotte toccate 200 · test_parser 12/12
**File protetti:**       ☐ nessuno toccato   ☐ sbloccato con «ok procedi» → [quale]
**Decisione:**           ☐ Mantenuto  ☐ Modificato ulteriormente  ☐ Rollback

-->
