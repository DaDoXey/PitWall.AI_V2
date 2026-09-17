"""
test_motec_bundle.py — da un file MoTeC di ACC a una sessione dell'archivio (L5 · Fase 2)

Il lettore (F1) dice che cosa c'è nel file; qui si prova che cosa ne fa PitWall:

1. **Canali canonici solo dove il significato coincide.** Velocità, pedali, pressioni,
   freni, sospensioni prendono il nome della shared memory con l'unità convertita;
   sterzo in gradi, marcia e `TYRE_TAIR` restano `motec.*`. `TIME`, `LAP_BEACON` e
   `CLUTCH` non si portano.
2. **Posizione ricavata, giri dai beacon.** La distanza si integra dalla velocità e si
   azzera a ogni traguardo; i tempi sul giro sono quelli del `.ldx`, al millisecondo.
   Senza traguardi, nessun giro inventato — salvo il ritaglio di MoTeC i2 lungo
   quanto la pista.
3. **Il consumo compare sempre con la sua fonte**: manuale prima del setup, e senza
   nessuno dei due lo si dice.
4. **Le rotte**: import, analisi, cancellazione (che porta via anche i canali), errori
   dichiarati.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_motec_bundle.py

Non richiede pytest, né rete, né i file veri.
"""

import json
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

import numpy as np  # noqa: E402

from app.analisi import analizza  # noqa: E402
from app.bundle.adapters import leggi_setup_acc  # noqa: E402
from app.bundle.adapters.motec import (  # noqa: E402
    CarburanteManuale,
    MotecNonConvertibile,
    bundle_da_motec,
)
from app.bundle.schema import SCHEMA_VERSION, Fonte, Mescola, SessionBundle  # noqa: E402
from app.motec import registrazione_da_byte  # noqa: E402
from app.tests.motec_finto import CanaleFinto, scrivi_ld, scrivi_ldx  # noqa: E402

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


FIXTURES = pathlib.Path(__file__).parent / "fixtures"
SETUP = leggi_setup_acc((FIXTURES / "acc_setup_gt3.json").read_bytes())
NOME = "monza-bmw_m4_gt3-5-2023.06.30-15.58.56.ld"

# ── uno stint finto: 1 s di uscita, 3 giri da 60 s, 2 s di rientro ─────────────
# Velocità con tre «curve» per giro, così l'analisi per curva ha qualcosa da trovare.
GIRO_S, USCITA_S, RIENTRO_S = 60.0, 1.0, 2.0
DURATA = USCITA_S + 3 * GIRO_S + RIENTRO_S


def profilo(t: np.ndarray, rallenta: float = 0.0) -> np.ndarray:
    fase = ((t - USCITA_S) % GIRO_S) / GIRO_S
    v = np.full_like(t, 60.0)
    for centro in (0.2, 0.5, 0.8):
        v -= (35.0 + rallenta) * np.exp(-((fase - centro) / 0.03) ** 2)
    return v


def stint(beacon=True, durata=DURATA, extra=None) -> tuple[bytes, bytes | None]:
    t60 = np.arange(int(durata * 60)) / 60
    t20 = np.arange(int(durata * 20)) / 20
    t200 = np.arange(int(durata * 200)) / 200
    canali = [
        CanaleFinto("LAP_BEACON", "..", 100, np.zeros(int(durata * 100), np.float32)),
        CanaleFinto("SPEED", "m/s", 60, profilo(t60).astype(np.float32)),
        CanaleFinto("THROTTLE", "%", 60, np.full(t60.size, 80.0, np.float32)),
        CanaleFinto("BRAKE", "%", 60, np.where(profilo(t60) < 40, 100.0, 0.0).astype(np.float32)),
        CanaleFinto("STEERANGLE", "deg", 60, np.full(t60.size, -12.5, np.float32)),
        CanaleFinto("GEAR", "no", 20, np.where(profilo(t20) < 40, 2.0, 5.0).astype(np.float32)),
        CanaleFinto("CLUTCH", "%", 60, np.zeros(t60.size, np.float32)),
        CanaleFinto("SUS_TRAVEL_LF", "mm", 200, np.full(t200.size, 30.0, np.float32)),
        CanaleFinto("TIME", "..", 50, (np.arange(int(durata * 50)) / 50 % 37).astype(np.float32)),
    ]
    for ruota, psi, tair in (("LF", 26.4, 80.0), ("RF", 26.6, 78.0), ("LR", 26.5, 83.0),
                             ("RR", 26.7, 79.0)):
        canali.append(CanaleFinto(f"TYRE_PRESS_{ruota}", "..", 20, np.full(t20.size, psi, np.float32)))
        canali.append(CanaleFinto(f"BRAKE_TEMP_{ruota}", "C", 20, np.full(t20.size, 450.0, np.float32)))
        canali.append(CanaleFinto(f"TYRE_TAIR_{ruota}", "C", 20, np.full(t20.size, tair, np.float32)))
    canali.extend(extra or [])
    ld = scrivi_ld(canali, vettura="M4 GT3", pista="monza")
    beacon_s = [USCITA_S + k * GIRO_S for k in range(4)]
    return ld, (scrivi_ldx(beacon_s) if beacon else scrivi_ldx([]))


