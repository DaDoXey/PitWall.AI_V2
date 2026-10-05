[English](README.md) | **Italiano**

# PitWall.AI_V2

Un ingegnere di pista virtuale per Assetto Corsa Competizione (ACC). Legge le sessioni dai file del
gioco e da MoTeC, calcola dove si perde tempo curva per curva e dice la prima cosa da cambiare. I
numeri li fa un motore dimostrabile; un modello linguistico li racconta alla radio. Nato nel corso
AI & Digital Innovation Specialist.

> **v2** della webapp PitWall.AI: migrazione da Streamlit a **Next.js + FastAPI**. Riusa la logica
> di dominio della v1 (client LLM, range ACC, vision) dietro un'API pulita, con una UI
> React ricca.

## Stato attuale
**Esame del 15/07/2026 superato**, con la demo in demo-mode. Ora è in corso la **build vera e
propria**: portare PitWall dalla demo al prodotto, con l'LLM reale sotto.

Il client LLM è già implementato: un'analisi a 5 sezioni validate, con retry e cascata di modelli,
che si accende con `PITWALL_ALLOW_LIVE=1` + `PITWALL_DEMO_MODE=0` + la chiave. Il client contiene
anche una chat di Gigi in streaming, servita da `POST /api/sessions/{id}/chat` dietro un interruttore
suo (`PITWALL_CHAT_LIVE=1`, spento di default). Ogni chiamata al modello passa da un **tetto di
spesa** giornaliero e mensile. **L'LLM reale resta spento di default**: si accende per scelta, dopo
il primo stress test di settembre (vedi Roadmap).

Cronologia delle iterazioni → `PROMPT_LOG.md` · malfunzionamenti gravi → `INCIDENTS.md`.

## Struttura

```
backend/       FastAPI
  app/
    main.py      # app + CORS + router sotto /api
    config.py    # env server-side (API key MAI nel client), flag demo/live
    logging_config.py  # log rotante con request-id (backend/logs/)
    budget.py    # tetto di spesa del ramo LLM, per categoria e per mese
    api/         # endpoint (elenco sotto)
    core/        # logica di dominio: agent, setup_params, vision_parser, risposte demo, prompts,
                 # data/ (catalogo ACC, guide dei tracciati, riferimenti Kunos e community)
    bundle/      # session bundle, adattatori, archivio, la sessione DEMO generata
    telemetria/  # shared memory di ACC: strutture, lettore, dizionario, registratore, banco sintetico
    motec/       # file MoTeC: lettore .ld/.ldx, scrittore con l'impaginazione esatta di ACC, export
    analisi/     # motore deterministico: ritmo, costanza, curve, gomme e freni; contesto di Gigi
    tests/       # 1276 test offline in 23 file: adattatori 96, aggancio 37, analisi 61,
                 # analisi_l4 46, budget 31, bundle 37, chat 29, confronto 56, curve 75,
                 # debrief 39, demo 38, gigi 36, motec 43, motec_bundle 45, motec_export 17,
                 # observability 24, registratore 69, riferimenti 74, sessions 67,
                 # setup_ranges 40, telemetria 97, telemetria_bundle 50, tracciati 169
  scripts/       # pipeline delle immagini, validatore delle guide, validazione MoTeC sui file veri
strumenti/     verifica in un comando, guardiano dei commit, avvio dei server, numeri dei documenti
frontend/      Next.js 15.5 (App Router) + TypeScript + Tailwind + Recharts + Framer Motion
  src/
    app/         # layout + pagine (elenco sotto)
    components/  # UI e grafici
    lib/         # client API, token di design, logica delle pagine
docs/          # planning storico (00-02) e architettura V2 as-built (03)
```
Dettaglio in [`docs/03-v2-architecture.md`](docs/03-v2-architecture.md).
Il rework della logica dati in corso (fonti native ACC, formato canonico, motore di analisi) è
specificato in [`docs/04-rework-dati.md`](docs/04-rework-dati.md).

### Pagine
| Rotta | Pagina |
|---|---|
| `/` | Dashboard: il verdetto della sessione aperta |
| `/telemetry` | Telemetria: giri, curve, gomme e freni |
| `/console` | Console (analisi del race engineer sulla sessione aperta) |
| `/setup` | Setup (parametri indicati dal verdetto) |
| `/sessioni` | Sessioni: import (PC), sessione manuale (console), archivio |
| `/lezioni` · `/lezioni/[slug]` | A Lezione con Gigi |
| `/crediti` | Crediti delle immagini (Wikimedia Commons) |
| `/login` | Accesso (Google oppure modalità demo) |

