# PitWall.AI v2 — REWORK DATI: specifica viva

> **Aperto:** 14/09/2026 · **Stato:** L0, L1, L2 fatti; **L3 in corso** (fasi 1 e 2 fatte il
> 15/09: struttura, lettore, dizionario dei canali, registratore). Prossimo: L3 fase 3.
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
| **L3** | Registratore shared memory → canali → analisi per curva | **fatto — 15/09** (F1 lettore · F2 registratore · F3 curve · F4 bundle e report unico) |
| **L4** | Gigi e schermate sul bundle; demo come bundle | **fatto — 16/09** (motore rivisto, soglie Kunos, demo generata, 5 schermate + Sessioni, Gigi a 5 sezioni) — vedi §11 |
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
- Entrambi sono codificati in **UTF-16 little-endian e SENZA BOM** (il file comincia con `{` seguito da un byte nullo):
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

**Dal 16/09 (L4):** 14 file di test, **751** in tutto, tutti offline — observability 24 · budget 31 ·
bundle 37 · adattatori 86 · analisi 57 · analisi_l4 45 · demo 38 · gigi 32 · sessions 50 ·
telemetria 97 · riferimenti 73 · registratore 69 · curve 62 · telemetria_bundle 50 — più
`npx tsc --noEmit` 0 errori.

## 10 · Posizionamento (ricerca concorrenti, 14/09/2026)

