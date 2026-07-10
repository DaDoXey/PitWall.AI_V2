# PitWall.AI — Riferimento di design & data-viz

> **Riferimento primario permanente: MoTeC i2 Pro.** Da qui in avanti, MoTeC i2 Pro è il riferimento
> per **ogni grafico, gauge e tabella** di PitWall.AI — **non solo per un singolo megaprompt, ma per
> tutti gli sviluppi futuri**. Documento non protetto: aggiornabile quando la direzione evolve.

## Vincolo di stile (non negoziabile)

Lo stile resta **quello di PitWall**: strumento analogico da pit wall — **il colore comunica solo lo
stato** (ok/warn/alarm/cold), **niente glow/drop-shadow**, **griglia hairline**, **assi sempre scalati
con unità visibili**, **numerici in monospace**. MoTeC informa **precisione dei dati, rigore degli assi
e layout** — **non è uno skin da copiare 1:1**. Palette e token restano quelli di
[`src/lib/instrument.ts`](../src/lib/instrument.ts) (`STATE`, `INSTRUMENT`, `STROKE`) e
[`src/lib/theme.ts`](../src/lib/theme.ts); le durate/easing da `src/lib/motion.ts`. **Non reinventare i token.**

Standard di qualità già raggiunto e da usare come metro per tutto il resto: i **gauge pressioni gomme**
a lancetta (needle gauge puliti).

## Componenti MoTeC i2 Pro di riferimento

- **Time/Distance Graph** — traccia canali nel tempo o sulla distanza; modalità *tiled* (impilate) e
  *overlap* (sovrapposte); doppio cursore con **delta automatico**; overlay **min/max/avg**; griglia
  hairline; assi sempre scalati con unità.
- **Channel Report** — statistiche per giro/sezione (**min / max / avg / delta**); disponibile sia in
  forma **tabellare** sia **grafica** (barre). → riferimento per la tabella "Dati giro-per-giro".
- **Time Variance Plot** — tempo **guadagnato/perso** tra giri lungo la distanza.
- **Track Report** — statistiche come **gradiente colore** sulla mappa del tracciato.
- **Scatter / XY Plot** — relazione tra due canali (es. *traction circle*: G laterale vs longitudinale).
- **Histogram** — distribuzione di frequenza di un canale.
- **Gauge** — a lancetta / lineari / bussola; lettura analogica immediata.
- **Values window** — lista numerica live dei canali (lettura puntuale).

## Come applicarlo in PitWall

- **Assi:** sempre scalati, con **unità** e tick leggibili (min/mid/max reali del canale); niente tick
  auto illeggibili. Griglia hairline (`INSTRUMENT.grid`), no glow.
- **Statistiche:** dove ha senso, esporre **min/max/avg/delta** in stile Channel Report (tabellare e/o a barre).
- **Cursore/lettura:** puntuale e con delta quando servono confronti (stile doppio cursore i2).
- **Colore = stato:** solo `STATE` sugli elementi dato; il resto in scala di grigi.
- **Coerenza:** ogni nuovo grafico/tabella si misura contro questo doc prima di essere considerato "fatto".

_Ultimo aggiornamento: 10/07/2026 (megaprompt di rifinitura MoTeC-style, FASE 1)._