### API
| Metodo | Rotta | Cosa fa |
|---|---|---|
| POST | `/api/analysis` | Analisi del race engineer su una sessione (5 sezioni; `session_id`, di default la DEMO) |
| GET | `/api/setup-params` | Parametri di setup, con la regola click → valore del gioco della vettura (`?car=`) |
| POST | `/api/setup/from-image` | Lettura del setup da uno screenshot (provata, oggi nessuna pagina la usa) |
| GET | `/api/catalog` | Catalogo vetture e circuiti |
| GET | `/api/catalog/car/{car_id}` | Scheda di una vettura |
| GET | `/api/catalog/track/{track_id}` | Scheda di un circuito |
| GET | `/api/catalog/track/{track_id}/guida` | Guida del circuito: settori e curva per curva |
| POST | `/api/sessions/import/setup` | Importa un setup salvato in ACC |
| POST | `/api/sessions/import/results` | Importa un file di risultati di ACC (409 se il file ha più vetture) |
| POST | `/api/sessions/manuale` | Sessione manuale (chi gioca su console): tempi, setup, racconto del pilota |
| POST | `/api/sessions/import/motec` | Importa un export MoTeC di ACC (.ld + .ldx, setup e litri facoltativi) come sessione con i canali |
| GET | `/api/sessions/{id}/export/motec` | La sessione come .ld + .ldx (zip) da aprire in MoTeC i2 |
| GET | `/api/sessions/{id}/debrief` | Il debrief di Gigi fase per fase (dal motore, senza modello) |
| PUT | `/api/sessions/{id}/debrief/tagli` | Le fasi ritagliate a mano, salvate nella sessione (`null` = quelle di Gigi) |
| GET | `/api/sessions/{id}/confronto` | «Sono migliorato?»: la sessione contro la precedente su stessa pista e vettura (dal motore, senza modello) |
| POST | `/api/sessions/{id}/export/setup` | Il setup della sessione con i click cambiati, come file JSON da ricaricare in ACC |
| GET | `/api/sessions` | Elenco delle sessioni, DEMO compresa |
| GET | `/api/sessions/{id}` | Una sessione (session bundle) |
| GET | `/api/sessions/{id}/analisi` | Report di analisi della sessione (deterministico, senza LLM; con curve, gomme e freni se ci sono i canali) |
| GET | `/api/sessions/{id}/tracce` | Canali di al massimo 4 giri sulla stessa griglia di distanza |
| GET | `/api/riferimenti/fisica` | Soglie di gomme e freni: Kunos (primaria) e community (da confermare) |
| DELETE | `/api/sessions/{id}` | Rimuove una sessione (non la DEMO) |
| GET | `/api/telemetria/stato` | Stato del registratore della telemetria (aggancio, sessione in corso) |
| POST | `/api/telemetria/avvia` · `/ferma` | Accende e spegne il registratore |
| GET | `/api/telemetria/sessioni` | Registrazioni di telemetria sul disco |
| GET | `/api/telemetria/sessioni/{id}` | Metadati di una registrazione |
| GET | `/api/telemetria/sessioni/{id}/canali` | Serie dei canali richiesti, con decimazione |
| GET | `/api/telemetria/sessioni/{id}/curve` | Analisi per curva: dove si perde, quanto, cosa fare (deterministica) |
| POST | `/api/telemetria/sessioni/{id}/importa` | La registrazione diventa una sessione dell'archivio |
| DELETE | `/api/telemetria/sessioni/{id}` | Cancella una registrazione |

## Avvio in locale

### Backend (FastAPI, porta 8000)
```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env        # opzionale: senza chiave gira in demo-mode
python -m uvicorn app.main:app
```
Health check: <http://localhost:8000/> · sessioni (DEMO compresa): <http://localhost:8000/api/sessions>

> **Niente `--reload`:** su Windows continua a servire il codice vecchio dopo una modifica al
> backend (HAZARD-V2-B in `INCIDENTS.md`). Dopo aver toccato il backend, fermalo e rilancialo.

### Frontend (Next.js, porta 3000)
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```
Apri <http://localhost:3000>. Senza un Client ID Google si entra con **«Entra in modalità demo»**.

> **Mai `npm run build` con `npm run dev` acceso:** corrompe `.next` (HAZARD-V2-A). Con il dev
> attivo, per controllare i tipi usa `npx tsc --noEmit`.

### Verifica
Un comando solo, dalla radice del repository, risponde verde o rosso:
```bash
python strumenti/verifica.py            # test, tipi, documenti; con i server accesi anche
                                        # pagine, cinque percorsi nel browser e catture
