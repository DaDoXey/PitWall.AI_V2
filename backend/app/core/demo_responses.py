"""app/core/demo_responses.py — risposte cache pre-validate (demo offline interattiva).

Nate dalla v1 (ui/console.py): 5 scenari scelti per keyword, così la demo risponde
davvero all'input SENZA rete. Sorgente di verità del contenuto demo di Gigi.

**Riscritte il 16/09/2026 (L4, «ok procedi su tutto»)** per due motivi:
* il formato passa a **5 sezioni** (nuova «Correzione di Guida», come il prompt v5);
* la demo ora è una sessione analizzata dal motore (`bundle/demo.py`): ogni numero qui
  sotto è un numero che il report della demo contiene davvero. Via i valori di setup
  inventati («58.0%», «60 → 75 Nm»): il setup della demo è un file vero di ACC, in
  click non convertiti, quindi le correzioni si danno in click o in psi relativi.
  Via anche il «limite di 95°C»: la soglia ufficiale Kunos è 100 °C al core.
"""

DEMO_PROMPT = "L'auto scivola dietro in accelerazione"

DEMO_RESPONSE = """## Diagnosi
L'auto perde il posteriore in uscita di curva, quando apri il gas. I numeri della sessione lo confermano: le **pressioni posteriori sono sotto la finestra Kunos per il 100% del tempo** (media 25.4 / 25.2 psi in pista, finestra indicativa 26–27) e la **Post.DX sta sopra i 100 °C al core per il 38% del tempo**, fino a 105 °C a fine stint. Dal giro 4 il ritmo cala di 352 ms a giro.

## Causa Meccanica Probabile
Causa primaria: **pressioni posteriori troppo basse** → la gomma flette troppo, scalda (per Kunos meno pressione genera più calore) e in trazione perde precisione.
Causa secondaria, da verificare dopo: un retrotreno nervoso in apertura gas può dipendere anche dal precarico del differenziale.

## Correzione Setup Consigliata
- Pressioni posteriori a freddo: **circa +0.6 psi su Post.SX e +0.8 psi su Post.DX**, per portarle dentro 26–27 psi in pista.
- Solo se dopo resta nervoso in uscita: **+1 click di precarico** del differenziale. Una modifica per volta: parti dalle pressioni.

## Correzione di Guida
- **Parabolica (curva 7)**: perdi 0.18 s a giro, con la velocità minima che balla di 4 km/h fra i giri. Con il retrotreno così, apri il gas più progressivo fino a macchina dritta.
- **Variante del Rettifilo (curva 1)**: 0.17 s a giro, persi soprattutto nei primi giri a gomme fredde.

## Note Aggiuntive
- Dopo la modifica, controlla che le posteriori entrino in 26–27 psi in pista e che la Post.DX torni sotto i 100 °C al core.
- Le pressioni del setup sono a freddo: in pista salgono, quindi correggi sullo scarto misurato a caldo.
- Sessione demo sintetica: i canali sono generati da PitWall, il setup è un file vero di ACC.
"""

DEMO_UNDERSTEER = """## Diagnosi
Chiedi del sottosterzo, ma i numeri di questa sessione non lo mostrano: le perdite dimostrate stanno in uscita (Parabolica, Ascari) e sul retrotreno, con le **posteriori sotto la finestra di pressione** per tutta la sessione. Gli anteriori sono dentro la finestra Kunos (26–27 psi).

## Causa Meccanica Probabile
Se senti l'anteriore che non gira in ingresso, le cause tipiche sono un anteriore troppo rigido in rollio (**barra antirollio anteriore**) o poco carico aerodinamico davanti. In questa sessione però non c'è un numero che lo dimostri.

## Correzione Setup Consigliata
- Prima sistema il retrotreno (**circa +0.6 / +0.8 psi** a freddo su Post.SX / Post.DX): un posteriore che scivola cambia anche come senti l'anteriore.
- Se il sottosterzo resta: **-1 click di barra antirollio anteriore**, una modifica per volta.

## Correzione di Guida
- **Variante del Rettifilo (curva 1)**: 0.17 s a giro. Se l'auto va larga in ingresso, anticipa di poco il rilascio del freno per caricare l'anteriore.

## Note Aggiuntive
- Dimmi in che fase della curva lo senti (ingresso, centro, uscita): stringe la diagnosi.
- A Monza, con le curve veloci, non togliere stabilità al posteriore in frenata.
"""