Track Titan (265k utenti, Porsche Ventures, $8–20/mese, post-sessione, consigli AI descritti come
generici) · Coach Dave Delta ($13/mese, forza = 2500+ setup, nessun vero feedback AI) · Garage 61
(condivisione telemetria, suggerimenti adattati allo stile) · VRS (giri di riferimento pro, iRacing) ·
TrackPro ($20/mese, l'unico in tempo reale: voce + haptics) · Trophi.ai ($15/mese, voce post-sessione).

Due letture: **tutti** leggono la shared memory → la strada scelta è lo standard del settore; e **tutti**
hanno uno strato AI sottile e incoraggiante. Nessuno vende un ingegnere di pista spietato che parla del
**tuo** setup con numeri deterministici, in italiano. È il posizionamento di Gigi.

## 8 · L3 — il registratore della shared memory (15/09/2026)

**Decisioni di Edoardo del 15/09, chiuse:** ACC sta sulla sua **PS5** e non sarà mai su questo PC →
il registratore non è verificabile contro ACC in locale, mai (non «finché non lo installa»).
**Assetto Corsa 1 resta solo banco di prova della tubatura** — stessi file mappati, stessi primi
campi — e **mai** fonte di dati per l'analisi: PitWall è ACC-only, tarare soglie su un'altra fisica
falserebbe tutto. Canali **cappati a 100 Hz**, struttura fissata alla **1.8.12**, archivio con
**tetto configurabile**, analisi per curva dentro L3 su canali sintetici.

### La fonte
Documento ufficiale **«ACC Shared Memory Documentation v1.8.12»** (Kunos Simulazioni), incrociato
con un'implementazione di riferimento mantenuta. Da lì escono tre cose, tutte estratte da script
riproducibili (`backend/scripts/estrai_appendici_acc.py`, `estrai_campi_acc.py`):

1. **le tre pagine** campo per campo → `app/telemetria/strutture.py` (800 · 1588 · 820 byte: i conti
   tornano esatti sommando i campi, e i test li ricontano);
2. **la descrizione ufficiale di ogni campo** → `app/core/data/acc_campi_shared_memory.json`
   (216 campi su 217 hanno la descrizione di Kunos; l'unico senza è `deprecated_2`, che il documento
   lascia in bianco);
3. **le tabelle per vettura** (appendici 2-7) → `app/core/data/acc_riferimenti_vetture.json`:
   43 vetture con Kunos ID, **carModelId numerico**, offset del brake bias, coefficienti della
   pressione freni, angolo di sterzo massimo, giri massimi.

Il `carModelId` è il pezzo che mancava a **L1**: i risultati scritti dai *server* identificano la
vettura con un numero, e finora si sapeva solo dire «vettura 30».

### Due fatti verificati che hanno cambiato il progetto
- **La dimensione di una mappa non si può misurare.** Windows arrotonda ogni sezione alla pagina da
  4 KB: mappare gli 800 byte di ACC su una sezione da 712 (AC1) riesce, e la coda legge zeri senza un
  errore. Tutte e tre le pagine stanno sotto i 4 KB → nessun controllo sulla dimensione può
  accorgersi del gioco sbagliato. L'unica difesa è l'**identità dichiarata nella pagina statica**
  (`smVersion`, `acVersion`, `carModel`), che il lettore legge all'aggancio e riporta.
- **Si apre, non si crea.** `mmap` di Python, su Windows, *crea* la mappa se non esiste: agganciarsi
  così a un gioco spento dà una pagina di zeri che sembra telemetria buona. Si chiama direttamente
  `OpenFileMappingW`, che esiste solo per aprire.

### Che cosa si registra
**Tutti** i parametri che ACC riempie davvero: **211 colonne** (136 dalla pagina fisica, 75 dalla
grafica), ognuna con nome canonico, unità (con la provenienza: documento / uso comune / non
dichiarata) e descrizione ufficiale — è il **dizionario dei canali**, scritto accanto ai dati di ogni
sessione. Restano fuori, con la ragione scritta nel dizionario: i campi che il documento marca «non
usati da ACC» (sono zeri), le stringhe (i tempi esistono già in millisecondi) e le due tabelle delle
**altre** vetture in pista (`carCoordinates`, `carID`: 240 colonne che non parlano del pilota).

### Come finisce su disco
```
<PITWALL_SESSIONS_DIR>/telemetria/<id>/
    sessione.json     metadati, assunzioni, elenco ordinato delle colonne
    dizionario.json   i 211 canali con unità e descrizione, e le avvertenze
    canali.npz        due matrici compresse: float32 e int32
```
**Due matrici, non una:** i tempi in millisecondi passati per un float32 comincerebbero ad
arrotondare sopra i 16,7 milioni, e un tempo sul giro arrotondato è un dato falso. Si scrive **a
blocchi ogni minuto**: se il gioco si pianta si perde un minuto, non la sessione, e i blocchi rimasti
si consolidano dopo. Il **tetto** (`PITWALL_TELEMETRIA_MAX_SESSIONI`, default 40) libera solo i
canali grezzi delle più vecchie e lascia metadati e dizionario, marcati `canali_rimossi`: niente
sparisce di nascosto. ⚠️ **L'archivio va tenuto fuori da OneDrive** (`PITWALL_SESSIONS_DIR`): a
100 Hz sono ~290 MB/ora grezzi, che una cartella sincronizzata manderebbe in rete.

### Ciclo di vita
Thread dentro il backend (nessun eseguibile da distribuire, nessuna firma da comprare), avviato con
l'app e fermato con lei; si aggancia da solo quando il gioco compare, registra **solo in stato LIVE**
(non replay, non pausa), deduplica sui `packetId` e chiude la sessione dopo 20 s fuori pista.
Interruttore **`PITWALL_ALLOW_RECORDER`** (default acceso, da spegnere sul deploy vetrina).
Rotte: `GET /api/telemetria/stato`, `POST .../avvia`, `POST .../ferma`, `GET .../sessioni`,
`GET .../sessioni/{id}`, `GET .../sessioni/{id}/canali`, `DELETE .../sessioni/{id}`.

### L'analisi per curva (F3)
`app/analisi/curve.py`, deterministica e senza LLM, in quattro passaggi:
1. **i giri si ritagliano dalla posizione** (`normalizedCarPosition` che riparte da 0); conta solo
   chi ha la spazzata completa, e i giri passati dai box restano fuori;
2. **i canali si reindicizzano sulla distanza** su una griglia fissa (2000 punti ≈ 2,5 m su un
   tracciato da 5 km): confrontare due giri nel tempo non ha senso, sulla stessa posizione sì;
3. **le curve si ricavano dal profilo di velocità mediano** fra i giri buoni (decisione 4: nessun
   dato a mano per 25 circuiti). Ogni curva è il tratto fra il massimo di velocità che la precede e
   quello che la segue → **i tratti si toccano e coprono tutto il giro**, quindi nessun decimo può
   sparire fra due curve (c'è un test che somma i tratti e ritrova il tempo sul giro);
4. **la perdita si misura per tratto**, contro il miglior tempo del pilota su quel tratto.
Per ogni curva e giro: punto di frenata, velocità minima e dove cade, riapertura del gas, trail
braking, coasting, tempo e decimi persi. Il verdetto esce ordinato per gravità, ogni voce con il
numero che la prova e l'azione da fare.

**Aggiunta ai canali:** `pitwall.tempo_ms`, l'unico canale che non viene da ACC. La shared memory
non porta un orologio della registrazione (`iCurrentTime` azzera a ogni giro, `Clock` è l'ora del
mondo di gioco): senza, nessun conto sul tempo è possibile. È dichiarato nel dizionario come nostro.

**La lunghezza del tracciato non esiste in ACC** (`trackSplineLength` è fra i campi non riempiti):
viene stimata integrando la velocità sul giro migliore — sul banco di prova dà 2999,5 m su 3000
veri. Serve solo a esprimere le posizioni in metri; nessun conto dipende dalla sua esattezza.

**Come si prova senza ACC:** un tracciato finto (`app/tests/pista_finta.py`) con curve in posizioni
note. Su tre giri identici il verdetto è **vuoto** (nessun falso allarme); mettendo un errore solo
nella curva 2 (v-min 105 invece di 120 km/h, frenata 40 m prima) il giro perde 700 ms e l'analisi
ne attribuisce **698,5 a quella curva**, riconoscendo i punti di frenata a 1380 m e 1340 m — cioè
esattamente i valori impostati.

### Stato delle fasi di L3
- **F1 struttura + lettore** — fatta (`test_telemetria` 97/97)
- **F2 dizionario + registratore + archivio + rotte** — fatta (`test_registratore` 69/69)
- **F3 distanza, curve, analisi per curva, rotta `/curve`** — fatta (`test_curve` 62/62)
- **F4 bundle e report unico** — fatta (`test_telemetria_bundle` 50/50)

### F4 — una registrazione diventa una sessione come le altre
`bundle/adapters/acc_telemetria.py` trasforma i canali in un **session bundle**: stessi giri, stesso
formato, stesso archivio di un file importato da ACC. Da qui in poi non esistono più «le sessioni
importate» e «le registrazioni»: esistono le sessioni.
- il **tempo sul giro lo dice ACC** (`iLastTime`, lo stesso dei risultati), non il nostro cronometro;
  `pitwall.tempo_ms` fa da controprova e uno scarto oltre mezzo secondo viene **dichiarato**;
- il **consumo vero per giro** finalmente c'è: dai risultati di ACC non si poteva ricavare (il campo
  `fuel` è costante per giro), qui è la differenza del serbatoio fra inizio e fine giro;
- i canali **non entrano** nel bundle: entra il loro indirizzo (decine di MB restano dove sono);
- i giri incompleti (registrazione avviata a metà pista) restano contati ma senza tempo.

`analisi/gomme.py` aggiunge gomme e freni, con un limite scelto apposta: **la finestra di pressione
«ottimale» di una GT3 non è pubblicata da ACC**, quindi non si giudica contro una costante non
verificata. *(Superato il 16/09: la fonte Kunos esiste ed è stata trovata — vedi §11.)* Si misurano e si giudicano solo gli **squilibri** (ant/post, sx/dx) e le **tendenze**
(pressione che sale sullo stint): una differenza e una pendenza si dimostrano da sole. I valori
assoluti si riportano sempre. Quando la tabella delle finestre sarà verificata in gioco
(decisione 7), i giudizi assoluti si aggiungono lì, marcati come verificati.

`analisi/motore.py` accetta ora i canali: **il report cresce invece di cambiare**. Curve, gomme e
freni entrano nello **stesso verdetto**, ordinato per gravità insieme alle voci di ritmo e costanza —
un solo elenco di priorità, che è la differenza fra un cruscotto e un ingegnere. Senza canali il
motore si comporta esattamente come prima e dichiara che non erano collegati.
Rotte: `POST /api/telemetria/sessioni/{id}/importa` e `GET /api/sessions/{id}/analisi`, che include
curve e gomme quando i canali esistono ancora sul disco.

### Identificativi delle vetture: allineati (15/09)
Quattro vetture del catalogo avevano un `acc_car_id` che **non** è l'identificativo Kunos (ACC scrive
il nome della cartella, non quello del modello): `bentley_continental_gt3_2015` → `..._2016`,
`lexus_rcf_gt3` → `lexus_rc_f_gt3`, `nissan_gt_r_gt3_2015` → `..._2017`,
`reiter_engineering_r_ex_gt3` → `lamborghini_gallardo_rex`. Con quegli slug il setup importato da ACC
per quelle quattro non si agganciava al catalogo. Corretti in `cars.json` (l'`id` interno di PitWall
non è cambiato: foto, ritagli e range di setup restano dove sono).
Aggiunta la **lista ufficiale completa** (`acc_lista_vetture_handbook.json`, 54 vetture dall'ACC
Server Admin Handbook v1.10.2): copre anche le GT3 del 2023-24 e la classe GT2, e ora **31 vetture
su 31** del catalogo hanno il loro `carModelId`. L'adattatore dei risultati traduce il numero in
vettura; se un numero non è in lista, lo dichiara invece di indovinare.

