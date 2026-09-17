"""analisi/gigi.py — ciò che Gigi riceve, e ciò che dice quando il modello è spento (L4).

Due funzioni, entrambe deterministiche:

* `contesto()` — il messaggio per il modello linguistico. Decisione del rework: Gigi
  riceve **solo il report del motore** (più setup, racconto e domanda), mai i canali
  grezzi. Poche centinaia di token: costa poco e non lascia spazio a numeri inventati,
  perché gli unici numeri che vede sono quelli già dimostrati.
* `risposta_dal_motore()` — la risposta a 5 sezioni composta **senza modello**, a
  partire dallo stesso report. Serve quando il live è spento (demo-mode, chiave
  assente, tetto di spesa) e la sessione non è la demo: prima si rispondeva con la
  storia di Monza qualunque sessione fosse aperta, e sarebbe stato un falso.

Stesso formato del modello (`## Diagnosi` … `## Note Aggiuntive`), così la Console
non distingue le due fonti se non per l'etichetta.
"""

from __future__ import annotations

from app.analisi.motore import ReportAnalisi
from app.bundle.schema import SessionBundle

MAX_VOCI_CONTESTO = 8
MAX_NOTE_CONTESTO = 6


def _mmss(ms: int | None) -> str:
    if ms is None:
        return "—"
    minuti, resto = divmod(int(ms), 60_000)
    return f"{minuti}:{resto // 1000:02d}.{resto % 1000:03d}"


def _intestazione(report: ReportAnalisi, bundle: SessionBundle) -> str:
    meta = bundle.meta
    pezzi = [
        f"vettura {report.car or 'non indicata'}",
        f"pista {report.track or 'non indicata'}",
        f"sessione {report.tipo_sessione}",
        f"fonte {report.fonte}",
    ]
    if meta.piattaforma:
        pezzi.append(f"piattaforma {meta.piattaforma.value}")
    if report.mescola:
        pezzi.append(f"gomme da {report.mescola}")
    c = meta.condizioni
    if c.temp_aria_c is not None or c.temp_pista_c is not None:
        pezzi.append(f"aria {c.temp_aria_c if c.temp_aria_c is not None else '—'} °C, "
                     f"pista {c.temp_pista_c if c.temp_pista_c is not None else '—'} °C")
    return " · ".join(pezzi)


