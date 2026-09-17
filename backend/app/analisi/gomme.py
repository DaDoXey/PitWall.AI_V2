"""Gomme e freni dai canali registrati (L3 · Fase 4, rivisto in L4 · Fase 1).

Era la promessa del rework: «il registratore sblocca gomme, pressioni, freni e il
consumo vero». Questo modulo è la parte gomme e freni.

**Contro che cosa si giudica.** Solo contro ciò che Kunos ha pubblicato: il documento
«Version 1.9 - Physics notes» (forum ufficiale, 19/04/2023) indica **26-27 psi** di
pressione e **70-100 °C al core** per le gomme da asciutto, chiamandoli *indicativi*.
Le soglie stanno in `core/data/acc_riferimenti_fisica_v19.json`, con la frase da cui
vengono; qui non c'è nessun numero scritto a mano.

Tre conseguenze, tutte volute:

* **si giudica la quota di tempo fuori finestra**, non il singolo campione: una
  finestra indicativa sfiorata per un giro non è un difetto, una ruota che passa un
  terzo della sessione sopra i 100 °C sì. La soglia (`QUOTA_FUORI_FINESTRA`) è
  dichiarata;
* **la finestra vale solo per la mescola da asciutto.** Sul bagnato Kunos non ha
  pubblicato niente: si riportano i valori, e il riferimento community resta
  un'etichetta, mai un giudizio;
* **una differenza di pressione fra gli assi non è un errore.** Il documento Kunos la
  descrive come uno strumento di setup (più rotazione dal posteriore): si misura e si
  riporta, ma nel verdetto non entra. Lo squilibrio fra **sinistra e destra** invece
  resta, perché nessuno lo giustifica.

I campioni che contano sono quelli dei **giri completi fuori dai box**: un out lap a
gomme fredde non è una sessione giocata fuori finestra.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

import numpy as np

from app.core import riferimenti_fisica as rif

RUOTE = ("FL", "FR", "RL", "RR")
NOMI_RUOTE = {"FL": "Ant.SX", "FR": "Ant.DX", "RL": "Post.SX", "RR": "Post.DX"}
# Il parametro del setup (stessi nomi dei 49 parametri) che regola la pressione di una ruota.
PARAMETRO_PRESSIONE = {r: f"tire_press_{r.lower()}" for r in RUOTE}

PRESSIONE = "physics.wheelPressure"
# `TYRE_TAIR` dei file MoTeC di ACC (L5): temperatura della gomma NON dichiarata come
# temperatura al core. Si riporta a parte e non si giudica mai contro la finestra Kunos.
TEMP_GOMMA_MOTEC = {"FL": "motec.TYRE_TAIR_LF", "FR": "motec.TYRE_TAIR_RF",
                    "RL": "motec.TYRE_TAIR_LR", "RR": "motec.TYRE_TAIR_RR"}
TEMP_GOMMA = "physics.tyreCoreTemp"
TEMP_FRENO = "physics.brakeTemp"
PASTIGLIE = "physics.padLife"
DISCHI = "physics.discLife"
GOMME_DA_PIOGGIA = "graphics.rainTyres"

ASCIUTTO = "asciutto"
BAGNATO = "bagnato"

# Oltre questa quota del tempo in pista fuori dalla finestra ufficiale, la ruota entra
# nel verdetto. Sotto, è la finestra «indicativa» che fa il suo mestiere.
QUOTA_FUORI_FINESTRA = 0.20
# Squilibrio fra i lati che entra nel verdetto (psi).
SQUILIBRIO_LATI_PSI = 0.3
# Crescita della pressione giro su giro, dopo il primo giro utile (psi/giro).
CRESCITA_PRESSIONE_PSI_GIRO = 0.08
# La gravità delle voci gomme non è un tempo: è una scala convenzionale, dichiarata,
# tarata perché un problema di gomme serio (un terzo della sessione fuori finestra)
# pesi come qualche decimo al giro.
GRAVITA_PER_QUOTA_FUORI = 600.0
GRAVITA_PER_PSI_LATI = 200.0
GRAVITA_PER_PSI_GIRO = 400.0


@dataclass
class PerRuota:
    FL: float | None = None
    FR: float | None = None
    RL: float | None = None
    RR: float | None = None

    @classmethod
    def da_valori(cls, valori: list[float | None], cifre: int = 2) -> "PerRuota":
        return cls(*[None if v is None else round(float(v), cifre) for v in valori])

    def come_lista(self) -> list[float | None]:
        return [self.FL, self.FR, self.RL, self.RR]


@dataclass
class Finestra:
    """Quanto tempo ogni ruota passa sotto, dentro e sopra la finestra ufficiale."""

    grandezza: str                 # "pressione" | "temperatura_core"
    min: float
    max: float
    unita: str
    fonte: str
    sotto_pct: PerRuota
    dentro_pct: PerRuota
    sopra_pct: PerRuota
    # Le ruote oltre la soglia di tempo fuori (QUOTA_FUORI_FINESTRA): quelle che
    # entrano nel verdetto. Deciso qui, mostrato dalle schermate.
    ruote_fuori: list[str] = field(default_factory=list)


@dataclass
class Gomme:
    pressione_media: PerRuota
    pressione_minima: PerRuota
    pressione_massima: PerRuota
    temperatura_media: PerRuota
    temperatura_massima: PerRuota
    mescola: str | None = None
    squilibrio_ant_post_psi: float | None = None
    squilibrio_sx_dx_psi: float | None = None
    squilibrio_temp_ant_post_c: float | None = None
    squilibrio_temp_sx_dx_c: float | None = None
    pendenza_pressione_psi_giro: float | None = None
    misurato_su_giri: int = 0
    finestra_pressione: Finestra | None = None
    finestra_temperatura: Finestra | None = None
    nota_assi: str = (
        "Pressioni diverse fra anteriore e posteriore sono uno strumento di setup per "
        "Kunos (più rotazione dal posteriore): si riportano, non si giudicano."
    )
    nota_finestra: str = ""
    # Solo per i file MoTeC: `TYRE_TAIR`, fuori da ogni giudizio (decisione del 17/09).
    temperatura_motec_media: PerRuota | None = None
    temperatura_motec_massima: PerRuota | None = None
    nota_temperatura_motec: str | None = None


@dataclass
class Freni:
    temperatura_media: PerRuota
    temperatura_massima: PerRuota
    squilibrio_ant_post_c: float | None = None
    pastiglie_consumate_mm: PerRuota | None = None
    dischi_consumati_mm: PerRuota | None = None
    riferimento_community: dict[str, Any] | None = None


@dataclass
class GiroGomme:
    """Le medie di un giro: la stessa cifra che le schermate disegnano giro per giro."""

    giro: int
    pressione: PerRuota
    temperatura: PerRuota
    freni_max: PerRuota


@dataclass
class VoceGomme:
    titolo: str
    prova: str
    azione: str
    gravita: float
    fonte: str = "misura"          # "misura" | "kunos"
    # I parametri del setup che la voce tocca, con la variazione consigliata nella
    # loro unità (psi) o None se la direzione c'è ma il numero no. La pagina Setup li
    # evidenzia senza dover interpretare il testo.
    parametri: dict[str, float | None] = field(default_factory=dict)


@dataclass
class ReportGommeFreni:
    gomme: Gomme | None
    freni: Freni | None
    per_giro: list[GiroGomme] = field(default_factory=list)
    voci: list[VoceGomme] = field(default_factory=list)
    punti_fermi: list[dict[str, str]] = field(default_factory=list)
    dati_mancanti: list[str] = field(default_factory=list)

    def come_json(self) -> dict[str, Any]:
        return {
            "gomme": asdict(self.gomme) if self.gomme else None,
            "freni": asdict(self.freni) if self.freni else None,
            "per_giro": [asdict(g) for g in self.per_giro],
            "voci": [asdict(v) for v in self.voci],
            "punti_fermi": list(self.punti_fermi),
            "dati_mancanti": self.dati_mancanti,
        }


def _colonne(canali: dict[str, np.ndarray], base: str) -> list[np.ndarray] | None:
    serie = [canali.get(f"{base}.{ruota}") for ruota in RUOTE]
    if any(s is None or s.size == 0 for s in serie):
        return None
    return [np.asarray(s, dtype=np.float64) for s in serie]


def _pendenza(valori: np.ndarray, giri: np.ndarray) -> float | None:
    """Quanto cresce una grandezza per giro. Regressione lineare, niente di più."""
    if valori.size < 3 or np.unique(giri).size < 3:
        return None
    coefficienti = np.polyfit(giri, valori, 1)
    return float(coefficienti[0])


def _ruote(nomi: list[str]) -> str:
    return ", ".join(NOMI_RUOTE[r] for r in nomi)


def mescola_dai_canali(canali: dict[str, np.ndarray]) -> tuple[str | None, str | None]:
    """(mescola, nota). La mescola dal canale `rainTyres`, se c'è e non cambia."""
    serie = canali.get(GOMME_DA_PIOGGIA)
    if serie is None or serie.size == 0:
        return None, "mescola non registrata"
    valori = np.unique(np.asarray(serie).astype(np.int64))
    if valori.size > 1:
        return None, "mescola cambiata durante la registrazione"
    return (BAGNATO if int(valori[0]) else ASCIUTTO), None


