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

> I **malfunzionamenti gravi** (Gigi giù, rottura backend/frontend, dati corrotti, vulnerabilità) NON
> vanno qui: si registrano in **`INCIDENTS.md`**. Qui restano le iterazioni e i fix ordinari.

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
- **Avvio dev:** `cd backend && ./.venv/Scripts/python -m uvicorn app.main:app` (:8000, **niente `--reload`**: HAZARD-V2-B) +
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

## Entry #006 — MEGAPROMPT rifiniture "MoTeC-style" (FASI 1–4) ✅

| Campo | Valore |
|---|---|
| Data | 10/07/2026 |
| Agente dev | Claude Code (`claude-opus-4-8`) |
| Area | Riferimento MoTeC + scrollbar + KPI Dashboard + tabella Telemetria |
| Commit | `253eee4` (F1) · `1682fb9` (F2) · `531e6f9` (F3) · `5ae0e20` (F4) |
| Contesto | Megaprompt intitolato "#4" dall'utente = **megaprompt #3 di rifinitura** nei log. Copre i rework **#7** (KPI) e **#5** (LapTable) + scrollbar + doc MoTeC. Input primario = screenshot. |

**Catalogo messaggi:**
1. Incollato il megaprompt "Rifiniture MoTeC-style" (FASE 0 audit + FASI 1–4).
2. Approvazioni FASE per FASE con verifica a schermo; 2 giri di screenshot sulla FASE 3.
3. Feedback: «mancano gli indici sulle ordinate» → titoli assi; «alcuni indicatori storti sull'asse Y» → unità da ruotata a orizzontale.
4. «ok push, spacchetta in 4 commit».

**Modifica (per FASE):**
- **F0 (audit):** slider Setup già con `.pw-range` (nulla da fare); scrollbar bianche su modale KPI/wrapper tabella/pagina; bug asse Y modale diagnosticato (YAxis senza `ticks`/`tickFormatter`).
- **F1:** `frontend/docs/DESIGN_REFERENCE.md` (MoTeC i2 Pro riferimento permanente) + rimando in `lib/instrument.ts`.
- **F2:** `.pw-scroll` su modale KPI (`page.tsx`) e wrapper tabella (`telemetry`); scrollbar di pagina in `globals.css`.
- **F3:** `niceStep()` + `KpiChart` condiviso (modale ↔ card estesa), assi con tick tondi + titoli (unità orizzontale + "Giro"); card estesa rende il grafico completo (`page.tsx`).
- **F4:** `LapTable` con intestazioni raggruppate + sintesi min/max/Δ; nuovo `LapChannelBars` (barre per canale); box in `telemetry/page.tsx`.

**Motivazione:** avvicinare grafici/tabelle allo standard MoTeC i2 Pro (precisione assi, Channel Report), sanare scrollbar fuori palette e il bug delle etichette Y illeggibili.

**Risultato osservato:** assi Y leggibili con scala tonda + unità; card estese al livello della modale; tabella "data-logger" con sintesi e pannello barre; nessuna barra bianca. Verificato a schermo con l'utente.

**Verifica:** `npx tsc --noEmit` 0 err (dopo ogni FASE) · rotte `/ /console /telemetry /setup /login` 200. Backend fuori scope.
**File protetti:** ☑ nessuno toccato (solo `frontend/src/` + doc; `lib/motion.ts` invariato).
**Decisione:** ☑ Mantenuto, committato in 4 commit di fase + pushato.

**Rework ancora aperti** (non in questo megaprompt): **#4** Setup, **#6** Sidebar, **#8** fix DnD card estese (vedi `INCIDENTS.md` INC-V2-005).

---

## Entry #007 — MEGAPROMPT #5: Sidebar redesign + Lap Times + viz MoTeC ✅ COMPLETO (F0–F13)

| Campo | Valore |
|---|---|
| Data | 11/07/2026 |
| Agente dev | Claude Code (`claude-opus-4-8`) |
| Area | Sidebar (blocco A) · Lap Times (blocco B) · colore best-time (blocco C) · viz MoTeC in Telemetria (blocco D) |
| Commit | `d3e536f` (Sidebar) · `053ef9e` (Lap Times + best-time) · `06643dc` (viz MoTeC) · `83a7f17` (docs) — **pushati** |
| Contesto | Quinto megaprompt, metodo a FASI (0–13) con STOP gate per fase. **TUTTE le FASI 0–13 COMPLETE**, poi committate e pushate previo «ok push». |

**Catalogo messaggi:**
1. Incollato MEGAPROMPT #5 (FASI 0–13, STOP gate + diff-only sui file protetti).
2. `ok procedi` fase per fase (0→7). **FASE 1:** scelte utente = **Opzione 1** per `lap_time` (solo demo, niente `csv_parser.py`) + **Analisi dentro Telemetria**.
3. **FASE 6:** confronto con "precedente (demo)" approvato così com'è; promemoria "carburante residuo" → salvato in memoria.
4. **FASE 7:** `ok procedi` sul diff-only del file protetto `demo_data.py`.
5. Richiesta esplicita dell'utente: **loggare ogni iterazione megaprompt nel PROMPT_LOG e gli incidenti in INCIDENTS**, seguendo i template (introdotto da questa entry).

**Modifica (per FASE):**
- **F0** — Audit read-only (nessun codice). Rilevate 2 correzioni al brief: **non esiste** `demo_session_monza_bmw.csv` (demo = `demo_data.py`); gauge a lancetta **già completo**.
- **F1** — Piano (solo testo): fix sidebar = **strategia C** (colonna `h-screen sticky` + area centrale scrollabile + footer ancorato); piano `lap_time` Opzione 1; conferma file intoccabili.
- **F2** — `Sidebar.tsx`: layout in 3 regioni (`sticky top-0 h-screen` + middle `flex-1 overflow-y-auto pw-scroll` + footer `border-t`, rimosso `mt-auto`). Risolve il vuoto a metà colonna.
- **F3** — NEW `lib/health.ts` + `components/ui/SessionHealth.tsx`: semaforo aggregato gomme/pressioni/carburante (riusa soglie esistenti, colore=stato).
- **F4** — NEW `lib/advice.ts` + `components/ui/GigiAdvice.tsx`: CTA "prossima azione" + mini-elenco ultimi consigli (da `suggested_params`); rimossa la vecchia riga singola dal footer.
- **F5** — NEW `lib/crosscheck.ts` (**estratto** da `telemetry/page.tsx`, riuso) + `SidebarSection.tsx` (sezioni comprimibili, stato in `localStorage`) + `AlertsFeed.tsx`; refactor `SessionHealth`/`GigiAdvice` a body-only.
- **F6** — NEW `MiniValues.tsx`, `QuickNotes.tsx` (note in `localStorage`), `QuickCompare.tsx` (vs "precedente demo" etichettata); footer: 2 shortcut-icona → **Confronto**/**Note**; "Storico completo" → link **"Storico sessioni · prossimamente"**. Limiti dato dichiarati (Δ giro→F7, residuo→consumo).
- **F7** — 🔒 `demo_data.py` **ADD** `LAP_TIMES` (8 tempi) + `_fmt_lap` + check coerenza col `best_lap`; `api/session.py` espone `lap_times`; `lib/telemetry.ts` tipo + `formatLapTime`; NEW `components/charts/LapTimesTable.tsx`; nuova sezione **"Tempi sul giro"** in `telemetry/page.tsx`.
- **F8** — Nuovo token semantico **best-time (fucsia `#C026D3`)**: `theme.ts` (`COLORS.best`) + `instrument.ts` (`STATE.best`, uso esclusivo, convenzione F1). Applicato al giro più veloce in `LapTimesTable` (marker `PB` + tempo). Riusabile in F9.
- **F9** — NEW `components/charts/LapDeltaChart.tsx`: grafico a barre del **Δ tempo** (toggle riferimento *giro precedente*/*media stint*, barre verde=più veloce/ambra=più lento, giro più veloce **fucsia**) + tabella delta multi-canale (tempo/consumo/temp max/pressione vs giro precedente). Nuova sezione **"Delta giro-su-giro"** in `telemetry/page.tsx`. _(Edoardo: prima versione ok ma con **inesattezze** non specificate da rivedere dopo → promemoria in memoria.)_
- **F10** — NEW `components/charts/TyreOverlay.tsx`: overlay delle 4 gomme sugli stessi assi con toggle **Temperatura/Pressione** (riusa colori TYRE_SERIES + soglie limite temp/finestra pressioni). Nuova sezione **"Overlay gomme · FL/FR/RL/RR"** in `telemetry/page.tsx`.
- **F10-fix (da screenshot Edoardo)** — sovrapposizione **legenda ↔ etichetta "Giro"** dell'asse X in `LapDeltaChart` e `TyreOverlay`. Causa: label X posizionata `insideBottom` ignorava lo spazio riservato a tick/legenda. Fix: rimossa la label X interna → didascalia HTML "Giro" sotto il grafico; nell'overlay **legenda spostata in alto** (`verticalAlign="top"`). Solo presentazione.
- **F11** — NEW `components/charts/ChannelHistogram.tsx`: **istogramma** distribuzione di un canale selezionabile (tempo giro / consumo / temp Post.DX / press Post.DX) su 5 fasce; fasce fuori-spec colorate per soglia (temp>limite=alarm, press fuori finestra=warn). Nuova sezione **"Analisi · Distribuzione (istogramma)"** in `telemetry/page.tsx`. Didascalie in HTML (no label X interne).
- **F11-fix (da screenshot Edoardo)** — l'hover sui grafici a barre mostrava il **cursor rettangolo grigio chiaro** di default Recharts che oscurava/lavava la barra (illeggibile su tema scuro). Fix: `Tooltip cursor={{ fill: COLORS.text, fillOpacity: 0.06 }}` (highlight sottile non invasivo) su `ChannelHistogram` **e** `LapDeltaChart`. Solo presentazione.
- **F11-fix2 (da screenshot Edoardo)** — nel tooltip dei grafici a barre la riga item (es. "Giri : 1") restava **nera/illeggibile**: le barre sono colorate via `<Cell>` e il `<Bar>` non ha `fill` proprio → Recharts usa il fallback nero per il testo item. Fix: `labelStyle={{color: COLORS.text}}` + `itemStyle={{color: COLORS.subtle}}` sui Tooltip di `ChannelHistogram` e `LapDeltaChart`. Solo presentazione.
- **F12** — NEW `components/charts/SetupRadar.tsx`: **radar/spider** bilanciamento su un giro selezionato (stepper ◀▶, default ultimo giro). 4 gomme disposte come sull'auto (`startAngle=135`), 2 poligoni sovrapposti **Temperatura (rosso) + Pressione (blu)** normalizzati 0–100 nel giro (la forma = squilibrio), **tooltip custom** coi valori reali. Nuova sezione **"Analisi · Bilanciamento (radar)"** in `telemetry/page.tsx`.
- **F12-fix (da screenshot Edoardo)** — radar troppo piccolo/confuso (cerchio vincolato dall'altezza in card larga). Fix: contenitore `max-w-md mx-auto` (radar quadrato e grande) + height 260→360 + `outerRadius 80%` + `strokeWidth 2` sugli outline. Solo presentazione.
- **F12-fix2 (proposta Edoardo: troppo vuoto ai lati)** — `SetupRadar` riorganizzato a **2 colonne**: radar (sx) + pannello **Snapshot giro** (griglia 2×2 valori reali temp/press per gomma, colorati per soglia) + **Bilanciamento** (Δ Ant↔Post e SX↔DX su temp/press). Riempie lo spazio con informazione pertinente al bilanciamento setup. Solo presentazione.
- **F13** — Verifica finale + changelog (nessuna modifica di codice). Controllo file protetti: **solo `demo_data.py`** toccato (aggiunta autorizzata in F7, **0 righe rimosse**); `agent.py`/`csv_parser.py`/`setup_params.py`/`vision_parser.py`/`car_setup_ranges.json`/`prompts/`/`lib/motion.ts` **intatti** (verificato con `git diff --quiet`).

**Motivazione:** Sidebar troppo vuota/densità mal gestita; mancava l'elenco dei **tempi giro** (solo `best_lap` isolato); porre le basi dati (lap_times) e cromatiche (viola) per le viz MoTeC.

**Risultato osservato:** Sidebar full-height senza vuoto, con semaforo + avvisi + consigli + mini-values + confronto/note; sezione "Tempi sul giro" con 8 giri, Δ sul best e giro più veloce evidenziato (`PB`).

**Verifica:** F2–F6 `npx tsc --noEmit` **0 err** + rotte toccate **200**. F7 anche: backend `test_parser` **12/12**, coerenza `min(LAP_TIMES)`→`1:47.812`==`best_lap`, `/api/session` espone `lap_times` (dopo **riavvio pulito** del backend — vedi **HAZARD-V2-B** in INCIDENTS: `--reload` serviva codice stale su Windows).
**Verifica finale (F13):** `npx tsc --noEmit` **0 errori** · rotte `/ /console /telemetry /setup /login` **tutte 200** · backend `test_parser` **12/12** · file protetti intatti (solo `demo_data.py` con sola aggiunta).

**File protetti:** F0–F6 ☑ **nessuno toccato**. **F7:** `demo_data.py` **sbloccato con «ok procedi»** → **solo AGGIUNTA** (`LAP_TIMES` + helper + check), **nessun numero esistente modificato**; `csv_parser.py` **NON toccato** (Opzione 1).

**Decisione:** ☑ FASI 0–13 **mantenute**. Megaprompt #5 **COMPLETO e verificato**, poi **committato in 4 commit logici e pushato** previo «ok push» (`main == origin` a `83a7f17`).

**Rif.:** HAZARD-V2-B (INCIDENTS.md); memoria promemoria "carburante residuo".

---

## Entry #008 — MEGAPROMPT #6: semplificazione UX (Sidebar + Telemetria) + Login/Google Sign-In ✅ COMPLETO (F0–F10)

| Campo | Valore |
|---|---|
| Data | 11/07/2026 |
| Agente dev | Claude Code (`claude-opus-4-8`) |
| Area | BLOCCO A Sidebar (fusione salute+avvisi) · BLOCCO B Telemetria (tab, corsie i2 Pro) · BLOCCO C Login/Google Sign-In |
| Commit | `48105ef` (auth/route group) · `6ab4097` (docs entry + chiusura INC-V2-004) — retro-compilato il 13/07 |
| Contesto | Sesto megaprompt: la Telemetria post-#5 è troppo densa ("PC della NASA", stesso dato gomme fino a 8 forme). Principio guida: checklist semplicità Jobs/Apple a ogni STOP gate + rigore MoTeC invariato. |

**Catalogo messaggi:**
1. Incollato MEGAPROMPT #6 (FASI 0–10, 3 blocchi, checklist semplicità sezione 0 come criterio d'accettazione).
2. `ok, procedi` sul report FASE 0 (audit read-only).
3. `ok procedi` sul piano FASE 1 + decisioni: **UserChip nella Sidebar** approvato; richiesta di documentare in PROMPT_LOG/INCIDENTS come da standard; spiegazione fornita per reperire il Google Client ID (Cloud Console, OAuth client web, origini localhost:3000, popup senza redirect URI).

**Modifica (per FASE):**
- **F0** — Audit read-only. Baseline duplicazione: temp gomme in **6–8 forme**, pressioni in **6** nella stessa pagina Telemetria; cross-check (il più actionable) ultimo in pagina. Nessuna lib auth presente; `@react-oauth/google` 0.13.5 compatibile React 19 (peer `>=16.8`). `/login` prende la Sidebar dal root layout → causa di INC-V2-004 → soluzione: route group `(app)`/`(auth)`. Snapshot 2×2 di `SetupRadar` estraibile a basso rischio. **Scoperta:** il placeholder "N" in alto a destra NON è nostro codice — è l'indicatore dev di Next.js → il chip profilo (F9) va creato da zero. File protetti: zero coinvolti in tutti e 3 i blocchi.
- **F1** — Piano file-per-file approvato: 6 file nuovi (`HealthStatus`, `Tabs`, `TelemetryLanes`, `TyreSnapshotGrid`, `ChannelReport`, `lib/auth.ts`+`UserChip`), 2 rimossi a fine F5 (`TempLineChart`, `TyreOverlay`), route group con 5 file spostati. Libreria Sign-In: **`@react-oauth/google`** (client-side puro, popup reale, niente sessione server = spec F9, no peso next-auth pre-esame).
- **F2** — NEW `components/ui/HealthStatus.tsx`: fusione a 2 stati (collassato = semaforo `SessionHealth`; espanso = + lista `AlertsFeed` nello stesso blocco). Composizione pura dei 2 componenti esistenti, zero soglie/logiche nuove. MOD `Sidebar.tsx`: le 2 `SidebarSection` "Salute sessione"+"Avvisi" → 1 sola, badge = stato aggregato + conteggio avvisi (visibile anche compressa).

- **F3** — MOD `telemetry/page.tsx`: **header fisso**. Cross-check spostato da ultimo blocco in fondo a **prima cosa in pagina** (reso riga orizzontale compatta `flex-wrap` invece di lista verticale); sotto, heatmap + 4 gauge pressioni **affiancati** (grid 1/3+2/3, gauge in 2×2); `TempLineChart` scesa sotto come blocco temporaneo (sarà sostituita in F5). Vecchio blocco cross-check in fondo rimosso. Nessuna KPI nuova (no mini-dashboard).

- **F4** — NEW `components/ui/Tabs.tsx` (switcher generico: mono uppercase, underline accent, niente glow). MOD `telemetry/page.tsx`: tutto il contenuto sotto l'header fisso entra in 2 tab — **"Tempi"** (LapTimesTable + LapDeltaChart, invariati dentro) e **"Analisi"** (provvisoria: line chart temp, TyreOverlay, Istogramma, Radar, LapTable, LapChannelBars spostati dentro senza modifiche — F5/F6 li trasformeranno). Dentro le tab niente motion wrapper (il cambio tab non ri-anima).

- **F5** — NEW `charts/TyreSnapshotGrid.tsx` (**estratto** dallo Snapshot di `SetupRadar`, componente condiviso, zero duplicazione) + NEW `charts/TelemetryLanes.tsx`: 2 corsie sottili impilate (Temperatura 150px + Pressione 130px), **stesso asse X**, **un solo cursore sincronizzato** (`syncId` Recharts), soglia 95° tratteggiata solo su corsia temp col **tratto oltre soglia ridisegnato in rosso** (serie `*Over` con null fuori soglia), finestra pressioni tratteggiata su corsia press; tooltip **muti** (content null, solo cursore) → i numeri esatti vivono UNA volta sola nel box **"Valori"** a lato (riusa TyreSnapshotGrid, default ultimo giro, hover/tap aggiorna). MOD `SetupRadar.tsx`: usa TyreSnapshotGrid (rimossi GRID/tc/pc inline). MOD `telemetry/page.tsx`: nella tab Analisi le 2 card line-chart-temp + overlay → 1 card "Andamento gomme" con le corsie. `TempLineChart.tsx`/`TyreOverlay.tsx` non più importati, **file su disco finché Edoardo non conferma a schermo** (poi rimozione).

- **F5-fix (da screenshot Edoardo)** — (a) sulla corsia Temperatura i punti del tratto oltre soglia (Post.DX) apparivano **rossi fissi invece che evidenziati all'hover** come le altre serie: la Line `*Over` aveva dot statici propri (r=2 alarm) e `activeDot={false}` → rimossi i dot statici. (b) box "Valori" con **spazio vuoto sotto**: aggiunte 2 statistiche del giro attivo che seguono il cursore — **Tempo giro** (fucsia `STATE.best` + badge `PB` se migliore, altrimenti Δ dal best) e **Consumo** (`fuel_per_lap`). Dati già esposti, nessun numero nuovo.
- **F5-fix2 (tentativo, superato)** — ipotesi doppio activeDot: serie over resa muta (`dot/activeDot=false`). Non risolveva: il problema non era l'hover.
- **F5-fix3 (RISOLUTIVO — primo screenshot effettivamente analizzato: gli allegati in chat non arrivavano, recuperato da `OneDrive/Immagini/Catture di schermata`)** — i marker di TUTTE le serie sono **pallini bianchi** (fill default Recharts); la linea over, **più spessa e disegnata sopra la base, copriva i pallini bianchi** della Post.DX sul tratto oltre soglia → punti "rossi/assenti" solo lì. Fix: la serie over ridisegna **gli stessi marker standard** (`dot={{r:1.6,strokeWidth:0}}` + `activeDot={{r:3}}`); base e over per Post.DX hanno lo stesso colore (accent) → sovrapposizione invisibile, marker identici ovunque.

- **F5 chiusa** — «ok tutto a posto» di Edoardo dopo F5-fix3 → **rimossi** `TempLineChart.tsx` e `TyreOverlay.tsx` (orfani, non più importati). `tsc` 0 err dopo la rimozione.
- **F6** — NEW `charts/ChannelReport.tsx`: unifica **LapTable** (tabella giro-per-giro) e **LapChannelBars** (barre per canale) in un solo componente con switch **Tabella ↔ Grafico** (come il Channel Report di i2 Pro); min/max/Δ leggibili in entrambe le modalità (sintesi in tabella, header card nelle barre). Riuso puro: i 2 componenti esistenti diventano interni. MOD `telemetry/page.tsx`: 2 card → 1 card "Channel report · giro per giro".

- **F7** — Assemblaggio tab Analisi (ordine corsie→istogramma→radar→channel report già corretto da F5/F6). Puliti i titoli ridondanti ("Analisi · X" → "X" dentro la tab Analisi). **2 decisioni di ridondanza prese CON Edoardo** (domanda esplicita, opzioni + raccomandazione): (1) **Snapshot 2×2 rimosso dal radar** — stessa griglia dello stesso componente 2 volte nella stessa tab; il radar tiene stepper + Bilanciamento (unico), i valori esatti vivono solo nel box "Valori" delle corsie; (2) **tabella delta di LapDeltaChart sfoltita a Δtempo+Δconsumo** — rimosse colonne Δtemp max/Δpress (canali della tab Analisi; la tab Tempi resta sul cronometro), rimossi calcoli `tempMax`/`pressAvg` e semplificato `deltaColor`. Conteggio duplicazione per il gate: baseline **8 forme** contemporanee → **2 al primo colpo d'occhio** (heatmap+gauge header) + 5 nella tab Analisi mai tutte insieme.

- **F8 (BLOCCO C)** — **Route group** (fix INC-V2-004): `app/(app)/` con NEW `(app)/layout.tsx` (Sidebar + main + MotionProvider) e pagine `page/console/telemetry/setup` spostate dentro con **`git mv`**; `app/(auth)/login/` con NEW `(auth)/layout.tsx` (nessuna Sidebar, card centrata full-screen); root `layout.tsx` ridotto a fonts+globals. URL invariati. Restyling login: centering demandato al layout, filetto accent in testa alla card (linguaggio PageHeader). **Gotcha post-spostamento:** `tsc` falliva sui tipi **stale** generati in `.next/types` (vecchi path) → `rm -rf .next/types/app` + re-hit rotte → rigenerati, 0 err. **INC-V2-004 spostato in RISOLTI** su INCIDENTS.md con nota di scope (auth-gate deliberatamente escluso, decisione megaprompt #6 §1).

- **F9 — VERIFICATA end-to-end da Edoardo:** popup "Continua su PitWall.AI" (dopo rename Branding: il client Sheets della lezione era nello stesso progetto e il nome app è per-progetto), login con account reale, profilo nel chip, ⏻ Esci, login-first su nuova tab. Troubleshooting OAuth documentato: "no registered origin"/401 invalid_client → mancavano le Origini JavaScript autorizzate (`http://localhost:3000` + `http://localhost`); nome popup errato → Branding di progetto, non nome client.
- **F9 (BLOCCO C)** — **Google Sign-In reale** + 2 richieste aggiuntive di Edoardo (logout; login sempre prima schermata). Client ID fornito da Edoardo → `frontend/.env.local` (`NEXT_PUBLIC_GOOGLE_CLIENT_ID`, gitignorato-verificato; **client secret NON usato né salvato** — flusso popup non ne ha bisogno; consigliata rigenerazione a Edoardo perché incollato in chat). Installato `@react-oauth/google@0.13.5`. NEW `lib/auth.tsx` (AuthProvider/useAuth: profilo in **sessionStorage** → muore con la tab → login sempre prima schermata di una nuova visita; decodifica JWT manuale base64url/UTF-8, zero dipendenze, zero logging — GDPR), NEW `ui/Providers.tsx` (GoogleOAuthProvider+AuthProvider nel root layout), NEW `ui/AuthGate.tsx` (gate client-side nel layout `(app)`: senza accesso → redirect `/login`, `return null` anti-flash; NON è confine di sicurezza server — scelta di progetto §1), NEW `ui/UserChip.tsx` (foto/nome/email reali o 🏁 Pilota demo + bottone **⏻ Esci** → signOut+`/login`) agganciato nell'header della Sidebar. MOD login page: bottone `GoogleLogin` reale (`theme=filled_black`; prop `locale` rimossa: non nel tipo TS), redirect se già loggato, nota privacy in card; **rimosso il form email/password finto** (con Sign-In reale accanto un form che non autentica stonava — decisione F9, reversibile). Restart dev server per caricare `.env.local`.

**Motivazione:** stesso avviso (es. Post.DX oltre soglia) appariva 2 volte nello scroll della Sidebar (semaforo + lista); ridurre lo scroll verticale mobile. In Telemetria l'informazione più actionable (cross-check) era l'ULTIMA visibile e 11 blocchi erano impilati senza gerarchia; l'andamento gomme era rappresentato da 2 grafici pieni separati (line chart + overlay con toggle) e i dati per giro da 2 pannelli impilati (tabella + barre). La /login ereditava la Sidebar dal root layout (INC-V2-004) e mancavano Sign-In vero, logout e un ingresso obbligato dal login.
- **F10** — Verifica finale + documentazione (nessuna modifica di codice, vedi sotto).

**Risultato osservato:** Sidebar con una sezione salute+avvisi a 2 stati; Telemetria = cross-check in testa + heatmap/gauge sempre visibili + 2 tab (Tempi cronometrica, Analisi con corsie sincronizzate/istogramma/radar/channel report); login prima schermata sempre (sessionStorage), Google Sign-In reale con profilo nel chip Sidebar e ⏻ Esci. Ogni fase verificata a schermo da Edoardo.

**Bilancio semplicità (checklist sezione 0, numeri prima→dopo):** forme del dato gomme visibili insieme **8 → 2** (header; 5 in tab Analisi mai simultanee); blocchi impilati in Telemetria **11 → 3 fissi + 2 tab**; duplicazioni eliminate: avvisi Sidebar 2×→1, line-chart+overlay→corsie uniche, tabella+barre→Channel Report a modalità, snapshot radar rimosso (=box Valori), delta multi-canale sfoltito, form login finto rimosso.

**Verifica finale (F10):** `npx tsc --noEmit` **0 errori** · rotte `/ /console /telemetry /setup /login` **tutte 200** · backend `test_parser` **12/12** · **file protetti tutti intatti** (`git diff --quiet` su agent/csv_parser/setup_params/vision_parser/demo_data/demo_responses/car_setup_ranges/prompts/ + `lib/motion.ts`) · `.env.local` fuori dal tracking git (verificato). Google Sign-In verificato **end-to-end da Edoardo** («ok tutto giusto e vedo pure il nome utente»).

**File protetti:** ☑ nessuno toccato in tutto il megaprompt #6.
**Decisione:** ☑ Megaprompt #6 **COMPLETO e verificato** (F0–F10). **NON committato/pushato**: in attesa dell'«ok push» esplicito di Edoardo. INC-V2-004 chiuso su INCIDENTS.md.

---

## Entry #009 — Licenza MIT + copyright in UI

| Campo | Valore |
|---|---|
| Data | 11/07/2026 |
| Agente dev | Claude Code (`claude-fable-5`) |
| Area | root (LICENSE, README) · login page · Sidebar footer |
| Commit | `47ac309` — retro-compilato il 13/07 |
| Contesto | Igiene pre-"post building": la v1 Streamlit aveva la MIT, la v2 no. |

**Catalogo messaggi:**
1. Richiesta licenza MIT come sulla v1.
2. Richiesta copyright nella pagina di login "e dove pensi sia migliore".

**Modifica:** NEW `LICENSE` (testo MIT identico alla v1, © 2026 Edoardo Ferlito) · MOD `README.md` (sezione "Licenza" finale) · MOD `(auth)/login/page.tsx` (riga footer card → "Progetto d'esame · © 2026 Edoardo Ferlito · Licenza MIT") · MOD `ui/Sidebar.tsx` (footer, sotto "v0.1.0 · v2 scaffold": riga "© 2026 Edoardo Ferlito · MIT", visibile su tutte le pagine dell'app).
**Motivazione:** repo pubblica senza licenza = tutti i diritti riservati di default; copyright visibile in UI su ingresso (login) e su ogni vista (Sidebar).
**Risultato osservato:** riga copyright nella card login e nel footer Sidebar, stesso stile mono/muted esistente.
**Verifica:** `tsc --noEmit` 0 err · `/` e `/login` 200 · backend/file protetti non toccati.
**File protetti:** ☑ nessuno toccato
**Decisione:** ☑ Mantenuto · in attesa di «ok push»

---

## Entry #010 — MEGAPROMPT #7: Sidebar sticky+snellita · icone nav · Scatter · Confronto sessioni · carburante residuo ✅ COMPLETO (F0–F10)

| Campo | Valore |
|---|---|
| Data | 12/07/2026 |
| Agente dev | Claude Code (`claude-fable-5`) |
| Area | Sidebar (2 zone + consolidamento) · nav icons · tab Analisi (Istogramma→Scatter) · Confronto sessioni · TODO carburante |
| Commit | `c1e8059` (F5–F6) · `9047005` (F2–F4, F7–F8) · `b3dc71d` (F9) · `4398c79` (docs) · licenza in `47ac309` — retro-compilato il 13/07 |
| Contesto | Settimo megaprompt (F0–F10). Estende la checklist Jobs/Apple del #6 alla Sidebar; scatter i2 Pro al posto dell'istogramma; chiude il TODO carburante residuo. Deadline 15/07 → robustezza sopra ambizione. |

**Catalogo messaggi:**
1. Incollato MEGAPROMPT #7 (FASI 0–10).
2. `procedi` sul report FASE 0.
3. `ok procedi, ricordati la documentazione` sulla diagnosi FASE 1.

**Modifica (per FASE):**
- **F0** — Audit read-only: (1) fusione Salute/Avvisi **già reale** nel #6 (`HealthStatus.tsx` unico componente a 2 stati; SessionHealth/AlertsFeed solo interni); (2) nav DENTRO la zona scrollabile → F2 necessaria; (3) **nessun secondo dataset demo** (demo_data.py = solo Monza asciutto 8 giri; demo_responses.py = solo markdown console) → F7 orienta al fallback giri 1–4 vs 5–8; (4) capacità serbatoio assente ovunque → costante frontend (proposta: `lib/catalog.ts`, 125 L BMW M4 GT3 in ACC), **niente STOP gate protetti**; (5) istogramma = `charts/ChannelHistogram.tsx` montato in tab Analisi (sopra il radar, ordine: corsie→istogramma→radar→channel report). Extra: `lucide-react` NON è dipendenza.
- **F1** — Diagnosi Sidebar con checklist Jobs per blocco. Proposta approvata: nav → header fisso; **rimossi** MiniValues (Δ giro placeholder morto, Giro statico, Consumo già in Dashboard), card "Sessioni recenti" (duplicato esatto di Sessione corrente; resta la riga Storico·prossimamente), widget Gigi dal footer (badge online migra sulla sezione Gigi consiglia); "Ultimi consigli" 3 voci → 1 CTA + link "vedi tutti → Console". Bilancio corpo: 6 blocchi → 3 + 1 riga.
- **F2** — MOD `ui/Sidebar.tsx`: `<nav>` spostato dal corpo scrollabile all'header fisso (dopo UserChip). I 4 tasti restano visibili a qualunque scroll. Diff 36+/30− (solo spostamento + commenti). **Confermato a schermo da Edoardo.**
- **F3** — Consolidamento come da diagnosi F1 approvata. MOD `ui/Sidebar.tsx`: rimossi il blocco MiniValues, la card "Sessioni recenti" (duplicato di Sessione corrente; la riga "Storico sessioni · prossimamente" resta, standalone dopo Gigi consiglia) e il widget Gigi dal footer; badge `● online` migrato sulla sezione "Gigi consiglia"; import GigiAvatar/MiniValues rimossi. MOD `ui/GigiAdvice.tsx`: rimosso il mini-elenco "Ultimi consigli" (3 voci → tutte puntavano a /console), resta la CTA "Prossima azione" + link "vedi tutti →". Corpo sidebar: **6 blocchi → 3 + 1 riga**. **Confermato a schermo da Edoardo** → `MiniValues.tsx` orfano cancellato (prassi F5 del #6).
- **F4** — NEW `ui/NavIcons.tsx`: 4 icone SVG line-style (`IconDashboard` griglia card · `IconConsole` eco dell'headset GigiAvatar · `IconTelemetry` traccia su assi · `IconSetup` slider verticali) — mono-linea `currentColor`, stroke 1.6/24, cap/join round, zero fill: stessa famiglia dell'headset di Gigi (lucide-react non è dipendenza → SVG custom come da megaprompt). MOD `ui/Sidebar.tsx`: NAV usa i componenti icona; stato attivo ridisegnato da pillola piena `bg-accent` → **barra accent sinistra** (motion.span `layoutId` conservato: la barra scivola tra le voci) + `bg-raised` + icona `text-accent` (hover `accent-hover` #CC0028), pattern coerente col filetto sinistro di Sessione corrente/Gigi consiglia; `aria-current="page"` aggiunto. Route e testi invariati.

- **F5** — MOD `telemetry/page.tsx`: rimossa la card "Distribuzione (istogramma)" dalla tab Analisi (import incluso); Bilanciamento/Radar e Channel report intatti. **Confermato a schermo da Edoardo** → `ChannelHistogram.tsx` orfano cancellato.
- **F6** — NEW `charts/ScatterPlot.tsx` ("Correlazione canali", stile i2 Pro), montato nello slot dell'istogramma (tab Analisi, sopra il radar). Un punto = un giro; selettori chip X/Y su **10 canali già esposti** (Tempo giro, Consumo, Temp×4, Press×4 — zero canali nuovi); giro PB in fucsia `STATE.best` (Cell dedicata + legenda minima + "· PB" nel tooltip); tooltip = giro + valori X/Y esatti (tempo giro in `formatLapTime`); assi `domain=[dataMin,dataMax]` (min/max reali, no padding), hairline grid, tick monospace, didascalie unità in HTML orizzontale (lezione F10-fix #5), zero glow, `isAnimationActive={false}`. Default didattico: X=Temp Post.DX · Y=Tempo giro (la storia demo: surriscaldamento → degrado).

- **F7** — Diagnosi confronto (no codice). Scoperta: "⇄ Confronto" non era un placeholder ma apriva `QuickCompare`, mini-tabella con sessione "precedente" **statica finta** hardcoded client-side (`PREV`). Proposta approvata da Edoardo: **opzione A** (fallback giri 1–4 vs 5–8 della sessione corrente, zero dati nuovi/protetti — scelta di scope dichiarabile all'esame) + **rimozione di QuickCompare/PREV** (via 4 numeri inventati; un solo "confronto" sotto il bottone).
- **F8** — NEW `charts/StintCompare.tsx` (`StintCompareModal`): modal overlay (pattern KpiModal: Esc/click-fuori, raggiungibile da ogni pagina) col confronto metà stint — corsia unica 2 serie sovrapposte su giro relativo 1–4 (metà 1 blu / metà 2 ambra = identità serie, idioma TYRE_SERIES), selettore canale chip sui **10 canali riusati** via `buildChannels` **esportata da ScatterPlot** (zero duplicazione), tooltip muto + cursore, sintesi sotto: media metà 1 · media metà 2 · **Δ colorato** (verde/rosso per tempo/consumo/temp; neutro per pressioni, idioma QuickCompare); etichetta onesta "stessa sessione · demo". MOD `ui/Sidebar.tsx`: bottone ⇄ da toggle pannello footer a **launcher del modal** (`aria-haspopup="dialog"`, AnimatePresence); `footerPanel` ridotto a `"notes" | null`. `QuickCompare.tsx` orfano, **su disco finché Edoardo non conferma**, poi rimozione.

- **F9** — Carburante residuo (chiude il TODO aperto dal #5/F6). MOD `lib/catalog.ts`: NEW costante `DEMO_TANK_CAPACITY_L = 125` (serbatoio BMW M4 GT3 in ACC; demo, frontend-only — `demo_data.py` protetto INTATTO, un punto solo da cui correggere). MOD `charts/TelemetryLanes.tsx` (box "Valori", posizione scelta: accanto a Consumo): riga "Residuo stimato ~X L" = capacità − consumo **cumulato fino al giro attivo** (segue il cursore come le altre statistiche); assunzione dichiarata in UI: "serbatoio 125 L · pieno al via (demo)". Nessuna cifra duplicata (il residuo non esiste altrove; Consumo resta il per-giro). `QuickCompare.tsx` orfano cancellato dopo conferma F8.

- **F10** — Verifica finale + documentazione (nessuna modifica di codice). Nota richiesta dal megaprompt: la fusione Salute/Avvisi dichiarata nel #6 era **già completa** (accertato in F0) → **niente da annotare** su INCIDENTS/SPEC_ERRATA; la F3 ha fatto solo consolidamenti ulteriori.

**Motivazione:** la nav spariva scrollando la sidebar; il corpo sidebar duplicava dati (stessa sessione in 2 card, consumo in 3 posti, Gigi rappresentato 2 volte, Δ giro placeholder mai riempito); le icone nav erano emoji miste; l'istogramma distribuiva un canale solo senza mostrare relazioni tra canali; il "confronto" usava una sessione precedente finta hardcoded; il residuo carburante era un TODO aperto dal #5.

**Risultato osservato:** nav sempre visibile (header fisso a 2 zone); corpo sidebar 6 blocchi → 3 + 1 riga; 4 icone line-style famiglia GigiAvatar con barra accent scorrevole sull'attiva; tab Analisi con "Correlazione canali" (scatter XY, PB fucsia) al posto dell'istogramma; "⇄ Confronto" apre il modal metà stint (giri 1–4 blu vs 5–8 ambra, Δ colorati) su dati reali; box Valori con "Residuo stimato" che segue il cursore (125 L − cumulato, assunzione dichiarata). Ogni fase verificata a schermo da Edoardo.

**Bilancio semplicità (numeri prima→dopo):** blocchi corpo sidebar **6 → 3+1 riga** · rappresentazioni di Gigi in sidebar **2 → 1** · card sessione duplicate **2 → 1** · numeri demo inventati client-side (PREV QuickCompare) **4 → 0** · file componenti: −3 cancellati (MiniValues, ChannelHistogram, QuickCompare) +3 nuovi (NavIcons, ScatterPlot, StintCompare) con `buildChannels` condivisa.

**Verifica finale (F10):** `npx tsc --noEmit` **0 errori** · rotte `/ /console /telemetry /setup /login` **tutte 200** · backend `test_parser` **12/12** · **file protetti tutti intatti** (`git diff --quiet` su agent/csv_parser/setup_params/vision_parser/demo_data/demo_responses/car_setup_ranges/prompts/ + `lib/motion.ts`). Diff totale: **11 file modificati (193+/295−, netto −102 righe) + 4 nuovi** (LICENSE, NavIcons, ScatterPlot, StintCompare), 3 cancellati.

**File protetti:** ☑ nessuno toccato in tutto il megaprompt #7.
**Decisione:** ☑ Megaprompt #7 **COMPLETO e verificato** (F0–F10). **NON committato/pushato**: in attesa dell'«ok push» esplicito di Edoardo. Include anche Entry #009 (LICENSE+copyright) nel working tree.

---

## Entry #011 — Favicon bandiera a scacchi

| Campo | Valore |
|---|---|
| Data | 12/07/2026 |
| Agente dev | Claude Code (`claude-fable-5`) |
| Area | `frontend/src/app/icon.svg` (nuovo) |
| Commit | `5960cda` |
| Contesto | Fix al volo richiesto da Edoardo mentre prepara gli screenshot: favicon nella tab del browser accanto al nome PitWall. |

**Catalogo messaggi:**
1. «piccolo fix al volo: mi aggiungeresti il favicon […] di una bandiera a scacchi»

**Modifica:**            NEW `src/app/icon.svg` — bandiera a scacchi 4×4 a tutto canvas (celle `#F4F4F5` su `#101014`, angoli arrotondati via clipPath), leggibile anche a 16px. Nessun altro file toccato: Next App Router rileva `app/icon.svg` automaticamente (zero modifiche a `layout.tsx`).
**Motivazione:**         La tab del browser non aveva icona (nessun favicon nel progetto, `public/` assente).
**Risultato osservato:** `GET /icon.svg` → 200 `image/svg+xml`; link `icon.svg?<hash>` presente nel `<head>`. **Confermato a schermo da Edoardo** («si vede, mi piace così»).
**Verifica:**            rotta `/icon.svg` 200 · `/` 200 · nessun file TS toccato (tsc non applicabile)
**File protetti:**       ☑ nessuno toccato
**Decisione:**           ☑ Mantenuto

---

## Entry #012 — MEGAPROMPT #8 · FASE 0: fix pressioni ACC v1.9 (shift −2.5, finestra caldo 26.0–27.0)

| Campo | Valore |
|---|---|
| Data | 12/07/2026 |
| Agente dev | Claude Code (`claude-fable-5`) |
| Area | Dati demo pressioni (protetti, sbloccati per la FASE 0) + finestra Setup e scala gauge frontend |
| Commit | `adabee2` |
| Contesto | Megaprompt #8, FASE 0 isolata. La finestra 28.5–30.0 psi a caldo era obsoleta: ACC v1.9 (dry DHF) usa 26.0–27.0 per tutte le GT, salita freddo→caldo ~1.5–2.0 psi (non 2.5–3.5). |

*(Commit: `fix(demo): pressioni ACC v1.9 — shift -2.5, finestra caldo 26.0-27.0` — include SPEC_ERRATA.md e questa entry.)*

**Catalogo messaggi:**
1. Incollato MEGAPROMPT #8 (FASE 0 + feature "A Lezione con Gigi", FASI 1–4).
2. Al gate parametri: scelta salita **+1.5 uniforme** (opzione consigliata, csv_parser intatto) + extra scope prompt v4/chat e esempio vision_parser.
3. «ok va tutto bene ma aspettiamo» → applicazione rimandata a sessione fresca.
4. «ok riprendiamo il lavoro. procedi con la fase 0.»

**Modifica (proposta solo-diff approvata al gate, poi applicata):**
- **`demo_data.py`** 🔓 — `HOT_PRESSURES` 29.0/29.2/28.2/28.0 → **26.5/26.7/25.7/25.5**; `HOT_PRESS_WINDOW` (28.5,30.0) → **(26.0,27.0)**; `HOT_PRESS_SERIES` −2.5 su tutti i 32 valori; `COLD_PRESSURES` 26.5/26.5/25.7/25.5 → **25.0/25.2/24.2/24.0** (delta uniformato a +1.5: prima la fr era +2.7); `COLD_PRESS_WINDOW` (26.0,27.0) → **(24.5,25.5)**; `PRESS_AVG_HOT` derivato 28.6 → 26.1; commenti riscritti (rif. ERR-02).
- **`demo_responses.py`** 🔓 — 6 righe: valori a caldo 28.2/28.0 → 25.7/25.5, finestra → 26.0–27.0 (righe 10/22/61), correzione «+1.0 · RL 24.2→25.2 · RR 24.0→25.0» (righe 17/64), nota salita «~2.5–3.5» → «~1.5–2.0» (riga 24). Narrazione INVARIATA.
- **`setup_params.py`** 🔓 — default slider pressioni: fl/fr 26.5 → 25.0, rl/rr 26.8 → 25.3 (min/max/step invariati).
- **`prompts/system_prompt_v4.txt`** 🔓 — righe 38/102/103/104: range freddo 24.5–25.5, salita 1.5–2.0, target freddo 25.0, target caldo 26.5 range 26.0–27.0. **`prompts/chat_system_prompt.txt`** 🔓 — riga 16 idem. **`vision_parser.py`** 🔓 — esempio JSON 26.5 → 25.0.
- **Frontend** — `lib/setup.ts` `COLD_PRESS_WINDOW` → [24.5, 25.5] (speculare a demo_data); `PressureGauge.tsx` scala MIN/MAX 27.0/30.5 → **24.5/28.0** (stessa traslazione −2.5: senza, la lancetta finiva a fondo scala).
- **Non toccati** (verificato in inventario): `csv_parser.py` (range 24.0–30.0 inclusivo, RR a freddo 24.0 ci sta), `car_setup_ranges.json` (non contiene pressioni), resto del frontend (legge tutto dall'API, media Dashboard inclusa).
- **NEW `SPEC_ERRATA.md`** alla radice (era citato da demo_data.py ma non esisteva nella v2): ERR-01 (eredità v1) + ERR-02 (questa correzione).

**Motivazione:** precisione tecnica non negoziabile per l'esame: i numeri pressione erano da ACC pre-1.9. La traslazione uniforme preserva per costruzione delta, spread e la storia demo (posteriori basse → Post.DX surriscalda → «alza le posteriori»).

**Risultato osservato:** gauge Telemetria su 26.5/26.7 (in finestra) e 25.7/25.5 (bassa, ambra/rossa come prima); KPI Dashboard media 26.1, «2 gomme fuori finestra · retrotreno basso» invariato; Setup coi 4 default verdi nella nuova finestra 24.5–25.5; Console con la nuova finestra e correzione +1.0 coerente.

**Verifica:** 11/11 invarianti FASE 0 OK (script dedicato: anteriori in finestra, 2/4 fuori, freddo<caldo per giro, salita +1.5 uniforme, serie coerenti coi gauge, correzione +1.0 rientra a caldo E a freddo, media 26.1, temp intatte, posteriori ambra nel Setup) · `tsc --noEmit` 0 err · rotte 5/5 200 · `test_parser` 12/12 · API verificata post-riavvio backend (hot/cold/finestre/default nuovi).
**File protetti:** ☑ sbloccati con «ok procedi» al gate solo-diff → demo_data, demo_responses, setup_params, prompts v4+chat, vision_parser (solo esempio)
**Decisione:** ☑ Mantenuto — **verificato a schermo da Edoardo** («verificato a schermo, tutto ok»)

---

## Entry #013 — MEGAPROMPT #8 · FASI 1–4: feature "A Lezione con Gigi" ✅ COMPLETA

| Campo | Valore |
|---|---|
| Data | 12/07/2026 |
| Agente dev | Claude Code (`claude-fable-5`) |
| Area | Nuova sezione /lezioni (indice + dettaglio) · Sidebar/NavIcons · lib/lessons.ts |
| Commit | `3377440` (F1) · `138da5a` (F2) · `ed56bdc` (F3) · `8dca0c0` (F4, docs) |
| Contesto | Megaprompt #8, feature dopo la FASE 0 (Entry #012). 8 mini-guide sim-racing: Gigi ti fa capire, non guida al posto tuo. Fonte testi: `docs/A_Lezione_con_Gigi_ContentPack_v1.md`. |

**Catalogo messaggi:**
1. Megaprompt #8, FASI 1–4 (dopo il gate FASE 0).
2. Scelte al gate F1: label nav **"Lezioni"** (consigliata) + icona **lampadina**; posizione dopo Setup.
3. Content pack consegnato alla radice → spostato in `docs/`.
4. Al gate F3: «cambia le x di errori comuni... rosso pitwall» → ✕ da `text-warn` a `text-accent`.
5. Conferme a schermo di Edoardo a ogni gate (F1, F2, F3+fix).

**Modifica (per FASE):**
- **F1** (`3377440`) — NEW `IconLessons` in `ui/NavIcons.tsx` (lampadina mono-linea, famiglia line-style 1.6/24); voce "Lezioni" dopo Setup nell'header fisso della Sidebar (idioma completo: barra accent `layoutId`, `aria-current`); rotta `/lezioni` placeholder con PageHeader.
- **F2** (`138da5a`) — NEW `lib/lessons.ts`: le 8 lezioni trascritte fedelmente dal content pack (tipo `Lesson` del megaprompt; `whenToUse` opzionale perché la Lezione 7 non lo definisce; la "NOTA DI ALLINEAMENTO" della Lezione 6 è omessa: risolta dalla FASE 0 con l'opzione (a), demo e lezione ora dicono entrambe 26.0–27.0). Indice `/lezioni`: griglia 8 card (numero mono + titolo + sintesi 1 riga + tag "aggancio PitWall" solo su 06/08 — disclosure progressiva, niente contenuto in lista). Content pack committato in `docs/`.
- **F3** (`ed56bdc`) — NEW `/lezioni/[slug]`: template unico (Sintesi lead · Perché conta · Quando usarla condizionale · Come si fa numerato · Errori comuni con ✕ · Aggancio PitWall condizionale con filetto accent · Approfondisci). Video card senza iframe: thumbnail statica `img.youtube.com/vi/{id}/hqdefault.jpg` + titolo + canale, `target="_blank" rel="noopener noreferrer"`; con `videoId="TODO"` → box tratteggiato "video in arrivo" (tutte e 8, in attesa degli URL di Edoardo). Slug ignoto → not-found. `Sidebar.tsx`: stato attivo esteso alle sotto-rotte (`startsWith`, "/" resta esatto — fix annunciato al gate F1). Fix su richiesta: ✕ errori comuni in rosso PitWall (`text-accent`).
- **F4** (questo commit) — Agganci verificati: Gomme→`/telemetry`, LiCo→`/console` vivono nei DATI (lib/lessons.ts) e nel template, **le pagine Telemetria/Console non sono mai state toccate** (verificato su `git diff --name-only` dell'intera feature). Micro-coerenza nav/icone ok. Entry di log.

**Motivazione:** ultima funzione pre-consegna: PitWall non solo monitora ma insegna i fondamentali (filosofia "Gigi ti fa capire"). Read-only, zero stato, zero storage, zero file protetti in tutta la feature.

**Risultato osservato:** quinta voce "Lezioni" (lampadina) con barra accent che scivola; `/lezioni` con 8 card; dettaglio con template a sezioni, agganci accent su Gomme/LiCo, video card "in arrivo"; voce nav evidenziata anche dentro un dettaglio.

**Verifica:** `tsc --noEmit` 0 errori · rotte `/ /console /telemetry /setup /login /lezioni /lezioni/[slug]` **8/8 200** · `test_parser` 12/12 · protetti: nessuna modifica non committata (`git diff --quiet HEAD` sull'elenco protetto) · feature: `/telemetry` e `/console` mai toccate.
**File protetti:** ☑ nessuno toccato (FASI 1–4)
**Decisione:** ☑ Mantenuto — ogni fase verificata a schermo da Edoardo. **Resta aperto:** incollare i VIDEO_ID confermati in `lib/lessons.ts` (8 × `"TODO"`).

---

## Entry #014 — MEGAPROMPT #9 (FINALE DEMO): video lezioni · wizard "Conosci il pilota" · tour schermate ✅ COMPLETO (F0–F7)

| Campo | Valore |
|---|---|
| Data | 13/07/2026 |
| Agente dev | Claude Code (`claude-fable-5`) |
| Area | lib/lessons.ts + dettaglio lezione · NEW lib/profile.tsx, OnboardingFlow, GigiTour · Console/api (iniezione profilo) · Sidebar footer |
| Commit | `82ca4fd` (F0) · `f37f51a` (F1) · `3606919` (F2) · `ddc00bf` (F3) · `db07b6f` (F5) · `5b09be1` (F6) · docs in questo commit |
| Contesto | Nono megaprompt — chiusura demo pre-esame: video card attive, wizard profilo pilota, tour guidato. Un gate per fase, un commit per fase. |

**Catalogo messaggi:**
1. Incollato MEGAPROMPT #9 (F0 video + wizard/tour F1–F7).
2. «ok procedi» sul piano, poi conferma a schermo a ogni gate (F0, F1, F2, F3, F5+fix, F6+fix lessico).
3. Al gate F5: «ok procedi» sull'iniezione via campo separato.
4. F6: «rivedi il lessico di Gigi» → fix apici (caporali «» come da convenzione Console).

**Modifica (per FASE):**
- **F0** (`82ca4fd`) — `lib/lessons.ts`: 8 × `videoId` "TODO" → ID confermati; titoli/canali allineati ai video reali (i placeholder non coincidevano; scelte dichiarate: L6 resta Coach Dave Academy, L7 canale "F1 Crash Course", L8 → Driver61); NEW campo opzionale `videoNote` + nota F1 verbatim sulla Lezione 7; template `[slug]` rende la nota in corsivo muted sotto la video card. Verificate le 8 thumbnail YouTube (HEAD 200).
- **F1** (`f37f51a`) — NEW `lib/profile.tsx` (tipi `WeakArea`/`DriverProfile` da megaprompt; `ProfileProvider`+`useProfile`; **localStorage** `pw_driver_profile` — sopravvive alle sessioni, a differenza del login) + NEW `OnboardingFlow.tsx` (guscio modal idioma StintCompare MA senza chiusura Esc/click-fuori: a metà wizard non si perdono risposte) montato SOLO nel layout `(app)` (mai su /login); trigger primo accesso (`completedAt` assente → wizard); Sidebar footer: bottone "↻ Rivedi tutorial" (replay NON azzera lo storage: riapre dallo step 1, il profilo resta finché non ricompleti — robustezza demo).
- **F2** (`3606919`) — Wizard 4 step a tap: livello · obiettivo · punti deboli (multipla, griglia 2 col, anche vuota) · setup; "Passo X di 4" + barra progress accent; Avanti disabilitato senza scelta; Indietro conserva; "Salta per ora" solo sul primo step; "Fine" salva (`completedAt`=adesso). Replay precompilato dal profilo salvato.
- **F3** (`ddc00bf`) — NEW `recommendLessons()` in lessons.ts (mappa punti deboli→slug della tabella; Costanza→2 lezioni; dedupe, max 3; default linea+frenata) + schermata finale "Ecco come guidi.": riepilogo 4 risposte, card lezioni → `/lezioni/[slug]` (click chiude e naviga), CTA "Fai il tour →" / "Salta".
- **F5** (`db07b6f`) — Iniezione profilo nel contesto di Gigi **senza toccare protetti**: gate di fattibilità → punto trovato in `backend/app/api/analysis.py` (api/, NON in lista protetta). Insidia sventata: il routing keyword della demo-cache avrebbe letto "gomme"/"carburante" dal profilo → il profilo viaggia in un **campo `profile` separato**, ignorato dal ramo demo/cache e inserito in `_context()` solo nel ramo LLM reale. Frontend: `postAnalysis(prompt, profile?)`, `profileContextLine()`, Console allega da `useProfile`. **F5-fix** (trovato da Edoardo col network tab in Opera): la domanda demo di mount partiva prima della lettura del profilo → l'effect aspetta `profileReady`. Invariante verificata: stessa domanda con/senza profilo → risposte demo byte-identiche.
- **F6** (`5b09be1`) — NEW `GigiTour.tsx`: fumetto FISSO basso-centro (mai ancorato → non si rompe), GigiAvatar + "Tour · X/5" + i 5 testi del megaprompt verbatim; Avanti naviga Dashboard→Console→Telemetria→Setup→Lezioni, Fine/Salta chiude; niente backdrop (accompagna, non blocca). `tourStep` nel ProfileProvider (sopravvive alla navigazione; push centralizzato al cambio step, non "strattona" se giri altrove). "Fai il tour →" del wizard cablato. **Fix lessico** su richiesta: apici dritti attorno a frase con apostrofo → caporali «l'auto scivola dietro» (convenzione del placeholder Console).
- **F7** — Verifica finale + questa entry (nessuna modifica di codice).

**Motivazione:** chiudere la demo: le 8 lezioni avevano il box "video in arrivo"; l'app non sapeva nulla del pilota (nessuna personalizzazione né onboarding); un visitatore nuovo non aveva una guida delle 5 pagine.

**Risultato osservato:** lezioni con video card cliccabili (thumbnail reale, YouTube in nuova scheda) e nota F1 sulla Lezione 7; al primo accesso wizard 4 step → profilo salvato → lezioni consigliate coerenti coi punti deboli; payload `/api/analysis` con riga "Profilo pilota: …" (verificato da Edoardo nel network tab); tour di Gigi pagina per pagina; tutto ri-lanciabile da "↻ Rivedi tutorial". Ogni fase verificata a schermo.

**Verifica:** `tsc --noEmit` 0 errori · rotte **8/8 200** (incluse `/lezioni/[slug]`) · `test_parser` **12/12** · thumbnail 8/8 · demo-cache invariante con profilo · **protetti: zero file toccati in tutto il megaprompt** (diff `origin/main..HEAD` sulla lista protetta = vuoto; `analysis.py` sta in `api/`, fuori lista, modificato con gate dedicato).
**File protetti:** ☑ nessuno toccato
**Decisione:** ☑ Megaprompt #9 **COMPLETO e verificato** (F0–F7). **NON pushato**: 7 commit locali in attesa di «ok push».

---

## Entry #015 — Fix INC-V2-006: modal Confronto coperto dalle card in Dashboard (portale)

| Campo | Valore |
|---|---|
| Data | 13/07/2026 |
| Agente dev | Claude Code (`claude-fable-5`) |
| Area | `ui/Sidebar.tsx` (overlay Confronto metà stint) |
| Commit | `cd82a30` (fix + INCIDENTS) · log in questo commit |
| Contesto | Bug segnalato da Edoardo a fine sessione precedente (screenshot 10:53 da OneDrive/Catture di schermata); fix post-megaprompt #9. In sessione anche: scritto `MEGAPROMPT9_REPORT.md` (gitignorato). |

**Catalogo messaggi:**
1. Ripresa sessione + «procedi col report» (MEGAPROMPT9_REPORT.md, nessun codice).
2. «procedi con la diagnosi del bug confronto in Dashboard … appena lo fixi mettilo negli incidents anche essendo un bug minore».

**Modifica:**            MOD `ui/Sidebar.tsx` (unico file): il blocco `AnimatePresence`+`StintCompareModal` è ora renderizzato in **portale su `document.body`** (`createPortal` da `react-dom`, guard `mounted` via `useEffect` per non toccare `document` in SSR). `StintCompare.tsx` INTATTO.
**Motivazione:**         Il modal era montato dentro l'`<aside sticky>`: `position: sticky` crea sempre uno stacking context, quindi lo `z-50` del modal valeva solo dentro la Sidebar (livello `auto`, dipinta prima del `main`). Le card KPI della Dashboard (wrapper `position: relative` per il DnD) passavano sopra. Solo in Dashboard perché unica pagina con card posizionate nell'area del modal; il KpiModal non soffre perché montato nel `main` dopo le card. Diagnosi confermata pixel-per-pixel dallo screenshot (card sopra, "Ultima sessione" non posizionata sotto, grafico visibile nei varchi).
**Risultato osservato:** Modal Confronto sopra le card anche in Dashboard; backdrop che scurisce davvero tutta la pagina Sidebar inclusa; comportamento invariato altrove (Esc/click-fuori/exit animation conservati dall'AnimatePresence dentro il portale).
**Verifica:**            `tsc --noEmit` 0 err · rotte `/ /console /telemetry /setup /login /lezioni` 6/6 200 (server rilanciati post-riavvio macchina: backend senza `--reload` come da HAZARD-V2-B) · backend health ok · nessun file protetto toccato. INCIDENTS.md: NEW **INC-V2-006** in RISOLTI (registrato su richiesta esplicita di Edoardo benché 🟡 minore).
**File protetti:**       ☑ nessuno toccato
**Decisione:**           ☑ Mantenuto — «ok push» di Edoardo: committato e pushato insieme ai 7 commit del megaprompt #9

---

## Entry #016 — Demo = postazione condivisa: wizard sempre da zero in demo + "Riparti da zero" per tutti

| Campo | Valore |
|---|---|
| Data | 13/07/2026 |
| Agente dev | Claude Code (`claude-fable-5`) |
| Area | `lib/profile.tsx` · `(auth)/login/page.tsx` · `ui/OnboardingFlow.tsx` |
| Commit | `e96ee70` — retro-compilato dopo l'«ok push» |
| Contesto | Richiesta di Edoardo dopo i test con i compagni: il profilo wizard (localStorage) restava quello del tester precedente e la profilazione andava rilanciata a mano da "↻ Rivedi tutorial" (per giunta precompilata). |

**Catalogo messaggi:**
1. «vorrei che la profilazione del pilota col tutorial si ripetesse ogni volta che qualcuno si logga … con il profilo demo … rimaneva il profilo precedente salvato».
2. «metti anche un'opzione per rifare il wizard … anche per chi logga da google … a prescindere per quelli che entrano in demo mode bisogna far azzerare ogni volta».

**Modifica:**
- MOD `lib/profile.tsx` — NEW `resetProfile()` nel ProfileProvider: azzera localStorage (`pw_driver_profile`) **e** lo stato in memoria (provider globale nel root layout: pulire solo lo storage non basterebbe) + `tourStep → null` (un tour a metà del tester precedente non deve riprendere).
- MOD `(auth)/login/page.tsx` — `handleDemo()` chiama `resetProfile()` prima di `enterDemo()`: **ogni ingresso «🏁 Entra in modalità demo» riparte con wizard in bianco** (il trigger esistente `ready && !profile` di OnboardingFlow fa il resto, zero modifiche al trigger). Login Google INVARIATO: ritrova il proprio profilo.
- MOD `ui/OnboardingFlow.tsx` — NEW bottone **"↺ Riparti da zero"** nel footer del primo step, visibile solo quando esiste un profilo salvato (cioè nel replay da "↻ Rivedi tutorial", Google incluso): `resetProfile()` + bozza locale svuotata; il bottone sparisce dopo il reset (condizione `profile`).

**Motivazione:** demo mostrata su un solo PC/browser: il localStorage è per-postazione, non per-persona. Semantica scelta: demo = postazione condivisa (reset a ogni ingresso), account Google = personale (profilo persistente, reset solo su richiesta esplicita via "Riparti da zero").
**Risultato osservato:** ogni ingresso demo → wizard "Conosci il pilota" da zero; «⏻ Esci → rientra demo» idem; "↻ Rivedi tutorial" → wizard precompilato con in più "↺ Riparti da zero" per svuotarlo. Un tester che fa "Salta per ora" in demo non lascia tracce al successivo.
**Verifica:**            `tsc --noEmit` 0 err · `/` e `/login` 200 · file protetti non toccati.
**File protetti:**       ☑ nessuno toccato
**Decisione:**           ☑ Mantenuto — «ok push» di Edoardo (13/07)

---

## Entry #017 — Investigazione TODO aperti: INC-V2-002 falso positivo · fix DnD (INC-V2-005) · audit placeholder e delta

| Campo | Valore |
|---|---|
| Data | 13/07/2026 |
| Agente dev | Claude Code (`claude-fable-5`) |
| Area | Dashboard DnD (`(app)/page.tsx`) · INCIDENTS.md · verifiche read-only su backend protetto |
| Commit | `d3cf00e` — retro-compilato dopo l'«ok push» · log in questo commit |
| Contesto | Richiesta di Edoardo: passare in rassegna tutti i TODO/fix in memoria prima del "lavorone" finale (test completi del sistema, anti-allucinazioni Gigi, controllo generale). |

**Catalogo messaggi:**
1. «manca qualcosa che hai ancora in memoria da fare? … inizia ad investigare tutto».
2. Decisioni per punto: (1) icone Prossime azioni "già fatta" [NOTA: in realtà le emoji ci sono ancora, segnalato] · (2) mojibake «puoi fixarla» · (3) DnD «controlla bene … in caso fixalo» · (4) delta «ricontrolla» · (5) placeholder ranges «post esame» purché non crashino · (6) Setup post-esame + accorgimento sui consigli di Gigi da dettare.

**Modifica:**
- **INC-V2-002 → CHIUSO senza toccare file: FALSO POSITIVO.** Byte grezzi API = `Velocit\xc3\xa0` (UTF-8 corretto); riga mai modificata dallo scaffold (`git log -L`). Il mojibake era dello strumento: PowerShell 5.1 decodifica i JSON senza charset come ISO-8859-1. Nessun gate necessario (nessuna modifica al protetto). INCIDENTS aggiornato con lezione di procedura (verificare i byte, non il testo decodificato da PS 5.1).
- **INC-V2-005 → FIX** in `(app)/page.tsx` (pointer-based, zero dipendenze): (a) drop = inserzione **prima/dopo il bersaglio** in base alla metà puntata (`clientX` vs centro card), non più "prendi l'indice del bersaglio" (asimmetrico); (b) **barra accent di inserzione** nel gap al posto del ring; (c) **fallback sul contenitore grid** per gap e buchi lasciati dalle card estese a capo (prima: no-op silenzioso, la card "tornava indietro" — probabile causa principale del sintomo); (d) indice corretto per lo shift post-rimozione. `stopPropagation` sulle card per non far scattare il fallback.
- **Audit placeholder `car_setup_ranges.json` (read-only, INC-V2-003):** NON possono crashare — `DA_VERIFICARE` vive solo in `_status` (mai copiato: whitelist `min/max/step/default` + guard `isinstance(dict)`), override seed = no-op sui generici, vettura ignota → fallback, JSON rotto → `{}`. Confermato rinvio post-esame senza rischi.
- **Ricontrollo "Delta giro-su-giro" (read-only):** 2 incoerenze reali trovate e RIPORTATE a Edoardo senza fixare (aveva detto "dovrebbe essere a posto"): il toggle riferimento cambia solo il grafico (tabella sempre vs precedente, non dichiarato); più lento = ambra nel grafico ma rosso in tabella. In attesa di sua decisione.

**Motivazione:** bonifica della coda TODO prima della fase di test finale pre-esame (15/07).
**Risultato osservato:** DnD Dashboard: barra rossa di inserzione che segue il puntatore (sinistra/destra del bersaglio), drop su gap/buchi = in fondo con barra sull'ultima card; nomi tracciato confermati corretti via byte.
**Verifica:**            `tsc --noEmit` 0 err · `/` 200 · file protetti INTATTI (verifiche solo read-only).
**File protetti:**       ☑ nessuno toccato
**Decisione:**           ☑ Mantenuto — «ok push» di Edoardo (13/07) · INC-V2-002 chiuso · resta aperta la decisione sui 2 punti del Delta giro-su-giro

---

## Entry #018 — Delta in sync col toggle + suggeriti di Gigi nel Setup: applica al click, scroll al parametro, ● rosso sul target

| Campo | Valore |
|---|---|
| Data | 13/07/2026 |
| Agente dev | Claude Code (`claude-fable-5`) |
| Area | `charts/LapDeltaChart.tsx` · `lib/setup.ts` · `(app)/setup/page.tsx` · `setup_params.py` (gate) |
| Commit | `485807d` (delta) · `304d62f` (setup + preload step) — retro-compilati dopo l'«ok push» · log in questo commit |
| Contesto | Coda della bonifica #017: ok di Edoardo sui 2 punti delta + dettatura dell'"accorgimento sui consigli di Gigi" per la pagina Setup. |

**Catalogo messaggi:**
1. «sistema pure i 2 punti del delta giro-su-giro».
2. Accorgimento Setup (verbatim, in sintesi): i parametri suggeriti hanno solo il tag GIGI ma nessuna modifica suggerita; il click sui suggeriti porta al tab ma poi «devo scorrere io fino giù e cambiare effettivamente il valore»; «vorrei che cliccando sui suggeriti i parametri si cambiassero da soli ed inoltre che siano segnati sugli slider con dei "punti rossi"».
3. Feedback sul primo giro: i pallini «sembrano messi lì per un errore del css» → «una sorta di striscia verticale dentro lo slider che lo prende in pienezza» — marker rifatto come **tacca verticale** a tutta altezza della traccia (3px, accent, stessa compensazione thumb).
4. Alla ripresa (sessione successiva, scelta tra 4 varianti proposte): **"tick da strumento"** — la tacca ora sporge ~3px sopra e sotto la traccia (`h-3.5` su traccia `h-2`), come le tacche di riferimento dei gauge.
5. «fixiamo l'assegnazione dei valori nel precarico, non fa impostare i 75 Nm» → **gate solo-diff** con 2 opzioni (step 10→5 vs narrazione 75→80): scelta **step 10→5**, narrazione INVARIATA.

**Modifica:**
- **LapDeltaChart** — (1) la tabella dei delta ora **segue il toggle** giro precedente/media stint (prima restava sempre vs precedente senza dichiararlo) + didascalia "Δ vs …" sopra la tabella; in "media stint" anche il giro 1 ha un Δ (vs media). (2) Più lento/più consumo = **ambra anche in tabella** (`STATE.warn`, era `alarm` rosso): è uno scostamento dal riferimento, non una soglia violata — stesso token del grafico.
- **lib/setup.ts** — NEW `GIGI_TARGETS`: i valori-obiettivo dei 3 suggeriti demo, **le stesse cifre della Console** (demo_responses: RL 24.2→**25.2** · RR 24.0→**25.0** psi freddo · precarico 60→**75** Nm). L'API espone solo le chiavi (`suggested_params`): i target vivono lato client come `DEMO_TANK_CAPACITY` (un punto solo da cui correggere). Protetti INTATTI.
- **setup/page.tsx** — chip "Suggeriti da Gigi": il click ora **applica il valore consigliato** (clamp nel range), cambia tab e **scrolla allo slider** (`scrollIntoView`, con retry perché AnimatePresence monta il tab in ritardo; deadline 1.5s); il chip mostra "→ 25.2 psi" accanto al nome. Slider: NEW **tacca rossa verticale** a tutta altezza della traccia alla posizione del target di Gigi (3px, compensazione corsa thumb 16px, `title` col valore; prima iterazione a pallino scartata su feedback), `id="param-<key>"` come ancora; didascalia banner aggiornata.
- **setup_params.py** 🔓 (gate solo-diff alla ripresa, opzione scelta da Edoardo) — `preload` **step 10 → 5**: con step 10 il 75 Nm della narrazione non era impostabile né dal chip né a mano. Min/max/default INTATTI, narrazione Console INVARIATA. Backend riavviato pulito (kill + relaunch senza `--reload`, HAZARD-V2-B); API verificata: `preload: 20 200 5 60`.
- **NOTA residua dichiarata:** i default slider RL/RR (25.3) non coincidono coi valori "attuali" della narrazione (24.2/24.0) — preesistente, fuori scope.

**Motivazione:** il collegamento Console↔Setup era solo informativo: tag e cambio tab, nessuna azione. Ora il consiglio di Gigi è actionable con un click e visibile sulla traccia (● rosso = "dove vuole Gigi"), coerente con la filosofia "ti faccio capire e ti porto lì".
**Risultato osservato:** click su "Precarico Differenziale" nel banner → tab Meccanica, scroll fino al Differenziale, valore 75 Nm applicato, tacca rossa verticale sulla traccia al target; idem pressioni RL/RR (25.2/25.0, valore verde in finestra); tabella delta coerente col toggle e ambra come il grafico.
**Verifica:**            `tsc --noEmit` 0 err · `/setup` `/telemetry` 200 · `test_parser` 12/12 post-riavvio · API `preload` step 5 · in attesa verifica a schermo di Edoardo.
**File protetti:**       ☑ sbloccato con gate solo-diff → `setup_params.py` (SOLO step preload 10→5); il resto intatto
**Decisione:**           ☑ Mantenuto — «ok tutto a posto» + «ok push» di Edoardo dopo verifica a schermo (tick, chip, 75 Nm impostabile, delta)

---

## Entry #019 — Certificazione demo pre-esame: test ×3 (243/243), blindatura off-topic, reset demo totale, icone azioni

| Campo | Valore |
|---|---|
| Data | 13/07/2026 (tarda sera) |
| Agente dev | Claude Code (`claude-fable-5`) |
| Area | `api/analysis.py` (off-topic guard) · `(auth)/login/page.tsx` (reset totale) · `(app)/page.tsx` (icone ACTIONS) · suite test (scratchpad) · NEW `DEMO_TEST_REPORT.md` (gitignorato) |
| Commit | `58ecb3a` (off-topic) · `c191400` (reset totale) · `25e7f4e` (icone) — retro-compilati dopo l'«ok push» · log in questo commit |
| Contesto | "Il lavorone": demo al 1000% per l'esame del 15/07. Domande preliminari poste a Edoardo (rete/dev-vs-build/reset/Gigi live) e risposte recepite. |

**Catalogo messaggi:**
1. «mettici le icone che ci stanno nella sidebar anche nelle 3 card infondo alla dashboard» · «per i test fai l'opzione A almeno 3 volte» · «finiti i test voglio un report completo .md … mini scaletta per lo speech» · invito a fare domande fuori dal quadro.
2. Risposte alle 4 domande: rete = WiFi istituto (hotspot fallback) · demo in `npm run dev` com'è ora, «vorrei evitare il lag, dimmi come fare» · reset totale demo: SÌ · domande live a Gigi: improbabili ma possibili → «facciamo in modo che risponda solo a domande inerenti la sessione».

**Modifica:**
- **`(app)/page.tsx`** — ACTIONS: emoji → `IconConsole/IconTelemetry/IconSetup` (NavIcons); `ActionCard` rende il componente icona (muted → accent in hover).
- **`(auth)/login/page.tsx`** — `handleDemo()`: azzera TUTTE le chiavi localStorage `pw_*` (profilo/tour già coperti da `resetProfile()` + ordine/taglie card `pw_dashboard_kpi_v1`, note `pw_quick_notes`, sezioni `pw_sb_*`) → demo sempre vergine, a prova di chiavi future.
- **`api/analysis.py`** (NON protetto, precedente F5 #9) — blindatura off-topic: NEW `_in_scope()` (riusa `_DEMO_ROUTES` del modulo protetto in sola lettura, zero duplicazione keyword) + `_off_topic_text()` (redirect onesto costruito dai dati `SESSION` — coerente per costruzione). Nel ramo demo: nessuna keyword → redirect, NON più il default sovrasterzo ("allucinazione percepita" davanti a domande tipo «che tempo fa?»).
- **NEW `DEMO_TEST_REPORT.md`** (gitignorato, `*_REPORT.md`): struttura demo, funzionamento demo-mode, le 4 garanzie di "infallibilità", tabella test, procedura giorno-esame (avvio, pre-warm anti-lag, rete, recovery), mini scaletta speech in 6 punti.
- Suite `demo_test_suite.py` (scratchpad, riutilizzabile): T1 coerenza numeri (34 check: demo_data ↔ narrazione ↔ setup_params ↔ costanti frontend) · T2 batteria Console (28: routing, 5 trappole off-topic, invariante profilo byte-identica, profilo non inquina il routing, timing) · T3 robustezza API (9: mai 500 su input sporchi, demo_mode ON, live_allowed OFF, UTF-8) · T4 rotte 8/8 (16).

**Motivazione:** certificare che in demo non possa accadere nulla di imprevisto: niente allucinazioni (per costruzione), niente numeri incoerenti (single source verificata), niente residui di test (reset totale), niente 500, niente lag reale.
**Risultato osservato:** **3 run × 81 = 243/243 PASS** · `tsc` 0 err · `test_parser` 12/12 · protetti intatti (diff vuoto sull'intera lista). Falso "lag" 2s smascherato come artefatto IPv6 del client di test (API reale: 1–15 ms su 127.0.0.1). Off-topic: «che tempo fa a Roma?» → redirect onesto, mai più l'analisi sovrasterzo.
**Verifica:**            vedi sopra (la verifica È l'oggetto dell'entry) + `/` e `/login` 200 dopo le modifiche frontend.
**File protetti:**       ☑ nessuno toccato (`_DEMO_ROUTES` letto, mai modificato)
**Decisione:**           ☑ Mantenuto — «ok push» di Edoardo (13/07 sera). Demo certificata per l'esame del 15/07.

---

## Entry #020 — Consegne finali per la prof: copie FINALE + completamento documentazione

| Campo | Valore |
|---|---|
| Data | 13/07/2026 (notte) |
| Agente dev | Claude Code (`claude-fable-5`) |
| Area | SPEC_ERRATA.md · PROMPT_LOG.md (titolo #008) · NEW cartella Desktop "consegne pitwall" (fuori repo) |
| Commit | non ancora committato |
| Contesto | Consegna serale del materiale alla prof (pre-esame 15/07). Richiesto controllo di completezza PRIMA delle copie. |

**Catalogo messaggi:**
1. «cartella sul desktop "consegne pitwall" … copie di prompt_log, incidents e spec_errata … "FINALE" nel nome … prima controlla che ci sia TUTTO … nella spec errata spero ci sia anche il perché della migrazione … il template si interrompa a fine documento».

**Modifica:**
- **Controllo di completezza** (esito): PROMPT_LOG #001–#019 continuo ✓ · INCIDENTS completo (5 risolti + INC-V2-003 aperto per scope + 2 hazard) ✓ · trovate e sanate 3 lacune:
  (a) MOD `PROMPT_LOG.md`: titolo Entry #008 «🔄 IN CORSO» → «✅ COMPLETO (F0–F10)» (il corpo lo diceva già);
  (b) MOD `SPEC_ERRATA.md`: NEW **Premessa "perché la v2"** — migrazione da Streamlit (decisione 08/07, fonte `docs/01-target-stack.md`: Streamlit collo di bottiglia sulla presentazione; FastAPI riusa la logica di dominio Python; SVG v1 → componenti React; API key solo server);
  (c) MOD `SPEC_ERRATA.md`: NEW **ERR-03** — passo precarico 10→5 Nm (incoerenza narrazione 75 Nm ↔ slider, gate Entry #018).
- **NEW `Desktop/consegne pitwall/`** (fuori repo): `PROMPT_LOG_FINALE.md` · `INCIDENTS_FINALE.md` · `SPEC_ERRATA_FINALE.md` — copie integrali con **template di coda rimossi** e **chiusura formale** («DOCUMENTO FINALE — consegna del 13/07/2026», sintesi di stato, © Edoardo Ferlito). Verificato: nessun blocco `<!-- TEMPLATE`, nessun segnaposto Entry #XXX / INC-V2-00X residuo.

**Motivazione:** i documenti consegnati devono leggersi come registri CHIUSI, completi e autoesplicativi (migrazione inclusa), senza scaffolding da lavoro-in-corso.
**Risultato osservato:** cartella sul Desktop con i 3 file FINALE (UTF-8, footer di chiusura); originali in repo arricchiti (premessa migrazione + ERR-03 + titolo #008).
**Verifica:**            script di controllo sulle copie (template assenti, footer presente) · originali: nessun file protetto toccato.
**File protetti:**       ☑ nessuno toccato
**Decisione:**           ☑ Consegna pronta — commit dei 2 file documentali dopo «ok push»

---

## Entry #021 — Build post-esame: primo blocco di fix UX/coerenza dopo verifica a schermo

| Campo | Valore |
|---|---|
| Data | 30/08/2026 |
| Agente dev | Claude Code (claude-sonnet-5) |
| Area | Frontend (OnboardingFlow, profile, Sidebar) · Backend protetto (setup_params.py, con «ok procedi») |
| Commit | non ancora committato |
| Contesto | Ripartenza post-esame (15/07 superato). Apertura di PitWall in locale + tour a schermo delle 6 pagine per decidere cosa migliorare. Primo blocco: i fix emersi dal giro; le aggiunte arriveranno dopo. |

**Catalogo messaggi:**
1. «apri pitwall e verifica a schermo cosa vorrei cambiare» → tour completo (login/dashboard/console/telemetria/setup/lezioni).
2. «inizia con i primi fix che hai suggerito e poi ti dirò cosa aggiungere».
3. «ok procedi con il fix #2» (sblocco STOP gate su `setup_params.py`) + richiesta di riaprire la scheda Chrome (freeze lato estensione).

**Modifica:**
- **Fix #1 — Wizard "Conosci il pilota" che riappariva a ogni navigazione.** `lib/profile.tsx`: nuovo flag persistito `pw_onboarding_skipped` (stato `onboardingSkipped` + `dismissOnboarding()`; `resetProfile` lo azzera). `components/ui/OnboardingFlow.tsx`: il trigger di primo accesso ora è `ready && !profile && !onboardingSkipped`; "Salta per ora" chiama `dismissOnboarding()` invece di `closeOnboarding()`. Il flag ha prefisso `pw_` → ripulito dall'ingresso demo (tester sempre fresco) e da "Riparti da zero".
- **Fix #2 — Slider pressioni Setup incoerenti con la storia demo.** `backend/app/core/setup_params.py` (PROTETTO, sbloccato con «ok procedi»): default `tire_press_fr` 25.0→**25.2**, `tire_press_rl` 25.3→**24.2**, `tire_press_rr` 25.3→**24.0** — allineati a `COLD_PRESSURES` di `demo_data.py`. Ora RL/RR partono sotto finestra (ambra) e i suggeriti Gigi (→25.2/25.0) le *alzano* dentro la finestra (prima erano 25.3 verdi e il consiglio le abbassava, controsenso).
- **Fix #3 — Badge versione datato.** `components/ui/Sidebar.tsx`: `v0.1.0 · v2 scaffold` → `v1.0.0 · post-esame`.

**Motivazione:** togliere la frizione UX del wizard ripetuto; rendere coerente la schermata Setup con la narrazione demo e con i consigli di Gigi; aggiornare l'etichetta di versione ora che l'app non è più uno scaffold.
**Risultato osservato:** wizard NON riappare più dopo "Salta per ora" (verificato su Telemetria e Setup dopo ingresso demo); Setup mostra FL 25.0🟢 / FR 25.2🟢 / RL 24.2🟠 / RR 24.0🟠 con tacca rossa target a 25.2/25.0; badge aggiornato.
**Verifica:**            `npx tsc --noEmit` 0 err · `test_parser` 12/12 (backend riavviato no-reload dopo il file protetto) · rotte `/ /login /telemetry /setup` 200 · verifica a schermo via Chrome.
**File protetti:**       ☑ sbloccato con «ok procedi» → `backend/app/core/setup_params.py` (default 3 pressioni gomme)
**Decisione:**           ☑ Mantenuto — in attesa di «ok push» per il commit

---

## Entry #022 — Lotto 1 asset ACC: integrazione in 3 fasi (catalogo → selettori → schede)

| Campo | Valore |
|---|---|
| Data | 30/08/2026 |
| Agente dev | Claude Code (claude-opus-4-8) |
| Area | NEW `core/catalog.py` + `api/catalog.py` + `data/{cars,tracks}.json` · frontend (api, catalog, setup, dashboard, NEW SessionBriefing) · `demo_data.py` (protetto, «ok procedi») |
| Commit | `8c00304` · `67a9ef2` · +2 (anno demo, schede UI) |
| Contesto | Primo lotto di asset consegnato da Claude Desktop (31 GT3 + 25 circuiti). Richiesta: capire **come** entra nel progetto prima di tutto il resto. |

**Catalogo messaggi:**
1. «partiamo dai problemi del lotto 1 … voglio capire come verrà introdotto tutto quanto dentro al progetto in primis» → piano a 5 fasi esposto e approvato.
2. «procedi con la fase 1» · «procedi con la fase 2» · «ok push e poi procedi con la fase 3» · «ok procedi con l'anno e poi committa tutto».

**Modifica:**
- **Nodo architetturale individuato:** l'app identifica auto/piste con la **stringa di display** (`catalog.ts`, `car_setup_ranges.json`, `demo_data.SESSION`), il lotto con **slug**. Verifica: piste 15/15 combaciavano, **auto 4/15 no** (Porsche 992/991 II, Mercedes-AMG Evo, Huracán EVO2).
- **FASE 1** — `data/cars.json` + `tracks.json` in `core/data/`. NEW **`core/catalog.py`** (non protetto): `resolve_car`/`resolve_track` accettano slug, acc_id, display, soprannome, nome breve o alias; normalizzazione accenti/punteggiatura; nessun match approssimativo (None se non trova). NEW **`GET /api/catalog`** + `/catalog/car/{id}` + `/catalog/track/{id}`. Pulito il record Jaguar ridondante. `SHORT_NAMES` curata a mano per i 25 circuiti (la UI dice "Monza", non "Autodromo Nazionale Monza").
- **FASE 2** — i selettori del Setup si popolano da `/api/catalog` (**15→31 auto, 15→25 piste**); liste storiche degradate a `*_FALLBACK` (backend giù → non si svuotano); `PwSelect` accetta `SelectOption[]` e mostra il badge **DLC** (8 auto, 14 piste).
- **FASE 3** — NEW **`SessionBriefing.tsx`**: card "Il tracciato" (nome ufficiale, soprannome, lunghezza/curve/deportanza, descrizione, riquadro *Focus setup*) e "La vettura" (anno + DLC, motore/potenza/peso, didascalia voce Gigi). In Dashboard raccontano la demo; nel Setup seguono i selettori. Aiuti segnalati **per assenza** (avviso se manca TC/ABS); provenienza esplicita quando `specs.confidence` non è "alta".
- **`demo_data.py`** (PROTETTO, «ok procedi»): `car_year` "2024" → **"2021"** — allineato al catalogo, l'header Dashboard e la scheda mostravano due anni diversi per la stessa auto.

**Bug trovati e risolti in corsa (nessuno preesistente in log):**
1. **Alias inefficaci e dannosi:** gli alias puntavano allo slug con underscore mentre le chiavi di confronto sono normalizzate senza → non agganciavano e **rompevano** i match che riuscivano da soli (Spa, Barcelona). Fix: `_norm()` sul valore dell'alias.
2. **Vetture irraggiungibili:** `Bentley Continental GT3` e `Nissan GT-R Nismo GT3` esistono in **due annate con nome identico** → stessa stringa all'API, `resolve_car` restituiva sempre la prima, la variante **2018 era inarrivabile** (oltre alle chiavi React duplicate viste in console). Fix: `display_names_by_id()` aggiunge l'anno dove il nome collide.
3. **Tipo che mentiva:** `TrackSheet.short_name` dichiarato obbligatorio ma l'endpoint singolo restituiva il dict grezzo, senza. Fix: aggiunto anche lì.

**Motivazione:** dare al catalogo un'identità unica (lo slug) prima di costruirci sopra, senza rompere le stringhe storiche; poi far arrivare i contenuti dove sono utili.
**Risultato osservato:** selettori con l'intero roster + badge DLC e varianti distinte; Dashboard e Setup mostrano le schede; anni coerenti.
**Verifica:**            `tsc --noEmit` 0 err · `test_parser` 12/12 · nomi storici 30/30 risolti · console browser **0 errori** · endpoint preesistenti 200 · verifica a schermo (Dashboard, Setup, cambio vettura → Porsche 992).
**File protetti:**       ☑ sbloccato con «ok procedi» → `demo_data.py` (solo `car_year`)
**Decisione:**           ☑ Mantenuto — pushato

> **Nota aperta:** `data_lotti/lotto_1_ACC/` (consegna grezza: SCHEDE.md, README_DATI.md, `fetch_assets.py`, `build_schede.py`) è **fuori dal repo e non ignorato**. Da decidere se tracciarlo o gitignorarlo — `fetch_assets.py` servirà nella Fase 4 (immagini).

---

## Entry #023 — Fase 4/5 asset: foto verificate a occhio, ritaglio scelto a mano, crediti

| Campo | Valore |
|---|---|
| Data | 03/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | NEW `backend/scripts/{apply_photos,build_crop_tool}.py` + `{photos,maps,crops}.json` · NEW `/crediti` · `SessionBriefing.tsx` · `Sidebar.tsx` · `.gitignore` |
| Commit | `chore(assets)` · `feat(assets)` ×2 · `feat(ui)` ×2 · questo log |
| Contesto | Ripresa dopo il 30/08: le foto scaricate in automatico erano piene di errori (modellino BMW 1:32, 911 stradali, monumento di Snetterton). Il materiale di correzione era già pronto ma mai applicato. |

**Catalogo messaggi:**
1. «riprendiamo il lavoro dell'altra volta … vediamo cosa ci sta da fare» → status esposto, piano approvato.
2. «ok procedi, e gitignora i 33 MB» + «fai runnare in background e fammi vedere a schermo».
3. «alcune non vengono allineate bene … fai in modo che non vengano tagliate del tutto».
4. «torniamo ai formati di prima … fammi utilizzare quel tool per ritagliare meglio le foto e fai in modo anche che possa zoommarle».
5. «ok tutto a posto» dopo la verifica dei 53 ritagli a schermo.

**Modifica:**
- **Foto verificate.** `photos (1).json` (export del provino `provino_foto_v3.html`, 53 foto scelte cliccandole una per una) promosso a `backend/scripts/photos.json`. NEW `apply_photos.py`: scarica le miniature a 1400px via `Special:FilePath` (non gli originali da 12-16 MB), sostituisce anche a estensione diversa, **rimuove** le foto delle entità senza candidato approvato, rigenera `manifest.json` e `ATTRIBUTIONS.md`. 53 applicate; 3 entità restano senza foto apposta (`audi_r8_lms_evo_ii_gt3`, `reiter_engineering_r_ex_gt3`, `valencia_ricardo_tormo`).
- **Attribuzione dei layout SVG recuperata.** `ATTRIBUTIONS.md` viene riscritto per intero, quindi i 25 layout scaricati da `fetch_assets.py` (registro mai persistito) sarebbero spariti dai crediti. Ricostruiti interrogando Commons con lo **SHA-1** dei file a disco — identificazione esatta, non per nome — e salvati in `maps.json` (`--riscopri-mappe`).
- **Ritaglio scelto a mano.** NEW `build_crop_tool.py` genera un tool: foto grande, riquadro reale sovrapposto, trascinamento e zoom, anteprima a dimensione vera, cursore per l'altezza della banda, salvataggio in localStorage, import/export. Export = `crops.json` (53 voci, banda **540×280**), copiato fra gli asset da `apply_photos.py`. `SessionBriefing.Hero` applica quattro percentuali già pronte dentro una banda a **rapporto fisso**; senza ritaglio ricade su `object-cover` centrato.
- **`.gitignore`**: `/frontend/public/assets/` (33 MB). Le sorgenti versionate sono `photos.json` (scelta umana), `maps.json`, `crops.json` (scelta umana) e gli script che le applicano.

**Motivazione:** il filtro automatico giudicava dal NOME DEL FILE, non dal contenuto; nessuna euristica testuale chiude quel buco, l'ultimo giudice deve essere un occhio umano. Stessa logica per l'inquadratura: la banda è molto più larga che alta, e il centro geometrico quasi mai coincide col soggetto.

**Risultato osservato:** vetture riconoscibili e circuiti che mostrano il tracciato in Dashboard e Setup; `/crediti` elenca 78 asset (53 foto + 25 layout).

**Bug trovati e risolti in corsa:**
1. **Pagina `/crediti` vuota:** avevo aggiunto una colonna "Confidenza" alla tabella; il parser cerca 6 colonne con una regex ancorata, con 7 non aggancia più nulla e la pagina si svuota **senza errori**. Tornato a 6 colonne, con un commento che avvisa in entrambi i file.
2. **Preesistente — 26 righe su 78 invisibili:** le parentesi negli URL Commons (`..._(DSC02308).jpg`) chiudevano il link markdown in anticipo e la riga non veniva riconosciuta. Ora sono percent-encoded: 78/78.

**Verifica:**            `tsc --noEmit` 0 err · `test_parser` 12/12 · 53/53 foto e 53/53 ritagli rivisti a schermo uno per uno · Dashboard, Setup e `/crediti` verificate.
**File protetti:**       ☐ nessuno toccato
**Decisione:**           ☑ Mantenuto — pushato

> **Note aperte:** i 25 **layout SVG** sono a disco, nel manifest e nei crediti ma **nessuna pagina li mostra** — prossimo passo. · `red_bull_ring` e `suzuka` restano deboli come contenuto (di meglio su Commons non c'era). · Con gli asset gitignorati, un eventuale **deploy** parte senza foto finché non gira `apply_photos.py`: da decidere se committarli o eseguire lo script in build.

---

## Entry #024 — Guide dei tracciati, blocco 1: provino delle mappe + validatore delle guide

| Campo | Valore |
|---|---|
| Data | 07/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | NEW `backend/scripts/build_maps_proof.py` · NEW `backend/scripts/check_track_knowledge.py` · NEW `backend/app/core/data/tracks_knowledge/` · NEW `backend/scripts/maps_candidates.json` |
| Commit | non ancora committato |
| Contesto | Primo blocco della fase "guide dei tracciati" consegnato da Claude Desktop (`files_nuovi.zip`). Le mappe a disco sono in gran parte layout storici sbagliati: stesso errore delle foto, scelta fatta sul nome del file. |

**Catalogo messaggi:**
1. «riprendiamo il lavoro dell'ultima volta, leggi la memoria e partiamo» → status esposto, consegna non ancora arrivata.
2. «ok appena scaricato il nuovo lotto … cercalo in download» → letto e giudicato tutto il blocco 1.
3. «ok fai il provino delle mappe, ricontrolla tutto poi inizia a buttare giù quel che serve per lavorare».
4. «sì applica La Source e prepara il prompt di sollecito».
5. «aspetta prima uso il tool poi vedi te dopo» → provino usato da Edoardo.
6. «ok ho esportato il json ora procedi».
7. «facciamo in modo di avere solamente il layout della pista esatto ed aggiornato invece di
   cercare per forza quello con le curve numerate» → **cambio di criterio**, vedi sotto.
8. «sì è sopraelevata, correggi il catalogo a 4.259» → verifica in gioco fatta da Edoardo.

**Consegna ricevuta (parziale):** `maps_candidates.json` **5/5** circuiti · `tracks_knowledge_*.json`
**2/5** (spa, imola) · `REPORT.md` parziale. Mancano zandvoort (che lui dichiara bloccato su una
discordanza), zolder, kyalami.

**Modifica:**
- NEW **`build_maps_proof.py`** → `frontend/public/assets/_provino_mappe.html`. Risolve i candidati
  contro l'API di Commons e li mette a schermo come immagini vere, su **placca avorio** (come li
  vedrà la UI), con sotto la *prova* e il *rischio* scritti da Claude Desktop, l'**impronta del
  catalogo** (km + curve) come metro di paragone, badge `trappola`/`dubbio`/`probabile`, zoom a
  tutto schermo, `Nessuna adatta`, localStorage, export **`maps_choice.json`**.
- NEW **`check_track_knowledge.py`**: controlla le guide consegnate (schema, numerazione contigua,
  numero di curve contro `tracks.json`, vocabolario di `freni.stress`/`track_limits.rischio`,
  fonti, stime marcate) e soprattutto la **coerenza del lato gomma**: in curva a destra si carica
  il lato sinistro. Riconosce un campo `direzione` per curva, se c'è.
- I due knowledge file promossi in `backend/app/core/data/tracks_knowledge/`. Unica modifica alla
  consegna, su ok esplicito: **Spa T1 La Source**, `gomme.stress` «anteriore **destro** in ingresso»
  → «anteriore **sinistro** in ingresso» (tornante destro ⇒ carica il lato sinistro). Verificato per
  confronto campo per campo con il file consegnato: **1 solo campo cambiato**, tutto il resto
  identico.

**Motivazione:** stessa lezione delle foto un giro dopo — su un circuito è peggio, perché due
layout dello stesso autodromo a trent'anni di distanza hanno lo stesso nome, lo stesso stile e la
stessa dimensione, e differiscono per un tratto di pista. E sul testo: il blocco 1 sono 38 curve e
le ho lette a mano, ma 25 circuiti sono ~450 — serve una macchina che faccia i controlli
meccanici e dica a voce alta cosa *non* può controllare.

**Risultato osservato:** provino con **130 candidati su 5 circuiti** (27 proposti da Claude Desktop
+ il resto delle categorie Commons). Verificato a schermo: immagini, scelta, banner verde con
`annulla`, contatore, persistenza. Il ripescaggio dalla categoria ha già ripagato: su **Kyalami**,
dato nel REPORT come "un solo candidato utilizzabile", la categoria contiene `Kyalami 16.png`
(2560×1577, CC BY-SA 4.0, con nomi e numeri di curva) — molto meglio del PNG 1330×706 proposto.

**Trovato leggendo (non è nel REPORT di Desktop):**
1. **Spa T1 La Source**: `gomme.stress` = «anteriore destro in ingresso» su un tornante **destro** —
   in curva a destra si carica l'anteriore **sinistro**. Unico caso su 38 curve: le altre 37 sono
   corrette. È il campo che Gigi userebbe per leggere le temperature.
2. **Spa T3 Raidillon**: il testo dice «gira ancora a sinistra» e il carico è coerente con una
   sinistra, ma in gran parte dei riferimenti Raidillon è la **salita a destra**. Da incrociare con
   la mappa scelta (il REPORT ammette che a Spa l'abbinamento nome↔numero è la parte debole).
3. **Imola: zero errori** su 19 curve.
4. I 27 titoli di file esistono **tutti** su Commons: niente inventato. Tre "candidati" di
   Zandvoort sono lo **stesso file** via redirect.
5. Le `commons_category` in `tracks.json` sono in gran parte **inesistenti** (`Category:Maps of …`):
   le categorie vere si chiamano `Category:<circuito> circuit maps`. Lo script le ricava dai file.

**Verifica:** `tsc --noEmit` 0 err · `test_parser` **12/12** · provino verificato a schermo
(spa, kyalami) e localStorage riazzerato dopo la prova · prova del nove del validatore: aggiungendo
`direzione: "destra"` a La Source l'errore esce come ERRORE, poi file ripristinato identico.

**Seconda parte (stessa iterazione) — la scelta applicata:**
- Edoardo ha scelto **5/5** nel provino (Zandvoort inclusa) ed esportato `maps_choice.json`.
- NEW **`apply_maps.py`**: porta a disco i layout approvati. Tre differenze dalle foto, tutte
  obbligate: gli **SVG si scaricano interi** (su un SVG `Special:FilePath?width=` restituisce un
  PNG renderizzato, che salvato `.svg` sarebbe un file rotto); il **vecchio file va cancellato**
  e non sovrascritto (le mappe nuove sono PNG, le vecchie SVG: con entrambi a disco il manifest
  indicizza due file sotto il ruolo `map` e vince l'ultimo in ordine alfabetico, cioe' proprio
  quello sbagliato); via anche i **`_layout.svg`** di `clean_maps.py`, che erano ricavati dai file
  vecchi e quindi sbagliati uguale.
- MOD **`apply_photos.py`**, due correzioni necessarie prima di applicare:
  (a) `scrivi_attribuzioni` scriveva a mano `..._map.svg` per i layout — con le mappe PNG i crediti
  avrebbero indicato un file inesistente; ora usa il percorso vero dal registro;
  (b) `--riscopri-mappe` ricostruiva `maps.json` **da zero** per sha1: i raster sono miniature
  scalate e il loro sha1 non corrisponde a nulla su Commons, quindi sarebbero spariti dai crediti
  in silenzio. Ora il registro si **fonde** invece di essere riscritto.

**Risultato osservato (parte 2):** 5 layout a disco — `imola_map.png` (1183×672, 19 curve
numerate), `zandvoort_map.png` (1920×1753, 14 numerate + nomi + settori a colori),
`kyalami_map.png` (1330×706, 16 numerate + nomi), `zolder_map.svg` (13 KB, nomi + numeri),
`spa_francorchamps_map.png` (880×1244). `maps.json` 25 layout (5 aggiornati), `manifest.json`
25/25 piste, `ATTRIBUTIONS.md` **78/78 righe** a 6 colonne, nessuna parentesi non codificata.

**Verifica incrociata mappa ↔ catalogo (fatta guardando le mappe scaricate):**
| pista | numeri sulla mappa | `corners` nel catalogo | |
|---|---|---|---|
| imola | 19 | 19 | ✓ |
| zandvoort | 14 | 14 | ✓ |
| kyalami | 16 | 16 | ✓ |
| zolder | **11** | 10 | ✗ da sciogliere |
| spa | **nessuno** (mappa muta) | 19 | ✗ da sciogliere |

> Sciolto un dubbio del REPORT: `Spa-Francorchamps of Belgium.svg` **e' il layout attuale** — la
> Bus Stop e' la chicane corta post-2007, guardata a schermo. Ma numera fino a **20**, mentre il
> catalogo e la guida dicono 19.

**Cambio di criterio deciso in corsa (messaggio 7): conta solo che il layout sia esatto e
aggiornato, i numeri di curva sulla mappa non sono piu' un requisito.** Supera la decisione del
03/09. Motivo di Edoardo: pretendere le curve numerate restringe il campo al punto da rendere
impossibile trovare le mappe giuste. Conseguenza: i due disallineamenti qui sopra (Spa 20 vs 19,
Zolder 11 vs 10) **non arrivano piu' a schermo**, perche' la mappa non mostrera' numeri che
contraddicono la guida. Memoria `pitwall-guide-tracciati` aggiornata di conseguenza.

**Verifica del layout col criterio nuovo** — la descrizione del file su Commons, non il nome:
| pista | file scelto | dichiarazione su Commons |
|---|---|---|
| spa | `Spa-Francorchamps-2007-v2.png` | "2007 layout of Spa-Francorchamps circuit" ✓ |
| imola | `Autodromo Enzo e Dino Ferrari 2022.png` | "Trazado de Imola", 2022 ✓ |
| zandvoort | `Zandvoort Circuit.png` | **"Zandvoort Circuit Layout (2020–present)"** ✓ |
| zolder | `Circuit Zolder-2002.svg` | "Circuit Zolder-2002 until today" ✓ |
| kyalami | `Kyalami Track Map 2016.png` | "Track layout from 2016-present" ✓ |

**Unica modifica alla scelta di Edoardo:** Spa passato da `Spa-Francorchamps-2007.png` a
`-v2.png`. **Non e' un cambio di layout**: Commons dichiara il secondo come "Other version" del
primo, stessa descrizione, stesso autore, stessa licenza — cambia solo che e' **1244×880 invece
di 880×1244**, cioe' orizzontale, e la banda della scheda e' 540×280. In verticale sarebbe
comparso minuscolo. Reversibile rimettendo il titolo in `maps_choice.json` e rilanciando lo script.

**Zandvoort CHIUSA (messaggio 8).** Edoardo ha verificato in gioco: **l'ultima curva e'
sopraelevata**, quindi ACC ha il layout 2020 e la mappa scelta e' quella giusta. MOD `tracks.json`,
4 righe su 666 (modifica chirurgica sul testo: le sezioni `assets` stanno su una riga sola e un
round-trip JSON avrebbe riformattato tutte e 25 le voci):
- `zandvoort.length_km` **4.307 → 4.259** (4.307 era la lunghezza del pre-2020);
- `zandvoort.corners_confidence` `da_verificare` → `alta`;
- `zandvoort.corners_note` **riscritta**: diceva il contrario di quello che si e' visto in gioco —
  «ACC riproduce il layout precedente al riprofilamento del 2020». Era quella nota a giustificare
  i 4.307 km. Adesso dichiara il layout 2020 e da' conto della correzione;
- `kyalami.corners_confidence` `da_verificare` → `alta`: la mappa "2016-present" numera 16 curve,
  quante ne porta il catalogo. La differenza di 7 m sulla lunghezza (4.522 contro i 4.529 di
  Wikipedia) resta aperta e `length_confidence` resta `da_verificare`.

> **Nota di metodo:** il campo `corners_note` di Zandvoort e' un caso da ricordare. Non era un
> dato mancante ma un dato **sbagliato e assertivo**, che aveva gia' prodotto un secondo dato
> sbagliato (la lunghezza) e che avrebbe fatto scartare la mappa giusta. Un `DA_VERIFICARE` in
> fondo a una nota non protegge da niente se nessuno va a verificare.

**File protetti:** ☐ nessuno toccato
**Decisione:** ☐ Mantenuto — **non ancora committato, in attesa di «ok push»**

> **Note aperte:** `maps_choice.json` NON si chiama `maps.json` apposta — quel nome è già il
> registro delle attribuzioni letto da `apply_photos.py`, e due schemi con lo stesso nome
> avrebbero svuotato `/crediti` in silenzio (stessa classe della trappola regex a 6 colonne).
> · Manca ancora `apply_maps.py` (porta a disco la scelta e rigenera il registro): si scrive dopo
> la scelta di Edoardo. · **Zandvoort resta bloccato** finché non si verifica in gioco se l'ultima
> curva è sopraelevata (layout 2020, 4.259 km) o no (pre-2020, 4.307 km come dice il catalogo).

---

## Entry #025 — Regole del blocco 2, guide zolder e zandvoort, pulizia `clean_maps.py`, README bilingue

| Campo | Valore |
|---|---|
| Data | 08/09/2026 (seconda metà) · 10/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | MOD `backend/scripts/check_track_knowledge.py` · MOD `build_maps_proof.py` · NEW `tracks_knowledge/{zolder,zandvoort}.json` · DEL `backend/scripts/clean_maps.py` · `README.md` + NEW `README.it.md` · MOD `backend/.env.example` · MOD `frontend/.env.local.example` |
| Commit | `802d841` (validatore) · `2bb38c6` (guide) · `d20da60` (README) · questo log |
| Contesto | L'08/09, dopo la consegna della PRR, la sessione è andata avanti ma si è chiusa per l'utilizzo residuo senza commit né entry. Il 10/09 si riparte dalla memoria, che era rimasta indietro rispetto al repo. |

**Catalogo messaggi (10/09):**
1. «leggi la memoria e riprendiamo il lavoro lasciato in sospeso» → status ricostruito dai file
   (date, diff, session-cache): la memoria diceva «guide 2/5» e «sei domande senza risposta», il
   repo aveva già 4 guide e le risposte trasformate in controlli.
2. «fuori dal repo la prr checklist, invece dimmi in breve che cosa ti è arrivato nell'ultimo file
   zip e che cosa ti manca» → `PRR_CHECKLIST_PitWall.md` resta **non tracciata**; riepilogo di
   `files.zip` riletto dal file, non a memoria.
3. «allora procedi con la coda leggera, parti da clean_maps» → scelte di Edoardo: cancellare
   `clean_maps.py` e i 20 `_layout.svg` residui.
4. Sei risposte sul README: esame superato e build vera e propria · roadmap sostituita dal
   backlog · deploy «da decidere» · variabili mancanti aggiunte · lingua da chiarire · elenchi
   ridotti alle cartelle.
5. «1 va bene, 2 ok push. per il read me fallo sia in inglese che in italiano» → due file
   (`README.md` inglese, `README.it.md` italiano).

La seconda metà dell'08/09 non ha un catalogo messaggi: è ricostruita da `.claude/session-cache.md`
e dal prompt di sollecito sul Desktop.

**Modifica — A) 08/09, regole del blocco 2 e guide (`802d841`, `2bb38c6`):**
- Le sei domande rimaste aperte nella #024 hanno avuto risposta e sono diventate controlli in
  `check_track_knowledge.py`: **`direzione` obbligatoria** su ogni curva (una guida intera senza =
  1 errore «in attesa del retrofit», non N); 4 campi di pista raccomandati (`senso_marcia`,
  `dislivello_m`, `rettilineo_piu_lungo_m`, `variante_acc`) come «da controllare», non errori;
  regola su `gt3_ref_lap_time` (o fonte, o stima di mestiere con confidence non alta).
  `build_maps_proof.py`: solo la docstring (consegna mappe = intera categoria Commons).
- Consegna dell'08/09 (`files.zip`): **zolder** e **zandvoort** accettate; **kyalami scartata**
  (troncata, curve 7-16 con `tipo`/`origine`/`confidence` a null); spa e imola riscritte **non
  applicate**; `maps_candidates.json` non serviva. Nessuna delle 5 guide aveva `direzione`.
- Correzioni su zandvoort, su ok di Edoardo: **T1 Tarzanbocht** «anteriore destro» → «anteriore
  sinistro» (curva a destra ⇒ carica il sinistro), trovata dal validatore; `verifica_catalogo`
  riscritta, perché dava ancora aperto il dubbio sul layout chiuso il 07/09.
- Girato a Claude Desktop `PROMPT_sollecito_guide_blocco1.txt`: chiede `direzioni_retrofit.json`
  (62 curve su spa, imola, zolder, zandvoort), kyalami rifatta da sola e un REPORT dei null.
  **Al 10/09 la risposta non è arrivata.**

**Modifica — B) 10/09, `clean_maps.py` e i `_layout.svg`:**
- DEL `backend/scripts/clean_maps.py` (mai committato, nessun chiamante; la sua docstring
  descriveva il filtro invert abbandonato il 07/09 per la placca chiara).
- DEL i **20 `{id}_layout.svg`** rimasti in `frontend/public/assets/tracks/`, ricavati dalle mappe
  vecchie. Non erano innocui: `fetch_assets.scrivi_manifest` indicizza tutto ciò che sta nella
  cartella, quindi il manifest li offriva come ruolo `layout` — il campo che una futura pagina
  mappe avrebbe usato, con 20 tracciati sbagliati. Il ruolo giusto è `map`; `SessionBriefing.tsx`
  oggi legge solo `photo`.
- Rigenerati manifest e crediti con `apply_photos.py --no-download` (prima un `--dry-run`: nulla
  da scaricare, nessuna foto da rimuovere). Nessuna traccia in git: file non tracciati e asset
  gitignorati.

**Modifica — C) 10/09, README e `.env.example` (`d20da60`):**
- `README.md` in inglese e `README.it.md` in italiano, con link reciproco e stessi contenuti.
  Stato attuale (esame superato, build in corso), 7 pagine e 8 rotte, avvio **senza `--reload`**,
  avviso su `npm run build`, sezione Test, come riscaricare le immagini, roadmap = backlog vero,
  deploy «da decidere».
- Chiesto «LLM funzionante»: **non scritto così**, perché il ramo è implementato ma spento di
  default e mai messo sotto carico. Il README dice come si accende e perché resta spento.
- **Errore del vecchio README trovato durante la verifica:** per l'LLM reale non basta
  `PITWALL_ALLOW_LIVE=1`; `config.py` richiede anche `PITWALL_DEMO_MODE=0` (default 1).
- `.env.example`: aggiunte le 4 variabili lette dal codice e assenti negli esempi
  (`PITWALL_CHAT_MAX_TOKENS`, `PITWALL_PROMPT_LOG_PATH`, `PITWALL_INCIDENTS_PATH`,
  `NEXT_PUBLIC_GOOGLE_CLIENT_ID`). Nella PRR ne erano state contate 3. Le due dei registri sono
  commentate: i default hanno lo stesso nome di `PROMPT_LOG.md` e `INCIDENTS.md`, percorso relativo
  alla cartella di avvio, e `open()` non crea cartelle.

**Verifica:**
- `test_parser` **12/12**, lanciato col comando scritto nel README.
- `check_track_knowledge.py`: 4 guide, **4 errori, tutti «manca `direzione`»**, nessuno di contenuto.
- Manifest **98 → 78** voci: tolte solo le 20 `layout`, nessuna aggiunta o cambiata.
  `ATTRIBUTIONS.md` **identico riga per riga** (108 righe), quindi `/crediti` invariata.
- Variabili d'ambiente: **12** lette dal codice, **12** negli esempi, nessuna in più o in meno.
- README: le due lingue hanno 14 titoli, 19 righe di tabella, 5 blocchi di codice, nessun link
  locale rotto. `apply_maps.py --dry-run` funziona lanciato dalla radice, come dice il README.
- Nessun file di `frontend/src` toccato: `tsc --noEmit` non necessario.

> **Nota di metodo (commit):** il primo commit di questa entry non è partito. PowerShell 5.1 passa
> male a git le virgolette doppie dentro un here-string (`"in attesa del retrofit"` → pathspec
> separati); il `git add` successivo ha trovato gli script ancora in stage e il commit delle guide li
> ha inglobati, sotto il messaggio sbagliato. Intercettato prima del push e diviso con un
> `reset --soft` del solo commit locale, con controllo che il precedente fosse `origin/main`.
> **Regola:** messaggi di commit da file (`git commit -F`) o da heredoc in Bash, mai inline in
> PowerShell.

**File protetti:** ☑ nessuno toccato
**Decisione:** ☑ Mantenuto — committato e pushato su «ok push»

> **Note aperte:** in attesa della risposta al sollecito (retrofit `direzione` + kyalami). Nel
> PROMPT_LOG, la sezione «Contesto tecnico rapido» in testa insegna ancora `--reload` all'avvio.
> Prossimo della coda: **MUST #1, logging del ramo LLM**, da proporre prima di scrivere codice.

---

## Entry #026 — MUST #1 della PRR: il ramo LLM diventa osservabile (log rotante + request-id)

| Campo | Valore |
|---|---|
| Data | 10/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | NEW `backend/app/logging_config.py` · MOD `backend/app/{config,main}.py` · MOD `backend/app/api/{analysis,vision}.py` · NEW `backend/app/tests/test_observability.py` · MOD `.gitignore` · MOD `backend/.env.example` · MOD `README.md` + `README.it.md` · MOD testata del PROMPT_LOG |
| Commit | `4ae01b2` (backend + test) · `0f0a74f` (README) · questo log |
| Contesto | Primo MUST del Product Backlog uscito dalla PRR dell'08/09. Scelte già fatte l'08/09: rotante 1 MB × 3 in `backend/logs/pitwall.log`, percorso da `__file__`, request-id, `agent.py` non si tocca. |

**Catalogo messaggi:**
1. «procedi» → proposta esposta prima del codice, dopo aver tracciato il percorso reale in V2.
2. Quattro risposte: nel log **solo la lunghezza** del testo del pilota · includere **anche
   `vision.py`** · registri di `agent.py` **in `backend/logs/`** · ritocchi collegati tutti e tre
   (README sulla chat, `--reload` nei commenti, `.env.example` dei registri).

**Il percorso tracciato in V2 — due correzioni alla PRR:**
- La PRR diceva che «ogni guasto del ramo reale non lascia traccia». **Era esagerato.** Gli errori
  delle chiamate ad Anthropic e le risposte malformate li registra `agent.log_incident()` in un
  markdown, con percorso relativo alla cartella di avvio (cioè `backend/INCIDENTS.md`, non il
  registro della radice). Senza traccia restavano: le eccezioni che escono da `get_ai_response`,
  inghiottite da `analysis.py:98` (caso reale: sopra gli 8000 token la funzione importa
  `streamlit`, **che non è installato**); la chiave mancante (fallback muto); la risposta non
  valida vista dall'endpoint; latenza e correlazione; ogni guasto di `vision.py` (500 al client,
  niente sul server).
- **Le chiamate reali al modello sono due, non una.** `/api/setup/from-image` usa
  `claude-sonnet-4-6` e **non guarda `PITWALL_ALLOW_LIVE`**: le basta la chiave. Con una chiave nel
  `.env` ogni screenshot la consuma anche in demo-mode. Non corretto qui: è un dato per il
  **modello di costo** (MUST #2), scritto nella roadmap dei README.
- `chat_with_gigi()` esiste in `agent.py` ma **nessuna rotta la chiama**: i README la davano per
  implementata senza dirlo. Precisato.

**Modifica:**
- NEW **`logging_config.py`**: logger `pitwall`, `RotatingFileHandler` su `backend/logs/pitwall.log`
  (1 MB × 3, UTF-8, da INFO), console da WARNING, request-id da `ContextVar` inserito da un filtro
  **sugli handler** (i filtri del logger non valgono per i figli), `propagate = False`.
  Richiamabile: sostituisce gli handler invece di duplicarli.
- MOD **`config.py`**: `LOG_DIR` da `__file__`; `os.environ.setdefault` per
  `PITWALL_PROMPT_LOG_PATH` / `PITWALL_INCIDENTS_PATH` → `backend/logs/llm_token_log.md` e
  `llm_incidents.md`. Sposta i registri di `agent.py` **senza toccarlo**: `agent.py` legge
  l'ambiente all'import, e lo importano solo gli endpoint. Un `.env` vince sempre.
- MOD **`main.py`**: middleware HTTP con request-id (quello del client solo se
  `[A-Za-z0-9._-]{1,64}`, altrimenti generato), durata, header `X-Request-ID` in risposta,
  `log.exception` sulle eccezioni non gestite. Docstring senza `--reload`.
- MOD **`analysis.py`**: ogni ramo registra `source` e, in fallback, **il motivo** (chiave
  assente · eccezione con traceback · tutti i modelli falliti · risposta senza le 4 sezioni) e la
  durata. Del testo del pilota solo lunghezza e presenza del profilo. **Contratto e testo restituito
  invariati.**
- MOD **`vision.py`**: WARNING sul 503, ERROR con traceback prima del 500, INFO con durata; nel log
  byte e tipo del file (`%r`, perché il tipo arriva dal client).
- `.gitignore` → `/backend/logs/`. `.env.example` → commento dei registri col default nuovo.
- README (EN + IT): chat di Gigi dichiarata **non collegata**, sezione **Log**, voce
  «Osservabilità» tolta dalla roadmap (fatta), costo esteso alla lettura screenshot, `logging_config.py`
  nella struttura. Testata del PROMPT_LOG: tolto l'ultimo `--reload`.

**Verifica:**
- NEW `test_observability.py` (offline, rete bloccata stubbando `call_claude`, log in cartella
  temporanea): **22/22**. Il caso dell'eccezione usa la `get_ai_response` **vera** con un input da
  33.000 caratteri e registra `ModuleNotFoundError: No module named 'streamlit'`. Verificato anche
  che il request-id arriva nella riga scritta dal thread dell'endpoint sincrono.
- `test_parser` **12/12** · `py_compile` dei 6 file · variabili d'ambiente 12 lette = 12 dichiarate ·
  README EN e IT con 15 titoli, 19 righe di tabella e 5 blocchi di codice ciascuno.
- **Backend reale** avviato staccato: health 200; `POST /api/analysis` → 200 `source=demo`, stesso
  request-id nell'header e nelle due righe di log; screenshot senza chiave → 503 con WARNING anche
  nella console di uvicorn; marcatore del prompt **assente** dal log; `git check-ignore` conferma
  `backend/logs/`. Backend spento dopo la prova, com'era all'inizio.

**File protetti:** ☑ nessuno toccato (`agent.py` e `vision_parser.py` solo letti)
**Decisione:** ☑ Mantenuto — committato e pushato l'11/09 su «ok push»

> **Note aperte:** quale modello ha risposto in cascata non arriva a `pitwall.log`: `agent.py` non lo
> restituisce, lo scrive solo nel suo `llm_token_log.md`. `vision.py` è `async` ma chiama il parser
> sincrono, che blocca l'event loop per tutta la chiamata al modello: da valutare con lo stress test.
> L'`import streamlit` a `agent.py:134` ora almeno **si vede**; toglierlo resta un intervento su file
> protetto.

---

## Entry #027 — La lettura screenshot passa dal presidio della demo-mode

| Campo | Valore |
|---|---|
| Data | 11/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | MOD `backend/app/api/vision.py` · MOD `backend/app/tests/test_observability.py` · MOD `README.md` + `README.it.md` · MOD `docs/03-v2-architecture.md` · MOD `backend/.env.example` |
| Commit | `ff5ff89` (codice + test + documentazione) · questo log |
| Contesto | Primo passo del MUST #2 (modello di costo), chiesto come intervento a sé: «fai subito ma prima fai tutti i controlli necessari». Entry #026 pushata in apertura di sessione (`4ae01b2` · `0f0a74f` · `d839d97`). |

**Catalogo messaggi:**
1. «leggi la memoria e riprendiamo il lavoro di ieri» → status: allineato a `origin`, Entry #026 non committata, test 12/12 e 22/22, nessuna consegna nuova da Claude Desktop.
2. «ok push» → tre commit dell'Entry #026 e push.
3. Risposte alle tre domande sul costo: tetto e periodo li scelgo io («il più efficiente e meno costoso»,
   categorizzando i modi di utilizzo); il blocco sugli screenshot subito, dopo i controlli.

**Controlli fatti prima di toccare il codice:**
- Chiamate reali al modello in `backend/app`: **tre**. `agent.call_claude` (analisi, dietro il presidio),
  `agent.chat_with_gigi` (nessuna rotta la chiama), `vision_parser.parse_setup_from_image` — l'unica
  raggiungibile **senza** presidio.
- Il README diceva «con `PITWALL_ALLOW_LIVE=0` la chiave non si consuma mai»: per gli screenshot **era
  falso**. `docs/02-repo-strategy.md` pianificava la rotta come «feature-flag»: il presidio mancante era
  una deviazione dal progetto, non una scelta.
- Frontend (`setup/page.tsx:497`): un 503 mostra già «🔒 Richiede la chiave server (in demo non è
  attiva)». Il blocco non richiede modifiche all'interfaccia.
- `backend/.env` assente su questo PC: oggi nessuno spendeva, nessuna regressione possibile in locale.

**Modifica:**
- `vision.py`: prima di tutto, anche della chiave, `if config.demo_mode()` → **503** «Lettura screenshot
  disattivata in demo-mode» + WARNING nel log con i due flag necessari. Scelto `demo_mode()` e non
  `allow_live()`: è la stessa regola della Console e del README (servono **entrambi**
  `ALLOW_LIVE=1` e `DEMO_MODE=0`), e `demo_mode()` è documentata come «nessuna rete». Il file caricato
  non viene nemmeno letto.
- README EN+IT: il presidio vale anche per gli screenshot; tolta dalla roadmap la frase sul flag
  aggirato. `docs/03`: 503 in demo-mode nel contratto API. `.env.example`: commento del flag.

**Verifica:**
- `test_observability` **24/24** (+2: T14 demo-mode con chiave presente → 503 e parser **mai chiamato**,
  contato con una spia; T15 `ALLOW_LIVE=1` ma `DEMO_MODE=1` → 503). Numerazione T16–T24 slittata.
- **Controprova:** con il `vision.py` di HEAD i due test nuovi **falliscono** (22/24), quindi misurano
  davvero il difetto.
- `test_parser` **12/12** · `py_compile` ok.
- **Backend reale** avviato staccato (demo-mode, senza `.env`): `POST /api/setup/from-image` → `503`
  `{"detail":"Lettura screenshot disattivata in demo-mode"}`, riga WARNING con lo stesso request-id
  dell'header. Backend spento dopo la prova, com'era all'inizio.

**File protetti:** ☑ nessuno toccato (`vision_parser.py` e `agent.py` solo letti)
**Decisione:** ☑ Mantenuto — committato e pushato l'11/09 su «ok push»

---

## Entry #028 — MUST #2 della PRR: tetto di spesa del ramo LLM

| Campo | Valore |
|---|---|
| Data | 11/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | NEW `backend/app/budget.py` · MOD ⚠️`backend/app/core/agent.py` · MOD ⚠️`backend/app/core/vision_parser.py` · MOD `backend/app/api/{analysis,vision}.py` · NEW `backend/app/tests/test_budget.py` · MOD `backend/app/tests/test_observability.py` · MOD `backend/.env.example` · MOD `README.md` + `README.it.md` · MOD `docs/03-v2-architecture.md` |
| Commit | `7fa6d37` (backend + test) · `ae07561` (README + docs) · questo log |
| Contesto | Secondo MUST del Product Backlog uscito dalla PRR. Entry #027 pushata subito prima (`ff5ff89` · `d9c9d34`). |

**Catalogo messaggi:**
1. Tre domande poste (tetto in chiamate o in token/euro? su che periodo? blocco screenshot subito?).
   Risposta: «scegli il migliore (il più efficiente e meno costoso sennò vedi tu)» · «vedi il migliore
   che ovviamente dipende dai modi di utilizzo e forse sarebbe meglio categorizzarli» · screenshot
   subito (→ Entry #027).
2. Proposta esposta con i conti; «ok push e procedi» = push dell'Entry #027 + **«ok procedi»** sui
   due file protetti.

**Le scelte e perché:**
- **Tetto in dollari sul costo reale, non in numero di chiamate.** Conti con i listini verificati
  sulla documentazione (haiku-4-5 $1/$5, sonnet-4-6 $3/$15 per milione di token): un'analisi tipica
  costa ~1 centesimo, quella peggiore (haiku×2 + sonnet×2) ~13. Un tetto a chiamate va prezzato sul
  caso peggiore e bloccherebbe l'app 13 volte prima del necessario.
- **Prenotazione + saldo.** Prima di ogni chiamata si prenota il costo massimo (byte di input, perché
  un token non è mai più corto di un byte, + margine + tutti i `max_tokens`); dopo si salda con
  `message.usage`. Il tetto non si supera nemmeno con richieste concorrenti. Serve `usage`, che
  `agent.py` e `vision_parser.py` non restituivano: da qui l'aggancio nei due protetti.
- **Categorie = modi di utilizzo:** `analisi` · `screenshot` · `chat` (tetto 0: nessuna rotta).
  **Periodi:** giornaliero per categoria + mensile complessivo. **Niente tetto per sessione:** senza un
  login vero lato server non si potrebbe far rispettare. Default: $0,50 · $0,25 · $0 · mese $5.
- **Sempre per eccesso:** chiamata fallita = resta il massimo; modello fuori listino = listino più
  caro; `.env` non valido = 0; stato illeggibile = chiamate bloccate (non si riparte da zero); a
  cavallo di mezzanotte il costo reale va nel giorno nuovo.
- **Scartati:** caching del prompt (su haiku-4-5 servono ≥ 4096 token, il system prompt v4 è ~7200
  caratteri) · passaggio a `claude-sonnet-5` ($2/$10, −33%): thinking adattivo attivo di default e
  immagini fino a ~3× i token, da valutare con lo stress test.

**Modifica:**
- NEW **`budget.py`**: `prenota()` / `salda()` / `disponibile()`, listino, tetti da env letti a ogni
  chiamata, stato in `backend/logs/llm_spesa.json` con scrittura atomica e `threading.Lock`. Riga INFO
  per ogni saldo con **modello, token e costo** — chiude la nota aperta dell'Entry #026 («quale
  modello ha risposto non arriva a `pitwall.log`»). WARNING a ogni rifiuto.
- ⚠️ **`agent.py`** (sbloccato con «ok procedi»): `call_claude` prenota «analisi» prima e salda dopo
  (il system prompt letto una volta sola invece che dentro la chiamata, stesso contenuto);
  `chat_with_gigi` prenota «chat» dentro il `try` e salda con `stream.get_final_message()`. Un rifiuto
  dentro la cascata è un'eccezione come le altre: `get_ai_response` passa al modello successivo, che
  viene rifiutato a sua volta, e il registro guasti scrive «tetto di spesa raggiunto».
- ⚠️ **`vision_parser.py`** (sbloccato con «ok procedi»): costanti `VISION_MODEL` / `VISION_MAX_TOKENS`
  al posto dei letterali (stessi valori), prenotazione «screenshot» con un'immagine, saldo.
  **Nessuna logica di parsing toccata.**
- **`analysis.py`**: nel ramo reale, prima di chiamare, testo oltre **4000** caratteri (prompt) o
  **1000** (profilo) → fallback con motivo; categoria senza margine → fallback con motivo. Contratto
  invariato. Effetto collaterale utile: l'input massimo (~5400 caratteri) resta lontano dai ~32.000
  che fanno scattare l'`import streamlit` di `agent.py:134`, ora **irraggiungibile dall'API**.
- **`vision.py`**: `BudgetEsaurito` → **429** «Tetto di spesa raggiunto per la lettura screenshot.»
  (il frontend mostra il `detail` così com'è); stato illeggibile → 503.
- `test_observability`: stato della spesa in cartella temporanea; T09 ora è il testo oltre il limite
  (modello mai chiamato), T10 l'eccezione nel ramo LLM con la privacy nel traceback.
- `.env.example` (4 variabili), README EN+IT (sezione *Tetto di spesa* con tabella, log, test,
  struttura, roadmap: tolto il modello di costo, primo punto ora lo stress test), `docs/03`.

**Verifica:**
- NEW `test_budget.py` offline con client Anthropic finto: **30/30** — conti (byte, fuori listino,
  cache), prenotazione e saldo, tetti giornaliero/mensile/categorie indipendenti, `.env` non valido,
  giorno e mese nuovi, mezzanotte, stato illeggibile, **20 thread con un tetto da 5 → passano
  esattamente 5**, cascata haiku×2→sonnet con spesa = somma dei costi reali, chat, endpoint in live.
- **Controprova:** con `agent.py` e `vision_parser.py` di HEAD falliscono 10 test su 30 (tutti quelli
  che attraversano le chiamate reali); ripristinati, 30/30.
- `test_observability` **24/24** · `test_parser` **12/12** · `py_compile` · variabili d'ambiente: 14
  lette = 14 dichiarate.
- **Backend reale** avviato staccato in **live** con chiave finta e tetti a $0,001, cioè sotto ogni
  prenotazione: **nessuna richiesta di rete**. `POST /api/analysis` → 200 `source=fallback`, due
  WARNING (haiku prenotazione $0,0217, sonnet $0,0652) con lo stesso request-id; `POST
  /api/setup/from-image` → **429** con il messaggio (prenotazione $0,0249). Backend spento; cancellato
  il `llm_incidents.md` nato dalla prova (prima non esisteva). Visto nel log e corretto: i tetti
  piccoli comparivano come «$0.00», ora `%g`.

**File protetti:** ☑ sbloccati con «ok procedi» → `agent.py`, `vision_parser.py` (solo aggancio, +27 −3)
**Decisione:** ☑ Mantenuto — committato e pushato l'11/09 su «ok push» (`7fa6d37` · `ae07561` · `fd852ba`)

> **Note aperte:** (1) `agent.py` crea il client con `timeout=30.0` e l'SDK ripete da solo fino a 2
> volte: una risposta sonnet da 2500 token può sforare i 30 s. Il tetto conta ogni tentativo al
> massimo, ma **se Anthropic fatturi le richieste interrotte non è verificato**: da misurare nello
> stress test. (2) Il listino in `budget.py` va aggiornato a mano se cambiano i prezzi. (3) Con più
> worker uvicorn il `threading.Lock` non basta: servirebbe un lock su file. (4) La Console, a tetto
> raggiunto, mostra «fallback» senza dire che è il tetto: il motivo sta solo nel log.

---

## Entry #029 — Primo stress test dell'LLM reale + `docs/03` riallineato al codice

| Campo | Valore |
|---|---|
| Data | 11/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | NEW `backend/scripts/stress_llm.py` · MOD `docs/03-v2-architecture.md` · NEW `backend/.env` (locale, gitignorato) |
| Commit | `5293574` (docs/03) · `c14813d` (stress_llm.py) · questo log |
| Contesto | Primo punto della roadmap dopo il tetto di spesa: accendere l'LLM reale e metterlo sotto stress. Prime chiamate reali della V2 in assoluto. |

**Catalogo messaggi:**
1. «la chat sarebbe meglio farla anche se limitata comunque sempre in quello scope, cioè essere ingegnere
   di pista. vedi se si può fare ma ci lavoreremo dopo» → fattibilità verificata e messa in memoria, nessun codice.
2. Risposte alle domande sullo stress test: «ok push» (Entry #028) · «la chiave api stava già nell'env» ·
   screenshot reali «li cercherò quando servirà» · tetto $1 «va bene» · `docs/03` «correggi tutto quel che ti serve».

**Preparazione:**
- La chiave **non** stava nel `.env` della V2 (non esisteva) né nelle variabili di Windows: stava nel `.env`
  della **v1** (`Desktop/PitWall.AI/.env`). Creato `backend/.env` copiando **solo** quella riga da file a
  file (il valore non è mai passato a schermo), `LLM_MODEL=claude-haiku-4-5`, **live spento**
  (`ALLOW_LIVE=0`, `DEMO_MODE=1`) e tetti per il test: analisi $1/giorno, mese **$1**. Verificato che
  `backend/.env` è gitignorato. Il live si accende solo nell'ambiente del processo uvicorn del test.
- NEW `stress_llm.py`: interroga il backend vero via HTTP e incrocia ogni risposta con le righe di
  `pitwall.log` dello stesso request-id (fonte, motivo, modello, token, costo). Si rifiuta di partire se
  il backend non è in live. Provato prima a vuoto contro la demo (18 richieste, zero chiamate).

**Risultati** (dati in `backend/logs/stress/`, gitignorata):

| Prova | Esito |
|---|---|
| **A** 12 domande nel perimetro (1 con profilo) | **12/12 `source=api`**, tutte con le 4 sezioni, sempre haiku al primo tentativo · 2615–2662 token in, 1049–1943 out · **$0,0079–0,0124** (media ~$0,009) · **12–24 s** |
| **B** 4 domande fuori tema | 4/4 `api`: il modello resta nel ruolo e rifiuta, ma **dentro le 4 sezioni** («## Diagnosi — Il tuo messaggio contiene una richiesta fuori scopo…»). In 2 casi su 4 la prima risposta era senza sezioni → **ripetuta**, costo doppio (~$0,01) |
| **C1** testo da 3900 caratteri | `api`, haiku, 3934/2105 token, $0,0145, **25,2 s** |
| **C2** testo da 4200 caratteri | `fallback` in 12 ms, nessuna chiamata (limite dell'Entry #028) |
| **D** 3 analisi in contemporanea | 3/3 `api` in **16,9 s** complessivi (come una sola); health interrogato 66 volte durante l'attesa, **max 9 ms** |
| **Sonnet**, domanda normale | `api` in **29,0 s** (1354 token out, $0,0282): a un secondo dal timeout di 30 s |
| **Sonnet**, testo da 3900 caratteri | **3 timeout di fila** (log dell'SDK: due «Retrying request»), `fallback` dopo **93 s** |
| Screenshot | **non provato**: nessuno screenshot reale disponibile |

**Spesa:** registro del tetto **$0,2845** su $1. Somma dei costi reali nel log $0,2078; la differenza
($0,0768) è la prenotazione della chiamata sonnet andata in timeout, rimasta al massimo come da progetto.

**Cosa ha trovato — da decidere con Edoardo:**
1. **Il timeout di 30 s di `agent.py` è il difetto principale.** Sonnet, cioè il modello di riserva
   della cascata, sta a ridosso del limite anche con una domanda normale e lo supera con un testo lungo.
   Ogni timeout l'SDK lo **ripete da solo 2 volte** (`max_retries` di default): 3× il tempo, e **una
   sola prenotazione del tetto per tre richieste**. Se Anthropic fattura le richieste interrotte (non
   verificabile da qui) il tetto conta per difetto. Proposta: in `agent.py` (protetto) timeout più
   ampio e `max_retries=0`, visto che la cascata è già il meccanismo di ripetizione.
2. **Fuori tema in live.** Il filtro per parole chiave della demo **non è riusabile**: nella prova a
   vuoto ha classificato «fuori perimetro» 5 domande della fase A su 11 perfettamente legittime (A1
   Parabolica, A2, A4, A6, A10). La risposta del modello è corretta nel merito ma forzata nel formato a
   4 sezioni, e a volte costa doppio. Da decidere come trattarla (prompt, formato, UI).
3. **Il contesto del ramo reale è sempre la sessione demo** (`_context()` di `analysis.py`: Monza,
   BMW M4 GT3, Post.DX a 105°C, pressioni fisse). Le risposte si ancorano a quei dati anche quando la
   domanda non c'entra: alla domanda sul carburante (A7) Gigi apre con «Prima di calcolare il
   carburante, stabilizza il profilo termico posteriore». Per un prodotto vero servono i dati del
   pilota (CSV, setup) nel contesto.
4. **Da giudicare nel merito (dominio di Edoardo):** A7 calcola «60 min ÷ 1.80 min/giro ≈ 33 giri × 3.2 =
   105.6 L» senza il giro in corso allo scadere del tempo né un margine. Le pressioni citate in tutte le
   risposte stanno fra 24,0 e 27,2 psi, coerenti con i range del progetto.

**`docs/03` riallineato** (era fermo al 10/07, megaprompt #2): route group `(app)`/`(auth)` e 8 pagine con le
API che chiamano, componenti e `lib/` reali, 6 router, `catalog`, logging e tetto di spesa, contratto API
completo (health, catalogo, `lap_times`, `profile`, 429/500), **pressioni demo corrette** (caldo 26.0–27.0,
freddo 24.5–25.5, delta +1.5: il documento diceva 28.5–30.0 / 26.0–27.0 / +2.5), avvio senza `--reload`,
deploy «da decidere» con le variabili vere e il rischio del registro della spesa su disco effimero, note
aperte (INC-V2-002/004/005 erano già risolti). Ogni voce verificata sui file. Stessa correzione nel
`CLAUDE.md` locale (avvio con `--reload`, 5 pagine, 5 endpoint).

**Verifica:** `test_parser` 12/12 · `test_observability` 24/24 · `test_budget` 30/30 con il `.env` vero presente ·
backend spento a fine prova.

**File protetti:** ☑ nessuno toccato
**Decisione:** ☑ Mantenuto — committato e pushato l'11/09 su «ok push». Decisioni di Edoardo sui 4 punti: (1) «ok
procedi» su `agent.py` → Entry #030 · (2) in perimetro «robe sempre riguardanti la pista e acc» · (3) dati reali del
pilota nel contesto «appena possibile» · (4) carburante «sembra di sì ma dipende dalle condizioni ed altri fattori»

---

## Entry #030 — Timeout del client LLM: 90 s e nessuna ripetizione dell'SDK

| Campo | Valore |
|---|---|
| Data | 11/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | MOD ⚠️`backend/app/core/agent.py` · MOD `backend/app/tests/test_budget.py` · MOD `backend/.env.example` |
| Commit | `d4ac3c4` (agent.py + test + .env.example) · questo log |
| Contesto | Punto 1 dello stress test (Entry #029). Entry #029 pushata (`5293574` · `c14813d` · `c3c45e3`). |

**Catalogo messaggi:**
1. «ok push. 1 ok procedi. 2 robe sempre riguardanti la pista e acc. 3 appena possibile. 4 sembra di sì ma
   dipende dalle condizioni ed altri fattori.»

**Modifica** (⚠️ `agent.py` sbloccato con «ok procedi»):
- Costanti `LLM_TIMEOUT_S = PITWALL_LLM_TIMEOUT_S` (default **90**) e `LLM_MAX_RETRIES = 0`, usate dai due
  client (`call_claude` e `chat_with_gigi`) al posto di `timeout=30.0` e delle 2 ripetizioni di default dell'SDK.
- **Perché 90:** sonnet ha prodotto ~47 token/s (1354 in 29,0 s; 2188 in 51 s): i 2500 token di `max_tokens`
  stanno in ~55 s, con margine. **Perché zero ripetizioni:** la cascata è già il secondo tentativo, e ogni suo
  passaggio prenota nel tetto; le ripetizioni interne dell'SDK erano invisibili al tetto (una prenotazione
  per fino a tre richieste).
- **Rovescio accettato:** un errore passeggero (429/529) non viene più ripetuto su haiku e la cascata passa
  subito a sonnet, che costa di più. Nello stress test non se n'è visto nessuno.
- `.env.example`: `PITWALL_LLM_TIMEOUT_S=90` documentata. `vision_parser.py` **non toccato** (usa ancora i
  default dell'SDK: 10 minuti e 2 ripetizioni): da rivedere con il test dello screenshot.

**Verifica:**
- `test_budget` **31/31** (+B21b: i client di `agent.py` nascono con il timeout configurato e `max_retries=0`;
  B25 lo controlla anche per la chat) · `test_observability` 24/24 · `test_parser` 12/12.
- **Backend reale, il caso che falliva:** sonnet come modello principale, testo da 3900 caratteri. Prima
  (Entry #029): 3 timeout, `fallback` dopo 93 s. Ora: **`source=api` in 51,0 s**, 3935/2188 token, $0,0446,
  **una sola richiesta HTTP** nel log dell'SDK, nessun «Retrying». Backend spento dopo la prova.
- Spesa registrata a settembre: $0,3292 su $1.

**File protetti:** ☑ sbloccato con «ok procedi» → `agent.py` (solo configurazione del client)
**Decisione:** ☑ Mantenuto — committato e pushato l'11/09 su «ok push»

> **Note dalle risposte di Edoardo:** (2) il perimetro di Gigi è «robe sempre riguardanti la pista e acc» —
> da tradurre nel prompt; (4) il conto del carburante regge ma «dipende dalle condizioni ed altri fattori»:
> il prompt dovrebbe chiedere o dichiarare le condizioni prima di dare un numero secco.

**Scope in definizione — dati reali del pilota nel contesto di Gigi (nessun codice scritto, si riprende dopo).**
Com'è oggi: il Setup tiene vettura, circuito, condizioni, temperature, i 49 valori e il CSV solo nello stato del
componente; la Console manda solo prompt e profilo; `_context()` aggiunge sempre la sessione demo; il system
prompt v4 ha già la sezione «UTILIZZO DATI CSV E SETUP (se forniti)».

Risposte di Edoardo (catalogo messaggi):
1. Live senza dati del pilota: «fai la seconda» → Gigi risponde in generale e dice quali dati servono; la
   sessione demo solo in demo-mode.
2. «solo cose tecnica per la risposta dell'LLM, le guide devono essere del testo messo dentro alle descrizioni
   dei tracciati» → all'LLM solo dati tecnici; le guide dei tracciati non vanno nel contesto.
3. Persistenza come il profilo (`localStorage`, cancellata entrando in modalità demo): «va bene la proposta».
4. Dashboard e Telemetria: «devono essere disponibili pure con LLM vero alla fine sono dati già analizzati e
   messi a schermo, come un report nulla di più. sono delle corrispondenze o sbaglio?» → sì: in demo schermate e
   Gigi leggono la stessa fonte; con i dati veri devono leggere gli stessi dati di Gigi.
5. Risposta fuori tema senza le 4 sezioni, con il ritocco a `agent.py`: «ok procedi».
6. «continua a fare le domande finché non hai uno scope ancora più definito e preciso. pulizia totale.»

Domande aperte, poste l'11/09: (1) con un CSV caricato le schermate mostrano quello e la demo solo in sua
assenza? (2) campi che il CSV non ha (tempi sul giro, pressioni giro per giro: il parser dà solo media/min/max)
→ card «dato non presente», nascosta, o formato CSV esteso (`csv_parser.py` protetto)? (3) pressioni del CSV a
caldo o a freddo (`demo_data.py` le dice «a freddo, da CSV/garage»)? (4) setup mandato a Gigi solo se toccato o
caricato da screenshot? (5) profilo pilota ancora a Gigi? (6) guide = testo nella scheda del circuito, senza LLM?
(7) testo fuori tema fisso o scritto dal modello? (8) «pulizia totale» = scope senza pezzi a metà, o anche
rimozione dei residui v1 (`import streamlit`, «ANALIZZA SESSIONE», «st.write_stream»)?


## Entry #031 — L0 del REWORK DATI: pulizia totale (CSV eliminato, residui Streamlit, codice morto)

| Campo | Valore |
|---|---|
| Data | 14/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | DEL ⚠️`core/csv_parser.py` · DEL `api/csv.py` · DEL `tests/test_parser.py` · MOD ⚠️`core/agent.py` · MOD ⚠️`core/vision_parser.py` (commenti) · MOD `main.py` `api/analysis.py` `tests/test_budget.py` `tests/test_observability.py` · MOD `setup/page.tsx` `lib/api.ts` `lib/instrument.ts` `lib/motion.ts` · NEW `docs/04-rework-dati.md` · MOD `README.md` `README.it.md` `docs/03-v2-architecture.md` |
| Commit | (da fare, in attesa di «ok push») |
| Contesto | Edoardo apre un **rework della logica dati**: «i csv limitano troppo la raccolta dei dati e anche l'elaborazione poi con le interfacce… fai in modo che l'analisi sia ancora più accurata, precisa e spietata». Ricerca sui concorrenti fatta online. 9 domande poste, 9 risposte, gate ricevuti. |

**Catalogo messaggi:**
1. «leggi la memoria e riprendiamo il lavoro dell'ultima volta»
2. «secondo me toccherebbe ristrutturare un po' tutta la logica per pitwall … i csv limitano troppo la raccolta dei dati … inizia a propormi delle idee o nuovi formati … se vuoi cerca online con chrome … per la pulizia totale intendevo tutti i residui di codice morto che ci sono e di streamlit, quindi da eliminare.»
3. «ok va tutto benissimo per la struttura ma ci sta un problema: i software che operano a livello kernel di norma vengono identificati come malware…» + le 9 risposte (vedi `docs/04-rework-dati.md` §5) + «vediamo di non perdere alcun progresso … tenere gli step importanti sotto memoria».
4. «va benissimo così, ok procedi e va bene tutto. iniziamo il lavoro.»

**Equivoco chiarito:** «kernel di analisi» significava *nucleo* software, non kernel di Windows →
rinominato **motore di analisi**. La shared memory di ACC è **user-space** (file mappato che Kunos
espone per le app di terze parti). Il rischio reale e residuo è un domani un `.exe` non firmato
(SmartScreen + euristiche AV): mitigato by design tenendo il registratore **dentro il backend FastAPI**,
senza processi né eseguibili nuovi da distribuire.

**Modifica — A. CSV eliminato** (⚠️ `csv_parser.py` sbloccato con «ok procedi»):
- Cancellati `core/csv_parser.py`, `api/csv.py`, `tests/test_parser.py`; rotta `/api/csv/parse`
  sfilata da `main.py` (import + tupla dei router).
- Frontend: via `postCsvParse`, `CsvResult` (`lib/api.ts`) e il componente `CsvUpload`
  (`setup/page.tsx`, ~60 righe); la griglia a 2 colonne degli upload diventa il solo `ScreenshotUpload`;
  l'etichetta del toggle non promette più il CSV.

**B. Residui Streamlit (eredità v1):**
- `agent.py`: rimosso il blocco `import streamlit as st` + `st.warning(...)` dentro `get_ai_response`
  → ora il contesto sovradimensionato si **annota nel log** (`log = logging.getLogger("pitwall.agent")`,
  nuovo); di conseguenza il parametro `show_warning`, che esisteva solo per quel blocco, è sparito
  dalla firma e dalle 2 chiamate in `test_budget`.
- `agent.py`: docstring di `get_env_var` non cita più `st.secrets`; via il riferimento a
  `st.write_stream` nella docstring di `chat_with_gigi`; via i riferimenti al CSV nelle docstring.
- ⚠️`vision_parser.py`: 3 commenti che citavano `Streamlit file_uploader` / `UploadedFile.type`
  riscritti sulla realtà v2 (rotta FastAPI). **Solo commenti, nessuna logica toccata.**
- `api/analysis.py` e `tests/test_observability.py`: commenti che citavano l'`import streamlit`.

**C. Codice morto:**
- `agent.py`: costante `MAX_RETRIES = 1` mai usata da nessuno (il riprovare lo fa la cascata dei modelli).
- `lib/instrument.ts`: `NO_GLOW`, `alarmGlow`, `MONO_CLASS` (zero riferimenti in tutto il frontend) →
  la regola estetica che documentavano resta come commento guardrail.
- `lib/motion.ts`: `cardHover`, `baseTransition` (zero riferimenti) + import `Transition` diventato inutile.
- Verificato che **non** ci sono altri file orfani (nessun modulo backend mai importato, nessun file
  frontend mai importato) e nessun `.csv` di esempio nel repo.

**D. Documentazione:**
- **Nuovo `docs/04-rework-dati.md`**: la specifica viva del rework (fonti ACC, formato canonico
  «session bundle», motore di analisi, le 9 decisioni chiuse, lotti L0–L5, baseline, posizionamento
  rispetto ai concorrenti). È la fonte di verità da aggiornare a ogni lotto, linkata da entrambi i README.
- README e `docs/03` riallineati: via il CSV da struttura, tabella rotte e comandi di test; corretto
  `test_budget` 30/30 → **31/31** (era rimasto indietro dall'Entry #030).

**Nuova baseline di verifica** (`test_parser` non esiste più): `test_observability` **24/24** +
`test_budget` **31/31** + `npx tsc --noEmit` **0 err**. I test del nuovo formato entrano con L1.

**Verifica:**
- `py_compile` su `main.py`, `agent.py`, `vision_parser.py`, `analysis.py` → OK.
- Rotte registrate dall'app: `/api/analysis`, `/api/catalog`, `/api/catalog/car/{car_id}`,
  `/api/catalog/track/{track_id}`, `/api/session`, `/api/setup-params`, `/api/setup/from-image`
  — **`/api/csv/parse` sparita**, le altre 7 intatte.
- `test_observability` **24/24** · `test_budget` **31/31** · `npx tsc --noEmit` **0 errori**.
- Nessuna chiamata LLM reale: spesa invariata ($0,3292 su $1).

**File protetti:** ☑ sbloccato con «ok procedi» → `csv_parser.py` (cancellato), `agent.py` (rimozione
Streamlit + costante morta), `vision_parser.py` (solo commenti).
**Rimasto fuori apposta:** ⚠️`prompts/chat_system_prompt.txt` riga 12 cita ancora il pulsante v1
«ANALIZZA SESSIONE» — è **contenuto** che cambia il comportamento di Gigi, non codice morto: serve un
«ok procedi» a sé e verrà riscritto con L4. Idem i commenti di `demo_data.py` che citano il CSV come
fonte delle pressioni a freddo: file protetto sui numeri, si riscrive quando la demo diventerà un bundle.

**Decisione:** ☑ Mantenuto — in attesa di «ok push».


## Entry #032 — L1 del REWORK DATI: dal file di ACC al «session bundle»

| Campo | Valore |
|---|---|
| Data | 14/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | NEW `app/bundle/` (`schema.py`, `store.py`, `adapters/lettura.py`, `acc_setup.py`, `acc_results.py`) · NEW `api/sessions.py` · NEW `tests/test_bundle.py`, `test_adattatori.py`, `test_sessions.py`, `tests/fixtures/` · MOD `main.py` `.gitignore` `backend/.env.example` `README.md` `README.it.md` `docs/04-rework-dati.md` |
| Commit | `f93ea57` (F1 formato) · `94ef0d6` (F2–F3 adattatori) · `7894fc2` (F4 archivio e rotte) · `c1a488b` (docs + questo log) |
| Contesto | Dopo L0 (#031, pushato). Edoardo: «procedi con f3», «procedi con la prossima fase» — metodo a fasi. |

**Catalogo messaggi:** «ok push e poi procedi, andiamo per fasi ricordatelo» · «assetto corsa
competizione non è installato sul pc purtroppo ti toccherà cercare online. ora procedi con il
prossimo punto» · «procedi con f3» · «procedi con la prossima fase».

**Vincolo emerso:** **ACC non è installato** su questo PC (c'è AC1; la cartella Documenti è un
residuo del 2021 con la sola `Config`). Su indicazione di Edoardo le strutture sono state ricavate da
**file reali pubblici**; le fixture nel repo hanno quella struttura con valori nostri.

**F1 — formato canonico** (`bundle/schema.py`, `test_bundle.py` **37/37**): `SessionBundle` =
`meta` + `giri[]` + `setup` + `eventi[]` + `canali` + `assunzioni[]`, con `schema_version` e rifiuto
delle versioni non leggibili. La decisione 7 è un vincolo di tipo: un `ValoreSetup` con un numero in
unità reali ma senza `verificato=True` **non è costruibile**, così nessuno può mostrare psi inventati.

**F2 — adattatore Setup** (`adapters/acc_setup.py`, +39 test): legge tutti e **49** i parametri con le
chiavi già usate da `setup_params.py`. Click restano click; **il camber esce in gradi e verificato**
perché è ACC a scriverlo come float; il `toe` no (`toeOutLinear` non è in gradi). Il JSON originale
resta in `Setup.raw`. **Tre assunzioni dichiarate** in `Setup.assunzioni` (ordine di `rideHeight`,
uso di `bumpStopRateUp`, caster da `casterLF`). Provato su **30 setup reali di 30 vetture** (GT3,
GT4, GT2, Challenge): 30/30 letti, 49 parametri ciascuno, slug sempre uguale al catalogo.

**F3 — adattatore Results** (`adapters/acc_results.py`, +42 test): legge **entrambi** gli schemi
(file del gioco: `sessionDef`/`lapTime`/`fuel`/tipo numerico; file del server: `trackName`/`laptime`/
`isValidForBest`). Con più vetture nel file **non sceglie**: `elenca_partecipanti()` e richiesta
esplicita di `car_id`/`player_id`. Provato su **9 file di risultati reali**; l'unico rifiutato è
quello senza giri. Un file reale ha fatto emergere `sessionType: "Q2"` (sessioni numerate dai server),
ora gestito.

**F4 — archivio e rotte** (`bundle/store.py`, `api/sessions.py`, `test_sessions.py` **44/44**):
un file JSON per sessione in `backend/sessions/` (gitignorata), id leggibile validato da regex **e**
dal controllo del percorso risolto (traversal), scrittura atomica. Rotte `POST
/api/sessions/import/setup`, `POST /api/sessions/import/results`, `GET /api/sessions`,
`GET /api/sessions/{id}`, `DELETE /api/sessions/{id}`. **Interruttore `PITWALL_ALLOW_IMPORT`**
(default acceso, da spegnere sul deploy vetrina): queste rotte non passano dal presidio della
demo-mode perché non usano né chiave né rete, e in locale il live è spento.

**Due correzioni a quanto avevo affermato prima, fatte sui dati veri:**
1. **Niente BOM.** I setup sono UTF-8 *senza* BOM e i risultati **UTF-16 LE senza BOM**: il
   riconoscimento della codifica guarda i byte nulli (`adapters/lettura.py`), non un marcatore che non
   c'è. Era il dettaglio che avrebbe fatto fallire l'import al primo file vero.
2. **Il carburante per giro non è gratis.** Nel file del gioco esaminato `fuel` è **costante su tutti
   i giri** di ogni vettura: sembra il carburante di partenza, non il residuo. Il consumo si calcola
   solo se il valore cala davvero, altrimenti il bundle lo **dichiara non calcolabile**. Il consumo
   affidabile arriverà da L3. Da riverificare su un file di sessione in singolo.

**Verifica:**
- `test_bundle` **37/37** · `test_adattatori` **81/81** · `test_sessions` **44/44** ·
  `test_observability` **24/24** · `test_budget` **31/31** (tutti offline).
- **Backend vivo, file veri:** setup importato (49 parametri, 4 in gradi, 2 assunzioni); risultati a
  16 vetture → **409 con l'elenco dei partecipanti**; con `car_id=3` → 22 giri, miglior giro
  101409 ms, 3 assunzioni; `GET /api/sessions` elenca entrambe; `/api/csv/parse` resta 404.
- Nessuna chiamata LLM: spesa invariata ($0,3292 su $1).

**File protetti:** ☑ nessuno toccato (`setup_params.py` solo letto per allineare le chiavi).
**Decisione:** ☑ Mantenuto — committato e pushato il 14/09 su «ok push» (`952fa05..c1a488b`).


## Entry #033 — L2 del REWORK DATI: il motore di analisi (prima versione)

| Campo | Valore |
|---|---|
| Data | 14/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | NEW `app/analisi/` (`__init__.py`, `motore.py`) · NEW `tests/test_analisi.py` · MOD `api/sessions.py` (rotta analisi) · MOD `tests/test_sessions.py` · MOD `README.md` `README.it.md` `docs/04-rework-dati.md` |
| Commit | `f9262a2` (motore + rotta + test) · `ec91fc7` (docs + questo log) |
| Contesto | Dopo L1 (#032, pushato `005c4f1`). Edoardo: «procedi che per oggi sarà l'ultima fase, appena hai finito pusha che poi staccherò». |

**Catalogo messaggi:** «procedi con la prossima fase» · «ok push» · «procedi che per oggi sarà
l'ultima fase, appena hai finito pusha che poi staccherò».

**Modifica:** `analisi/motore.py` con `analizza(bundle) -> ReportAnalisi`, deterministico e senza
LLM. Calcola **ritmo** (miglior giro, giro teorico dalla somma dei settori migliori, lasciato sul
tavolo, media/mediana/media dei 3 migliori), **settori** (migliore, media, dispersione, perdita media
per giro e sul giro migliore), **costanza** (deviazione, coefficiente di variazione, scarto massimo,
giri entro mezzo secondo, giudizio), **degrado** (regressione lineare: ms/giro, R², perdita su 10
giri), **carburante** (solo se il residuo cala davvero) e il **verdetto** ordinato per gravità, con
prova numerica e azione per ogni voce (decisione 3 del 14/09: spietato, ma con la correzione
attaccata). `dati_mancanti` raccoglie le assunzioni dell'import e ciò che i risultati non contengono.

**Due scelte di metodo che tengono onesti i numeri:**
1. **Giri di ritmo.** Un giro oltre il **+10% sul miglior giro** non entra in medie, settori,
   costanza e degrado: è un out lap, un rientro, una bandiera. Resta contato, e il report dichiara
   quanti ne ha esclusi. Prima avevo usato la **mediana** come riferimento: su una sessione corta la
   mediana è già inquinata dagli out lap che si vogliono togliere, e infatti sulla fixture da 4 giri
   dava una deviazione di 67 secondi. Corretto sul miglior giro.
2. **Soglie minime dichiarate:** sotto 3 giri niente costanza, sotto 5 niente degrado, sotto 2 niente
   settori. E un giro teorico più lento del miglior giro reale non viene mostrato: vorrebbe dire
   settori non confrontabili.

**Rotta nuova:** `GET /api/sessions/{id}/analisi` (deterministica, nessuna rete, nessuna spesa).

**Verifica:**
- `test_analisi` **57/57**, con i conti fatti a mano nei commenti del test (giro teorico, medie,
  deviazioni, pendenza del degrado esatta a 200 ms/giro con R² 1).
- `test_sessions` **50/50** (+6 sulla rotta di analisi) · `test_bundle` 37/37 ·
  `test_adattatori` 81/81 · `test_observability` 24/24 · `test_budget` 31/31.
- **Backend vivo, sessione reale da 23 giri:** 20 giri di ritmo, 3 esclusi; miglior giro 100.230;
  costanza 804 ms → «ballerina», solo il 10% dei giri entro mezzo secondo; settore 3 a 6,7 decimi di
  media dal proprio migliore; ritmo in **miglioramento** (−98 ms/giro, R² 0,49) → nessuna voce di
  degrado nel verdetto, come dev'essere.
- Nessuna chiamata LLM: spesa invariata ($0,3292 su $1).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — pushato il 14/09 su indicazione di Edoardo.

## Entry #034 — L3 del REWORK DATI, fasi 1-2: la shared memory di ACC, letta e registrata

| Campo | Valore |
|---|---|
| Data | 15/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | NEW `app/telemetria/` (`strutture.py`, `lettore.py`, `dizionario.py`, `registratore.py`) · NEW `app/api/telemetria.py` · NEW `app/core/riferimenti_acc.py` · NEW `data/acc_riferimenti_vetture.json`, `data/acc_campi_shared_memory.json` · NEW `scripts/estrai_appendici_acc.py`, `scripts/estrai_campi_acc.py` · NEW test `test_telemetria` `test_riferimenti` `test_registratore` + `tests/banco_finto.py` · MOD `app/main.py` `README.md` `README.it.md` `docs/04-rework-dati.md` |
| Commit | `e965dda` (F1 lettore) · `9bf6742` (riferimenti ufficiali) · `bd62a04` (F2 registratore e rotte) · `cb4ab5c` (docs) — pushati il 15/09 |
| Contesto | L3 del rework dati (dopo #033). Sei domande di scope chiuse prima di scrivere codice. |

**Catalogo messaggi:** «leggi la memoria e riprendiamo il lavoro dell'ultima volta» · risposte alle
6 domande di scope (ACC su PS5, AC1 come banco, tutti i parametri, formato e ciclo di vita delegati
a me, analisi per curva dentro L3) · «estraile e ricordati di concentrarti su ACC e non AC1. poi
procedi con il resto».

**Decisioni chiuse in apertura:** ACC sta sulla **PS5** di Edoardo e non sarà mai su questo PC → il
registratore non è verificabile contro ACC, mai. **AC1 solo come banco di prova della tubatura**,
mai come fonte di dati: PitWall è ACC-only e tarare soglie su un'altra fisica falserebbe tutto.
100 Hz, struttura fissata alla 1.8.12, tetto d'archivio configurabile.

**Modifica:**
- **F1** — `strutture.py`: le tre pagine campo per campo dal documento ufficiale Kunos v1.8.12
  (85+87+45 campi; 800 · 1588 · 820 byte). `lettore.py`: aggancio con `OpenFileMappingW`,
  deduplica sui `packetId`, stato del gioco, identità dichiarata dalla pagina statica.
- **Appendici** — due script riproducibili estraggono dal PDF le tabelle per vettura (43 vetture:
  Kunos ID, **carModelId numerico**, offset del bias, coefficienti dei freni, angolo di sterzo, giri
  massimi) e la descrizione ufficiale di **216 campi su 217**. Nuovo modulo `riferimenti_acc.py`.
- **F2** — `dizionario.py`: **211 canali** con nome canonico, unità (con provenienza) e descrizione
  ufficiale. `registratore.py`: thread nel backend, registra solo in stato LIVE, scrive a blocchi
  ogni minuto, consolida in `canali.npz` (due matrici: float32 e int32), tetto configurabile che
  libera i canali grezzi ma **lascia la sessione dichiarata**. Rotte `/api/telemetria/*`.

**Tre correzioni fatte sui fatti, non sulle intenzioni:**
1. **Due offset sbagliati miei** (`brakeTemp`, `clutch`): avevo trascritto la fine del campo invece
   dell'inizio. Il test li ricalcola dal documento e li ha bocciati. Un offset sbagliato non dà
   errore: dà numeri plausibili e falsi.
2. **La difesa sulla dimensione della mappa non funziona.** Windows arrotonda ogni sezione alla
   pagina da 4 KB: mappare 800 byte su una sezione da 712 riesce e la coda legge zeri. Tolta,
   sostituita con l'identità dichiarata nella pagina statica. I test inchiodano il fatto.
3. **Il tetto dell'archivio ordinava per nome**, che ha la risoluzione del secondo: due sessioni
   nello stesso secondo potevano far cancellare i canali di quella sbagliata. Ora ordina per data di
   scrittura.

**Trovato per strada (da decidere):** quattro vetture del catalogo hanno un `acc_car_id` che **non**
è il Kunos ID ufficiale (`bentley_continental_gt3_2015` → `bentley_continental_gt3_2016`,
`lexus_rcf_gt3` → `lexus_rc_f_gt3`, `nissan_gt_r_gt3_2015` → `nissan_gt_r_gt3_2017`,
`reiter_engineering_r_ex_gt3` → `lamborghini_gallardo_rex`). Con quegli slug, il setup importato da
ACC per quelle quattro non si aggancia al catalogo. `cars.json` **non è stato toccato**: serve la
decisione di Edoardo.

**Verifica:**
- `test_telemetria` **97/97** · `test_riferimenti` **56/56** · `test_registratore` **66/66** ·
  test già esistenti invariati: bundle 37/37, adattatori 81/81, analisi 57/57, sessions 50/50,
  observability 24/24, budget 31/31. **Totale 499**, tutti offline.
- Backend vivo: `/` espone `recorder_allowed`, `/api/telemetria/stato` risponde (211 colonne,
  non agganciato perché ACC non c'è), elenco vuoto, id malformato → 400.
- Nessuna chiamata LLM: spesa invariata ($0,3292 su $1).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — pushato il 15/09 («ok push e procedi con la F4»).

## Entry #035 — Vetture allineate agli identificativi ufficiali, archivio fuori da OneDrive, e L3 fase 3 (analisi per curva)

| Campo | Valore |
|---|---|
| Data | 15/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | MOD `data/cars.json` (4 slug) · MOD `bundle/adapters/acc_results.py` · NEW `data/acc_lista_vetture_handbook.json` + `scripts/estrai_lista_vetture_handbook.py` · MOD `core/riferimenti_acc.py` · NEW `analisi/curve.py` · NEW `tests/pista_finta.py`, `tests/test_curve.py` · MOD `telemetria/dizionario.py`, `telemetria/registratore.py`, `api/telemetria.py` · MOD `.env` `.env.example` `README*.md` `docs/04` |
| Commit | `bc5625a` (vetture allineate) · `be90962` (F3 analisi per curva) · `cb4ab5c` (docs) — pushati il 15/09 |
| Contesto | Seguito di #034, stessa sessione: le tre cose lasciate in sospeso + F3 di L3. |

**Catalogo messaggi:** «1 riallinea le vetture sbagliate e fixa il problema in modo da avere tutti i
modelli precisi… 2 l'archivio io volevo che fosse nel desktop sennò spostalo dove ti fa comodo basta
che te mi ricordi dove l'hai spostato. 3 benissimo così, ricordati che ogni cosa deve essere
allineata precisamente sotto ogni aspetto. miriamo alla perfezione assoluta. vai col prossimo passo».

**1 · Vetture allineate.** Corretti i quattro `acc_car_id` che non erano gli identificativi Kunos
(`bentley_continental_gt3_2015`→`..._2016`, `lexus_rcf_gt3`→`lexus_rc_f_gt3`,
`nissan_gt_r_gt3_2015`→`..._2017`, `reiter_engineering_r_ex_gt3`→`lamborghini_gallardo_rex`);
l'`id` interno di PitWall non è stato toccato, quindi foto, ritagli e range di setup restano agganciati.
Le stranezze sono confermate da **tre fonti**: appendice 2 del documento shared memory, ACC Server
Admin Handbook v1.10.2, e l'implementazione di Race Element (che le commenta come «kunos feature»).
Aggiunta la **lista ufficiale completa** delle 54 vetture (handbook), che copre anche le GT3 2023-24 e
la classe GT2: ora **31 su 31** vetture del catalogo hanno il loro `carModelId`, e l'adattatore dei
risultati traduce il numero in vettura (prima restava un numero).

**2 · Archivio spostato.** Da `backend/sessions/` (dentro OneDrive) a
`%LOCALAPPDATA%\PitWall\sessions`, via `PITWALL_SESSIONS_DIR` nel `.env`. Sul Desktop c'è il
collegamento **«PitWall - dati sessioni»**: il Desktop *è* OneDrive, e a 100 Hz la telemetria fa
~290 MB/ora. I tre bundle del 14/09 sono stati spostati e si rivedono tutti.

**3 · L3 fase 3 — analisi per curva** (`analisi/curve.py`): giri ritagliati dalla posizione, canali
reindicizzati sulla distanza (griglia da 2000 punti), curve ricavate dal profilo di velocità mediano,
perdita misurata per tratto contro il miglior tempo del pilota su quel tratto. Per curva e per giro:
punto di frenata, v-min e dove cade, riapertura del gas, trail braking, coasting, decimi persi.
Verdetto ordinato per gravità, ogni voce con prova numerica e azione. Rotta
`GET /api/telemetria/sessioni/{id}/curve`. Aggiunto il canale **`pitwall.tempo_ms`** (l'unico non di
ACC: la shared memory non porta un orologio della registrazione).

**Due difetti trovati dai test, corretti:**
1. **Le curve lunghe a velocità costante sparivano.** Misuravo la profondità del minimo in una
   finestra fissa: dentro un curvone il profilo è piatto, quindi profondità zero e nessuna curva.
   Ora la profondità si misura *camminando* ai due lati finché il profilo non risale (prominenza).
2. **Le rotte nei README erano finite due volte**, per una doppia sostituzione mia su CRLF e LF.

**Verifica:**
- `test_curve` **62/62** (banco: tracciato finto a 3 curve). Su tre giri identici il verdetto è
  **vuoto**; con un errore piazzato solo nella curva 2 il giro perde 700 ms e l'analisi ne attribuisce
  **698,5 a quella curva**, con punti di frenata a 1380 m e 1340 m — i valori impostati.
  La lunghezza del tracciato stimata dalla velocità: **2999,5 m su 3000**.
- `test_adattatori` **86/86** (+5) · `test_riferimenti` **73/73** (+17) ·
  `test_registratore` **69/69** (+3) · `test_telemetria` 97/97 · gli altri invariati.
  **Totale 583**, tutti offline.
- Backend vivo: rotte 200, `/curve` su una registrazione da un giro solo risponde **422 spiegando
  perché**, non 500.
- Nessuna chiamata LLM: spesa invariata ($0,3292 su $1).

**File protetti:** ☑ nessuno toccato (`cars.json` non è nell'elenco dei protetti; `car_setup_ranges.json` non toccato).
**Decisione:** ☑ Mantenuto — pushato il 15/09 («ok push e procedi con la F4»).

## Entry #036 — L3 fase 4: la registrazione diventa una sessione, e il verdetto torna uno solo

| Campo | Valore |
|---|---|
| Data | 15/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | NEW `bundle/adapters/acc_telemetria.py` · NEW `analisi/gomme.py` · MOD `analisi/motore.py` · MOD `api/telemetria.py` `api/sessions.py` `bundle/adapters/__init__.py` · NEW `tests/test_telemetria_bundle.py` · MOD `tests/pista_finta.py` · MOD `README*.md` `docs/04` |
| Commit | `5169c07` (codice) + commit docs successivo — pushati il 16/09 |
| Contesto | Chiude L3. Seguito di #034 e #035 (pushati come `cb4ab5c`). |

**Catalogo messaggi:** «ok push e procedi con la F4».

**Modifica:** una registrazione della shared memory diventa un **session bundle**, cioè
esattamente ciò che l'app già consuma. Da qui in poi non esistono più «le sessioni importate» e
«le registrazioni»: esistono le sessioni, in un archivio solo, con un'analisi sola.
- **Il tempo sul giro lo dice ACC** (`iLastTime`), non il nostro cronometro; `pitwall.tempo_ms` fa
  da controprova e uno scarto oltre mezzo secondo viene dichiarato invece di essere risolto di nascosto.
- **Il consumo vero per giro** c'è finalmente: dai risultati del gioco non si poteva ricavare (`fuel`
  costante per giro, cfr. #032), qui è la differenza del serbatoio fra inizio e fine giro.
- I canali non entrano nel bundle: entra il loro indirizzo.
- `analisi/gomme.py`: pressioni, temperature, freni, consumo pastiglie. **Limite scelto apposta:** la
  finestra di pressione «ottimale» di una GT3 non è pubblicata da ACC, quindi non si giudica contro
  una costante non verificata. Si giudicano solo squilibri e tendenze, che si dimostrano da sé; i
  valori assoluti si riportano sempre.
- `analisi/motore.py` accetta i canali: il report **cresce invece di cambiare**, e curve, gomme e
  freni entrano nello **stesso verdetto** ordinato per gravità. Un solo elenco di priorità.
- Rotte: `POST /api/telemetria/sessioni/{id}/importa`; `GET /api/sessions/{id}/analisi` ora include
  curve e gomme quando i canali esistono ancora.

**Un test che avevo scritto debole, rifatto:** B23 sulla crescita delle pressioni passava comunque
(`... or True`). Ora verifica la pendenza vera (0,12 psi/giro imposti, 0,12 misurati) e ho aggiunto
il caso opposto: con pressioni stabili e bilanciate il verdetto dev'essere **vuoto**.

**Una correzione al banco di prova:** lo squilibrio fra i lati chiesto al generatore non era quello
misurato (0,4 contro 0,5), perché il banco aveva scostamenti per ruota che si sommavano. Ora gli
scostamenti sono uguali fra sinistra e destra: ciò che si chiede è ciò che si misura.

**Verifica:**
- `test_telemetria_bundle` **50/50** · gli altri dieci invariati. **Totale 636**, tutti offline.
- Backend vivo: importazione di una registrazione, `/api/sessions` la elenca con fonte `acc_shm`,
  `/analisi` risponde con curve e gomme; tolti i canali dal disco, la stessa rotta torna al report di
  L2 **dichiarando** che i canali non sono collegati, invece di crollare.
- Nessuna chiamata LLM: spesa invariata ($0,3292 su $1).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» del 16/09 («ok push e prepara le domande di L4»).

---

## Entry #037 — L4: Gigi e le schermate sul bundle, soglie Kunos, demo generata, percorso console

| Campo | Valore |
|---|---|
| Data | 16/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | Backend: `analisi/` (motore, gomme, curve, NEW gigi) · `bundle/` (schema 1.1, store, adattatore telemetria, NEW demo) · NEW `core/riferimenti_fisica.py` + 2 JSON di riferimenti · `api/` (sessions, telemetria, analysis; via session.py) · 🔓 `core/agent.py`, `prompts/` (NEW v5, via v4, chat), `demo_responses.py`, via `demo_data.py` · `telemetria/banco.py` (ex tests/pista_finta) · test NEW analisi_l4, demo, gigi. Frontend: NEW `lib/sessione.tsx`, `lib/formato.ts`, pagina `/sessioni`, `Verdetto`, `GiriSessione`, `AnalisiCurve`, `GommeFreni`; riscritti Dashboard, Telemetria, Setup, Sidebar, Console, api, setup, console, profile, onboarding, tour; cancellati 19 componenti/lib della v1. Docs: `docs/04` §11, `docs/03`, README. |
| Commit | `c93e347` motore e riferimenti · `1ef647a` demo e Gigi · `d953f4f` API · `4953b6f` frontend + commit docs successivo — pushati il 17/09 |
| Contesto | Lotto L4 del rework dati (dopo #036). |

**Catalogo messaggi:**
1. «ok push e prepara le domande di L4» → push di F4 (`5169c07` `7031086`), primo giro di 8 domande.
2. «vanno bene tutte le tue proposte, fai il secondo giro… la ricerca per la fonte kunos… puoi farla direttamente te… verificare fonti alternative come la community… delle chicche però da confermare» → ricerca fatta dal terminale, secondo giro di 8 domande.
3. «1-6 vanno bene… 7 ti propongo di chiedere all'utente da che piattaforma gioca… per console fare qualcosa di più ridotto ma che alla fine funzioni esattamente come quello per pc… 8 proviamo… la cosa importante ora è ristrutturare tutto quanto e verificare che funzioni senza problemi, difetti o sbavature durante le analisi… ok procedi su tutto».
4. (17/09) «ho visto la demo… è un gigantesco passo avanti… riprendiamo» → «ok push per tutti i commit… poi L5 MoTeC, le guide dei tracciati, inc-v2-003, chat di gigi ed il lotto 2».

**Ricerca (fonte primaria trovata):** «Version 1.9 - Physics notes», PDF di Aristotelis (staff Kunos) sul forum ufficiale, 19/04/2023, letto per intero: 26–27 psi indicativi, 70–100 °C al core, assi con pressioni diverse = strumento di setup, 15 °C esterno/interno, bumpstop 20–30 mm. Community (da confermare, fonti e limiti scritti): freni ≤650/450 °C (fonte del 2022, pre-1.9), bagnato 29,5–31 psi, pastiglie 1–4 (fonti in disaccordo su 3 e 4).

**Modifica:** dettaglio completo in `docs/04-rework-dati.md` §11. In sintesi:
- **Motore**: verdetto solo di perdite + `cosa_regge`; gomme giudicate contro la finestra Kunos per quota di tempo fuori (solo asciutto, solo giri utili) con `parametri` per il Setup; assi fuori dal verdetto; degrado dal giro migliore; teorico con motivo; `giri` e `significativo`/`ruote_fuori` decisi nel backend.
- **Difetti trovati e chiusi** (da test, dalla demo e dai dati veri del 14/09): terzo settore perso nelle registrazioni (`iSplit` → `lastSectorTime`); voce di curva 1 con i numeri della curva 12; degrado nascosto dalla «U» dei giri freddi (R² 0,02 → 0,98 sulla demo); «alza la pressione» insieme a «parti più basso»; «Il giro non l'hai messo insieme» per 10 ms; «Costanza solida» rivendicata mentre il ritmo cala; «il ritmo tiene» su uno stint che migliora di 98 ms a giro; azione a 0.8 psi su due ruote con scarti 0.6 e 0.8; consumo da `fuel` in kg; freni della demo a 893 °C.
- **Demo come sessione** generata e calibrata (Monza, 7 curve, 1:47.82 al giro 4), setup vero di ACC; via `demo_data.py` e `/api/session`.
- **Piattaforma**: primo passo del wizard; percorso console con sessione manuale e racconto per fasi, stesso motore.
- **Gigi**: prompt v5 a 5 sezioni (nuova «Correzione di Guida»), contesto = report compresso; risposta dal motore quando il live è spento su sessioni non demo; cache demo riscritta sui numeri del report.
- **Schermate**: selettore di sessione, Dashboard sul verdetto, Telemetria a 3 tab, pagina Sessioni, Setup guidato dal verdetto; nessun conto nel browser.

**Verifica:**
- Backend **751/751** in 14 file, tutti offline (nuovi: analisi_l4 45, demo 38, gigi 32). `tsc --noEmit` 0 errori.
- Backend e frontend vivi: tutte le rotte 200. Nel browser: Dashboard, Telemetria (Giri, Curve con due giri sovrapposti, Gomme e freni), Console (5 sezioni; fonte demo e fonte motore su una sessione vera), Sessioni (percorso console, archivio), Setup (variazione del verdetto applicata 24.2 → 24.8 psi), cambio sessione e persistenza alla ricarica. Nessun errore in console.
- Sbavature viste a schermo e corrette: card KPI senza grafico centrate in verticale, settori oltre il minuto, etichette C1… tagliate, testi del motore in minuscolo, sessione persa alla ricarica in demo.
- Nessuna chiamata LLM: spesa invariata.
- Incidente mio, chiuso: un log del frontend finito sul Desktop (OneDrive) per un percorso relativo sbagliato, cancellato subito; un file `curve.py` vuoto creato alla radice da un comando fallito, cancellato.

**File protetti:** 🔓 sbloccati con «ok procedi su tutto» → `agent.py`, `prompts/*`, `demo_responses.py`, `demo_data.py` (cancellato). Non toccati: `setup_params.py`, `car_setup_ranges.json`, `vision_parser.py`.
**Decisione:** ☑ Mantenuto — verifica a schermo della demo il 17/09 («un gigantesco passo avanti… sta venendo come mi immaginavo») e «ok push per tutti i commit… nell'ordine che mi hai proposto». Prima dei commit rilanciati 751/751 e `tsc` 0. Non verificati a schermo da Edoardo: wizard completo, sessione vera col login Google, pagina Sessioni nel dettaglio.

---

## Entry #038 — L5: MoTeC, il motore su dati veri di ACC (lettore, import, validazione, confronto, export)

| Campo | Valore |
|---|---|
| Data | 17/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | Backend: NEW `app/motec/` (`ld.py` lettore, `ldx.py` giri e nome file, `scrittura.py` scrittore con l'impaginazione di ACC, `esporta.py`) · NEW `bundle/adapters/motec.py` · `bundle/schema.py` 1.2 (`FonteCarburante`, `meta.riferimento`, `meta.ritaglio_i2`) · `bundle/store.py` · `bundle/adapters/acc_telemetria.py` · `analisi/motore.py` (fonte del consumo, giri buttati) · `analisi/gomme.py` (TYRE_TAIR a parte) · `telemetria/registratore.py` (riferimenti fuori dal tetto) · `api/sessions.py` (import e export MoTeC, tempo nelle tracce, cancellazione dei canali convertiti) · `api/telemetria.py` · NEW `scripts/valida_motec.py` · test NEW motec, motec_bundle, motec_export (+ `motec_finto.py`), `test_analisi`. Frontend: `AnalisiCurve` (confronto con altre sessioni, delta), Sessioni (import MoTeC, etichette, «MoTeC ↓»), Dashboard (fonte del consumo), `GommeFreni`, `GiriSessione`, Sidebar, `lib/sessione`, `lib/api`, `lib/formato`. Docs: `docs/04` §12, README. |
| Commit | `2b38080` lettore, scrittore ed export · `c695336` import e motore · `0d5d730` API · `9ac2e0e` frontend · `7d754cc` docs — **pushati il 17/09** con «ok push» |
| Contesto | Lotto L5 del rework dati (dopo #037), primo filone dell'ordine deciso il 17/09: L5 → guide dei tracciati → range di setup + INC-V2-003 → chat di Gigi → Lotto 2; deploy per ultimo. |

**Catalogo messaggi:**
1. «ok push per tutti i commit… poi svolgiamo nell'ordine seguente: L5 MoTeC, le guide dei tracciati, inc-v2-003, chat di gigi ed il lotto 2. il deploy lo svolgeremo appena sarà possibile mettere tutto quanto a runnare online… prima di svolgere inc-v2-003 controlleremo tutti i range di setup da verificare» → push di L4, primo giro di domande su L5.
2. «1 c, 2 claude desktop, 3-4-5 vanno bene» → scopo: validazione del motore + giri di riferimento; lettore nostro; bundle `motec` «riferimento»; canali sul dizionario.
3. «1 va bene poi in caso ricontrolla se manca qualcosa… sennò falla te direttamente la ricerca… 2 va bene. 3 va bene la proposta. 4 perfetto così» → ricerca fatta dal terminale; 17 coppie `.ld`/`.ldx` scaricate (fuori dal repo).
4. «falle direttamente te le ricerche… ok per il download… le piste su console sono identiche» → prompt per Claude Desktop sul Desktop (`PROMPT_L5_stint_MoTeC_ACC.txt`).
5. «ok parti da F1 e mettimi il prompt in un file txt sul desktop» → F1.
6. «ho finito il report di ricerca… 1 va bene anche se troppo approssimativo… 2 va bene. 3 no dobbiamo fare in modo che risulti anche quello… hai tutte le autorizzazioni» → analisi del report, 6 giri BMW + 18 setup scaricati da Drive, precisazioni su posizione e carburante.
7. «1 ok… 3 ok chiarissimo… 1 va bene. 2 se si possono gestire allora certo. 3 aggiungilo. ora procedi con la F2» → consumo con fonte, ritagli i2, export come F5.
8. «ok procedi con la F3» · «ok su tutti e tre, poi procedi con la F4» · «procedi con F5 poi appena finito committiamo ogni cosa».

**Ricerca e file veri** (tutti fuori dal repo, in `%LOCALAPPDATA%\PitWall\motec\riferimenti`): `kyxap/acc-all-in-one` (CC BY-NC-SA 4.0, 16 export nativi ACC 1.9.x, un giro ciascuno) e 6 cartelle Drive di un canale YouTube (BMW M4 GT3, file salvati da MoTeC i2 + setup, nessuna licenza scritta). Nessuno stint ACC gratuito di più giri trovato, né da Claude Code né dal report di Claude Desktop (che conteneva un errore: «hotlap da 150-300 KB», i veri pesano 2-6 MB).

**Modifica:** dettaglio in `docs/04-rework-dati.md` §12. In sintesi:
- **F1 lettore**: formato verificato byte per byte su 22 file; giri dai beacon del `.ldx` (microsecondi, uguali al «Fastest Time» al millesimo); `LAP_BEACON`, `CLUTCH`, `TIME` inutilizzabili; nessun canale di posizione né di carburante.
- **F2 import**: griglia a 100 Hz, nomi canonici solo dove il significato coincide; posizione ricavata dalla velocità e azzerata a ogni traguardo; ritagli di MoTeC i2 validi come un giro se la distanza torna col catalogo (4%); consumo sempre con la fonte (misurato › manuale › setup); `TYRE_TAIR` mai contro la finestra Kunos; rotta `POST /api/sessions/import/motec`.
- **F3 validazione** (`scripts/valida_motec.py`): distanza integrata −0,9% in mediana (sempre corta: traiettoria vs mezzeria), curve ≈ metà del catalogo (il motore vede le frenate), minimi spostati 14-62 m fra file diversi. Tre difetti proposti e applicati su ok: giri incompleti contati «buttati» (14 file su 22, anche le registrazioni della shared memory), «1 giri», tolleranza del ritaglio al 3%.
- **F4 confronto**: tab Curve con giro B da un'altra sessione (stessa vettura e pista), traccia delta B − A, avviso sui ritagli i2; import MoTeC nella pagina Sessioni; riferimenti mai di default; conversioni MoTeC escluse dalle registrazioni da importare.
- **F5 export**: scrittore con l'impaginazione di ACC — **i 16 export nativi riletti e riscritti sono identici byte per byte**, `.ld` e `.ldx`; `GET /api/sessions/{id}/export/motec` (zip) con i canali di ACC nelle loro unità più FUEL, TYRE_CORE_TEMP, LAP_POSITION, STEER_INPUT, GEAR_SM; beacon sui tempi ufficiali dei giri.

**Correzioni a letture mie di F1** (trovate scrivendo F5, corrette): a 86-93 dell'intestazione non c'è un u32 «3 604 535» ma quattro u16 (canali ×2, frequenza massima e minima); l'unità dei canali sta nel campo da 8 byte, non in quello da 12.

**Verifica:**
- Backend **858/858** in 17 file, tutti offline (nuovi: motec 43, motec_bundle 45, motec_export 17; analisi 59). `tsc --noEmit` 0 errori.
- File veri: 22/22 letti, convertiti e analizzati; 16/16 riscritti identici; validazione senza più «buttati».
- Backend e frontend vivi: tutte le pagine 200; 6 file veri importati dalla rotta; nel browser il confronto di Zandvoort (McLaren contro riferimento, delta al traguardo +0,290 s = 1:38.334 − 1:38.042), l'avviso dei ritagli i2 a Spa, il modulo di import; 3 export scaricati dalla rotta e riletti senza avvertenze.
- Nessuna chiamata LLM: spesa invariata. Nessun file protetto toccato.
- **Da sapere:** nell'archivio vero restano le 6 sessioni MoTeC di prova (Zandvoort ×3, Monza BMW, Spa BMW ×2), cancellabili dall'Archivio.

**File protetti:** non toccati.
**Decisione:** ☑ Mantenuto — «procedi con F5 poi appena finito committiamo ogni cosa». **Pushati il 17/09** con «ok push».

---

## Entry #039 — Guide dei tracciati, passo 1: la sezione Tracciati (le guide finalmente a schermo)

| Campo | Valore |
|---|---|
| Data | 18/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | Backend: `core/catalog.py` (guide dei tracciati, `map_verified`, bandierine nel `track_summary`) · `api/catalog.py` (`GET /api/catalog/track/{id}/guida`, bandierine nella scheda) · `core/data/tracks.json` (stato dei layout) · NEW `app/tests/test_tracciati.py`. Frontend: NEW `app/(app)/tracciati/page.tsx` e `tracciati/[id]/page.tsx` · NEW `components/ui/CurvaGuida.tsx` · NEW `lib/assets.ts` (manifest e ritagli condivisi) · `components/ui/SessionBriefing.tsx` (usa il modulo nuovo) · `lib/api.ts` (tipi della guida) · `Sidebar.tsx` + `NavIcons.tsx` (voce Tracciati). Asset: 20 layout non verificati tolti dal repo, `manifest.json` e `ATTRIBUTIONS.md` rigenerati. |
| Commit | non ancora committato |
| Contesto | Apertura del filone «guide dei tracciati» (2° dell'ordine deciso il 17/09), dopo cinque giri di domande. Passo 1 di 4: sezione a schermo → ricerca del blocco B2 → provino di ancoraggio → aggancio in sessione. |

**Catalogo messaggi:**
1. «leggi la memoria e riprendiamo il lavoro di pitwall» → status di rito e piano.
2. Giri di domande 1-5 (26 domande, tutte con proposta motivata). Decisioni chiuse: **prima a schermo poi la raccolta**; sezione **/tracciati** nuova; circuiti senza guida = scheda onesta senza placeholder; `direzione`/lato gomma da verificare a mano sulle 38 curve; blocchi mappa+guida accoppiati; **le guide restano fuori dal contesto LLM**; aggancio agli errori nel tab Curve con **zoom sulla curva sbagliata** e navigazione a frecce fra più curve; abbinamento curva↔guida con **ancoraggio semiautomatico** (fallback: per settore); campo nuovo `progressione` a tre livelli; ordine dei blocchi B2→B6, Nordschleife parcheggiato.
3. «per la ricerca perfetto così almeno non facciamo più il ping pong… 25 perfetto e vai con il passo 1» → **la ricerca delle guide passa da Claude Desktop a me** (fonti concordate, formato invariato, si parte da **Monza sola** per tarare); via libera al passo 1.

**Modifica:**
- **Catalogo**: `track_guide()` legge le guide da `data/tracks_knowledge/` con cache, `has_guide()`/`map_verified()` danno le due bandierine, che entrano sia nell'indice sia nella scheda. La guida si serve su una **rotta sua** (`/api/catalog/track/{id}/guida`): pesa 15-29 KB e non deve gravare su chi chiede il catalogo per popolare un selettore. 404 pulito per i 21 circuiti che non ce l'hanno.
- **Layout**: `tracks.json` ora distingue `verificata` (5, con nome del file Commons e nota) da `da_verificare` (20). I 20 file non verificati sono **usciti dal repo** (spostati in `%LOCALAPPDATA%\PitWall\mappe_da_verificare`, non cancellati: se uno passa il provino si ripesca); `manifest.json` rigenerato con `scrivi_manifest()` e `ATTRIBUTIONS.md` ripulito delle 20 righe orfane.
- **Frontend**: sezione **Tracciati** in sidebar → lista dei 25 con foto, dati e bandierine (filtri Tutti / Con guida / Ancora senza) → scheda con foto, **layout su placca chiara** solo se verificato, dati del catalogo, e la guida per intero: settori, curva per curva apribile, errore del principiante, gomme/freni, track limits, box, meteo, traffico, chicche e **fonti richiudibili**. `CurvaGuida` è un componente a sé perché lo stesso blocco servirà in sessione (passo 4).
- **Igiene**: manifest e ritagli spostati in `lib/assets.ts`, una fetch sola condivisa fra SessionBriefing e Tracciati.

**Motivazione:** le 4 guide e i 5 layout verificati esistevano dal 7-8 settembre e **non li leggeva nessuna riga di UI**. Senza vederli a schermo non si poteva decidere cosa chiedere nei blocchi successivi — da qui l'ordine «prima a schermo, poi la raccolta».

**Risultato osservato:** `/tracciati` mostra 25 circuiti, «4 con la guida curva per curva»; Zolder apre mappa + 10 curve (T1 Eerste: riferimento, insidia, costo dell'errore, sorpasso e difesa, stress gomme/freni/track limits, gara vs qualifica, marcatura «consiglio di mestiere · confidenza alta»); Monza, senza guida, dice che le nozioni non ci sono ancora e non mostra alcun layout.

**Verifica:**
- Backend **891/891** in 18 file (858 di prima + `test_tracciati` 33/33), tutti offline. `tsc --noEmit` 0 errori.
- Pagine a 200: `/ /tracciati /tracciati/zolder /tracciati/monza /sessioni /setup /telemetry /lezioni /crediti /console`. Console del browser pulita dopo il passaggio a `useParams` (la prop `params` in Next 15 è una Promise).
- Nessuna chiamata LLM: spesa invariata. Nessun file protetto toccato.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☐ in attesa della verifica a schermo di Edoardo e di «ok push».

---

## Entry #040 — Guide dei tracciati: Monza, retrofit delle 4 guide vecchie, mappa nel riquadro

| Campo | Valore |
|---|---|
| Data | 18/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | `core/data/tracks_knowledge/` (NEW `monza.json`; `imola`, `spa_francorchamps`, `zandvoort`, `zolder` retrofittate) · `scripts/check_track_knowledge.py` (`progressione` obbligatoria dal blocco 2) · `app/tests/test_tracciati.py` · frontend `CurvaGuida.tsx` (progressione + senso della curva), `lib/api.ts`, `tracciati/[id]/page.tsx` (riquadro del layout) |
| Commit | `ae032c3` + `ecfe603` (Monza) · `5d08e8a` retrofit · `add62ec` riquadro del layout · `557d5c7` docs — **pushati il 18/09** con «ok push» |
| Contesto | Passo 2 del filone guide: prima guida cercata dal terminale, poi retrofit delle quattro del blocco 1. |

**Catalogo messaggi:**
1. «ok push, poi fai la ricerca della guida di monza» → guida di Monza da fonti community, validata, a schermo.
2. «ok push, poi fai il retrofit delle 4 guide vecchie» → `direzione` + `progressione` su 62 curve.
3. «meglio seguire le fonti come coachdave… allineiamo tutto quanto con le fonti più autorevoli senza andare a riscrivere tutto ogni volta… per le sezioni mancanti metteremo sempre le guide seguendo queste fonti» → **regola nuova: le guide community (Coach Dave in testa) sono la fonte primaria**; correzioni a mano solo per errori gravi.
4. «mi dà la mappa di zolder fuori dal riquadro… riduciamo i possibili errori a 0» → riquadro del layout rifatto e verificato **misurando** su tutti e cinque i circuiti con mappa.

**Modifica:**
- **Monza**: 11 curve, `direzione` su tutte (le due guide ACC concordano: 7 destre, 4 sinistre) e `progressione` a tre livelli. Consumo, tempo perso ai box, lato box e dislivello restano `null`: nessuna fonte seria li pubblica.
- **Retrofit**: `direzione` su 71 curve su 73 (restano Imola T19 e Zandvoort T14, le pieghe finali che nessuna fonte qualifica), `progressione` su **tutte e 73**.
- **Due errori scovati dall'incrocio direzione↔lato gomma**, entrambi corretti allineando alla fonte: *Zandvoort T7 Mastersbocht* dichiarava carico sull'anteriore destro su una curva a destra (ribaltato, come La Source); *Spa T3 Raidillon* diceva «anteriore destro in cima» sulla destra della sequenza — riscritto in «anteriore sinistro nel Raidillon, anteriore destro nella sinistra in cima».
- **Imola T1 corretta**: l'avevo letta come destra sulla mappa, Coach Dave la dichiara «left-hand kink». Vince la fonte.
- **Riquadro del layout**: la placca avorio ora si adatta al disegno (`w-fit`) e l'immagine ha **altezza** fissa con larghezza derivata — `zolder_map.svg` dichiara solo il `viewBox`, e con la larghezza in automatico il browser lo riduceva a un quadratino.
- **Validatore**: `progressione` obbligatoria dal blocco 2, con lo stesso trattamento di `direzione` (un rilievo per guida, non uno per curva).

**Motivazione:** il campo `direzione` esisteva per rendere verificabile il lato gomma, che è il dato con cui si leggono le temperature. Su 73 curve ne ha sbattuti fuori due sbagliati.

**Verifica:** validatore da 8 errori a **zero** · `test_tracciati` **38/38** · `tsc --noEmit` 0 · riquadro misurato su spa, imola, zandvoort, zolder, kyalami: immagine dentro la placca e placca dentro la sezione, nessun overflow orizzontale · nessuna chiamata LLM.

**Chiuse su decisione di Edoardo (stessa sessione):**
- *Zandvoort T12 Kumhobocht* → si segue la **fonte ufficiale**: è a sinistra. Allineati il testo
  («curva a destra» → «curva a sinistra») e il lato gomma («lato sinistro» → «lato destro»).
- *Numerazione di Zandvoort riallineata* a quella ufficiale, che è anche quella stampata sulla mappa
  mostrata in pagina: lo **Scheivlak conta come due curve** (6 e 7, la seconda è la discesa verso la
  staccata del Masters, marcata `origine: mestiere`), tutte le successive scalano di uno e **l'ultima
  è l'Arie Luyendijkbocht (14)**. La vecchia T14 («l'immissione sul rettilineo») è stata **eliminata**:
  non è una curva, e quel che diceva vive ora nella progressione dell'ultima. Totale invariato: 14,
  come dichiara il catalogo. Validatore su Zandvoort: **nessun errore**.
- *Imola T19* → **leggera piega a destra**, su indicazione diretta di Edoardo (nessuna fonte scritta la
  qualifica). Con questa il validatore e' **pulito su tutte e cinque le guide**: `direzione` e
  `progressione` su tutte le 73 curve.
- *Quattro campi di pista* (`senso_marcia`, `dislivello_m`, `rettilineo_piu_lungo_m`, `variante_acc`)
  sulle quattro guide del blocco 1: rimandati al prossimo giro, insieme al blocco B2.

**Da sapere:** tre fonti community lette (Full Grip su Zolder e su Imola, SoloX su Zolder) danno la prima curva di Zolder a destra, ma si chiama **Eerste Links** ed è una sinistra; Full Grip dà anche la Rivazza 2 a destra, mentre la Rivazza è doppia sinistra. Coach Dave si è invece dimostrato affidabile su Monza e Imola. Restano da decidere: la numerazione di Zandvoort sfasata rispetto alla mappa ufficiale, e Zandvoort T12 Kumhobocht (il testo dice destra, il sito ufficiale sinistra).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — verificato a schermo e **pushato il 18/09** con «ok push».

---

## Entry #041 — Foto del circuito stirata nella scheda del tracciato

| Campo | Valore |
|---|---|
| Data | 18/09/2026 |
| Agente dev | Claude Code (claude-opus-5) |
| Area | `frontend/src/app/(app)/tracciati/[id]/page.tsx` |
| Commit | vedi sotto |
| Contesto | Segnalazione di Edoardo: «la foto di imola appare stretchata (foto del circuito reale e non track map)». |

**Catalogo messaggi:**
1. «la foto di imola appare stretchata… fixala» → diagnosi misurata e correzione.

**Modifica:** nella scheda del circuito la foto non usa piu' le percentuali di `crops.json`
(larghezza e altezza indipendenti) ma **`object-cover`**, con il ritaglio scelto a mano conservato
come punto d'interesse in `object-position` (funzione `puntoDiInteresse`). La lista dei tracciati e
le card di sessione restano col ritaglio esatto: li' il riquadro ha davvero le proporzioni della
banda 540×280 su cui i ritagli sono stati scelti.

**Motivazione:** la foto sta in una colonna flex accanto al testo, e il flex **stira il riquadro**
all'altezza della colonna (347 px invece di 197). Le percentuali del ritaglio si adeguavano al
riquadro deformato e deformavano l'immagine: Imola misurava rapporto naturale **1,500** contro
**0,849** renderizzato. Non era un difetto del file, e non riguardava solo Imola: capitava su ogni
circuito con il testo piu' alto della foto.

**Risultato osservato:** Imola `object-fit: cover @ 50% 61.1%`, immagine proporzionata; idem Monza e
Spa. Nella lista `/tracciati`: **23 foto caricate, zero stirate** (controllate tutte).

**Verifica:** `tsc --noEmit` 0 errori · rapporti misurati nel browser, non giudicati a occhio.
**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push».

---

## Entry #042 — Guide dei tracciati, blocco B2: campi di pista, Silverstone, Nürburgring GP, Barcelona e le loro mappe

| Campo | Valore |
|---|---|
| Data | 23/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `core/data/tracks_knowledge/` (NEW `silverstone.json`, `nurburgring_gp.json`, `barcelona_catalunya.json`; campi di pista su `imola`, `monza`, `spa_francorchamps`, `zandvoort`, `zolder`) · `core/data/tracks.json` (4 mappe verificate, `corners_confidence`, nota di Barcelona, descrizione di Silverstone) · `scripts/check_track_knowledge.py` (`fonti_campi_pista`) · `scripts/maps.json` + `scripts/maps_choice.json` · `app/tests/test_tracciati.py` · frontend `lib/api.ts`, `tracciati/[id]/page.tsx` (sezione «La pista») |
| Commit | vedi sotto |
| Contesto | Ripresa dal blocco B2 del filone guide (ordine del 17/09). Ricerca fatta dal terminale, fonte primaria Coach Dave (regola del 18/09). |

**Catalogo messaggi:**
1. «leggi la memoria e riprendiamo il lavoro di pitwall» → status di rito e piano.
2. «ok procedi, prima i 4 campi poi il B2» → ricerca dei quattro campi di pista sulle guide del blocco 1.
3. «1 sì, 2 segnala fonte singola, 3 null, 4 dopo il B2» → blocco `fonti_campi_pista` anche su Monza; le fonti singole restano a vista nel validatore; `lato_box` senza fonte a `null`; la numerazione di Spa secondo Coach Dave rimandata a dopo il B2.
4. «ho fatto con l'esportazione del json ora puoi ricominciare» → mappe del B2 applicate e confrontate con le guide.
5. «1 va bene, 2 va bene, 3 sì, 4 va bene, giusto, correggiamola» → Nürburgring a 15 curve con nota sulla mappa; nomi di Coach Dave più la tabella dei nomi attuali; tre nomi di Barcelona dalla mappa; sezione «La pista» nella scheda; `corners_confidence` ad «alta» dove la guida conferma; descrizione di Silverstone corretta.

**Modifica:**
- **Quattro campi di pista** (`senso_marcia`, `dislivello_m`, `rettilineo_piu_lungo_m`, `variante_acc`) sulle quattro guide del blocco 1, e blocco nuovo **`fonti_campi_pista`** su tutte le guide: per ogni campo il link, oppure una nota che dice perché manca, e `fonte_singola` quando c'è un solo riscontro. Dove due fonti non concordano il valore e' `null` con tutti e due i numeri in nota (rettilineo di Zandvoort 690/850 m; dislivello e rettilineo di Zolder). Dove Wikipedia e un sito minore non concordano vince Wikipedia, che per i dati di pista e' la fonte di riferimento (dislivello di Zandvoort 8,9 m contro 18).
- **`lato_box`** di Spa e Imola a `null` («da vedere in gioco»); **fonte della lunghezza** aggiunta a Zandvoort e Zolder.
- **Validatore**: legge `fonti_campi_pista`. Un valore senza fonte né nota è da controllare, un link che non è un link è un errore, una fonte singola resta nell'elenco «da controllare a occhio».
- **Tre guide nuove**, stesso schema di Monza (`direzione` e `progressione` su ogni curva):
  - *Silverstone*: 18 curve, numerazione moderna (T1 = Abbey). Coach Dave + Driver61; Hangar Straight 770 m dal sito ufficiale.
  - *Nürburgring GP*: 15 curve, GP-Strecke con Mercedes-Arena. Coach Dave; dislivello 55 m (Wikipedia tedesca, concorda trackdaytickets con 56).
  - *Barcelona*: 16 curve. **Chiuso il dubbio del catalogo**: ACC usa il Grand Prix Circuit 2007-2020 con la chicane finale (4,655 km), confermato da Coach Dave, da Wikipedia e dalla mappa. Rettilineo dei box 1047 m.
  - Full Grip scartato per le curve (sbaglia sensi, marce e nomi a Silverstone e al Nürburgring): se ne tengono solo i tempi di riferimento, come per Monza, scrivendo il limite nella nota.
- **Mappe del B2** scelte a occhio da Edoardo nel provino e applicate: `Monza-2021.svg`, `Silverstone Circuit 2020.png`, `Circuit Nürburgring-2013-GP.svg`, `Circuit Catalunya 2007.svg`. `tracks.json` le segna «verificata»; `maps_choice.json` tiene ora i due blocchi (9 scelte); `maps.json` aggiornato per i crediti. Il provino e' stato costruito con candidati cercati dal terminale, con le trappole di confronto marcate (Silverstone 2004-09, Nürburgring 24h senza Arena, Barcelona 2021 e 2023).
- **Confronto mappe ↔ guide**: Monza 11 su 11; Silverstone senza numeri, nomi concordi; Barcelona 16 su 16. **Nürburgring**: la mappa numera 16 curve (conta quattro curve nella Mercedes-Arena, Coach Dave tre) e usa i nomi degli sponsor attuali. Deciso di tenere 15 (Coach Dave, Wikipedia inglese, catalogo) e di spiegarlo in due chicche: la numerazione della mappa (dopo l'Arena il numero sulla mappa e' quello della guida più uno) e la tabella dei nomi vecchi e attuali.
- **Nomi dalla mappa** dove la guida aveva `null`: Barcelona T12 Banc de Sabadell, T13 Europcar, T16 New Holland; Nürburgring T12 Falkenbogen.
- **Catalogo**: `corners_confidence` ad «alta» su Spa, Imola, Zolder, Silverstone, Nürburgring GP e Barcelona, cioè dove la guida ha `curve_confermate: true` (la scheda non scrive più «da verificare» accanto al numero di curve); nota di Barcelona riscritta; descrizione di Silverstone corretta («nel finale il tornante di Luffield» → «a metà giro, la lunga Luffield»: la Luffield e' la T7 e non e' un tornante).
- **Scheda del circuito**: sezione nuova **«La pista»** subito dopo il layout (senso di marcia, dislivello, rettilineo più lungo, variante in ACC). I valori `null` non si disegnano, e una riga in fondo dice quali valori vengono da una fonte singola.
- **Test**: in `test_tracciati` l'esempio di «circuito senza guida» passa da Silverstone alla Nordschleife (l'ultima dell'ordine); i layout verificati attesi passano da 5 a 9; il caso «guida sì, mappa no» (Monza, che ora ha la mappa) e' diventato «mappa sì, guida no» su Kyalami.

**Motivazione:** chiudere il blocco B2 seguendo le regole del 18/09: fonte community per la guida, fonti ufficiali per i dati di pista, e ogni contraddizione con la mappa o col nome della curva segnalata invece che copiata.

**Risultato osservato:** guide **8/25**, mappe verificate **9/25**. Le tre schede nuove e la sezione «La pista» verificate a schermo (Spa con la riga della fonte singola, Silverstone senza «da verificare» e con la descrizione corretta, Nürburgring con le due chicche e la T12 Falkenbogen).

**Verifica:** validatore **senza errori**, 5 fonti singole a vista (dislivello di Barcelona, rettilineo di Monza e di Spa, senso di marcia di Nürburgring e Zolder) · **908/908** test in 18 file (`test_tracciati` 38 → **50**: le regole di contenuto si applicano a ogni guida in più) · `tsc --noEmit` 0 · backend riavviato a mano dopo le modifiche al catalogo · nessuna chiamata LLM.

**Da sapere:**
- Coach Dave numera Spa diversamente dalla nostra guida (Eau Rouge/Raidillon 2-4, Les Combes 5-7, Bus Stop 18-19): rimandato a dopo il B2, su decisione di Edoardo.
- Le `commons_category` scritte in `tracks.json` restano quelle vecchie e inesistenti (`Category:Maps of ...`), come nel blocco 1: quelle vere si chiamano `Category:<circuito> circuit maps`.
- Il provino delle mappe dice ancora «Claude Desktop» nei testi fissi: da quando la ricerca la faccio dal terminale non e' più vero.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» (commit `d952964` campi di pista · `f890f28` blocco B2 e mappe · `ead585c` sezione La pista · docs).

---

## Entry #043 — Guide dei tracciati, blocco B3: Misano, Brands Hatch, Hungaroring, Paul Ricard e le loro mappe

| Campo | Valore |
|---|---|
| Data | 24/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `core/data/tracks_knowledge/` (NEW `misano.json`, `brands_hatch.json`, `hungaroring.json`, `paul_ricard.json`) · `core/data/tracks.json` (4 mappe verificate, `corners_confidence`, record e descrizione di Paul Ricard) · `scripts/maps.json` + `scripts/maps_choice.json` · `app/tests/test_tracciati.py` · README, README.it, `docs/03` |
| Commit | vedi sotto |
| Contesto | Ripresa dal blocco B3 del filone guide (ordine del 17/09). Ricerca dal terminale, fonte primaria Coach Dave (regola del 18/09). |

**Catalogo messaggi:**
1. «leggi la memoria e dimmi lo status attuale di pitwall» → status di rito.
2. «partiamo dal blocco B3» → verifica dei layout: tre concordano col catalogo, Paul Ricard no (Wikipedia mette il record GT3 sotto il layout senza chicane); Coach Dave non ha una guida di Paul Ricard; due sospetti errori di Coach Dave (Misano, Hungaroring).
3. «1 sì c'è la chicane, 2 fonti secondarie, 3 sì, 4 sì» → Paul Ricard con la chicane del Mistral; guida da fonti secondarie con confidence dichiarata; correzioni solo con mappa numerata + seconda fonte; record di Paul Ricard a null con nota.
4. «1 sul rettilineo principale appena si esce da curva 15 [...] 2 [...] sembra piatta. 3 correggi come per silverstone» → ingresso box di Paul Ricard visto in gioco; dislivello a null; descrizione del catalogo corretta.
5. «ho esportato il json, puoi procedere» → mappe applicate, confronto con le guide, test, verifica a schermo.

**Modifica:**
- **Quattro guide nuove**, schema del B2 (`direzione` e `progressione` su ogni curva, campi di pista con `fonti_campi_pista`):
  - *Misano*: 16 curve, GP 2008-oggi in senso orario. Coach Dave. Nel suo riassunto iniziale Coach Dave scrive «6 destre e 10 sinistre»; la sua descrizione curva per curva e la mappa numerata danno il contrario (10 destre, 6 sinistre): vale la descrizione, scritto in nota. Sensi di T4 (Rio, doppia destra) e T7 dalla mappa. Rettilineo 565 m (Coach Dave + trackdaytickets).
  - *Brands Hatch*: 9 curve, Grand Prix Circuit 2003-oggi (non l'Indy). Coach Dave, sensi confermati da Wikipedia italiana e dalla mappa numerata. Dislivello 32 m da Wikipedia tedesca (fonte singola, a vista).
  - *Hungaroring*: 14 curve, GP 2003-oggi. Coach Dave, riscontro Driver61 (che numera 16). **Il dubbio sulla T13 era mio ed era sbagliato**: la mappa numerata la da' a sinistra, come Coach Dave. Rettilineo 908 m (Wikipedia inglese + trackdaytickets; la tedesca dice 788,9, in nota); dislivello 36 m (Wikipedia tedesca; trackdaytickets 33).
  - *Paul Ricard*: 15 curve, layout 1C-V2 con la chicane Montréal sul Mistral (confermata in gioco da Edoardo). Coach Dave non ha la guida: contenuto dalle guide GT3 di RaceControl e della wiki di Le Mans Ultimate, solo dove concordano con la mappa numerata di Commons, confidence «media» (T12-T14 «bassa»). La wiki LMU da' la T1 a destra, mappa e RaceControl a sinistra; RaceControl dalla Beausset in poi sposta i nomi di una curva: parti scartate e scritte in nota. Tempo di riferimento da Track Titan (una vettura, dichiarato). Ingresso box: in ACC e' quello pre-2019, sul rettilineo appena usciti dal Pont, sulla destra, segnato dalla striscia bianca (Edoardo in gioco); `lato_box` = destra. Dislivello a null (Wikipedia 33 m, trackdaytickets 8 m, pista piatta in gioco).
  - Full Grip usato solo per i tempi, come nel B2 (la sua pagina di Paul Ricard mostra Monza, quella di Brands Hatch conta 12 curve, e da' la Quercia di Misano a destra).
  - Tolte prima della consegna due frasi mie senza fonte (una chicca sulla mappa di Misano, una sugli onboard di Brands Hatch) e un'affermazione sulla T12 dell'Hungaroring che la fonte non sostiene.
- **Mappe del B3** scelte a occhio da Edoardo nel provino e applicate: `Misano World Circuit.svg`, `Brands Hatch.svg`, `Hungaroring.svg`, `Le Castellet circuit map Formula One 2018 without corner names English 29 06 2021.svg` (la 2018 perche' ha l'ingresso box sul rettilineo, come ACC). Provino costruito con candidati cercati dal terminale e trappole marcate (Misano 2001-2006 e 2007, Brands Hatch Indy e 1999-2002, Hungaroring 1986-1988 e 1989-2002, Paul Ricard senza chicane e storici). `maps_choice.json` ora ha tre blocchi (13 scelte); `maps.json` aggiornato per i crediti.
- **Confronto mappe ↔ guide**: tutte e quattro le mappe numerano le curve come le guide, con gli stessi sensi.
- **Catalogo**: `corners_confidence` ad «alta» su Misano, Brands Hatch e Hungaroring; Paul Ricard: `lap_record_real` a null con `lap_record_note` (il 1:39.914 era Rosberg in F1 nel 1985 sul tracciato originale) e descrizione corretta («i suoi 15 curvoni» → «le sue 15 curve»).
- **Test**: in `test_tracciati` i layout verificati attesi passano da 9 a 13.
- **Docs**: README e README.it a 924 test (`tracciati` 66); `docs/03` a 12 guide su 25 e — debito trovato — a 18 file e 924 test (diceva ancora 14 file e 751 test, fermo a prima di L5).

**Motivazione:** chiudere il blocco B3 con le regole del 18/09 e del 23/09, verificando ogni senso di curva sulla mappa numerata prima di scriverlo.

**Risultato osservato:** guide **12/25**, mappe verificate **13/25**. Le quattro schede verificate a schermo (layout sulla placca, sezione «La pista» con i valori e la riga «fonte singola» su Misano e Brands Hatch, «Record reale» assente su Paul Ricard, ingresso box a schermo). Accesso demo impostato solo nella sessione della scheda di prova, senza il pulsante demo, per non cancellare il profilo in localStorage.

**Verifica:** validatore **senza errori** su 12 guide, fonti singole a vista (dislivello di Brands Hatch e Misano, piu' le 5 del B2) · **924/924** test in 18 file (`test_tracciati` 50 → **66**) · `tsc --noEmit` 0 · rotte `/ /tracciati /crediti /login` 200 · backend riavviato a mano dopo le modifiche al catalogo · nessuna chiamata LLM.

**Da sapere:**
- La mappa dell'Hungaroring colora il tracciato a tratti: sono i settori del disegno, non quelli di ACC.
- Resta rimandata la numerazione di Spa secondo Coach Dave; il provino dice ancora «Claude Desktop» nei testi fissi (nelle note delle scelte del B3 l'ho corretto a mano in `maps_choice.json`).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» (commit `0497a4a` blocco B3 e mappe · docs).

---

## Entry #044 — Guide dei tracciati, blocco B4: Suzuka, la mappa del Red Bull Ring e il catalogo

| Campo | Valore |
|---|---|
| Data | 25/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `core/data/tracks_knowledge/` (NEW `suzuka.json`) · `core/data/tracks.json` (Suzuka: curve confermate, record e descrizione; Kyalami: lunghezza confermata; Red Bull Ring: mappa verificata e nota sul layout) · `scripts/maps.json` + `scripts/maps_choice.json` · `app/tests/test_tracciati.py` · README, README.it, `docs/03` |
| Commit | vedi sotto |
| Contesto | Ripresa dal blocco B4 del filone guide (kyalami, red_bull_ring, mount_panorama, suzuka). Coach Dave non ha guide ACC per nessuno dei quattro: il blocco e' stato diviso. |

**Catalogo messaggi:**
1. «passiamo a pitwall» → status di rito.
2. «riprendiamo con il B4» → Coach Dave non copre il B4 (solo due guide iRacing di evento, senza curve); proposta di regola per le fonti secondarie.
3. «1 sì usa chrome, 2 sì, 3 sì» → fonti lette anche dal Chrome di Edoardo; B4 insieme; controlli in gioco raccolti in una lista.
4. «va bene la tua proposta, parti con suzuka» → trovata una sola guida ACC seria (SimRacingSetup, Suzuka): B4 diviso. Ora Suzuka, provino delle tre mappe e verifica del catalogo; Kyalami, Red Bull Ring e Bathurst parcheggiati finche' non c'e' una fonte.
5. «ho esportato il json, puoi procedere» → nell'export c'e' solo il Red Bull Ring; chiesto se Suzuka e Bathurst erano scoperti apposta.
6. «nessuna delle dei due circuiti aveva della mappe adatte» → applicata la sola mappa del Red Bull Ring.
7. «1 non ce ne erano di adatte [...] 2 sì a entrambe, 3 confermo tutto, al rb ring non ci sta la chicane [...] a suzuka l'entrata dei box sta all'uscita dell'ultima chicane, nell'ultima curva» → record e descrizione di Suzuka corretti, scelte confermate, ingresso box e layout del Red Bull Ring annotati.

**Fonti del B4 (verificate il 25/09):**
- SimRacingSetup ha guide ACC solo per Spa, Valencia, Suzuka e Imola; SoloX mostra una pagina vuota anche in Chrome (non aggirata); Full Grip sbaglia la numerazione anche qui (Kyalami: T1 = Crowthorne; Suzuka: 10 = Hairpin e chicane invertita); il blog di Track Titan su Kyalami e' generico e sbagliato (Sunset e Mineshaft «tornanti»). Track Titan (app) resta buono per tempi, marce e punti di frenata, a segmenti senza numeri.
- Per Kyalami, Red Bull Ring e Bathurst nessuna fonte spiega come si guidano in GT3: guide parcheggiate.

**Modifica:**
- **Guida nuova `suzuka.json`**, schema del B2: 18 curve, Grand Prix Circuit 2003-oggi. Numerazione e sensi dalla mappa numerata di Commons (`Suzuka circuit map--2005.svg`), che conta 10 destre e 8 sinistre come la guida ufficiale del circuito in PDF (luglio 2026). Contenuto curva per curva dalla guida ACC di SimRacingSetup (Ferrari 296 GT3), marce e frenate riscontrate su Track Titan con tre GT3 (Ferrari 296, Porsche 992, McLaren 720S). SimRacingSetup dopo l'Hairpin sfasa i numeri (chiama 13 la 200R e unisce le due parti della Spoon): testo riassegnato alle curve giuste e scritto in nota. Nomi ufficiali di oggi con il nome storico fra parentesi (NIPPO Corner ex Dunlop, NISSIN Brake Hairpin, Astemo Chicane ex Casio Triangle). Confidence «media», «bassa» sulla T10. Campi di pista: senso di marcia null (e' un otto: meta' giro orario, meta' antiorario); dislivello null (nessuna fonte); rettilineo piu' lungo 1000 m dalla guida ufficiale (rettilineo ovest; Wikipedia 1,2 km, in nota; fonte singola a vista). Ingresso box all'uscita della Astemo Chicane, dentro la Last Curve (visto in gioco da Edoardo); lato e tempo perso null.
- **Catalogo**: Suzuka `corners_confidence` ad «alta»; `lap_record_real` a null con nota (il 2:03.611 non e' confermato da nessuna fonte; il record ufficiale e' della F1, 1:30.965); descrizione corretta («Ospita dal 2018 una 10 Ore» → «Ha ospitato la 10 Ore [...] nel 2018 e nel 2019»). Kyalami: tolto `length_confidence: da_verificare` (il sito ufficiale da' 4,522 km, 16 curve, senso antiorario; Wikipedia 4,529). Red Bull Ring: mappa verificata e `corners_note` (layout auto identico alla F1, senza la chicane delle moto, verificato in gioco da Edoardo).
- **Provino delle mappe del B4** (Suzuka, Red Bull Ring, Bathurst: 39 candidati, trappole marcate). Scelto e applicato solo il Red Bull Ring: `Spielberg bare map numbers contextless 2016 onwards.svg`. Suzuka e Bathurst restano **senza mappa** per scelta di Edoardo: Suzuka aveva solo mappe coi settori della F1, Bathurst solo mappe vecchie.
- **Test**: in `test_tracciati` i layout verificati attesi passano da 13 a 14.
- **Docs**: README e README.it a 928 test (`tracciati` 70); `docs/03` a 13 guide su 25 e 928 test.

**Motivazione:** chiudere del B4 la parte che ha fonti serie, senza scrivere guide «di mestiere» dove nessuna fonte spiega come si guida.

**Risultato osservato:** guide **13/25**, mappe verificate **14/25**. Scheda di Suzuka verificata a schermo (settori, 18 curve con sensi e marce, riga «fonte singola» sul rettilineo, box, traffico, chicche); dopo il riavvio del backend il record reale non compare piu' e la descrizione e' corretta. Scheda del Red Bull Ring con la mappa sulla placca (10 curve numerate, corsia box). La mappa compare in /crediti.

**Verifica:** validatore **senza errori** su 13 guide · **928/928** test in 18 file (`test_tracciati` 66 → **70**) · `tsc --noEmit` 0 · rotte `/ /tracciati /tracciati/suzuka /tracciati/red_bull_ring /crediti /login` 200 · backend riavviato a mano dopo le modifiche al catalogo · nessuna chiamata LLM.

**Da sapere:**
- Restano da fare, quando ci sara' una fonte: le guide di Kyalami, Red Bull Ring e Bathurst, e le mappe di Suzuka e Bathurst. A Bathurst due mappe numerate non danno lo stesso nome alle stesse curve (Griffins Bend e Quarry): da risolvere con la guida.
- La numerazione di Spa secondo Coach Dave resta rimandata; il provino dice ancora «Claude Desktop» nei testi fissi (nella nota della scelta del Red Bull Ring l'ho corretto a mano in `maps_choice.json`).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» (commit `68751dc` guida di Suzuka, mappa del Red Bull Ring e catalogo · docs).

---

## Entry #045 — Ancoraggio delle curve (Monza, Zandvoort) e sensi corretti nelle guide di Zandvoort e Imola

| Campo | Valore |
|---|---|
| Data | 28/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | NEW `core/ancore.py` · NEW `analisi/eventi_curva.py` · NEW `core/data/tracks_anchors/` (`monza.json`, `zandvoort.json`) · NEW `scripts/build_anchors_proof.py`, `apply_anchors.py`, `verifica_ancore.py` · `scripts/check_track_knowledge.py` · `core/data/tracks_knowledge/zandvoort.json`, `imola.json` · `app/tests/test_tracciati.py` · README, README.it, `docs/03` |
| Commit | vedi sotto |
| Contesto | Passo 3 del filone guide: sapere, per ogni curva della guida, dove sta sul giro e sulla mappa, per agganciare poi la guida al verdetto del motore (che trova le curve dai minimi di velocità e le numera da sé). Scope chiuso il 25/09, corretto il 28/09 dopo il primo provino. |

**Catalogo messaggi:**
1. «riprendiamo pitwall» → status di rito; misurato il motore sulle 6 sessioni MoTeC: un solo giro completo ciascuna, su un giro solo il motore trova 10, 8 o 9 curve a Zandvoort, 6 minimi per 11 curve a Monza. Quattro domande.
2. «1 va bene, 2 va bene, 3 va bene, 4 giusto, 5 a posto così. ok procedi» → provino v1 costruito; trovati sei sensi ribaltati nella guida di Zandvoort (telemetria e mappa numerata d'accordo, guida no).
3. «le curve non devono essere rilevate solo dalla forza g [...] dovrebbero essere rilevate anche dagli input di frenata [...] cerca queste informazioni finché non sei CERTO» → ricerca (metodo di rilevamento, segno di G_LAT, fonti scritte sui sensi di Zandvoort, controllo di Imola e Zolder); correzioni del primo provino salvate; scoperto che l'aggancio automatico del clic aveva spostato un suo input.
4. «1 sì, 2 sì esatto la curva va indicata all'inizio, gli altri input arrivano in seguito [...] 5 t1 di imola è a destra» → guide corrette, rilevamento rifatto con la frenata, ancore a tre fasi, provino v2 che riparte dalle sue correzioni.
5. «1 sì ±1%, 2 sì solo informativo, 3 li controllo io» → tolleranza della verifica ±1%, controllo sul tratto del motore solo informativo.
6. «non riesco a selezionarti i punti sulla track map che non riesco a zoommare» → zoom e spostamento sulla mappa, mappa a tutto schermo.
7. «ho esportato entrambe e con le ancore che ho segnato rappresentano l'inizio della curva, procedi» → ancore applicate.

**Ricerca (28/09):**
- Fasi di una curva: frenata in rettilineo → inserimento → apice → uscita (Driver61, «The 6 phases of a corner»).
- Rilevamento: metodo documentato di assetto-mcp (`docs/INTERNALS.md`, PR #56). Curve dal carico laterale, due tratti dello stesso senso uniti se il carico fra loro resta sopra il 70% della soglia; punto di frenata camminando dall'apice all'uscita della curva precedente, primo tratto di freno che toglie almeno un quarto della velocità tolta dal più pesante.
- Segno di `motec.G_LAT`: Kunos non lo documenta (né il blog MoTeC né la documentazione della shared memory). Verificato sui dati di Monza, Zandvoort e Spa con curve dal senso indiscusso (Tarzan, La Source, Raidillon, Parabolica a destra; Eau Rouge a sinistra): **negativo = destra**, senza eccezioni.
- Sensi di Zandvoort: Mercedes-AMG F1 (T5 sinistra, T9 destra, T11-12 destra-sinistra, T13 destra), F1 Chronicle (T5 sinistra, Hans Ernst destra-sinistra), FanAmp (Hans Ernst destra-sinistra, T13 destra; dà la T5 a destra, contraddetta da tutto il resto), All Fast Things (T10 sinistra, Kumho destra). Il sito ufficiale conferma i nomi 5 Slotemaker e 6-7 Scheivlak ma non scrive i sensi.
- Controllo delle altre guide sistemate prima della regola «sensi dalla mappa numerata»: Monza e Spa tornano con la telemetria (Spa: 17 curve abbinate su 19, nessun contrasto), Imola e Zolder con le mappe numerate.

**Modifica:**
- **Guide.** Zandvoort: sensi di T5 (sinistra), T9 (destra), T10 (sinistra), T11 (destra), T12 (sinistra), T13 (destra); lato gomma e nota della T13 (la correzione del 18/09 citava il sito ufficiale, che il senso non lo scrive); geometria della Hans Ernst (destra a 45 gradi e tornante a sinistra, non «doppio tornantino»); nome della T10 a null («Renaultbocht» è il vecchio nome della T9); T10 «lega la 9», non la 8; quattro fonti aggiunte. Imola: T1 a destra (verificata in gioco da Edoardo; Coach Dave la chiama «left-hand kink», contrasto scritto nella nota). Diff limitati alle righe cambiate.
- **Ancore (schema 2).** Per ogni curva della guida: **inizio** (punto di frenata, o inserimento se la curva è in pieno: è il clic di Edoardo), **apice**, **uscita** sul giro (0-1, come `normalizedCarPosition`) e **punto sulla mappa verificata** (frazioni di larghezza e altezza). Un file per pista in `data/tracks_anchors/`, legato a sessione, guida e mappa: se la guida viene rinumerata o la mappa cambia, il validatore lo respinge.
- **Rilevamento** (`analisi/eventi_curva.py`): curve dal carico laterale e frenata attribuita come sopra; proposta automatica che abbina in ordine le curve della guida a quelle del giro premiando il senso giusto, con avviso quando il senso misurato contraddice la guida. Sulle 25 curve l'inizio proposto cade in media a 0,2% di giro dai clic di Edoardo, al massimo 0,45%.
- **Provino** (`build_anchors_proof.py`): profilo di velocità, pedali, carico laterale e marcia del giro di origine, altre sessioni in grigio; clic = inizio **esatto** (tolto l'aggancio automatico del primo provino, che aveva spostato la T8 di Zandvoort), Maiusc+clic = apice, Alt+clic = uscita; mappa con zoom a rotella, trascinamento e schermo intero; bozze in `%LOCALAPPDATA%\PitWall\ancore_bozze` caricate sopra la proposta; «Esporta ancore» solo a lavoro completo (il pulsante dice cosa manca), «Esporta bozza» sempre.
- **Applicazione e verifica**: `apply_anchors.py` valida e scrive (rifiuta le bozze); `verifica_ancore.py` riporta gli apici sulle altre sessioni della pista: tolleranza **±1%** (lo stesso punto si sposta di ~0,6% fra sessioni); il confronto col tratto del motore è **solo informativo** (su un giro solo il motore divide Gerlach e Hans Ernst in modo diverso da una sessione all'altra).
- **Validatore**: `check_track_knowledge.py` controlla anche le ancore.
- **Test** (`test_tracciati` 70 → 98): validatore delle ancore (ogni regola rotta una alla volta, motivo verificato), rilevamento su un giro sintetico (frenata, curva in pieno, chicane, un tocco di freno a metà rettilineo che non diventa staccata), proposta e verifica, ancore a disco conformi, sensi di Zandvoort e T1 di Imola bloccati.

**Motivazione:** il primo provino confondeva le curve nelle grandi staccate (guardava solo il carico laterale) e salvava l'apice, mentre per chi guida la curva comincia dove si frena. E una guida col senso sbagliato dà una lettura ribaltata delle gomme: a Zandvoort erano sei curve.

**Risultato osservato:** Monza 11 ancore e Zandvoort 14, confermate da Edoardo nel provino (sessioni `20260917-145307-monza_bmw_m4_gt3-bcf3` e `20260917-145306-zandvoort_mclaren_720s_gt3_evo-5f1e`). Punti sulla mappa controllati sulle mappe numerate: ognuno accanto al numero della sua curva. Zandvoort regge **14/14** su entrambe le altre sessioni (a ±1%); Monza ha una sola sessione, niente verifica incrociata. Nel provino le 14 curve di Zandvoort hanno il senso della guida uguale a quello misurato all'apice.

**Verifica:** validatore senza errori su 13 guide e 2 file di ancore · **956/956** test in 18 file (`test_tracciati` 70 → 98) · provino verificato a schermo (clic esatto, Maiusc+clic, zoom, trascinamento, mappa grande, export intercettato senza download) · `apply_anchors.py --dry-run` e `verifica_ancore.py` sugli export veri · nessuna chiamata LLM · frontend non toccato (il provino sta in `public/assets/`, gitignorato).

**Da sapere:**
- Spa è esclusa dal provino finché non si rifà la numerazione secondo Coach Dave. Le altre 9 piste con guida e mappa aspettano una sessione registrata.
- Da controllare in gioco (Edoardo, 28/09): nella guida di Zandvoort la T3 e la T14 dicono «layout pre-2020, non sopraelevato» mentre la mappa verificata è quella 2020; la T9 dice «senza mai chiudere il gas» ma nel giro registrato si frena da 173 a 95 km/h.
- Prossimo passo: l'aggancio in sessione (testo della guida accanto al verdetto nel tab Curve, zoom sulla curva).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 28/09 (commit `cfdb0b2` sensi delle guide · `8ff1fa2` ancoraggio delle curve · `44eb749` docs).

---

## Entry #046 — Analisi per curva solo sui giri di ritmo, e tre sessioni MoTeC multi-giro vere

| Campo | Valore |
|---|---|
| Data | 29/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `backend/app/analisi/curve.py` · `backend/app/tests/test_curve.py` · README, README.it, `docs/03`, `docs/04` · archivio dati (fuori repo) |
| Commit | vedi sotto |
| Contesto | Prerequisito dell'aggancio in sessione (che diventa la #047). Le sessioni MoTeC in archivio avevano un giro solo, quindi l'analisi per curva (servono 2 giri) non si era mai vista su dati veri. Edoardo non può registrare: prima la ricerca online di una sessione multi-giro, poi la costruzione. |

**Catalogo messaggi:**
1. «leggi la memoria e dimmi cosa dobbiamo fare con pitwall» → riepilogo dello stato; domanda aperta: ricerca prima o costruzione prima.
2. «prima la ricerca, poi costruiamo» → ricerca con tetto di 1 ora, chiusa in ~20 minuti; misurato il motore sui file trovati: l'analisi per curva conta anche i giri lenti.
3. «1 sì, 2 sì, 3 sì» → import delle due sessioni PS_Racing, correzione come entry a sé, anche il file di Zandvoort.
4. «1 sì, 2 sì, 3 sì, ok procedi» → setup Q dedotto da `telemetryLaps`; con un solo giro di ritmo niente analisi per curva; esclusi anche i giri invalidati.

**Ricerca (29/09):**
- Trovati: **PS_Racing** (YouTube, «Hotlap + FREE Setup», Drive pubblico), Monza, export grezzi di ACC con 10 giri nel `.ldx`: Ferrari 488 GT3 Evo 25/01/2026 (ACC 1.10.4) e Audi R8 Evo II 30/03/2025 (1.10.3), 8 giri completi e 6 di ritmo ciascuna, 23/27 °C, Optimal. **schubert** (YouTube, 14/06/2022), Zandvoort, Honda NSX GT3 Evo, ACC 1.8.14: 5 giri completi, 4 di ritmo.
- Scartati: Fri3d0lf (hotlap ritagliati in MoTeC i2, un giro), Abesports (MEGA, un giro), il dataset Kaggle «Monza» (è Assetto Corsa 1, in CSV), Flickerdox (multi-giro ma Hungaroring e Barcelona, 1.8), fixture di t-babin (Laguna Seca, Kyalami, Imola), un workspace MoTeC senza dati. Ripiego a pagamento non usato: Coach Dave, €5,99, 3 giri.
- Nessuna licenza esplicita sui file trovati: stanno in `%LOCALAPPDATA%\PitWall\motec\riferimenti\ps_racing_drive\` e `schubert_drive\`, ognuna col suo `PROVENIENZA.md`; mai nel repo.

**Modifica:**
- **`curve.py`**: nuova `giri_di_ritmo()`. L'analisi per curva usa solo i giri completi, **validi** e **entro il +10% sul migliore**: la regola del ritmo del motore, con la stessa costante `FATTORE_ANOMALO` importata da `motore.py` (una sola fonte). I giri esclusi restano nell'elenco dei giri del report e sono dichiarati nelle note («2 giri fuori dall'analisi per curva: oltre il +10% sul giro migliore» / «…invalidati dal gioco»). Con meno di 2 giri di ritmo l'analisi per curva **non si fa** e lo dice («servono almeno 2 giri di ritmo»): il ritmo, con un giro solo, tiene tutto, le curve no, perché una perdita misurata contro una sosta è un numero falso. Vale per il motore e per la rotta `/api/telemetria/.../curve`, che usano la stessa funzione.
- **Test** (`test_curve` 62 → 74, C59-C70): giro con sosta (+24%) escluso dal dettaglio ma presente fra i giri, perdite uguali a quelle dei soli giri buoni, verdetto senza la curva della sosta, nota con la soglia, 3 giri considerati per curva; un giro buono più una sosta → rifiuto; giro invalidato escluso e dichiarato; nessuna nota con giri tutti buoni. Sul `curve.py` di prima 9 dei 12 test nuovi falliscono.
- **Archivio** (fuori repo): le tre sessioni importate dalla rotta `POST /api/sessions/import/motec` come «riferimento, non tuo», col setup usato. PS_Racing allega un setup Q e uno R: solo il Q ha `telemetryLaps = 10`, come i 10 giri del file (l'R ha 0); schubert ha un setup solo, `telemetryLaps = 7` come i 7 tratti del `.ldx`. Il setup è caricato col nome «… (dedotto da telemetryLaps)», perché la rotta non ha un campo per le note. Id: `20260929-131527-monza_ferrari_488_gt3_evo-7801`, `20260929-131529-monza_audi_r8_lms_evo_ii_gt3-919f`, `20260929-131531-zandvoort_honda_nsx_gt3_evo-fedb`.

**Motivazione:** sui file veri il motore scriveva «Perdi 13,62 s a giro in curva 6» (Ferrari, per due giri da 151 e 176 s) e «Perdi 91,58 s a giro in curva 9» (NSX, un giro da 551 s fermo), più frenate «ballerine» di 254 m. Con l'aggancio sarebbe diventato «…in curva 6 (T11 Parabolica)»: un errore scritto più in grande.

**Risultato osservato** (prima → dopo, perdita totale per curva e prima voce di curva del verdetto):
- Ferrari 488 Monza: curva 6 −13,62 s → la voce più grave è la curva 5, −0,15 s; perdita totale 0,36 s su 6 giri; «2 giri fuori».
- Audi R8 Monza: curva 1 −5,14 s e frenata ballerina di 254,8 m → curva 5, −0,31 s; totale 0,92 s; «2 giri fuori».
- NSX Zandvoort: curva 9 −91,58 s → curva 9, −0,22 s; totale 0,67 s su 4 giri; «1 giro fuori».
- Il motore trova 6 tratti a Monza (11 curve nella guida) e 9 a Zandvoort (14): più curve della guida per tratto, come previsto dalla regola dell'aggancio. Lunghezza stimata 5751-5757 m contro 5793 (−0,7%) a Monza, 4185 contro 4259 (−1,7%) a Zandvoort.

**Verifica:** **968/968** test in 18 file (`test_curve` 62 → 74) · demo e numeri di Gigi invariati (`test_demo` 38/38, `test_gigi` 32/32) · import e `GET /api/sessions/{id}/analisi` sui tre file veri col backend acceso · nessuna chiamata LLM · frontend non toccato.

**Da sapere:**
- Nelle assunzioni dell'import della Ferrari compare «canali più lunghi del giro ritagliato» anche se il file non è ritagliato (i canali `EN_*` e `TIME` durano fino a 5057 s): la frase viene dal caso i2 e qui è impropria. Non corretta in questa entry.
- Il file di Zandvoort è di fisica 1.8: vale per le curve e per l'aggancio, non per giudicare gomme e freni.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 29/09 (commit `8f895e9` curve solo sui giri di ritmo · `9a6a4c3` docs).

---

## Entry #047 — Aggancio della guida in sessione: nomi dei tratti, scheda della curva, linee nel confronto

| Campo | Valore |
|---|---|
| Data | 29/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | NEW `backend/app/analisi/aggancio.py` · `analisi/curve.py` · `analisi/motore.py` · NEW `app/tests/test_aggancio.py` · `frontend/src/components/charts/AnalisiCurve.tsx` · `frontend/src/lib/api.ts` · README, README.it, `docs/03` |
| Commit | vedi sotto |
| Contesto | Passo 4 del filone guide, dopo l'ancoraggio (#045) e i giri di ritmo nelle curve (#046). Scope chiuso il 28/09: (a) tabella del tab Curve + scheda della guida con mappa zoomata e frecce, (b) linee della guida nel confronto, (c) nomi della guida nel verdetto; niente sulla demo. Ora si vede su dati veri (le tre sessioni della #046). |

**Catalogo messaggi:**
1. «partiamo con l'aggancio» → studiato il codice e calcolato l'abbinamento sulle due sessioni vere; piano e cinque domande.
2. «1 va benissimo era quello che volevo fare dall'inizio, 2 giusto, 3 va bene, 4 proviamo poi in caso sistemeremo, 5 appena lo vedo ti dirò se va bene [...] ora procedi e poi vediamo come organizzare di nuovo le schermate e la colonna di sinistra se serve» → costruito.

**Modifica:**
- **`analisi/aggancio.py`** (niente numpy): una curva della guida appartiene al **tratto del motore che ne contiene l'apice**, anche se il tratto scavalca il traguardo (la Parabolica a Monza). Le curve vengono da `data/tracks_anchors/` (inizio, apice, uscita, punto sulla mappa), il nome dalla guida (fonte; l'ancora ne ha una copia). Nome del tratto: intervallo più nomi distinti senza le fasi «(ingresso)», «(centro)», «(uscita)» — «T8-T10 Variante Ascari», «T1-T3 Variante del Rettifilo · Curva Grande»; una curva sola col nome intero; senza nome resta «T9»; curve non consecutive elencate («T1, T3»).
- **Motore**: il report ha un blocco nuovo `aggancio` (curve della guida con il tratto, nomi dei tratti, nota). C'è anche quando l'analisi per curva non si fa (un giro solo): le curve senza tratto servono al grafico. **Demo**: blocco vuoto con la riga «Sulla demo la guida non si aggancia: il circuito è generato…». Piste senza ancore o sessioni senza canali: nessun blocco.
- **Verdetto (c)**: `analizza_curve` accetta una funzione che dà il nome ai tratti appena trovati. Con il nome: «Perdi 0.15 s a giro in curva 5 (T8-T10 Variante Ascari)», e «apice al metro 3939» scende in testa alla prova; lo stesso nome sulle altre voci della curva (frenata ballerina, velocità minima incostante, folle). Senza nome il titolo resta quello di prima. L'ordinamento usa il campo `curva` della voce, non il titolo: nessun effetto sulle gravità.
- **Tab Curve (a)**: colonna «Guida» dopo «Curva» («—» se il tratto non contiene curve della guida). Clic su una riga → scheda sotto la tabella con la prima curva della guida del tratto: titolo (`TitoloCurva`), «nel tratto C5», mappa verificata ingrandita ×2,5 con il punto dell'ancora al centro e un pallino, testo della guida (`CurvaGuida`, lo stesso componente della sezione Tracciati), frecce ← → nell'ordine della guida (T1…Tn; la riga del tratto si evidenzia), ✕ per chiudere. La mappa compare solo se il layout è verificato, come in Tracciati.
- **Confronto (b)**: con la guida agganciata le linee verticali segnano l'**inizio** delle curve della guida («T1…T14» sulle linee, i nomi nella riga sotto il grafico); senza, restano gli apici dei tratti del motore.
- **Test** (`test_aggancio`, 37): regola dell'apice e tratto a cavallo del traguardo; nomi (fasi, nomi diversi, ordine, curve non consecutive, senza nome); ancore vere di Monza (11) e Zandvoort (14), T10 di Zandvoort senza nome; abbinamento atteso sui tratti della Ferrari; giro singolo senza tratti; JSON; demo; verdetto con e senza nomi, stesse perdite; demo nel report senza nomi; niente aggancio senza canali.

**Motivazione:** «perdi 0,15 s in curva 5» non dice niente a chi guida: la curva 5 del motore a Monza è la Variante Ascari intera. Con il nome della guida e la scheda accanto il verdetto si legge sulla pista, e la guida si ritrova dove serve, dopo l'errore.

**Risultato osservato** (verificato a schermo, modalità demo, sessioni scelte dalla colonna di sinistra):
- Ferrari 488 Monza: C1 «T1-T3 Variante del Rettifilo · Curva Grande», C2 «T4-T5 Variante della Roggia», C3 «T6 Curva di Lesmo 1», C4 «T7 Curva di Lesmo 2», C5 «T8-T10 Variante Ascari», C6 «T11 Curva Parabolica (Alboreto)». Clic su C5 → scheda T8 con la mappa centrata accanto al numero 08; frecce fino a T11 (→ disattivata in fondo). Dashboard: «Perdi 0.15 s a giro in curva 5 (T8-T10 Variante Ascari)», «Velocità minima incostante in curva 5 (T8-T10 Variante Ascari)».
- NSX Zandvoort: 9 tratti, tutte le 14 curve abbinate (C3 = T3-T6, C8 = T11-T12 Hans Ernstbocht, C9 = T13-T14).
- McLaren Zandvoort, un giro solo: niente tabella, confronto con le linee T1…T14 sull'inizio delle frenate.
- Demo: nessun nome nel verdetto, la riga che spiega perché.

**Verifica:** **1005/1005** test in 19 file (`test_aggancio` 37 nuovi) · demo e numeri di Gigi invariati · `tsc --noEmit` 0 errori · rotte `/`, `/sessioni`, `/telemetry` 200 · console del browser senza errori · nessuna chiamata LLM.

**Da sapere:**
- La T11 di Monza si chiama «Curva Parabolica (Alboreto)» nella guida: nel titolo del verdetto viene «in curva 6 (T11 Curva Parabolica (Alboreto))», con le parentesi doppie. Da decidere con Edoardo.
- Edoardo vuole rivedere l'ordine delle schermate e della colonna di sinistra, che si sono riempite: la colonna «Guida» va giudicata dentro quel riordino.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 29/09 (commit `328ad35` aggancio nel motore · `8a9161b` tab Curve e confronto · `bdb078e` docs). Colonna «Guida» e scheda approvate da Edoardo; parentesi doppie della Parabolica: si corregge la guida (entry successiva).

---

## Entry #048 — Colonna di sinistra riordinata, archivio ripulito, T11 di Monza «Curva Alboreto»

| Campo | Valore |
|---|---|
| Data | 29/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `frontend/src/components/ui/Sidebar.tsx` · `UserChip.tsx` · NEW `PannelloPista.tsx` · DEL `SidebarSection.tsx` · `app/(app)/layout.tsx` · `core/data/tracks_knowledge/monza.json` · `core/data/tracks_anchors/monza.json` · `app/tests/test_aggancio.py` · `docs/03` · archivio dati (fuori repo) |
| Commit | vedi sotto |
| Contesto | Dopo la #047 Edoardo: «la colonna a sinistra sta diventando troppo piena [...] il riquadro per le sessioni ora è troppo confusionario». Regole di riferimento: #008 e #010 (niente duplicati, navigazione sempre visibile, pochi blocchi). |

**Catalogo messaggi:**
1. «1 va bene anche se la colonna a sinistra sta diventando troppo piena, tocca sistemarla [...] 2 va bene, 3 ok push» → push della #047; diagnosi della colonna, proposta con schema e sei domande; domanda sul nome della T11.
2. «va bene la proposta ora vediamo come verrà a schermo. 1 va bene, 2 va bene, 3 sì, 4 va bene, 5 ok, 6 controlliamo dopo aver riorganizzato. va bene A. ok procedi.» → costruito.
3. «segnalo come riferimento, invece per la colonna e l'impostazione della pagina molto meglio ma risulta ancora disordinata e troppo attaccata. dagli un'occhiata e aggiusta il tutto» → McLaren marcata come riferimento; seconda passata su colonna e impaginazione (sotto).
4. «già meglio però risulta ancora vuota la sidebar, risolviamo questo problema una volta per tutte» → misurato il vuoto (~360 px su una finestra 1080p); tre strade proposte (mappa della pista, numeri della sessione, colonna più stretta): scelta **mappa della pista**.
5. «non vedo le modifiche che hai fatto, non vedo la pista.» → errore mio: il pannello era tarato per sparire sugli schermi bassi e l'avevo provato solo simulando uno schermo alto; lo schermo di Edoardo è quello del browser di prova (1536×639-695). Terza passata, misurata sullo schermo reale (sotto).
6. «continua a risultare troppo vuota, ti ho fatto uno screenshot adesso, guardalo e poi aggiusta tutto. non possiamo rimanere bloccati su questo.» → screenshot `Catture di schermata/Screenshot 2026-09-29 174932.png` (1920×1080 al 125% = 1536×696 px di pagina, sessione demo): pannello centrato con ~60 px vuoti sopra e sotto e una sola riga «Perdi di più · C7». Quarta passata: il pannello si riempie di contenuto (sotto).

**Diagnosi (prima):** su uno schermo alto ~650 px il blocco fisso in alto (marchio, utente, 7 voci) occupava due terzi della colonna, e il riquadro della sessione restava tagliato; l'elenco delle sessioni metteva in fila per data 13 sessioni di quattro tipi (demo, proprie, riferimenti di altri piloti, risultati di ACC senza telemetria), tutte uguali; il riquadro «Verdetto» era la copia della prima voce della Dashboard; in fondo Note, Tutorial, versione, Crediti.

**Modifica:**
- **Sidebar** (versione finale dopo la seconda passata): in cima solo marchio e **sessione aperta** (pista, vettura e tipo · giri su tre righe); navigazione in due gruppi con etichette leggibili, **«La sessione»** (Dashboard, Telemetria, Setup, Engineer Console) e **«Archivio e studio»** (Sessioni, Tracciati, Lezioni: righe più piccole e più tenui — la prima versione a tre riquadri era stretta, con scritte da 0,55 rem); tolto il riquadro Verdetto; in fondo **chip dell'utente** (menu verso l'alto), bottone **✎ Note** accanto, versione. La prima passata aveva utente e sessione in cima, due riquadri bordati quasi uguali uno sotto l'altro: si confondevano. Su 1536×639 la colonna entra intera (navigazione: 342 px di contenuto in 342 px); scorre solo col pannello delle note aperto. Il selettore sta fuori dallo scroll perché il suo elenco non venga tagliato.
- **Pannello della pista, versione finale (quarta passata):** allineato in alto subito sotto la navigazione — intestazione «La pista · Monza · guida →», la mappa, e **«Dove perdi»**: le curve sopra i 30 ms in ordine di perdita, **numerate** (1 in rosso, le altre scure) con lo **stesso numero sulla mappa** (le prime tre, sulla prima curva della guida del tratto), il nome della guida quando la pista è ancorata, la perdita a giro; ogni riga porta a Telemetria. Le righe sono **quante ne entrano** (fino a 5): misurato sullo schermo di Edoardo (colonna 695 px), demo = 3 righe (C7 −0.18, C1 −0.17, C6 −0.16), Ferrari Monza = 3 righe con i nomi (C5 · T8-T10 Variante Ascari, C6 · T11 Curva Alboreto, C1 · T1-T3 …), **1 px** libero in fondo. Senza analisi per curva: il motivo («Curve non misurabili: …»).
- **Versione con note e utente in testa, tarata sullo schermo di Edoardo (1536×639):** niente piede — **note** e **utente** sono due icone tonde accanto al marchio (il menu dell'utente contiene nome, «Rifai il tutorial», «Crediti immagini», «Esci» e la versione; le note si aprono in un riquadro sotto l'icona); «Archivio e studio» è **una riga** di collegamenti «Sessioni · Tracciati · Lezioni»; voci della navigazione e margini un po' più bassi; il pannello della pista è compatto (mappa, «Perdi di più −0.15 s», «C5 · T8-T10 Variante Ascari», tutto cliccabile verso la guida). Misure sullo schermo reale: testa 183 px, navigazione 235, pista 222 con la mappa a 191×107 px. Prima (secondo giro) la pista non compariva: testa 185 + navigazione 339 + piede 93 non lasciavano spazio.
- **«La pista»** (NEW `PannelloPista.tsx`), nello spazio fra la navigazione e il fondo della colonna: la mappa verificata della pista della sessione aperta con un **pallino** (pulsante, `motion-safe`) sulle curve della guida del tratto dove perdi di più (dall'aggancio), sotto «Perdi di più −0.15 s» e «C5 · T8-T10 Variante Ascari»; mappa e testo portano a `/tracciati/<pista>` (guida o scheda). Non ripete la Dashboard: la mappa non c'è in nessuna pagina della sessione. Il pannello **misura l'altezza che gli resta** (ResizeObserver) e mostra mappa + testo, solo il testo, o niente: su uno schermo basso la navigazione ha la precedenza. Il contenitore vuoto vale zero pixel (senza margini, `flex-1 basis-0`); il contenuto è centrato nello spazio libero. Le mappe SVG dichiarano solo il viewBox: larghezza piena e altezza dal disegno, e se esce troppo alta si stringe la larghezza con le proporzioni misurate al caricamento (con larghezza e altezza automatiche collassava a zero). Senza mappa verificata: pista · km · curve. Sotto i 30 ms (soglia del verdetto) nessuna «perdi di più». Demo: la mappa senza pallino e senza nomi (niente aggancio).
- **Impaginazione** (`app/(app)/layout.tsx`): contenuto centrato (`max-w-6xl mx-auto`) con margini 32-48 px; prima partiva a 24 px dalla colonna, allineato a sinistra, con una banda vuota a destra. Vale per tutte le pagine.
- **Elenco delle sessioni**: tre gruppi, **Le tue**, **Riferimenti · altri piloti**, **Demo**, con il conteggio; al massimo 5 per gruppo più «altre N in Sessioni»; la sessione aperta resta visibile anche oltre le prime cinque; «senza telemetria» sulle sessioni che non hanno canali. L'elenco è largo 320 px (sborda sulla pagina) e ogni voce ha pista, vettura e dati su tre righe: nella larghezza della colonna le vetture uscivano troncate («McLar…»).
- **UserChip**: diventa il menu dell'utente, in fondo alla colonna — «Rifai il tutorial», «Crediti immagini» (l'attribuzione resta raggiungibile, come chiedono le licenze CC), «Esci».
- **`SidebarSection.tsx`** cancellato: lo usava solo il riquadro Verdetto.
- **T11 di Monza**: nome «Curva Alboreto» (ufficiale dal 2021) al posto di «Curva Parabolica (Alboreto)», nella guida e nelle ancore (il validatore li confronta). Il resto della guida non cambia: la chicca «Dal 2021 la Parabolica si chiama ufficialmente Curva Alboreto…» c'era già. Nel verdetto: «…in curva 6 (T11 Curva Alboreto)», senza parentesi doppie.
- **Archivio** (fuori repo): cancellate dall'app (rotta DELETE, che toglie anche i canali) 7 sessioni — Spa BMW ×2 e Zandvoort McLaren ×2 del 17/09, e le 3 del 14/09 coi soli risultati/setup di ACC. **Tenute** le due sessioni d'origine delle ancore: Monza BMW (`…-711b`, registrazione `…-bcf3`) e Zandvoort McLaren (`…-3e52`, registrazione `…-5f1e`; nella proposta era sfuggita, stesso criterio). I file MoTeC grezzi restano in `motec/riferimenti`. Restano 6 sessioni: demo, le due d'origine, le tre multi-giro della #046. La McLaren `…-3e52` (file di kyxap, importata il 17/09 senza la spunta) marcata come **riferimento** su richiesta di Edoardo: bundle riscritto con `store.salva` (stesso id, così le ancore di Zandvoort puntano ancora alla sua registrazione `…-5f1e`) e `riferimento` nel `sessione.json` della registrazione; copia di sicurezza dei due file prima. Il gruppo «Le tue» ora è vuoto e non compare.

**Motivazione:** la colonna era cresciuta a ogni filone senza un disegno; le regole del #008/#010 erano state perse per strada.

**Risultato osservato — «La pista»:** su una colonna alta 1030 px (simulata rimpicciolendo la pagina al 62%) Ferrari Monza: mappa con tre pallini sulla Variante Ascari, «C5 · T8-T10 Variante Ascari −0.15 s»; NSX Zandvoort: pallini su Kumho e Arie Luyendijk, «C9 · T13-T14 … −0.22 s». Su 639 px reali la navigazione entra esatta (339/339 px) e il pannello si toglie da solo. Il verdetto dopo il riavvio del backend dice «(T11 Curva Alboreto)».
**Risultato osservato — colonna e pagine** (a schermo, 1536×639, Dashboard, Telemetria, Tracciati): la colonna intera sta nello schermo senza scorrere; elenco delle sessioni a gruppi e leggibile («Riferimenti · 5», «Demo · 1»); menu dell'utente verso l'alto con le tre voci; pannello Note sopra il chip; contenuto delle pagine centrato. Console del browser senza errori.

**Verifica:** `tsc --noEmit` 0 errori · rotte `/ /telemetry /setup /console /sessioni /tracciati /tracciati/monza /lezioni /crediti /login` 200 · validatore delle guide senza errori (13 guide, 2 ancore) · `test_aggancio` 37/37 · `test_tracciati` 98/98 · nessuna chiamata LLM.

**Da sapere:**
- Prossimo, deciso da Edoardo: rivedere le pagine una alla volta dopo il riordino della colonna.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 29/09 («ora va benissimo»): `71610c7` Curva Alboreto · `0fe52c5` colonna di sinistra e pannello della pista · `f2d64ae` docs. Nota: la cancellazione di `SidebarSection.tsx` è finita in `71610c7` (era già in stage da prima del primo commit) invece che in `0fe52c5`; il contenuto è corretto, la storia pushata non si riscrive.

---

## Entry #049 — Dalla demo alla guida: invito nel tab Curve e tab che resta al cambio di sessione

| Campo | Valore |
|---|---|
| Data | 29/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `frontend/src/components/charts/AnalisiCurve.tsx` · `frontend/src/components/ui/Tabs.tsx` · `frontend/src/app/(app)/telemetry/page.tsx` |
| Commit | vedi sotto |
| Contesto | Dopo la #048 Edoardo: «adesso mancano le curve nella telemetria, non ci sta lo zoom che volevo e su cui avevamo lavorato». Stava guardando la DEMO, la sessione di partenza della modalità demo, dove l'aggancio è escluso per scelta (scope del 28/09: circuito generato, la Parabolica a 0,934 invece di 0,8975). Verificato: sulla Ferrari di Monza colonna «Guida», scheda e zoom funzionano. |

**Catalogo messaggi:**
1. «ok però adesso mancano le curve nella telemetria, non ci sta lo zoom che volevo e su cui avevamo lavorato.» → diagnosi (demo senza aggancio per scelta), tre strade proposte: invito nel tab Curve, partire da una sessione vera, agganciare anche la demo (file protetto). Scelta: **invito nel tab Curve**.

**Modifica:**
- **Invito** (`AnalisiCurve.tsx`, `InvitoGuida`): sulla demo, al posto della riga di nota, un riquadro con il perché («Sulla demo la guida non si aggancia…») e il bottone **«Apri Monza · Ferrari 488 GT3 Evo con la guida →»**: la sessione vera della stessa pista con telemetria e più giri, a parità la più recente (Ferrari 25/01/2026 prima dell'Audi 30/03/2025). La demo resta com'è: verdetto, numeri e cache di Gigi invariati, nessun file protetto.
- **Tab che resta** (`Tabs.tsx`, `telemetry/page.tsx`): il tab scelto vive nella pagina (i `Tabs` accettano `value`/`onChange`), perché mentre la sessione nuova carica la pagina smonta i tab e al ritorno ripartivano da «Giri». Ora cambiando sessione si resta sul tab dov'eri; i contenuti (Giri, Curve, Gomme e freni) ripartono puliti con `key={idSessione}`, così la scheda di una curva non resta aperta su un'altra pista.

**Motivazione:** chi entra in demo parte dalla demo, e sulla demo la guida non c'è: senza un invito non trovava mai la cosa appena costruita.

**Risultato osservato** (a schermo, 1536×639): demo → Telemetria → Curve: riquadro con il bottone; clic → Ferrari di Monza, **sempre sul tab Curve**, colonna «Guida» (C1 «T1-T3 Variante del Rettifilo · Curva Grande» … C6 «T11 Curva Alboreto») e linee T1…T11 nel confronto. Console senza errori.

**Verifica:** `tsc --noEmit` 0 errori · percorso provato nel browser · backend non toccato.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 29/09 (commit `70b954d` invito e tab · `b7403cd` docs).

---

## Entry #050 — Dashboard riordinata: il verdetto al centro, indicatori in colonna, niente doppioni

| Campo | Valore |
|---|---|
| Data | 29/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `frontend/src/app/(app)/page.tsx` · `frontend/src/components/ui/SessionBriefing.tsx` · DEL `frontend/src/components/charts/Sparkline.tsx` |
| Commit | vedi sotto |
| Contesto | Prima pagina della revisione «una alla volta» chiesta da Edoardo dopo il riordino della colonna (#048). Regole del #008/#010: niente doppioni, niente vuoti, gerarchia. |

**Catalogo messaggi:**
1. «partiamo dalla dashboard» → fotografata sul suo schermo (1536×639): pagina alta 2350 px. Diagnosi e tre impaginazioni proposte (verdetto al centro, numeri in alto, stessa pagina più compatta) + destino delle schede di pista e vettura. Scelte: **verdetto al centro** e **pista e vettura compatte in fondo**.

**Diagnosi (prima):** la scheda della sessione ripeteva miglior giro, teorico e consumo che stavano anche negli indicatori; accanto al verdetto la colonna di destra finiva presto e lasciava un vuoto; 7 indicatori in riquadri grandi, 3 per riga, l'ultimo da solo, alcuni senza grafico e mezzi vuoti, con trascina/allarga; foto di pista e vettura a tutta larghezza (quasi una schermata) con testi del catalogo; «Prossime azioni» = doppione della colonna di sinistra.

**Modifica:**
- **Fascia della sessione** in alto, una riga: pista e vettura, poi tipo · giri (e buttati) · gomme · con/senza telemetria · data, e il distintivo della fonte (demo / MoTeC · rif.). I numeri non ci sono più: stanno negli indicatori.
- **Due colonne**: a sinistra il **verdetto** (invariato) con sotto le **note sui dati** (dicono su cosa poggia il verdetto, e pareggiano le colonne); a destra **«Cosa regge»** e i **7 indicatori come righe** (pallino di stato, nome, valore, nota sotto; clic = lo stesso dettaglio di prima, con grafico, riferimenti e «come si calcola»).
- **Pista e vettura compatte** in fondo (`TrackCard`/`CarCard` con `compatta`): miniatura accanto al testo, una riga di dati (km, curve, deportanza / anno, CV, kg, aiuti mancanti), il «focus setup» o la didascalia in due righe. La pagina Setup usa ancora le schede grandi.
- **Tolti**: numeri della vecchia scheda, riquadri grandi degli indicatori con trascina/allarga (e la loro persistenza), «Prossime azioni», `Sparkline.tsx` (lo usava solo la Dashboard).

**Motivazione:** la Dashboard era cresciuta per aggiunte: tre schermate e mezza, con i numeri ripetuti due volte e i collegamenti ripetuti dalla colonna.

**Risultato osservato** (a schermo, 1536×639, sessione demo): pagina **1028 px** (da 2350); colonne del verdetto e degli indicatori alte uguali (611 px e 611 px); il dettaglio di «Degrado» si apre col grafico e i riferimenti; console senza errori.

**Verifica:** `tsc --noEmit` 0 errori e nessuna variabile inutilizzata nei file toccati (`--noUnusedLocals`) · rotte `/` e `/setup` 200 · backend non toccato.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 30/09 (commit `50465e7` Dashboard · `65f3f60` docs). Chiuso anche INC-V2-005: il trascina/allarga della Dashboard non esiste più.

---

## Entry #051 — Telemetria riordinata: Giri, Curve, Gomme e freni; perdite in un solo formato

| Campo | Valore |
|---|---|
| Data | 30/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `frontend/src/components/charts/GiriSessione.tsx` · `AnalisiCurve.tsx` · `frontend/src/components/ui/PannelloPista.tsx` · `Verdetto.tsx` · `frontend/src/lib/formato.ts` · `lib/api.ts` · `app/(app)/page.tsx` · `GommeFreni.tsx` · DEL `frontend/src/components/charts/PressureGauge.tsx` · `backend/app/analisi/motore.py` · `backend/app/tests/test_analisi.py` · `test_analisi_l4.py` · `docs/03-v2-architecture.md` |
| Commit | vedi sotto |
| Contesto | Seconda pagina della revisione «una alla volta», dopo la Dashboard (#050). Misurata sul suo schermo (1536×639): Giri 1063 px, Curve 1216, Gomme e freni 1605. |

**Catalogo messaggi:**
1. «ok push, poi partiamo dalla telemetria» → diagnosi dei tre tab e 5 proposte: Giri con barre nella colonna e settori a destra; Gomme e freni = «macchina vista dall'alto» + un grafico con selettore; Curve senza la riga dei nomi e con freno e gas in una traccia; perdite nello stesso formato ovunque («+0.15 s», col punto come il resto dell'app); un tab alla volta dentro una sola entry.
2. «ok a tutte le proposte, partiamo dal tab Giri» → tab Giri.
3. «va bene, passiamo al tab Curve però una cosa: aggiungi un disclaimer per i settori ed in caso controlla perché se ricordo bene nel gtwc non ci stanno 3 settori registrati nei tempi sul giro ma 4» → disclaimer, verifica dei settori, tab Curve.
4. «1 i settori sono 3 te lo confermo, togliamo il disclaimer, 2 approvo la proposta. ok procedi.» → disclaimer tolto; verdetto della Dashboard con il segno «+».
5. «1 va bene, 2 guardiamolo adesso. ok procedi.» → perdita al millisecondo dal motore; degrado: pendenza e media dette per quello che sono.
6. «ok va bene così procedi con il resto.» → tab Gomme e freni.
7. «siccome per la macchina con vista dall'alto abbiamo avuto sempre problemi mentre la progettavamo, toglila completamente e lascia solo le sagome degli pneumatici. però tutto il resto mi sta piacendo abbastanza. ok push e poi ok procedi con il resto.» → via la carrozzeria: al centro solo le quattro gomme; riquadro «Ruota per ruota».

**Modifica — tab Giri:**
- **Tolto il grafico «Distacco dal giro migliore»**: ripeteva la colonna Δ migliore. Ora la barra sta nella cella, accanto al numero, in scala sul distacco più grande fra i giri di ritmo. I giri fuori ritmo sono fuori scala: solo il numero, spento.
- **Settori a destra** (320 px) come righe: S1 · perdita a giro (arancio), poi migliore · media, poi dispersione · «nel migliore» (quanto ci ha lasciato il giro migliore; «pari» se zero). Nota con il significato dei due termini e il giro teorico.
- **Sessioni senza split** (es. MoTeC della Ferrari a Monza): spariscono le colonne S1-S3 e il riquadro dei settori, la tabella va a tutta larghezza e la nota dice «Questa sessione non ha i tempi dei settori.» Prima: tre colonne di trattini e un riquadro col messaggio tecnico del motore.
- NEW `perdita(ms)` in `lib/formato.ts`: «+0.228 s», sempre positivo, al millesimo come i giri e i delta (a due decimali 46 e 50 ms diventavano entrambi «+0.05 s»).
- ~~Disclaimer sui settori~~: messo (msg 3) e tolto (msg 4) dopo la conferma di Edoardo che in ACC i settori sono 3.

**Verifica sui settori (messaggio 3):** nel codice sono fissi a **3** — il motore (`analisi/motore.py`) tiene solo i giri con esattamente 3 split, l'API ne accetta al massimo 3 (`api/sessions.py`), il frontend disegna S1-S3; le 13 guide hanno 3 settori. Però la shared memory di ACC ha `sectorCount` («Number of sectors»), che il registratore **non legge**: quindi ACC prevede un numero variabile. Nessuna sessione vera dell'archivio ha split (li ha solo la demo, generata da noi) e la cartella Results di ACC è vuota: **non c'è un dato per confermare né smentire i 4 settori**; ricerca web senza esito. **Chiuso (msg 4): Edoardo conferma 3 settori**, niente generalizzazione.

**Modifica — Dashboard (`components/ui/Verdetto.tsx`):** la perdita a giro del verdetto passa da «−0.31 s» a «+0.31 s», come nel resto dell'app. Resta ai centesimi: il motore manda `decimi` già arrotondati (315 ms → 3.1), quindi sulla stessa schermata il verdetto dice «+0.18 s» e la colonna «+0.184 s» per la curva 7. Per il millesimo serve il valore in ms dal motore (backend): chiesto a Edoardo → fatto (msg 5, sotto).

**Modifica — motore (msg 5, `backend/app/analisi/motore.py`, non protetto):** `Perdita` ha due campi nuovi: `perdita_ms` (lo stesso numero di `decimi` al millisecondo, valorizzato dove c'è `decimi`: teorico, settore, costanza, degrado, curva principale) e `misura` (cosa misura il numero: «a giro» di default, «in media a giro» per il degrado, «di deviazione» per la costanza). `decimi` resta per i testi. Il verdetto (`Verdetto.tsx`) scrive `perdita(perdita_ms)` e sotto la `misura`. Test nuovi: N26b, N31b (`test_analisi`), L37b (`test_analisi_l4`).

**Degrado, «+0.70 s a giro» contro «352 ms/giro» (msg 5):** non era un errore, sono due misure diverse con la stessa etichetta. L'indicatore mostra la **pendenza** (ogni giro più lento del precedente di 352 ms) → ora «+352 ms ogni giro»; il verdetto mostra quanto costa **in media a giro** sui 5 giri del calo (352 × 4 / 2 = 704 ms) → ora «+0.704 s · in media a giro». Anche la costanza ora dice «di deviazione» invece di «a giro».

**Risultato osservato — Dashboard** (demo, 1536×639, backend riavviato): verdetto «+0.704 s in media a giro», «+0.315 s a giro» (come il tab Giri), «+0.184 s a giro» (come la colonna di sinistra); Degrado «+352 ms ogni giro»; pagina sempre 1028 px. Restano ai centesimi i **testi** del motore (titolo «Perdi 0.18 s a giro in curva 7», prove in decimi): parlano in decimi per scelta, non toccati.

**Modifica — tab Gomme e freni (msg 6):**
- **«Ruota per ruota»**: le quattro ruote al loro posto (Ant.SX, Ant.DX sopra; Post.SX, Post.DX sotto); al centro, dopo il msg 7, **solo le sagome delle quattro gomme** (la carrozzeria disegnata è stata tolta) con «▲ davanti» e gli squilibri fra gli assi (psi e °C; si riportano, non si giudicano). Ogni ruota ha tre righe: **pressione** e **core** con il valore (verde dentro, arancio fuori, giudizio del motore), la barra sotto/dentro/sopra la finestra Kunos con la quota e il min–max; **freno** con la massima, la media e le pastiglie. Il pallino di ogni ruota ha il colore della sua linea nel grafico.
- Sessioni MoTeC senza temperatura al core: la riga diventa «Gomma · 83 °C · MoTeC · non giudicata» (prima un riquadro a parte).
- **Un grafico solo** «Giro per giro» con il selettore Pressione / Temperatura al core / Freni, massima (solo le grandezze che la sessione ha) e la **legenda delle ruote** nel titolo (prima mancava). Banda Kunos e linee community come prima; la nota community compare con i freni.
- Tolti: i 4 manometri (`PressureGauge.tsx` cancellato, lo usava solo questo tab), il grafico dei freni sempre visibile (quattro righe piatte fra 450 e 650 °C), le schede separate dei freni, le barre delle temperature.
- Piccoli: squilibri arrotondati prima del segno (niente «−0.0 psi»); punto finale sulle note del motore che non l'avevano.
- `docs/03`: righe di Dashboard (era ancora «7 KPI con drag&drop»), Telemetria e `components/charts/`.

**Risultato osservato — Gomme e freni** (1536×639): demo **854 px** (da 1605; 879 con i freni, per la nota community), Ferrari a Monza 875 px con «Gomma … MoTeC · non giudicata» e il selettore a due voci. Console senza errori; rotte `/ /telemetry /setup /console /login /sessioni` 200.

**Altezze finali della Telemetria** (demo / Ferrari): Giri 639 / 639 (da 1063) · Curve 1224 / 1132 (da 1291 / 1216) · Gomme e freni 854 / 875 (da 1605).

**Verifica backend:** suite **1008/1008** in 19 file (1005 + N26b, N31b, L37b), `test_tracciati` 98/98.

**Modifica — tab Curve:**
- **Perdita media** nella tabella e nel «Dove perdi» della colonna di sinistra con `perdita()`: prima «154 ms» e «−0.15 s» per lo stesso dato, ora «+0.154 s» in tutti e due.
- **Pedali in una traccia**: gas sopra lo zero, freno sotto (tacche in valore assoluto, tooltip «Gas A/B», «Freno A/B» con valori positivi). Due grafici da 90 px → uno da 130.
- **Via la riga coi nomi** delle curve sotto il confronto (ripeteva la colonna Guida): il nome è nel **tooltip**, accanto ai metri, solo fra l'inizio e l'uscita della curva della guida (sul rettilineo niente nome; la prima versione diceva «T7 Lesmo 2» anche a metà del rettilineo).
- Nota del confronto: tolto il «;» finale quando B è della stessa sessione.

**Risultato osservato — Curve** (1536×639): Ferrari a Monza **1132 px** (da 1216), demo 1224 (da 1291); tooltip «3904 m · T8 Variante Ascari (ingresso)»; colonna e tabella dicono entrambe «+0.154 s». Console senza errori.

**Risultato osservato — Giri** (a schermo, 1536×639): tab Giri **639 px** (da 1063), cioè una schermata, sia sulla demo (8 giri, colonne 525/531 px) sia sulla Ferrari a Monza (10 giri, senza settori). Console senza errori.

**Verifica:** `tsc --noEmit` 0 errori.

**Nota a margine (non toccata):** sulla Ferrari a Monza il carburante è 3.10 l in tutti i giri completi: sembra una media spalmata, non una misura giro per giro. Da guardare a parte.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 30/09 (msg 7), dopo aver tolto la carrozzeria: `4c4b41f` Telemetria · `3730c71` verdetto al millisecondo · `0fec3fb` docs.

---

## Entry #052 — Engineer Console: stato vero, scenari onesti, risposta senza doppioni

| Campo | Valore |
|---|---|
| Data | 30/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `frontend/src/app/(app)/console/page.tsx` · `components/ui/PageHeader.tsx` · `lib/console.ts` · `backend/app/analisi/gigi.py` · `analisi/curve.py` · `app/tests/test_gigi.py` · `test_curve.py` · `docs/03-v2-architecture.md` |
| Commit | vedi sotto |
| Contesto | Terza pagina della revisione (la Setup si rivede dopo la verifica dei range). Misurata sulla Ferrari a Monza (MoTeC, live spento): 1411 px. |

**Catalogo messaggi:**
1. «ok push e poi ok procedi con il resto» (dopo la #051) → diagnosi della Console e 4 proposte: testa unica con lo stato vero; scenari a modello spento disattivati (A; la risposta per argomento, B, con la chat di Gigi); risposta del motore senza doppioni; testi del motore al millesimo.
2. «ok a tutte le proposte, procedi».

**Diagnosi (prima):** sotto il titolo un riquadro ripeteva «Gigi» e la sessione (già nella colonna) con «ONLINE» — falso: la risposta era «dal motore di analisi · senza modello»; a modello spento **ogni scenario dava la stessa risposta** («Calcola carburante» → le pressioni); la risposta ripeteva la Dashboard (tutto il verdetto nella Diagnosi, «Regge» e note sui dati con i codici dei canali EN_ET, EN_TL… nelle Note) e se stessa (la Causa ripeteva la prima frase della Diagnosi, la Guida le voci della Diagnosi); «Perdi 0.15 s» contro «+0.154 s» della colonna.

**Modifica:**
- **Testa**: via il riquadro di Gigi; `PageHeader` accetta `azioni` a destra, e la Console ci mette lo **stato vero** dalla fonte della risposta: «dal vivo» (verde) / «demo-mode» / «cache» / «dal motore · senza modello» / «fallback offline». Tolta la stessa etichetta dalla barra «Analisi richiesta» (doppione).
- **Senza modello** (fonte `motore` o `fallback`, sessione non demo): i 4 scenari, la casella e ANALIZZA si spengono, con la riga «Gigi dal vivo è spento: qui risponde il motore di analisi, sempre con l'analisi della sessione. Scenari e domande libere tornano attivi con Gigi dal vivo.» Sulla demo (risposte preparate per scenario) restano accesi.
- **Risposta dal motore** (`gigi.py`): la Diagnosi dice solo il problema numero uno, poi «Qui sotto la causa e le correzioni; il verdetto completo (N voci) è nella Dashboard.»; la Causa, se il problema numero uno è di gomme, non lo ripete («è il problema numero uno qui sopra», più le altre voci di gomme); le Note non ripetono «Regge» né le note tecniche: «Cosa regge e le note sui dati sono nella Dashboard (N note).»; la riga «Alla domanda…» non compare per «Analizza la sessione». La riga «senza modello linguistico» resta (G11).
- **Titolo delle curve** (`curve.py`): «Perdi 0.154 s a giro in curva 5» (millesimo, come verdetto e colonna).
- Test nuovi: G11b-G11e (`test_gigi`), C42b (`test_curve`).

**Risultato osservato** (1536×639): Ferrari a Monza **1111 px** (da 1411), stato «dal motore · senza modello», scenari e casella spenti con la riga di spiegazione, Diagnosi di due righe, Causa «è il problema numero uno qui sopra», Guida e colonna con «0.154 s»; demo: stato «demo-mode», scenari accesi, risposta della cache invariata. Console del browser senza errori.

**Verifica:** backend **1013/1013** in 19 file (1008 + G11b-e + C42b) · `tsc --noEmit` 0 errori, nessuna variabile inutilizzata nei file toccati.

**File protetti:** ☑ nessuno toccato (`demo_responses.py`, `core/agent.py`, `core/prompts/*` invariati).
**Decisione:** ☑ Mantenuto — «ok push» il 30/09 (commit `bd34b89` Console · `17ae9f9` risposta di Gigi e curve · `2fa958c` docs).

---

## Entry #053 — Sessioni: archivio in cima e a gruppi, un solo riquadro per aggiungere

| Campo | Valore |
|---|---|
| Data | 30/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `frontend/src/app/(app)/sessioni/page.tsx` · `frontend/src/lib/sessione.tsx` · `frontend/src/components/ui/Sidebar.tsx` · `docs/03-v2-architecture.md` |
| Commit | vedi sotto |
| Contesto | Quarta pagina della revisione. Misurata sul suo schermo (1536×639), percorso PC: 1201 px. |

**Catalogo messaggi:**
1. «ok push, poi procedi con Sessioni» (dopo la #052) → diagnosi e 4 proposte: archivio sempre visibile e in cima; archivio a gruppi come la colonna, meno etichette; un solo riquadro «Aggiungi una sessione» a tab con MoTeC predefinito; stima ~850 px.
2. «ok a tutte le proposte, procedi».

**Diagnosi (prima):** senza piattaforma scelta (succede entrando in demo, che azzera il profilo) la pagina mostrava solo «Dove giochi ad ACC?» e **l'archivio spariva**; con la piattaforma, l'archivio stava in fondo (da 767 px) sotto tre riquadri di import (file di ACC con i percorsi per intero, telemetria registrata mezzo vuota, MoTeC — l'unico usato davvero: 5 sessioni vere su 5); ogni riga dell'archivio ripeteva MOTEC · RIFERIMENTO · TELEMETRIA · SETUP.

**Modifica:**
- **Archivio sempre, e per primo**, a gruppi **Le tue / Riferimenti · altri piloti / Demo** con il conteggio: gli stessi gruppi della colonna di sinistra, spostati in `lib/sessione.tsx` (`GRUPPI_SESSIONI`) e usati da tutte e due. Tolte le etichette «riferimento» (lo dice il gruppo) e «telemetria» sulle MoTeC (un export MoTeC ha sempre i canali). Restano MoTeC, setup, ritaglio i2, racconto; invariati Apri, MoTeC ↓, Cancella con la conferma sul bottone.
- **«Aggiungi una sessione»**: un riquadro solo, con «Giochi su PC · cambia» nel titolo; senza piattaforma la domanda sta qui dentro (e l'archivio resta visibile sopra). PC = tre tab **Export MoTeC** (predefinito) · **File di ACC** · **Registrazione dal vivo**, con il pallino di stato del registratore e il numero di registrazioni da importare sul nome del tab (lo stato si legge nel percorso, così resta vero anche a tab chiuso). Ogni tab ha una riga di istruzioni al posto dei percorsi per intero. Il percorso console è una parte dello stesso riquadro (non più un riquadro nel riquadro), dietro «Mostra anche il percorso console».

**Risultato osservato** (1536×639, percorso PC): **1022 px** con il tab MoTeC (da 1201), 948 con File di ACC o Registrazione; l'archivio comincia subito sotto il titolo (prima da 767 px). Tab verificati uno per uno, percorso console aperto e richiuso. Console del browser senza errori. La stima di ~850 era ottimista: le 6 righe dell'archivio in cima pesano circa 460 px.

**Nota di processo:** un passaggio di `prettier` (il progetto non lo usa) aveva riformattato tutto il file; ripristinato e rifatte le sole modifiche, così il diff contiene solo quelle.

**Verifica:** `tsc --noEmit` 0 errori, nessuna variabile inutilizzata nei file toccati · backend non toccato.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 30/09 (commit `b146f32` Sessioni · `cc08913` docs).

---

## Entry #054 — Tracciati: indice più denso e legato alle sessioni, scheda con mappa e curve affiancate

| Campo | Valore |
|---|---|
| Data | 30/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `frontend/src/app/(app)/tracciati/page.tsx` · `frontend/src/app/(app)/tracciati/[id]/page.tsx` · `docs/03-v2-architecture.md` |
| Commit | vedi sotto |
| Contesto | Quinta pagina della revisione. Misurata sul suo schermo (1536×639): indice 3282 px, scheda di Monza 3638. |

**Catalogo messaggi:**
1. «ok push, poi procedi con Tracciati» (dopo la #053) → diagnosi di indice e scheda, 7 proposte: indice a quattro colonne (A); soprannome solo se diverso; «aperta ora» e sessioni per pista; mappa e curva per curva affiancati; dati di pista nei numeri in alto; sezioni brevi a coppie; accenti veri nelle guide (entry a parte, dopo).
2. «ok a tutte le proposte, procedi».

**Modifica — indice:**
- **Quattro card per riga** (da tre), corpo più compatto. La foto non si accorcia cambiando le proporzioni del riquadro: con i ritagli di `crops.json` tornerebbe stirata (#041); con la card più stretta si rimpicciolisce da sola nelle stesse proporzioni.
- **Soprannome solo se dice qualcosa**: «COTA» sotto COTA non c'è più (anche nella scheda). Numeri e bandierine in fondo alla card (`mt-auto`): le card della stessa riga restano allineate.
- **Legame con le sessioni**: «aperta ora» sulla pista della sessione aperta, «N sessioni» dove ce ne sono in archivio (tue o di riferimento, non la demo).

**Modifica — scheda:**
- **Mappa verificata e curva per curva affiancati**; la mappa resta ferma mentre scorre l'elenco (`sticky`). Senza mappa (Suzuka) l'elenco va a tutta larghezza; senza guida (Kyalami) la mappa va a tutta larghezza come prima; senza nessuno dei due (COTA) nessun riquadro vuoto.
- **Dati di pista della guida nella riga dei numeri** (senso di marcia, dislivello, rettilineo più lungo), con «In ACC · …» e «fonte singola, da confermare» sotto la descrizione: via il riquadro «La pista».
- **Sezioni brevi a coppie** su due colonne (gomme e freni | track limits, box | meteo, traffico); l'errore comune e le chicche restano larghi.

**Risultato osservato** (1536×639): indice **2134 px** (da 3282); Monza **2801 px** (da 3638), con mappa e 11 curve affiancate; Spa 3654 con 19 curve e la mappa ferma accanto; Suzuka, Kyalami, COTA come sopra. Console senza errori. Le stime (1900 e 2400) erano ottimiste: le card hanno ancora la foto, e le sezioni lunghe (settori, chicche) restano larghe.

**Verifica:** `tsc --noEmit` 0 errori · backend non toccato.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 30/09 (commit `c6a0e13` Tracciati · `5f80122` docs).

---

## Entry #055 — Accenti veri nelle 13 guide dei tracciati

| Campo | Valore |
|---|---|
| Data | 30/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `backend/app/core/data/tracks_knowledge/*.json` (13 guide) · NEW `backend/scripts/accenti_guide.py` · `backend/app/tests/test_tracciati.py` |
| Commit | vedi sotto |
| Contesto | Proposta 7 della #054, approvata come entry a parte: nelle schede dei tracciati la guida si leggeva «e'», «piu'», «velocita'», «perche'». |

**Catalogo messaggi:**
1. «ok push, poi procedi con gli accenti».

**Censimento:** nelle 13 guide 1696 parole che finiscono con l'apostrofo. Casi ambigui guardati nel contesto uno per uno: «da'» è sempre il verbo (→ dà), «se'» in «in se'», «di per se'», «a se'» (→ sé), «ne'» (→ né), «si'» (→ sì), «mori'», «ospito'» (Zolder) e «negozio'» (Zandvoort) → morì, ospitò, negoziò. **Restano come sono**: «po'» (30), l'imperativo «sta'» (Monza), le elisioni davanti a un numero («all'80%», «dell'8%») e le parole fra virgolette singole ('abusare', 'sicura', '2002-present').

**Modifica:**
- NEW `scripts/accenti_guide.py`: converte parola per parola da una tabella (grave: è, più, già, può, però, così, lì…; acuto: perché, finché, purché, né, sé; -ità: velocità, stabilità, difficoltà…), solo se l'apostrofo non è seguito da una lettera. Lavora sul testo del file: indentazione e ordine delle chiavi restano, e ogni file deve restare JSON valido. **Una parola fuori tabella ferma lo script** (si guarda e si decide, non si indovina); `--prova` dice cosa cambierebbe. Serve anche per le guide che arriveranno scritte allo stesso modo.
- Conversione: **1658 accenti** in 13 file (955 righe cambiate, nessuna spostata).
- Test nuovo in `test_tracciati`: nessuna guida con accenti in apostrofo (usa la stessa espressione dello script); verificato che **fallisce sulle guide di prima** e passa su quelle nuove.

**Verifica:** validatore `check_track_knowledge.py` «ERRORI: nessuno»; `verifica_ancore.py zandvoort` con output **identico prima e dopo** (le 3 «NON REGGE» c'erano già); Monza 11/11 ancore. Suite **1014/1014** (1013 + il test degli accenti). Scheda di Monza a schermo: «È il punto di sorpasso», «più violenta», «Velocità pura», «lì vanno tutti uguali»; nessuna parola con l'apostrofo finale nel testo della pagina.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 30/09 (commit `6acd69c` guide, script e test · `9002e4e` docs).

---

## Entry #056 — Lezioni: collegamenti giusti con l'app e lezioni consigliate dal verdetto

| Campo | Valore |
|---|---|
| Data | 30/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `frontend/src/lib/lessons.ts` · `frontend/src/app/(app)/lezioni/page.tsx` · `frontend/src/app/(app)/lezioni/[slug]/page.tsx` · `frontend/src/app/(app)/telemetry/page.tsx` · `docs/A_Lezione_con_Gigi_ContentPack_v1.md` · `docs/03-v2-architecture.md` |
| Commit | vedi sotto |
| Contesto | Ultima pagina della revisione (la Setup si rivede dopo la verifica dei range). Indice 729 px, lezione ~1050: le misure andavano già bene, i problemi erano i collegamenti. |

**Catalogo messaggi:**
1. «andiamo avanti» → diagnosi di Lezioni e 4 proposte: LiCo → Consumo della Dashboard; Gomme → Telemetria sul tab Gomme e freni; «aggancio PitWall» → «nell'app»; «Consigliate» dal profilo e dal verdetto (tabella da mostrare prima). Nota sui contenuti della lezione 06.
2. «ok a tutte le proposte, procedi» → 1-3 fatte e verificate; tabella verdetto → lezione mostrata.
3. «1 va bene la tabella, 2 va bene la proposta. ok procedi.» → «Consigliate per te» e valori community segnati nella lezione 06.

**Diagnosi (prima):** la lezione LiCo diceva «si lega al calcolo strategia carburante» e apriva la Console, dove dalla #052 «Calcola carburante» è spento sulle sessioni vere; la lezione Gomme apriva la Telemetria sull'ultimo tab usato; «aggancio PitWall» era gergo nostro e sbilanciava le card; `recommendLessons` (dal profilo) esisteva ma l'indice non la usava, e nessuna lezione veniva dal verdetto.

**Modifica:**
- **LiCo** → la Dashboard: «Il consumo misurato della sessione aperta è nella Dashboard, indicatore Consumo: il LiCo è come lo abbassi in pista».
- **Gomme** → `/telemetry?tab=gomme`: la Telemetria legge il parametro una volta all'arrivo (senza `useSearchParams`, che in build chiederebbe un Suspense) e apre «Gomme e freni».
- «aggancio PitWall» → **«nell'app»** (card) e **«Nell'app»** (riquadro della lezione); etichetta in fondo alla card, card allineate.
- **«Consigliate per te»** in cima all'indice (`lezioniConsigliate` in `lib/lessons.ts`): le voci del verdetto in ordine di gravità con la tabella decisa da Edoardo (gomme → 06; ritmo che cala → 07; costanza, giro mai messo insieme, settore, frenata ballerina → 02; «Perdi … in curva» → 01; v-min incostante → 04; troppo tempo in folle → 05; giri buttati → nessuna), poi i punti deboli del profilo; senza doppioni, al massimo 3, ognuna col motivo («dal verdetto: …», «dal tuo profilo: …»). Né verdetto né profilo → la sezione non c'è.
- **Lezione 06**: «ottimale 80–90°C» e «±0.1 psi ogni ±1°C» detti per quello che sono, valori della community da confermare; la finestra 70–100°C al core indicata come Kunos. Stesso testo nel content pack in `docs/`.

**Risultato osservato** (1536×639): demo → consigliate 07 (ritmo che cala), 06 (pressioni posteriori), 02 (settore 3); Ferrari a Monza → 06, 01 (curva 5), 04 (v-min in curva 5); dal riquadro «Nell'app» della lezione 06 la Telemetria si apre su «Gomme e freni» (anche scrivendo l'indirizzo); indice 908 px con le consigliate. Rotte `/lezioni`, `/lezioni/gomme-finestra`, `/telemetry`, `/` 200; console senza errori.

**Verifica:** `tsc --noEmit` 0 errori · backend non toccato.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 30/09 (commit `9082b5e` Lezioni · `8e5b4d3` docs).

---

## Entry #057 — Range di setup, BMW M4 GT3: i click diventano i valori del gioco (INC-V2-003)

| Campo | Valore |
|---|---|
| Data | 30/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | ⚠️`backend/app/core/data/car_setup_ranges.json` · ⚠️`backend/app/core/setup_params.py` · `backend/app/bundle/adapters/acc_setup.py` · `backend/app/bundle/schema.py` · `backend/app/analisi/gigi.py` · NEW `backend/scripts/riconverti_setup.py` · NEW `backend/app/tests/test_setup_ranges.py` · `test_adattatori.py` · `test_sessions.py` · docs |
| Commit | `0aeca53` codice e test · `191b24f` docs |
| Contesto | Passo successivo dopo la revisione delle pagine: i range `DA_VERIFICARE` e INC-V2-003. La pagina Setup è la #058. |

**Catalogo messaggi:**
1. «leggi la memoria e riprendiamo il lavoro con pitwall» → status e due giri di domande. Scelte: si parte dalla sola **BMW M4 GT3**; fonte = tabella community + verifica in gioco con una **scheda da spuntare**; **nuovo schema** click → valore; vetture non verificate **solo in click** (niente slider né range generici); i suggerimenti di Gigi in click si fanno **dopo**, con la chat.
2. «1 fai sia excel che pdf […], 2 va bene, 3 va bene. ok procedi.» → scheda sul Desktop (`Scheda_setup_BMW_M4_GT3.xlsx` e `.pdf`, 51 righe) + `PitWall_verifica_BMW.json` (il setup di Monza 711b da caricare in gioco). Entry divise: #057 backend, #058 pagina Setup; INC-V2-003 resta aperto.
3. «non riesco a compilare la scheda pensaci te, poi compila il resto del codice.» → scheda chiusa con le fonti invece che in gioco, poi il codice.

**Le fonti** (nessuna è Kunos, che non documenta il formato):
- **Race Element** (RE, GPL-3.0, commit `55121bb`): conversione per vettura in C#, `SetupParser/Cars/GT3/BmwM4GT3.cs`. Ripresi i numeri, non il codice.
- **acc-setup-diff** (ASD, MIT, `7abe17d`): tabella per vettura in JS, ma alcune formule uguali per tutte.
- **simsource** (sito chiuso) come lo riporta **acc-setup-comparison** (`059a204`).
- **simracingsetup** (SRS): valori mostrati per 3 setup BMW pubblicati (letti dal Chrome di Edoardo). Senza i click: solo controllo di coerenza, e potrebbe usare le tabelle di RE.
- **PitLane Coach**: pressioni GT3 = 20.3 + 0.1 × click.

**Disaccordi e come si sono chiusi:**
- *Ripartizione di frenata*: RE e simsource 48.5 + **0.3** × click, ASD 0.2 (uguale per tutte le vetture). Il 51.2 % di un setup SRS con 0.2 cadrebbe fra due click → **0.3**, due fonti indipendenti.
- *Bumpstop rate*: RE 200 + 50 × click, ASD 300 + 100 (uguale per tutte). I 550 N di un setup SRS danno ragione a RE, ma SRS da sola non basta → **resta in click** (`DA_VERIFICARE`).
- *Splitter*: RE il click, ASD il click + 1; SRS mostra 0 → come RE, stesso limite → **resta in click**.
- *Caster*: RE un elenco di 41 valori, ASD e simsource 6.1 + 0.195 × click. Stessi estremi, ma su 19 click fino a 0.1° di differenza; i 9.7° di SRS ci sono solo nell'elenco di RE → **resta in click**.
- **Massimi**: nessuna fonte li dà, tranne le molle (6 valori per asse). `click_max: null` = nessun limite in alto noto.

**Due errori del codice trovati per strada** (confermati da tutte e due le fonti che danno la formula):
- l'altezza **posteriore** si prendeva dal secondo valore di `rideHeight`: è il **terzo** (sul setup 711b: 61 mm invece di 50 mm);
- il **camber** si prendeva da `staticCamber` e si marcava «verificato»: non è il valore del gioco (-4.21 contro i -4.0° del click 0, dietro -1.89 contro -3.5°). Ora si legge dal click; `staticCamber` resta nel grezzo.

**Modifica:**
- `car_setup_ranges.json` riscritto: `_meta` con tipi di regola (`lineare`: base + passo × click; `elenco`: valori[click]), stati (`gioco`, `fonti`, `DA_VERIFICARE`) e le 5 fonti con commit e licenza; `cars.bmw_m4_gt3` con i 49 parametri, ognuno con fonti e, dove serve, nota e stato proprio. Via gli override per nome di vettura e per pista (erano segnaposto senza effetto).
- `setup_params.py`: `regole_vettura(car)` (solo le regole `gioco`/`fonti`), `click_in_reale(regola, click)` (None per click negativi, non interi, oltre l'elenco o oltre `click_max`: niente numeri inventati), arrotondamento senza code di virgola mobile. `get_params_for_car` restituisce i 49 generici come prima (la pagina Setup cambia nella #058); `SETUP_SECTIONS`, `validate_setup`, `format_setup_for_prompt` non toccati.
- `acc_setup.py`: camber dal click, altezza posteriore da `rideHeight[2]`, conversione con la tabella della vettura; le assunzioni scendono a **due** (bumpstop, caster).
- `schema.py`: `ValoreSetup.fonte` («gioco» | «fonti» | None, compatibile con i bundle già salvati).
- `gigi.py`: nel contesto del setup dice che le unità reali vengono da fonti concordi, non ancora viste in gioco.
- NEW `scripts/riconverti_setup.py`: rilegge il JSON originale conservato nei bundle con la tabella di oggi (`--prova` per vedere prima; copia di backup accanto all'archivio). Lanciato: 4 sessioni riconvertite (BMW 711b: 45 valori reali; Ferrari, Audi, Honda: il camber torna in click). Demo rigenerata con `assicura_demo(forza=True)`, senza toccare `demo.py`.

**Risultato osservato:** setup BMW di Monza → pressioni 25.7/26.4/25.1/25.7 psi, camber -4.0/-3.5°, ripartizione 51.8 %, molle 120000/105000 N/m, altezze 54/50 mm, precarico 120 Nm; caster, splitter e bumpstop rate in click. Le altre vetture tutte in click. A schermo la pagina Setup non cambia ancora (è la #058).

**Verifica:** suite **1041/1041** in 20 file (1014 + 25 di `test_setup_ranges` + 2 nuovi in `test_adattatori`); riscritti i 10 test di `test_adattatori` e i 2 di `test_sessions` che fissavano il comportamento vecchio (pressioni in click, camber da `staticCamber`, tre assunzioni). `riconverti_setup.py --prova` dopo la riconversione: «nessuna sessione da riconvertire».

**File protetti:** ⚠️ sbloccati con «ok procedi» del 30/09 → `setup_params.py` e `car_setup_ranges.json`. `demo.py`, `demo_responses.py`, `agent.py`, prompt: non toccati.
**Decisione:** ☑ Mantenuto — «ok push» il 30/09 (commit `0aeca53` codice · `191b24f` docs).

---

## Entry #058 — Pagina Setup: il setup della sessione in click, frecce come in ACC, file da riportare in gioco

| Campo | Valore |
|---|---|
| Data | 30/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `frontend/src/app/(app)/setup/page.tsx` (riscritta) · `frontend/src/lib/setup.ts` · `frontend/src/lib/api.ts` · `frontend/src/app/(app)/sessioni/page.tsx` · `backend/app/api/setup.py` · `backend/app/api/sessions.py` · `backend/app/bundle/adapters/acc_setup.py` · `backend/app/main.py` (CORS) · test · docs |
| Commit | `fc38161` pagina, API e test · `97ab22c` docs |
| Contesto | Seguito della #057: la pagina Setup lavorava ancora su 49 slider con range generici in unità reali, che non erano della vettura (INC-V2-003). Ultima pagina della revisione. |

**Catalogo messaggi:**
1. «ok push, poi procedi con la #058, accendi i server dev che vorrei vedere cosa stai facendo il prima possibile.» → push della #057, server accesi, due giri di domande sullo scope.
2. Risposte (tutte le proposte): **frecce − / + come in ACC** per tutti i parametri; senza setup **invito a importarlo** (niente valori di partenza inventati); verdetto **convertito in click** dove c'è la tabella, altrove solo la direzione; **«Scarica il setup per ACC»** in questa entry; via selettori vettura/pista, schede auto/pista e **screenshot** (parcheggiato con Gigi); modifiche **nella scheda con «Ripristina»**, la sessione archiviata non cambia; via **«Crea una sessione con questo setup»**; brake power e steering ratio **non ora**.

**Modifica:**
- **Pagina Setup riscritta.** Vettura e pista sono quelle del setup della sessione aperta. Ogni parametro ha le frecce ◀ ▶ e mostra il click e, se la vettura ha la regola, il valore del gioco («54 · 25.7 psi»; una volta sola dove il gioco mostra il numero del click, «4»). Limite in alto solo dove è noto (molle), mai sotto zero. Bollino «da verificare» sui parametri che la tabella lascia in click (caster, splitter, bumpstop rate della BMW). Parametro cambiato: «era 48 · 25.1 psi · ripristina»; pallino bianco sulla tab con modifiche; contatore, «Ripristina» e «Scarica il setup per ACC ↓» accanto alle tab. Una riga dice da dove vengono i numeri (tabella da fonti concordi, non vista in gioco; o «per questa vettura non c'è ancora una tabella»). Rake solo con le due altezze in mm. Assunzioni dell'import in fondo. Senza setup: riquadro con il percorso dei file di ACC e il link a Sessioni.
- **Verdetto**: «+0.6 psi» → «+6 click (+0.6 psi)», un clic lo applica e porta al parametro; senza regola «… senza tabella, solo la direzione».
- `lib/setup.ts`: tipo `Regola` (lineare | elenco), `reale`, `clickMax`, `formatReale`, `clickDaVariazione` (stessa conversione del backend); via `formatValue`, `CHIAVE_BOZZA_SETUP` e i min/max/default dal tipo `Param`.
- **Sessioni**: tolto il codice della bozza di setup (nessuno la scrive più); il riquadro della sessione manuale dice che il setup arriva dal file di ACC.
- **Backend**: `/api/setup-params` aggiunge `regola` a ogni parametro (`regole_vettura`, nessun file protetto toccato); NEW `POST /api/sessions/{id}/export/setup` (file originale con i click nuovi, nome ASCII «<setup> PitWall.json»; 409 senza file originale, 422 su click non valido o parametro sconosciuto); `acc_setup.applica_click` scrive i click nel punto del file e sposta della stessa quantità il gemello per i parametri tenuti per asse (molle, bumpstop, caster destro); `main.py` espone `Content-Disposition` al browser.

**Risultato osservato** (1536×639, demo BMW Monza): riga «45 parametri su 49»; verdetto «Pressione RL +6 click (+0.6 psi)» · «Pressione RR +8 click (+0.8 psi)»; il clic su RL porta 48 → 54 click (25.1 → 25.7 psi) con «era 48 · 25.1 psi · ripristina» e «1 modifica»; caster «23 click · da verificare»; aerodinamica 55/50 mm, rake −5 mm, splitter da verificare. Export provato dall'API: pressioni `[54, 61, 54, 54]`, resto del file identico. Nota: con la scheda di Chrome in secondo piano le animazioni del cambio tab restano ferme (il DOM cambia): è il browser di prova, non la pagina.

**Verifica:** `tsc --noEmit` 0 errori · rotte `/ /setup /sessioni /telemetry /console` 200 · suite **1060/1060** (+11 `test_sessions`: regole in `/api/setup-params`, export, errori 409/422/404, CORS; +8 `test_adattatori`: `applica_click`).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 30/09 (commit `fc38161` · `97ab22c` docs).

---

## Entry #059 — Il debrief di Gigi fase per fase (motore)

| Campo | Valore |
|---|---|
| Data | 30/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | NEW `backend/app/analisi/debrief.py` · `backend/app/bundle/schema.py` (`fasi_tagli`) · `backend/app/api/sessions.py` (2 rotte) · NEW `backend/app/tests/test_debrief.py` · docs |
| Commit | `5ba9b01` motore, rotte e test · `7de3b6a` docs |
| Contesto | Prima delle tre entry della nuova Engineer Console (#059 motore · #060 Console · #061 chat di Gigi). |

**Catalogo messaggi:**
1. «ora vorrei cambiare l'aspetto dell'engineer console che mi sembra un po' datata, sono aperto a proposte» + la chat di Gigi come fase successiva → domande (chat spenta senza modello con domande preparate; fuori tema con una regola nel prompt; 12 messaggi, ultimi 8 al modello) e tre concetti visivi in una pagina privata (A una cosa alla volta · B radio del muretto · C il tavolo del debrief).
2. «mix tra b e c perché il team radio è geniale mentre tutta la sezione di debrief ti va a spiegare […] come un ingegnere tutti i passi che hai fatto nel corso dei giri e delle sessioni, dove hai sbagliato […] fai in modo che ci entri anche l'opzione a» → tavola D; poi lo spettro audio della B, la mappa vera, l'onda che si muove, la striscia dei giri, il passaggio fra le fasi, «Riascolta il debrief», «In ballo», i tasti sistemati.
3. «ok va bene così, ora iniziamo a costruire su pitwall.» → ultime domande: fasi = quelle di Gigi **più** il ritaglio a mano (clic fra i giri), salvato nella sessione; le 5 sezioni dentro la radio + «Rapporto completo»; più sessioni dopo; tre entry.

**Modifica:**
- NEW `analisi/debrief.py`: `debrief(report, tagli)` → le fasi sui giri di ritmo. Tagli automatici al giro migliore e al successivo: **L'avvio** · **Il giro** · **Il calo** (degrado dimostrato dal motore) o **La tenuta**. A mano, ogni fase prende il tipo dalla sua posizione rispetto al migliore; due fasi dello stesso tipo si chiamano con i giri («Il calo · G5–6»). Per ogni fase: scarto medio dal migliore, le curve dove si perde (media ≥ 50 ms sui suoi giri, «il grosso» solo se la fase si prende più della sua parte), le gomme fuori dalla finestra Kunos nei suoi giri (non nell'avvio: le gomme stanno salendo), il messaggio di Gigi, la prova in piccolo e gli **argomenti** per gli agganci (ritmo, curva:N, settore:N, gomme). Nomi e punti sulla mappa dall'aggancio della guida, come il pannello «La pista». In più: striscia dei giri con lo scarto, giri fuori ritmo, **in ballo** (media − migliore), **prima cosa da fare** (la voce più grave che tocca il setup). Centesimi arrotondati per eccesso sulla metà (155 ms → 0.16 s).
- `SessionBundle.fasi_tagli` (None = fasi di Gigi).
- `GET /api/sessions/{id}/debrief` (tagli salvati che non valgono più → fasi di Gigi con una nota, mai un errore) e `PUT /api/sessions/{id}/debrief/tagli` (422 tagli non validi, 503 con le scritture spente come gli import).

**Risultato osservato:** demo → «Nei primi 3 giri sei a +0.73 s dal tuo migliore. Il grosso lo lasci in curva 1» · «Questo è il giro: 1:47.820, il 4. A 10 millesimi dal teorico: l'hai messo insieme tutto.» · «Da qui cedi 352 millesimi a giro. Il grosso lo lasci in curva 7 […] la Post.DX arriva a 105 °C.»; in ballo 684 ms. Ferrari a Monza (giri 1-2 e 7 fuori ritmo, migliore all'ultimo) → «Nei 5 giri prima del migliore sei a +0.42 s in media. Dove perdi di più: T8-T10 Variante Ascari» + «Il giro». Honda a Zandvoort → avvio · il giro · «Giro 6: +0.74 s […] Tutte e quattro sopra la finestra (27.6–27.8 psi).»

**Verifica:** suite **1097/1097** (+37 `test_debrief`); rotte provate sul backend vivo.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» il 30/09 (commit `5ba9b01` · `7de3b6a` docs).

---

## Entry #060 — Engineer Console: Gigi alla radio del muretto

| Campo | Valore |
|---|---|
| Data | 30/09/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `frontend/src/app/(app)/console/page.tsx` (riscritta) · NEW `frontend/src/components/console/` (`Onda`, `StrisciaGiri`, `MappaFase`, `Radio`, `RapportoCompleto`) · NEW `frontend/src/lib/debrief.ts` · `lib/api.ts` · `lib/console.ts` · `app/globals.css` · `components/ui/GigiTour.tsx` · `backend/app/analisi/debrief.py` (`stato_gomme`) · `test_debrief.py` · docs |
| Commit | `366a2d6` (console e motore) + commit docs, pushati l'01/10/2026 |
| Contesto | Seconda delle tre entry della nuova Console: la tavola D scelta da Edoardo (radio + debrief + una cosa alla volta) costruita dentro PitWall sul debrief della #059. |

**Catalogo messaggi:**
1. «ok push, poi procedi con la #060».
2. «ok devo dire molto meglio però forse è meglio pulire la schermata, mi sembra un po' troppo piena e confusionaria» → sei fonti di rumore proposte; «mi piace molto la schermata ma la ritengo troppo piena. vedi te altri fix» → pulizia (sotto). La mappa nella colonna di sinistra resta: l'aveva scelta Edoardo il 29/09 perché la colonna era «troppo vuota».
3. (01/10) «mi sembra una schermata troppo piena di informazioni e l'utente medio penso che non possa capire bene tutto» (guardata su demo e Monza · Ferrari 488) → una cosa alla volta (sotto). La #060 si pusha a rifinitura finita.
4. (01/10) «lì va bene metterci la chat con gigi come avevamo già fatto e va bene lo spazio vuoto a sinistra ma rendiamolo migliore, meglio sopra il punto, era meglio il distacco messo come prima […] rendiamolo più appetibile» → scelte: conversazione + casella, «la sessione in numeri» a sinistra, la conversazione resta al cambio di fase.

**Modifica:**
- **La pagina.** In testa «GIGI · RADIO» con la cuffia, la sessione, **In ballo** (media − migliore, in ambra), lo stato di Gigi dal vivo e il pulsante **Rapporto completo**. A sinistra la **striscia dei giri** e la **pista della fase**; a destra **la prima cosa da fare** e **la radio**. Tarata sull'area contenuti del tuo schermo (1152 × ~575 px): la pagina non scorre, scorre solo la radio.
- **Striscia dei giri** (`StrisciaGiri`): le fasi come intestazioni cliccabili (colore per tipo: avvio grigio, il giro viola, il calo rosso, la tenuta verde), i giri con lo scarto dal migliore (il migliore in viola con il tempo), una **fessura fra due giri**: clic = taglia una fase nuova o unisce (salvato nella sessione), «Torna alle fasi di Gigi». **▶ Riascolta il debrief** fa scorrere le fasi ogni 4.5 s.
- **Pista della fase** (`MappaFase`): la mappa verificata con i punti della fase quando la pista è agganciata alla guida (primo punto rosso che pulsa); altrimenti «Dove perdi in questa fase» in elenco. Le quattro gomme colorate con lo stato del motore (in finestra · bassa · alta · oltre i 100 °C). Mappa non verificata: lo dice.
- **Radio** (`Radio`): un messaggio di Gigi per fase, con la prova in piccolo; quello della fase ascoltata è **in onda** (onda rossa che si muove, riquadro acceso, link alle altre sezioni: Telemetria su Giri/Curve/Gomme e freni, lezione sulla finestra gomme). Le tue domande con la loro onda grigia. **Domande preparate** che il debrief sa rispondere da solo: La prossima · Perché? · Dove perdo? · E le gomme? · Il giro migliore? — ognuna porta anche la striscia e la mappa sulla fase di cui parla. La casella resta spenta finché non c'è Gigi dal vivo (#061).
- **La prima cosa da fare**: la voce più grave che tocca il setup, detta in click con la tabella della vettura («Alza le pressioni: Post.SX +6 · Post.DX +8 click»), in psi dove la tabella non c'è; «Nel setup →».
- **Rapporto completo** (`RapportoCompleto`, pannello a destra in un portale): le 5 sezioni di sempre, dalla stessa rotta (cache sulla demo, motore altrove).
- `lib/debrief.ts`: agganci dagli argomenti, barre dell'onda deterministiche, titolo della prima cosa, risposte preparate, taglio sì/no. Via gli scenari rapidi (`CHIPS`). Onda animata in `globals.css` (ferma con «riduci movimento»). Tour: nuova frase sulla Console.
- **Backend**: ogni fase porta `stato_gomme` per ruota (ok · bassa · alta · calda, stesse finestre Kunos del messaggio; niente nell'avvio, sul bagnato o senza canali): i conti restano nel motore.

**Pulizia (messaggio 2):** testata con solo «In ballo 0.684 s a giro» (media e migliore nel tooltip) e «Rapporto completo», lo stato dal vivo lo dice la casella della radio; via la riga d'istruzioni sotto la striscia (nel tooltip; resta «Fasi tagliate da te · torna a quelle di Gigi» solo dopo un taglio) e le fessure fra i giri si vedono solo passandoci sopra; la prima cosa da fare su una riga (il titolo della voce nel tooltip); nella radio la prova solo sul messaggio in onda, gli altri al massimo su due righe; sulla mappa un solo riquadro nell'angolo vuoto con gomme e «dove perdi».

**Una cosa alla volta (messaggio 3, 01/10):** la stessa cosa era detta quattro volte (colonna di sinistra, mappa, messaggio, riga di prova) e con numeri diversi fra sessione e fase. Ora: alla radio **un solo messaggio**, quello della fase in onda o la risposta all'ultima domanda («Mi hai chiesto: …»), con le domande subito sotto; la **prova** esce solo con «Perché?»; casella e microfono nascosti finché non c'è Gigi dal vivo (#061; via anche la lettura dello stato del backend dalla pagina); sulla mappa il **nome solo sul punto peggiore**, gli altri pallini numerati con il nome nel tooltip (senza punti sulla mappa: una riga «Perdi di più»); nella striscia scritto solo il tempo del giro migliore, gli altri «G3» con tempo e scarto nel tooltip; in testata «Hai 0.35 s a giro di margine» al posto di «In ballo»; `Sidebar`: il pannello della pista **non compare sulla Console** (sulle altre pagine resta). Scelte di Edoardo: un messaggio, un punto con nome, pannello nascosto sulla Console; il resto «vedi tu». Verificato a 1536×695 su demo e Monza · Ferrari 488 («Perché?» compreso); `tsc` 0, rotte 200; backend non toccato.

**Rifinitura (messaggio 4, 01/10):** sotto le domande torna la **conversazione** (domande tue e risposte di Gigi accodate, restano al cambio di fase; il messaggio in onda in alto è sempre quello della fase) e in fondo la **casella** con il microfono, spenta fino alla #061; l'etichetta del punto peggiore sta **sopra il punto** (sotto se è in cima alla mappa, allineata al bordo vicino ai lati); in testata torna il **Distacco** come numero ambra in un riquadro («Distacco · media · giro migliore · +0.349 s a giro»), al posto di «di margine»; nella colonna di sinistra, solo sulla Console, NEW `components/ui/PannelloSessione.tsx`: giro migliore, media, giri di ritmo (questi dal debrief). Verificato a 1536×695 su Monza · Ferrari 488 con tre domande: la pagina non scorre, scorre la conversazione; `tsc` 0.

**Colonna piena (messaggio 5, 01/10):** «rimane lo spazio vuoto nella colonna di sinistra» → `PannelloSessione` riempito di contenuto fino in fondo: due riquadri (Migliore, Media) e sotto i **giri di ritmo uno per uno** con tempo e scarto (il migliore in viola), che sulla striscia sono solo barre; le righe si spartiscono l'altezza (ResizeObserver, come `PannelloPista`). Verificato a 1536×695: 6 giri sulla Ferrari, 8 sulla demo, tutti dentro, senza vuoto sotto. Scartata la riga «Costanza»: sulla Ferrari dà ± 8.243 s (deviazione su tutti i giri, non solo quelli di ritmo), accanto alla media di ritmo confonde. `tsc` 0.

**Risultato osservato** (1536×639, demo, prima del messaggio 3): In ballo 0.684 s; fasi L'avvio · Il giro · Il calo con gli scarti; in onda il calo con l'onda rossa; mappa di Monza con «Dove perdi in questa fase» (la demo non è agganciata); gomme «Post.SX pressione bassa · Post.DX oltre i 100 °C al core»; «Dove perdo?» risponde e porta la fase all'avvio; il taglio fra G6 e G7 dà «Il calo · G5–6» e «Il calo · G7–8» (poi rimesse le fasi di Gigi). Nota: con la scheda di Chrome in secondo piano le animazioni si fermano a metà nelle catture (la pagina è a posto).

**Verifica:** `tsc --noEmit` 0 errori · rotte `/ /console /setup /telemetry` 200 · suite **1099/1099** (+2 `test_debrief` sullo stato delle gomme).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» dell'01/10/2026.

---

## Entry #061 — Gigi dal vivo alla radio (chat)

| Campo | Valore |
|---|---|
| Data | 01/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | NEW `backend/app/api/chat.py` · `analisi/gigi.py` (`contesto_chat`) · `config.py` (`chat_live`) · `budget.py` (`regge`) · `main.py` · NEW `app/tests/test_chat.py` · `frontend`: `console/page.tsx`, `components/console/Radio.tsx`, `lib/api.ts`, `lib/debrief.ts` |
| Commit | `b5c7967` (chat) + commit docs, pushati l'01/10/2026 |
| Contesto | Terza entry della nuova Console: la casella della radio scrive al modello. |

**Catalogo messaggi:**
1. «ok iniziamo con la #061» → giro di domande. Scelte di Edoardo: **interruttore solo per la chat**; tetto **$0,10 al giorno**; contesto **tutto** (report, setup, debrief, fase); **microfono tolto per ora**. Già decisi il 30/09: 12 domande a conversazione, ultimi 8 messaggi al modello, 800 token, fuori tema = regola nel prompt (protetto).

2. «ok procedi, modificato il .env» → prompt della chat sbloccato. Nel `.env` le modifiche erano finite su altre righe (`ALLOW_LIVE=1`, tetto dell'analisi «o.10»): segnalato, nessuna prova.
3. «ok no avevo sbagliato, riprova ed ok procedi. ho sistemato il valore» → `.env` sistemato da me su tre righe (`PITWALL_ALLOW_LIVE=0`, `PITWALL_CHAT_LIVE=1`, `PITWALL_BUDGET_CHAT_GIORNO=0.10`; il tetto dell'analisi resta a 0.10 come l'ha lasciato lui), copia di prima in scratchpad, chiave mai stampata. Poi la prova vera.

4. «ok push ed ok procedi, dobbiamo essere precisi con le analisi e queste banalità non sono ammesse. in caso cambiamo il modello e mettiamo quello di haiku più recente» → blocco PRECISIONE nel prompt (sotto). Il modello resta `claude-haiku-4-5`: è già l'Haiku più recente.

**Modifica:**
- **Rotta** `POST /api/sessions/{id}/chat`: risposta in streaming (testo semplice) da `agent.chat_with_gigi`, che non è stato toccato. 503 chat spenta o senza chiave · 429 tetto finito · 409 conversazione piena · 422 domanda oltre 1000 caratteri o ultimo messaggio non del pilota. Nel log solo lunghezze.
- **Interruttore** `PITWALL_CHAT_LIVE=1` (`config.chat_live`): accende solo la chat; Rapporto completo e screenshot restano in demo-mode. `GET /` porta `chat_live` (interruttore e chiave).
- **Contesto** (`contesto_chat`): report del motore, setup, racconto, profilo, le fasi del debrief con messaggio e prova, distacco, prima cosa da fare, la fase in ascolto, e quanto vale un click per la vettura (o «nessuna tabella: unità reali»).
- **Tetto**: `budget.regge()` controlla il costo massimo PRIMA dello streaming. Senza, a tetto quasi finito `agent.py` avrebbe risposto «problema di collegamento, controlla la API key» con un 200 (trovato dal test C16).
- **Console**: la casella scrive a Gigi (Invio o freccia), contatore «2/12», risposta che arriva pezzo per pezzo con l'etichetta «GIGI · DAL VIVO»; al modello va solo la conversazione dal vivo (le risposte preparate vengono dal debrief, già nel contesto); a conversazione piena «Nuova conversazione»; errori in ambra nella conversazione, e lo scambio fallito non conta. Senza chat la casella resta spenta, com'era. Via il microfono.

- **Prompt della chat** (protetto, «ok procedi» dell'01/10): blocco PERIMETRO (fuori tema = una frase e si torna alla sessione), correzioni di setup in click quando c'è la tabella, rimando al «Rapporto completo», riga su [DEBRIEF] e [FASE IN ASCOLTO].
- **Dalla prova vera**: senza tabella dei click il modello scriveva «da 48 a circa 48.2 click» (sommava psi ai click grezzi del setup) → il blocco [CLICK DELLA VETTURA] ora dice che quei valori sono click e che la correzione va data solo in unità reali; le risposte arrivano con grassetti ed elenchi → nella radio passano dallo stesso markdown-lite del Rapporto completo (`SectionBody` esportato).

**Prova col modello vero (01/10, claude-haiku-4-5, 5 domande, $0,0229 = ~$0,0046 a domanda):** primo pezzo in 1,5–5 s, risposta completa in 2–7 s. Ferrari Monza: guida sulla Variante Ascari con i numeri del report (0.19 s, v-min 139 km/h); fuori tema («mondiale 2006») rifiutato in una frase; pressioni dopo la correzione: «+0.2 psi Ant.SX, +0.3 psi Post.SX», e dice di non avere la tabella dei click. Demo BMW: «Post.SX +6 click, Post.DX +8 click», gli stessi della prima cosa da fare. Da tenere d'occhio: sulla demo ha detto «95 °C, sopra il limite» (95 è la media, la finestra arriva a 100; il fuori finestra è il 38% del tempo) e qualche espressione storta («butta giù il freno», «centralizza l'Ascari»). Non ancora vista a schermo col modello vero: lo streaming a schermo è stato visto solo col modello finto.

**Precisione (messaggio 4):** nel prompt della chat il blocco PRECISIONE: media, picco e percentuale di tempo non si scambiano; prima di dire «sopra/sotto/fuori» si confrontano i due numeri; le correzioni sono SOLO quelle delle «azione» del verdetto e della prima cosa da fare (stessi parametri, stesse quantità); su ciò che il contesto non dice si risponde «i dati di questa sessione non lo dimostrano»; italiano corretto, niente gergo inventato né vezzeggiativi. Prima della regola sulle correzioni haiku aveva inventato «rebound Post.DX +2 click (da 24 a 26)» con una causa sua. Dopo, sulle stesse domande della demo: pressioni +6 / +8 click e basta; «media 95 °C, il 38% del tempo sopra i 100 °C, picchi fino a 105 °C»; alla domanda su ammortizzatori e ala «i dati di questa sessione non lo dimostrano». Restano modi colloquiali («scalda come un forno»). Spesa della giornata dopo 12 domande vere: $0,0621 (~$0,006 l'una col prompt più lungo).

**Verifica:** `test_chat.py` **25/25** (modello finto, nessuna spesa) · suite **1124/1124** in 22 file · `tsc --noEmit` 0 · a schermo (1536×695, Monza · Ferrari 488) con un backend di prova a modello finto: due domande, streaming, storia al modello (1 poi 3 messaggi), contatore 2/12, la pagina non scorre. 

**File protetti:** ☑ sbloccato con «ok procedi» → `core/prompts/chat_system_prompt.txt` (solo le quattro modifiche concordate). `agent.py` non toccato.
**Decisione:** ☑ Mantenuto — «ok push» dell'01/10/2026.

---

## Entry #062 — Numeri sospetti: da dove viene ogni numero che Gigi legge

| Campo | Valore |
|---|---|
| Data | 01/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `backend/app/analisi/gigi.py` (contesto) · `app/tests/test_chat.py` · `frontend/src/components/charts/GiriSessione.tsx` |
| Commit | `e7637b9` + commit docs, pushati l'01/10/2026 |
| Contesto | Dopo la #061 Edoardo: «dobbiamo essere precisi con le analisi». Tre numeri sospetti annotati durante la #060/#061, controllati sul motore e sulle 6 sessioni dell'archivio. |

**Catalogo messaggi:**
1. «ok parti dal punto 1 poi continua con quest'ordine» (1 numeri sospetti · 2 click della Ferrari · 3 Lotto 2 · 4 guide · 5 Console parcheggiate · 6 fuori dal codice · 7 deploy).

**Esito del controllo:**
- **Costanza «± 8.243 s» sulla Ferrari a Monza: falso allarme mio.** Il motore dà 243 ms sui 6 giri di ritmo (`_costanza` lavora già sui soli giri di ritmo); avevo letto male «0.243» in una cattura rimpicciolita. Nessuna modifica.
- **Carburante 3.10 l uguale in tutti i giri: non è un errore di calcolo, è la fonte.** Nelle sessioni MoTeC il consumo è `fuelPerLap` del setup di ACC (fonte «setup»), lo stesso numero su ogni giro. La Dashboard lo dichiarava già («dal setup»); non lo dichiaravano la tabella dei giri in Telemetria e il contesto di Gigi, che diceva «consumo 3.1 l/giro su 8 giri» come fosse una misura.
- **«sessione ?»**: i file MoTeC non dicono che sessione era; al modello arrivava il punto interrogativo.

**Modifica:**
- `gigi.py`: il consumo porta la sua fonte («misurato su N giri» · «stima salvata da ACC nel setup, NON una misura» · «media dai litri scritti dal pilota, NON misurata giro per giro»); tipo sconosciuto → «tipo di sessione non indicato». Vale per la chat e per l'analisi a 5 sezioni (stesso blocco).
- `GiriSessione.tsx`: colonna «Carburante · dal setup» (o «· inserito da te») e una riga sotto la tabella che dice che non è misurato.
- Il motore e la logica del carburante non sono stati toccati.

**Verifica:** `test_chat` **29/29** (+4 sul contesto) · `test_gigi` 36/36 · `test_analisi` 61/61 · `test_analisi_l4` 46/46 · `test_demo` 38/38 · `tsc --noEmit` 0. Non vista a schermo.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» dell'01/10/2026.

---

## Entry #063 — Click della Ferrari 488 GT3 Evo (INC-V2-003, seconda vettura)

| Campo | Valore |
|---|---|
| Data | 01/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `backend/app/core/data/car_setup_ranges.json` (protetto) · `app/tests/test_setup_ranges.py` · `INCIDENTS.md` · `docs/03` · archivio: sessione Ferrari riconvertita |
| Commit | `8a276c8` + commit docs, pushati l'01/10/2026 |
| Contesto | Punto 2 dell'ordine dell'01/10: senza tabella, sulla Ferrari (la sessione di riferimento di Edoardo) Console e chat restavano in psi. |

**Catalogo messaggi:**
1. «ok push e ok procedi, va bene la 3» → push della #062, file protetto sbloccato, stato «da fonti, non visto in gioco» accettato anche per la Ferrari.

**Fonti lette l'01/10/2026:** Race Element `Cars/GT3/Ferrari488GT3evo.cs` (RE), acc-setup-diff `CarData.js` + `App.js` (ASD), acc-setup-comparison `setup.py` (SIMSOURCE). Regola della #057: un valore si usa se almeno due fonti indipendenti concordano.

**Modifica:**
- Voce `ferrari_488_gt3_evo` nella tabella, **43 parametri su 49** usabili: pressioni 20.3 + 0.1 psi · convergenza −0.4 + 0.01° su tutte e quattro · ripartizione 47.0 + 0.2 % · molle (11 valori per asse: ant. 94–189, post. 106–212 kN/m) · bumpstop rate 300 + 100 N · altezze 55 mm + click · precarico 20 + 10 Nm · TC, ABS, barre, bumpstop range, ammortizzatori, ala e prese freni = il click (mappa motore = click + 1).
- Restano in click: **camber** (solo RE dà una regola), **caster** (RE un elenco di 99 valori, ASD e simsource una retta: coincidono agli estremi, non in mezzo), **splitter** (RE il click, ASD il click + 1).
- La voce è stata generata dalla voce BMW (stesse 49 chiavi, stesso ordine) da uno script che prima verifica di saper riscrivere il file identico: il diff sono 691 righe aggiunte e nessuna tolta.
- `riconverti_setup.py`: 1 sessione riconvertita (Monza · Ferrari 488, 43 valori), copia in `_backup_riconversione/20261001-154559`.

**Risultato osservato:** `/api/setup-params?car=ferrari_488_gt3_evo` porta 43 regole; il setup di Monza si legge 25.1 / 26.0 / 25.3 / 25.9 psi a freddo, ripartizione 57 %, molle 176000 / 134000 N/m. Gigi dal vivo, alla domanda «per le pressioni quanti click?»: «Ant.SX +0.2 psi = +2 click, Post.SX +0.3 psi = +3 click, da 25.1 a 25.3 e da 25.3 a 25.6 psi a freddo» (una domanda vera, $0,005). La «prima cosa da fare» della Console usa la stessa regola (0.2 e 0.3 psi con click da 0.1): non vista a schermo.

**Verifica:** `test_setup_ranges` **40/40** (+8 dal ciclo sulle vetture, +7 sulla Ferrari) · suite **1143/1143** in 22 file · frontend non toccato.

**File protetti:** ☑ sbloccato con «ok procedi» → `data/car_setup_ranges.json` (solo la voce nuova; BMW e `_meta` identici).
**Decisione:** ☑ Mantenuto — «ok push» dell'01/10/2026.

---

## Entry #064 — Lotto 2: le 23 vetture non GT3 nel catalogo

| Campo | Valore |
|---|---|
| Data | 01/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `backend/app/core/data/cars.json` · `acc_lista_vetture_handbook.json` · `acc_riferimenti_vetture.json` · NEW `backend/scripts/consegne/lotto_2_vetture.py` · NEW `backend/scripts/build_photos_proof.py` · `core/catalog.py` (commento) · `app/tests/test_riferimenti.py` · `frontend`: `sessioni/page.tsx`, `lib/catalog.ts` · docs |
| Commit | `3c48d0f` + commit docs, pushati l'01/10/2026 |
| Contesto | Punto 3 dell'ordine dell'01/10. Il Lotto 1 aveva portato le 31 GT3; restavano 11 GT4, 6 GT2, 5 monomarca (GTC) e la BMW M2 CS Racing (TCX). |

**Catalogo messaggi:**
1. «1 falla te la ricerca, è più comodo. 2 va bene. 3 va bene. ok push ed ok procedi» → ricerca fatta da me (non da Claude Desktop), schede complete come le GT3, foto con provino mio e scelta a occhio di Edoardo. («ok push» era per la #063.)

2. «ok fatto il json, ok procedi» → `photos_lotto2.json` dai Download: 23 foto scelte su 23, nessuna «Nessuna adatta».

**Ricerca (01/10/2026), con le fonti scritte vettura per vettura nello script di consegna:**
- **Slug di ACC** (`acc_car_id`): Race Element, `ConversionFactory.cs` — compresi i sei delle GT2, che l'handbook di Kunos non dava.
- **Pacchetti**: GT4 Pack (15/07/2020), Challengers Pack (23/03/2022), GT2 Pack (24/01/2024); 991.2 Cup e Huracán Super Trofeo 2015 sono contenuto base.
- **Specifiche**: siti dei costruttori dove ci sono (Alpine, Audi, KTM, Porsche, McLaren), altrimenti stampa di settore e Wikipedia; tratti di guida da Coach Dave Academy, la fonte community già scelta per le guide.
- **TC e ABS in ACC**: detti solo dove una fonte lo dice — tutte le GT2 con TC e ABS; 991.2 Cup senza TC né ABS; 992 Cup senza TC, con ABS; M2 CS Racing con ABS. Le altre restano `null`: la scheda non scrive «senza TC» su una vettura di cui non sappiamo.

**Modifica:**
- `cars.json`: da 31 a **54 vetture** (GT3 31 · GT4 11 · GT2 6 · GTC 5 · TCX 1), stesso schema; in più `caption_fonte`, `fonti` e `specs.nota` sulle voci nuove. Le 31 GT3 sono identiche a prima (diff: sole aggiunte).
- **Dati lasciati vuoti apposta**: Aston Martin Vantage GT4 (potenza, peso, cambio) e McLaren 570S GT4 (potenza, peso) sono `da_verificare` — le fonti lette danno i numeri stradali o si contraddicono; peso della Huracán ST EVO2 e della Maserati MC20 GT2 non dichiarato; cambio dell'Audi R8 LMS GT2 non indicato.
- **Didascalie**: 15 con tratti di guida presi da Coach Dave Academy; 8 (Alpine, Audi GT4, Camaro, Ginetta, KTM GT4, Maserati GT4, McLaren, Huracán Super Trofeo 2015) dicono solo com'è fatta la vettura, perché nessuna fonte letta descrive come si guida in ACC.
- `acc_lista_vetture_handbook.json`: le 23 righe agganciate al catalogo (slug e id); `acc_riferimenti_vetture.json`: le 6 GT2 dichiarate senza riferimenti (il documento della shared memory si ferma alla 1.8.12).
- Selettore della vettura in «Aggiungi una sessione» raggruppato per classe (`CLASSI_VETTURE` in `lib/catalog.ts`).
- `build_photos_proof.py`: provino delle foto per le vetture senza foto. 650 candidati da Wikimedia Commons per le 23 vetture, solo licenze libere e almeno 1000 px; export `photos_lotto2.json` nello schema di `photos.json`.

**Verifica:** suite **1144/1144** in 22 file (`test_riferimenti` 74/74, +1) · `tsc --noEmit` 0 · `/api/catalog` → 54 vetture con le cinque classi · le 54 vetture si risolvono per id, slug ACC e nome (54 nomi univoci) · il provino si apre e le miniature si caricano (controllato via script: la scheda di prova di Chrome era nascosta e nelle catture risultano nere).

**Foto (messaggio 2):** le 23 voci aggiunte a `backend/scripts/photos.json` (53 → 76, formato del file invariato), poi `apply_photos.py`: 76 foto applicate, `manifest.json` 52 vetture + 24 circuiti, `ATTRIBUTIONS.md` da 78 a 101 righe — nessuna riga di prima è sparita, 23 nuove, tutte a 6 colonne; `/crediti` risponde 200 e porta le vetture nuove. Restano senza foto apposta le tre di sempre (Audi R8 LMS Evo II GT3, Reiter R-EX, Valencia). **Maserati MC20 GT2 corretta al ricontrollo (messaggio 3):** la foto scelta era la **GT2 Stradale**, cioè la versione stradale (lo diceva la targhetta). Fra i 25 candidati l'unica vettura da corsa è «Maserati GT2 (55054641642)» (LP Racing · apm Monaco, esposta a un salone, pannello «Maserati Corse GT2», CC BY-SA 4.0, Alexandre Prevot): sostituita in `photos.json` e riapplicata. Nota per il futuro: `apply_photos.py --only <id>` riscrive `ATTRIBUTIONS.md` con le sole righe di quella vettura (101 → 26, in silenzio): per cambiare una foto si rilancia il giro intero (confronto riga per riga: cambia solo la riga della Maserati).

**Aperto:** i **ritagli** delle 23 foto nuove (`build_crop_tool.py` → `/assets/_ritaglio.html`, export `crops.json`): senza ritaglio la foto si vede centrata. Nota vecchia riemersa: il nome a schermo «Mercedes-AMG AMG GT3/GT4/GT2» ripete «AMG» (era già così per le GT3).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» dell'01/10/2026; i ritagli delle 23 foto restano a parte.

---

## Entry #065 — Spa: la numerazione di Coach Dave

| Campo | Valore |
|---|---|
| Data | 01/10/2026 |
| Agente dev | Claude Code (claude-sonnet-5-5) |
| Area | `backend/app/core/data/tracks_knowledge/spa_francorchamps.json` · `app/tests/test_tracciati.py` |
| Commit | `d5687eb` + commit docs, pushati il 02/10/2026 |
| Contesto | Punto 4 dell'ordine dell'01/10 (guide dei tracciati): prima di aprire altri circuiti, la numerazione di Spa rimandata dal 23/09. |

**Catalogo messaggi:**
1. «ok push, la maserati la ricontrolliamo adesso, i ritagli dopo» → push del Lotto 2 (`3c48d0f` · `e9a5c99`) e Maserati sostituita.
2. Domande sulle guide (scelte di Edoardo): **guide «leggere» dai fatti** per i circuiti senza fonte scritta per ACC (curve, nomi, sensi, settori, record, tempi; nessun consiglio di guida inventato) · **Spa prima**.

**Scoperta preliminare:** su 12 circuiti senza guida, **solo Oulton Park** ha una guida scritta di Coach Dave; Traxion (Kyalami, Red Bull Ring, Watkins Glen, Indianapolis, COTA…) pubblica video con due righe di introduzione (aperti Kyalami e Watkins Glen: zero curve spiegate nel testo).

**Spa — cosa c'era di sbagliato** (Coach Dave, 19 curve): T2-T4 Eau Rouge e Raidillon · T5-T7 Les Combes · T8 Bruxelles (ex Rivage) · T9 senza nome · T10-T11 Pouhon · T12-T13 Fagnes · T14 Campus · **T15 Courbe Paul Frère** · **T16-T17 Blanchimont** · **T18-T19 Bus Stop**.
- La guida aveva Blanchimont come una sola curva (T16), la Bus Stop a T17-T18 e una **«T19» in più** (una destra «prima del traguardo») che nello schema di Coach Dave non esiste.
- T15 si chiamava «Stavelot»: per Coach Dave Stavelot è il vecchio nome di Campus (T14), e T15 è la Courbe Paul Frère. Wikipedia usa «Stavelot» solo come luogo e non numera le curve, quindi non arbitra; la mappa di Spa nel repo è un contorno senza numeri.
- T8 si chiamava «Rivage»: Coach Dave dice «Bruxelles, formerly Rivage».
- Una frase di pista metteva Blanchimont (una sinistra) fra le curve che caricano il lato sinistro: è il destro, come dice già la sua scheda.

**Modifica:** nuova T17 (Blanchimont, seconda parte) con soli fatti di Coach Dave (apice tardo, astroturf in ingresso, niente cordolo interno, track limits in uscita); Bus Stop passata a T18 (destra) e T19 (sinistra); tolta la «T19»; T15 → «Courbe Paul Frère»; T8 → «Bruxelles»; 14 frasi con i nomi aggiornati (settori, track limits, traffico, meteo di notte, gomme e freni della pista). Il verso di ogni curva è verificato sul percorso della mappa (Blanchimont = la lunga sinistra prima della chicane; Bus Stop = destra-sinistra, come dice Coach Dave). Restano «mestiere» le marce e il resto del contenuto delle altre curve (come prima).

**Verifica:** `check_track_knowledge.py --solo spa_francorchamps` → nessun errore (una sola voce «da controllare»: rettilineo da fonte singola, già a vista) · `test_tracciati` **103/103** (+4 che bloccano numerazione, nomi e sensi di Spa).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» del 02/10/2026.

---

## Entry #066 — Oulton Park: la guida da Coach Dave

| Campo | Valore |
|---|---|
| Data | 01/10/2026 |
| Agente dev | Claude Code (claude-sonnet-5-5) |
| Area | NEW `backend/app/core/data/tracks_knowledge/oulton_park.json` · `data/tracks.json` (Oulton Park) · docs |
| Commit | `0c83800` + commit docs, pushati il 02/10/2026 |
| Contesto | Punto 4, primo circuito nuovo dopo Spa. Oulton Park è l'unico dei 12 senza guida che ha una guida scritta di Coach Dave. |

**Catalogo messaggi:** «continua con quest'ordine» (stesso filone della #065).

**Guida (14ª su 25):** 17 curve, tutte con nome e senso, dal testo di Coach Dave: T1 Old Hall · T2 Denton's · T3 Cascades · T4 Island Bend · T5 Shell Oils · T6-T9 Britten's (destra, sinistra, destra, sinistra) · T10-T11 Hislop's · T12 Knickerbrook · T13 Clay Hill · T14 Water Tower · T15 Druids · T16 Lodge Corner · T17 Deer Leap. Dove Coach Dave dà un riferimento lo riporto com'è (la linea bianca che finisce a Old Hall, l'avvallamento di Cascades, il primo blocco arancione di Shell Oils, la macchia di cemento di Britten's, il casotto verde di Hislop's, il cartello bianco di Lodge Corner), con le marce che dice lui.
- **Campi vuoti apposta** (nessuna fonte consultata li dà): `dislivello_m`, `rettilineo_piu_lungo_m`, lato dei box, tempo perso ai box, consumo per giro, meteo, traffico; il rischio dei limiti di pista su 9 curve dove Coach Dave non dice niente. La nota di ognuno dice perché.
- **Senso di marcia «orario»**: nessuna fonte consultata lo scrive in chiaro; è ricavato dalla descrizione di Coach Dave (le curve grandi sono a destra: Old Hall, tornante di Shell Oils di 180°, Lodge di 90°) e dichiarato come tale nella nota, da confermare in gioco.
- **Sorpasso**: una sola curva, Lodge Corner (T16), perché Coach Dave dice che il rettilineo dopo Druids è «uno dei pochi punti di sorpasso»; sulle altre non dice niente e resta «no».
- **Tempo di riferimento GT3**: 1:35.0 (Pro/Am di Traxion; Pro 1:31.60, Am 1:40.00), con la fonte accanto.
- Le due chicche vengono da Wikipedia (la chicane di Hislop's dopo la morte di Paul Warwick nel 1991; il paragone con la Nordschleife).

**Catalogo corretto** (`tracks.json`): Oulton Park da **16 a 17 curve**, confidenza «alta»: Coach Dave ne numera 17 e Wikipedia dà 17 nella scheda. La lunghezza resta 4,332 km: la scheda di Wikipedia scrive 4,307 km ma il testo dice 2,692 miglia, che sono 4,332 km.

**Verifica:** `check_track_knowledge.py` → nessun errore (9 voci «da controllare»: i limiti di pista senza fonte) · `test_tracciati` **107/107** · scheda `/tracciati/oulton_park` guardata a 1536×639 dopo il riavvio del backend (che tiene catalogo e guide in cache): 17 curve, senso orario, riga «in ACC». Mappa non verificata: la scheda non la mostra, come per gli altri circuiti senza mappa scelta.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» del 02/10/2026.

---

## Entry #067 — La guida «essenziale» e Kyalami

| Campo | Valore |
|---|---|
| Data | 02/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `scripts/check_track_knowledge.py` · `core/catalog.py` · `api/catalog.py` · NEW `tracks_knowledge/kyalami.json` · NEW `scripts/sensi_da_mappa.py` · NEW `requirements-dev.txt` · `tests/test_tracciati.py` · `lib/api.ts` · `tracciati/page.tsx` · `tracciati/[id]/page.tsx` |
| Commit | `ce2a9b2` · `3db5778` + commit docs, pushati il 02/10/2026 |
| Contesto | Punto 4 dell'ordine (guide). Per i circuiti senza una guida scritta per ACC Edoardo ha scelto l'01/10 le guide «essenziali»: solo i fatti con la loro fonte, prima i circuiti che hanno già la mappa (Kyalami, Red Bull Ring). |

**Catalogo messaggi:**
1. «ok push e riprendiamo il lavoro» → push di #065 e #066 (`d5687eb` · `0c83800` · `b71b018`), poi il punto 2 della ripresa.
2. Domande: sensi del Red Bull Ring → **lettura sulla mappa** (lo strumento sugli SVG non è affidabile); `sensi_da_mappa.py` → **nel repo con la #067**, Pillow in un requirements di sviluppo.

**Due correzioni ai «fatti raccolti» dell'01/10, trovate rileggendo le fonti prima di scrivere:**
- **Mineshaft è la T11, non la T12.** Il sito ufficiale elenca i 12 nomi in ordine di percorso e numera a parte le curve senza nome: i file delle icone sono `Turn-4`, `Tun-8`, `Turn-12`, `Turn-14`, e l'icona della Mineshaft ha la didascalia «Turn 11» (il sito scambia per errore le didascalie di Mineshaft e Turn 12). La lettura dell'01/10 aveva T11 senza nome e Mineshaft al 12, come la mappa di Commons.
- **I sensi di T3 e T14 erano invertiti.** Lo strumento cercava il massimo di curvatura entro 70 px dal numero: vicino al «3» prendeva la piega di Barbeque e vicino al «14» la Cheetah. I due errori si compensavano e il conto tornava lo stesso (6 destre, 10 sinistre, come il sito ufficiale): la «validazione» dell'01/10 non valeva. Con la ricerca a 25 px ogni punto misurato cade sulla curva del suo numero (immagine `--salva-scheletro` guardata curva per curva), e coincide con la lettura a occhio delle due zone ingrandite: **T3 destra, T14 sinistra** (piega lieve).

**Modifica:**
- **Livello della guida**: campo `livello: "essenziale"` (assente = completa). Il validatore, sulle essenziali, chiede solo `id`, `verifica_catalogo`, `curve`, `fonti_curve`, `fonti`; per curva `n`, `nome` (anche null), `direzione`, `origine`, `confidence`. `tipo` null è lecito, una curva «mestiere» è un errore, e nomi e sensi devono dire da dove vengono (`fonti_curve`, stesso schema di `fonti_campi_pista`). Settori e progressione non si pretendono.
- **Catalogo/API**: bandierina `guida_essenziale` nell'indice e nella scheda (`catalog.guide_is_essential`).
- **Scheda** (`tracciati/[id]`): riquadro «Guida essenziale: solo i fatti verificati» sotto l'intestazione; le curve non si aprono (dentro non c'è niente) e sotto l'elenco ci sono le righe «Nomi · …» e «Sensi · …»; il **riferimento GT3** fra i numeri, con la fonte sotto (il riquadro promette i tempi, e la pagina finora non li mostrava per nessuna guida). **Elenco**: bandierina «guida essenziale» e «(1 essenziale)» nel sottotitolo.
- **Guida di Kyalami** (15ª su 25): antiorario; 16 curve: T1 The Kink · T2 Crowthorne · T3 Jukskei Sweep · T4 — · T5 Barbeque · T6 Sunset · T7 Clubhouse Bend · T8 — · T9 The Esses · T10 Leeukop · T11 Mineshaft · T12 — · T13 The Crocodiles · T14 — · T15 Cheetah · T16 Ingwe; sensi dx sx dx sx sx dx sx sx dx sx sx sx dx sx dx sx. Riferimento GT3 1:41.5 Pro-Am (Traxion: Pro 1:39.40, Am 1:43.50). Limite box 50 km/h. Chicca: 1.532 m di quota, larghezza media 12 m. Dislivello, rettilineo, layout ACC, lato box, consumo: vuoti con la nota del perché.
- **`sensi_da_mappa.py`**: ricerca a 25 px; nel docstring la regola «si accetta solo guardando `--salva-scheletro`» e il limite sugli SVG. **`requirements-dev.txt`** con `pillow==12.3.0` (installato nel venv; l'app non ne ha bisogno).

**Verifica:** `check_track_knowledge.py` → nessun errore · `test_tracciati` **119/119** (+12: flag nella scheda e nell'indice, 4 della guida a disco, nomi/sensi/livello di Kyalami, 4 del validatore: la guida vera passa, una curva «mestiere» e l'assenza di `fonti_curve` sono respinte, senza `livello` la stessa guida è trattata da completa e respinta) · suite **1164/1164** in 22 file · `tsc --noEmit` 0 · rotte `/tracciati`, `/tracciati/kyalami`, `/tracciati/oulton_park` 200 · a schermo nel Chrome di Edoardo (1536×639): scheda di Kyalami dall'alto in fondo, elenco con la bandierina, Oulton (guida completa) con le curve che si aprono come prima e senza riquadro. Backend riavviato.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» del 02/10/2026; con lo stesso messaggio Edoardo chiede il riferimento GT3 anche sulle guide complete (entry a parte).

---

## Entry #068 — Il riferimento GT3 su tutte le guide

| Campo | Valore |
|---|---|
| Data | 02/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `frontend/src/app/(app)/tracciati/[id]/page.tsx` · `lib/api.ts` |
| Commit | `f52b2db` + commit docs, pushati il 02/10/2026 |
| Contesto | Nella #067 il tempo di riferimento GT3 compariva solo sulle guide essenziali; le 14 complete lo avevano nei dati ma nessuna pagina lo mostrava. |

**Catalogo messaggi:**
1. «mostralo anche sulle complete. ok push ed ok procedi.» → push della #067; questo lavoro è nuovo e va col prossimo «ok push».

**Modifica:** il riferimento GT3 sta in fondo alla fila dei numeri della scheda per ogni guida che ha un valore, e sotto la descrizione la riga «Riferimento GT3 · …» dice da dove viene (dopo «fonte singola», che resta attaccata ai dati di pista). Le **stime di mestiere** (Imola 1:42, Spa 2:17: nessuna fonte, confidenza media) si leggono «Riferimento GT3 · stima» e la riga riporta anche la loro `nota` («Nessuna fonte pubblica certifica i tempi in ACC…»). Zandvoort e Zolder non hanno un valore e non mostrano niente. Tipo `GuidaValoreConFonte` con `origine`, `confidence`, `nota`.

**Verifica:** `tsc --noEmit` 0 · nel Chrome di Edoardo: Spa (stima con la nota, dopo «fonte singola»), Monza e Kyalami (con fonte), Zandvoort (nessun riferimento). Backend non toccato.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» del 02/10/2026.

---

## Entry #069 — Red Bull Ring: guida essenziale

| Campo | Valore |
|---|---|
| Data | 02/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | NEW `tracks_knowledge/red_bull_ring.json` · `data/tracks.json` (Red Bull Ring) · `tests/test_tracciati.py` · docs |
| Commit | `941dc63` + commit docs, pushati il 02/10/2026 |
| Contesto | Secondo circuito con mappa e senza guida scritta per ACC («ok procedi»). Sensi letti a occhio sulla mappa, scelta di Edoardo nella #067. |

**Fatti e fonti:**
- **Sensi**: letti sulla mappa verificata nel verso della freccia (traguardo verso ovest, orario). Nove curve si leggono chiare: destre T1, T3, T4, T5 (dentro la lunga piega fra 4 e 6), T8, T9, T10; sinistre T6, T7. La **T2** è una piega lieve sul tratto in salita (il disegno piega prima a destra e poi a sinistra, il numero sta sul flesso): la decide Wikipedia in tedesco, che cita formula1.com: «sieben Rechts- und drei Linkskurven» e «die beiden schnellen Linkskurven im Infield» → T2 **sinistra**. Il conto qui scioglie l'unica curva dubbia, non convalida le altre (la lezione della #067).
- **Nomi**: solo la **T1 «Niki Lauda»** (formula1.com, rinomina del 30/06/2019; il sito del circuito la chiama «Niki Lauda turn»). La mappa di Commons del 2021 scrive «Ams Ag» (3), «Rauch» (4), «Rindt» (9): i primi due sono sponsor e nessuna fonte di oggi li conferma, quindi restano null e la nota li riporta.
- **Pista**: orario (24hseries, «Clockwise»); 4,318 km (24hseries e catalogo; Wikipedia: stesso tracciato misurato 4,326 km dal 2025); 10 curve (Wikipedia en, formula1.com via de.wiki, mappa; 24hseries ne conta 8). Layout auto senza la chicane delle moto alla 2 (de.wiki + verifica in gioco di Edoardo del 25/09). Dislivello in metri: nessuna fonte del tracciato di oggi (i 65 m sono dell'Österreichring); le pendenze (12% e 9,3%) vanno nelle chicche.
- **Riferimento GT3 1:28.0** da Track Titan: il 5% più veloce gira in 1:27.882 (Ferrari 296), 1:27.917 (McLaren 720S Evo), 1:28.037 (BMW M4), 1:28.117 (Porsche 992); media 1:30.827 (Porsche). Traxion non ha tempi per questo circuito, Full Grip mostra Monza per ogni indirizzo, SimRacingSetup blocca i bot.
- **Catalogo**: `corners_confidence` da «media» ad «alta» (10 curve con tre fonti concordi).

**Verifica:** `check_track_knowledge.py` → nessun errore (guide mancanti 9/25) · `test_tracciati` **125/125** (+6: 4 della guida a disco, sensi e nomi del Red Bull Ring) · suite **1170/1170** · `tsc` 0 · scheda `/tracciati/red_bull_ring` nel Chrome di Edoardo dopo il riavvio del backend: riquadro essenziale, 10 curve con i sensi, righe Nomi e Sensi, riferimento 1:28.0, «10 curve» senza «da verificare».

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» del 02/10/2026.

---

## Entry #070 — Le mappe degli ultimi otto circuiti

| Campo | Valore |
|---|---|
| Data | 02/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `scripts/build_maps_proof.py` · `scripts/maps_choice.json` · `scripts/maps.json` · `data/tracks.json` · `tests/test_tracciati.py` (+ fuori repo: 8 SVG in `public/assets/tracks/`, `ATTRIBUTIONS.md`, `manifest.json`) |
| Commit | `2ea773c` · `7cc7211` + commit docs, pushati il 02/10/2026 |
| Contesto | Punto 3 della ripresa: provino delle mappe per gli 8 circuiti senza layout verificato (laguna_seca, watkins_glen, cota, indianapolis, donington_park, snetterton, valencia, mount_panorama). |

**Catalogo messaggi:**
1. «ok procedi, direi che sta andando tutto bene finora» → provino costruito.
2. «ok push, ho esportato maps_choice.json e controlla al volo i layout per vedere se risultano giusti dalle fonti come concordato in precedenza» → push di #068/#069 (`f52b2db` · `941dc63` · `b47c0f6`), controllo delle scelte, applicazione.

**Provino:** categorie Commons vere trovate per tutti e 8 («… circuit maps»; quelle del catalogo «Maps of …» non esistono). 77 candidati scritti da me con verdetto dalla sola descrizione della pagina (anno, layout dichiarato) e il layout che usa ACC in testa a ogni circuito; il provino ci aggiunge il resto delle categorie (117 in tutto).
- **Bug corretto in `build_maps_proof.py`**: la regex dei titoli escludeva le parentesi, e 6 proposte con «(…)» nel nome (fra cui la migliore di Valencia) perdevano il verdetto in silenzio, ricomparendo in fondo come «dalla categoria». Ora le parentesi sono ammesse nel nome e il titolo finisce all'estensione.

**Controllo sulle fonti delle 8 scelte di Edoardo** (la mappa dell'infobox di Wikipedia per il layout in uso + lunghezza e curve del catalogo):
- **Laguna Seca, Watkins Glen, Indianapolis, Snetterton, Valencia**: il file scelto è proprio quello dell'infobox (Laguna 1996-oggi 3,602 km/11 · Watkins Glen GP con Inner Loop 5,552/11 · Indianapolis GP Road Course 2014-oggi 3,925/14 · Snetterton 300 4,779/12 · Valencia GP 4,005/14).
- **COTA** e **Mount Panorama**: file diverso dall'infobox, stesso tracciato messo a confronto (COTA 20 curve, solo ruotato; Bathurst 23 curve con The Chase alle 20-22).
- **Donington**: layout 2010 giusto, ma la mappa scelta («Donington as of 2010.svg», che nella descrizione dice «may or may not be the current version») numerava **11** curve contro le 12 di catalogo e Wikipedia. Scelta di Edoardo: **«Donington circuit.svg»**, la mappa dell'infobox (12 curve, 4,02 km, aggiornata al 2011).

**Applicazione:** `apply_maps.py --scelte` con le sole 8 (nessun file vecchio da togliere): 8 SVG da 34 a 436 KB; `maps.json` (8 voci aggiornate), `ATTRIBUTIONS.md` e manifest rigenerati (8 righe a 6 colonne). `maps_choice.json` (lo storico versionato) da 14 a 22 scelte, nota corretta («candidato Claude Code», il provino scrive ancora «Claude Desktop»). `tracks.json`: le 8 mappe `verificata` con file e nota; la riscrittura normalizza anche il rientro di 4 righe del blocco 3 (Brands Hatch, Hungaroring, Misano, Paul Ricard: 6 spazi invece di 8). `test_tracciati`: la lista dei layout approvati passa a 22.

**Verifica:** `test_tracciati` **125/125** · suite **1170/1170** · validatore senza errori · catalogo: 22 mappe verificate, restano senza Nordschleife, Oulton Park e Suzuka · le 8 schede nel Chrome di Edoardo dopo il riavvio del backend: la mappa compare in tutte (Donington guardata a occhio; il suo SVG ha uno sfondo grigio chiaro proprio, appena diverso dall'avorio della placca).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» del 02/10/2026.

---

## Entry #071 — Guide essenziali, blocco A: Laguna Seca, Watkins Glen, COTA, Indianapolis

| Campo | Valore |
|---|---|
| Data | 02/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | NEW `tracks_knowledge/{laguna_seca,watkins_glen,cota,indianapolis}.json` · `data/tracks.json` · `tests/test_tracciati.py` · docs |
| Commit | `8c0fc7a` + commit docs, pushati il 02/10/2026 |
| Contesto | Dopo le mappe della #070, le guide essenziali degli 8 circuiti che ora le hanno, in due blocchi da quattro. |

**Catalogo messaggi:**
1. «ok push e procedi con le guide essenziali» → push della #070 (`2ea773c` · `7cc7211` · `fe5816d`), poi questo blocco. Prima del push corretto un mio errore: avevo scritto «senza mappa solo il Nordschleife», invece mancano anche Oulton Park e Suzuka (commento del test, entry #070, docs/03).

**Metodo:** sensi letti sulla mappa verificata nel verso della freccia, curva per curva, poi confrontati con le fonti scritte; nomi solo dove una fonte li dà; riferimento GT3 da Track Titan (5% più veloce con Porsche 992, Ferrari 296, McLaren 720S Evo e BMW M4; controllato che ogni pagina sia del circuito chiesto); stesse sezioni di Kyalami e Red Bull Ring.
- **Laguna Seca** (antiorario, 11 curve): il Corkscrew numerato 8-8A è **una curva sola** con senso null (gira nei due sensi, come ammette il validatore), così le curve restano 11 come il catalogo e Wikipedia. RaceControl: «11 (4 right, 7 left)» e la 1 «a fast, sweeping left-hander»; la 7, piega lieve prima del dosso, la decide il conto. Nomi da Wikipedia: Andretti Hairpin (2), Corkscrew (8; nel 2026 «Zanardi Corkscrew»), Rainey Curve (9). 1:22.4.
- **Watkins Glen** (orario, 11 curve, long course con il Boot): 7 destre e 4 sinistre; il Boot come lo descrive Wikipedia (sinistra in discesa, due destre, sinistra che rientra). Nomi: The 90 (1), **Esses alle 3 e 4** (Wikipedia e NASA Speed News; altre guide le fanno partire dalla 2, che resta senza nome), Outer Loop (5; NASA Speed News: «The Carousel»), Toe e Heel (7, 8). L'Inner Loop non ha numero. 1:43.8.
- **COTA** (antiorario, 20 curve, de.wiki e 24hseries): 9 destre e 11 sinistre, coerenti con Wikipedia (2 destra in discesa, 16-18 multi-apex a destra, ultime due sinistre). «Big Red» alla 1. Dislivello 40 m (de.wiki, fonte singola, a vista). 2:05.3.
- **Indianapolis** (orario, Grand Prix Road Course 2014-oggi, 14 curve): 9 destre e 5 sinistre, nessuna piega dubbia; nessun nome nelle fonti. Senso orario da de.wiki. 1:35.5.
- **Catalogo**: `corners_confidence` «alta» per i quattro (Laguna e COTA da «media», Watkins Glen e Indianapolis da «da_verificare»).
- Due frasi di COTA riscritte senza «l'11%»: il test degli accenti prende «l'» per un apostrofo al posto dell'accento.

**Verifica:** validatore senza errori (guide 20/25) · `test_tracciati` **147/147** (+22: 16 delle guide a disco, sensi dei quattro, nomi di Laguna Seca e Watkins Glen) · suite **1192/1192** · scheda di Laguna Seca nel Chrome di Edoardo dopo il riavvio del backend (mappa accanto alle 11 curve, Corkscrew senza senso, righe Nomi e Sensi). Frontend non toccato.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» del 02/10/2026.

---

## Entry #072 — Guide essenziali, blocco B: Donington, Snetterton, Valencia, Mount Panorama

| Campo | Valore |
|---|---|
| Data | 02/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | NEW `tracks_knowledge/{donington_park,snetterton,valencia_ricardo_tormo,mount_panorama}.json` · `data/tracks.json` · `tests/test_tracciati.py` · docs |
| Commit | `4b92ecd` + commit docs, pushati il 02/10/2026 |
| Contesto | Secondo blocco delle guide essenziali, stesso metodo della #071. Con questo, 24 guide su 25: manca solo il Nordschleife, parcheggiato. |

**Catalogo messaggi:**
1. «ok push e procedi con il blocco B» → push della #071 (`8c0fc7a` · `bad9a27`), poi questo blocco.

**Fatti e fonti:**
- **Donington** (orario, 12 curve): sensi dalla mappa, confermati curva per curva da Oversteer48 (Redgate e Hollywood destre, Craner Curves, Starkey's Bridge e Schwantz Curve sinistre, McLean's e Coppice destre, Fogarty Esses sinistra-destra); Melbourne (destra) e Goddards (sinistra) sono tornanti senza verso scritto, dal disegno. Tutti e 12 i nomi nell'ordine di Oversteer48 e della mappa (Fogarty Esses alla 9-10; Oversteer48 conta 11 curve con le Esses come una). Driver61 descrive il National (senza Melbourne, Goddards chicane): non usato per il GP. 1:26.5.
- **Snetterton** (orario, 12 curve, circuito 300): la mappa scelta ha i nomi ma non i numeri; la tabella di Wikipedia numera le 12 nello stesso ordine del giro. La 2 è **«Wilson»** dal 2016 (prima «Montreal», come sulla mappa del 2015). 7 destre e 5 sinistre; Wikipedia conferma Murrays sinistra. 1:46.2.
- **Valencia** (antiorario, 14 curve): 9 sinistre e 5 destre (4, 5, 10, 11, 12), esattamente il conto di Sky Sport, che descrive anche 2, 4, 10, 12 e 14. Nomi dalla mappa verificata (è quella dell'infobox di Wikipedia), la 4 «Nico Terol» confermata da soymotero.net. 1:30.6.
- **Mount Panorama** (antiorario, 23 curve): sensi dalla mappa, coerenti con le sezioni di Wikipedia (Hell Corner sinistra, Griffins Bend destra, The Cutting due sinistre, Quarry destra, Reid Park destra-sinistra, McPhillamy sinistra, Skyline destra, Murray's sinistra). Le Esses le ho seguite a occhio sul tratto ingrandito: `sensi_da_mappa.py` agganciava più numeri allo stesso punto e non seguiva la Chase disegnata in blu (risultati scartati). Esses e 18 a confidenza media. Nomi solo dove le due mappe e il testo concordano (14 su 23; la mappa scelta chiama «Quarry» la 2, Wikipedia «Griffins Bend»). Dislivello 174 m dalla mappa di Wikipedia (fonte singola, a vista). 2:00.7.
- **Catalogo**: `corners_confidence` «alta» per Donington, Snetterton e Mount Panorama (Valencia lo era già).

**Verifica:** validatore senza errori (guide 24/25) · `test_tracciati` **169/169** (+22) · suite **1214/1214** · scheda di Mount Panorama nel Chrome di Edoardo dopo il riavvio del backend (23 curve accanto alla mappa). Frontend non toccato.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» del 02/10/2026.

---

## Entry #073 — I ritagli delle foto del Lotto 2

| Campo | Valore |
|---|---|
| Data | 02/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `backend/scripts/crops.json` (+ fuori repo: `public/assets/crops.json`, manifest e ATTRIBUTIONS rigenerati) |
| Commit | `b36e3a4` + commit docs, pushati il 02/10/2026 |
| Contesto | Ultimo pezzo del Lotto 2 (#064): le 23 foto delle vetture non GT3 erano a disco senza ritaglio. |

**Catalogo messaggi:**
1. «ok push e procedi con i ritagli del Lotto 2» → push della #072 (`4b92ecd` · `c127ff9`), strumento di ritaglio rigenerato (`build_crop_tool.py`, 76 foto, 53 già fatte) e aperto nel Chrome di Edoardo.
2. «ho esportato crops.json, applica i ritagli, l'unica cosa è che purtroppo alcune foto sono a bassa risoluzione oppure non mi soddisfano affatto però ci adattiamo così e fa niente.»

**Modifica:** l'export di Edoardo (`Downloads/crops (1).json`: 76 voci, banda 540×280, nessuna foto mancante né in più) sostituisce `backend/scripts/crops.json` (53 voci). Oltre alle 23 nuove, l'export porta **10 ritagli vecchi spostati**: Audi R8 LMS, Bentley Continental 2015 e 2018, Ferrari 296 e 488, Honda NSX, Huracán GT3, McLaren 720S ed Evo, Nissan GT-R 2018. Sono spostamenti veri del riquadro (non arrotondamenti), probabilmente ritocchi rimasti nel browser da una sessione precedente: applicati come scelta di Edoardo, la versione di prima resta nella storia del repo. `apply_photos.py --no-download` lanciato per intero (mai `--only`, trappola dell'01/10).

**Nota di Edoardo:** alcune foto del Lotto 2 sono a bassa risoluzione o non lo soddisfano; per ora si tengono. Possibile lavoro futuro: un provino per sostituirle.

**Verifica:** ATTRIBUTIONS.md **identico riga per riga** a una copia presa prima (101 righe) · manifest 98 asset · `public/assets/crops.json` = `scripts/crops.json` (76) e servito dal frontend con le voci nuove. Nessuna sessione in archivio usa una vettura del Lotto 2, quindi la card in app non si può vedere con queste foto: l'anteprima dello strumento di ritaglio usa la stessa geometria della card.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» del 02/10/2026; Lotto 2 chiuso. Sessione chiusa da Edoardo («per ora basta così»).

---

## Entry #074 — «Sono migliorato?»: la sessione contro la precedente

| Campo | Valore |
|---|---|
| Data | 05/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | NEW `backend/app/analisi/confronto.py` · NEW `backend/app/bundle/demo_precedente.py` · `backend/app/api/sessions.py` (1 rotta) · NEW `backend/app/tests/test_confronto.py` · `frontend/src/app/(app)/console/page.tsx` · `components/console/Radio.tsx` · `lib/debrief.ts` · `lib/api.ts` · docs |
| Commit | `368f110` + commit docs, pushati il 05/10/2026 |
| Contesto | Punto 5 dell'ordine dell'01/10: le tre cose parcheggiate della Console. Questa è la prima, il debrief su più sessioni; restano la dettatura al microfono e la prova degli screenshot del setup. |

**Catalogo messaggi:**
1. «leggi la memoria e riprendiamo il lavoro con pitwall» → status (main = origin = `d6aa84f`, server spenti), poi tre giri di domande. Scelte di Edoardo: si parte dal **debrief su più sessioni**; confronto fra sessioni sulla **stessa pista e vettura**; **ultima contro precedente**; contenuto **ritmo, curve, setup cambiato, gomme**; **nella radio di Gigi** come domanda in più; «la precedente» **dentro lo stesso gruppo** (tue · riferimenti · demo); condizioni diverse = **si confronta e si dichiara**, gomme confrontate entro **5 °C** di pista; la domanda si chiama **«Sono migliorato?»**; **un messaggio**, il resto con «Perché?». Dettatura: detta e poi invii tu. Screenshot: provarli prima, con immagini cercate online.
2. «non ho ACC sul pc, quindi tocca trovare una soluzione» → dati: **seconda demo + ricerca online** (scelta sua); storia della seconda demo «setup e guida insieme»; «ricordati di accendere i server dev così vedo cosa fai a schermo».
3. «ok procedi. vai avanti con tutto quello che serve.» → scaricato il file trovato, reimportati i due Zandvoort già sul disco, scritta la seconda demo (numeri protetti) e costruito tutto.

**I dati (fuori repo).** In archivio non c'era nessuna coppia vera «stessa pista e vettura». Ricerca online (~10 minuti): **PS_Racing, BMW M4 GT3 a Monza** (video del 19/04/2024, ACC 1.10.1, Drive pubblico, nessuna licenza esplicita → uso locale, `PROVENIENZA.md` aggiornato). 10 giri, 8 con tempo, migliore 1:46.829; setup Q dedotto da `telemetryLaps = 10`. Importata come riferimento (`20261005-151527-monza_bmw_m4_gt3-3afe`): fa coppia con la `…711b` (Fri3d0lf, 2023, un giro, altro pilota). Reimportati i due file Zandvoort · McLaren 720S di kyxap del 5 e 6 dicembre 2023 (`…e93b`, `…9a04`): con la `…3e52` del 10 dicembre sono tre sessioni dello stesso pilota in giorni diversi, un giro lanciato l'una.

**Modifica:**
- NEW `analisi/confronto.py`. `scegli_precedente(riassunti, id)`: stessa pista, stessa vettura, stesso gruppo, iniziata prima, la più vicina (date con e senza fuso; senza data di inizio vale quella di import; fuori le sessioni senza un tempo). `confronta(...)` → `Confronto`:
  - **Ritmo**: giro migliore contro giro migliore; la media solo con almeno 2 giri di ritmo per parte.
  - **Curve**: **giro migliore contro giro migliore sugli stessi tratti** (quelli del motore per la sessione aperta; se ha un giro solo, quelli della precedente o quelli ricavati dal giro). I tratti si toccano e coprono il giro: la somma delle differenze è la differenza sul giro. Così il confronto regge anche fra due sessioni da un giro. Nomi e punti dall'aggancio della guida; si nominano solo le differenze da 50 ms in su.
  - **Setup**: i parametri con un click diverso, con il valore del gioco dove la vettura ha la tabella («Pressione Post.SX +4 click (24.7 → 25.1 psi)»); nella prova i primi sei, gli altri contati. Mai detto come causa del tempo.
  - **Gomme**: per ruota, sui giri di ritmo, pressione media, temperatura massima al core e stato contro la finestra Kunos; una ruota si nomina se cambia stato, o di almeno 0.2 psi o 3 °C. Oltre 5 °C di differenza di pista non si confrontano.
  - **Condizioni**: differenza di pista e di aria dichiarata da 3 °C; temperatura non registrata → detto; fra riferimenti «possono essere di piloti diversi». Asciutto contro bagnato: nessun confronto, con il motivo.
  - **Messaggio** («Sì / No / Sei lì», i due tempi, la media, il tratto che pesa di più e quello che va contro) e **prova** riga per riga.
- NEW `bundle/demo_precedente.py`, **la volta prima della demo**: stesso banco e tracciato, 14/07/2026, migliore **1:48.150** al giro 3, media 1:49.072, posteriori 4 click più basse nel file di setup (0.4 psi a caldo), Post.DX a 108 °C, Roggia −4.5 km/h, Lesmo 1 +4.5 km/h. **Solo in memoria**: non è in archivio, non compare negli elenchi, non si apre come sessione (così non tocca colonna di sinistra, Rapporto completo in cache, conteggi dei tracciati). `demo.py` non è modificato.
- `GET /api/sessions/{id}/confronto`: senza una precedente risponde `precedente: null` con il motivo.
- **Console**: la domanda **«Sono migliorato?»** compare fra le domande preparate solo se c'è una precedente; Gigi risponde con il messaggio, e il «Perché?» subito dopo dà le prove del confronto (non quelle della fase). La prova va a capo riga per riga.

**Risultato osservato:**
- Demo: «Sì: il giro migliore è 0.33 s più veloce della volta prima (1:47.820 contro 1:48.150). Anche in media guadagni 0.57 s a giro. Il grosso lo guadagni in curva 3: 0.40 s; in curva 4 ne lasci 0.06 s.» Prova: setup «Pressione Post.SX +4 click (24.7 → 25.1 psi) · Pressione Post.DX +4 click (25.3 → 25.7 psi)», gomme «Post.SX 25.0 → 25.4 psi (ancora sotto la finestra) · Post.DX 24.8 → 25.2 psi · 108 → 105 °C al core (ancora oltre la finestra di temperatura)».
- BMW M4 a Monza (PS_Racing contro Fri3d0lf): «No: il giro migliore è 0.63 s più lento della sessione precedente (1:46.829 contro 1:46.200). Il grosso lo lasci in T8-T10 Variante Ascari: 0.39 s.» Setup: 39 parametri cambiati su 49. Dichiarati: temperatura della pista non registrata, piloti diversi.
- McLaren a Zandvoort (10/12 contro 06/12/2023): «Sì: … 0.50 s più veloce … Il grosso lo guadagni in T8 Mastersbocht: 0.35 s; in T1 Tarzanbocht ne lasci 0.20 s.»

**Limiti dichiarati:**
- I file MoTeC non portano la temperatura della pista né la versione di ACC: la prima si dichiara come «non registrata», la seconda non si può dire.
- Sulle sessioni MoTeC la posizione in pista è ricavata dalla velocità: fra due file i tratti possono scostarsi di qualche metro (giri di riferimento 5760 e 5749 m a Monza).
- Sulla demo le curve restano «curva 3», senza nome: la guida non si aggancia (come nel resto della Console).
- A schermo le domande ora sono sei e vanno su due righe: la conversazione perde una riga di altezza. Da decidere con Edoardo.

**Verifica:** suite **1270/1270** in 23 file (+56 `test_confronto`) · `tsc --noEmit` 0 errori · a schermo a 1536×695 su demo e su Monza · BMW M4 GT3 (domanda, risposta, «Perché?»; la pagina non scorre).

**File protetti:** ☑ numeri della demo: scritti in un file nuovo (`demo_precedente.py`) con l'«ok procedi» del 05/10; `demo.py`, `demo_responses.py`, prompt, `agent.py`, `setup_params.py` non toccati (`setup_params` solo letto, per le etichette).
**Decisione:** ☑ Mantenuto — «ok push» del 05/10/2026.

---

## Entry #075 — La dettatura alla radio di Gigi

| Campo | Valore |
|---|---|
| Data | 05/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | NEW `frontend/src/lib/dettatura.ts` · `frontend/src/components/console/Radio.tsx` · `frontend/src/app/globals.css` · docs |
| Commit | `5ac0c6c` + commit docs, pushati il 05/10/2026 |
| Contesto | Seconda delle tre cose parcheggiate della Console (punto 5). Il microfono era stato tolto con la #061 («microfono via per ora»). |

**Catalogo messaggi:**
1. (primo giro di domande della #074) Dettatura: **«Detta, poi invii tu»**, con il riconoscimento vocale del browser.
2. «ok push, poi procedi con la dettatura» → push della #074 (`368f110` · `086e877`), poi questa.

**Modifica:**
- NEW `lib/dettatura.ts`: `useDettatura` sopra la Web Speech API del browser (`SpeechRecognition` / `webkitSpeechRecognition`), in italiano (`it-IT`), con la frase che compare mentre si parla; l'ascolto si chiude da solo al silenzio o con un secondo clic. `accoda()` attacca il dettato a quello che era già scritto, entro i 1000 caratteri della casella.
- `Radio`: un pulsante con il microfono nella casella, fra il testo e il contatore. **Scrive nella casella e non invia**: una parola capita male si corregge prima di spendere una delle 12 domande. Mentre ascolta il pulsante pulsa in rosso e la casella dice «Ti ascolto… poi premi Invio»; inviando, l'ascolto si ferma.
- Il microfono compare solo con Gigi dal vivo acceso **e** se il browser ha la Web Speech API (Chrome, Edge; non Firefox). Permesso negato, nessun microfono o rete assente: lo dice la casella, senza finestre.
- `globals.css`: l'alone del microfono in ascolto (fermo con «riduci movimento»).

**Cosa va saputo:** in Chrome l'audio lo riconoscono i server di Google, non PitWall: è scritto nel tooltip del pulsante. Nessuna spesa per PitWall, nessuna chiave. Il backend non è toccato.

**Verifica:** `tsc --noEmit` 0 errori · a 1536×695 il pulsante è nella casella, la pagina non scorre, l'API è presente nel Chrome di Edoardo. **Non verificato da me:** il riconoscimento vero (serve la voce di Edoardo e il permesso del microfono nel suo browser).

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» del 05/10/2026 (Edoardo non ha riferito l'esito della prova a voce).

---

## Entry #076 — La lettura degli screenshot del setup, provata per la prima volta

| Campo | Valore |
|---|---|
| Data | 05/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | nessun file del repo (prova): `core/vision_parser.py` chiamato così com'è · immagini e resoconto in `%LOCALAPPDATA%\PitWall\screenshot_prova\` |
| Commit | solo questa entry (docs) |
| Contesto | Terza e ultima delle cose parcheggiate della Console (punto 5). La rotta `POST /api/setup/from-image` esiste dalla v1 ma non era mai stata provata con un'immagine vera (#029: «nessuno screenshot reale disponibile»); dalla #058 nessuna pagina la usa. |

**Catalogo messaggi:**
1. (giri di domande della #074) Screenshot: **«Provarlo, poi decidere»**; senza ACC sul PC di Edoardo, immagini **cercate online**; il caricamento torna nella pagina Setup solo se la lettura è buona.
2. «ok push, poi procedi con gli screenshot» → push della #075 (`5ac0c6c` · `02c0902`), poi la prova.

**Le immagini.** I fermo-immagine dai video di YouTube non si sono potuti prendere (nella scheda in secondo piano il video non si carica). Usate le sette immagini dell'articolo di racinggames.gg sul setup della Porsche 911 GT3 R a Imola: schermate vere di ACC 1.6.5, una per scheda (Tyres, Electronics, Fuel & strategy, Mechanical grip, Dampers, Aero) più una visuale dall'abitacolo senza setup. **Limite:** il sito le serve a 1024×576, non a 1920×1080 come dice il nome del file: più piccole di uno screenshot fatto in casa. Uso locale, fuori dal repo, provenienza scritta accanto. I valori giusti li ho letti io, immagine per immagine (49 in tutto).

**La prova.** Parser chiamato direttamente da uno script (la rotta in demo-mode risponde 503, per scelta della #027), con il modello vero (`claude-sonnet-4-6`) e passando dal tetto di spesa.

| Scheda | Giusti | Note |
|---|---|---|
| Tyres | 13/13 | pressioni, toe, camber, caster |
| Electronics | 4/4 | |
| Mechanical grip | 10/10 | brake bias compreso (59.0 %) |
| Dampers | 16/16 | ma il parser li segna «fuori range» (sotto) |
| Aero | 5/6 | **ala posteriore letta 5, è 6** |
| Fuel & strategy | — | **letti 4 valori che non sono del setup** (sotto) |
| Abitacolo | — | nessun valore, giusto |

**48 valori giusti su 49**, 2–5 secondi a immagine, **$0,0395** per le sette (ottobre a $0,107 su $1,00).

**I tre difetti trovati:**
1. **Un numero sbagliato in silenzio**: ala 5 invece di 6 (cifra bianca sopra la barra rossa, a 1024 px). Il parser lo dà per buono: non c'è modo di accorgersene senza guardare l'immagine.
2. **La scheda Fuel & strategy inganna**: le pressioni della strategia di sosta (26.5 / 26.1 / 25.6 / 25.3) sono state lette come pressioni del setup (`tire_press_*`), che in quel setup sono 26.2 / 25.7 / 25.7 / 25.6. Validazione «ok».
3. **Falsi allarmi della validazione**: `validate_setup` usa i range generici (ammortizzatori 0–11), e segna «fuori range» i 12 e 13 veri della Porsche. È il vecchio INC-V2-003 visto da qui.

**Il nodo che la prova ha fatto emergere.** Lo screenshot porta i **valori del gioco** (psi, N/m, gradi); dalla #057/#058 PitWall lavora in **click** e conosce la conversione solo per BMW M4 GT3 e Ferrari 488 GT3 Evo. Per le altre vetture un setup letto da screenshot non si può portare nella pagina Setup né confrontare con un file di ACC senza la tabella di quella vettura.

**Verifica:** resoconto completo (attesi, letti, risposta grezza del modello) in `screenshot_prova/racinggames_porsche_991_imola/resoconto_prova.json`; l'ala a 6 ricontrollata su un ritaglio ingrandito.

**File protetti:** ☑ nessuno toccato (`vision_parser.py` solo chiamato).
**Decisione:** ☑ «lascialo parcheggiato» (Edoardo, 05/10/2026): la rotta resta, nessuna pagina la usa. Con questa il punto 5 è chiuso.

---

## Entry #077 — Pulizia del repo: righe false, codice morto, documenti del corso fuori da Git

| Campo | Valore |
|---|---|
| Data | 05/10/2026 |
| Agente dev | Claude Code (claude-opus-5-5) |
| Area | `docs/03-v2-architecture.md` · `README.md` · `README.it.md` · `frontend/src/app/(auth)/login/page.tsx` · `frontend/src/lib/api.ts` · `backend/app/tests/test_budget.py` · `.gitignore` |
| Commit | `ba54c38` (README) · `d08221d` (pulizia) + commit docs, pushati il 05/10/2026 |
| Contesto | Punto 6 dell'ordine (fuori dal codice). Scrivendo il Runbook è saltata fuori una riga vecchia del README; Edoardo: «dimmi se vedi qualcosa di errato o ancora antico sul repo che lo sistemiamo». |

**Catalogo messaggi:**
1. «ok va bene, correggi il readme e procedi con la landing» → README riallineati nelle due lingue: la chat di Gigi è collegata (stato attuale e tabella del tetto, italiano), roadmap aggiornata (stress test fatto, guide 24/25, mappe 22/25, Lotto 2 chiuso, ultimo punto = deploy dimostrativo e prima prova con piloti esterni).
2. «ok push, poi dimmi se vedi qualcosa di errato o ancora antico sul repo» → push (`ba54c38`) e ricerca: frasi superate, codice che nessuno usa, numeri di versione. Sei correzioni proposte, tre decisioni lasciate a lui.
3. «ok procedi con i sei punti».

**Modifica:**
- `docs/03`, limiti noti: via «LLM reale mai acceso: manca lo stress test» (fatto l'11/09) e «`agent.py:134` ha ancora `import streamlit`» (non c'è più); corretti «la pagina Setup si rifà nella #058» e «La chat dal vivo arriva con la #061»; la rotta degli screenshot dichiarata non usata da nessuna pagina.
- Pagina di login: via «Progetto d'esame» dal piede (restano copyright e licenza).
- `test_budget.py`: il test B14 si chiamava «chat a $0 (non collegata)»; cambiato solo il nome.
- `lib/api.ts`: via tre funzioni che nessuno chiamava (`getHealth`, `getRiferimenti`, `postSetupFromImage`) e i tre tipi che servivano solo a loro. La rotta `/api/setup/from-image` nel backend resta (parcheggiata, #076).
- `.gitignore`: `/*_PitWall.md`, per i documenti del corso compilati nella radice (PRR, Scorecard, Backlog, Runbook, Landing, informativa privacy).
- README: la rotta degli screenshot segnata «nessuna pagina la usa».

**Errore mio, corretto subito:** la prima scrittura del `.gitignore` ha raddoppiato i fine riga e per qualche minuto Git ha visto come nuovi `backend/.env`, `node_modules` e i report. Nessun commit in quello stato: file ripristinato con `git checkout`, riga riaggiunta in coda, e verificato con `git check-ignore` che `.env`, `CLAUDE.md`, `node_modules`, i report e i documenti del corso siano ignorati.

**Lasciato a Edoardo (non toccato):** il numero di versione (0.1.0 in `package.json` e nell'API, `v1.1.0` nel menu utente) · la frase d'apertura dei README, ancora centrata sugli LLM · la licenza MIT prima di un deploy pubblico. Segnalato e non toccato perché protetto: il modello di ripiego e quello degli screenshot sono `claude-sonnet-4-6`.

**Trovato cercando, da decidere:** `npm audit` segnala 4 vulnerabilità nelle dipendenze del frontend (Next.js critica, `sharp`, `postcss`, `nanoid` alte), con correzione disponibile · le due rotte `DELETE` (sessione e registrazione) non passano dal presidio delle scritture: su una vetrina pubblica chiunque potrebbe cancellare le sessioni che non sono la demo · nessuna CI e nessun test del frontend.

**Verifica:** `tsc --noEmit` 0 errori · `test_budget` 31/31 · rotte `/ /login /console /setup /telemetry` 200.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ Mantenuto — «ok push» del 05/10/2026.

---

## Entry #078 — Gli attrezzi: la verifica in un comando solo (pacchetto 1.0)

| Campo | Valore |
|---|---|
| Data | 05/10/2026 |
| Area | NEW `strumenti/` (`verifica.py`, `guardiano.py`, `hooks/pre-commit`, `server.ps1`, `numeri_documenti.py`, `numeri.json`) · NEW `frontend/e2e/` + `playwright.config.ts` · NEW `.github/workflows/verifica.yml` · `.gitignore` · README · docs/03 |
| Commit | `ab0be2c` + commit docs, pushati il 05/10/2026 |

**Perché.** Edoardo ha chiesto una tabella di marcia e tempi più corti «ingegnandosi», senza togliere sicurezza né qualità. Il primo pacchetto della tabella sono gli attrezzi che fanno risparmiare tempo a ogni seduta. Da questa voce il registro è breve, per sua scelta: cosa, perché, verifica, decisione.

**Cosa.**
- `python strumenti/verifica.py`: test del backend, tipi, numeri dei documenti e, con i server accesi, pagine, cinque percorsi nel browser e 27 catture (nove pagine su tre formati di schermo) con l'elenco di quelle cambiate. Verde o rosso; un passo saltato lo dice.
- Guardiano prima di ogni commit: rifiuta file protetti (salvo `PITWALL_OK_PROCEDI=1` dopo un «ok procedi»), `.env` e gli altri file che non devono entrare nel repository, e ogni testo che somigli a una chiave.
- `server.ps1`: avvia, ferma, riavvia, stato.
- `numeri_documenti.py`: i conteggi dei test nei README e in `docs/03` li scrive il codice; ogni rotta dell'API deve comparire nelle tabelle dei README.
- Controlli a ogni push su GitHub (la verifica veloce).
- Playwright fra gli strumenti di sviluppo del frontend.

**Trovato dagli attrezzi al primo giro.** La rotta `GET /api/catalog/track/{id}/guida` mancava nei due README: aggiunta · sei file di test usano la memoria condivisa finta di ACC e in parallelo si disturbano: la verifica li mette in fila · la Console regge senza modifiche a 1920×1080 e 1366×768, e nessuna pagina scorre in orizzontale sui tre formati.

**Verifica.** Verifica completa verde: 1270 test, 0 errori di tipo, 9 pagine, 5 percorsi, 27 catture · guardiano provato con `.env` e `agent.py` in stage: commit rifiutato, poi tutto ripulito (anche dagli oggetti locali di Git).

**Decisioni di Edoardo:** attrezzi nel repository · Playwright sì · versione `0.9.0` fino alla beta (si applica nel pacchetto 1.1).
**File protetti:** ☑ nessuno modificato (`agent.py` toccato e ripristinato per provare il guardiano).
**Su GitHub.** I controlli sono partiti al primo push e sono usciti rossi due volte: su Linux falliscono solo `test_telemetria` e `test_registratore`, perché la memoria condivisa di ACC esiste solo su Windows e le strutture hanno un'altra dimensione. I controlli ora girano su Windows, come PitWall, e i passi rossi diventano annotazioni leggibili da fuori (`a86fcb7`, `b22dfb4`). Verdi dal commit `b22dfb4`; il test dei tracciati lì è saltato e lo dichiara.

**Decisione:** ☑ «ok push» del 05/10/2026. Pacchetto 1.0 chiuso: tutte le voci del «finito quando» sono vere.

---

## Entry #079 — Messa in sicurezza (pacchetto 1.1)

| Campo | Valore |
|---|---|
| Data | 05/10/2026 |
| Area | `frontend/package.json` + lock · `backend/app/api/sessions.py` · `backend/app/api/telemetria.py` · `backend/app/main.py` · `components/ui/UserChip.tsx` · `test_sessions.py` · `strumenti/verifica.py` · documenti |
| Commit | `a11f16c` + commit docs, pushati il 05/10/2026 |

**Perché.** Secondo pacchetto della tabella di marcia: chiudere ciò che diventa un problema il giorno del deploy.

**Cosa.**
- **Dipendenze del frontend.** Next.js 15.5.20 → 15.5.27 (via la vulnerabilità critica), `sharp` e `nanoid` aggiornati, PostCSS 8.4.49 → 8.5.29 anche dentro Next (con `overrides`). **In ciò che arriva agli utenti: zero vulnerabilità.**
- **Restano 5 «alte» negli strumenti di sviluppo**, tutte dalla stessa radice: Tailwind 3 usa `braces`, che non ha una versione corretta. Si tolgono solo passando a Tailwind 4, che è un salto di versione con modifiche a tutta la configurazione degli stili. Non l'ho fatto: è fuori dal pacchetto e lo decide Edoardo. Riguardano la compilazione degli stili sul PC di chi sviluppa, non l'app in funzione.
- **Rotte di cancellazione.** `DELETE /api/sessions/{id}` e `DELETE /api/telemetria/sessioni/{id}` ora passano dal presidio delle scritture: con `PITWALL_ALLOW_IMPORT=0` rispondono 503, demo compresa.
- **Versione `0.9.0`** in un punto solo del backend (`VERSIONE`), in `package.json` e nel menu utente.
- **Verifica:** nuovo passo «Dipendenze dell'app» (`npm audit --omit=dev`), rosso con una vulnerabilità alta o critica in ciò che arriva agli utenti.

**Verifica.** Verde su tutto: 1275 test (+5 sulle rotte di cancellazione), tipi 0 errori, 9 pagine, 5 percorsi, 27 catture con **nessuna pagina cambiata** dopo l'aggiornamento di Next.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ «ok push» del 05/10/2026. Sulle 5 vulnerabilità degli strumenti di sviluppo Edoardo ha scelto: Tailwind 4 dopo la prima uscita. Pacchetto 1.1 chiuso.

---

## Entry #080 — Pronto per occhi esterni, su ogni schermo (pacchetto 1.2)

| Campo | Valore |
|---|---|
| Data | 05/10/2026 |
| Area | NEW `components/ui/ServizioFermo.tsx`, `SchermoPiccolo.tsx`, `lib/errori.ts` · Console, Setup, Tracciati, Sessioni, Dashboard, Telemetria, Rapporto completo · `Radio.tsx`, `lib/debrief.ts` · `frontend/e2e/*`, `playwright.config.ts` · `strumenti/verifica.py` · README |
| Commit | `4f691f0` + commit docs, pushati il 05/10/2026 |

**Perché.** Terzo pacchetto della tabella: quello che uno sconosciuto vede quando qualcosa non va, o quando apre PitWall su uno schermo che non è quello di Edoardo.

**Cosa.**
- **Servizio fermo.** Via «Backend non raggiungibile — avvia FastAPI su :8000 (vedi README)» da cinque punti, e «riprova quando il backend è su» dai Tracciati. Ora ovunque: «PitWall non risponde in questo momento. Riprova fra qualche secondo.» con il pulsante **Riprova**, che rifà le richieste senza ricaricare la pagina.
- **Un difetto trovato dal percorso nuovo:** con il servizio fermo all'apertura, la Console diceva «Nessuna sessione aperta» e il Setup «Nessun setup in questa sessione». Ora dicono che il servizio non risponde.
- **Domande della radio su una riga.** «La prossima» non è una domanda: è diventata una freccia accanto al nome della fase. «Il giro migliore?» è «Il giro?». Cinque domande, una riga.
- **Schermo stretto.** Sotto i 900 px: «Aprilo da computer», con «Guarda lo stesso».
- **Tre browser.** I percorsi girano su Chromium, Firefox ed Edge (21 prove); due percorsi nuovi: schermo stretto e servizio fermo con «Riprova».
- **Cattura del login corretta:** fotografava la Dashboard, perché l'utente demo era già dentro.
- **README:** frase d'apertura nuova (il motore calcola, il modello racconta), scelta da Edoardo. Nella pagina Sessioni «il backend legge la shared memory» è diventato «PitWall legge la telemetria».

**Emerso dal giro da sconosciuto, non corretto qui** (è scritto nella tabella di marcia come lavoro da decidere): parole da addetti ai lavori nella Dashboard («R² 0.984», «soglia Kunos», «stint», «al core», «apice al metro 5414») · la pagina di login non dice che cos'è PitWall · la freccia della fase successiva è piccola.

**Verifica.** Verde su tutto: 1275 test, tipi 0 errori, 9 pagine, 21 prove sui tre browser, 27 catture (cambiate, come atteso, solo la Console e il login).

**Non verificato:** Gigi dal vivo e la dettatura a voce restano da provare da parte di Edoardo (decisione D6).
**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ «ok push» del 05/10/2026. Pacchetto 1.2 chiuso. Delle cose emerse dal giro da sconosciuto Edoardo ha messo in programma le parole della Dashboard (pacchetto 2.6, prima della prova).

---

## Entry #081 — Il primo deploy, la preparazione (pacchetto 1.3, prima parte)

| Campo | Valore |
|---|---|
| Data | 05/10/2026 |
| Area | NEW `render.yaml` · NEW `.github/workflows/sveglia.yml` · NEW `components/ui/Accensione.tsx` · `lib/sessione.tsx` · `(app)/layout.tsx` · `frontend/public/assets/` (101 file ora nel repository) · `.gitignore` · `strumenti/guardiano.py` · `frontend/e2e/percorsi.spec.ts` · `.env.local.example` |
| Commit | `0e606ba` (deploy) + commit delle immagini e dei documenti, pushati il 05/10/2026 |

**Perché.** Quarto pacchetto della tabella: mettere online la vetrina. Questa voce copre tutto quello che si prepara nel repository; gli account e la pubblicazione vera li fa Edoardo, guidato, e avranno la loro voce.

**Decisioni di Edoardo.** Frontend su Vercel e backend su Render, piani gratuiti (D4) · immagini nel repository, dopo il chiarimento che vengono da Wikimedia Commons e che in vetrina sono comunque pubbliche · repository pubblico e MIT fino al cancello M3 (D1) · indirizzo gratuito per ora, il dominio con il nome definitivo · «PitWall» resta il nome in codice · il sonno del backend si tratta con una schermata d'attesa e una sveglia diurna.

**Cosa.**
- **Immagini nel repository:** 101 file, 46,6 MB (foto, mappe verificate, ritagli, crediti); restano fuori i provini di lavoro (`_*`). Il test dei tracciati ora gira anche su GitHub.
- **`render.yaml`:** il backend come vetrina in sola lettura. Modello, scritture e registratore spenti; nessuna chiave API; si pubblica solo un commit che ha passato i controlli.
- **Accensione:** quando il backend dorme, il primo visitatore legge «Il muretto si sta accendendo» e la pagina riparte da sola; solo dopo l'attesa configurata compare «PitWall non risponde». In locale l'attesa è zero.
- **Sveglia:** una richiesta ogni 10 minuti nelle ore diurne, da GitHub, all'indirizzo scritto in una variabile del repository.
- **Percorsi:** uno nuovo sull'accensione; il primo (ingresso dal login) reso stabile, perché ogni tanto cliccava prima che la pagina fosse viva. 8 percorsi su 3 browser = 24 prove.

**Da sapere.** Le immagini pesano 46,6 MB, non i 33 scritti finora nei documenti (sono cresciute con il Lotto 2) · il piano gratuito basta per la vetrina, non per la prova: lì il disco si azzera a ogni riavvio, e dal pacchetto 2.2 servirà un backend con disco permanente (5-7 dollari al mese) · `autoDeployTrigger: checksPass` in `render.yaml` va verificato alla prima pubblicazione.

**Verifica.** Test, tipi, documenti, dipendenze, pagine: verdi; 24 prove nei browser verdi, il percorso dell'accensione ripetuto tre volte sui tre browser; catture: nessuna pagina cambiata.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ «ok push» del 05/10/2026. Il pacchetto resta aperto fino alla pubblicazione vera.

---

## Entry #082 — La vetrina è online (pacchetto 1.3, seconda parte)

| Campo | Valore |
|---|---|
| Data | 05/10/2026 |
| Area | Vercel e Render (account di Edoardo) · `backend/app/config.py`, `main.py` · `frontend/src/app/layout.tsx` · `.github/workflows/sveglia.yml` · `frontend/e2e/*` · `test_sessions.py` · Runbook (fuori repo) |
| Commit | `114e177` + commit docs, pushati il 05/10/2026 |

**Cosa è successo.** Edoardo ha creato gli account e pubblicato, guidato passo per passo: backend su Render dal `render.yaml` (https://pitwall-backend-5del.onrender.com), frontend su Vercel dalla cartella `frontend` (https://pitwall-wine.vercel.app), le due variabili su Vercel, l'origine del frontend su Render. È la prima volta che questa versione di PitWall gira fuori dal suo PC.

**L'unico intoppo.** Nella variabile `PITWALL_CORS_ORIGINS` è finito l'indirizzo con `/login` in coda: il backend rifiutava ogni richiesta del frontend e la pagina restava su «Il muretto si sta accendendo», senza un errore leggibile. Trovato provando da fuori quali origini il backend accettava. Corretto il valore; e nel codice `config.origini()` ora toglie percorso e barra finale, con un test.

**In più.** Backend e frontend dicono quale commit è online (campo `commit` dello stato, tag `pitwall-commit` della pagina): così si vede da fuori se un push è arrivato · l'esito della sveglia è un'annotazione leggibile senza credenziali · il percorso «servizio fermo» non dà più per scontata l'attesa zero del PC · le catture fanno un giro a vuoto prima di fotografare (un falso allarme sulla Dashboard dopo il riavvio dei server).

**Verifica.** Da fuori: il backend risponde come vetrina (modello, chat, registratore spenti; una sola sessione, la demo; cancellare, caricare, registrare, scrivere a Gigi, leggere uno screenshot: tutti 503). Gli **otto percorsi automatici passano contro la vetrina vera**. In locale: 1276 test, 24 prove nei browser, verifica verde.

**Non verificato da me:** l'apertura da un telefono con un'altra rete (la fa Edoardo) · il nome scelto per `pitwall-backend` su Render esisteva già, di un altro: l'indirizzo vero ha un suffisso e non va indovinato.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ «ok procedi» del 05/10/2026 dopo aver visto la vetrina funzionare. Resta il cancello M1, che è di Edoardo.

---

## Entry #083 — Vetrina: via il pulsante di Google che dava errore, e il telefono in orizzontale

| Campo | Valore |
|---|---|
| Data | 05/10/2026 |
| Area | `frontend/src/app/(auth)/login/page.tsx` · `components/ui/SchermoPiccolo.tsx` · `frontend/e2e/percorsi.spec.ts` |
| Commit | `b268c66` + commit docs, pushati il 05/10/2026 |

**Perché.** Edoardo, provando la vetrina: «Continua con Google» apriva una finestra di Google con «Errore 400: invalid_request — Missing required parameter: client_id». E dopo averla fatta aprire da più telefoni: va bene, e in orizzontale si guarda, anche se scomodo.

**Causa.** Errore mio di preparazione: sulla vetrina il Client ID di Google non c'è, di proposito, e avevo dato per scontato che senza di esso il pulsante non comparisse. Compariva sempre.

**Cosa.** Il pulsante di Google, il separatore «oppure» e la nota sul profilo Google compaiono solo dove c'è un Client ID; senza, la pagina di login dice «Nessun account e nessun dato richiesto: è una demo da guardare». L'avviso sugli schermi stretti suggerisce di girare il telefono, e in orizzontale sparisce da solo. Due percorsi automatici lo coprono.

**Verifica.** Verifica completa verde in locale; Vercel ha pubblicato da solo in circa un minuto; i **nove percorsi passano contro la vetrina vera**, compreso quello nuovo sul login senza Google.

**File protetti:** ☑ nessuno toccato.
**Decisione:** ☑ richiesta di Edoardo del 05/10/2026.

---

## Entry #084 — Pacchetto 1.3 chiuso, cancello M1 superato: la fase 1 è finita

| Campo | Valore |
|---|---|
| Data | 05/10/2026 |
| Area | `.github/workflows/sveglia.yml` · tabella di marcia e Runbook (fuori repo) |
| Commit | `6df80fb` (sveglia) + questo commit docs |

**Cosa.** La sveglia è confermata: la variabile `PITWALL_BACKEND_URL` su GitHub non era stata creata, e l'avviso «niente da svegliare» era stato letto come un «tutto acceso». Creata da Edoardo; il giro lanciato a mano ha risposto «200 in 0,5 s». Ora senza variabile la sveglia fallisce in rosso. Backend pubblicato a mano da Edoardo: frontend e backend online sono tutti e due a `6df80fb`, nove percorsi verdi contro la vetrina.

**Limite noto, accettato da Edoardo per chiudere:** Render non pubblica il backend da solo, anche se l'impostazione è «After CI Checks Pass». Si aggiorna con «Manual Deploy → Deploy latest commit». Ipotesi da provare al prossimo lavoro sul backend: guarda solo l'ultimo commit del push, che finora è sempre stato quello dei documenti.

**Decisioni di Edoardo.** Pacchetto 1.3 chiuso con quel limite · **cancello M1 superato**: la vetrina si può far vedere (l'ha già fatta aprire da più dispositivi) · il primo giro a orario della sveglia lo verifica lui domani.

**Bilancio della fase 1.** Quattro pacchetti (1.0 attrezzi, 1.1 sicurezza, 1.2 occhi esterni, 1.3 deploy) in circa 3,75 sessioni su una stima di 4 – 6. La vetrina è online: https://pitwall-wine.vercel.app

**File protetti:** ☑ nessuno toccato in tutta la fase.
**Decisione:** ☑ «chiudiamo l'1.3 […] ok procedi per togliere il cancello M1» (05/10/2026).

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