LD, LDX = stint()
reg = registrazione_da_byte(LD, LDX, NOME)
bundle, canali, metadati = bundle_da_motec(reg, nome_file=NOME)

# ---------------------------------------------------------------------------
print("\n─── Canali ───")
# ---------------------------------------------------------------------------
test("F01 vettura e pista dal nome del file, risolte sul catalogo",
     (bundle.meta.car, bundle.meta.track) == ("bmw_m4_gt3", "monza"),
     f"{bundle.meta.car} {bundle.meta.track}")
test("F02 fonte motec, piattaforma PC, riferimento per default",
     bundle.meta.fonte == Fonte.MOTEC and bundle.meta.piattaforma.value == "pc"
     and bundle.meta.riferimento is True)
v = canali["physics.speedKmh"]
test("F03 velocità m/s → km/h sulla griglia a 100 Hz",
     v.size == int(DURATA * 100) and abs(float(v.max()) - 216.0) < 0.5, f"{v.size} {v.max()}")
test("F04 pedali % → 0-1, sospensioni mm → m, pressioni in psi",
     abs(float(canali["physics.gas"].mean()) - 0.8) < 1e-5
     # il pedale si interpola: fra 0 e 1, con i valori intermedi delle transizioni
     and float(canali["physics.brake"].min()) == 0.0 and float(canali["physics.brake"].max()) == 1.0
     and abs(float(canali["physics.suspensionTravel.FL"][0]) - 0.030) < 1e-6
     and abs(float(canali["physics.wheelPressure.RL"][0]) - 26.5) < 1e-5)
test("F05 ruote MoTeC LF/RF/LR/RR → FL/FR/RL/RR",
     abs(float(canali["physics.wheelPressure.FR"][0]) - 26.6) < 1e-5
     and abs(float(canali["physics.brakeTemp.RR"][0]) - 450.0) < 1e-3)
test("F06 sterzo in gradi, marcia e TYRE_TAIR restano motec.* (significato diverso)",
     "motec.STEERANGLE" in canali and "physics.steerAngle" not in canali
     and "motec.GEAR" in canali and "motec.TYRE_TAIR_LF" in canali
     and "physics.tyreCoreTemp.FL" not in canali)
test("F07 la marcia si ricampiona a gradini: solo valori interi del file",
     canali["motec.GEAR"].dtype == np.int32 and set(np.unique(canali["motec.GEAR"])) <= {2, 5})
test("F08 TIME, LAP_BEACON e CLUTCH non si portano",
     not any(k in canali for k in ("motec.TIME", "motec.LAP_BEACON", "motec.CLUTCH")))
test("F09 colonne del sessione.json = canali, divise per tipo",
     sorted(metadati["colonne"]["f4"] + metadati["colonne"]["i4"]) == sorted(canali)
     and metadati["riferimento"] is True and metadati["campioni"] == v.size)

# ---------------------------------------------------------------------------
print("\n─── Giri e posizione ───")
# ---------------------------------------------------------------------------
completi = [g for g in bundle.giri if g.valido]
test("F10 tre giri completi, tempi dal .ldx al millisecondo",
     [g.tempo_ms for g in completi] == [60000, 60000, 60000], f"{[(g.numero, g.tempo_ms) for g in bundle.giri]}")
test("F11 uscita e rientro contati ma non completi",
     len(bundle.giri) == 5 and [g.valido for g in bundle.giri] == [False, True, True, True, False],
     f"{[(g.numero, g.valido) for g in bundle.giri]}")