def maschera_giri_utili(n_campioni: int, giri) -> np.ndarray | None:
    """True sui campioni dei giri completi fuori dai box. None se non ci sono giri."""
    if giri is None:
        return None
    maschera = np.zeros(n_campioni, dtype=bool)
    for giro in giri:
        if giro.completo and not giro.ai_box:
            maschera[giro.inizio:giro.fine] = True
    return maschera


def _finestra(grandezza: str, serie: list[np.ndarray], minimo: float, massimo: float,
              unita: str) -> Finestra:
    sotto, dentro, sopra = [], [], []
    for valori in serie:
        n = max(1, valori.size)
        quanti_sotto = float(np.sum(valori < minimo)) / n
        quanti_sopra = float(np.sum(valori > massimo)) / n
        sotto.append(100 * quanti_sotto)
        sopra.append(100 * quanti_sopra)
        dentro.append(100 * (1 - quanti_sotto - quanti_sopra))
    return Finestra(
        grandezza=grandezza, min=minimo, max=massimo, unita=unita,
        fonte=rif.citazione_fonte(),
        sotto_pct=PerRuota.da_valori(sotto, 1),
        dentro_pct=PerRuota.da_valori(dentro, 1),
        sopra_pct=PerRuota.da_valori(sopra, 1),
        ruote_fuori=[r for r, s, o in zip(RUOTE, sotto, sopra)
                     if max(s, o) / 100 >= QUOTA_FUORI_FINESTRA],
    )


