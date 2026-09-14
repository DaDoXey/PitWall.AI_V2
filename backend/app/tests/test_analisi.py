"""
test_analisi.py — il motore di analisi (L2, Entry #033)

I numeri del motore sono calcolati a mano nei commenti di ogni blocco: se un test
fallisce, il conto giusto è scritto lì accanto e si vede subito chi ha torto fra il
test e il codice. Nessun LLM, nessuna rete.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_analisi.py
"""

import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))  # -> backend/

from app.analisi import analizza  # noqa: E402
from app.bundle.adapters import leggi_results_acc  # noqa: E402
from app.bundle.schema import Fonte, Giro, Meta, SessionBundle, TipoSessione  # noqa: E402

FIX = pathlib.Path(__file__).parent / "fixtures"

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


def bundle(giri: list[Giro], **meta) -> SessionBundle:
    campi = {"fonte": Fonte.ACC_RESULTS, "car": "bmw_m4_gt3", "track": "monza",
             "tipo_sessione": TipoSessione.QUALIFICA}
    campi.update(meta)
    return SessionBundle(meta=Meta(**campi), giri=giri)


def vicino(a, b, tolleranza=1) -> bool:
    return a is not None and abs(a - b) <= tolleranza


print("\n" + "═" * 60)
print("TEST — motore di analisi")
print("═" * 60 + "\n")

# ---------------------------------------------------------------------------
# 1. Sessione di riferimento, conti fatti a mano
#    giri di ritmo: 100000, 101000, 102000, 100500 (out lap 120000 e rientro
#    130000 esclusi: soglia = 100000 × 1,10 = 110000)
#    settori migliori: 29500 + 35000 + 35000 = 99500 → teorico 99500
#    lasciato sul tavolo: 100000 − 99500 = 500 ms = 5,0 decimi
# ---------------------------------------------------------------------------
sessione = bundle([
    Giro(numero=1, tempo_ms=120000, splits_ms=[45000, 38000, 37000]),   # out lap
    Giro(numero=2, tempo_ms=100000, splits_ms=[30000, 35000, 35000]),
    Giro(numero=3, tempo_ms=101000, splits_ms=[29500, 36000, 35500]),
    Giro(numero=4, tempo_ms=102000, splits_ms=[30500, 35500, 36000]),
    Giro(numero=5, tempo_ms=100500, splits_ms=[29800, 35200, 35500]),
    Giro(numero=6, tempo_ms=130000, splits_ms=[30000, 35000, 65000]),   # rientro ai box
])
r = analizza(sessione)

test("N01 conta tutti i giri della sessione", r.giri_totali == 6, str(r.giri_totali))
test("N02 tiene solo i giri di ritmo per le statistiche", r.giri_di_ritmo == 4, str(r.giri_di_ritmo))
test("N03 e dichiara quanti ne ha esclusi", r.giri_esclusi_dal_ritmo == 2,
     str(r.giri_esclusi_dal_ritmo))
test("N04 out lap e rientro non inquinano il miglior giro",
     r.ritmo.miglior_giro_ms == 100000, str(r.ritmo.miglior_giro_ms))
test("N05 giro teorico = somma dei settori migliori (29500+35000+35000)",
     r.ritmo.giro_teorico_ms == 99500, str(r.ritmo.giro_teorico_ms))
test("N06 lasciato sul tavolo = 500 ms", r.ritmo.lasciato_sul_tavolo_ms == 500,
     str(r.ritmo.lasciato_sul_tavolo_ms))
test("N07 media dei giri di ritmo = 100875", r.ritmo.media_ms == 100875, str(r.ritmo.media_ms))
test("N08 mediana = 100750", r.ritmo.mediana_ms == 100750, str(r.ritmo.mediana_ms))
test("N09 media dei 3 migliori = 100500", r.ritmo.media_migliori_3_ms == 100500,
     str(r.ritmo.media_migliori_3_ms))

s1, s2, s3 = r.settori
test("N10 tre settori, numerati da 1", [s.numero for s in r.settori] == [1, 2, 3])
test("N11 settore 1: migliore 29500, media 29950, perdita 450",
     (s1.migliore_ms, s1.media_ms, s1.perdita_media_ms) == (29500, 29950, 450),
     f"{s1.migliore_ms}/{s1.media_ms}/{s1.perdita_media_ms}")
test("N12 settore 2: migliore 35000, media 35425, perdita 425",
     (s2.migliore_ms, s2.media_ms, s2.perdita_media_ms) == (35000, 35425, 425))
test("N13 settore 3: migliore 35000, media 35500, perdita 500",
     (s3.migliore_ms, s3.media_ms, s3.perdita_media_ms) == (35000, 35500, 500))
test("N14 dispersione del settore 1 ≈ 364 ms", vicino(s1.deviazione_ms, 364),
     str(s1.deviazione_ms))