pos = canali["graphics.normalizedCarPosition"]
i0, i1 = int(USCITA_S * 100), int((USCITA_S + GIRO_S) * 100)
giro_pos = pos[i0:i1]
test("F12 dentro un giro la posizione va da 0 a ~1 e non torna mai indietro",
     giro_pos[0] == 0.0 and giro_pos[-1] > 0.99 and bool(np.all(np.diff(giro_pos) >= 0)))
test("F13 i tratti senza traguardo di chiusura restano sotto la soglia di giro completo",
     float(pos[-150:].max()) <= 0.94 and float(pos[:100].min()) >= 0.06)
test("F14 la posizione ricavata è dichiarata nelle assunzioni",
     any("posizione in pista ricavata" in a for a in bundle.assunzioni))

report = analizza(bundle, canali)
test("F14b uscita e rientro non sono «giri buttati» (validazione L5)",
     report.giri_buttati == 0 and not any("buttat" in v.titolo for v in report.verdetto),
     f"{report.giri_buttati} {[v.titolo for v in report.verdetto]}")
test("F15 l'analisi per curva gira sui canali MoTeC (3 curve per giro)",
     report.curve is not None and len(report.curve["curve"]) == 3,
     f"{(report.curve or {}).get('curve')} {report.dati_mancanti}")
gomme = report.gomme_e_freni["gomme"]
test("F16 TYRE_TAIR mostrata a parte, mai come temperatura al core",
     gomme["temperatura_media"]["FL"] is None
     and gomme["temperatura_motec_media"] == {"FL": 80.0, "FR": 78.0, "RL": 83.0, "RR": 79.0}
     and gomme["finestra_temperatura"] is None, f"{gomme}")

ld_no, ldx_no = stint(beacon=False)
try:
    bundle_da_motec(registrazione_da_byte(ld_no, ldx_no, NOME))
    esito = "nessun errore"
except MotecNonConvertibile as e:
    esito = str(e)
test("F17 niente traguardi e niente ritaglio → errore, nessun giro inventato",
     "nessun passaggio sul traguardo" in esito, esito)
try:
    bundle_da_motec(registrazione_da_byte(LD, None, NOME))
    esito = "nessun errore"
except MotecNonConvertibile as e:
    esito = str(e)
test("F18 senza .ldx → stesso errore dichiarato", "nessun passaggio sul traguardo" in esito, esito)

# ── il ritaglio di MoTeC i2: un giro lungo quanto Monza, canali «lunghi» a parte ──
MONZA_M = 5793.0


def ritaglio(metri: float) -> bytes:
    durata = 100.0
    velocita = np.full(int(durata * 60), metri / durata, np.float32)
    lungo = CanaleFinto("EN_W", "..", 50, np.full(50 * 900, 1210.0, np.float32))  # 900 s
    return scrivi_ld([CanaleFinto("SPEED", "m/s", 60, velocita),
                      CanaleFinto("TYRE_PRESS_LF", "..", 20, np.full(2000, 26.5, np.float32)),
                      lungo])


ldx_i2 = (b'<?xml version="1.0"?><LDXFile Locale="English_Australia.1252" DefaultLocale="C" '
          b'Version="1.6"><Layers><Layer LayerName=""><MarkerBlock><MarkerGroup Name="Beacons">'
          b'</MarkerGroup></MarkerBlock></Layer></Layers></LDXFile>')
b_i2, c_i2, _ = bundle_da_motec(registrazione_da_byte(ritaglio(MONZA_M * 0.99), ldx_i2, NOME))
test("F19 ritaglio di MoTeC i2 lungo quanto la pista → un giro, tempo = durata",
     [(g.tempo_ms, g.valido) for g in b_i2.giri] == [(100000, True)]
     and any("MoTeC i2" in a for a in b_i2.assunzioni), f"{b_i2.giri} {b_i2.assunzioni}")
test("F19b il ritaglio i2 è marcato nel bundle (confronto meno preciso)",
     b_i2.meta.ritaglio_i2 is True and bundle.meta.ritaglio_i2 is False)
test("F20 …e i canali più lunghi del ritaglio sono esclusi e dichiarati",
     "motec.EN_W" not in c_i2 and any("EN_W" in a for a in b_i2.assunzioni))
try:
    bundle_da_motec(registrazione_da_byte(ritaglio(MONZA_M * 0.8), ldx_i2, NOME))
    esito = "nessun errore"
