"""
test_telemetria.py — le tre pagine di shared memory e il lettore (L3 · Fase 1)

Su questo PC ACC non c'è e non ci sarà (decisione del 15/09: sta su PS5). Questi
test non possono quindi «provare che leggiamo ACC»: provano le tre cose che si
possono provare senza il gioco, e sono anche quelle che di solito rompono.

1. **La struttura è quella giusta.** Le dimensioni (800 · 1588 · 820 byte) e gli
   offset dei campi chiave sono ricalcolati a mano dal documento ufficiale Kunos
   v1.8.12 e scritti qui come numeri nudi: se qualcuno sposta un campo, la somma
   non torna più e il test cade. È il controllo che vale di più, perché un offset
   sbagliato non dà errore a schermo — dà numeri plausibili e falsi.
2. **Il lettore legge davvero.** Si crea una mappa finta (nome `pitwall_test_*`,
   mai quello del gioco), ci si scrive una pagina costruita a tavolino e si
   verifica che torni indietro identica.
3. **Il lettore non mente.** Gioco spento → errore dichiarato, non pagina di zeri.
   E sezione più corta del previsto (il caso del banco di prova su AC1) → i test
   inchiodano il fatto che Windows la lascia mappare lo stesso, arrotondandola alla
   pagina da 4 KB: la dimensione non è una verifica, l'identità nella pagina statica
   (`smVersion`, `acVersion`, `carModel`) sì.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_telemetria.py

Non richiede pytest, né rete, né chiave, né ACC.
"""

import ctypes
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))  # -> backend/