test("N15 sul giro migliore il settore 1 costava 500 ms",
     s1.perdita_sul_giro_migliore_ms == 500, str(s1.perdita_sul_giro_migliore_ms))
test("N16 e i settori 2 e 3 erano già i migliori",
     (s2.perdita_sul_giro_migliore_ms, s3.perdita_sul_giro_migliore_ms) == (0, 0))

test("N17 deviazione dei tempi ≈ 740 ms", vicino(r.costanza.deviazione_ms, 740),
     str(r.costanza.deviazione_ms))
test("N18 scarto dal migliore al peggiore = 2000 ms", r.costanza.scarto_max_ms == 2000,
     str(r.costanza.scarto_max_ms))
test("N19 due giri su quattro entro mezzo secondo (50%)",
     (r.costanza.giri_entro_mezzo_secondo, r.costanza.percentuale_entro_mezzo_secondo) == (2, 50.0),
     f"{r.costanza.giri_entro_mezzo_secondo}/{r.costanza.percentuale_entro_mezzo_secondo}")
test("N20 il giudizio non è una carezza", "ballerina" in (r.costanza.giudizio or ""),
     str(r.costanza.giudizio))

test("N21 con 4 giri il degrado non si calcola e lo dice",
     r.degrado.calcolabile is False and "almeno 5" in (r.degrado.motivo or ""),
     str(r.degrado.motivo))

# ---------------------------------------------------------------------------
# 2. Verdetto
# ---------------------------------------------------------------------------
titoli = [v.titolo for v in r.verdetto]
test("N22 il verdetto elenca le perdite trovate", len(r.verdetto) >= 2, str(titoli))
test("N23 ogni voce porta il numero che la dimostra",
     all(v.prova.strip() for v in r.verdetto))
test("N24 e l'azione che la chiude", all(v.azione.strip() for v in r.verdetto))
test("N25 le voci sono ordinate per gravità",
     [v.gravita for v in r.verdetto] == sorted((v.gravita for v in r.verdetto), reverse=True))
test("N26 il giro mai messo insieme compare con i suoi 5 decimi",
     any("insieme" in t for t in titoli)
     and next(v.decimi for v in r.verdetto if "insieme" in v.titolo) == 5.0,
     str(titoli))
test("N27 il settore peggiore è il 3, non un altro",
     any("Settore 3" in t for t in titoli), str(titoli))

# ---------------------------------------------------------------------------
# 3. Degrado: sei giri che peggiorano di 200 ms l'uno
#    pendenza attesa 200 ms/giro, R² = 1, perdita su 10 giri = 2000 ms
# ---------------------------------------------------------------------------
calante = bundle([Giro(numero=i + 1, tempo_ms=100000 + 200 * i,
                       splits_ms=[30000, 35000, 35000 + 200 * i]) for i in range(6)])
d = analizza(calante)
test("N28 la pendenza del degrado è esatta (200 ms/giro)",
     d.degrado.calcolabile and vicino(d.degrado.pendenza_ms_giro, 200, 0.5),
     str(d.degrado.pendenza_ms_giro))
test("N29 con un degrado perfettamente lineare R² = 1", vicino(d.degrado.r_quadro, 1.0, 0.001),
     str(d.degrado.r_quadro))
test("N30 la perdita su dieci giri è 2000 ms", d.degrado.perdita_su_10_giri_ms == 2000,
     str(d.degrado.perdita_su_10_giri_ms))
test("N31 e il verdetto lo dice", any("cala con lo stint" in v.titolo for v in d.verdetto),
     str([v.titolo for v in d.verdetto]))

migliorante = bundle([Giro(numero=i + 1, tempo_ms=101000 - 200 * i,
                           splits_ms=[30000, 35000, 35000]) for i in range(6)])
m = analizza(migliorante)
test("N32 un ritmo che migliora non viene spacciato per degrado",
     not any("cala con lo stint" in v.titolo for v in m.verdetto)
     and (m.degrado.pendenza_ms_giro or 0) < 0, str(m.degrado.pendenza_ms_giro))

# ---------------------------------------------------------------------------
# 4. Giri buttati
# ---------------------------------------------------------------------------
tagliati = bundle([
    Giro(numero=1, tempo_ms=100000, splits_ms=[30000, 35000, 35000]),
    Giro(numero=2, tempo_ms=99500, splits_ms=[29800, 34900, 34800], valido=False),
    Giro(numero=3, tempo_ms=99000, splits_ms=[29700, 34800, 34500], valido=False),
    Giro(numero=4, tempo_ms=100500, splits_ms=[30100, 35100, 35300]),
])
t = analizza(tagliati)
test("N33 i giri invalidi sono contati", t.giri_buttati == 2, str(t.giri_buttati))
test("N34 e non entrano nel miglior giro (99000 era invalido)",
     t.ritmo.miglior_giro_ms == 100000, str(t.ritmo.miglior_giro_ms))
