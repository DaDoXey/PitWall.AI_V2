"""
test_analisi_l4.py — l'analisi rivista per L4 (fase 1)

Le decisioni del 16/09/2026, inchiodate una per una:
* i **settori** di una registrazione sono tre, e sommano al giro: il giro teorico
  esiste anche per le sessioni registrate;
* le gomme si giudicano contro la **finestra Kunos** (26-27 psi, 70-100 °C al core),
  per quota di tempo fuori, **solo sull'asciutto**;
* una differenza di pressione **fra gli assi** non è un errore (Kunos: è uno
  strumento di setup), fra i lati sì;
* i valori **community** si mostrano ma non giudicano mai;
* il **verdetto** contiene solo perdite, ciò che regge va in `cosa_regge`;
* il giro teorico, quando manca, dice **perché**;
* una voce della curva 12 non prende i numeri della curva 1;
* il racconto del pilota (console) è un dato: una sessione con solo quello si analizza.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_analisi_l4.py
"""

import json
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from app.analisi import analizza  # noqa: E402
from app.analisi.curve import analizza_curve  # noqa: E402
from app.bundle.adapters.acc_telemetria import bundle_da_canali  # noqa: E402
from app.bundle.schema import (  # noqa: E402
    Fonte,
    Giro,
    Mescola,
    Meta,
    Racconto,
    SessionBundle,
)
from app.core import riferimenti_fisica as rif  # noqa: E402
from app.tests.pista_finta import (  # noqa: E402
    CurvaFinta,
    GiroFinto,
    PistaFinta,
    genera,
    pista_tre_curve,
)

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []


def test(name: str, passed: bool, detail: str = ""):
    status = PASS if passed else FAIL
    line = f"{status}  {name}"
    if detail and not passed:
        line += f"\n        → {detail}"
    print(line)
    results.append((name, passed))


METADATI = {
    "id": "20260916-100000-pista_finta-bbbb", "vettura": "bmw_m4_gt3",
    "pista": "pista_finta", "tipo_sessione": "PRACTICE", "frequenza_hz": 100.0,
}
pista = pista_tre_curve()
buone = pista.curve


def sessione(**opzioni):
    giri = opzioni.pop("giri", [GiroFinto(curve=buone) for _ in range(5)])
    canali = genera(pista, giri, completo=True, **opzioni)
    bundle = bundle_da_canali(canali, METADATI)
    return bundle, canali, analizza(bundle, canali)


def titoli(report):
    return [v.titolo for v in report.verdetto]


# ---------------------------------------------------------------------------
# 1 · I settori delle registrazioni
# ---------------------------------------------------------------------------
print("\n─── Settori e giro teorico ───")

bundle, canali, report = sessione()
completi = [g for g in bundle.giri if g.tempo_ms]
test("L01 ogni giro completo ha tre settori",
     all(len(g.splits_ms) == 3 for g in completi),
     f"{[g.splits_ms for g in completi]}")
test("L02 …e i tre settori sommano al tempo del giro (entro 100 ms)",
     all(abs(sum(g.splits_ms) - g.tempo_ms) <= 100 for g in completi),
     f"{[(sum(g.splits_ms), g.tempo_ms) for g in completi]}")
test("L03 il giro teorico esiste anche per una sessione registrata",
     report.ritmo.giro_teorico_ms is not None and report.ritmo.motivo_teorico is None,
     f"{report.ritmo}")
test("L04 l'ultimo giro, senza traguardo dopo, ha il terzo settore ricavato e dichiarato",
     any("terzo settore" in a for a in bundle.assunzioni), f"{bundle.assunzioni}")

senza_split_sul_migliore = SessionBundle(
    meta=Meta(fonte=Fonte.MANUALE),
    giri=[Giro(numero=1, tempo_ms=99000),
          Giro(numero=2, tempo_ms=100500, splits_ms=[33000, 33500, 34000]),
          Giro(numero=3, tempo_ms=100700, splits_ms=[33100, 33400, 34200])],
)
r = analizza(senza_split_sul_migliore)
test("L05 se il giro migliore non ha split, il teorico tace…",
     r.ritmo.giro_teorico_ms is None)
