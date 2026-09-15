"""
test_curve.py — analisi per curva sui canali (L3 · Fase 3)

Su un tracciato finto (`pista_finta.py`) si sa la risposta prima di chiedere: le curve
stanno dove le ho messe, e il giro storto è storto di quanto ho deciso io. Serve
esattamente a questo — su dati veri «sembra giusto» è tutto quello che si può dire.

Le cose che qui si vogliono inchiodare:
* i giri si ritagliano dalla posizione, e out lap / giri ai box restano fuori;
* le curve vengono trovate **dove sono**, e un'increspatura non diventa una curva;
* i tratti delle curve **coprono tutto il giro**: la somma dei tempi per tratto fa il
  tempo sul giro, quindi nessun decimo può sparire nelle crepe;
* la perdita finisce sulla curva giusta: 700 ms buttati nella curva 2 devono risultare
  nella curva 2, non spalmati;
* il verdetto è vuoto quando i giri sono identici (nessun falso allarme) e ogni voce
  porta con sé il numero che la prova e l'azione da fare.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_curve.py
"""

import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

import numpy as np  # noqa: E402

from app.analisi.curve import (  # noqa: E402
    CurveNonCalcolabili,
    analizza_curve,
    dividi_in_giri,
    lunghezza_stimata,
    su_distanza,
    trova_curve,
)
from app.tests.pista_finta import (  # noqa: E402
    CurvaFinta,
    GiroFinto,
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


def errore(fn) -> str | None:
    try:
        fn()
    except (ValueError, KeyError) as e:
        return str(e)
    return None


pista = pista_tre_curve()
buone = pista.curve
tre_giri_uguali = genera(pista, [GiroFinto(curve=buone) for _ in range(3)])

# ---------------------------------------------------------------------------
# 1 · I giri
# ---------------------------------------------------------------------------
print("\n─── Ritaglio dei giri ───")

giri = dividi_in_giri(tre_giri_uguali)
test("C01 trova tutti e tre i giri", len(giri) == 3, f"{len(giri)}")
test("C02 i giri sono numerati da 1", [g.numero for g in giri] == [1, 2, 3])
test("C03 sono tutti completi", all(g.completo for g in giri))
test("C04 i tempi sono uguali fra loro (giri identici)",
     len({g.tempo_ms for g in giri}) == 1, f"{[g.tempo_ms for g in giri]}")
test("C05 il tempo sul giro è quello atteso (~57,07 s)",
     abs(giri[0].tempo_ms - 57070) < 50, f"{giri[0].tempo_ms} ms")
test("C06 i campioni di un giro sono coerenti con 100 Hz",
     abs(giri[0].campioni - 5707) < 10, f"{giri[0].campioni}")

con_box = genera(pista, [GiroFinto(curve=buone),
                         GiroFinto(curve=buone, ai_box=True),
                         GiroFinto(curve=buone)])
giri_box = dividi_in_giri(con_box)
test("C07 un giro passato dai box viene marcato", giri_box[1].ai_box is True)
test("C08 …e gli altri no", not giri_box[0].ai_box and not giri_box[2].ai_box)

non_valido = genera(pista, [GiroFinto(curve=buone),
                            GiroFinto(curve=buone, valido=False),
                            GiroFinto(curve=buone)])
test("C09 un giro invalidato viene marcato",
     dividi_in_giri(non_valido)[1].valido is False)

# Un mezzo giro in coda non deve passare per giro intero.
mezzo = {k: v[: int(len(v) * 0.9)] for k, v in tre_giri_uguali.items()}
giri_mezzo = dividi_in_giri(mezzo)
test("C10 l'ultimo giro tagliato a metà non risulta completo",
     giri_mezzo[-1].completo is False, f"{giri_mezzo[-1]}")

# ---------------------------------------------------------------------------
# 2 · La griglia sulla distanza
# ---------------------------------------------------------------------------
print("\n─── Indicizzazione sulla distanza ───")

profilo = su_distanza(tre_giri_uguali, giri[0],
                      ["physics.speedKmh", "pitwall.tempo_ms"], punti=2000)
test("C11 il profilo ha un punto per ogni casella della griglia",
     len(profilo["physics.speedKmh"]) == 2000)
test("C12 il tempo lungo il giro cresce sempre",
     bool(np.all(np.diff(profilo["pitwall.tempo_ms"]) >= 0)))
test("C13 la velocità massima del profilo è quella del rettilineo",
     abs(profilo["physics.speedKmh"].max() - 220.0) < 1.0,
     f"{profilo['physics.speedKmh'].max():.1f}")
test("C14 la velocità minima è quella della curva più lenta",
     abs(profilo["physics.speedKmh"].min() - 70.0) < 2.0,
     f"{profilo['physics.speedKmh'].min():.1f}")

lunghezza = lunghezza_stimata(profilo, giri[0].tempo_ms)
test("C15 la lunghezza stimata del tracciato sta entro l'1% di quella vera",
     lunghezza is not None and abs(lunghezza - 3000.0) / 3000.0 < 0.01,
     f"{lunghezza}")
test("C16 senza tempo sul giro la lunghezza non viene inventata",
     lunghezza_stimata(profilo, None) is None)

# ---------------------------------------------------------------------------
# 3 · Le curve
# ---------------------------------------------------------------------------
print("\n─── Riconoscimento delle curve ───")

curve = trova_curve(profilo["physics.speedKmh"])
test("C17 trova tre curve, come quelle della pista", len(curve) == 3, f"{len(curve)}")
attesi = [600.0, 1500.0, 2400.0]
for curva, atteso in zip(curve, attesi):
    metri = curva.apice * 3000.0
    test(f"C18.{curva.numero} l'apice della curva {curva.numero} è al metro {atteso:.0f}",
         abs(metri - atteso) < 15.0, f"trovato {metri:.1f}")
test("C19 le velocità minime di riferimento sono quelle giuste",
     all(abs(c.velocita_minima_riferimento - v) < 5.0
         for c, v in zip(curve, [90.0, 120.0, 70.0])),
     f"{[round(c.velocita_minima_riferimento, 1) for c in curve]}")
test("C20 ingresso, apice e uscita sono in quest'ordine lungo il giro",
     all(0.0 <= c.ingresso <= 1.0 and 0.0 <= c.uscita <= 1.0 for c in curve))

piatto = np.full(2000, 180.0)
test("C21 un profilo piatto non produce curve inventate", trova_curve(piatto) == [])

increspato = np.full(2000, 180.0)
increspato[500:520] = 172.0          # 8 km/h: rumore, non una curva
test("C22 un'increspatura sotto soglia non diventa una curva",
     trova_curve(increspato) == [])

profondo = np.full(2000, 180.0)
profondo[500:560] = 140.0            # 40 km/h: questa è una curva
test("C23 un rallentamento vero invece sì", len(trova_curve(profondo)) == 1)

# Il caso che aveva rotto la prima versione: un curvone lungo a velocità costante.
# Con la profondità misurata in una finestra stretta spariva del tutto, perché dentro
# la finestra il profilo era piatto. Ora la profondità si misura camminando.
lungo = np.full(2000, 180.0)
lungo[400:700] = 140.0               # 300 campioni, il 15% del giro
curve_lunghe = trova_curve(lungo)
test("C23b una curva lunga a velocità costante viene riconosciuta",
     len(curve_lunghe) == 1, f"{len(curve_lunghe)}")
test("C23c …e il suo apice cade in mezzo al curvone, non a un estremo",
     0.26 < curve_lunghe[0].apice < 0.29 if curve_lunghe else False,
     f"{curve_lunghe[0].apice if curve_lunghe else '—'}")

# ---------------------------------------------------------------------------
# 4 · L'analisi completa: giri identici
# ---------------------------------------------------------------------------
print("\n─── Analisi su giri identici: nessun falso allarme ───")

uguale = analizza_curve(tre_giri_uguali)
test("C24 riconosce le tre curve", len(uguale.curve) == 3)
test("C25 il riferimento è uno dei giri", uguale.giro_di_riferimento in (1, 2, 3))
test("C26 con giri identici la perdita è praticamente zero",
     uguale.perdita_totale_ms < 5.0, f"{uguale.perdita_totale_ms} ms")
test("C27 …e il verdetto è vuoto: non si inventano problemi",
     uguale.verdetto == [], f"{[v.titolo for v in uguale.verdetto]}")

somma = sum(r.tempo_migliore_ms for r in uguale.riepilogo)
test("C28 i tratti coprono tutto il giro (somma dei tratti = tempo sul giro)",
     abs(somma - giri[0].tempo_ms) < 20.0,
     f"somma {somma:.0f} vs giro {giri[0].tempo_ms}")

# ---------------------------------------------------------------------------
# 5 · L'analisi completa: un giro storto in una curva sola
# ---------------------------------------------------------------------------
print("\n─── Analisi con un errore piazzato apposta ───")

storte = [buone[0],
          CurvaFinta(posizione_m=1500.0, velocita_minima_kmh=105.0, frenata_m=160.0),
          buone[2]]
misto = genera(pista, [GiroFinto(curve=buone), GiroFinto(curve=storte),
                       GiroFinto(curve=buone)])
r = analizza_curve(misto)

tempi = [g.tempo_ms for g in r.giri]
differenza = tempi[1] - tempi[0]
test("C29 il giro storto è più lento di ~700 ms", 650 < differenza < 750,
     f"{differenza} ms")

perdita_2 = next(x for x in r.dettaglio if x.curva == 2 and x.giro == 2).perdita_ms
test("C30 la perdita finisce sulla curva 2, quasi per intero",
     perdita_2 > differenza * 0.95, f"{perdita_2} su {differenza}")
altre = [x.perdita_ms for x in r.dettaglio if x.curva != 2]
test("C31 …e sulle altre curve non finisce niente", max(altre) < 5.0, f"{altre}")

dettaglio_2 = {x.giro: x for x in r.dettaglio if x.curva == 2}
test("C32 la v-min del giro storto è quella imposta (105 km/h)",
     abs(dettaglio_2[2].velocita_minima - 105.0) < 1.0,
     f"{dettaglio_2[2].velocita_minima}")
test("C33 la v-min degli altri giri è 120 km/h",
     abs(dettaglio_2[1].velocita_minima - 120.0) < 1.0,
     f"{dettaglio_2[1].velocita_minima}")
test("C34 il punto di frenata del giro buono è a 1380 m (apice 1500 − 120)",
     abs(dettaglio_2[1].punto_di_frenata_m - 1380.0) < 12.0,
     f"{dettaglio_2[1].punto_di_frenata_m}")
test("C35 quello del giro storto è 40 m prima, come impostato",
     abs(dettaglio_2[2].punto_di_frenata_m - 1340.0) < 12.0,
     f"{dettaglio_2[2].punto_di_frenata_m}")
test("C36 la riapertura del gas cade dopo l'apice",
     dettaglio_2[1].riapertura_gas > r.curve[1].apice - 0.01,
     f"{dettaglio_2[1].riapertura_gas} vs apice {r.curve[1].apice}")

riepilogo_2 = next(x for x in r.riepilogo if x.curva == 2)
test("C37 il riepilogo misura la dispersione del punto di frenata in metri",
     riepilogo_2.dispersione_frenata > 15.0, f"{riepilogo_2.dispersione_frenata}")
test("C38 …e quella della velocità minima in km/h",
     riepilogo_2.dispersione_vmin > 5.0, f"{riepilogo_2.dispersione_vmin}")
test("C39 il giro di riferimento è uno dei due buoni",
     r.giro_di_riferimento in (1, 3), f"{r.giro_di_riferimento}")

print("\n─── Verdetto ───")
test("C40 il verdetto non è vuoto", len(r.verdetto) > 0)
test("C41 la voce più grave è sulla curva 2", "curva 2" in r.verdetto[0].titolo,
     r.verdetto[0].titolo)
test("C42 la voce più grave cita i decimi persi",
     "0.2" in r.verdetto[0].titolo or "0.3" in r.verdetto[0].titolo,
     r.verdetto[0].titolo)
test("C43 ogni voce porta la prova numerica", all(v.prova for v in r.verdetto))
test("C44 ogni voce porta l'azione da fare", all(v.azione for v in r.verdetto))
test("C45 le voci sono ordinate per gravità",
     [v.gravita for v in r.verdetto] == list(range(1, len(r.verdetto) + 1)))
test("C46 il report si serializza in JSON senza perdere pezzi",
     set(r.come_json()) == {"giri", "curve", "riepilogo", "dettaglio", "verdetto",
                            "giro_di_riferimento", "perdita_totale_ms",
                            "lunghezza_stimata_m", "dati_mancanti"})

# ---------------------------------------------------------------------------
# 6 · Quando non si può dire niente, si dice
# ---------------------------------------------------------------------------
print("\n─── Rifiuti dichiarati ───")

msg = errore(lambda: analizza_curve({"physics.speedKmh": np.zeros(10)}))
test("C47 senza i canali indispensabili rifiuta, dicendo quali mancano",
     msg is not None and "mancanti" in msg, msg or "nessun errore")

un_giro = genera(pista, [GiroFinto(curve=buone)])
msg = errore(lambda: analizza_curve(un_giro))
test("C48 con un giro solo non si confronta niente, e lo dice",
     msg is not None and "2 giri" in msg, msg or "nessun errore")

senza_freno = {k: v for k, v in tre_giri_uguali.items() if k != "physics.brake"}
senza = analizza_curve(senza_freno)
test("C49 senza il canale del freno l'analisi continua…",
     len(senza.curve) == 3)
test("C50 …dichiarando che quelle misure non ci sono",
     any("freno" in d for d in senza.dati_mancanti), f"{senza.dati_mancanti}")
test("C51 …e senza inventare punti di frenata",
     all(d.punto_di_frenata is None for d in senza.dettaglio))

# ---------------------------------------------------------------------------
# 7 · La rotta, sopra una registrazione scritta su disco
# ---------------------------------------------------------------------------
print("\n─── Rotta /curve ───")

import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import tempfile  # noqa: E402

radice = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_curve_"))
os.environ["PITWALL_SESSIONS_DIR"] = str(radice)
try:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app as fastapi_app  # noqa: E402

    id_sessione = "20260915-120000-pista_finta-abcd"
    cartella = radice / "telemetria" / id_sessione
    cartella.mkdir(parents=True)
    colonne_f4 = [k for k, v in misto.items() if v.dtype == np.float32]
    colonne_i4 = [k for k, v in misto.items() if v.dtype == np.int32]
    np.savez_compressed(
        cartella / "canali.npz",
        f4=np.column_stack([misto[c] for c in colonne_f4]).astype(np.float32),
        i4=np.column_stack([misto[c] for c in colonne_i4]).astype(np.int32),
    )
    (cartella / "sessione.json").write_text(json.dumps({
        "id": id_sessione, "inizio": "2026-09-15T12:00:00+00:00",
        "fine": "2026-09-15T12:03:00+00:00", "vettura": "bmw_m4_gt3",
        "pista": "pista_finta", "frequenza_hz": 100.0, "campioni": len(misto[VEL := "physics.speedKmh"]),
        "attendibile": True, "assunzioni": [],
        "colonne": {"f4": colonne_f4, "i4": colonne_i4},
    }, ensure_ascii=False), encoding="utf-8")

    client = TestClient(fastapi_app, raise_server_exceptions=False)
    risposta = client.get(f"/api/telemetria/sessioni/{id_sessione}/curve")
    corpo = risposta.json()
    test("C52 la rotta risponde 200", risposta.status_code == 200, risposta.text[:150])
    test("C53 …con le tre curve e il verdetto",
         len(corpo["curve"]) == 3 and len(corpo["verdetto"]) > 0)
    test("C54 …e la voce più grave è ancora la curva 2",
         "curva 2" in corpo["verdetto"][0]["titolo"], corpo["verdetto"][0]["titolo"])
    test("C55 il dettaglio per giro non viaggia se non lo chiedi",
         "dettaglio" not in corpo)
    con_dettaglio = client.get(f"/api/telemetria/sessioni/{id_sessione}/curve",
                               params={"dettaglio": "true"}).json()
    test("C56 …e arriva quando lo chiedi",
         len(con_dettaglio["dettaglio"]) == 9)   # 3 curve × 3 giri

    # Una registrazione che non permette l'analisi: si spiega, non si esplode.
    corto = radice / "telemetria" / "20260915-120500-corta-beef"
    corto.mkdir(parents=True)
    un_giro_solo = genera(pista, [GiroFinto(curve=buone)])
    f4 = [k for k, v in un_giro_solo.items() if v.dtype == np.float32]
    i4 = [k for k, v in un_giro_solo.items() if v.dtype == np.int32]
    np.savez_compressed(
        corto / "canali.npz",
        f4=np.column_stack([un_giro_solo[c] for c in f4]).astype(np.float32),
        i4=np.column_stack([un_giro_solo[c] for c in i4]).astype(np.int32),
    )
    (corto / "sessione.json").write_text(json.dumps({
        "id": corto.name, "colonne": {"f4": f4, "i4": i4}, "campioni": 1,
    }), encoding="utf-8")
    breve = client.get(f"/api/telemetria/sessioni/{corto.name}/curve")
    test("C57 una sessione con un giro solo dà 422, non 500",
         breve.status_code == 422, f"{breve.status_code} {breve.text[:100]}")
    test("C58 …e la risposta dice perché", "2 giri" in breve.text, breve.text[:120])
finally:
    os.environ.pop("PITWALL_SESSIONS_DIR", None)
    shutil.rmtree(radice, ignore_errors=True)

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Analisi per curva conforme")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
