# PitWall.AI v2 — Architettura as-built

> **Stato documentato:** 11/09/2026, dopo l'Entry #028 (tetto di spesa del ramo LLM) · build post-esame.
> Riallineato al codice l'11/09: la versione precedente fotografava il 10/07 (fine megaprompt #2, `ed18898`).
> Completa i doc di planning `00`/`01`/`02` (che descrivono la *sorgente* v1 e la *decisione* di stack):
> questo file fotografa la v2 **com'è realmente costruita**. Per la cronologia → `PROMPT_LOG.md`;
> per i malfunzionamenti gravi → `INCIDENTS.md`.

## 1 · Stack & runtime
| Layer | Tech | Versione |
|---|---|---|
| Frontend | Next.js (App Router) / React | 15.5.20 / 19.0 |
| | TypeScript / Tailwind | 5.7 / 3.4 |
| | Recharts / Framer Motion | 2.15 / 11.15 |
| Backend | Python / FastAPI / Uvicorn | 3.12 / 0.115 / 0.34 |
| | Anthropic SDK / Pandas / Pydantic | 0.113 / 3.0 / 2.10 |
| LLM (Gigi) | analisi: `claude-haiku-4-5` (env `LLM_MODEL`), fallback `claude-sonnet-4-6` · screenshot: `claude-sonnet-4-6` | |

**Avvio dev:** `cd backend && ./.venv/Scripts/python -m uvicorn app.main:app` (:8000, **senza `--reload`**:
HAZARD-V2-B) + `cd frontend && npm run dev` (:3000). Health `GET :8000/` →
`{status:"ok", demo_mode:true, live_allowed:false}`.

## 2 · Frontend (`frontend/src/`)
**Layout** (i route group non entrano negli URL):
- **`app/layout.tsx`** — root: font (Orbitron/Inter/JetBrains Mono), `globals.css`, `Providers` (Google OAuth + stato di accesso).
- **`app/(app)/layout.tsx`** — app "loggata": `AuthGate` (senza accesso → `/login`) → `Sidebar` + `<main>` con
  `MotionProvider` (`<MotionConfig reducedMotion="user">`); in più `OnboardingFlow` (wizard "Conosci il pilota" al
  primo accesso) e `GigiTour`.
- **`app/(auth)/layout.tsx`** — senza Sidebar, card centrata (fix INC-V2-004).

