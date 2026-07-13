# INCIDENTS — PitWall.AI **v2** (Next.js + FastAPI)
**Corso:** AI Projects Development — ITS ICT Academy Roma
**Autore:** Ferlito Edoardo
**Aperto:** 10/07/2026 (ricostruito da git log + report di stato)
**Repo:** github.com/DaDoXey/PitWall.AI_V2

> Registro dei **malfunzionamenti gravi** della v2 (Gigi non risponde, rottura backend/frontend,
> dati corrotti, vulnerabilità, hazard operativi). **NON** i fix brevi/cosmetici: quelli stanno nel
> `PROMPT_LOG.md`. L'`INCIDENTS.md` della v1 non è presente su questo PC (era sull'altro, dismesso):
> gli item v1 in coda sono ricostruiti dal `PROMPT_LOG.md` della v1.

## Come usare questo file
Un incidente = un problema **grave** (blocca/degrada l'app, corrompe dati, o è un rischio di sicurezza).
Per ognuno: **ID · Data · Severità · Stato · Area · Sintomo · Causa radice · Impatto · Risoluzione/Workaround · File · Riferimenti**.
- **Severità:** 🔴 Critico (app/demo rotta) · 🟠 Alto (funzione chiave degradata o rischio sicurezza) · 🟡 Medio (difetto reale, impatto limitato/circoscritto).
- **Stato:** `APERTO` · `IN LAVORAZIONE` · `RISOLTO` · `MITIGATO`.
- **ID:** `INC-V2-00X` per gli incidenti, `HAZARD-V2-X` per gli hazard/near-miss operativi.

---

## 🔴🟠 Incidenti APERTI

### INC-V2-002 — Mojibake `track_nick` servito da `GET /api/session`
| | |
|---|---|
| **Data** | rilevato 09/07/2026 · **Stato:** 🟡 Medio · `APERTO` |
| **Area** | Backend / dati demo (**file protetto**) |

- **Sintomo:** `GET /api/session` ritorna `track_nick` = "Tempio della Velocità" **mal-codificato**
  (doppia codifica UTF-8, byte verificati `ï¿½\xa0`).
- **Causa radice:** stringa salvata con doppia codifica UTF-8 in `demo_data.py`.
- **Impatto:** oggi il campo **non è renderizzato** in UI → nessun difetto visibile, ma l'API serve un
  **dato corrotto**; diventerebbe visibile appena lo si mostrasse.
- **Workaround:** nessuno necessario (campo inutilizzato).
- **Risoluzione:** APERTA — richiede STOP gate + «ok procedi» (file protetto). Fix = ricodifica corretta della stringa.
- **File:** `backend/app/core/demo_data.py`.
- **Rif.:** MEGAPROMPT_STATE_REPORT §6 B1.

### INC-V2-003 — Override `car_setup_ranges.json` no-op (la vettura non cambia i 49 parametri)
| | |
|---|---|
| **Data** | rilevato 09/07/2026 · **Stato:** 🟡 Medio · `APERTO` |
| **Area** | Backend / dati ACC (protetto-adiacente) |

- **Sintomo:** selezionare un'altra vettura nel Setup **non** cambia i range/default dei 49 parametri.
- **Causa radice:** gli override sono tutti placeholder `DA_VERIFICARE` → `get_params_for_car(car,track)`
  ricade sempre sul set generico.
- **Impatto:** la selezione vettura è **cosmetica**; i range non riflettono la vettura scelta. Accettabile
  nella demo blindata (Monza · BMW M4 GT3), ma blocca l'uso multi-vettura reale.
- **Risoluzione:** APERTA — servono i **valori ACC reali** confermati dall'utente (dato di dominio).
- **File:** `backend/app/core/data/car_setup_ranges.json`.
- **Rif.:** MEGAPROMPT_STATE_REPORT §6 B2.

### INC-V2-005 — Dashboard: le card ingrandite non si riposizionano col drag&drop
| | |
|---|---|
| **Data** | 10/07/2026 · **Stato:** 🟡 Medio · `IN LAVORAZIONE` (rework #8) |
| **Area** | Frontend / Dashboard (DnD) |

- **Sintomo:** ingrandendo una card a `col-span-2` e trascinandola, **non si sposta dove atteso**.
- **Causa radice (diagnosticata):** il riordino usa l'**indice dell'array**; con card a span variabile la
  **posizione visiva** nel grid non coincide con l'indice → il drop calcola una posizione errata.
- **Impatto:** funzione drag&drop inaffidabile con layout a taglie miste.
- **Workaround:** riordinare senza card estese.
- **Risoluzione:** pianificata nel **megaprompt #3 (#8)** — DnD basato sulla **posizione del puntatore**
  (insertion index dalle bounding box) o adozione di **`dnd-kit`**.
- **File:** `frontend/src/app/page.tsx` (`onDragStart`/`onDragOver`/`onDrop`, `reorder`).
- **Rif.:** REDESIGN_REWORK_REPORT §2 REWORK #8.

---

## ✅ Incidenti RISOLTI

### INC-V2-006 — Modal "Confronto metà stint" coperto dalle card KPI in Dashboard
| | |
|---|---|
| **Data** | rilevato 13/07/2026 (screenshot 10:53) · risolto 13/07/2026 · **Stato:** 🟡 Medio · `RISOLTO` |
| **Area** | Frontend / Sidebar + overlay (stacking context) |

- **Sintomo:** aprendo "⇄ Confronto" dalla Dashboard, il modal (`fixed inset-0 z-50`) veniva
  **sovrapposto dalle card KPI** (grafico visibile solo nei varchi tra le card); sulle altre
  pagine il modal appariva integro. Anche il backdrop non copriva davvero la pagina.
- **Causa radice:** il modal era montato **dentro** `<aside className="sticky …">` della Sidebar.
  `position: sticky` crea **sempre** uno stacking context (spec CSS) → lo `z-50` del modal valeva
  solo all'interno dell'aside, che nel contesto radice sta a livello `auto` e viene dipinta
  **prima** del `<main>` (ordine DOM). Le card KPI della Dashboard hanno il wrapper
  `position: relative` (drag&drop) → da elementi posizionati successivi nel DOM passavano sopra
  l'intero subtree della Sidebar, modal incluso. Solo in Dashboard perché è l'unica pagina con
  card posizionate nell'area del modal; il KpiModal (stesso idioma `z-50`) non soffre perché è
  montato nel `main`, **dopo** le card.
- **Impatto:** funzione Confronto inutilizzabile dalla Dashboard (la pagina di partenza tipica);
  nessun dato errato.
- **Workaround (pre-fix):** aprire il confronto da un'altra pagina.
- **Risoluzione:** RISOLTO — il blocco `AnimatePresence` + modal è renderizzato in **portale React
  su `document.body`** (`createPortal`, guard `mounted` anti-SSR): fuori dallo stacking context
  dell'aside lo `z-50` torna a valere a livello viewport su tutte le pagine, e il backdrop copre
  anche la Sidebar (comportamento modale corretto).
- **File:** `frontend/src/components/ui/Sidebar.tsx` (solo; `StintCompare.tsx` intatto).
- **Rif.:** PROMPT_LOG Entry #015 · screenshot `Screenshot 2026-07-13 105342.png`.

### INC-V2-004 — Login espone la Sidebar dell'app (manca auth-gate reale)
| | |
|---|---|
| **Data** | rilevato 09/07/2026 · risolto 11/07/2026 · **Stato:** 🟡 Medio · `RISOLTO` |
| **Area** | Frontend / routing + auth |

- **Sintomo:** la rotta `/login` renderizzava la **Sidebar** applicativa; nessun confine tra ingresso e app.
- **Causa radice:** `app/layout.tsx` montava `Sidebar` su **ogni** rotta.
- **Impatto:** login non isolata (incoerenza UX), assenza di confine auth.
- **Risoluzione:** RISOLTO (megaprompt #6, **FASE 8**) — **route group**: `app/(app)/` (Sidebar + main; pagine spostate con `git mv`) e `app/(auth)/login/` (layout pulito, card centrata full-screen); root layout ridotto a fonts+globals. URL invariati; rotte 200; `tsc` 0 err (puliti i tipi stale in `.next/types` post-spostamento).
- **Nota di scope (decisione di progetto, megaprompt #6 §1):** la parte "auth-gate reale" è **deliberatamente esclusa** — Google Sign-In reale in FASE 9 ma **senza** sessione server né protezione route (login dimostrativo; contenimento rischio pre-esame 15/07). Non è un residuo dimenticato.
- **File:** `frontend/src/app/layout.tsx` · `app/(app)/layout.tsx` (new) · `app/(auth)/layout.tsx` (new) · `app/(auth)/login/page.tsx`.
- **Rif.:** MEGAPROMPT_STATE_REPORT §6 A2 · PROMPT_LOG Entry #008 (F8).

### INC-V2-001 — Next.js 15.1.3 vulnerabile (CVE-2025-66478)
| | |
|---|---|
| **Data** | 08/07/2026 · **Stato:** 🟠 Alto · `RISOLTO` |
| **Area** | Frontend / supply-chain (dipendenza core) |

- **Sintomo:** lo scaffold iniziale (`336ec6a`) fissava **Next.js 15.1.3**, colpita da **CVE-2025-66478**.
- **Causa radice:** versione di default del template al momento dello scaffold.
- **Impatto:** vulnerabilità nota nella dipendenza core del frontend prima ancora delle feature.
- **Risoluzione:** bump **`15.1.3 → 15.5.20`** + rigenerazione `package-lock.json` (commit **`acd8a44`**, 08/07).
- **File:** `frontend/package.json`, `frontend/package-lock.json`.
- **Rif.:** commit `acd8a44` "chore(frontend): Next 15.1.3 -> 15.5.20 (CVE-2025-66478)".

> _Difetti minori risolti (sparkline gradient reso statico in megaprompt #2, ecc.) sono fix brevi e
> stanno nel `PROMPT_LOG.md`, non qui._

---

## ⚠️ Hazard / near-miss operativi

### HAZARD-V2-A — `npm run build` con `npm run dev` attivo corrompe `.next`
| | |
|---|---|
| **Stato** | `MITIGATO` (procedura) · **Area:** Frontend / build |

- **Sintomo:** lanciare `npm run build` mentre `npm run dev` è attivo **corrompe la cartella `.next`** → dev instabile / build fallata.
- **Mitigazione (procedura fissa):** con il dev server attivo usare **solo** `npx tsc --noEmit` per la verifica; **mai** `npm run build`. Regola ripetuta in `PROMPT_LOG.md`, session-cache e report.

### HAZARD-V2-B — `uvicorn --reload` su Windows serve codice **stale** dopo modifica backend
| | |
|---|---|
| **Stato** | `MITIGATO` (procedura) · **Area:** Backend / dev server |

- **Sintomo:** dopo aver modificato `demo_data.py`/`session.py` (FASE 7), `GET /api/session` **non** esponeva
  `lap_times` benché l'import diretto della funzione (`app.api.session.get_session()`) lo restituisse
  correttamente. WatchFiles stampava «detected changes … Reloading» ma la risposta HTTP restava vecchia.
- **Causa radice:** reloader **WatchFiles** di uvicorn inaffidabile su Windows — reload segnalato ma il
  processo di serving non rigenerato col nuovo modulo.
- **Impatto:** verifica a endpoint **fuorviante** (sembrava un bug del codice, mentre il codice era corretto).
  Nessun dato corrotto, nessun impatto sul deliverable.
- **Mitigazione (procedura):** confermare le modifiche backend con **import diretto** della funzione +
  `curl` **dopo** un **riavvio pulito** del backend **senza `--reload`** (kill processo + relaunch).
- **Rif.:** PROMPT_LOG Entry #007 (megaprompt #5, FASE 7), verifica.

---

## 🗄️ Eredità v1 (contesto — NON incidenti v2)

Ricostruiti dal `PROMPT_LOG.md` della v1 (Streamlit); riguardano **Gigi** e la robustezza, utili come storia del progetto.

- **INC-003 (v1) — Deploy Streamlit stale → "Gigi non risponde":** sul deploy pubblico Gigi sembrava
  non rispondere perché il deploy Streamlit Cloud non era allineato al `main` corretto. **Risolto** con ri-deploy.
- **INC-004 (v1) — Engineer Console percepita statica:** in demo-mode tornava sempre la stessa analisi e
  l'input era poco visibile → sensazione di "Gigi bloccato". **Risolto** con 5 risposte-cache per scenario
  (router per keyword) + input inline «⚙ ANALIZZA».
- **Manutenzione Git (v1, 02/07):** ref locali `main`/`origin/main` **azzerate** da crash filesystem →
  ripristinate a `e9115cb` **senza perdita dati**.

> ⚠️ **Nota di completezza:** in v2 **non ho evidenza** di un malfunzionamento runtime di Gigi (la Console
> è cablata a `POST /api/analysis` con cache demo; nessun crash registrato nel git log). Se hai visto a
> schermo un incidente v2 che non risulta qui (es. Gigi che non risponde, errore backend/frontend),
> **dimmelo**: lo aggiungo come `INC-V2-00X` con i dettagli reali invece di inventarlo.

---

<!-- TEMPLATE — copia per ogni nuovo incidente

### INC-V2-00X — [titolo breve]
| | |
|---|---|
| **Data** | GG/MM/AAAA · **Stato:** 🔴/🟠/🟡 · APERTO/IN LAVORAZIONE/RISOLTO/MITIGATO |
| **Area** | [backend / frontend / dati / auth / build …] |

- **Sintomo:**
- **Causa radice:**
- **Impatto:**
- **Workaround:**
- **Risoluzione:**
- **File:**
- **Rif.:**

-->