test("L06 …e dice perché", r.ritmo.motivo_teorico is not None
     and "split" in r.ritmo.motivo_teorico, f"{r.ritmo.motivo_teorico}")
test("L07 …anche nei dati mancanti",
     any("giro teorico" in d for d in r.dati_mancanti), f"{r.dati_mancanti}")

# ---------------------------------------------------------------------------
# 2 · Finestra Kunos
# ---------------------------------------------------------------------------
print("\n─── Finestra ufficiale di pressione e temperatura ───")

test("L08 le soglie arrivano dal documento Kunos: 26-27 psi",
     rif.finestra_pressione_asciutto() == (26.0, 27.0))
test("L09 …e 70-100 °C al core", rif.finestra_core_asciutto() == (70.0, 100.0))
test("L10 ogni voce ufficiale porta la sua citazione",
     all(v.get("citazione") for v in rif.ufficiali()["voci"].values()))
test("L11 la mescola da asciutto finisce nel bundle", bundle.meta.mescola is Mescola.ASCIUTTO)

_, _, basse = sessione(pressioni={"RL": 25.4, "RR": 25.4})
voce_basse = next((v for v in basse.verdetto if "sotto la finestra di pressione" in v.titolo), None)
test("L12 posteriori a 25,4 psi: la voce «sotto la finestra» c'è",
     voce_basse is not None, f"{titoli(basse)}")
test("L13 …nomina le due ruote posteriori e nessuna anteriore",
     voce_basse is not None and "Post.SX" in voce_basse.titolo and "Post.DX" in voce_basse.titolo
     and "Ant." not in voce_basse.titolo, voce_basse.titolo if voce_basse else "—")
test("L14 …dichiara che poggia su una soglia Kunos",
     voce_basse is not None and voce_basse.fonte == "kunos" and voce_basse.categoria == "gomme"
     and "Kunos" in voce_basse.prova)
test("L15 …e porta l'azione con il numero",
     voce_basse is not None and "Alza la pressione" in voce_basse.azione
     and "0.6 psi" in voce_basse.azione, voce_basse.azione if voce_basse else "—")
test("L15b …e i parametri del setup da toccare, con la variazione in psi",
     voce_basse is not None
     and voce_basse.parametri == {"tire_press_rl": 0.6, "tire_press_rr": 0.6},
     f"{voce_basse.parametri if voce_basse else '—'}")
finestra = basse.gomme_e_freni["gomme"]["finestra_pressione"]
test("L16b le ruote oltre la soglia sono dichiarate dal motore",
     finestra["ruote_fuori"] == ["RL", "RR"], f"{finestra['ruote_fuori']}")
test("L16 la quota fuori finestra è misurata ruota per ruota (100% sotto dietro)",
     finestra["sotto_pct"]["RL"] == 100.0 and finestra["dentro_pct"]["FL"] == 100.0,
     f"{finestra}")

_, _, cotte = sessione(temperature_core={"RR": 105.0})
test("L17 Post.DX a 105 °C al core: sopra la finestra di temperatura",
     any("Post.DX sopra la finestra di temperatura" in t for t in titoli(cotte)),
     f"{titoli(cotte)}")

_, _, bagnato = sessione(pressioni={"RL": 25.4, "RR": 25.4}, gomme_da_bagnato=True)
test("L18 con gomme da bagnato la finestra da asciutto non giudica",
     not any("finestra" in t for t in titoli(bagnato)), f"{titoli(bagnato)}")
test("L19 …e la nota lo dice",
     "bagnato" in bagnato.gomme_e_freni["gomme"]["nota_finestra"])

# ---------------------------------------------------------------------------
# 3 · Assi, lati, community
# ---------------------------------------------------------------------------
print("\n─── Assi, lati e valori community ───")

