# PitWall.AI v2 — REWORK DATI: specifica viva

> **Aperto:** 14/09/2026 · **Stato:** L0 in corso.
> Questo file è la **fonte di verità** del rework della logica dati: formato, strati, lotti e stato.
> Va aggiornato a ogni avanzamento, prima del commit del lotto. Cronologia → `PROMPT_LOG.md`;
> architettura in vigore → `03-v2-architecture.md`; malfunzionamenti → `INCIDENTS.md`.

## 0 · Perché

Il CSV proprietario accettava 2 colonne obbligatorie (`lap`, `fuel_cons`) + 8 opzionali e restituiva
medie/min/max per gomma. Tre limiti strutturali:

1. **ACC non lo produce.** Il pilota doveva costruirlo a mano: attrito di raccolta troppo alto.
2. **Niente tempi, velocità, input, posizione in pista** → nessuna analisi per curva → nessuna
   analisi *spietata* possibile: solo «il posteriore destro è caldo».
3. Le schermate e il contesto di Gigi erano modellati su quelle 10 colonne: **le interfacce non
   possono essere migliori del dato che leggono**.

Obiettivo del rework: analisi **accurata, precisa e spietata**, con **attrito di raccolta ≈ zero**,
usando le fonti che ACC già scrive da sé.

## 1 · Fonti dati (L1 · adattatori)

| Fonte | Percorso / meccanismo | Contenuto | Attrito |
|---|---|---|---|
| **Results JSON** | `Documents/Assetto Corsa Competizione/Results/*.json` | scritto in automatico a fine sessione: tempo per giro, 3 splits, validità, vettura, pista | **zero** |
| **Setup JSON** | `Documents/.../Setups/<auto>/<pista>/*.json` | il setup vero ed esatto (valori in *click*) | **zero** |
| **Shared memory** | file mappati `acpmf_physics` / `acpmf_graphics` / `acpmf_static` | gas, freno, sterzo, marcia, rpm, velocità, `wheel_slip`, `wheel_pressure`, `tyre_core_temp`, `brake_temp`, usura pad/dischi, sospensioni, G, **`normalized_car_position`**, tempi, pioggia, grip, fuel, auto/pista/pilota | registratore attivo durante la guida |
| **MoTeC `.ld/.ldx`** | export nativo ACC (da abilitare) | telemetria completa | medio — **L5, opzionale** |

**`normalized_car_position` è la chiave dell'intero rework:** trasforma i canali da serie *nel tempo*
a serie *sulla distanza del tracciato*, che è ciò che permette il confronto curva per curva.

**Nota sicurezza (chiarita il 14/09):** la shared memory di ACC è **user-space** — un file mappato che
Kunos espone per le app di terze parti (SimHub, Race Element, CrewChief leggono così). Nessun driver,
nessun ring-0, nessuna certificazione. Il registratore **non è un processo separato**: vive dentro il
backend FastAPI come task in background → nessun eseguibile da distribuire, quindi nessun problema di
firma digitale / SmartScreen / euristiche antivirus. Se un domani servirà un pacchetto one-click per
altri piloti, la firma si affronterà allora.

## 2 · Formato canonico (L2 · «session bundle»)

Documento versionato (`schema_version`), prodotto da **ogni** adattatore e consumato da **tutto** il
resto (analisi, schermate, Gigi, demo):

- `meta` — vettura, pista, tipo sessione, data, pilota, temp aria/pista, grip, pioggia, durata
- `laps[]` — numero, tempo, 3 splits, validità, carburante consumato, in/out lap, set gomme, mescola
- `channels` — serie ricampionate (20–50 Hz) **+ copia indicizzata sulla distanza**, per giro
- `setup` — parametri normalizzati (+ valore grezzo in click sempre conservato) e scostamenti
- `events[]` — pit, bandiere, penalità, off-track, contatti

Storage: metadati JSON + canali in formato colonnare compatto, sotto `sessions/`, con indice.
**Anche la demo diventa un bundle in questo formato** → un solo percorso di codice per demo e live, e
il vecchio problema di `_context()` (contesto sempre ancorato alla sessione demo) sparisce da sé.

## 3 · Motore di analisi (L3 · Python deterministico, niente LLM)

> Si chiamava «kernel di analisi» nella prima proposta: *nucleo* software, nessun rapporto con il
> kernel di Windows. Rinominato per non generare equivoci.

