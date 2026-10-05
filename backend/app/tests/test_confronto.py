"""
test_confronto.py — «Sono migliorato?»: la sessione contro la precedente (Entry #074)

Controlla che la precedente sia quella giusta (stessa pista e vettura, stesso gruppo, la
più vicina prima), che ritmo, curve, setup e gomme si confrontino con numeri del motore,
che le condizioni diverse si dichiarino e che quello che manca non venga inventato.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_confronto.py

Non richiede pytest, né rete, né chiave.
"""

import os
import pathlib
import shutil
import sys
import tempfile
from types import SimpleNamespace

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from app.analisi import analizza  # noqa: E402
from app.analisi.confronto import (  # noqa: E402
    SOGLIA_TRATTO_MS,
    confronta,
    scegli_precedente,
)
from app.bundle import demo, demo_precedente  # noqa: E402
from app.bundle.schema import Fonte, Giro, Mescola, Meta, SessionBundle, TipoSessione  # noqa: E402

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


def sessione(tempi: list[int | None], **meta) -> SessionBundle:
    campi = {"fonte": Fonte.ACC_RESULTS, "car": "bmw_m4_gt3", "track": "monza",
             "tipo_sessione": TipoSessione.PROVE}
    campi.update(meta)
    return SessionBundle(meta=Meta(**campi),
                         giri=[Giro(numero=i + 1, tempo_ms=t) for i, t in enumerate(tempi)])


def riga(c, inizio: str) -> str:
    return next((p for p in c.prova if p.startswith(inizio)), "")


# ---------------------------------------------------------------------------
# 1 · La demo contro la sua «volta prima»
# ---------------------------------------------------------------------------
print("\n─── La demo e la volta prima ───")
oggi, canali_oggi, _ = demo.costruisci()
prima, canali_prima = demo_precedente.costruisci()
r_oggi, r_prima = analizza(oggi, canali_oggi), analizza(prima, canali_prima)
c = confronta(oggi, r_oggi, canali_oggi, prima, r_prima, canali_prima, demo_precedente.ID)

test("C01 la demo di oggi non è cambiata: migliore 1:47.820 al giro 4",
     r_oggi.ritmo.miglior_giro_ms == 107820 and r_oggi.ritmo.miglior_giro_numero == 4)
test("C02 la volta prima: migliore 1:48.150 al giro 3, otto giri di ritmo",
     r_prima.ritmo.miglior_giro_ms == 108150 and r_prima.ritmo.miglior_giro_numero == 3
     and r_prima.giri_di_ritmo == 8, f"{r_prima.ritmo.miglior_giro_ms} g{r_prima.ritmo.miglior_giro_numero}")
test("C03 la volta prima è del giorno prima, stessa pista e vettura, fonte demo",
     prima.meta.iniziata_il < oggi.meta.iniziata_il and prima.meta.car == oggi.meta.car
     and prima.meta.track == oggi.meta.track and prima.meta.fonte is Fonte.DEMO)
test("C04 la volta prima si dichiara sintetica, e dichiara le pressioni cambiate dal generatore",
     any("SINTETICA" in a for a in prima.assunzioni) and any("posteriori" in a for a in prima.setup.assunzioni))
test("C05 ritmo: giro migliore −330 ms, media −568 ms",
     c.ritmo.delta_migliore_ms == -330 and c.ritmo.delta_media_ms == r_oggi.ritmo.media_ms - r_prima.ritmo.media_ms
     and c.ritmo.delta_media_ms == -568, f"{c.ritmo}")
test("C06 il messaggio risponde «Sì» con i due tempi",
     c.messaggio.startswith("Sì: il giro migliore è 0.33 s più veloce della volta prima (1:47.820 contro 1:48.150)."),
     c.messaggio)
test("C07 …e dice anche la media", "Anche in media guadagni 0.57 s a giro." in c.messaggio, c.messaggio)
tratti = {t.curva: t for t in c.curve}
test("C08 i tratti sono quelli del motore per la sessione di oggi (7 curve)",
     sorted(tratti) == [x["numero"] for x in r_oggi.curve["curve"]] and len(tratti) == 7)