DEMO_FUEL = """## Diagnosi
Consumo **stabile a 3.2 l/giro** su 8 giri (25.6 l totali), misurato giro per giro dal serbatoio. Nessuna anomalia: è una domanda di strategia, non un problema meccanico.

## Causa Meccanica Probabile
Il consumo è regolare. Le leve sono la **mappa motore** e la gestione del gas in uscita di curva, dove oggi perdi tempo alla Parabolica.

## Correzione Setup Consigliata
- Per un long run, una **mappa motore più economica** di un gradino, se la potenza lo consente.
- Carburante = giri × 3.2 l + 1 giro di margine.

## Correzione di Guida
- In uscita dalla Parabolica (curva 7) apri il gas più progressivo: con il posteriore che scivola spendi carburante e tempo (0.18 s a giro).

## Note Aggiuntive
- Gara da 20 giri: 20 × 3.2 = 64 l + un giro di riserva (3.2 l) ≈ **67 l**.
- Meno pattinamento in trazione significa anche meno consumo.
"""

DEMO_TYRES = """## Diagnosi
La **Post.DX sta sopra i 100 °C al core per il 38% del tempo** (media 95 °C, 105 °C a fine stint): fuori dalla finestra ufficiale Kunos di 70–100 °C. Le altre tre gomme restano dentro. Le **posteriori sono sotto la finestra di pressione per tutta la sessione** (media 25.4 / 25.2 psi).

## Causa Meccanica Probabile
**Pressioni posteriori sotto la finestra** (26–27 psi, indicativa): la gomma flette di più e per Kunos meno pressione genera più calore. La destra, più caricata a Monza, è quella che cuoce.

## Correzione Setup Consigliata
- Pressioni posteriori a freddo: **circa +0.6 psi su Post.SX e +0.8 psi su Post.DX**, per portarle dentro la finestra in pista e abbassare la temperatura.
- Se la Post.DX resta calda, rivedi campanatura e convergenza su quell'angolo: per Kunos decidono come si distribuisce il calore.

## Correzione di Guida
- Negli ultimi giri perdi fra Ascari (curva 6, 0.16 s a giro) e Parabolica (curva 7, 0.18 s): meno slittamento in uscita vuol dire meno calore sulla Post.DX.

## Note Aggiuntive
- Controlla dopo la modifica che la Post.DX torni sotto i 100 °C al core.
- La differenza fra esterno e interno del battistrada (max 15 °C per Kunos) la telemetria non la espone: guardala nel garage di ACC.
"""

DEMO_BRAKES = """## Diagnosi
Freni in temperatura: massime di **649 °C davanti e 458 °C dietro**. I valori che circolano nella community (fino a circa 650 °C davanti e 450 °C dietro) sono **da confermare**: Kunos non pubblica una finestra per i freni. Il problema dimostrato resta il retrotreno, con le posteriori sotto la finestra di pressione.

## Causa Meccanica Probabile
Con un posteriore poco sostenuto, una ripartizione troppo arretrata rende la staccata instabile e favorisce il bloccaggio dietro.

## Correzione Setup Consigliata
- Prima le pressioni posteriori: **circa +0.6 / +0.8 psi** a freddo su Post.SX / Post.DX.
- Se la staccata resta nervosa: **bilanciamento freni avanti di 1–2 click**. Una modifica per volta.

## Correzione di Guida
- **Variante del Rettifilo (curva 1)**: 0.17 s a giro. Frena sempre sullo stesso riferimento e rilascia progressivo: prima la ripetibilità, poi il ritardo della staccata.

## Note Aggiuntive
- A Monza le staccate delle varianti sono le più severe: priorità alla stabilità.
- Le soglie dei freni della community restano etichettate «da confermare» finché non c'è una fonte primaria.
"""

# (keyword) → testo. Ordine = priorità di match. Default = scenario sovrasterzo.
_DEMO_ROUTES = [
    (("sottosterz", "sotto sterz", "non gira", "va largo"), DEMO_UNDERSTEER),
    (("carburant", "benzina", "fuel", "consum", "strategia"), DEMO_FUEL),
    (("gomm", "pneumatic", "tyre", "temperatur", "termic"), DEMO_TYRES),
    (("fren", "brake", "bilanciament", "staccata", "bloccagg"), DEMO_BRAKES),
    (("sovrasterz", "scivola", "perde il posteriore", "trazione", "dietro"), DEMO_RESPONSE),
]


def pick_demo_response(prompt: str) -> str:
    """Sceglie la risposta cache più pertinente all'input."""
    p = (prompt or "").lower()
    for keys, text in _DEMO_ROUTES:
        if any(k in p for k in keys):
            return text
    return DEMO_RESPONSE


def is_demo_prompt(prompt: str) -> bool:
    """True se l'utente ha scritto (almeno) l'intero prompt demo canonico."""
    import re
    norm = re.sub(r"[^a-z]", "", (prompt or "").lower())
    demo_norm = re.sub(r"[^a-z]", "", DEMO_PROMPT.lower())
    return demo_norm in norm