def _voci_finestra(finestra: Finestra, serie: list[np.ndarray]) -> list[VoceGomme]:
    """Una voce per direzione (sotto/sopra), con tutte le ruote coinvolte."""
    voci: list[VoceGomme] = []
    etichetta = "di pressione" if finestra.grandezza == "pressione" else "di temperatura al core"
    formato = "{:.1f}" if finestra.grandezza == "pressione" else "{:.0f}"
    for direzione, quote in (("sotto", finestra.sotto_pct), ("sopra", finestra.sopra_pct)):
        coinvolte = [(r, q) for r, q in zip(RUOTE, quote.come_lista())
                     if q is not None and q / 100 >= QUOTA_FUORI_FINESTRA]
        if not coinvolte:
            continue
        peggiore = max(q for _, q in coinvolte)
        ruote = [r for r, _ in coinvolte]
        medie = {r: float(np.mean(serie[RUOTE.index(r)])) for r in ruote}
        confine = finestra.min if direzione == "sotto" else finestra.max
        segno = 1.0 if direzione == "sotto" else -1.0
        if finestra.grandezza == "pressione":
            parametri = {PARAMETRO_PRESSIONE[r]: round(segno * abs(medie[r] - confine), 1)
                         for r in ruote}
        else:
            # Temperatura: la direzione è nota (più pressione raffredda, meno scalda),
            # il valore no.
            parametri = {PARAMETRO_PRESSIONE[r]: None for r in ruote}
        dettaglio = " · ".join(
            f"{NOMI_RUOTE[r]} {q:.0f}% del tempo (media {formato.format(medie[r])} {finestra.unita})"
            for r, q in coinvolte)
        if finestra.grandezza == "pressione":
            quanto = ", ".join(f"{abs(parametri[PARAMETRO_PRESSIONE[r]]):.1f} psi su {NOMI_RUOTE[r]}"
                               for r in ruote)
            azione = (
                f"{'Alza' if direzione == 'sotto' else 'Abbassa'} la pressione a freddo di "
                f"circa {quanto}, a meno che non sia una scelta "
                f"voluta: Kunos indica {finestra.min:.0f}-{finestra.max:.0f} psi, "
                f"{'e sotto la gomma flette di più e scalda di più' if direzione == 'sotto' else 'e sopra la gomma è più precisa ma scalda meno'}."
            )
        else:
            azione = (
                f"{'Gomma fredda' if direzione == 'sotto' else 'Gomma che cuoce'} su "
                f"{_ruote(ruote)}: per Kunos meno pressione genera più calore e più "
                f"pressione ne genera meno, e campanatura e convergenza decidono come "
                f"il calore si distribuisce. "
                f"{'Scendi di pressione su quell’angolo, poi rivedi l’allineamento' if direzione == 'sotto' else 'Sali di pressione su quell’angolo, poi rivedi l’allineamento'}."
            )
        voci.append(VoceGomme(
            titolo=(f"{_ruote(ruote)} {direzione} la finestra {etichetta} "
                    f"({finestra.min:g}-{finestra.max:g} {finestra.unita}) per il "
                    f"{peggiore:.0f}% del tempo"),
            prova=f"{dettaglio}; finestra indicativa da {finestra.fonte}",
            azione=azione,
            gravita=round(GRAVITA_PER_QUOTA_FUORI * peggiore / 100, 1),
            fonte="kunos",
            parametri=parametri,
        ))
    return voci