test("C09 la somma delle differenze per tratto è la differenza sul giro (±2 ms)",
     abs(sum(t.delta_ms for t in c.curve) - c.ritmo.delta_migliore_ms) <= 2,
     f"{sum(t.delta_ms for t in c.curve)}")
test("C10 la Roggia (curva 3) è dove si guadagna: circa 0.40 s",
     -420 <= tratti[3].delta_ms <= -380, f"{tratti[3].delta_ms}")
test("C11 la Lesmo 1 (curva 4) è dove si lascia qualcosa, sopra la soglia",
     SOGLIA_TRATTO_MS <= tratti[4].delta_ms <= 90, f"{tratti[4].delta_ms}")
test("C12 le altre curve non si muovono (sotto la soglia)",
     all(abs(t.delta_ms) < SOGLIA_TRATTO_MS for n, t in tratti.items() if n not in (3, 4)))
test("C13 il messaggio nomina il guadagno e la perdita",
     "Il grosso lo guadagni in curva 3: 0.40 s; in curva 4 ne lasci 0.06 s." in c.messaggio, c.messaggio)
test("C14 sulla demo le curve restano senza nome (la guida non si aggancia)",
     all(t.nome is None and t.mappa is None for t in c.curve))
test("C15 setup: due parametri, le pressioni posteriori, +4 click l'una",
     [(p.chiave, p.delta_click) for p in c.setup] == [("tire_press_rl", 4), ("tire_press_rr", 4)]
     and c.setup_confrontabile, f"{c.setup}")
test("C16 …dette con il valore del gioco, l'unità una volta sola",
     "Pressione Post.SX +4 click (24.7 → 25.1 psi)" in riga(c, "setup"), riga(c, "setup"))
ruote = {g.ruota: g for g in c.gomme}
test("C17 gomme: posteriori 0.4 psi più su, ancora sotto la finestra",
     ruote["RL"].pressione_prima == 25.0 and ruote["RL"].pressione == 25.4
     and ruote["RL"].stato == ruote["RL"].stato_prima == "bassa", f"{ruote['RL']}")
test("C18 gomme: la Post.DX da 108 a 105 °C, ancora oltre la finestra",
     ruote["RR"].temperatura_max_prima == 108 and ruote["RR"].temperatura_max == 105
     and ruote["RR"].stato == "calda" and "108 → 105 °C al core" in riga(c, "gomme"), riga(c, "gomme"))
test("C19 le anteriori, uguali e in finestra, non si nominano",
     "Ant." not in riga(c, "gomme"))
test("C20 la prova dice con chi è il confronto",
     c.prova[-1] == "confronto con la sessione del 14/07/2026 (demo)", c.prova[-1])
test("C21 il messaggio non attribuisce il tempo al setup",
     "click" not in c.messaggio and "pression" not in c.messaggio.lower())
test("C22 la volta prima è sempre la stessa (deterministica, in memoria)",
     demo_precedente.costruisci()[0] is prima)

# ---------------------------------------------------------------------------
# 2 · Al contrario, e contro sé stessa
# ---------------------------------------------------------------------------
print("\n─── Al contrario e contro sé stessa ───")
inv = confronta(prima, r_prima, canali_prima, oggi, r_oggi, canali_oggi, demo.DEMO_ID)
test("C23 al contrario risponde «No», più lento di 0.33 s",
     inv.messaggio.startswith("No: il giro migliore è 0.33 s più lento"), inv.messaggio)
test("C24 …e in media perde", "Anche in media perdi 0.57 s a giro." in inv.messaggio, inv.messaggio)
test("C25 …il grosso lo lascia alla curva 3 e ne riprende alla 4",
     "Il grosso lo lasci in curva 3: 0.40 s; in curva 4 ne riprendi 0.06 s." in inv.messaggio, inv.messaggio)
test("C26 …e i click hanno il segno opposto",
     [p.delta_click for p in inv.setup] == [-4, -4] and "−4 click (25.1 → 24.7 psi)" in riga(inv, "setup"))
