[English](README.md) | **Italiano**

# PitWall.AI_V2

Un Virtual Race Engineer per Assetto Corsa Competizione (ACC). Usa gli LLM per trasformare la
telemetria e il feedback del pilota in consigli concreti di setup e strategia di gara. Pensato per
colmare la distanza fra dati complessi e prestazione in pista per i sim-racer. Sviluppato per il
corso AI & Digital Innovation Specialist.

> **v2** della webapp PitWall.AI: migrazione da Streamlit a **Next.js + FastAPI**. Riusa la logica
> di dominio della v1 (client LLM, range ACC, vision) dietro un'API pulita, con una UI
> React ricca.

## Stato attuale
**Esame del 15/07/2026 superato**, con la demo in demo-mode. Ora è in corso la **build vera e
propria**: portare PitWall dalla demo al prodotto, con l'LLM reale sotto.

Il client LLM è già implementato: un'analisi a 5 sezioni validate, con retry e cascata di modelli,
che si accende con `PITWALL_ALLOW_LIVE=1` + `PITWALL_DEMO_MODE=0` + la chiave. Il client contiene
anche una chat di Gigi in streaming, non ancora collegata a nessuna rotta. Ogni chiamata al modello
passa da un **tetto di spesa** giornaliero e mensile. **L'LLM reale resta spento di default** finché
non è stato messo sotto stress (vedi Roadmap).

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
    analisi/     # motore deterministico: ritmo, costanza, curve, gomme e freni; contesto di Gigi
    tests/       # 751 test offline: observability 24, budget 31, bundle 37, adattatori 86,
                 # analisi 57, analisi_l4 45, demo 38, gigi 32, sessions 50, telemetria 97,
                 # riferimenti 73, registratore 69, curve 62, telemetria_bundle 50
  scripts/       # pipeline delle immagini (foto, ritagli, mappe) e validatore delle guide
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
| GET | `/api/setup-params` | Parametri di setup e relativi range |
| POST | `/api/setup/from-image` | Lettura del setup da uno screenshot |
| GET | `/api/catalog` | Catalogo vetture e circuiti |
| GET | `/api/catalog/car/{car_id}` | Scheda di una vettura |
| GET | `/api/catalog/track/{track_id}` | Scheda di un circuito |
| POST | `/api/sessions/import/setup` | Importa un setup salvato in ACC |
| POST | `/api/sessions/import/results` | Importa un file di risultati di ACC (409 se il file ha più vetture) |
| POST | `/api/sessions/manuale` | Sessione manuale (chi gioca su console): tempi, setup, racconto del pilota |
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

### Test
```bash
cd backend
./.venv/Scripts/python app/tests/test_observability.py   # log e request-id, offline
./.venv/Scripts/python app/tests/test_budget.py          # tetto di spesa, offline (client finto)
```

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
Le immagini arrivano da Wikimedia Commons (~33 MB) e **non sono nel repo**: `frontend/public/assets/`
è gitignorata. Dopo un clone l'app funziona lo stesso, ma senza foto nelle schede e con `/crediti`
che segnala gli asset come non ancora scaricati. Nel repo è versionata la selezione fatta a mano;
per scaricarla, dalla radice del repo:
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
| `screenshot` | Setup, `POST /api/setup/from-image` | `PITWALL_BUDGET_SCREENSHOT_GIORNO=0.25` |
| `chat` | chat di Gigi (non collegata) | `PITWALL_BUDGET_CHAT_GIORNO=0` |

Sopra le tre categorie c'è un tetto **mensile** complessivo, `PITWALL_BUDGET_MESE=5.00`. Il giorno si
azzera a mezzanotte (ora del server). A tetto raggiunto l'analisi risponde dalla cache con
`source: "fallback"` e lo screenshot risponde `429`. In più il ramo reale dell'analisi accetta al
massimo 4000 caratteri di domanda e 1000 di profilo. Nel dubbio si conta per eccesso: una chiamata
fallita resta al costo massimo, un modello fuori listino si paga al listino più caro, un registro
della spesa illeggibile blocca le chiamate.

## Roadmap
1. **Accensione e stress test dell'LLM reale**, con il tetto di spesa già in funzione.
2. **Guide dei tracciati** per tutti i 25 circuiti ACC: settori e curva per curva.
3. **Mappe dei circuiti**: 5 layout su 25 verificati. Restano da sostituire gli altri 20, e manca
   ancora la pagina che le mostri.
4. **Lotto 2 del catalogo**: 23 vetture GT4, GT2, GTC e TCX.
5. **Range di setup per vettura** (INC-V2-003): oggi cambiare vettura non cambia i 49 parametri.
6. **Deploy**.

## Deploy
Piattaforma **da decidere**. Da tenere presente: le immagini non sono versionate, quindi un deploy
parte senza foto finché non si esegue `apply_photos.py`.

## Licenza
Distribuito con licenza **MIT** — vedi [LICENSE](LICENSE).
