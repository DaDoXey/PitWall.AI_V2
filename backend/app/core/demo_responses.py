"""app/core/demo_responses.py — risposte cache pre-validate (demo offline interattiva).

Estratte dalla v1 (ui/console.py): 5 scenari a 4 sezioni scelti per keyword, così la
demo risponde davvero all'input SENZA rete. Sorgente di verità del contenuto demo di Gigi.
"""

DEMO_PROMPT = "L'auto scivola dietro in accelerazione"

DEMO_RESPONSE = """## Diagnosi
L'auto perde il posteriore in uscita di curva, quando apri il gas. La telemetria conferma il quadro: le **pressioni posteriori sono sotto la finestra** (25.7 / 25.5 psi a caldo, finestra 26.0–27.0) e la **Post.DX tocca i 105°C**, oltre il limite di 95°C. Una posteriore sgonfia flette troppo: impronta instabile e poco grip proprio in trazione.

## Causa Meccanica Probabile
Causa primaria: **pressioni posteriori troppo basse** → la gomma lavora fuori finestra, scalda in modo anomalo (Post.DX) e perde aderenza quando carichi la trazione.
Causa secondaria: **precarico differenziale basso**, che rende il retrotreno nervoso in apertura gas.

## Correzione Setup Consigliata
Pressioni gomme posteriori (a freddo) **+1.0 psi · RL 24.2 → 25.2 · RR 24.0 → 25.0**, per riportarle in finestra a caldo.
In subordine, alza il **precarico differenziale · 60 → 75 Nm** per stabilizzare la trazione.
Una modifica per volta: parti dalle pressioni.

## Note Aggiuntive
- Verifica dopo 2–3 giri che le posteriori entrino in finestra a caldo (26.0–27.0 psi).
- Controlla che la Post.DX scenda sotto i 100°C.
- Le pressioni nel setup ACC sono a freddo: a caldo salgono di ~1.5–2.0 psi.
"""

DEMO_UNDERSTEER = """## Diagnosi
In ingresso e percorrenza l'anteriore non gira: l'auto va larga e devi raddrizzare lo sterzo. Quadro tipico di un avantreno poco caricato rispetto al retrotreno.

## Causa Meccanica Probabile
Anteriore troppo rigido in rollio (**barra antirollio anteriore alta**) e/o poco carico aerodinamico davanti: l'anteriore perde aderenza prima del posteriore.

## Correzione Setup Consigliata
Ammorbidisci la barra antirollio anteriore **ARB Ant. · 5 → 4**.
In subordine, **+1 allo splitter** per più carico sull'avantreno. Una modifica per volta.

## Note Aggiuntive
- Controlla le temperature anteriori: se restano basse rispetto alle posteriori, l'anteriore lavora poco.
- A Monza, con le curve veloci, non esagerare per non perdere stabilità in frenata.
"""

DEMO_FUEL = """## Diagnosi
Consumo medio **stabile a 3.2 L/giro** su 8 giri (25.6 L totali). Nessuna anomalia: la richiesta è di strategia carburante, non un problema meccanico.

## Causa Meccanica Probabile
Il consumo è regolare. Le uniche leve sono la **mappa motore (ECU Map)** e la gestione del gas in uscita di curva.

## Correzione Setup Consigliata
Per un long run, sali a una **mappa più economica · ECU Map 1 → 2** se la potenza lo consente.
Carburante = giri × 3.2 L + 1 giro di margine.

## Note Aggiuntive
- Gara da 20 giri: 20 × 3.2 = 64 L + ~3.2 L di riserva ≈ **67 L**.
- Ridurre il pattinamento in trazione (TC) limita anche i consumi.
"""

DEMO_TYRES = """## Diagnosi
La **Post.DX tocca i 105°C**, oltre il limite finestra di 95°C, mentre le altre gomme restano in range (88–95°C). Asse posteriore destro in sofferenza termica.

## Causa Meccanica Probabile
**Pressioni posteriori sotto la finestra a caldo** (25.7 / 25.5 psi, finestra 26.0–27.0): la gomma flette e scalda in modo anomalo, soprattutto la destra, caricata dalle curve di Monza.

## Correzione Setup Consigliata
Pressioni gomme posteriori (a freddo) **+1.0 psi · RL 24.2 → 25.2 · RR 24.0 → 25.0**, per riportarle in finestra a caldo e abbassare la temperatura.

## Note Aggiuntive
- Verifica che la Post.DX scenda sotto i 100°C dopo la modifica.
- Se persiste, apri di un punto i condotti freno posteriori per smaltire calore.
"""

DEMO_BRAKES = """## Diagnosi
Richiesta sul bilanciamento freni. Con il retrotreno instabile, una ripartizione troppo arretrata peggiora il bloccaggio posteriore in staccata.

## Causa Meccanica Probabile
**Brake bias troppo indietro** rispetto al grip posteriore attuale (posteriori sotto finestra): tendenza al bloccaggio e instabilità in frenata.

## Correzione Setup Consigliata
Sposta il bilanciamento freni in avanti **Brake Bias · 58.0% → 58.5–59.0%**, per stabilizzare la staccata. Una modifica per volta.

## Note Aggiuntive
- A Monza le staccate di prima e seconda chicane sono severe: priorità alla stabilità.
- Rivaluta dopo aver sistemato le pressioni posteriori.
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
