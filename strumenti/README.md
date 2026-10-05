# Strumenti

Gli attrezzi di lavoro di PitWall. Non fanno parte dell'app: servono a chi la sviluppa.
I comandi si lanciano dalla radice del repository.

| Comando | A cosa serve |
|---|---|
| `python strumenti/verifica.py` | **La verifica in un comando solo.** Test del backend, tipi del frontend, numeri dei documenti e, con i server accesi, pagine, cinque percorsi nel browser e catture su tre formati di schermo. Risponde verde o rosso |
| `python strumenti/verifica.py --veloce` | La stessa senza il browser. È quella che gira su GitHub a ogni push |
| `python strumenti/verifica.py --accetta-catture` | Le catture di ora diventano il termine di paragone per il giro dopo |
| `.\strumenti\server.ps1 avvia` · `ferma` · `riavvia` · `stato` | Accende e spegne backend e frontend. `riavvia` va fatto dopo ogni modifica al backend, alle guide o al catalogo |
| `python strumenti/guardiano.py --installa` | Attiva il guardiano dei commit in questo clone (una volta sola) |
| `python strumenti/numeri_documenti.py` | Riscrive nei README e in `docs/03` i conteggi dei test, ed elenca le rotte dell'API che mancano nelle tabelle |

## Il guardiano

Prima di ogni commit rifiuta: i **file protetti** (logica, prompt e numeri della demo: si toccano
solo con un «ok procedi», poi `PITWALL_OK_PROCEDI=1 git commit …`), i **file che non devono
entrare nel repository** (`.env`, report, strumenti locali, immagini scaricate) e qualunque testo
che somigli a una **chiave API**.

## Le catture

`frontend/e2e/catture/ora/` contiene le pagine fotografate a 1536×695, 1920×1080 e 1366×768;
`prima/` quelle del giro precedente. La verifica elenca le pagine **cambiate**: sono quelle da
guardare a schermo. Una pagina cambiata non è un errore; una pagina che scorre in orizzontale sì.
La cartella non è nel repository.

## Prima volta su un PC nuovo

```bash
cd frontend && npm install && npx playwright install chromium   # il browser di prova
python strumenti/guardiano.py --installa
```