_, _, assi = sessione(pressioni={"FL": 26.9, "FR": 26.9, "RL": 26.1, "RR": 26.1})
gomme_assi = assi.gomme_e_freni["gomme"]
test("L20 0,8 psi fra gli assi è misurato",
     abs(gomme_assi["squilibrio_ant_post_psi"] - 0.8) < 0.02,
     f"{gomme_assi['squilibrio_ant_post_psi']}")
test("L21 …ma non entra nel verdetto (Kunos: è uno strumento)",
     not any("sse" in t for t in titoli(assi)), f"{titoli(assi)}")
test("L22 …e la nota cita Kunos", "Kunos" in gomme_assi["nota_assi"])

_, _, lati = sessione(squilibrio_pressione_psi=0.4)
test("L23 uno squilibrio fra i lati resta nel verdetto",
     any("sbilanciat" in t.lower() for t in titoli(lati)), f"{titoli(lati)}")

_, _, freni_caldi = sessione(freni_c=(820.0, 600.0))
test("L24 freni oltre i valori community: nessuna voce nel verdetto",
     not any("fren" in t.lower() and "curva" not in t.lower() for t in titoli(freni_caldi)),
     f"{titoli(freni_caldi)}")
riferimento = freni_caldi.gomme_e_freni["freni"]["riferimento_community"]
test("L25 …ma il riferimento community viaggia, etichettato e da confermare",
     riferimento["etichetta"] == "community" and riferimento["stato"] == "da_confermare"
     and riferimento["anteriori_max_c"] == 650.0, f"{riferimento}")
test("L26 ogni voce community è da confermare",
     all(v["stato"] == "da_confermare" for v in rif.community()["voci"].values()))

# ---------------------------------------------------------------------------
# 4 · Verdetto e cosa regge
# ---------------------------------------------------------------------------
print("\n─── Verdetto solo di perdite ───")

pulita = report
test("L27 cinque giri identici: la costanza va in «cosa regge»",
     any(p.titolo.startswith("Costanza") for p in pulita.cosa_regge),
     f"{[p.titolo for p in pulita.cosa_regge]}")
test("L28 …e non nel verdetto", not any("Costanza" in t for t in titoli(pulita)),
     f"{titoli(pulita)}")
test("L29 gomme in finestra: è un punto fermo, con la prova",
     any("finestra Kunos" in p.titolo and p.prova for p in pulita.cosa_regge),
     f"{[p.titolo for p in pulita.cosa_regge]}")
test("L30 nessun giro buttato: punto fermo",
     any(p.titolo == "Nessun giro buttato" for p in pulita.cosa_regge))
test("L31 nessun titolo compare sia nel verdetto sia fra i punti fermi",
     not ({v.titolo for v in pulita.verdetto} & {p.titolo for p in pulita.cosa_regge}))
test("L32 la tabella dei giri del report ha un solo giro migliore",
     sum(1 for g in pulita.giri if g.migliore) == 1, f"{pulita.giri}")
test("L33 …e i delta sono misurati sul migliore",
     all(g.delta_migliore_ms is not None and g.delta_migliore_ms >= 0
         for g in pulita.giri if g.tempo_ms))
test("L34 le medie gomme giro per giro ci sono, una per giro completo",
     len(pulita.gomme_e_freni["per_giro"]) == len(completi),
     f"{len(pulita.gomme_e_freni['per_giro'])} contro {len(completi)}")

ballerina = SessionBundle(
    meta=Meta(fonte=Fonte.MANUALE),
    giri=[Giro(numero=i + 1, tempo_ms=t) for i, t in
          enumerate([100000, 101500, 100200, 102100, 100900, 101800])],
)
rb = analizza(ballerina)
test("L35 una costanza che costa resta nel verdetto",
     any("Costanza" in v.titolo for v in rb.verdetto), f"{[v.titolo for v in rb.verdetto]}")

