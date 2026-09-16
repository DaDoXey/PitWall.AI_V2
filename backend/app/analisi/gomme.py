"""Gomme e freni dai canali registrati (L3 · Fase 4).

Era la promessa del rework: «il registratore sblocca gomme, pressioni, freni e il
consumo vero». Questo modulo è la parte gomme e freni.

**Una scelta di onestà che limita di proposito quello che si dice.** La finestra di
pressione «giusta» di una GT3 (i famosi 27,5-28,0 psi) non è pubblicata da nessuna
parte in ACC: è un numero che gira fra i piloti. Giudicare una sessione contro una
costante non verificata vorrebbe dire scrivere «pressioni basse» con la stessa
sicurezza con cui si scrive un tempo sul giro — e le due cose non valgono uguale.

Qui quindi si misura, e si giudica **solo ciò che si dimostra da sé**:

* gli **squilibri** — fra anteriore e posteriore, fra sinistra e destra: una
  differenza è una differenza, non serve nessuna tabella per dirlo;
* le **tendenze** — la pressione che sale sullo stint, la temperatura che cresce:
  una pendenza è misurabile senza sapere quale sia il valore ideale;
* la **dispersione** — quanto ballano i valori.

I valori assoluti vengono riportati sempre, così il pilota li legge e decide lui.
Quando la tabella delle finestre sarà verificata in gioco (decisione 7 del rework),
i giudizi assoluti si aggiungono qui, marcati come verificati.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

import numpy as np

RUOTE = ("FL", "FR", "RL", "RR")

PRESSIONE = "physics.wheelPressure"
TEMP_GOMMA = "physics.tyreCoreTemp"
TEMP_FRENO = "physics.brakeTemp"
PASTIGLIE = "physics.padLife"
DISCHI = "physics.discLife"


@dataclass
class PerRuota:
    FL: float | None = None
    FR: float | None = None
    RL: float | None = None
    RR: float | None = None

    @classmethod
    def da_valori(cls, valori: list[float | None]) -> "PerRuota":
        return cls(*[None if v is None else round(float(v), 2) for v in valori])

    def come_lista(self) -> list[float | None]:
        return [self.FL, self.FR, self.RL, self.RR]


@dataclass
class Gomme:
    pressione_media: PerRuota
    pressione_minima: PerRuota
    pressione_massima: PerRuota
    temperatura_media: PerRuota
    squilibrio_ant_post_psi: float | None = None
    squilibrio_sx_dx_psi: float | None = None
    squilibrio_temp_ant_post_c: float | None = None
    squilibrio_temp_sx_dx_c: float | None = None
    pendenza_pressione_psi_giro: float | None = None
    misurato_su_giri: int = 0
    nota_finestra: str = (
        "la finestra di pressione «ottimale» non è pubblicata da ACC: qui si "
        "riportano i valori e gli squilibri, non un giudizio su un numero non verificato"
    )


@dataclass
class Freni:
    temperatura_media: PerRuota
    temperatura_massima: PerRuota
    squilibrio_ant_post_c: float | None = None
    pastiglie_consumate_mm: PerRuota | None = None
    dischi_consumati_mm: PerRuota | None = None


@dataclass
class VoceGomme:
    titolo: str
    prova: str
    azione: str
    gravita: float


@dataclass
class ReportGommeFreni:
    gomme: Gomme | None
    freni: Freni | None
    voci: list[VoceGomme] = field(default_factory=list)
    dati_mancanti: list[str] = field(default_factory=list)

    def come_json(self) -> dict[str, Any]:
        return {
            "gomme": asdict(self.gomme) if self.gomme else None,
            "freni": asdict(self.freni) if self.freni else None,
            "voci": [asdict(v) for v in self.voci],
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


def analizza_gomme_e_freni(
    canali: dict[str, np.ndarray], indice_giri: np.ndarray | None = None
) -> ReportGommeFreni:
    """Statistiche e squilibri di gomme e freni su tutta la registrazione."""
    mancanti: list[str] = []
    voci: list[VoceGomme] = []

    pressioni = _colonne(canali, PRESSIONE)
    temperature = _colonne(canali, TEMP_GOMMA)
    temp_freni = _colonne(canali, TEMP_FRENO)
    pastiglie = _colonne(canali, PASTIGLIE)
    dischi = _colonne(canali, DISCHI)

    gomme = None
    if pressioni is None:
        mancanti.append("pressioni gomme non registrate")
    else:
        medie = [float(np.mean(p)) for p in pressioni]
        gomme = Gomme(
            pressione_media=PerRuota.da_valori(medie),
            pressione_minima=PerRuota.da_valori([float(np.min(p)) for p in pressioni]),
            pressione_massima=PerRuota.da_valori([float(np.max(p)) for p in pressioni]),
            temperatura_media=PerRuota.da_valori(
                [float(np.mean(t)) for t in temperature] if temperature
                else [None, None, None, None]
            ),
            squilibrio_ant_post_psi=round((medie[0] + medie[1]) / 2
                                          - (medie[2] + medie[3]) / 2, 2),
            squilibrio_sx_dx_psi=round((medie[0] + medie[2]) / 2
                                       - (medie[1] + medie[3]) / 2, 2),
            misurato_su_giri=int(np.unique(indice_giri).size) if indice_giri is not None else 0,
        )
        if temperature:
            temp_medie = [float(np.mean(t)) for t in temperature]
            gomme.squilibrio_temp_ant_post_c = round(
                (temp_medie[0] + temp_medie[1]) / 2 - (temp_medie[2] + temp_medie[3]) / 2, 2)
            gomme.squilibrio_temp_sx_dx_c = round(
                (temp_medie[0] + temp_medie[2]) / 2 - (temp_medie[1] + temp_medie[3]) / 2, 2)
        else:
            mancanti.append("temperature del core gomma non registrate")

        if indice_giri is not None and indice_giri.size == pressioni[0].size:
            media_per_campione = np.mean(np.vstack(pressioni), axis=0)
            gomme.pendenza_pressione_psi_giro = (
                None if (p := _pendenza(media_per_campione, indice_giri.astype(float))) is None
                else round(p, 3)
            )

        # ── giudizi che si reggono da soli ──
        squilibrio_lato = abs(gomme.squilibrio_sx_dx_psi or 0)
        if squilibrio_lato >= 0.3:
            lato = "sinistra" if (gomme.squilibrio_sx_dx_psi or 0) > 0 else "destra"
            voci.append(VoceGomme(
                titolo=f"Pressioni sbilanciate: {squilibrio_lato:.2f} psi in più a {lato}",
                prova=(f"media FL {gomme.pressione_media.FL} · FR {gomme.pressione_media.FR} · "
                       f"RL {gomme.pressione_media.RL} · RR {gomme.pressione_media.RR} psi"),
                azione=("Su un tracciato con curve nei due sensi uno squilibrio così "
                        "resta: correggi le pressioni a freddo del lato che scalda di più."),
                gravita=200.0 * squilibrio_lato,
            ))
        squilibrio_asse = abs(gomme.squilibrio_ant_post_psi or 0)
        if squilibrio_asse >= 0.5:
            asse = "anteriore" if (gomme.squilibrio_ant_post_psi or 0) > 0 else "posteriore"
            voci.append(VoceGomme(
                titolo=f"Asse {asse} più gonfio di {squilibrio_asse:.2f} psi",
                prova=(f"anteriore {(gomme.pressione_media.FL + gomme.pressione_media.FR)/2:.2f} psi · "
                       f"posteriore {(gomme.pressione_media.RL + gomme.pressione_media.RR)/2:.2f} psi"),
                azione=("Riporta i due assi nella stessa finestra prima di toccare "
                        "barre e ammortizzatori: il bilanciamento che senti può venire da qui."),
                gravita=150.0 * squilibrio_asse,
            ))
        if (gomme.pendenza_pressione_psi_giro or 0) >= 0.08:
            voci.append(VoceGomme(
                titolo="Le pressioni salgono giro dopo giro",
                prova=f"+{gomme.pendenza_pressione_psi_giro:.3f} psi per giro sullo stint",
                azione=("Abbassa le pressioni a freddo: con questa pendenza a fine stint "
                        "sei fuori finestra anche partendo giusto."),
                gravita=400.0 * (gomme.pendenza_pressione_psi_giro or 0),
            ))

    freni = None
    if temp_freni is None:
        mancanti.append("temperature freni non registrate")
    else:
        medie_freni = [float(np.mean(t)) for t in temp_freni]
        freni = Freni(
            temperatura_media=PerRuota.da_valori(medie_freni),
            temperatura_massima=PerRuota.da_valori(
                [float(np.max(t)) for t in temp_freni]),
            squilibrio_ant_post_c=round((medie_freni[0] + medie_freni[1]) / 2
                                        - (medie_freni[2] + medie_freni[3]) / 2, 2),
        )
        if pastiglie:
            freni.pastiglie_consumate_mm = PerRuota.da_valori(
                [float(p[0] - p[-1]) for p in pastiglie])
        if dischi:
            freni.dischi_consumati_mm = PerRuota.da_valori(
                [float(d[0] - d[-1]) for d in dischi])

    return ReportGommeFreni(gomme=gomme, freni=freni, voci=voci, dati_mancanti=mancanti)


def indice_giri(canali: dict[str, np.ndarray], giri) -> np.ndarray | None:
    """Per ogni campione, il numero del giro: serve alle tendenze sullo stint."""
    posizione = canali.get("graphics.normalizedCarPosition")
    if posizione is None:
        return None
    indice = np.zeros(posizione.size, dtype=np.int32)
    for giro in giri:
        indice[giro.inizio:giro.fine] = giro.numero
    return indice
