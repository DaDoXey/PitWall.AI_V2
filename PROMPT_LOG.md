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

## Entry #008 — MEGAPROMPT #6: semplificazione UX (Sidebar + Telemetria) + Login/Google Sign-In 🔄 IN CORSO

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