stessa = confronta(oggi, r_oggi, canali_oggi, oggi, r_oggi, canali_oggi, demo.DEMO_ID)
test("C27 contro sé stessa: «Sei lì», nessuna curva, setup identico, gomme uguali",
     stessa.messaggio.startswith("Sei lì:") and "nessuna cambia" in riga(stessa, "curve")
     and riga(stessa, "setup") == "setup: identico alla volta prima"
     and riga(stessa, "gomme") == "gomme: pressioni e temperature come la volta prima", f"{stessa.prova}")

# ---------------------------------------------------------------------------
# 3 · Quello che manca non si inventa
# ---------------------------------------------------------------------------
print("\n─── Senza telemetria, senza setup ───")
a = sessione([108000, 107500, 107900])
b = sessione([108400, 108300, 108900])
ra, rb = analizza(a, None), analizza(b, None)
solo_tempi = confronta(a, ra, None, b, rb, None, "prima")
test("C28 senza canali il ritmo si confronta lo stesso",
     solo_tempi.ritmo.delta_migliore_ms == -800 and solo_tempi.messaggio.startswith("Sì:"), solo_tempi.messaggio)
test("C29 …curve, setup e gomme dicono che cosa manca, e dove",
     riga(solo_tempi, "curve") == "curve non confrontabili: manca la telemetria in tutte e due"
     and riga(solo_tempi, "setup") == "setup non confrontabile: manca in tutte e due"
     and riga(solo_tempi, "gomme").startswith("gomme non confrontabili")
     and not solo_tempi.curve and not solo_tempi.setup and not solo_tempi.gomme
     and not solo_tempi.setup_confrontabile and not solo_tempi.gomme_confrontabili, f"{solo_tempi.prova}")
meta_canali = confronta(oggi, r_oggi, canali_oggi, b, rb, None, "prima")
test("C30 canali solo oggi: lo dice («la volta prima»)",
     riga(meta_canali, "curve").endswith("manca la telemetria la volta prima")
     and riga(meta_canali, "setup") == "setup non confrontabile: manca la volta prima", f"{meta_canali.prova}")
uno = sessione([107000])
r_uno = analizza(uno, None)
un_giro = confronta(uno, r_uno, None, b, rb, None, "prima")
test("C31 con un giro solo la media non si confronta, e si dice perché",
     un_giro.ritmo.delta_media_ms is None and "ne servono almeno 2 per parte" in riga(un_giro, "media"),
     riga(un_giro, "media"))
vuota = sessione([None, None])
test("C32 senza un giro con il tempo: nessun confronto, con il motivo",
     confronta(vuota, analizza(vuota, None), None, b, rb, None, "prima").ritmo is None
     and "non c'è un giro con il tempo" in confronta(vuota, analizza(vuota, None), None, b, rb, None, "prima").motivo)

# ---------------------------------------------------------------------------
# 4 · Condizioni diverse: si confronta e si dichiara
# ---------------------------------------------------------------------------
print("\n─── Condizioni ───")


def con_pista(bundle: SessionBundle, gradi: float | None, aria: float | None = None) -> SessionBundle:
    copia = bundle.model_copy(deep=True)
    copia.meta.condizioni.temp_pista_c = gradi
    copia.meta.condizioni.temp_aria_c = aria
    return copia


def cfr(pista_oggi, pista_prima, aria_oggi=None, aria_prima=None):
    return confronta(con_pista(oggi, pista_oggi, aria_oggi), r_oggi, canali_oggi,
                     con_pista(prima, pista_prima, aria_prima), r_prima, canali_prima, "prima")


test("C33 temperatura della pista non registrata: lo dichiara e confronta le gomme",
     any("non registrata in nessuna delle due" in x for x in cfr(None, None).condizioni)
     and cfr(None, None).gomme_confrontabili)
test("C33b la demo e la sua volta prima hanno la stessa pista: niente da dichiarare", c.condizioni == [],
     f"{c.condizioni}")
test("C34 nota in una sola: «in una delle due»",
     any("non registrata in una delle due" in x for x in cfr(30, None).condizioni))
