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
| Commit | non ancora committato |
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
