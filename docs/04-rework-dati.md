# PitWall.AI v2 — REWORK DATI: specifica viva

> **Aperto:** 14/09/2026 · **Stato:** L0, L1 e **L2 (prima versione) fatti**. Prossimo: L3.
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
| **L0** | Pulizia totale (CSV, residui Streamlit, codice morto) + questa specifica | **fatto — 14/09** (`167b9a2` `22cb500` `952fa05`) |
| **L1** | Adattatori Results JSON + Setup JSON → session bundle | **fatto — 14/09** (`f93ea57` `94ef0d6` `7894fc2` `c1a488b`) |
| **L2** | Motore di analisi v1: ritmo, settori, costanza, degrado, carburante | **fatto — 14/09**, 57/57 |
| **L3** | Registratore shared memory → canali → analisi per curva | da fare |
| **L4** | Gigi e schermate sul bundle; demo come bundle | da fare |
| **L5** | Import MoTeC (opzionale) | da fare |

## 7 · Fatti verificati sui file reali (14/09/2026)

Su questo PC **ACC non è installato** (c'è Assetto Corsa 1; la cartella
`Documenti/Assetto Corsa Competizione/` è un residuo del 2021: c'è `Config`, ma `Results` è vuota,
`Setups` non esiste e `MoTeC` ha solo `Workspaces`). Gli adattatori si costruiscono quindi su
**fixture di struttura verificata** su file reali pubblici, e si validano sui file di Edoardo appena
ne esisteranno.

**Setup JSON** (verificato su un `bmw_m4_gt3/monza` reale):
- codificato **UTF-8, senza BOM** nei file veri esaminati → si legge con `utf-8-sig`, che copre
  entrambi i casi se ACC un domani ne scrivesse uno;
- `carName` è già lo **slug del catalogo** di PitWall (`bmw_m4_gt3`): nessun ponte da costruire;
- la maggior parte dei valori sono **indici di click** (`tyrePressure: [54,61,48,54]`, `rearWing`,
  `brakeBias`, dampers, ARB, bumpstop, `preload`, `casterLF/RF`, `steerRatio`, elettronica);
- ma **camber, toe, `rodLength` sono già valori fisici** scritti da ACC come float
  (`staticCamber: -4.2328…`): per quei parametri la tabella di conversione **non serve**;
- `strategy` porta anche `fuelPerLap` e la strategia dei pit stop.

**Results JSON:** esistono **due schemi diversi**, e quello che ci serve è il primo.
- **File del gioco** (quello che scrive ACC giocando da soli, il nostro caso): chiavi `sessionDef`,
  `snapShot`, `laps`, `points`. Ogni giro ha `carId`, `driverId`, `lapTime` (ms), `splits[3]`,
  **`fuel`** (residuo a fine giro), `flags`, `timestampMS`. `sessionType` è **numerico**, la vettura
  è un **`carModel` numerico**, e le condizioni stanno in `sessionDef.trackStatus`
  (`idealLineGrip`, `wetLevel`, …).
- **File del server dedicato:** chiavi `sessionType` ("R"), **`trackName`**, `serverName`,
  `sessionResult`, `laps` con `laptime` e `isValidForBest` — ma **senza carburante**.
- Entrambi sono codificati in **UTF-16 little-endian e SENZA BOM** (il file comincia con `{ `):
  letti come UTF-8 danno spazzatura, e **non ci si può basare sul BOM per accorgersene** — il
  riconoscimento va fatto guardando i byte nulli.

**Struttura stabile:** verificata su 8 file di vetture diverse (GT3, GT4, GT2, Challenge) — stesse
chiavi di primo livello, `drivetrain` sempre minuscolo, array a 4 elementi, `brakeDuct` a 2,
`casterLF`/`casterRF`. L'adattatore può contare su questa forma.

**Due lacune da colmare, non aggirabili:**
1. **Il file del gioco non contiene il nome del circuito.** Va preso altrove: dalla scelta del
   pilota, o da `static.track` della shared memory (L3). L'adattatore lo tratta come metadato
   opzionale e non lo inventa.
2. **`carModel` è un id numerico** che va mappato sugli slug del catalogo: tabella da costruire
   (lavoro di dati, come le tabelle di conversione).