except MotecNonConvertibile as e:
    esito = str(e)
test("F21 ritaglio più corto della pista del 20% → non è un giro intero", "non è un giro intero" in esito,
     esito)
b_35, _, _ = bundle_da_motec(registrazione_da_byte(ritaglio(MONZA_M * 0.965), ldx_i2, NOME))
try:
    bundle_da_motec(registrazione_da_byte(ritaglio(MONZA_M * 0.95), ldx_i2, NOME))
    esito = "nessun errore"
except MotecNonConvertibile as e:
    esito = str(e)
test("F21b tolleranza del ritaglio al 4%: −3,5% è un giro, −5% no",
     len(b_35.giri) == 1 and "non è un giro intero" in esito, esito)

# ---------------------------------------------------------------------------
print("\n─── Carburante e mescola ───")
# ---------------------------------------------------------------------------
test("F22 senza litri né setup: consumo non calcolabile, e lo si dice",
     bundle.carburante_fonte is None and not report.carburante.calcolabile
     and any("MoTeC non esporta il carburante" in a for a in bundle.assunzioni))

b_man, c_man, _ = bundle_da_motec(reg, carburante=CarburanteManuale(40.0, 30.0), setup=SETUP)
usati = [g.carburante_usato_l for g in b_man.giri if g.valido]
r_man = analizza(b_man, c_man)
test("F23 manuale: 10 l ripartiti sulla distanza, 60/183 della registrazione per giro",
     all(abs(u - 10.0 * 60 / DURATA) < 0.02 for u in usati), f"{usati}")
test("F24 il manuale vale più del setup, e la fonte arriva nel report",
     b_man.carburante_fonte.value == "manuale" and r_man.carburante.fonte == "manuale"
     and r_man.carburante.calcolabile)
b_set, c_set, _ = bundle_da_motec(reg, setup=SETUP)
r_set = analizza(b_set, c_set)
test("F25 dal setup: fuelPerLap su ogni giro completo, fonte «setup»",
     [g.carburante_usato_l for g in b_set.giri if g.valido] == [3.6, 3.6, 3.6]
     and r_set.carburante.fonte == "setup" and r_set.carburante.consumo_medio_l_giro == 3.6)
try:
    bundle_da_motec(reg, carburante=CarburanteManuale(20.0, 25.0))
    esito = "nessun errore"
except MotecNonConvertibile as e:
    esito = str(e)
test("F26 più litri alla fine che all'inizio → errore, non un consumo negativo", "consumo" in esito, esito)
test("F27 mescola dal setup (tyreCompound 0 = asciutto)", b_set.meta.mescola == Mescola.ASCIUTTO)
b_bag, _, _ = bundle_da_motec(reg, setup=SETUP, mescola=Mescola.BAGNATO)
test("F28 la mescola indicata vale più di quella del setup", b_bag.meta.mescola == Mescola.BAGNATO)
test("F29 con mescola asciutto la pressione si giudica, la TYRE_TAIR no",
     r_set.gomme_e_freni["gomme"]["finestra_pressione"] is not None
     and r_set.gomme_e_freni["gomme"]["finestra_temperatura"] is None)

# ---------------------------------------------------------------------------
print("\n─── Schema ───")
# ---------------------------------------------------------------------------
test("F30 schema 1.2, e il bundle si rilegge identico",
     SCHEMA_VERSION == "1.2"
     and SessionBundle.from_json(b_man.to_json()).model_dump() == b_man.model_dump())
vecchio = json.loads(b_set.to_json())
vecchio["schema_version"] = "1.1"
vecchio.pop("carburante_fonte")
vecchio["meta"].pop("riferimento")
riletto = SessionBundle.from_json(json.dumps(vecchio))
test("F31 un bundle 1.1 (senza i campi nuovi) si legge ancora",
     riletto.meta.riferimento is False and riletto.carburante_fonte is None)

