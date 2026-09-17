"""
test_motec_export.py — le sessioni di PitWall come file MoTeC (L5 · Fase 5)

MoTeC i2 non si può aprire qui. La compatibilità dell'impaginazione è provata a parte
sui file veri di ACC (`scripts/valida_motec.py`, sezione H: riscritti identici byte per
byte, 16 su 16). Questi test provano, offline, che cosa finisce nel file:

1. **Lo scrittore rifà l'impaginazione di ACC**: blocchi agli stessi indirizzi, costanti,
   unità nel campo da 8 byte, coda con massimo e minimo arrotondati e decimali.
2. **L'andata e ritorno torna**: la demo esportata e riletta ha gli stessi canali (nelle
   unità di ACC), gli stessi giri dai beacon e, reimportata, le stesse curve.
3. **I canali in più non fingono equivalenze**: FUEL, TYRE_CORE_TEMP, LAP_POSITION,
   STEER_INPUT, GEAR_SM.
4. **La rotta**: zip con .ld e .ldx per chi ha i canali, 409 per chi non li ha.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_motec_export.py
"""

import io
import os
import pathlib
import shutil
import struct
import sys
import tempfile
import zipfile
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

import numpy as np  # noqa: E402

from app.analisi import analizza  # noqa: E402
from app.bundle import demo  # noqa: E402
from app.bundle.adapters.motec import bundle_da_motec  # noqa: E402
from app.motec import leggi_ld, leggi_nome_file, registrazione_da_byte  # noqa: E402
from app.motec.esporta import esporta  # noqa: E402
from app.motec.scrittura import CanaleDaScrivere, scrivi_ld, scrivi_ldx  # noqa: E402

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


# ---------------------------------------------------------------------------
print("\n─── Scrittore ───")
# ---------------------------------------------------------------------------
quando = datetime(2023, 11, 28, 9, 57, 6)
velocita = np.array([16.4, 40.0, 75.5], dtype=np.float32)
ld = scrivi_ld([CanaleDaScrivere("LAP_BEACON", "..", 100, np.zeros(3)),
                CanaleDaScrivere("SPEED", "m/s", 60, velocita),
                CanaleDaScrivere("ROTY", "rad/s", 20, np.array([-0.9, 1.2]))],
               vettura="M4 GT3", pista="monza", data_ora=quando, peso_kg=1385)
test("X01 blocchi agli indirizzi di ACC (evento 1762, pista 4918, vettura 8020, canali 13384)",
     struct.unpack_from("<IIII", ld, 0)[0] == 0x40 and struct.unpack_from("<I", ld, 36)[0] == 1762
     and struct.unpack_from("<H", ld, 1762 + 1152)[0] == 4918
     and struct.unpack_from("<H", ld, 4918 + 1098)[0] == 8020
     and struct.unpack_from("<I", ld, 8)[0] == 13384)
test("X02 costanti dell'intestazione come nei file veri",
     ld[64:94].hex() == "020040420f00441f000041444c0000000000a401b0ad03000300640014000000"[:60]
     and struct.unpack_from("<I", ld, 1502)[0] == 0x000C81A4 and ld[1644] == 0x63
     and struct.unpack_from("<H", ld, 1762 + 1156)[0] == 0x2C48, ld[64:94].hex())
riletto = leggi_ld(ld)
speed = riletto.canale("SPEED")
test("X03 unità nel campo da 8 byte, riletta come unità", speed.unita == "m/s" and speed.nome_breve == "")
test("X04 coda: massimo e minimo arrotondati, decimali di SPEED (1) e limiti di ROTY (±100)",
     (speed.massimo_arrotondato, speed.minimo_arrotondato, speed.decimali_display) == (76, 16, 1)
     and (riletto.canale("ROTY").limite_alto, riletto.canale("ROTY").limite_basso) == (100.0, -100.0))
test("X05 conteggio canali e frequenze nell'intestazione (3, 3, 100, 20)",
     struct.unpack_from("<HHHH", ld, 86) == (3, 3, 100, 20) and riletto.avvertenze == [],
     f"{struct.unpack_from('<HHHH', ld, 86)} {riletto.avvertenze}")
test("X06 data, vettura, pista e peso riletti",
     riletto.data_ora == quando and (riletto.vettura, riletto.pista, riletto.peso_vettura) == ("M4 GT3", "monza", 1385))
ldx = scrivi_ldx([0.5, 110.0015], 109501, 1, primo_beacon=2).decode()
test("X07 .ldx: microsecondi interi, numerazione dal contatore di ACC, tre dettagli",
     'Name="2, id=99" Flags="13" Time="5.00000000000000000e+05"' in ldx
     and 'Time="1.10001500000000000e+08"' in ldx and 'Value="1:49.501"' in ldx
     and 'Id="Total Laps" Value="3"' in ldx, ldx)