python strumenti/verifica.py --veloce   # senza browser: è quella che gira su GitHub a ogni push
```
I test del backend girano senza rete e senza spesa. Gli altri attrezzi (avvio dei server,
guardiano dei commit, numeri dei documenti) sono descritti in [`strumenti/`](strumenti/README.md).

### Log
Il backend scrive in `backend/logs/` (gitignorata):
- `pitwall.log`: log dell'app, rotante (1 MB × 3), con in ogni riga un request-id che torna al
  client anche nell'header `X-Request-ID`. Avvisi ed errori compaiono anche in console. Ogni analisi
  registra la sua fonte e, quando ripiega sulla cache, il motivo. Quello che scrive il pilota non
  finisce mai nel log, solo la sua lunghezza. Ogni chiamata reale al modello lascia una riga con
  modello, token e costo, oppure il motivo per cui il tetto di spesa l'ha rifiutata.
- `llm_spesa.json`: la spesa del giorno per categoria e quella del mese (vedi *Tetto di spesa*).
- `llm_token_log.md` e `llm_incidents.md`: token stimati per chiamata e chiamate fallite, scritti
  dal client LLM quando l'LLM reale è acceso.

### Immagini (foto e mappe)
Le immagini arrivano da Wikimedia Commons e sono **nel repo** (`frontend/public/assets/`, circa
47 MB): foto, layout verificati dei circuiti, ritagli e crediti. Autori e licenze sono in
`ATTRIBUTIONS.md` e nella pagina `/crediti`. La selezione fatta a mano è versionata a parte; per
rigenerare le immagini da quella, dalla radice del repo:
```bash
backend/.venv/Scripts/python backend/scripts/apply_photos.py   # foto (photos.json) + ritagli + crediti
backend/.venv/Scripts/python backend/scripts/apply_maps.py     # layout dei circuiti (maps_choice.json)
```

## Variabili d'ambiente e presidio API key
Tutte le variabili, con i valori di default, sono documentate in `backend/.env.example` e
`frontend/.env.local.example`.

La `ANTHROPIC_API_KEY` vive **solo nel backend**. Con `PITWALL_ALLOW_LIVE=0` (default) la demo-mode
è forzata qualunque cosa dica il resto: si serve la **cache demo**, senza rete, e la chiave non si
consuma. L'LLM reale richiede **entrambi** `PITWALL_ALLOW_LIVE=1` e `PITWALL_DEMO_MODE=0`, più la
chiave nei secret del server. Lo stesso presidio vale per la **lettura del setup da screenshot**: in
demo-mode risponde `503` senza chiamare il modello.

### Tetto di spesa
Con l'LLM reale acceso, ogni chiamata al modello **prenota il suo costo massimo** prima di partire
(token di input stimati per eccesso più tutti i token di output consentiti) e, a risposta arrivata,
lo sostituisce con il **costo reale**. Se il tetto non regge la prenotazione, la chiamata non parte:
il tetto non si supera nemmeno con più richieste insieme. Importi in dollari, la valuta in cui
Anthropic fattura.

| Categoria | Uso | Tetto giornaliero (default) |
|---|---|---|
| `analisi` | Console, `POST /api/analysis` | `PITWALL_BUDGET_ANALISI_GIORNO=0.50` |
| `screenshot` | `POST /api/setup/from-image` (nessuna pagina la usa) | `PITWALL_BUDGET_SCREENSHOT_GIORNO=0.25` |
| `chat` | Gigi dal vivo nella Console, `POST /api/sessions/{id}/chat` | `PITWALL_BUDGET_CHAT_GIORNO=0` |

Sopra le tre categorie c'è un tetto **mensile** complessivo, `PITWALL_BUDGET_MESE=5.00`. Il giorno si
azzera a mezzanotte (ora del server). A tetto raggiunto l'analisi risponde dalla cache con
`source: "fallback"` e lo screenshot risponde `429`. In più il ramo reale dell'analisi accetta al
massimo 4000 caratteri di domanda e 1000 di profilo. Nel dubbio si conta per eccesso: una chiamata
fallita resta al costo massimo, un modello fuori listino si paga al listino più caro, un registro
della spesa illeggibile blocca le chiamate.

## Roadmap
PitWall oggi è un progetto personale che gira in locale. Il piano porta a due uscite:

1. **Attrezzi e vetrina online.** Verifica con un comando solo, dipendenze aggiornate, rotte di
   scrittura chiuse, prova su altri schermi e browser, primo deploy in sola lettura con la demo.
2. **Pronti per la prova.** Landing page, uno spazio privato per ogni pilota senza registrarsi,
   conteggio dell'uso, percorso d'ingresso per chi porta le proprie sessioni, tabelle dei click
   (oggi BMW M4 GT3 e Ferrari 488 GT3 Evo, INC-V2-003).
3. **La prova.** Da tre a cinque piloti di ACC lo usano da soli: arrivano alla prima analisi?
   tornano? Intanto: accesso facoltativo con Google, backup.
4. **Prima uscita:** beta pubblica gratuita, in italiano, da computer.
5. **Seconda uscita:** versione inglese (le guide dei circuiti restano in italiano).

Già fatto: motore di analisi senza modello, import dai file di ACC e da MoTeC, 24 guide dei circuiti
su 25 e 22 mappe su 25, catalogo di 54 vetture, Gigi dal vivo con tetto di spesa, confronto fra
sessioni.

## Deploy
La vetrina è pensata in due pezzi, tutti e due nel piano gratuito: il **frontend su Vercel** (cartella
`frontend`) e il **backend su Render**, descritto in [`render.yaml`](render.yaml) come vetrina in sola
lettura: modello, scritture e registratore spenti, nessuna chiave API, solo la sessione demo. Il
backend gratuito si addormenta dopo un quarto d'ora senza visite: il frontend lo aspetta («Il muretto
si sta accendendo», `NEXT_PUBLIC_ATTESA_ACCENSIONE_S`) e `.github/workflows/sveglia.yml` lo tiene
acceso di giorno.

## Licenza
Distribuito con licenza **MIT** — vedi [LICENSE](LICENSE).
