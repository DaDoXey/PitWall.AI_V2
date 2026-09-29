"""
test_aggancio.py — la guida del tracciato agganciata ai tratti del motore (Entry #047)

Quel che si prova qui:

* la regola: una curva della guida sta nel tratto del motore che ne contiene l'**apice**,
  anche quando il tratto scavalca il traguardo;
* il nome di un tratto: intervallo più nomi distinti senza le fasi («T8-T10 Variante
  Ascari»), una curva sola col nome intero, una senza nome resta «T9»;
* le curve della guida con le ancore vere di Monza e Zandvoort, e sui tratti che il
  motore trova davvero sulla Ferrari di Monza (29/09) l'abbinamento atteso;
* il verdetto per curva prende il nome della guida, e il metro dell'apice scende nella
  prova; senza nomi resta com'era;
* la demo non si aggancia, e lo dice; una pista senza ancore non ha aggancio.

Tutto offline, nessuna spesa.
"""

import json
import pathlib
import sys
from dataclasses import dataclass

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from app.analisi import aggancio as agg  # noqa: E402
from app.analisi import analizza  # noqa: E402
from app.analisi.aggancio import CurvaAgganciata, etichetta  # noqa: E402
from app.analisi.curve import analizza_curve  # noqa: E402
from app.bundle import demo  # noqa: E402
from app.tests.pista_finta import CurvaFinta, GiroFinto, genera, pista_tre_curve  # noqa: E402

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


@dataclass
class Tratto:
    numero: int
    ingresso: float
    uscita: float


def curva(n: int, nome: str | None, apice: float = 0.5) -> CurvaAgganciata:
    return CurvaAgganciata(n=n, nome=nome, inizio=apice - 0.01, apice=apice,
                           uscita=apice + 0.01, mappa=None)


# ---------------------------------------------------------------------------
# 1 · La regola dell'apice
# ---------------------------------------------------------------------------
print("\n─── L'apice decide il tratto ───")

normale = Tratto(1, 0.20, 0.40)
scavalca = Tratto(6, 0.864, 0.1295)          # la Parabolica: dal 86% al 13% del giro dopo
test("A01 un apice dentro il tratto ci sta", agg.dentro(0.30, normale))
test("A02 l'ingresso è compreso, l'uscita no (i tratti si toccano)",
     agg.dentro(0.20, normale) and not agg.dentro(0.40, normale))
test("A03 un tratto a cavallo del traguardo prende la fine del giro…",
     agg.dentro(0.90, scavalca))
test("A04 …e l'inizio del giro dopo", agg.dentro(0.05, scavalca))
test("A05 …ma non il mezzo", not agg.dentro(0.50, scavalca))
test("A06 fuori da tutti i tratti: nessun tratto, non uno a caso",
     agg.tratto_di(0.60, [normale]) is None)

# ---------------------------------------------------------------------------
# 2 · Il nome di un tratto
# ---------------------------------------------------------------------------
print("\n─── Il nome del tratto ───")

test("A07 una curva: numero e nome intero",
     etichetta([curva(11, "Curva Parabolica (Alboreto)")]) == "T11 Curva Parabolica (Alboreto)")
test("A08 una curva senza nome resta il numero", etichetta([curva(9, None)]) == "T9")
ascari = [curva(8, "Variante Ascari (ingresso)"), curva(9, "Variante Ascari (centro)"),
          curva(10, "Variante Ascari (uscita)")]
test("A09 le fasi di una stessa curva diventano un nome solo",
     etichetta(ascari) == "T8-T10 Variante Ascari", etichetta(ascari))
rettifilo = [curva(1, "Variante del Rettifilo"), curva(2, "Variante del Rettifilo (uscita)"),
             curva(3, "Curva Grande")]
test("A10 nomi diversi nello stesso tratto: tutti, separati",
     etichetta(rettifilo) == "T1-T3 Variante del Rettifilo · Curva Grande", etichetta(rettifilo))
test("A11 l'ordine è quello della guida, non quello d'arrivo",
     etichetta(list(reversed(rettifilo))) == etichetta(rettifilo))
test("A12 curve non consecutive: elencate, non un intervallo che mente",
     etichetta([curva(1, "A"), curva(3, "B")]) == "T1, T3 A · B")
test("A13 più curve senza nome: solo l'intervallo",
     etichetta([curva(9, None), curva(10, None)]) == "T9-T10")
test("A14 nessuna curva: nessun nome", etichetta([]) is None)

# ---------------------------------------------------------------------------
# 3 · Le curve della guida con le ancore vere
# ---------------------------------------------------------------------------
print("\n─── Ancore di Monza e Zandvoort ───")

monza = agg.curve_della_pista("monza")
zandvoort = agg.curve_della_pista("zandvoort")
test("A15 Monza: 11 curve della guida ancorate", monza is not None and len(monza) == 11,
     f"{monza and len(monza)}")
test("A16 Zandvoort: 14", zandvoort is not None and len(zandvoort) == 14,
     f"{zandvoort and len(zandvoort)}")
test("A17 ogni curva ha inizio < apice e il punto sulla mappa",
     all(c.mappa and 0 <= c.inizio <= 1 and 0 <= c.apice <= 1 for c in (monza or []) + (zandvoort or [])))
test("A18 il nome viene dalla guida: la T10 di Zandvoort non ce l'ha, e non si inventa",
     next(c for c in zandvoort if c.n == 10).nome is None)