## 11 · L4 — Gigi e le schermate sul bundle (16/09/2026)

Aperto con due giri di domande, tutte le proposte approvate e «ok procedi su tutto» (anche sui file
protetti: numeri demo, prompt, agente). Priorità dichiarata da Edoardo: **ristrutturare tutto e
verificare che funzioni senza difetti o sbavature nelle analisi**, come base per completare la build.

### Le soglie: una fonte primaria, e una community separata
La finestra delle gomme **è pubblicata da Kunos**: «Version 1.9 - Physics notes», PDF di Aristotelis
(staff Kunos) nel thread ufficiale del forum assettocorsa.net, 19/04/2023. Da lì, con la frase esatta
e la pagina, in `core/data/acc_riferimenti_fisica_v19.json`: **26–27 psi** in pista (dichiarata
*indicativa*), **70–100 °C al core** (tipica 80–90), superficie fra 50 e 120+ °C normale, **massimo
15 °C fra esterno e interno** (non esposto dalla shared memory: non misurabile), **pressioni diverse
fra gli assi = strumento di setup**, bumpstop 20–30 mm. Il PDF non è nel repo, solo i valori.
I valori che circolano fra piloti (freni ant. ≤650 °C e post. ≤450 °C, bagnato 29,5–31 psi, pastiglie
1–4) stanno in `acc_riferimenti_community.json` con `stato: "da_confermare"`, le fonti e i loro
limiti: si mostrano con l'etichetta «community», **mai nel verdetto**. Diventano verificati solo con
due fonti indipendenti più una conferma primaria (Kunos o lettura in gioco).