def _blocco_report(report: ReportAnalisi, bundle: SessionBundle) -> list[str]:
    r = report.ritmo
    righe = [
        "[REPORT DEL MOTORE]",
        _intestazione(report, bundle),
        (f"giri {report.giri_totali} (validi {r.giri_validi}, buttati {report.giri_buttati}, "
         f"di ritmo {report.giri_di_ritmo})"),
    ]
    if r.miglior_giro_ms:
        teorico = (f"teorico {_mmss(r.giro_teorico_ms)} (lasciato sul tavolo "
                   f"{r.lasciato_sul_tavolo_ms} ms)" if r.giro_teorico_ms
                   else f"teorico non calcolabile: {r.motivo_teorico}")
        righe.append(f"miglior giro {_mmss(r.miglior_giro_ms)} (giro {r.miglior_giro_numero}), "
                     f"{teorico}, media {_mmss(r.media_ms)}")
    if report.costanza.deviazione_ms is not None:
        righe.append(f"costanza: deviazione {report.costanza.deviazione_ms} ms, "
                     f"{report.costanza.percentuale_entro_mezzo_secondo}% entro 0,5 s")
    if report.degrado.calcolabile:
        righe.append(f"degrado dal giro {report.degrado.dal_giro}: "
                     f"{report.degrado.pendenza_ms_giro} ms/giro (R² {report.degrado.r_quadro})")
    if report.carburante.calcolabile:
        righe.append(f"consumo {report.carburante.consumo_medio_l_giro} l/giro "
                     f"su {report.carburante.giri_misurati} giri")
    if report.settori:
        righe.append("settori (migliore / perdita media a giro): " + " · ".join(
            f"S{s.numero} {s.migliore_ms / 1000:.3f} s / {s.perdita_media_ms} ms"
            for s in report.settori))

    gomme = (report.gomme_e_freni or {}).get("gomme")
    if gomme:
        media = gomme["pressione_media"]
        temp = gomme["temperatura_media"]
        righe.append(
            "gomme (media nei giri utili) pressione psi FL/FR/RL/RR "
            f"{media['FL']}/{media['FR']}/{media['RL']}/{media['RR']} · core °C "
            f"{temp['FL']}/{temp['FR']}/{temp['RL']}/{temp['RR']}")
        for chiave, nome in (("finestra_pressione", "pressione"),
                             ("finestra_temperatura", "temperatura core")):
            f = gomme.get(chiave)
            if f:
                righe.append(
                    f"finestra Kunos {nome} {f['min']}-{f['max']} {f['unita']}: % fuori "
                    f"(sotto/sopra) FL {f['sotto_pct']['FL']}/{f['sopra_pct']['FL']} · "
                    f"FR {f['sotto_pct']['FR']}/{f['sopra_pct']['FR']} · "
                    f"RL {f['sotto_pct']['RL']}/{f['sopra_pct']['RL']} · "
                    f"RR {f['sotto_pct']['RR']}/{f['sopra_pct']['RR']}")
    freni = (report.gomme_e_freni or {}).get("freni")
    if freni:
        massima = freni["temperatura_massima"]
        righe.append(f"freni temperatura massima °C FL/FR/RL/RR {massima['FL']}/{massima['FR']}/"
                     f"{massima['RL']}/{massima['RR']} (riferimento community, da confermare)")

    righe.append("VERDETTO (ordinato per gravità):")
    if report.verdetto:
        for i, v in enumerate(report.verdetto[:MAX_VOCI_CONTESTO], start=1):
            righe.append(f"{i}. {v.titolo} — prova: {v.prova} — azione: {v.azione}")
    else:
        righe.append("nessuna perdita dimostrabile con questi dati")
    if report.cosa_regge:
        righe.append("COSA REGGE: " + " · ".join(f"{p.titolo} ({p.prova})"
                                                 for p in report.cosa_regge))
    if report.dati_mancanti:
        righe.append("DATI MANCANTI / ASSUNZIONI: " + " | ".join(
            report.dati_mancanti[:MAX_NOTE_CONTESTO]))
    return righe


def _blocco_setup(bundle: SessionBundle) -> list[str]:
    if not bundle.setup or not bundle.setup.valori:
        return ["[SETUP]", "nessun setup collegato a questa sessione"]
    valori = []
    for nome, valore in sorted(bundle.setup.valori.items()):
        if valore.verificato and valore.reale is not None:
            valori.append(f"{nome}={valore.reale} {valore.unita}")
        else:
            valori.append(f"{nome}={valore.raw}")
    reali, totale = bundle.setup.quanti_verificati()
    return ["[SETUP]", f"{totale} parametri, {reali} in unità reali, gli altri in click",
            ", ".join(valori)]


def _blocco_racconto(bundle: SessionBundle) -> list[str]:
    r = bundle.racconto
    if not r or r.vuoto():
        return []
    righe = ["[RACCONTO]"]
    for etichetta, testo in (("andamento", r.andamento), ("frenata", r.frenata),
                             ("ingresso", r.ingresso), ("centro curva", r.centro),
                             ("uscita", r.uscita), ("gomme", r.gomme), ("note", r.note)):
        if testo:
            righe.append(f"{etichetta}: {testo}")
    if r.curve_critiche:
        righe.append("curve critiche: " + ", ".join(r.curve_critiche))
    return righe


def contesto(report: ReportAnalisi, bundle: SessionBundle, domanda: str,
             profilo: str | None = None) -> str:
    """Il messaggio per il modello: report, setup, racconto, profilo e domanda."""
    righe = _blocco_report(report, bundle) + [""] + _blocco_setup(bundle)
    racconto = _blocco_racconto(bundle)
    if racconto:
        righe += [""] + racconto
    if profilo and profilo.strip():
        righe += ["", "[PROFILO PILOTA]", profilo.strip()]
    righe += ["", "[DOMANDA]", domanda.strip() or "Analizza la sessione."]
    return "\n".join(righe)