test("A19 una pista senza ancore non ha aggancio", agg.aggancia("spa_francorchamps", None) is None)
test("A20 una sessione senza pista neanche", agg.aggancia(None, None) is None)

# I tratti che il motore trova sulla Ferrari 488 di PS_Racing a Monza (29/09/2026).
tratti_ferrari = [Tratto(1, 0.1295, 0.3425), Tratto(2, 0.3425, 0.4205), Tratto(3, 0.4205, 0.481),
                  Tratto(4, 0.481, 0.657), Tratto(5, 0.657, 0.864), Tratto(6, 0.864, 0.1295)]
a = agg.aggancia("monza", tratti_ferrari)
test("A21 ogni curva della guida finisce in un tratto",
     a is not None and all(c.tratto is not None for c in a.curve))
atteso = {1: "T1-T3 Variante del Rettifilo · Curva Grande", 2: "T4-T5 Variante della Roggia",
          3: "T6 Curva di Lesmo 1", 4: "T7 Curva di Lesmo 2", 5: "T8-T10 Variante Ascari",
          6: "T11 Curva Alboreto"}
test("A22 l'abbinamento di Monza è quello atteso, tratto per tratto",
     a is not None and a.tratti == atteso, f"{a and a.tratti}")
test("A23 la Parabolica sta nel tratto che scavalca il traguardo",
     next(c for c in a.curve if c.n == 11).tratto == 6)

senza_tratti = agg.aggancia("monza", None)
test("A24 senza analisi per curva (un giro solo) le curve della guida ci sono lo stesso…",
     senza_tratti is not None and len(senza_tratti.curve) == 11)
test("A25 …senza tratto e senza nomi di tratto",
     all(c.tratto is None for c in senza_tratti.curve) and senza_tratti.tratti == {})

j = a.come_json()
test("A26 il blocco si serializza in JSON (chiavi dei tratti come testo)",
     set(j) == {"pista", "curve", "tratti", "nota"} and "5" in j["tratti"]
     and json.loads(json.dumps(j, ensure_ascii=False)) == j)

d = agg.aggancia("monza", tratti_ferrari, demo=True)
test("A27 la demo non si aggancia: nessuna curva…", d is not None and d.curve == [] and d.tratti == {})
test("A28 …e una riga che dice perché", d is not None and d.nota == agg.NOTA_DEMO)

# ---------------------------------------------------------------------------
# 4 · Il verdetto per curva prende il nome
# ---------------------------------------------------------------------------
print("\n─── Il verdetto con i nomi della guida ───")

pista = pista_tre_curve()
buone = pista.curve
storte = [buone[0],
          CurvaFinta(posizione_m=1500.0, velocita_minima_kmh=105.0, frenata_m=160.0),
          buone[2]]
misto = genera(pista, [GiroFinto(curve=buone), GiroFinto(curve=storte), GiroFinto(curve=buone)])

visti: list = []


def nomi(curve):
    visti.extend(curve)
    return {c.numero: f"T{c.numero + 3} Curva di prova" for c in curve}


con = analizza_curve(misto, nomi_tratti=nomi)
senza = analizza_curve(misto)
test("A29 la funzione dei nomi riceve le curve trovate dal motore",
     [c.numero for c in visti] == [c.numero for c in con.curve])
principale = next(v for v in con.verdetto if v.titolo.startswith("Perdi "))
test("A30 il titolo dice la curva del motore e il nome della guida",
     principale.titolo.endswith("in curva 2 (T5 Curva di prova)"), principale.titolo)
test("A31 il metro dell'apice scende nella prova",
     principale.prova.startswith("apice al metro "), principale.prova)
test("A32 anche le altre voci della stessa curva portano il nome",
     all("(T5 Curva di prova)" in v.titolo for v in con.verdetto if v.curva == 2),
     f"{[v.titolo for v in con.verdetto]}")
principale_senza = next(v for v in senza.verdetto if v.titolo.startswith("Perdi "))
test("A33 senza nomi il titolo resta quello di prima (apice nel titolo)",
     "(apice al metro" in principale_senza.titolo
     and not principale_senza.prova.startswith("apice"), principale_senza.titolo)
test("A34 i numeri non cambiano: stesse perdite con e senza nomi",
     [(v.curva, v.perdita_ms) for v in con.verdetto]
     == [(v.curva, v.perdita_ms) for v in senza.verdetto])

# ---------------------------------------------------------------------------
# 5 · Nel report del motore
# ---------------------------------------------------------------------------
print("\n─── Nel report ───")

bundle_demo, canali_demo, _ = demo.costruisci()
report_demo = analizza(bundle_demo, canali_demo)
test("A35 la demo (Monza) ha il blocco d'aggancio con la sola nota",
     report_demo.aggancio is not None and report_demo.aggancio["curve"] == []
     and report_demo.aggancio["nota"] == agg.NOTA_DEMO)
test("A36 …e il suo verdetto non prende nomi della guida",
     not any("(T" in v.titolo for v in report_demo.verdetto),
     f"{[v.titolo for v in report_demo.verdetto]}")
report_senza = analizza(bundle_demo, None)
test("A37 senza canali niente aggancio (non ci sono grafici su cui metterlo)",
     report_senza.aggancio is None)

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Aggancio della guida conforme")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