test("C35 2 °C di differenza: non si dichiara niente", cfr(30, 28).condizioni == [], f"{cfr(30, 28).condizioni}")
caldo = cfr(32, 28)
test("C36 4 °C: si dichiara («pista 4 °C più calda») e le gomme si confrontano",
     caldo.condizioni == ["pista 4 °C più calda della volta prima (32 contro 28 °C)"] and caldo.gomme_confrontabili,
     f"{caldo.condizioni}")
test("C37 5 °C giusti: le gomme si confrontano ancora", cfr(33, 28).gomme_confrontabili)
freddo = cfr(20, 28)
test("C38 8 °C: dichiarato («più fredda») e le gomme non si confrontano",
     "pista 8 °C più fredda" in freddo.condizioni[0] and not freddo.gomme_confrontabili and not freddo.gomme
     and riga(freddo, "gomme").startswith("gomme non confrontate: fra le due sessioni la pista cambia di 8 °C"),
     f"{freddo.prova}")
test("C39 …ma ritmo, curve e setup restano",
     freddo.ritmo.delta_migliore_ms == -330 and len(freddo.curve) == 7 and len(freddo.setup) == 2)
test("C40 anche l'aria si dichiara da 3 °C in su",
     "aria 5 °C più calda della volta prima" in cfr(30, 30, 25, 20).condizioni, f"{cfr(30, 30, 25, 20).condizioni}")
bagnata = prima.model_copy(deep=True)
bagnata.meta.mescola = Mescola.BAGNATO
r_bagnata = analizza(bagnata, canali_prima)
misto = confronta(oggi, r_oggi, canali_oggi, bagnata, r_bagnata, canali_prima, "prima")
test("C41 asciutto contro bagnato: nessun confronto, e lo dice",
     misto.ritmo is None and not misto.messaggio and not misto.prova
     and misto.motivo.startswith("Non le confronto: oggi eri sull'asciutto, la volta prima del 14/07/2026 sul bagnato."),
     f"{misto.motivo}")
rif_oggi, rif_prima = oggi.model_copy(deep=True), prima.model_copy(deep=True)
rif_oggi.meta.riferimento = rif_prima.meta.riferimento = True
rif_oggi.meta.fonte = rif_prima.meta.fonte = Fonte.MOTEC
fra_rif = confronta(rif_oggi, r_oggi, canali_oggi, rif_prima, r_prima, canali_prima, "prima")
test("C42 fra riferimenti: «della sessione precedente», e dichiara i piloti diversi",
     "più veloce della sessione precedente" in fra_rif.messaggio
     and "sessioni di riferimento: possono essere di piloti diversi" in fra_rif.condizioni
     and fra_rif.prova[-1].endswith("(riferimento)"), f"{fra_rif.messaggio} {fra_rif.condizioni}")

# ---------------------------------------------------------------------------
# 5 · Chi è «la precedente»
# ---------------------------------------------------------------------------
print("\n─── La precedente ───")


def voce(ident, quando, car="bmw_m4_gt3", track="monza", riferimento=False, demo_=False, migliore=107000,
         importato="2026-10-05T10:00:00+00:00"):
    return SimpleNamespace(id=ident, iniziata_il=quando, importato_il=importato, car=car, track=track,
                           riferimento=riferimento, demo=demo_, miglior_giro_ms=migliore)


elenco = [
    voce("ora", "2026-09-10T10:00:00"),
    voce("vicina", "2026-09-01T10:00:00+00:00"),
    voce("lontana", "2026-08-01T10:00:00"),
    voce("dopo", "2026-09-20T10:00:00"),
    voce("altra_pista", "2026-09-05T10:00:00", track="spa"),
    voce("altra_vettura", "2026-09-06T10:00:00", car="ferrari_488_gt3_evo"),
    voce("riferimento", "2026-09-07T10:00:00", riferimento=True),
    voce("riferimento_prima", "2026-09-02T10:00:00", riferimento=True),
    voce("demo", "2026-07-15T10:00:00", demo_=True),
    voce("senza_tempo", "2026-09-08T10:00:00", migliore=None),
]
test("C43 la più vicina prima, stessa pista e vettura (date con e senza fuso)",
     scegli_precedente(elenco, "ora").id == "vicina")