def _riferimento_freni() -> dict[str, Any]:
    voci = rif.community()["voci"]
    ant, post = voci["temperatura_freni_anteriori"], voci["temperatura_freni_posteriori"]
    return {
        "stato": "da_confermare",
        "etichetta": "community",
        "anteriori_max_c": ant["max_consigliato"], "anteriori_picco_c": ant["picco_max"],
        "posteriori_max_c": post["max_consigliato"], "posteriori_picco_c": post["picco_max"],
        "fonte": ant["fonti"][0]["url"],
        "limiti": ant["limiti"],
    }


def analizza_gomme_e_freni(
    canali: dict[str, np.ndarray],
    indice_giri: np.ndarray | None = None,
    giri=None,
    mescola: str | None = None,
) -> ReportGommeFreni:
    """Statistiche, finestre e squilibri di gomme e freni.

    `giri` (quelli di `curve.dividi_in_giri`) restringe il conto ai giri completi
    fuori dai box; senza, si usa tutta la registrazione e lo si dichiara.
    `mescola` ("asciutto" | "bagnato") arriva dal bundle; se manca si cerca nel canale
    `rainTyres`. Senza mescola nota, niente giudizio contro la finestra.
    """
    mancanti: list[str] = []
    voci: list[VoceGomme] = []
    punti_fermi: list[dict[str, str]] = []

    pressioni = _colonne(canali, PRESSIONE)
    temperature = _colonne(canali, TEMP_GOMMA)
    temp_freni = _colonne(canali, TEMP_FRENO)
    pastiglie = _colonne(canali, PASTIGLIE)
    dischi = _colonne(canali, DISCHI)

    n = next((s[0].size for s in (pressioni, temperature, temp_freni) if s), 0)
    maschera = maschera_giri_utili(n, giri)
    if maschera is not None and not maschera.any():
        maschera = None
        mancanti.append("nessun giro completo fuori dai box: gomme misurate su tutta la "
                        "registrazione, giri lenti compresi")
    elif maschera is None and n:
        mancanti.append("giri non ritagliati: gomme misurate su tutta la registrazione")

    def utili(serie: list[np.ndarray] | None) -> list[np.ndarray] | None:
        if serie is None:
            return None
        return [s[maschera] for s in serie] if maschera is not None else serie

    if mescola is None:
        mescola, nota = mescola_dai_canali(canali)
        if nota:
            mancanti.append(f"{nota}: niente giudizio contro la finestra ufficiale")

    gomme = None
    if pressioni is None:
        mancanti.append("pressioni gomme non registrate")
    else:
        p_utili = utili(pressioni)
        medie = [float(np.mean(p)) for p in p_utili]
        t_utili = utili(temperature)
        gomme = Gomme(
            pressione_media=PerRuota.da_valori(medie),
            pressione_minima=PerRuota.da_valori([float(np.min(p)) for p in p_utili]),
            pressione_massima=PerRuota.da_valori([float(np.max(p)) for p in p_utili]),
            temperatura_media=PerRuota.da_valori(
                [float(np.mean(t)) for t in t_utili] if t_utili else [None] * 4, 1),
            temperatura_massima=PerRuota.da_valori(
                [float(np.max(t)) for t in t_utili] if t_utili else [None] * 4, 1),
            mescola=mescola,
            squilibrio_ant_post_psi=round((medie[0] + medie[1]) / 2
                                          - (medie[2] + medie[3]) / 2, 2),
            squilibrio_sx_dx_psi=round((medie[0] + medie[2]) / 2
                                       - (medie[1] + medie[3]) / 2, 2),
            misurato_su_giri=(len([g for g in giri if g.completo and not g.ai_box])
                              if giri is not None and maschera is not None
                              else (int(np.unique(indice_giri).size)
                                    if indice_giri is not None else 0)),
        )
        if t_utili:
            temp_medie = [float(np.mean(t)) for t in t_utili]
            gomme.squilibrio_temp_ant_post_c = round(
                (temp_medie[0] + temp_medie[1]) / 2 - (temp_medie[2] + temp_medie[3]) / 2, 2)
            gomme.squilibrio_temp_sx_dx_c = round(
                (temp_medie[0] + temp_medie[2]) / 2 - (temp_medie[1] + temp_medie[3]) / 2, 2)
        else:
            mancanti.append("temperature del core gomma non registrate")
            serie_motec = [canali.get(TEMP_GOMMA_MOTEC[r]) for r in RUOTE]
            if all(s is not None and s.size for s in serie_motec):
                tm = utili([np.asarray(s, dtype=np.float64) for s in serie_motec])
                gomme.temperatura_motec_media = PerRuota.da_valori(
                    [float(np.mean(t)) for t in tm], 1)
                gomme.temperatura_motec_massima = PerRuota.da_valori(
                    [float(np.max(t)) for t in tm], 1)
                gomme.nota_temperatura_motec = (
                    "TYRE_TAIR dall'export MoTeC di ACC: non è dichiarata come temperatura "
                    "al core, quindi si mostra e non si giudica contro la finestra Kunos")

        # ── finestre ufficiali: solo gomme da asciutto ──
        if mescola == ASCIUTTO:
            p_min, p_max = rif.finestra_pressione_asciutto()
            gomme.finestra_pressione = _finestra("pressione", p_utili, p_min, p_max, "psi")
            voci.extend(_voci_finestra(gomme.finestra_pressione, p_utili))
            if t_utili:
                t_min, t_max = rif.finestra_core_asciutto()
                gomme.finestra_temperatura = _finestra(
                    "temperatura_core", t_utili, t_min, t_max, "°C")
                voci.extend(_voci_finestra(gomme.finestra_temperatura, t_utili))
            gomme.nota_finestra = (f"Finestra ufficiale indicativa da {rif.citazione_fonte()}; "
                                   f"entra nel verdetto oltre il "
                                   f"{QUOTA_FUORI_FINESTRA:.0%} del tempo fuori")
            dentro = [
                min(q for q in (f.dentro_pct.come_lista()) if q is not None)
                for f in (gomme.finestra_pressione, gomme.finestra_temperatura) if f
            ]
            if dentro and min(dentro) >= 80:
                punti_fermi.append({
                    "titolo": "Gomme nella finestra Kunos",
                    "prova": (f"tutte e quattro le ruote dentro la finestra per almeno il "
                              f"{min(dentro):.0f}% del tempo, pressione"
                              f"{' e temperatura al core' if gomme.finestra_temperatura else ''}"),
                })
        elif mescola == BAGNATO:
            gomme.nota_finestra = ("Gomme da bagnato: Kunos non pubblica una finestra, qui "
                                   "si riportano solo i valori (riferimento community da "
                                   "confermare: 29,5-31 psi)")
        else:
            gomme.nota_finestra = "Mescola non nota: niente giudizio contro la finestra"

        # ── pendenza: medie per giro, dopo il primo giro utile (le gomme si scaldano) ──
        if giri is not None:
            utili_giri = [g for g in giri if g.completo and not g.ai_box]
            if len(utili_giri) >= 4:
                numeri = np.array([g.numero for g in utili_giri[1:]], dtype=float)
                medie_giro = np.array([
                    float(np.mean([p[g.inizio:g.fine].mean() for p in pressioni]))
                    for g in utili_giri[1:]
                ])
                pendenza = _pendenza(medie_giro, numeri)
                gomme.pendenza_pressione_psi_giro = (
                    None if pendenza is None else round(pendenza, 3))
        elif indice_giri is not None and indice_giri.size == pressioni[0].size:
            media_per_campione = np.mean(np.vstack(pressioni), axis=0)
            pendenza = _pendenza(media_per_campione, indice_giri.astype(float))
            gomme.pendenza_pressione_psi_giro = None if pendenza is None else round(pendenza, 3)

        squilibrio_lato = abs(gomme.squilibrio_sx_dx_psi or 0)
        if squilibrio_lato >= SQUILIBRIO_LATI_PSI:
            lato = "sinistra" if (gomme.squilibrio_sx_dx_psi or 0) > 0 else "destra"
            voci.append(VoceGomme(
                titolo=f"Pressioni sbilanciate: {squilibrio_lato:.2f} psi in più a {lato}",
                prova=(f"media Ant.SX {gomme.pressione_media.FL} · Ant.DX {gomme.pressione_media.FR} · "
                       f"Post.SX {gomme.pressione_media.RL} · Post.DX {gomme.pressione_media.RR} psi"),
                azione=("Su un tracciato con curve nei due sensi uno squilibrio così "
                        "resta: correggi le pressioni a freddo del lato che scalda di più."),
                gravita=round(GRAVITA_PER_PSI_LATI * squilibrio_lato, 1),
            ))
        # Che le pressioni salgano mentre la gomma si scalda è normale. Diventa un
        # problema solo se la salita porta fuori finestra: con la finestra nota si
        # guarda dove arriva l'ultimo giro, altrimenti si segnala la tendenza e basta.
        # Senza questo controllo il verdetto direbbe insieme «alza la pressione» e
        # «parti più basso».
        esce_dalla_finestra = True
        if gomme.finestra_pressione is not None and giri is not None:
            ultimi = [g for g in giri if g.completo and not g.ai_box]
            if ultimi:
                ultimo = ultimi[-1]
                esce_dalla_finestra = any(
                    float(p[ultimo.inizio:ultimo.fine].mean()) > gomme.finestra_pressione.max
                    for p in pressioni)
        if (gomme.pendenza_pressione_psi_giro or 0) >= CRESCITA_PRESSIONE_PSI_GIRO \
                and esce_dalla_finestra:
            voci.append(VoceGomme(
                titolo="Le pressioni salgono giro dopo giro",
                prova=(f"+{gomme.pendenza_pressione_psi_giro:.3f} psi per giro sullo stint, "
                       f"primo giro utile escluso"),
                azione=("Parti più basso a freddo: con questa pendenza a fine stint "
                        "esci dalla finestra anche partendo giusto."),
                gravita=round(GRAVITA_PER_PSI_GIRO * (gomme.pendenza_pressione_psi_giro or 0), 1),
            ))

    freni = None
    if temp_freni is None:
        mancanti.append("temperature freni non registrate")
    else:
        f_utili = utili(temp_freni)
        medie_freni = [float(np.mean(t)) for t in f_utili]
        freni = Freni(
            temperatura_media=PerRuota.da_valori(medie_freni, 0),
            temperatura_massima=PerRuota.da_valori([float(np.max(t)) for t in f_utili], 0),
            squilibrio_ant_post_c=round((medie_freni[0] + medie_freni[1]) / 2
                                        - (medie_freni[2] + medie_freni[3]) / 2, 1),
            riferimento_community=_riferimento_freni(),
        )
        if pastiglie:
            freni.pastiglie_consumate_mm = PerRuota.da_valori(
                [float(p[0] - p[-1]) for p in pastiglie], 3)
        if dischi:
            freni.dischi_consumati_mm = PerRuota.da_valori(
                [float(d[0] - d[-1]) for d in dischi], 3)

    # ── medie giro per giro, per le schermate ──
    per_giro: list[GiroGomme] = []
    if giri is not None and (pressioni or temperature or temp_freni):
        for giro in giri:
            if not giro.completo:
                continue
            pezzo = slice(giro.inizio, giro.fine)
            per_giro.append(GiroGomme(
                giro=giro.numero,
                pressione=PerRuota.da_valori(
                    [float(p[pezzo].mean()) for p in pressioni] if pressioni else [None] * 4),
                temperatura=PerRuota.da_valori(
                    [float(t[pezzo].mean()) for t in temperature] if temperature else [None] * 4, 1),
                freni_max=PerRuota.da_valori(
                    [float(t[pezzo].max()) for t in temp_freni] if temp_freni else [None] * 4, 0),
            ))

    return ReportGommeFreni(gomme=gomme, freni=freni, per_giro=per_giro, voci=voci,
                            punti_fermi=punti_fermi, dati_mancanti=mancanti)


def indice_giri(canali: dict[str, np.ndarray], giri) -> np.ndarray | None:
    """Per ogni campione, il numero del giro: serve alle tendenze sullo stint."""
    posizione = canali.get("graphics.normalizedCarPosition")
    if posizione is None:
        return None
    indice = np.zeros(posizione.size, dtype=np.int32)
    for giro in giri:
        indice[giro.inizio:giro.fine] = giro.numero
    return indice