**Il carburante NON è gratis come sembrava** (corretto il 14/09 dopo l'esame dei dati veri): nel file
del gioco esaminato `fuel` è **costante su tutti i giri** di ogni vettura e diverso da vettura a
vettura — sembra il carburante di *partenza*, non il residuo di fine giro. L'adattatore calcola il
consumo **solo se il valore cala davvero**, altrimenti lo dichiara non calcolabile. Il consumo giro
per giro affidabile arriverà dal registratore della shared memory (L3). Va verificato su un file di
sessione **in singolo** (quello esaminato era multiplayer, 16 vetture).

## 8 · L1 — fasi

| Fase | Contenuto | Stato |
|---|---|---|
| **F1** | `bundle/schema.py`: il formato canonico + `test_bundle.py` | **fatto — 37/37** |
| **F2** | Adattatore Setup JSON → `Setup` del bundle (grezzo + camber in gradi) | **fatta — 39/39**, provata su 30 setup reali di 30 vetture |
| **F3** | Adattatore Results JSON (schema del gioco **e** del server) → `meta` + `giri[]` | **fatta — 81/81**, provata su 9 file di risultati reali |
| **F4** | Store su disco + rotte API di import ed elenco sessioni | **fatta — 44/44**, provata sul backend vivo con file veri |

### Cosa fa l'adattatore del setup (F2)
`bundle/adapters/acc_setup.py` legge il file e riempie **tutti e 49** i parametri già noti a
`setup_params.py`, con le chiavi di PitWall. Regole:
- valori in **click**, `verificato=False`, per tutto ciò che ACC scrive come indice;
- **camber in gradi e verificato**, perché è ACC stesso a scriverlo come float: non c'è nessuna
  tabella da indovinare (4 parametri su 49);
- il `toe` resta in click: `toeOutLinear` è un valore lineare, **non** gradi, e non viene spacciato
  per tale;
- il JSON originale resta intero in `Setup.raw` (anche `bumpStopRateDn`, `rodLength`, la strategia
  con `fuelPerLap`, che i 49 parametri non prevedono).

**Tre assunzioni dichiarate** in `Setup.assunzioni`, perché il file non le esplicita: l'ordine
dell'array `rideHeight` (0=anteriore, 1=posteriore), l'uso di `bumpStopRateUp` per l'unico parametro
bumpstop per asse, e il caster preso da `casterLF`. Si chiudono con un riscontro in gioco.

**Prova su dati veri:** 30 setup di 30 vetture diverse (GT3, GT4, GT2, Challenge) letti senza un
errore, 49 parametri ciascuno, slug della vettura sempre coincidente con il catalogo.

### Cosa fa l'adattatore dei risultati (F3)
`bundle/adapters/acc_results.py` legge **entrambi** gli schemi e produce il bundle di **una** vettura.
- **Quale vettura è la tua:** il file contiene tutti i partecipanti (16 in quello reale). Con una sola
  vettura la prende; con più di una **si ferma e chiede** (`car_id` o `player_id`), ed
  `elenca_partecipanti()` restituisce l'elenco con pilota, numero e giri fatti per farlo scegliere.
- **Tipo sessione:** numerico nel file del gioco (enum del Broadcasting SDK, 10 = gara), testuale in
  quello del server — comprese le sigle numerate dei server (`Q2`, `FP1`). Una sigla ignota resta «?».
- **Validità:** `isValidForBest` quando c'è (server). Nel file del gioco **non esiste**: c'è solo
  `flags`, campo di bit non documentato → si conserva in `Giro.flags_acc` ma **non** decide la
  validità, e il bundle lo dichiara.
- **Condizioni** da `trackStatus` (grip linea ideale e fuori linea, livello di bagnato) e
  `isWetSession`.

**Prova su dati veri:** 9 file di risultati reali (uno del gioco con 16 vetture, otto di server con
qualifiche, prove, gare, tagli e GT4) letti tutti correttamente; l'unico rifiutato è quello **senza
giri**, che è il comportamento voluto. Un file reale ha fatto emergere `sessionType: "Q2"`, che ora è
gestito.

### Archivio e rotte (F4)
`bundle/store.py` — un file JSON per sessione in `backend/sessions/` (gitignorata, o
`PITWALL_SESSIONS_DIR`). Niente database e **niente indice separato**: l'elenco si ricava leggendo i
file, perché un indice sarebbe una seconda verità da tenere allineata. Id leggibile
(`20260914-144749-monza-ff3d`) validato con regex **e** con un controllo che il percorso risolto stia
dentro l'archivio: gli id arrivano dalla rete e un `..` non deve poter leggere il `.env`. Scrittura
atomica (file temporaneo + `os.replace`): o c'è la versione vecchia o quella nuova, mai mezza.

Rotte: `POST /api/sessions/import/setup` · `POST /api/sessions/import/results` ·
`GET /api/sessions` · `GET /api/sessions/{id}` · `DELETE /api/sessions/{id}`.
- **Non passano dal presidio della demo-mode**, che serve a proteggere la chiave API: qui non c'è né
  chiave né rete, e sul PC del pilota il live è spento, quindi bloccarle in demo le renderebbe inutili
  proprio dove servono. Hanno un interruttore loro, **`PITWALL_ALLOW_IMPORT` (default acceso)**, da
  mettere a **0 sul deploy vetrina** perché nessuno possa caricare file sul server.
- **Più vetture nel file → 409**, non una scelta a caso: la risposta porta l'elenco dei partecipanti
  (pilota, numero, giri) e il frontend richiama con `car_id`.
- Tetto di 20 MB per file; un file vuoto, troncato o del tipo sbagliato risponde **400 con il motivo**,
  mai 500.

**Prova sul backend vivo** (14/09): setup reale importato (49 parametri, 4 in gradi, 2 assunzioni),
risultati reali a 16 vetture → **409 con l'elenco**, poi import della vettura 3 → 22 giri, miglior
giro 101409 ms, 3 assunzioni dichiarate; elenco e rilettura corretti.

## 8b · Il motore di analisi (L2, prima versione)

`app/analisi/motore.py` — `analizza(bundle) -> ReportAnalisi`. Statistica elementare su dati veri,
**nessun LLM**: è la fonte delle cifre che Gigi citerà, e per questo dev'essere ripetibile a mano.

**Cosa calcola, con i soli risultati di ACC:**
- **Ritmo**: miglior giro, **giro teorico** (somma dei settori migliori), quanto hai *lasciato sul
  tavolo*, media, mediana, media dei 3 migliori.
- **Settori**: migliore, media, dispersione, **perdita media per giro** e perdita sul giro migliore.
- **Costanza**: deviazione, coefficiente di variazione, scarto dal migliore al peggiore, quanti giri
  entro mezzo secondo, e un giudizio che non è una carezza.
- **Degrado**: regressione lineare sui giri di ritmo (ms/giro + R², perdita su 10 giri).
- **Carburante**: consumo medio quando il residuo cala davvero; altrimenti dichiara perché no.
- **Verdetto**: le perdite **ordinate per gravità**, ognuna con la **prova** (i numeri) e l'**azione**.

**Due scelte che tengono onesti i numeri:**
1. **Giri di ritmo.** Un giro oltre il **+10% sul migliore** non è ritmo (out lap, rientro ai box,
   bandiera, fuoripista): resta nei conteggi ma non entra in medie, settori, costanza e degrado, e il
   report dice **quanti** ne ha esclusi. Il riferimento è il giro migliore e non la mediana, perché su
   una sessione corta la mediana è già inquinata proprio dagli out lap che si vogliono togliere.
2. **Soglie minime.** Sotto 3 giri niente costanza, sotto 5 niente degrado, con meno di 2 giri niente
   settori: invece di un numero fragile si dice quanti giri servono. E se il giro teorico risultasse
   più lento del miglior giro reale, non viene mostrato: vorrebbe dire settori non confrontabili.

`dati_mancanti` raccoglie le assunzioni dell'import **e** ciò che i risultati non contengono (gomme,
pressioni, freni, traiettorie): un silenzio non deve mai passare per «va tutto bene».