# ---------------------------------------------------------------------------
print("\n─── Andata e ritorno sulla demo ───")
# ---------------------------------------------------------------------------
bundle, canali, _ = demo.costruisci()
e = esporta(bundle, canali)
test("X08 nome del file nel formato di ACC, rileggibile",
     (n := leggi_nome_file(e.nome_base + ".ld")) is not None and (n.pista, n.vettura) == ("monza", "bmw_m4_gt3"),
     e.nome_base)
reg = registrazione_da_byte(e.ld, e.ldx, e.nome_base + ".ld")
test("X09 il file si rilegge senza avvertenze, fino all'ultimo byte",
     reg.avvertenze == [] and max(c._puntatore_dati + c.campioni * 4 for c in reg.ld.canali) == len(e.ld),
     str(reg.avvertenze))
test("X10 canali nelle unità di ACC: SPEED in m/s, THROTTLE e BRAKE in %",
     np.allclose(reg.ld.canale("SPEED").valori() * 3.6, canali["physics.speedKmh"], atol=1e-3)
     and float(reg.ld.canale("THROTTLE").valori().max()) <= 100.0 + 1e-3
     and np.allclose(reg.ld.canale("BRAKE").valori() / 100, canali["physics.brake"], atol=1e-5))
test("X11 le ruote tornano LF/RF/LR/RR",
     np.allclose(reg.ld.canale("TYRE_PRESS_LR").valori(), canali["physics.wheelPressure.RL"], atol=1e-4))
test("X12 canali in più con nomi che non fingono equivalenze",
     {"FUEL", "LAP_POSITION", "STEER_INPUT", "GEAR_SM", "TYRE_CORE_TEMP_RR"} <= set(e.canali)
     and "GEAR" not in e.canali and "STEERANGLE" not in e.canali, str(e.canali))
tempi_demo = [g.tempo_ms for g in bundle.giri]
tempi_file = [round(t * 1000) for t in reg.ldx.tempi_giro_s]
test("X13 un beacon per ogni traguardo, bordi compresi: 8 giri con i tempi ufficiali al millesimo",
     len(tempi_file) == 8 and tempi_file == tempi_demo and reg.avvertenze == [],
     f"{tempi_demo} {tempi_file}")
test("X14 giro migliore dichiarato nel .ldx (1:47.820, quarto tratto)",
     reg.ldx.tempo_migliore == "1:47.820" and reg.ldx.giro_migliore == 4,
     f"{reg.ldx.tempo_migliore} {reg.ldx.giro_migliore}")
b2, c2, _ = bundle_da_motec(reg)
r2 = analizza(b2, c2)
r1 = analizza(bundle, canali)
test("X15 reimportata, la demo ha gli stessi giri e le stesse curve",
     len(b2.giri) == 8 and r2.curve is not None and len(r2.curve["curve"]) == len(r1.curve["curve"]),
     f"{[(g.numero, g.tempo_ms) for g in b2.giri]} {r2.dati_mancanti}")

# ---------------------------------------------------------------------------
print("\n─── Rotta ───")
# ---------------------------------------------------------------------------
radice = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_export_"))
os.environ["PITWALL_SESSIONS_DIR"] = str(radice)
try:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.bundle import store  # noqa: E402
    from app.bundle.schema import Fonte, Meta, SessionBundle  # noqa: E402
    from app.main import app as fastapi_app  # noqa: E402

    client = TestClient(fastapi_app, raise_server_exceptions=False)
    demo.assicura_demo()
    risposta = client.get(f"/api/sessions/{demo.DEMO_ID}/export/motec")
    nomi = []
    if risposta.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(risposta.content)) as z:
            nomi = z.namelist()
    test("X16 la rotta dà uno zip con .ld e .ldx, come allegato",
         risposta.status_code == 200 and risposta.headers["content-type"] == "application/zip"
         and "attachment" in risposta.headers.get("content-disposition", "")
         and sorted(p.rsplit(".", 1)[1] for p in nomi) == ["ld", "ldx"], f"{risposta.status_code} {nomi}")
    senza = store.salva(SessionBundle(meta=Meta(fonte=Fonte.MANUALE, car="bmw_m4_gt3", track="monza")))
    r409 = client.get(f"/api/sessions/{senza}/export/motec")
    test("X17 sessione senza canali → 409 con il motivo", r409.status_code == 409 and "canali" in r409.text, r409.text)
finally:
    shutil.rmtree(radice, ignore_errors=True)

# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]
print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Export MoTeC conforme")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
