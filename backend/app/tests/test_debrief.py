"""
test_debrief.py — il debrief di Gigi fase per fase (Entry #059)

Controlla che le fasi si taglino come dice la regola (avvio · il giro · calo/tenuta),
che i tagli a mano si validino e si salvino nella sessione, e che ogni frase porti
numeri del report e non numeri inventati.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_debrief.py

Non richiede pytest, né rete, né chiave.
"""

import os
import pathlib
import shutil
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from app.analisi import analizza  # noqa: E402
from app.analisi.debrief import TagliNonValidi, debrief, tagli_automatici  # noqa: E402
from app.bundle import demo  # noqa: E402
from app.bundle.schema import Fonte, Giro, Meta, SessionBundle, TipoSessione  # noqa: E402

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


def errore(fn) -> str | None:
    try:
        fn()
    except TagliNonValidi as e:
        return str(e)
    return None


def sessione(tempi: list[int | None], **meta) -> SessionBundle:
    campi = {"fonte": Fonte.ACC_RESULTS, "car": "bmw_m4_gt3", "track": "monza",
             "tipo_sessione": TipoSessione.PROVE}
    campi.update(meta)
    return SessionBundle(meta=Meta(**campi),
                         giri=[Giro(numero=i + 1, tempo_ms=t) for i, t in enumerate(tempi)])


# ---------------------------------------------------------------------------
# 1 · La demo: tre fasi, con curve e gomme
# ---------------------------------------------------------------------------
print("\n─── La demo ───")
bundle, canali, _ = demo.costruisci()
report = analizza(bundle, canali)
d = debrief(report)

test("F01 fasi di Gigi: avvio (G1–3) · il giro (G4) · il calo (G5–8)",
     [(f.tipo, f.giri) for f in d.fasi] == [("avvio", [1, 2, 3]), ("giro", [4]), ("calo", [5, 6, 7, 8])],
     str([(f.tipo, f.giri) for f in d.fasi]))
test("F02 i tagli automatici sono il giro migliore e quello dopo", d.tagli == [4, 5] and not d.manuale)
test("F03 «in ballo» = media dei giri di ritmo − giro migliore (1:48.504 − 1:47.820)",
     d.in_ballo_ms == 684, str(d.in_ballo_ms))
test("F04 la striscia dei giri porta lo scarto dal migliore (G1 +1.600, G4 migliore)",
     d.giri[0].delta_ms == 1600 and d.giri[3].migliore and d.giri[3].delta_ms == 0)
avvio, giro, calo = d.fasi
test("F05 l'avvio dice lo scarto medio dei suoi giri", "+0.73 s" in avvio.messaggio, avvio.messaggio)
test("F06 …e dove lascia il grosso (curva 1, soprattutto nei primi giri)",
     "curva 1" in avvio.messaggio and avvio.punti[0].curva == 1, avvio.messaggio)
test("F07 nell'avvio le gomme non si giudicano (stanno ancora salendo)",
     "finestra" not in avvio.messaggio and "gomme" not in avvio.argomenti)
test("F08 il giro: tempo e distanza dal teorico",
     "1:47.820" in giro.messaggio and "10 millesimi" in giro.messaggio, giro.messaggio)
test("F09 il calo: il degrado del motore, la curva peggiore e le gomme",
     "352 millesimi" in calo.messaggio and "curva 7" in calo.messaggio
     and "Post.DX arriva a 105 °C" in calo.messaggio, calo.messaggio)
test("F09b lo stato delle gomme nel calo: posteriori basse, la destra calda, anteriori ok",
     calo.stato_gomme == {"FL": "ok", "FR": "ok", "RL": "bassa", "RR": "calda"}, str(calo.stato_gomme))
test("F09c nell'avvio lo stato delle gomme non si dà", avvio.stato_gomme is None)
test("F10 gli argomenti portano alle altre sezioni (ritmo, curve, gomme)",
     {"ritmo", "curva:7", "gomme"} <= set(calo.argomenti), str(calo.argomenti))
test("F11 la prima cosa da fare è la voce più grave che tocca il setup",
     d.prima_cosa is not None and d.prima_cosa.categoria == "gomme"
     and d.prima_cosa.parametri == {"tire_press_rl": 0.6, "tire_press_rr": 0.8}, str(d.prima_cosa))
test("F12 sulla demo non c'è aggancio: le curve restano numerate, senza punto sulla mappa",
     all(p.nome is None and p.mappa is None for f in d.fasi for p in f.punti))

# ---------------------------------------------------------------------------
# 2 · Tagli a mano
# ---------------------------------------------------------------------------
print("\n─── Tagli a mano ───")
m = debrief(report, [6, 3, 6])
test("F13 tagli a mano: ordinati e senza doppioni", m.tagli == [3, 6] and m.manuale, str(m.tagli))
test("F14 ogni fase prende il tipo dalla posizione rispetto al migliore",
     [(f.tipo, f.giri) for f in m.fasi] == [("avvio", [1, 2]), ("giro", [3, 4, 5]), ("calo", [6, 7, 8])])
test("F15 nel giro ritagliato largo, lo scarto degli altri giri esclude il migliore (+0.16 s)",
     "+0.16 s" in m.fasi[1].messaggio, m.fasi[1].messaggio)
doppio = debrief(report, [4, 5, 7])
test("F16 due fasi dello stesso tipo: il nome dice i giri",
     [f.nome for f in doppio.fasi][-2:] == ["Il calo · G5–6", "Il calo · G7–8"], str([f.nome for f in doppio.fasi]))