### Il motore, rivisto
- **Verdetto solo di perdite**; ciò che funziona va in `cosa_regge` con la sua prova. Un «Costanza
  solida» in cima a un elenco di problemi non ci finisce più.
- **Gomme contro la finestra Kunos** per *quota di tempo fuori* (>20% → voce), solo con mescola da
  asciutto, solo nei giri completi fuori dai box. Le voci portano `parametri` (es.
  `tire_press_rl: +0.6`) che la pagina Setup usa senza interpretare testo.
- **Squilibrio fra gli assi fuori dal verdetto** (Kunos: è uno strumento); fra i lati resta.
- **Pressioni che salgono**: voce solo se la salita porta fuori finestra (prima il verdetto poteva dire
  insieme «alza la pressione» e «parti più basso»).
- **Degrado dal giro migliore in poi**: i giri a gomme fredde facevano una «U» che nascondeva il calo
  (demo: R² 0,02 → 0,98). Gravità = perdita media a giro, stessa scala delle altre voci. Il campo
  `significativo` lo decide il motore. Un ritmo che **migliora** è un punto fermo con il suo nome, e
  la voce sulla costanza dice che parte della dispersione viene da lì.
- **Giro teorico** con `motivo_teorico` quando non si calcola; sotto i 100 ms dal reale non è una perdita.
- **Settori delle registrazioni** letti da `lastSectorTime` (durata ufficiale del settore): prima si
  usava `iSplit`, ambiguo, e il terzo settore andava perso → nessun giro teorico per le sessioni
  registrate. Il terzo, se manca il traguardo successivo, è ricavato per differenza e dichiarato.