# ─────────────────────────────────────────────
# Risposta senza modello
# ─────────────────────────────────────────────


def _elenco(righe: list[str]) -> str:
    return "\n".join(f"- {r}" for r in righe)


def risposta_dal_motore(report: ReportAnalisi, bundle: SessionBundle, domanda: str = "") -> str:
    """Le 5 sezioni di Gigi composte dal report, senza modello linguistico."""
    tempo = [v for v in report.verdetto if v.categoria == "tempo"]
    gomme = [v for v in report.verdetto if v.categoria == "gomme"]
    racconto = bundle.racconto if bundle.racconto and not bundle.racconto.vuoto() else None

    # ── Diagnosi ──
    diagnosi: list[str] = []
    if report.verdetto:
        primo = report.verdetto[0]
        prova = primo.prova[:1].upper() + primo.prova[1:]
        diagnosi.append(f"Il problema numero uno: **{primo.titolo}**. {prova}.")
        altri = [v.titolo for v in report.verdetto[1:4]]
        if altri:
            diagnosi.append("Poi, in ordine di gravità: " + "; ".join(altri) + ".")
    elif report.giri_totali:
        diagnosi.append("Con questi dati il motore non trova perdite dimostrabili.")
    else:
        diagnosi.append("In questa sessione non ci sono giri misurati: il motore non ha tempi "
                        "da analizzare.")
    if racconto and racconto.andamento:
        diagnosi.append(f"Il tuo racconto: «{racconto.andamento}».")

    # ── Causa meccanica ──
    causa: list[str] = []
    if gomme:
        causa.append("Dai numeri, la causa sta nelle gomme: " + "; ".join(
            v.titolo for v in gomme[:3]) + ".")
    elif report.ha_canali:
        causa.append("Gomme e freni sono nelle finestre misurabili: le perdite dimostrate "
                     "stanno nella guida (curve e settori), non nella macchina.")
    else:
        causa.append("Senza la telemetria il motore non vede gomme, pressioni e freni: una "
                     "causa meccanica non si può dimostrare con i numeri.")
        if racconto:
            causa.append("Il racconto indica dove guardare, ma resta una sensazione da "
                         "verificare in pista.")

    # ── Correzione setup ──
    setup: list[str] = [v.azione for v in gomme[:2]]
    if not setup:
        setup.append("Nessuna correzione di setup dimostrata dai numeri di questa sessione.")
    if not report.ha_setup:
        setup.append("Il setup non è collegato alla sessione: per dare i click giusti serve "
                     "il file del setup (o i valori scritti a mano).")

    # ── Correzione di guida ──
    guida: list[str] = [f"**{v.titolo}** — {v.azione}" for v in tempo[:3]]
    if not guida:
        guida.append("Nessuna perdita di guida dimostrata." if report.ha_canali else
                     "Senza telemetria niente dati per curva: le correzioni di guida si "
                     "possono dare solo sul racconto.")

    # ── Note ──
    note: list[str] = []
    for p in report.cosa_regge[:3]:
        note.append(f"Regge: {p.titolo} ({p.prova}).")
    for d in report.dati_mancanti[:3]:
        note.append(f"Dato mancante o assunzione: {d}.")
    if domanda.strip():
        note.append(f"Alla domanda «{domanda.strip()[:160]}» rispondono i numeri qui sopra: "
                    "per un commento su misura serve Gigi dal vivo.")
    note.append("Risposta composta dal motore di analisi, senza modello linguistico.")

    return (
        "## Diagnosi\n" + "\n".join(diagnosi) + "\n\n"
        "## Causa Meccanica Probabile\n" + "\n".join(causa) + "\n\n"
        "## Correzione Setup Consigliata\n" + _elenco(setup) + "\n\n"
        "## Correzione di Guida\n" + _elenco(guida) + "\n\n"
        "## Note Aggiuntive\n" + _elenco(note) + "\n"
    )
