"""
test_telemetria_bundle.py — la registrazione diventa un session bundle (L3 · Fase 4)

È il test che dice se il rework ha mantenuto la sua promessa: un file di risultati e
una sessione registrata devono diventare **lo stesso documento**, e il motore di
analisi deve produrre **un solo verdetto** — non un cruscotto con due elenchi.

Quello che si vuole inchiodare:
* il bundle prende il tempo sul giro **ufficiale di ACC**, non il nostro cronometro,
  e dichiara se i due divergono;
* il **consumo vero** per giro c'è (dai risultati di ACC non si poteva ricavare);
* i canali non finiscono dentro il bundle: ci finisce il loro indirizzo;
* con i canali il report cresce (curve, gomme, freni) e le loro voci entrano nello
  stesso verdetto, ordinate per gravità insieme alle altre;
* senza canali il motore di L2 continua a funzionare esattamente come prima.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_telemetria_bundle.py
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
from app.analisi.gomme import analizza_gomme_e_freni  # noqa: E402
from app.bundle.adapters.acc_telemetria import (  # noqa: E402
    TelemetriaNonConvertibile,
    bundle_da_canali,
)
from app.bundle.schema import Fonte, TipoSessione  # noqa: E402
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
storte = [buone[0],
          CurvaFinta(posizione_m=1500.0, velocita_minima_kmh=105.0, frenata_m=160.0),
          buone[2]]

canali = genera(
    pista,
    [GiroFinto(curve=buone), GiroFinto(curve=storte), GiroFinto(curve=buone),
     GiroFinto(curve=buone)],
    completo=True, consumo_per_giro_l=2.5,
    squilibrio_pressione_psi=0.4, crescita_pressione_psi_giro=0.12,
)
metadati = {
    "id": "20260915-140000-pista_finta-aaaa", "vettura": "bmw_m4_gt3",
    "pista": "pista_finta", "pilota": "Edoardo Ferlito",
    "tipo_sessione": "PRACTICE", "frequenza_hz": 100.0, "assunzioni": [],
}

# ---------------------------------------------------------------------------
# 1 · Dalla registrazione al bundle
# ---------------------------------------------------------------------------
print("\n─── Il bundle di una sessione registrata ───")

bundle = bundle_da_canali(canali, metadati)

test("B01 la fonte dice che viene dalla shared memory",
     bundle.meta.fonte is Fonte.ACC_SHARED_MEMORY)
test("B02 vettura, pista e pilota arrivano dai metadati",
     bundle.meta.car == "bmw_m4_gt3" and bundle.meta.track == "pista_finta"
     and bundle.meta.pilota == "Edoardo Ferlito")
test("B03 il tipo di sessione diventa quello del bundle",
     bundle.meta.tipo_sessione is TipoSessione.PROVE)
test("B04 ci sono quattro giri", len(bundle.giri) == 4, f"{len(bundle.giri)}")
test("B05 i tempi sul giro ci sono", all(g.tempo_ms for g in bundle.giri),
     f"{[g.tempo_ms for g in bundle.giri]}")
test("B06 il tempo viene da ACC (`iLastTime`), non dal nostro cronometro",
     bundle.giri[0].tempo_ms == 57080, f"{bundle.giri[0].tempo_ms}")
test("B07 il giro storto è il più lento",
     max(bundle.giri, key=lambda g: g.tempo_ms).numero == 2,
     f"{[(g.numero, g.tempo_ms) for g in bundle.giri]}")

test("B08 il consumo per giro c'è, ed è quello vero (2,5 l)",
     all(abs((g.carburante_usato_l or 0) - 2.5) < 0.05 for g in bundle.giri),
     f"{[g.carburante_usato_l for g in bundle.giri]}")
test("B09 …e il residuo scende di giro in giro",
     [round(g.carburante_residuo_l, 1) for g in bundle.giri]
     == sorted([round(g.carburante_residuo_l, 1) for g in bundle.giri], reverse=True),
     f"{[g.carburante_residuo_l for g in bundle.giri]}")
test("B10 il set di gomme viene registrato", bundle.giri[0].set_gomme == 1)

test("B11 i canali NON finiscono dentro il bundle: ci finisce il loro indirizzo",
     bundle.canali is not None and bundle.canali.file.endswith("canali.npz"))
test("B12 il riferimento dichiara frequenza, numero di canali e campioni",
     bundle.canali.frequenza_hz == 100.0
     and len(bundle.canali.nomi) == len(canali)
     and bundle.canali.campioni == len(canali["pitwall.tempo_ms"]))
test("B13 la durata della sessione è dichiarata",
     bundle.meta.durata_s and bundle.meta.durata_s > 200,
     f"{bundle.meta.durata_s}")
test("B14 le condizioni arrivano dai canali",
     abs(bundle.meta.condizioni.temp_aria_c - 24.0) < 0.1
     and abs(bundle.meta.condizioni.temp_pista_c - 31.0) < 0.1,
     f"{bundle.meta.condizioni}")
test("B15 pista asciutta riconosciuta come tale",
     bundle.meta.condizioni.pioggia == 0.0)
test("B16 il bundle sopravvive a salvataggio e rilettura",
     type(bundle).from_json(bundle.to_json()).giri[1].tempo_ms
     == bundle.giri[1].tempo_ms)

# Giro a metà: nessun tempo inventato.
tagliato = {k: v[: int(len(v) * 0.85)] for k, v in canali.items()}
bundle_tagliato = bundle_da_canali(tagliato, metadati)
test("B17 un giro incompleto resta contato ma senza tempo",
     bundle_tagliato.giri[-1].tempo_ms is None
     and len(bundle_tagliato.giri) == 4,
     f"{[(g.numero, g.tempo_ms) for g in bundle_tagliato.giri]}")
test("B18 …e la cosa è dichiarata nelle assunzioni",
     any("incompleti" in a for a in bundle_tagliato.assunzioni),
     f"{bundle_tagliato.assunzioni}")

senza_carburante = {k: v for k, v in canali.items() if k != "physics.fuel"}
test("B19 senza il canale del carburante lo dichiara invece di stimare",
     any("carburante" in a for a in
         bundle_da_canali(senza_carburante, metadati).assunzioni))

msg = errore(lambda: bundle_da_canali({"physics.speedKmh": np.zeros(5)}, metadati))
test("B20 senza posizione e tempo non si costruisce niente, e si dice perché",
     msg is not None and "servono almeno" in msg, msg or "nessun errore")

# ---------------------------------------------------------------------------
# 2 · Gomme e freni
# ---------------------------------------------------------------------------
print("\n─── Gomme e freni dai canali ───")

report_gomme = analizza_gomme_e_freni(canali)
g = report_gomme.gomme
test("B21 le pressioni medie per ruota ci sono",
     g is not None and all(v is not None for v in g.pressione_media.come_lista()))
test("B22 lo squilibrio sinistra-destra è quello imposto (0,4 psi)",
     abs(g.squilibrio_sx_dx_psi - 0.4) < 0.06, f"{g.squilibrio_sx_dx_psi}")
from app.analisi.curve import dividi_in_giri  # noqa: E402
from app.analisi.gomme import indice_giri  # noqa: E402

con_giri = analizza_gomme_e_freni(canali, indice_giri(canali, dividi_in_giri(canali)))
test("B23 la crescita di pressione sullo stint è quella imposta (0,12 psi/giro)",
     con_giri.gomme.pendenza_pressione_psi_giro is not None
     and abs(con_giri.gomme.pendenza_pressione_psi_giro - 0.12) < 0.02,
     f"{con_giri.gomme.pendenza_pressione_psi_giro}")
test("B23b …e finisce nel verdetto come tendenza, non come valore assoluto",
     any("salgono" in v.titolo for v in con_giri.voci),
     f"{[v.titolo for v in con_giri.voci]}")

piatto = genera(pista, [GiroFinto(curve=buone) for _ in range(3)], completo=True)
report_piatto = analizza_gomme_e_freni(
    piatto, indice_giri(piatto, dividi_in_giri(piatto)))
test("B23c con pressioni stabili e bilanciate non si inventa nessun problema",
     report_piatto.voci == [], f"{[v.titolo for v in report_piatto.voci]}")
test("B24 le temperature dei freni distinguono anteriore e posteriore",
     report_gomme.freni is not None
     and abs(report_gomme.freni.squilibrio_ant_post_c - 50.0) < 1.0,
     f"{report_gomme.freni.squilibrio_ant_post_c if report_gomme.freni else '—'}")
test("B25 il consumo delle pastiglie è misurato",
     report_gomme.freni.pastiglie_consumate_mm.FL > 0)
test("B26 lo squilibrio fra i lati entra nel verdetto",
     any("sbilanciat" in v.titolo.lower() for v in report_gomme.voci),
     f"{[v.titolo for v in report_gomme.voci]}")
test("B27 …con la prova numerica e l'azione",
     all(v.prova and v.azione for v in report_gomme.voci))
test("B28 la finestra «ottimale» non verificata non viene usata per giudicare",
     "non è pubblicata" in g.nota_finestra)

senza_gomme = {k: v for k, v in canali.items() if "wheelPressure" not in k}
test("B29 senza le pressioni lo dichiara invece di tacere",
     any("pressioni" in d for d in analizza_gomme_e_freni(senza_gomme).dati_mancanti))

# ---------------------------------------------------------------------------
# 3 · Un report solo, un verdetto solo
# ---------------------------------------------------------------------------
print("\n─── Il motore di analisi con i canali ───")

senza = analizza(bundle)
con = analizza(bundle, canali)

test("B30 senza canali il report resta quello di L2",
     senza.ha_canali is False and senza.curve is None and senza.gomme_e_freni is None)
test("B31 …e dichiara che i canali non sono collegati",
     any("canali della shared memory non collegati" in d for d in senza.dati_mancanti))
test("B32 con i canali il report porta l'analisi per curva",
     con.ha_canali is True and con.curve is not None
     and len(con.curve["curve"]) == 3, f"{con.curve is None}")
test("B33 …e gomme e freni", con.gomme_e_freni is not None
     and con.gomme_e_freni["gomme"] is not None)
test("B34 il ritmo di L2 non cambia per l'arrivo dei canali",
     con.ritmo.miglior_giro_ms == senza.ritmo.miglior_giro_ms)
test("B35 il verdetto diventa uno solo, più ricco",
     len(con.verdetto) > len(senza.verdetto),
     f"{len(con.verdetto)} contro {len(senza.verdetto)}")
test("B36 …ordinato per gravità",
     [v.gravita for v in con.verdetto]
     == sorted([v.gravita for v in con.verdetto], reverse=True))
test("B37 nel verdetto unico c'è la curva che costa di più",
     any("curva 2" in v.titolo for v in con.verdetto),
     f"{[v.titolo for v in con.verdetto][:4]}")
test("B38 …e lo squilibrio delle pressioni",
     any("sbilanciat" in v.titolo.lower() for v in con.verdetto))
test("B39 ogni voce del verdetto unico ha prova e azione",
     all(v.prova and v.azione for v in con.verdetto))
test("B40 il report intero si serializza (è quello che leggerà Gigi)",
     len(con.model_dump_json()) > 1000)

# ---------------------------------------------------------------------------
# 4 · Le rotte: importa e analizza
# ---------------------------------------------------------------------------
print("\n─── Rotte ───")

radice = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_f4_"))
os.environ["PITWALL_SESSIONS_DIR"] = str(radice)
try:
    from fastapi.testclient import TestClient  # noqa: E402

    from app.main import app as fastapi_app  # noqa: E402

    id_registrazione = metadati["id"]
    cartella = radice / "telemetria" / id_registrazione
    cartella.mkdir(parents=True)
    colonne_f4 = [k for k, v in canali.items() if v.dtype == np.float32]
    colonne_i4 = [k for k, v in canali.items() if v.dtype == np.int32]
    np.savez_compressed(
        cartella / "canali.npz",
        f4=np.column_stack([canali[c] for c in colonne_f4]).astype(np.float32),
        i4=np.column_stack([canali[c] for c in colonne_i4]).astype(np.int32),
    )
    (cartella / "sessione.json").write_text(
        json.dumps({**metadati, "colonne": {"f4": colonne_f4, "i4": colonne_i4}},
                   ensure_ascii=False),
        encoding="utf-8")

    client = TestClient(fastapi_app, raise_server_exceptions=False)
    risposta = client.post(f"/api/telemetria/sessioni/{id_registrazione}/importa")
    corpo = risposta.json()
    test("B41 la registrazione si importa nell'archivio delle sessioni",
         risposta.status_code == 200 and corpo["giri"] == 4, risposta.text[:150])
    id_sessione = corpo["id_sessione"]

    elenco = client.get("/api/sessions").json()
    voce = next((s for s in elenco["sessioni"] if s["id"] == id_sessione), None)
    test("B42 …e compare nell'elenco insieme alle altre, con la sua fonte",
         voce is not None and voce["fonte"] == "acc_shm", f"{voce}")

    analisi = client.get(f"/api/sessions/{id_sessione}/analisi").json()
    test("B43 l'analisi della sessione registrata include le curve",
         analisi["ha_canali"] is True and len(analisi["curve"]["curve"]) == 3)
    test("B44 …e gomme e freni", analisi["gomme_e_freni"]["gomme"] is not None)
    test("B45 …e un verdetto unico che cita la curva peggiore",
         any("curva 2" in v["titolo"] for v in analisi["verdetto"]),
         f"{[v['titolo'] for v in analisi['verdetto']][:3]}")
    test("B46 il consumo vero arriva fino al report",
         analisi["carburante"]["calcolabile"] is True,
         f"{analisi['carburante']}")

    # Canali spariti (tetto dell'archivio): il report torna quello di L2, dichiarandolo.
    (cartella / "canali.npz").unlink()
    ridotta = client.get(f"/api/sessions/{id_sessione}/analisi").json()
    test("B47 se i canali non ci sono più, l'analisi non crolla",
         ridotta["ha_canali"] is False and ridotta["curve"] is None)
    test("B48 …e lo dichiara nei dati mancanti",
         any("canali della shared memory non collegati" in d
             for d in ridotta["dati_mancanti"]))
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
    print("✅ Registrazione, bundle e report allineati")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