- **Per curva** (curve ricavate automaticamente da velocità+posizione, nessun dato a mano per 25
  circuiti): punto di frenata, velocità minima, posizione dell'apice, riapertura del gas,
  sovrapposizione freno/gas, **decimi persi rispetto al riferimento**
- **Riferimento**: miglior giro valido → giro teorico (somma dei migliori micro-settori) → traccia delta
- **Costanza**: deviazione standard di tempo sul giro, punto di frenata, velocità minima per curva
- **Gomme**: % di tempo in finestra di pressione e temperatura, squilibri ant/post e dx/sx, **pendenza
  del degrado** sullo stint
- **Freni**: finestra di temperatura per mescola, consumo pastiglie per giro
- **Carburante**: consumo reale per giro **in funzione delle condizioni**, target rifornimento, margine
- **Stile**: coasting, slip, correzioni di sterzo
- **Verdetto**: le prime perdite in decimi, **ordinate per gravità**, ognuna con il numero che la prova

## 4 · Gigi sul nuovo dato (L4)

Gigi riceve **solo il report numerico** del motore (poche centinaia di token), **mai i canali grezzi**:
costa meno, non può allucinare i dati, e diventa credibile perché cita misure. Le stesse identiche
cifre alimentano Dashboard e Telemetria → la corrispondenza fra schermate e Gigi diventa **strutturale**
invece che da mantenere a mano.

## 5 · Decisioni prese (14/09/2026) — chiuse

| # | Decisione |
|---|---|
| 1 | **Locale-first**: il backend gira sul PC del pilota (vede Documenti + shared memory). Il deploy pubblico resta vetrina in demo-mode (`PITWALL_ALLOW_LIVE=0`). |
| 2 | **Solo post-sessione** per ora; il tempo reale dopo. |
| 3 | **Spietato**: verdetto ordinato per gravità, numeri nudi, zero consolazione, **sempre con l'azione correttiva**. |
| 4 | **Curve ricavate automaticamente**; le mappe dei circuiti restano estetica. |
| 5 | **CSV eliminato** (non declassato): parser, rotta e UI rimossi. |
| 6 | **49 parametri = ibrido**: setup importato dal JSON, poi modificabile a slider; inserimento manuale se non c'è file. |
| 7 | **Ranges in tre gradi**: (a) valore grezzo in click sempre conservato; (b) unità reali solo dove la tabella è verificata, altrimenti etichetta «click»; (c) tabella costruita partendo dalle vetture realmente guidate → via d'uscita graduale da **INC-V2-003**. |
| 8 | **Si può rompere la compatibilità** con le schermate attuali; si costruisce in parallelo e la demo resta verde a ogni lotto. |
| 9 | **Pulizia totale come L0**, subito. |

## 6 · Lotti e stato

| Lotto | Contenuto | Stato |
|---|---|---|
| **L0** | Pulizia totale (CSV, residui Streamlit, codice morto) + questa specifica | **in corso — 14/09** |
| **L1** | Adattatori Results JSON + Setup JSON → session bundle | da fare |
| **L2** | Motore di analisi v1: giri, carburante, costanza, gomme | da fare |
| **L3** | Registratore shared memory → canali → analisi per curva | da fare |
| **L4** | Gigi e schermate sul bundle; demo come bundle | da fare |
| **L5** | Import MoTeC (opzionale) | da fare |

## 7 · Baseline di verifica

Con `test_parser` eliminato insieme al CSV, la verifica minima di ogni entry diventa:
`python app/tests/test_observability.py` **24/24** · `python app/tests/test_budget.py` **31/31** ·
`npx tsc --noEmit` **0 errori**. I test del nuovo formato entreranno nella baseline con L1.

## 8 · Posizionamento (ricerca concorrenti, 14/09/2026)

Track Titan (265k utenti, Porsche Ventures, $8–20/mese, post-sessione, consigli AI descritti come
generici) · Coach Dave Delta ($13/mese, forza = 2500+ setup, nessun vero feedback AI) · Garage 61
(condivisione telemetria, suggerimenti adattati allo stile) · VRS (giri di riferimento pro, iRacing) ·
TrackPro ($20/mese, l'unico in tempo reale: voce + haptics) · Trophi.ai ($15/mese, voce post-sessione).

Due letture: **tutti** leggono la shared memory → la strada scelta è lo standard del settore; e **tutti**
hanno uno strato AI sottile e incoraggiante. Nessuno vende un ingegnere di pista spietato che parla del
**tuo** setup con numeri deterministici, in italiano. È il posizionamento di Gigi.