- **Consumo** da `usedFuel` (litri, documentato) invece di `fuel` (kg per il documento).
- **Bug curva 1 / curva 12**: la gravità di una voce per curva si cercava nel titolo («curva 1» sta
  dentro «curva 12»). Ora la voce porta `curva` e `perdita_ms`.
- Il report porta `giri` (stato di ogni giro deciso dal motore): le schermate non ricalcolano niente.

### La demo è una sessione
`bundle/demo.py` genera una sessione DEMO nello stesso archivio (id fisso, data 2000 → in fondo
all'elenco): Monza con 7 curve nelle posizioni reali, velocità massima e perdite **calibrate** sui
tempi della storia (1:47.82 al giro 4, calo fino a 1:49.16), pressioni posteriori basse, Post.DX oltre
i 100 °C, consumo 3,2 l/giro, freni con picchi realistici. Il setup è un **file vero di ACC**. Nel repo
c'è il generatore, non i canali: si crea all'avvio, si ricrea se manca o se cambia versione, non si
cancella, non conta nel tetto dell'archivio. `core/demo_data.py` e `GET /api/session` sono spariti.

### Console e PC: due percorsi, un motore
Decisione di Edoardo: si chiede **dove gioca** (primo passo del wizard, o nella pagina Sessioni). Su
PC: import dei file e registratore. Su console: sessione manuale con tempi (facoltativi), setup
preparato nella pagina Setup e **racconto** per fasi (andamento, frenata, ingresso, centro, uscita,
gomme, curve critiche). Stesso bundle (`meta.piattaforma`, `racconto`), stesso motore, stesse schermate;
il report dichiara ciò che manca. `POST /api/sessions/manuale`.

### Gigi
Prompt **v5** (il v4 è cancellato): riceve report compresso, setup, racconto, profilo e domanda; cita
solo numeri presenti; riferimenti Kunos nel prompt; **5 sezioni**, nuova «Correzione di Guida». Con il
live spento: sulla DEMO la cache (riscritta sui numeri veri del report demo, 5 sezioni), sulle altre
sessioni la **risposta dal motore** (`analisi/gigi.py`, fonte `motore`) — prima avrebbe raccontato la
storia di Monza su qualunque sessione.

### Schermate
- **Selettore di sessione** nella Sidebar; `lib/sessione.tsx` condivide sessione e report fra tutte le
  pagine. Ultima sessione di default; in demo si parte dalla DEMO e la scelta vale per la visita.
- **Dashboard**: scheda sessione, verdetto (prime 5, espandibile), cosa regge, note sui dati, 7 KPI dal
  report (best, teorico, costanza, degrado, consumo, pressioni e temperature in finestra).
- **Telemetria**: tab Giri (tabella, delta, settori), Curve (riepilogo + due giri sovrapposti sulla
  distanza da `GET /api/sessions/{id}/tracce`), Gomme e freni (gauge con finestra Kunos neutra, serie
  per giro, freni con riferimento community tratteggiato).
- **Sessioni** (nuova): percorso PC, percorso console, archivio.
- **Setup**: parametri da toccare secondo il verdetto (click = applica la variazione), setup grezzo
  della sessione in lettura, «crea una sessione con questo setup».
- **Via** (conti nel browser o numeri scritti a mano): corsie, scatter, radar, channel report, heatmap,
  confronto metà stint, salute sessione, avvisi, consigli, finestra pressioni «a freddo», target fissi.

### Verifica
751 test offline, `tsc` 0 errori, backend e frontend vivi: tutte le pagine 200; controllate nel
browser Dashboard, Telemetria (3 tab), Console (5 sezioni, fonti demo e motore), Sessioni, Setup
(variazione applicata 24.2 → 24.8 psi), cambio di sessione e persistenza alla ricarica.