from app.telemetria import strutture as s  # noqa: E402
from app.tests.banco_finto import (  # noqa: E402
    NOMI_DI_PROVA,
    MappaFinta,
    byte_di,
    fisica_di_prova,
    grafica_di_prova,
    statica_di_prova,
)
from app.telemetria.lettore import (  # noqa: E402
    SU_WINDOWS,
    LettoreSharedMemory,
    PaginaMappata,
    TelemetriaNonDisponibile,
    pagina_a_dizionario,
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
# 1 · La struttura: dimensioni e offset ricalcolati dal documento ufficiale
# ---------------------------------------------------------------------------

print("\n─── Struttura delle tre pagine ───")

test("T01 la pagina fisica è di 800 byte",
     ctypes.sizeof(s.SPageFilePhysics) == 800,
     f"trovati {ctypes.sizeof(s.SPageFilePhysics)}")
test("T02 la pagina grafica è di 1588 byte",
     ctypes.sizeof(s.SPageFileGraphics) == 1588,
     f"trovati {ctypes.sizeof(s.SPageFileGraphics)}")
test("T03 la pagina statica è di 820 byte (non 784: 784 tronca wetTyresName)",
     ctypes.sizeof(s.SPageFileStatic) == 820,
     f"trovati {ctypes.sizeof(s.SPageFileStatic)}")

# Offset contati a mano sul documento: se cade uno di questi, è saltato un campo.
offset_fisica = {
    "packetId": 0, "gas": 4, "brake": 8, "fuel": 12, "gear": 16, "rpm": 20,
    "steerAngle": 24, "speedKmh": 28, "velocity": 32, "accG": 44,
    "wheelSlip": 56, "wheelPressure": 88, "tyreCoreTemp": 152,
    "suspensionTravel": 184, "brakeTemp": 348, "clutch": 364,
    "brakeBias": 564, "slipRatio": 640, "slipAngle": 656,
    "waterTemp": 712, "brakePressure": 716, "padLife": 740, "discLife": 756,
    "absVibrations": 796,
}
for campo, atteso in offset_fisica.items():
    vero = getattr(s.SPageFilePhysics, campo).offset
    test(f"T04.{campo} fisica: {campo} all'offset {atteso}", vero == atteso,
         f"trovato {vero}")

offset_grafica = {
    "packetId": 0, "status": 4, "session": 8, "currentTime": 12,
    "completedLaps": 132, "iCurrentTime": 140, "tyreCompound": 176,
    "normalizedCarPosition": 248, "carCoordinates": 256, "carID": 976,
    "isValidLap": 1408, "trackStatus": 1416, "mfdTyrePressureLF": 1540,
    "gapBehind": 1584,
}
for campo, atteso in offset_grafica.items():
    vero = getattr(s.SPageFileGraphics, campo).offset
    test(f"T05.{campo} grafica: {campo} all'offset {atteso}", vero == atteso,
         f"trovato {vero}")

offset_statica = {
    "smVersion": 0, "acVersion": 30, "numberOfSessions": 60, "numCars": 64,
    "carModel": 68, "track": 134, "playerNick": 332, "sectorCount": 400,
    "maxRpm": 412, "maxFuel": 416, "dryTyresName": 688, "wetTyresName": 754,
}
for campo, atteso in offset_statica.items():
    vero = getattr(s.SPageFileStatic, campo).offset
    test(f"T06.{campo} statica: {campo} all'offset {atteso}", vero == atteso,
         f"trovato {vero}")

# I campi dichiarati «non usati da ACC» devono esistere davvero: un nome sbagliato
# qui vorrebbe dire escludere dai canali un campo che invece il gioco riempie.
for pagina_nome, campi in s.CAMPI_NON_USATI.items():
    struttura = s.PAGINE[pagina_nome][1]
    esistenti = {n for n, _ in struttura._fields_}
    mancanti = sorted(campi - esistenti)
    test(f"T07.{pagina_nome} i campi «non usati» esistono nella struttura",
         not mancanti, f"non esistono: {mancanti}")

test("T08 la versione della struttura è dichiarata",
     s.VERSIONE_STRUTTURA == "1.8.12")
test("T09 i nomi delle tre mappe sono quelli di ACC",
     [n for n, _ in s.PAGINE.values()] ==
     ["Local\\acpmf_physics", "Local\\acpmf_graphics", "Local\\acpmf_static"])

# ---------------------------------------------------------------------------
# 2 · Il lettore, contro mappe finte
# ---------------------------------------------------------------------------

if not SU_WINDOWS:
    test("T10 lettore provabile solo su Windows", False, "questo non è Windows")
else:
    print("\n─── Lettore su mappe finte ───")

    NOMI = NOMI_DI_PROVA

    # Gioco spento: nessuna mappa esiste.
    lettore = LettoreSharedMemory(NOMI)
    stato = lettore.aggancia()
    test("T10 gioco spento: l'aggancio fallisce invece di restituire zeri",
         not stato.agganciato and "non sta girando" in (stato.motivo or ""),
         f"stato={stato}")

    # …e il tentativo non deve aver *creato* la mappa (è l'errore classico di mmap).
    pagina = PaginaMappata("physics", NOMI["physics"])
    creata = True
    try:
        pagina.apri()
    except TelemetriaNonDisponibile:
        creata = False
    finally:
        pagina.chiudi()
    test("T11 un aggancio fallito non crea mappe fantasma", not creata)

    # Gioco «acceso»: tre mappe finte con dentro pagine costruite a tavolino.
    mappe = [
        MappaFinta(NOMI["physics"], byte_di(fisica_di_prova())),
        MappaFinta(NOMI["graphics"], byte_di(grafica_di_prova())),
        MappaFinta(NOMI["static"], byte_di(statica_di_prova())),
    ]
    try:
        lettore = LettoreSharedMemory(NOMI)
        stato = lettore.aggancia()
        test("T12 con le mappe presenti l'aggancio riesce", stato.agganciato,
             stato.motivo or "")
        test("T13 mappa tutti i byte delle tre pagine",
             stato.pagine == {"physics": 800, "graphics": 1588, "static": 820},
             f"{stato.pagine}")
        test("T14 nessun campo dichiarato illeggibile", stato.campi_non_letti == {},
             f"{stato.campi_non_letti}")

        fisica = lettore.leggi_fisica()
        test("T15 la fisica torna indietro identica: velocità",
             abs(fisica.speedKmh - 123.4) < 0.01, f"{fisica.speedKmh}")
        test("T16 la fisica torna indietro identica: marcia e giri",
             fisica.gear == 4 and fisica.rpm == 7250)
        test("T17 gli array a 4 ruote restano nell'ordine FL FR RL RR",
             [round(v, 1) for v in fisica.wheelPressure] == [27.5, 27.6, 27.1, 27.2],
             f"{list(fisica.wheelPressure)}")
        test("T18 le temperature del core gomma tornano indietro",
             [round(v, 1) for v in fisica.tyreCoreTemp] == [82.0, 83.5, 79.0, 80.5])

        # Deduplica: stesso packetId = stesso istante, non un campione nuovo.
        test("T19 stesso packetId: nessun campione nuovo",
             lettore.leggi_fisica() is None)
        mappe[0].scrivi(byte_di(fisica_di_prova(packet_id=8)))
        test("T20 packetId cambiato: campione nuovo",
             lettore.leggi_fisica() is not None)
        test("T21 con salta_duplicati=False si rilegge comunque",
             lettore.leggi_fisica(salta_duplicati=False) is not None)

        grafica = lettore.leggi_grafica()
        test("T22 la posizione sul giro (normalizedCarPosition) torna indietro",
             abs(grafica.normalizedCarPosition - 0.375) < 1e-6,
             f"{grafica.normalizedCarPosition}")
        test("T23 le stringhe wide-char si rileggono come stringhe",
             grafica.currentTime == "1:48.123", repr(grafica.currentTime))
        test("T24 stato del gioco letto come enum",
             lettore.stato_gioco() is s.ACC_STATUS.LIVE)
        test("T25 in pista solo quando il gioco è LIVE", lettore.in_pista())

        mappe[1].scrivi(byte_di(grafica_di_prova(stato=1)))
        test("T26 nel replay non si registra", not lettore.in_pista())
        mappe[1].scrivi(byte_di(grafica_di_prova(stato=3)))
        test("T27 in pausa non si registra", not lettore.in_pista())
        mappe[1].scrivi(byte_di(grafica_di_prova(stato=99)))
        test("T28 stato sconosciuto: si tratta come spento, non si indovina",
             lettore.stato_gioco() is s.ACC_STATUS.OFF)
        mappe[1].scrivi(byte_di(grafica_di_prova()))

        statica = lettore.leggi_statica()
        test("T29 la pagina statica dà vettura e pista",
             statica.carModel == "bmw_m4_gt3" and statica.track == "monza")
        test("T30 l'ultimo campo della statica (wetTyresName) si legge davvero",
             statica.wetTyresName == "WHE2020", repr(statica.wetTyresName))
        test("T31 la versione della shared memory del gioco è leggibile",
             statica.smVersion == "1.8.12")

        # Conversione in dizionario
        d = pagina_a_dizionario(fisica, "physics")
        test("T32 il dizionario contiene i campi utili", d["speedKmh"] is not None)
        test("T33 gli array diventano liste", isinstance(d["wheelPressure"], list)
             and len(d["wheelPressure"]) == 4)
        test("T34 gli array 4x3 diventano liste di liste",
             isinstance(d["tyreContactPoint"][0], list)
             and len(d["tyreContactPoint"]) == 4)
        test("T35 i campi che ACC non riempie restano fuori per default",
             "tyreWear" not in d and "camberRAD" not in d and "drs" not in d)
        test("T36 …ma si possono chiedere esplicitamente",
             "tyreWear" in pagina_a_dizionario(fisica, "physics",
                                               includi_non_usati=True))

        lettore.sgancia()
        test("T37 dopo lo sgancio il lettore non risulta agganciato",
             not lettore.agganciato)
    finally:
        for m in mappe:
            m.chiudi()

    # Sezione più corta del previsto: è il caso del banco di prova su AC1, la cui
    # pagina fisica è di 712 byte contro gli 800 di ACC.
    #
    # Questo blocco esiste per inchiodare un fatto scomodo che ho verificato qui e
    # che contraddice la prima versione di questo lettore: **Windows arrotonda ogni
    # sezione alla pagina da 4 KB**, quindi mappare 800 byte su una sezione da 712
    # RIESCE, e i byte in più leggono zero senza un solo errore. Tutte e tre le
    # pagine di ACC stanno sotto i 4 KB → nessun controllo sulla dimensione può
    # accorgersi del gioco sbagliato. Se un giorno qualcuno volesse rimettere una
    # "verifica della dimensione", questi test dicono perché non funzionerebbe.
    print("\n─── Sezione più corta del previsto (banco AC1) ───")
    corte = [
        MappaFinta(NOMI["physics"], byte_di(fisica_di_prova())[:712]),
        MappaFinta(NOMI["graphics"], byte_di(grafica_di_prova())),
        MappaFinta(NOMI["static"], byte_di(statica_di_prova())),
    ]
    try:
        lettore = LettoreSharedMemory(NOMI)
        stato = lettore.aggancia()
        test("T38 con una sezione corta l'aggancio riesce lo stesso",
             stato.agganciato, stato.motivo or "")
        test("T39 Windows arrotonda alla pagina: la dimensione NON è misurabile",
             stato.pagine.get("physics") == 800, f"{stato.pagine}")
        fisica = lettore.leggi_fisica()
        test("T40 i campi dentro la parte scritta sono corretti",
             abs(fisica.speedKmh - 123.4) < 0.01)
        test("T41 i campi oltre la sezione leggono zero, in silenzio",
             list(fisica.padLife) == [0.0, 0.0, 0.0, 0.0])
        lettore.sgancia()
    finally:
        for m in corte:
            m.chiudi()

    # Ciò che resta a difenderci: l'identità che il gioco dichiara nella statica.
    print("\n─── Identità di chi sta dall'altra parte ───")
    altri = [
        MappaFinta(NOMI["physics"], byte_di(fisica_di_prova())),
        MappaFinta(NOMI["graphics"], byte_di(grafica_di_prova())),
        MappaFinta(NOMI["static"], byte_di(statica_di_prova())),
    ]
    try:
        lettore = LettoreSharedMemory(NOMI)
        stato = lettore.aggancia()
        test("T42 l'aggancio riporta la versione della shared memory",
             stato.versione_sm == "1.8.12", f"{stato.versione_sm}")
        test("T43 …la versione del gioco", stato.versione_gioco == "1.10.2",
             f"{stato.versione_gioco}")
        test("T44 …la vettura e la pista dichiarate",
             stato.vettura == "bmw_m4_gt3" and stato.pista == "monza",
             f"{stato.vettura} / {stato.pista}")
        test("T45 e la versione di struttura con cui stiamo leggendo",
             stato.versione_struttura == s.VERSIONE_STRUTTURA)
        lettore.sgancia()
    finally:
        for m in altri:
            m.chiudi()

    # Stringhe senza terminatore: ctypes non deve esplodere.
    print("\n─── Casi limite ───")
    grezzo = bytearray(byte_di(statica_di_prova()))
    piena = "X" * 15
    grezzo[0:30] = piena.encode("utf-16-le")
    piena_mappa = MappaFinta(NOMI["static"], bytes(grezzo))
    altre = [
        MappaFinta(NOMI["physics"], byte_di(fisica_di_prova())),
        MappaFinta(NOMI["graphics"], byte_di(grafica_di_prova())),
    ]
    try:
        lettore = LettoreSharedMemory(NOMI)
        lettore.aggancia()
        letto = None
        esploso = False
        try:
            letto = lettore.leggi_statica().smVersion
        except ValueError:
            esploso = True
        test("T46 una stringa senza terminatore non fa esplodere la lettura",
             not esploso, "ctypes ha alzato ValueError")
        test("T47 …e viene letta per intero", letto == piena, repr(letto))
        lettore.sgancia()
    finally:
        piena_mappa.chiudi()
        for m in altre:
            m.chiudi()

    # Leggere senza aver agganciato è un errore dichiarato, non un crash oscuro.
    lettore = LettoreSharedMemory(NOMI)
    alzato = False
    try:
        lettore.leggi_fisica()
    except TelemetriaNonDisponibile:
        alzato = True
    test("T48 leggere senza aggancio alza un errore dichiarato", alzato)

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Lettura della shared memory conforme")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
