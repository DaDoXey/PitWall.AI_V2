"""
test_registratore.py — dizionario dei canali e registrazione su disco (L3 · Fase 2)

Si registra da mappe finte (gli stessi nomi `pitwall_test_*` di test_telemetria):
si scrive una pagina, si chiama `passo()`, si guarda cosa finisce su disco. Niente
attese sul tempo che scorre: il ciclo è separato dal passo apposta, così questi test
sono deterministici e durano un istante.

Le cose che qui si vogliono inchiodare:
* il dizionario copre **tutte** le colonne registrate, con unità e descrizione;
* un valore scritto nella pagina esce identico dal file `.npz` — passando per il
  nome del canale, non per la posizione;
* i tempi in millisecondi restano **interi esatti** (è il motivo per cui interi e
  decimali stanno in due matrici separate);
* si registra solo in pista, e mai due volte lo stesso istante;
* una registrazione interrotta a metà non perde i blocchi già scritti.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_registratore.py
"""

import ctypes
import json
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

from app.telemetria import dizionario, strutture as s  # noqa: E402
from app.telemetria.lettore import SU_WINDOWS  # noqa: E402
from app.telemetria.registratore import (  # noqa: E402
    Registratore,
    consolida,
    leggi_canali,
    nuovo_id,
)
from app.tests.banco_finto import (  # noqa: E402
    NOMI_DI_PROVA,
    MappaFinta,
    byte_di,
    fisica_di_prova,
    grafica_di_prova,
    statica_di_prova,
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


# ---------------------------------------------------------------------------
# 1 · Il dizionario dei canali
# ---------------------------------------------------------------------------

print("\n─── Dizionario dei canali ───")

canali = dizionario.canali()
nomi = dizionario.nomi()

test("G01 ci sono canali", len(canali) > 150, f"{len(canali)}")
test("G02 i nomi sono unici", len(set(nomi)) == len(nomi))
test("G03 ogni canale ha la descrizione ufficiale di Kunos",
     all(c.descrizione for c in canali),
     f"senza: {[c.nome for c in canali if not c.descrizione][:5]}")
test("G04 ogni canale dichiara un tipo numerico",
     all(c.tipo in ("f4", "i4") for c in canali))
test("G05 ogni canale dichiara l'unità e da dove viene",
     all(c.unita and c.unita_fonte for c in canali))
test("G06 i campi che ACC non riempie non sono canali",
     not [c for c in canali if c.campo in s.CAMPI_NON_USATI.get(c.pagina, frozenset())])
test("G07 le altre vetture in pista restano fuori, e la ragione è scritta",
     not [c for c in canali if c.campo in ("carCoordinates", "carID")]
     and "carCoordinates" in dizionario.ESCLUSI)
test("G08 le stringhe non diventano canali",
     not [c for c in canali if c.campo in ("currentTime", "tyreCompound")])
test("G09 gli array a 4 si aprono sulle quattro ruote",
     {"physics.wheelPressure.FL", "physics.wheelPressure.FR",
      "physics.wheelPressure.RL", "physics.wheelPressure.RR"} <= set(nomi))
test("G10 i vettori si aprono sui tre assi",
     {"physics.accG.x", "physics.accG.y", "physics.accG.z"} <= set(nomi))
test("G11 i danni si aprono per lato, con nomi leggibili",
     "physics.carDamage.centro" in nomi and "physics.carDamage.anteriore" in nomi)
test("G12 le matrici 4x3 si aprono ruota per asse",
     "physics.tyreContactPoint.RR.z" in nomi)
test("G13 c'è la posizione sul giro, che regge tutta l'analisi per curva",
     "graphics.normalizedCarPosition" in nomi)
test("G14 i tempi in millisecondi sono canali interi",
     [c.tipo for c in canali if c.nome == "graphics.iCurrentTime"] == ["i4"])
test("G15 il dizionario da scrivere su disco porta con sé le avvertenze",
     len(dizionario.come_json(100.0)["avvertenze"]) >= 3)
test("G16 …e la versione di struttura con cui è stato registrato",
     dizionario.come_json(100.0)["versione_struttura"] == s.VERSIONE_STRUTTURA)

print("\n─── Nomi delle sessioni ───")
id_1 = nuovo_id("bmw_m4_gt3", "monza")
test("N01 l'id contiene pista e vettura", "monza" in id_1 and "bmw_m4_gt3" in id_1, id_1)
test("N02 due id di fila sono diversi", nuovo_id("a", "b") != nuovo_id("a", "b"))
test("N03 un id senza vettura né pista resta valido",
     bool(nuovo_id(None, None)), nuovo_id(None, None))

# ---------------------------------------------------------------------------
# 2 · La registrazione vera, su mappe finte
# ---------------------------------------------------------------------------

if not SU_WINDOWS:
    test("R00 registrazione provabile solo su Windows", False, "questo non è Windows")
else:
    NOMI = NOMI_DI_PROVA
    radice = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_reg_"))

    def fisica(packet_id: int, velocita: float = 123.4) -> s.SPageFilePhysics:
        p = fisica_di_prova(packet_id)
        p.speedKmh = velocita
        return p

    def grafica(stato: int = 2, posizione: float = 0.0,
                tempo_ms: int = 108123) -> s.SPageFileGraphics:
        g = grafica_di_prova(stato=stato, posizione=posizione)
        g.iCurrentTime = tempo_ms
        return g

    mappe = [
        MappaFinta(NOMI["physics"], byte_di(fisica(1))),
        MappaFinta(NOMI["graphics"], byte_di(grafica())),
        MappaFinta(NOMI["static"], byte_di(statica_di_prova())),
    ]
    try:
        print("\n─── Registrazione ───")
        reg = Registratore(frequenza_hz=10.0, secondi_per_blocco=0.5,  # blocco = 5 campioni
                           cartella=radice, nomi_mappa=NOMI)
        stato = reg._lettore.aggancia()
        test("R01 il registratore si aggancia", stato.agganciato, stato.motivo or "")

        test("R02 prima di registrare non c'è nessuna sessione", not reg.in_registrazione)
        test("R03 il primo passo registra e apre la sessione",
             reg.passo() and reg.in_registrazione)

        sessione = reg.sessione
        test("R04 la sessione prende vettura e pista dalla pagina statica",
             sessione.vettura == "bmw_m4_gt3" and sessione.pista == "monza")
        test("R05 …e il pilota", sessione.pilota == "Edoardo", f"{sessione.pilota}")
        test("R06 …e il tipo di sessione", sessione.tipo_sessione == "PRACTICE",
             f"{sessione.tipo_sessione}")
        test("R07 la sessione è marcata attendibile", sessione.attendibile)
        test("R08 il dizionario viene scritto accanto ai dati",
             (sessione.cartella / "dizionario.json").exists())
        test("R09 i metadati vengono scritti subito, non solo alla fine",
             (sessione.cartella / "sessione.json").exists())

        test("R10 lo stesso packetId non viene registrato due volte",
             reg.passo() is False and sessione.campioni == 1)
        test("R11 …e il duplicato viene contato, non ignorato in silenzio",
             sessione.duplicati_saltati == 1)

        # Una manciata di campioni con valori che cambiano.
        for i in range(2, 12):
            mappe[0].scrivi(byte_di(fisica(i, velocita=100.0 + i)))
            mappe[1].scrivi(byte_di(grafica(posizione=i / 100.0,
                                            tempo_ms=100000 + i * 1000)))
            reg.passo()
        test("R12 ha registrato tutti i campioni nuovi", sessione.campioni == 11,
             f"{sessione.campioni}")
        test("R13 …e ha scritto blocchi su disco senza aspettare la fine",
             sessione.blocchi >= 2, f"{sessione.blocchi}")

        # Fuori dalla pista non si registra.
        mappe[1].scrivi(byte_di(grafica(stato=1, posizione=0.5)))   # replay
        mappe[0].scrivi(byte_di(fisica(99)))
        test("R14 nel replay non registra", reg.passo() is False)
        mappe[1].scrivi(byte_di(grafica(stato=3, posizione=0.5)))   # pausa
        test("R15 in pausa non registra", reg.passo() is False)
        test("R16 …e la sessione resta aperta (non si chiude a ogni pausa)",
             reg.in_registrazione)

        cartella = sessione.cartella
        id_chiuso = reg.ferma()
        test("R17 alla chiusura la sessione viene consolidata",
             id_chiuso == sessione.id and (cartella / "canali.npz").exists())
        test("R18 i blocchi temporanei spariscono",
             not list(cartella.glob("blocchi/*.npz")))

        print("\n─── Ciò che è finito su disco ───")
        serie = leggi_canali(cartella)
        test("R19 il file rilegge tutte le colonne del dizionario",
             set(serie) == set(dizionario.nomi()),
             f"differenza: {sorted(set(dizionario.nomi()) ^ set(serie))[:4]}")
        test("R20 ogni colonna ha un valore per campione",
             all(len(v) == 11 for v in serie.values()))
        test("R21 la velocità torna indietro campione per campione",
             [round(float(v), 1) for v in serie["physics.speedKmh"][:3]]
             == [123.4, 102.0, 103.0],
             f"{[round(float(v),1) for v in serie['physics.speedKmh'][:3]]}")
        test("R22 la pressione gomme resta sulla ruota giusta",
             abs(float(serie["physics.wheelPressure.FR"][0]) - 27.6) < 0.01)
        test("R23 la posizione sul giro torna indietro",
             abs(float(serie["graphics.normalizedCarPosition"][2]) - 0.03) < 1e-6,
             f"{float(serie['graphics.normalizedCarPosition'][2])}")
        test("R24 i tempi in millisecondi sono interi ESATTI",
             list(serie["graphics.iCurrentTime"][1:4]) == [102000, 103000, 104000]
             and serie["graphics.iCurrentTime"].dtype == np.int32,
             f"{list(serie['graphics.iCurrentTime'][1:4])}")

        orologio = serie["pitwall.tempo_ms"]
        test("R24b c'è l'orologio della registrazione, che ACC non fornisce",
             "pitwall.tempo_ms" in serie and orologio.dtype == np.int32)
        test("R24c parte da zero col primo campione", int(orologio[0]) == 0,
             f"{orologio[0]}")
        test("R24d …e non torna mai indietro",
             bool(np.all(np.diff(orologio) >= 0)), f"{list(orologio[:5])}")

        meta = json.loads((cartella / "sessione.json").read_text(encoding="utf-8"))
        test("R25 i metadati dichiarano frequenza, versione e conteggi",
             meta["frequenza_hz"] == 10.0
             and meta["versione_struttura"] == s.VERSIONE_STRUTTURA
             and meta["campioni"] == 11)
        test("R26 …e la fine della sessione", bool(meta["fine"]))
        diz = json.loads((cartella / "dizionario.json").read_text(encoding="utf-8"))
        test("R27 il dizionario su disco descrive esattamente quelle colonne",
             diz["colonne"] == len(dizionario.canali())
             and {c["nome"] for c in diz["canali"]} == set(serie))

        print("\n─── Registrazione interrotta male ───")
        # Nessun `ferma()`: i blocchi restano lì, come dopo un crash del gioco.
        mappe[0].scrivi(byte_di(fisica(200)))
        mappe[1].scrivi(byte_di(grafica(posizione=0.9)))
        reg2 = Registratore(frequenza_hz=10.0, secondi_per_blocco=0.2,
                            cartella=radice, nomi_mappa=NOMI)
        reg2._lettore.aggancia()
        for i in range(200, 206):
            mappe[0].scrivi(byte_di(fisica(i)))
            reg2.passo()
        cartella2 = reg2.sessione.cartella
        campioni2 = reg2.sessione.campioni
        blocchi_rimasti = list((cartella2 / "blocchi").glob("*.npz"))
        test("R28 i blocchi scritti prima dell'interruzione sono sul disco",
             len(blocchi_rimasti) >= 1, f"{blocchi_rimasti}")
        uscita = consolida(cartella2)
        test("R29 si possono consolidare dopo, senza perdere niente",
             uscita is not None and uscita.exists())
        with np.load(cartella2 / "canali.npz") as dati:
            righe = dati["f4"].shape[0]
        test("R30 …e contengono i campioni già registrati",
             0 < righe <= campioni2, f"{righe} su {campioni2}")
        reg2._lettore.sgancia()
    finally:
        for m in mappe:
            m.chiudi()
        shutil.rmtree(radice, ignore_errors=True)

    # -----------------------------------------------------------------------
    # 3 · Le rotte, sopra una registrazione vera
    # -----------------------------------------------------------------------
    print("\n─── Rotte ───")
    import os

    radice_api = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_api_"))
    os.environ["PITWALL_SESSIONS_DIR"] = str(radice_api)
    mappe_api = [
        MappaFinta(NOMI["physics"], byte_di(fisica_di_prova(1))),
        MappaFinta(NOMI["graphics"], byte_di(grafica_di_prova())),
        MappaFinta(NOMI["static"], byte_di(statica_di_prova())),
    ]
    try:
        from fastapi.testclient import TestClient  # noqa: E402

        from app.main import app as fastapi_app  # noqa: E402

        reg3 = Registratore(frequenza_hz=10.0, secondi_per_blocco=10.0,
                            nomi_mappa=NOMI)
        reg3._lettore.aggancia()
        for i in range(1, 6):
            mappe_api[0].scrivi(byte_di(fisica_di_prova(i)))
            mappe_api[1].scrivi(byte_di(grafica_di_prova(posizione=i / 10.0)))
            reg3.passo()
        id_sessione = reg3.sessione.id
        reg3.ferma()

        client = TestClient(fastapi_app, raise_server_exceptions=False)

        r = client.get("/api/telemetria/stato")
        test("A01 lo stato risponde 200 e dice se è abilitato",
             r.status_code == 200 and r.json()["abilitato"] is True, r.text[:120])
        test("A02 …e quante colonne registra",
             r.json()["colonne"] == len(dizionario.canali()))

        r = client.get("/api/telemetria/sessioni")
        elenco = r.json()
        test("A03 l'elenco trova la registrazione appena chiusa",
             r.status_code == 200
             and any(s["id"] == id_sessione for s in elenco["sessioni"]),
             r.text[:160])
        voce = next(s for s in elenco["sessioni"] if s["id"] == id_sessione)
        test("A04 l'elenco mostra vettura, pista e campioni",
             voce["vettura"] == "bmw_m4_gt3" and voce["pista"] == "monza"
             and voce["campioni"] == 5, f"{voce}")
        test("A05 …e dichiara il tetto dell'archivio", "tetto" in elenco)

        r = client.get(f"/api/telemetria/sessioni/{id_sessione}")
        test("A06 il dettaglio dà i metadati completi",
             r.status_code == 200 and r.json()["frequenza_hz"] == 10.0
             and r.json()["ha_canali"] is True, r.text[:160])

        r = client.get(f"/api/telemetria/sessioni/{id_sessione}/canali",
                       params={"nomi": "physics.speedKmh,graphics.normalizedCarPosition"})
        dati = r.json()
        test("A07 i canali si chiedono per nome",
             r.status_code == 200 and len(dati["canali"]) == 2, r.text[:160])
        test("A08 …e tornano indietro campione per campione",
             len(dati["canali"]["physics.speedKmh"]) == 5, f"{dati['campioni']}")
        test("A09 la decimazione funziona",
             len(client.get(f"/api/telemetria/sessioni/{id_sessione}/canali",
                            params={"nomi": "physics.speedKmh", "ogni": 2}
                            ).json()["canali"]["physics.speedKmh"]) == 3)
        test("A10 senza nomi non si scarica tutto: 400",
             client.get(f"/api/telemetria/sessioni/{id_sessione}/canali"
                        ).status_code == 400)
        test("A11 un canale inventato dà 404",
             client.get(f"/api/telemetria/sessioni/{id_sessione}/canali",
                        params={"nomi": "physics.inventato"}).status_code == 404)
        test("A12 un id malformato non arriva al disco: 400",
             client.get("/api/telemetria/sessioni/../../etc").status_code in (400, 404))
        test("A13 un id ben formato ma inesistente: 404",
             client.get("/api/telemetria/sessioni/20200101-000000-nessuna-0000"
                        ).status_code == 404)

        r = client.delete(f"/api/telemetria/sessioni/{id_sessione}")
        test("A14 la cancellazione funziona ed è definitiva",
             r.status_code == 200
             and not (radice_api / "telemetria" / id_sessione).exists())

        # Tetto dell'archivio: i canali grezzi si liberano, la storia resta.
        os.environ["PITWALL_TELEMETRIA_MAX_SESSIONI"] = "1"
        from app.telemetria.registratore import applica_tetto  # noqa: E402

        cartelle = []
        for n in range(2):
            reg4 = Registratore(frequenza_hz=10.0, secondi_per_blocco=10.0,
                                nomi_mappa=NOMI)
            reg4._lettore.aggancia()
            for i in range(1, 4):
                mappe_api[0].scrivi(byte_di(fisica_di_prova(100 * n + i)))
                reg4.passo()
            cartelle.append(reg4.sessione.cartella)
            reg4.ferma()
        vecchia, nuova = cartelle
        test("A15 oltre il tetto i canali grezzi della più vecchia spariscono",
             not (vecchia / "canali.npz").exists() and (nuova / "canali.npz").exists())
        meta_vecchia = json.loads((vecchia / "sessione.json").read_text(encoding="utf-8"))
        test("A16 …ma la sessione resta, dichiarando che i canali sono stati rimossi",
             meta_vecchia.get("canali_rimossi") is True
             and meta_vecchia["campioni"] == 3)
        test("A17 applicare di nuovo il tetto non rompe niente",
             applica_tetto(radice_api / "telemetria") == [])
        os.environ.pop("PITWALL_TELEMETRIA_MAX_SESSIONI", None)
    finally:
        for m in mappe_api:
            m.chiudi()
        os.environ.pop("PITWALL_SESSIONS_DIR", None)
        shutil.rmtree(radice_api, ignore_errors=True)

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Registratore conforme")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