**Rotta:** `GET /api/sessions/{id}/analisi` — deterministica, zero rete, zero spesa.

**Prova sul backend vivo** (sessione reale di 23 giri): 20 giri di ritmo, 3 esclusi; miglior giro
100.230, costanza 804 ms → «ballerina», solo il 10% dei giri entro mezzo secondo; settore 3 a 6,7
decimi di media dal proprio migliore; ritmo in miglioramento (−98 ms/giro, R² 0,49) e quindi
**nessuna** voce di degrado nel verdetto.

## 9 · Baseline di verifica

Con `test_parser` eliminato insieme al CSV, la verifica minima di ogni entry diventa:
`python app/tests/test_observability.py` **24/24** · `python app/tests/test_budget.py` **31/31** ·
`npx tsc --noEmit` **0 errori** · da L1: `app/tests/test_bundle.py` **37/37** e
`app/tests/test_adattatori.py` **81/81** · `app/tests/test_sessions.py` **50/50** ·
`app/tests/test_analisi.py` **57/57**.

## 10 · Posizionamento (ricerca concorrenti, 14/09/2026)

Track Titan (265k utenti, Porsche Ventures, $8–20/mese, post-sessione, consigli AI descritti come
generici) · Coach Dave Delta ($13/mese, forza = 2500+ setup, nessun vero feedback AI) · Garage 61
(condivisione telemetria, suggerimenti adattati allo stile) · VRS (giri di riferimento pro, iRacing) ·
TrackPro ($20/mese, l'unico in tempo reale: voce + haptics) · Trophi.ai ($15/mese, voce post-sessione).

Due letture: **tutti** leggono la shared memory → la strada scelta è lo standard del settore; e **tutti**
hanno uno strato AI sottile e incoraggiante. Nessuno vende un ingegnere di pista spietato che parla del
**tuo** setup con numeri deterministici, in italiano. È il posizionamento di Gigi.
