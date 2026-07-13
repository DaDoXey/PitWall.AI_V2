# SPEC_ERRATA — PitWall.AI_V2

> Registro delle correzioni alla **specifica tecnica ACC** usata dal progetto (dati di
> dominio: finestre, target, fisica gomme). Non è un log di bug del software (per quello
> c'è `INCIDENTS.md`): qui si annota quando un *numero di riferimento* si scopre errato,
> da dove veniva l'errore e come è stato corretto. Citato da `demo_data.py`.

## Premessa — perché la v2 (migrazione da Streamlit, decisa l'08/07/2026)

La **v1** di PitWall.AI era una web app **Streamlit** (Python monolitico: UI, logica di
dominio e chiamate LLM nello stesso processo). Funzionava, ma Streamlit era il **collo di
bottiglia sulla presentazione**: componenti in iframe, CSS non pienamente controllabile,
rerun completo dell'app a ogni interazione, grafici SVG "stringati" dentro l'HTML — il
livello di UI "da strumento di pit wall" (gauge animati, heatmap, micro-interazioni) non
era raggiungibile.

La decisione (documentata in `docs/01-target-stack.md`, con tabella comparativa dei
criteri): **separare dominio e presentazione**.
- **Backend FastAPI** che **riusa la logica di dominio Python della v1** — parser CSV,
  vision, range setup ACC, agente Gigi: il valore del progetto è stato *portato*, non
  riscritto.
- **Frontend Next.js (App Router) + React + TypeScript + Tailwind + Framer Motion +
  Recharts**: i componenti SVG fatti a mano nella v1 (gauge, heatmap, sparkline) sono
  diventati componenti React riutilizzabili e animabili quasi 1:1.
- **Invariante di sicurezza mantenuto:** la `ANTHROPIC_API_KEY` vive solo lato server;
  il frontend parla solo con la nostra API; in demo pubblica risponde la cache validata.

Questo registro esiste proprio perché la v2 tratta i **numeri ACC come dati di dominio
verificabili** e ne traccia le correzioni nel tempo.

---

## ERR-01 — Distinzione pressioni a FREDDO vs a CALDO (ereditata dalla v1)

- **Errore:** nella v1 le pressioni da CSV/garage (a freddo) e quelle del display
  telemetria (a caldo) venivano confrontate come se fossero la stessa grandezza.
- **Correzione (v1, FASE 2.1):** dataset demo separato in `COLD_PRESSURES` /
  `HOT_PRESSURES`, mai mescolate; il Setup ragiona a freddo, Telemetria/Console a caldo.
- **Stato:** recepita fin dall'inizio della v2 (`demo_data.py`, docstring).

## ERR-02 — Finestra pressioni ACC v1.9: 26.0–27.0 psi a caldo (12/07/2026 · megaprompt #8, FASE 0)

- **Errore:** l'intero stack (demo, prompt, UI) usava la finestra a caldo **28.5–30.0 psi**
  (target 29.0) e una salita freddo→caldo di **+2.5–3.5 psi**. Valori corretti per le
  versioni vecchie di ACC, ma **obsoleti dalla v1.9** (mescola dry DHF).
- **Dato corretto (verificato):** finestra operativa a caldo **26.0–27.0 psi** per tutte
  le classi GT; temperatura di lavoro 70–100°C (ottimale 80–90°C); salita freddo→caldo
  **~1.5–2.0 psi** (regola ±0.1 psi / ±1°C ambiente). Le pressioni di garage sono a freddo.
- **Correzione applicata:** traslazione uniforme **−2.5 psi** dell'intero dataset a caldo
  (valori, serie per giro, finestra → 26.0–27.0); valori a freddo riderivati con **salita
  uniforme +1.5 psi** (finestra a freddo 24.5–25.5, prima 26.0–27.0); default slider Setup,
  risposte demo Console, prompt (v4 + chat) ed esempio vision allineati; scala del gauge
  frontend traslata (24.5–28.0). La costante preserva delta, spread e narrazione demo:
  posteriori sotto finestra → «alza di +1.0 psi» resta la correzione valida.
- **Invarianti verificati dopo lo shift:** anteriori a caldo 26.5/26.7 in finestra;
  posteriori 25.7/25.5 sotto (esattamente 2/4 fuori); freddo < caldo a ogni giro;
  lato temperature invariato (Post.DX 105°C oltre il limite 95°C).
- **File toccati:** `demo_data.py` · `demo_responses.py` · `setup_params.py` ·
  `prompts/system_prompt_v4.txt` · `prompts/chat_system_prompt.txt` · `vision_parser.py`
  (esempio) · `lib/setup.ts` · `PressureGauge.tsx`. **Non toccati:** `csv_parser.py`
  (range 24.0–30.0 inclusivo copre ancora tutti i valori demo), `car_setup_ranges.json`
  (non contiene pressioni).

## ERR-03 — Passo del precarico differenziale: 10 → 5 Nm (13/07/2026 · gate Entry #018)

- **Incoerenza:** la correzione demo di Gigi consiglia **precarico 60 → 75 Nm**
  (fisicamente sensato), ma lo slider del Setup aveva **passo 10 Nm** (…60, 70, 80…):
  il valore consigliato **non era impostabile** — né dal click sui suggeriti né a mano.
- **Correzione applicata:** passo dello slider `preload` **10 → 5 Nm** in
  `setup_params.py` (min/max/default intatti; narrazione Console invariata). Scelta al
  gate tra due opzioni: cambiare il passo (applicata) o alzare il consiglio a 80 Nm
  (scartata: avrebbe toccato la narrazione validata).
- **Verifica:** 75 raggiungibile sul passo ((75−20) % 5 = 0); API `setup-params` →
  `step: 5`; test parser 12/12; coerenza narrazione↔target verificata dalla suite demo
  (243/243).