**Pagine:**
| Rotta | File | Cosa fa · API |
|---|---|---|
| `/` | `(app)/page.tsx` | **Dashboard** (L4; riordinata nelle Entry #050-#051): fascia della sessione, verdetto con le note sui dati | cosa regge e 7 indicatori a righe (clic = dettaglio), pista e vettura compatte · report da `lib/sessione.tsx` (`GET /api/sessions/{id}/analisi`) |
| `/telemetry` | `(app)/telemetry/page.tsx` | **Telemetria** (L4; riordinata nella Entry #051): tab Giri (tabella con il distacco disegnato nella cella, settori a destra), Curve (tabella con la guida, confronto velocità / delta / pedali), Gomme e freni (la macchina vista dall'alto, ruota per ruota, e un grafico giro per giro con selettore) · report + `GET /api/sessions/{id}/tracce` |
| `/console` | `(app)/console/page.tsx` + `components/console/*` | **Engineer Console** (#060): Gigi alla radio. Debrief fase per fase (`GET /api/sessions/{id}/debrief`), striscia dei giri con le fasi da ascoltare e da ritagliare (`PUT …/debrief/tagli`), replay, mappa verificata della fase con il punto peggiore e le gomme, il distacco media · giro migliore, la prima cosa da fare (in click con la tabella della vettura), un solo messaggio in onda e sotto la conversazione con le domande preparate risposte dal debrief (casella spenta senza modello), «Rapporto completo» a 5 sezioni (`POST /api/analysis`). La chat dal vivo arriva con la #061 |
| `/setup` | `(app)/setup/page.tsx` | **Setup** (#058): il setup della sessione in click, 5 tab / 49 parametri con frecce − / + come in ACC e, dove la vettura ha la tabella, il valore del gioco accanto; verdetto convertito in click; modifiche nella scheda con «Ripristina»; «Scarica il setup per ACC». Senza setup: invito a importarlo. Lo screenshot non è più in pagina (torna con il lavoro su Gigi) · `/api/setup-params?car`, `/api/sessions/{id}`; `POST /api/sessions/{id}/export/setup` |
| `/sessioni` | `(app)/sessioni/page.tsx` | **Sessioni** (L4; riordinata nella Entry #053): in cima l'archivio a gruppi (Le tue / Riferimenti / Demo, gli stessi della colonna), sotto «Aggiungi una sessione» — PC a tab (Export MoTeC, File di ACC, Registrazione dal vivo), console con la sessione manuale e il racconto |
| `/tracciati` · `/tracciati/[id]` | `(app)/tracciati/…` | **Tracciati** (dal 18/09; riordinata nella Entry #054): indice dei 25 circuiti a quattro colonne, con «guida», «layout», «aperta ora» e le sessioni in archivio per pista; scheda con foto e numeri (dati di pista della guida compresi), mappa verificata accanto al curva per curva, settori, sezioni brevi a coppie, chicche e fonti · `GET /api/catalog`, `/api/catalog/track/{id}`, `/guida` |
| `/lezioni` · `/lezioni/[slug]` | `(app)/lezioni/…` | **A Lezione con Gigi**: indice (con «Consigliate per te» dal verdetto della sessione aperta e dal profilo, Entry #056) e dettaglio, contenuti read-only da `lib/lessons.ts` |
| `/crediti` | `(app)/crediti/page.tsx` | Crediti delle immagini Wikimedia Commons: legge `public/assets/ATTRIBUTIONS.md` a build-time |
| `/login` | `(auth)/login/page.tsx` | Google Sign-In (popup) oppure modalità demo; profilo solo in `sessionStorage`, nessuna sessione server |

Le schede vettura/circuito (`SessionBriefing`) leggono `GET /api/catalog/car/{id}` e `/api/catalog/track/{id}`.

- **`components/ui/`**: `AuthGate`, `CountUp`, `GigiAvatar`, `GigiTour`, `MotionProvider`, `NavIcons`,
  `OnboardingFlow` (5 passi, il primo è la piattaforma), `PageHeader`, `Providers`, `QuickNotes`, `SessionBriefing`,
  `Sidebar` (dal 29/09, Entry #048: in cima la sessione aperta con l'elenco a gruppi «Le tue» / «Riferimenti» / «Demo»; navigazione in due gruppi «La sessione» e «Archivio e studio»; nello spazio libero `PannelloPista` — mappa della pista aperta con la curva dove perdi di più, adattata all'altezza dello schermo; sulla Console al suo posto `PannelloSessione`: migliore, media e i giri di ritmo uno per uno; note e utente come icone accanto al marchio, versione nel menu dell'utente), `Tabs`, `UserChip` (menu: tutorial, crediti, esci), `Verdetto`. Il layout `(app)` centra il contenuto (`max-w-6xl`).
- **`components/charts/`**: `AnalisiCurve`, `GiriSessione`, `GommeFreni` (`Sparkline` tolto nella #050, `PressureGauge` nella #051).
- **`lib/`**: `api.ts` (fetch client tipizzato sul report + `ApiError`), **`sessione.tsx`** (sessione aperta e report
  condivisi da tutte le pagine), **`formato.ts`** (solo formattazione: nessun conto), `auth.tsx`, `profile.tsx`,
  `theme.ts`, **`instrument.ts`** (token "analogici"), **`motion.ts`**, `catalog.ts` (liste di fallback),
  `console.ts`, `lessons.ts`, `setup.ts`.
- **Regola L4**: i conti li fa il motore di analisi nel backend; il frontend mostra.
- Asset visivi in `public/assets/` (**gitignorata**, ~33 MB): si rigenerano con gli script di `backend/scripts/`.

## 3 · Backend (`backend/app/`)
- **`main.py`** — FastAPI, CORS, 6 router sotto `/api`, middleware request-id. **`config.py`** — env server-side +
  presidio chiave (flag demo/live), cartella dei log. **`logging_config.py`** — log rotante con request-id (Entry #026).
  **`budget.py`** — tetto di spesa del ramo LLM: prenotazione al costo massimo e saldo al reale, per categoria
  (analisi/screenshot/chat) e per mese (Entry #028).
- **`api/`**: `sessions.py` (archivio, import, sessione manuale, analisi, tracce, riferimenti), `telemetria.py`,
  `analysis.py`, `setup.py`, `vision.py`, `catalog.py`.
- **`bundle/`**: `schema.py` (session bundle 1.1), `store.py`, `adapters/` (setup, risultati, telemetria),
  `demo.py` (sessione DEMO generata). **`telemetria/`**: shared memory di ACC, registratore, `banco.py` sintetico.
  **`analisi/`**: `motore.py`, `curve.py`, `gomme.py`, `gigi.py`, `aggancio.py` (la guida del tracciato agganciata ai tratti del motore dalle ancore, Entry #047). Dettaglio in `docs/04-rework-dati.md`.
- **`core/`** (⚠️ = protetto): ⚠️`agent.py` (client LLM: analisi a 5 sezioni con cascata + `chat_with_gigi`, non
  collegata), ⚠️`setup_params.py` (+ ⚠️`data/car_setup_ranges.json`), ⚠️`vision_parser.py`,
  ⚠️`prompts/` (`system_prompt_v5.txt`, `chat_system_prompt.txt`), ⚠️`demo_responses.py`, `riferimenti_fisica.py`
  (+ `data/acc_riferimenti_fisica_v19.json` Kunos e `acc_riferimenti_community.json`), `riferimenti_acc.py`,
  `catalog.py` + `data/cars.json` (31 GT3) e `data/tracks.json` (25 circuiti), `data/tracks_knowledge/` (guide: 13 su 25, al 25/09), `data/tracks_anchors/` (ancore delle curve: inizio, apice, uscita sul giro e punto sulla mappa per ogni curva della guida; Monza e Zandvoort al 28/09; formato e validatore in `core/ancore.py`, rilevamento in `analisi/eventi_curva.py`).
- **`tests/`**: 19 file, 1005 test offline (elenco nei README).
- **`backend/scripts/`** (fuori da `app/`): pipeline delle immagini (foto, ritagli, mappe, crediti) e validatore delle guide.
- **`backend/logs/`** (gitignorata): `pitwall.log`, `llm_spesa.json`, e i registri `llm_token_log.md` / `llm_incidents.md`
  scritti da `agent.py`.

## 4 · Contratto API
- `GET /` → health `{status, service, version, demo_mode, live_allowed}`.
- Sessioni, analisi, tracce, telemetria e riferimenti: tabella nei README, formato in `docs/04-rework-dati.md`.
- `POST /api/analysis` body `{prompt, profile?, session_id?}` → `{question, text (5 sezioni md), source:
  demo|cache|motore|api|fallback}`. Live spento: sulla DEMO la cache per keyword (fuori perimetro → reindirizzo), sulle
  altre sessioni la risposta composta dal motore (`motore`). Live: `fallback` senza chiave, a tetto di spesa o con
  testo oltre 4000/1000 caratteri — cache sulla DEMO, motore sulle altre.
- `GET /api/setup-params?car&track` (entrambi opzionali) → 5 sezioni / 49 `Param{label,min,max,step,unit,default,tip,regola}`; `regola` = come il click diventa il valore del gioco per quella vettura (`car` = carName di ACC), `null` senza tabella. I min/max/default generici non li usa più nessuna pagina (#058).
- `GET /api/sessions/{id}/debrief` → `Debrief{fasi[{tipo,nome,giri,delta_medio_ms,messaggio,prova,punti,argomenti}],tagli,tagli_automatici,manuale,giri,fuori_ritmo,in_ballo_ms,prima_cosa,nota}` (`analisi/debrief.py`, #059): fasi avvio · il giro · calo/tenuta dal motore, senza modello. `PUT /api/sessions/{id}/debrief/tagli` `{tagli: [giri] | null}` salva in `SessionBundle.fasi_tagli` (422 tagli non validi, 503 con le scritture spente).
- `POST /api/sessions/{id}/export/setup` `{click: {parametro: click}}` → il file di setup originale di ACC con quei click (409 senza file originale, 422 click non scrivibile). Non cambia la sessione archiviata.
- `POST /api/setup/from-image` (multipart) → `{params,summary,…}` (503 in demo-mode, 503 se manca la key server,
  429 a tetto di spesa raggiunto, 500 se la lettura fallisce).
- `GET /api/catalog` → indice di vetture e circuiti · `GET /api/catalog/car/{car_id}` e `/api/catalog/track/{track_id}`
  → scheda completa (accettano slug, id ACC, nome o alias; 404 se non trovati).
- Ogni risposta porta l'header `X-Request-ID`.

## 5 · Presidio API key
`ANTHROPIC_API_KEY` vive **solo lato server**. Con `PITWALL_ALLOW_LIVE=0` (default, e forzato sul deploy
pubblico) si serve la **cache demo** offline → la chiave non si consuma mai e non finisce nel bundle JS.
La LLM reale si abilita con `PITWALL_ALLOW_LIVE=1` + `PITWALL_DEMO_MODE=0` + chiave nei secret del server; lo
stesso presidio vale per la lettura screenshot (Entry #027).
Acceso il live, ogni chiamata passa da `budget.prenota()` / `budget.salda()` (agganci in `agent.py` e
`vision_parser.py`): tetti `PITWALL_BUDGET_{ANALISI,SCREENSHOT,CHAT}_GIORNO` + `PITWALL_BUDGET_MESE`.

## 6 · La sessione DEMO (`bundle/demo.py`, dal 16/09/2026)
`core/demo_data.py` non esiste più: la demo è una sessione generata e analizzata dallo stesso motore delle altre.
- Monza · BMW M4 GT3 · 8 giri di prove su asciutto · best **1:47.820** al giro 4 · 3.2 l/giro (25.6 l).
- Storia: posteriori sotto la finestra Kunos (media 25.4 / 25.2 psi), Post.DX oltre i 100 °C al core per il 38% del
  tempo (105 °C a fine stint), calo di 352 ms a giro dal giro 4.
- I numeri della cache di Gigi (`demo_responses.py`) sono quelli del report della demo: lo verifica `test_gigi.py`.
- Si alza `VERSIONE_GENERATORE` quando cambia il generatore: all'avvio la demo si rigenera.

## 7 · Verifica
- Frontend: `npx tsc --noEmit` **0 err** + rotte `/ /console /telemetry /setup /sessioni /lezioni /crediti /login` **200**.
- Backend: 19 file di test in `app/tests/`, **1005** test, tutti offline.
- **Mai** `npm run build` con `npm run dev` attivo (corrompe `.next`, HAZARD-V2-A).

## 8 · Deploy (da decidere)
Nessun workflow nel repo. L'ipotesi dei doc di planning era frontend → **Vercel**, backend → **Render/Railway/Fly**.
- Frontend: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_GOOGLE_CLIENT_ID`.
- Backend: secret `ANTHROPIC_API_KEY`, `PITWALL_ALLOW_LIVE`, `PITWALL_DEMO_MODE`, `PITWALL_BUDGET_*`,
  `PITWALL_CORS_ORIGINS` (origine del frontend).
- Da tenere presente: le immagini non sono versionate (serve `apply_photos.py`); su un disco effimero
  `backend/logs/llm_spesa.json` si perde a ogni riavvio, e con lui la spesa del giorno e del mese.

## 9 · Note aperte (vedi `INCIDENTS.md`)
- **Unico incidente aperto:** INC-V2-003, in corso: `car_setup_ranges.json` converte i click nel valore del gioco
  vettura per vettura (Entry #057); per ora c'è la sola BMW M4 GT3 (45 parametri su 49, da fonti concordi, non ancora
  visti in gioco). Le altre vetture restano in click; la pagina Setup si rifà nella #058.
- LLM reale **mai acceso**: manca lo stress test.
- `chat_with_gigi()` non è collegata a nessuna rotta né a una UI.
- `api/vision.py` è `async` ma chiama il parser sincrono: blocca l'event loop per tutta la chiamata al modello.
- `agent.py:134` ha ancora `import streamlit` (non installato): dall'Entry #028 non è raggiungibile dall'API.
- Tetto di spesa: il lucchetto è per un solo processo (con più worker servirebbe un lock su file).
- Mappe dei circuiti: 5 layout su 25 verificati, nessuna pagina le mostra.