test("C44 non una sessione dopo, non un'altra pista o vettura, non una senza tempo",
     scegli_precedente(elenco, "vicina").id == "lontana")
test("C45 la prima di tutte non ha una precedente", scegli_precedente(elenco, "lontana") is None)
test("C46 i riferimenti solo con i riferimenti",
     scegli_precedente(elenco, "riferimento").id == "riferimento_prima"
     and scegli_precedente(elenco, "riferimento_prima") is None)
test("C47 la demo non passa dall'archivio", scegli_precedente(elenco, "demo") is None)
test("C48 senza data di inizio vale quella di import",
     scegli_precedente([voce("ora", None, importato="2026-10-05T10:00:00+00:00"),
                        voce("prima", None, importato="2026-10-01T10:00:00+00:00")], "ora").id == "prima")
test("C49 un id che non c'è, o una sessione senza pista: nessuna precedente",
     scegli_precedente(elenco, "boh") is None
     and scegli_precedente([voce("ora", "2026-09-10T10:00:00", track=None), elenco[1]], "ora") is None)

# ---------------------------------------------------------------------------
# 6 · La rotta
# ---------------------------------------------------------------------------
print("\n─── Rotta ───")
radice = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_confronto_"))
os.environ["PITWALL_SESSIONS_DIR"] = str(radice)
try:
    from datetime import datetime, timezone

    from fastapi.testclient import TestClient  # noqa: E402

    from app.bundle import store  # noqa: E402
    from app.main import app as fastapi_app  # noqa: E402

    client = TestClient(fastapi_app, raise_server_exceptions=False)
    demo.assicura_demo()
    resp = client.get(f"/api/sessions/{demo.DEMO_ID}/confronto")
    corpo = resp.json()
    test("C50 GET /confronto sulla demo: la volta prima generata, con messaggio e prova",
         resp.status_code == 200 and corpo["precedente"]["id"] == demo_precedente.ID
         and corpo["precedente"]["demo"] is True and corpo["messaggio"].startswith("Sì:")
         and len(corpo["prova"]) >= 5, resp.text[:300])
    elenco_api = client.get("/api/sessions").json()["sessioni"]
    test("C51 la volta prima non è in archivio: non compare nell'elenco e non scrive niente",
         demo_precedente.ID not in [s["id"] for s in elenco_api]
         and not (radice / f"{demo_precedente.ID}.json").exists()
         and not (radice / "telemetria" / demo_precedente.ID).exists())
    test("C52 la volta prima non si apre come sessione: 404",
         client.get(f"/api/sessions/{demo_precedente.ID}").status_code == 404)

    vecchia = sessione([108400, 108300, 108900], iniziata_il=datetime(2026, 9, 1, 10, tzinfo=timezone.utc))
    nuova = sessione([108000, 107500, 107900], iniziata_il=datetime(2026, 9, 10, 10, tzinfo=timezone.utc))
    id_vecchia, id_nuova = store.salva(vecchia, "20260901-100000-monza_bmw_m4_gt3-aaaa"), \
        store.salva(nuova, "20260910-100000-monza_bmw_m4_gt3-bbbb")
    corpo = client.get(f"/api/sessions/{id_nuova}/confronto").json()
    test("C53 due sessioni tue in archivio: la nuova si confronta con la vecchia",
         corpo["precedente"]["id"] == id_vecchia and corpo["precedente"]["giorno"] == "01/09/2026"
         and corpo["ritmo"]["delta_migliore_ms"] == -800, str(corpo)[:300])
    corpo = client.get(f"/api/sessions/{id_vecchia}/confronto").json()
    test("C54 la più vecchia non ha una precedente: `precedente` null e il motivo",
         corpo["precedente"] is None and "Non c'è una sessione precedente" in corpo["motivo"], str(corpo)[:200])
    test("C55 sessione che non c'è → 404",
         client.get("/api/sessions/20990101-000000-nessuna-0000/confronto").status_code == 404)
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
    print("✅ Confronto fra sessioni in ordine")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
