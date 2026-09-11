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