# ---------------------------------------------------------------------------
print("\n─── Rotte ───")
# ---------------------------------------------------------------------------
radice = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_motec_api_"))
os.environ["PITWALL_SESSIONS_DIR"] = str(radice)
try:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app as fastapi_app  # noqa: E402
    from app.telemetria import registratore  # noqa: E402

    client = TestClient(fastapi_app, raise_server_exceptions=False)
    risposta = client.post(
        "/api/sessions/import/motec",
        files={"ld": (NOME, LD, "application/octet-stream"),
               "ldx": (NOME + "x", LDX, "application/xml"),
               "setup": ("setup.json", (FIXTURES / "acc_setup_gt3.json").read_bytes(),
                         "application/json")},
        data={"carburante_inizio_l": "40", "carburante_fine_l": "30"},
    )
    corpo = risposta.json() if risposta.status_code == 200 else {}
    test("F32 import: 200, 5 giri di cui 3 con tempo, riassunto «riferimento»",
         risposta.status_code == 200 and corpo["giri"] == 5 and corpo["giri_con_tempo"] == 3
         and corpo["riassunto"]["riferimento"] is True and corpo["riassunto"]["fonte"] == "motec",
         risposta.text[:300])
    cartella = registratore.cartella_telemetria() / corpo.get("id_registrazione", "x")
    test("F33 i canali stanno nella cartella della telemetria, nel formato del registratore",
         (cartella / "canali.npz").exists() and (cartella / "sessione.json").exists()
         and len(registratore.leggi_canali(cartella)) == len(canali))
    analisi = client.get(f"/api/sessions/{corpo.get('id')}/analisi")
    dati = analisi.json() if analisi.status_code == 200 else {}
    test("F34 l'analisi passa dalla stessa rotta: canali, curve e consumo manuale",
         analisi.status_code == 200 and dati["ha_canali"] is True and dati["curve"] is not None
         and dati["carburante"]["fonte"] == "manuale", analisi.text[:300])
    test("F35 un riferimento non conta nel tetto dell'archivio",
         registratore._e_demo(cartella) is True)
    tracce = client.get(f"/api/sessions/{corpo.get('id')}/tracce",
                        params={"giri": "2,3", "canali": "physics.speedKmh,pitwall.tempo_ms", "punti": 200})
    dt = tracce.json()["giri"][0]["canali"]["pitwall.tempo_ms"] if tracce.status_code == 200 else []
    test("F35b tracce con il tempo sulla distanza (per il delta fra giri)",
         tracce.status_code == 200 and len(dt) == 200 and dt[-1] - dt[0] > 59000, tracce.text[:200])
    elenco_reg = client.get("/api/telemetria/sessioni").json()["sessioni"]
    reimporta = client.post(f"/api/telemetria/sessioni/{corpo.get('id_registrazione')}/importa")
    test("F35c la conversione MoTeC non compare fra le registrazioni da importare, e non si reimporta",
         all(r["id"] != corpo.get("id_registrazione") for r in elenco_reg) and reimporta.status_code == 409,
         f"{[r['id'] for r in elenco_reg]} {reimporta.status_code}")
    cancellata = client.delete(f"/api/sessions/{corpo.get('id')}")
    test("F36 cancellare la sessione porta via anche i suoi canali",
         cancellata.status_code == 200 and not cartella.exists())

    solo_inizio = client.post("/api/sessions/import/motec",
                              files={"ld": (NOME, LD), "ldx": (NOME + "x", LDX)},
                              data={"carburante_inizio_l": "40"})
    test("F37 litri solo a inizio → 400", solo_inizio.status_code == 400, solo_inizio.text)
    sbagliato = client.post("/api/sessions/import/motec", files={"ld": ("giro.csv", LD)})
    test("F38 estensione sbagliata → 400", sbagliato.status_code == 400, sbagliato.text)
    rotto = client.post("/api/sessions/import/motec", files={"ld": (NOME, LD[:500])})
    test("F39 .ld rotto → 400 con il motivo", rotto.status_code == 400
         and "intestazione" in rotto.json()["detail"], rotto.text)
    senza_giri = client.post("/api/sessions/import/motec",
                             files={"ld": (NOME, ld_no), "ldx": (NOME + "x", ldx_no)})
    test("F40 nessun traguardo → 422, niente canali orfani sul disco",
         senza_giri.status_code == 422
         and not any(p.name.endswith("monza-bmw_m4_gt3") or "monza" in p.name
                     for p in registratore.cartella_telemetria().iterdir()
                     if p.is_dir() and not p.name.startswith("DEMO")
                     and (p / "sessione.json").exists()
                     and json.loads((p / "sessione.json").read_text(encoding="utf-8")).get("fonte") == "motec"),
         senza_giri.text)
finally:
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
    print("✅ Import MoTeC conforme")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