# Stint che migliora (visto sui risultati veri del 14/09): il punto fermo deve dirlo,
# non «il ritmo tiene», e la costanza deve spiegare da dove viene parte della dispersione.
migliorante = SessionBundle(
    meta=Meta(fonte=Fonte.MANUALE),
    giri=[Giro(numero=i + 1, tempo_ms=t) for i, t in
          enumerate([103000, 101600, 102500, 100900, 101800, 100400, 101100, 100000])],
)
rm = analizza(migliorante)
test("L35b un ritmo che migliora è un punto fermo con il suo nome",
     any(p.titolo == "Il ritmo migliora giro dopo giro" for p in rm.cosa_regge)
     and not any(p.titolo == "Il ritmo tiene sullo stint" for p in rm.cosa_regge),
     f"{[p.titolo for p in rm.cosa_regge]} · {rm.degrado}")
test("L35c …e la voce sulla costanza dice che parte della dispersione è il miglioramento",
     any("ritmo che migliora" in v.prova for v in rm.verdetto if "Costanza" in v.titolo),
     f"{[(v.titolo, v.prova) for v in rm.verdetto]}")

# ---------------------------------------------------------------------------
# 5 · Curva 1 contro curva 12
# ---------------------------------------------------------------------------
print("\n─── Voci per curva ───")

dodici = PistaFinta(
    lunghezza_m=12000.0, velocita_massima_kmh=220.0,
    curve=[CurvaFinta(posizione_m=500.0 + 1000.0 * i, velocita_minima_kmh=100.0)
           for i in range(12)],
)
storte = list(dodici.curve)
storte[11] = CurvaFinta(posizione_m=11500.0, velocita_minima_kmh=70.0, frenata_m=170.0)
canali_12 = genera(dodici, [GiroFinto(curve=dodici.curve), GiroFinto(curve=storte),
                            GiroFinto(curve=dodici.curve)], completo=True)
report_12 = analizza(bundle_da_canali(canali_12, METADATI), canali_12)
curve_12 = analizza_curve(canali_12)
test("L36 il tracciato da dodici curve ne riconosce dodici",
     len(curve_12.curve) == 12, f"{len(curve_12.curve)}")
voce_12 = next((v for v in report_12.verdetto if "curva 12" in v.titolo
                and v.titolo.startswith("Perdi")), None)
perdita_12 = next(r.perdita_media_ms for r in curve_12.riepilogo if r.curva == 12)
test("L37 la voce della curva 12 porta la perdita della curva 12",
     voce_12 is not None and voce_12.decimi == round(perdita_12 / 100, 1)
     and voce_12.gravita == perdita_12,
     f"{voce_12} contro {perdita_12}")

# ---------------------------------------------------------------------------
# 6 · Formato: compatibilità e racconto
# ---------------------------------------------------------------------------
print("\n─── Formato del bundle ───")

vecchio = json.loads(bundle.to_json())
vecchio["schema_version"] = "1.0"
for campo in ("mescola", "piattaforma"):
    vecchio["meta"].pop(campo, None)
vecchio.pop("racconto", None)
test("L38 un bundle 1.0 si legge ancora",
     SessionBundle.from_json(json.dumps(vecchio)).meta.mescola is None)

solo_racconto = SessionBundle(
    meta=Meta(fonte=Fonte.MANUALE, piattaforma="playstation"),
    racconto=Racconto(andamento="sottosterzo in ingresso nelle lente, gomme calde dopo 6 giri",
                      curve_critiche=["Variante 1", "Ascari"]),
)
test("L39 una sessione con il solo racconto ha dati utili", solo_racconto.ha_dati_utili())
rr = analizza(solo_racconto)
test("L40 …si analizza senza crollare, e il report sa che il racconto c'è",
     rr.ha_racconto is True and rr.giri_totali == 0)
test("L41 …dichiarando che mancano i giri",
     any("nessun giro" in d for d in rr.dati_mancanti), f"{rr.dati_mancanti}")

# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Analisi L4 allineata alle decisioni del 16/09")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