test("F17 nessun taglio = una fase sola", len(debrief(report, []).fasi) == 1)
msg = errore(lambda: debrief(report, [1]))
test("F18 il primo giro non si taglia (una fase comincia già lì)", msg is not None and "primo" in msg, str(msg))
msg = errore(lambda: debrief(report, [42]))
test("F19 un giro che non esiste (o non di ritmo) viene rifiutato", msg is not None and "42" in msg, str(msg))

# ---------------------------------------------------------------------------
# 3 · Sessioni senza canali
# ---------------------------------------------------------------------------
print("\n─── Solo tempi ───")
b = sessione([None, 120000, 108000, 107500, 107000, 107300, 107400, 107450])
r = analizza(b, None)
s = debrief(r)
test("F20 senza canali le fasi restano (avvio · il giro · dopo)",
     [f.tipo for f in s.fasi][:2] == ["avvio", "giro"] and len(s.fasi) == 3, str([f.tipo for f in s.fasi]))
test("F21 …e parlano solo di tempi, dicendolo", s.nota is not None and "telemetria" in s.nota
     and all(not f.punti and f.stato_gomme is None for f in s.fasi))
test("F22 il giro buttato (out lap lento) resta fuori dal ritmo", 2 in s.fuori_ritmo, str(s.fuori_ritmo))
test("F23 senza degrado dimostrato il dopo è «La tenuta», non «Il calo»",
     s.fasi[-1].tipo == "tenuta", s.fasi[-1].tipo)
sparsi = debrief(analizza(sessione([None, 150000, 108000, 107900, 175000, 107800, 107500]), None))
test("F24 giri di ritmo non consecutivi prima del migliore: «nei 3 giri prima del migliore», non «nei primi»",
     sparsi.fasi[0].giri == [3, 4, 6] and "Nei 3 giri prima del migliore" in sparsi.fasi[0].messaggio,
     f"{sparsi.fasi[0].giri} {sparsi.fasi[0].messaggio}")
ultimo = debrief(analizza(sessione([108000, 107800, 107600]), None))
test("F25 migliore all'ultimo giro: solo avvio e il giro", [f.tipo for f in ultimo.fasi] == ["avvio", "giro"],
     str([f.tipo for f in ultimo.fasi]))
test("F26 tagli automatici su un giro solo: nessuno", tagli_automatici(analizza(sessione([107000]), None)) == [])
vuoto = debrief(analizza(sessione([None, None]), None))
test("F27 nessun giro di ritmo: niente fasi, e lo dice", not vuoto.fasi and vuoto.nota is not None)

# ---------------------------------------------------------------------------
# 4 · Le rotte: leggere il debrief, salvare i tagli
# ---------------------------------------------------------------------------
print("\n─── Rotte ───")
radice = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_debrief_"))
os.environ["PITWALL_SESSIONS_DIR"] = str(radice)
try:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.bundle import store  # noqa: E402
    from app.main import app as fastapi_app  # noqa: E402

    client = TestClient(fastapi_app, raise_server_exceptions=False)
    ident = store.salva(bundle)

    resp = client.get(f"/api/sessions/{ident}/debrief")
    test("F28 GET /debrief risponde con le fasi di Gigi",
         resp.status_code == 200 and [f["tipo"] for f in resp.json()["fasi"]] == ["avvio", "giro", "calo"],
         resp.text[:200])
    resp = client.put(f"/api/sessions/{ident}/debrief/tagli", json={"tagli": [3, 6]})
    test("F29 PUT dei tagli risponde con il debrief nuovo", resp.status_code == 200
         and resp.json()["tagli"] == [3, 6] and resp.json()["manuale"] is True, resp.text[:200])
    test("F30 i tagli restano salvati nella sessione", store.leggi(ident).fasi_tagli == [3, 6])
    test("F31 …e il GET dopo li usa",
         client.get(f"/api/sessions/{ident}/debrief").json()["tagli"] == [3, 6])
    test("F32 tagli non validi → 422 con il motivo, niente salvato",
         client.put(f"/api/sessions/{ident}/debrief/tagli", json={"tagli": [1]}).status_code == 422
         and store.leggi(ident).fasi_tagli == [3, 6])
    test("F33 un taglio non intero → 422",
         client.put(f"/api/sessions/{ident}/debrief/tagli", json={"tagli": ["3"]}).status_code == 422)
    resp = client.put(f"/api/sessions/{ident}/debrief/tagli", json={"tagli": None})
    test("F34 null torna alle fasi di Gigi", resp.status_code == 200 and resp.json()["manuale"] is False
         and store.leggi(ident).fasi_tagli is None)
    # Tagli salvati che non valgono più: il GET ripiega sulle fasi di Gigi, dicendolo.
    rotto = store.leggi(ident)
    rotto.fasi_tagli = [99]
    store.salva(rotto, ident)
    resp = client.get(f"/api/sessions/{ident}/debrief")
    test("F35 tagli salvati non più validi: fasi di Gigi e una nota, non un errore",
         resp.status_code == 200 and resp.json()["manuale"] is False and "non valgono" in (resp.json()["nota"] or ""))
    test("F36 sessione che non c'è → 404",
         client.get("/api/sessions/20990101-000000-nessuna-0000/debrief").status_code == 404)
    os.environ["PITWALL_ALLOW_IMPORT"] = "0"
    test("F37 con le scritture spente (vetrina) i tagli non si salvano: 503",
         client.put(f"/api/sessions/{ident}/debrief/tagli", json={"tagli": [4]}).status_code == 503)
    os.environ.pop("PITWALL_ALLOW_IMPORT", None)
finally:
    os.environ.pop("PITWALL_SESSIONS_DIR", None)
    shutil.rmtree(radice, ignore_errors=True)

# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Debrief fase per fase in ordine")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