test("N35 il verdetto rinfaccia i giri buttati",
     any("buttati" in v.titolo for v in t.verdetto), str([v.titolo for v in t.verdetto]))

# ---------------------------------------------------------------------------
# 5. Quando un dato non c'è, si dice
# ---------------------------------------------------------------------------
senza_split = bundle([Giro(numero=i + 1, tempo_ms=100000 + 100 * i) for i in range(5)])
ns = analizza(senza_split)
test("N36 senza split non si inventa un giro teorico", ns.ritmo.giro_teorico_ms is None)
test("N37 e la mancanza è dichiarata", any("settori" in x for x in ns.dati_mancanti),
     str(ns.dati_mancanti))
test("N38 ma ritmo e costanza si calcolano lo stesso",
     ns.ritmo.miglior_giro_ms == 100000 and ns.costanza.deviazione_ms is not None)

test("N39 le gomme e i freni assenti sono dichiarati, non taciuti",
     any("gomme" in x for x in ns.dati_mancanti))
test("N40 e anche il setup mancante", any("setup" in x for x in ns.dati_mancanti))

consumo = bundle([
    Giro(numero=1, tempo_ms=100000, carburante_residuo_l=84.0),
    Giro(numero=2, tempo_ms=100500, carburante_residuo_l=80.4, carburante_usato_l=3.6),
    Giro(numero=3, tempo_ms=100200, carburante_residuo_l=76.8, carburante_usato_l=3.6),
])
c = analizza(consumo)
test("N41 il consumo medio si calcola quando i dati ci sono",
     c.carburante.calcolabile and vicino(c.carburante.consumo_medio_l_giro, 3.6, 0.01),
     str(c.carburante.consumo_medio_l_giro))
test("N42 e dice su quanti giri l'ha misurato", c.carburante.giri_misurati == 2)

costante = bundle([Giro(numero=i + 1, tempo_ms=100000 + 100 * i, carburante_residuo_l=81.0)
                   for i in range(4)])
k = analizza(costante)
test("N43 col carburante costante non inventa un consumo",
     k.carburante.calcolabile is False and k.carburante.consumo_medio_l_giro is None)
test("N44 e spiega perché", "shared memory" in (k.carburante.motivo or ""),
     str(k.carburante.motivo))

# ---------------------------------------------------------------------------
# 6. Casi limite: non deve mai esplodere
# ---------------------------------------------------------------------------
vuoto = analizza(bundle([]))
test("N45 una sessione senza giri non fa saltare il motore",
     vuoto.ritmo.giri_validi == 0 and vuoto.verdetto == [])
test("N46 e dichiara comunque cosa manca", len(vuoto.dati_mancanti) >= 2)

uno = analizza(bundle([Giro(numero=1, tempo_ms=100000, splits_ms=[30000, 35000, 35000])]))
test("N47 con un solo giro niente costanza inventata",
     uno.costanza.deviazione_ms is None and "almeno 3" in (uno.costanza.giudizio or ""))
test("N48 con un solo giro niente settori (non c'è confronto)", uno.settori == [])
test("N49 ma il miglior giro c'è", uno.ritmo.miglior_giro_ms == 100000)

identici = analizza(bundle([Giro(numero=i + 1, tempo_ms=100000,
                                 splits_ms=[30000, 35000, 35000]) for i in range(5)]))
test("N50 giri identici: deviazione zero e nessuna lamentela sulla costanza",
     identici.costanza.deviazione_ms == 0
     and not any("Costanza" in v.titolo for v in identici.verdetto))
test("N51 giri identici: niente giro teorico più veloce del reale",
     identici.ritmo.lasciato_sul_tavolo_ms == 0)

# ---------------------------------------------------------------------------
# 7. Su un file di ACC vero (fixture con la struttura reale)
# ---------------------------------------------------------------------------
vero = analizza(leggi_results_acc(FIX / "acc_results_gioco_prove.json", track="monza"))
test("N52 il motore gira su un bundle importato da ACC", vero.giri_totali == 4)
test("N53 out lap e rientro riconosciuti anche lì", vero.giri_esclusi_dal_ritmo == 2,
     str(vero.giri_esclusi_dal_ritmo))
test("N54 il miglior giro è quello giusto (103134)", vero.ritmo.miglior_giro_ms == 103134,
     str(vero.ritmo.miglior_giro_ms))
# Questa fixture ha un residuo che cala davvero, quindi il consumo si calcola:
# ciò che resta dichiarato è l'assunzione dell'import sulla validità dei giri.
test("N55 le assunzioni dell'import finiscono nei dati mancanti del report",
     any("validità" in x for x in vero.dati_mancanti), str(vero.dati_mancanti)[:200])
test("N55b e qui il consumo si calcola, perché il residuo cala davvero",
     vero.carburante.calcolabile is True, str(vero.carburante.motivo))
test("N56 il report è serializzabile in JSON", len(vero.model_dump_json()) > 100)

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Motore di analisi conforme")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
