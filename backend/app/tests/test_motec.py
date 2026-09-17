"""
test_motec.py — lettura dei file MoTeC di ACC: `.ld`, `.ldx` e nome del file (L5 · Fase 1)

I file veri non stanno nel repo (licenza CC BY-NC-SA, e comunque non sono di Edoardo):
il lettore è stato verificato su di loro a parte, il 17/09 — 16 file su 16, giri
uguali al millesimo al «Fastest Time», dati letti fino all'ultimo byte. Questi test
provano, su file costruiti a tavolino con la stessa impaginazione, le tre cose che
devono restare vere per sempre:

1. **Si legge quello che c'è scritto.** Intestazione, vettura, pista, data, canali,
   frequenze, valori — e i giri dai beacon del `.ldx`, in microsecondi.
2. **Il lettore non mente.** File troncato, marcatore sbagliato, lista dei canali che
   gira in tondo, puntatore oltre la fine: errore dichiarato, mai numeri inventati.
   Un canale di tipo sconosciuto resta nell'elenco con il motivo, gli altri si leggono.
3. **Quello che ACC non riempie non si usa.** I canali si contano sulla lista (e se
   l'intestazione ne dichiara altri lo si dice); il giro più veloce si ricontrolla sui beacon.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_motec.py

Non richiede pytest, né rete, né chiave, né i file veri.
"""

import pathlib
import shutil
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))  # -> backend/

import numpy as np  # noqa: E402

from app.motec import (  # noqa: E402
    FileMotecNonValido,
    LdxNonValido,
    leggi_ld,
    leggi_ldx,
    leggi_nome_file,
    leggi_registrazione,
    tempo_in_secondi,
)
from app.motec.ld import DIMENSIONE_CANALE, DIMENSIONE_INTESTAZIONE  # noqa: E402
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


def alza(eccezione, funzione, *args) -> tuple[bool, str]:
    try:
        funzione(*args)
    except eccezione as e:
        return True, str(e)
    except Exception as e:  # noqa: BLE001 — un errore diverso è un test fallito, non un crash
        return False, f"{type(e).__name__}: {e}"
    return False, "nessun errore"


# Una registrazione di 10 s: velocità a 60 Hz, freno a 20 Hz, pressione a 20 Hz.
DURATA = 10.0
velocita = np.linspace(20.0, 70.0, int(DURATA * 60), dtype=np.float32)
freno = np.tile(np.array([0.0, 0.0, 100.0, 50.0], dtype=np.float32), int(DURATA * 5))
pressione = np.full(int(DURATA * 20), 26.5, dtype=np.float32)
CANALI = [
    CanaleFinto("SPEED", "m/s", 60, velocita),
    CanaleFinto("BRAKE", "%", 20, freno),
    CanaleFinto("TYRE_PRESS_LF", "..", 20, pressione),
]
LD = scrivi_ld(CANALI)

# ---------------------------------------------------------------------------
print("\n─── Intestazione e canali ───")
# ---------------------------------------------------------------------------
f = leggi_ld(LD)
test("M01 vettura e pista dall'intestazione", (f.vettura, f.pista) == ("M4 GT3", "monza"),
     f"{f.vettura!r} {f.pista!r}")
test("M02 data e ora interpretate",
     f.data_ora is not None and f.data_ora.isoformat() == "2023-11-28T09:57:06", str(f.data_ora))
test("M03 dispositivo ADL 420 e peso vettura dal blocco vettura",
     (f.dispositivo, f.versione_dispositivo, f.peso_vettura) == ("ADL", 420, 1257))
test("M04 i canali si contano sulla lista; l'intestazione a u16 torna (3)",
     len(f.canali) == 3 and f.canali_dichiarati == 3, f"{len(f.canali)} {f.canali_dichiarati}")
f_bugia = leggi_ld(scrivi_ld(CANALI, canali_dichiarati=7))
test("M04b intestazione che dichiara altri canali → avvertenza, vale la lista",
     len(f_bugia.canali) == 3 and any("dichiara 7" in a for a in f_bugia.avvertenze), str(f_bugia.avvertenze))
test("M05 nomi, unità e frequenze nell'ordine del file",
     [(c.nome, c.unita, c.frequenza_hz) for c in f.canali]
     == [("SPEED", "m/s", 60), ("BRAKE", "%", 20), ("TYRE_PRESS_LF", "..", 20)])
v = f.canale("SPEED")
test("M06 valori float32 riletti identici", np.array_equal(v.valori(), velocita.astype(np.float64)))
test("M07 durata del canale = campioni / frequenza", abs(v.durata_s - DURATA) < 1e-9, str(v.durata_s))
test("M08 i valori si leggono una volta sola (stessa copia)", v.valori() is v.valori())
test("M09 un file di ACC non produce avvertenze", f.avvertenze == [], str(f.avvertenze))
test("M10 canale inesistente → None, non errore", f.canale("FUEL") is None)

# ---------------------------------------------------------------------------
print("\n─── Tipi e conversione ───")
# ---------------------------------------------------------------------------
int16 = CanaleFinto("GEAR_RAW", "", 10, np.array([12, 34, -5], dtype=np.int16), tipo=(3, 2),
                    scala=2, decimali=1, offset=3, moltiplicatore=2)
f2 = leggi_ld(scrivi_ld([int16]))
c = f2.canale("GEAR_RAW")
atteso = (np.array([12, 34, -5]) / 2 * 0.1 + 3) * 2
test("M11 int16 con scala/decimali/offset/moltiplicatore: formula applicata",
     np.allclose(c.valori(), atteso), f"{c.valori()} vs {atteso}")
test("M12 conversione non identità dichiarata come non verificata",
     not c.conversione_verificata and not c.tipo_verificato
     and any("GEAR_RAW" in a for a in f2.avvertenze), str(f2.avvertenze))
doppio = CanaleFinto("LAT", "deg", 10, np.array([45.123456789, 9.1], dtype=np.float64), tipo=(8, 8))
test("M13 float64 letto senza perdita",
     np.array_equal(leggi_ld(scrivi_ld([doppio])).canale("LAT").valori(), np.array([45.123456789, 9.1])))

sconosciuto = bytearray(scrivi_ld([CanaleFinto("STRANO", "", 10, np.zeros(4, np.float32)),
                                   CanaleFinto("SPEED", "m/s", 10, np.ones(4, np.float32))]))
p_meta = int.from_bytes(sconosciuto[8:12], "little")
sconosciuto[p_meta + 18:p_meta + 20] = (99).to_bytes(2, "little")  # famiglia del tipo
f3 = leggi_ld(bytes(sconosciuto))
strano = f3.canale("STRANO")
ok_err, msg = alza(FileMotecNonValido, strano.valori)
test("M14 tipo sconosciuto: canale non leggibile con il motivo, gli altri sì",
     not strano.leggibile and "tipo" in (strano.motivo or "") and ok_err
     and np.array_equal(f3.canale("SPEED").valori(), np.ones(4)), f"{strano.motivo} {msg}")

# ---------------------------------------------------------------------------
print("\n─── Il lettore non mente ───")
# ---------------------------------------------------------------------------
ok_err, msg = alza(FileMotecNonValido, leggi_ld, LD[:1000])
test("M15 file più corto dell'intestazione → errore dichiarato", ok_err, msg)
rotto = bytearray(LD)
rotto[0:4] = (0x41).to_bytes(4, "little")
ok_err, msg = alza(FileMotecNonValido, leggi_ld, bytes(rotto))
test("M16 marcatore iniziale sbagliato → «non è un .ld»", ok_err and "marcatore" in msg, msg)
ok_err, msg = alza(FileMotecNonValido, leggi_ld, LD[:-100])
test("M17 dati troncati → errore, non una lettura oltre la fine", ok_err and "oltre la fine" in msg, msg)

ciclo = bytearray(LD)
p_meta = int.from_bytes(ciclo[8:12], "little")
secondo = p_meta + DIMENSIONE_CANALE
ciclo[secondo + 4:secondo + 8] = p_meta.to_bytes(4, "little")  # il 2° punta di nuovo al 1°
ok_err, msg = alza(FileMotecNonValido, leggi_ld, bytes(ciclo))
test("M18 lista dei canali che torna su se stessa → errore", ok_err and "se stessa" in msg, msg)

fuori = bytearray(LD)
fuori[8:12] = (len(LD) + 10).to_bytes(4, "little")
ok_err, msg = alza(FileMotecNonValido, leggi_ld, bytes(fuori))
test("M19 puntatore ai canali oltre la fine → errore", ok_err, msg)

vuoto = bytearray(LD)
vuoto[8:12] = (0).to_bytes(4, "little")
ok_err, msg = alza(FileMotecNonValido, leggi_ld, bytes(vuoto))
test("M20 nessun canale → errore", ok_err and "nessun canale" in msg, msg)

prec = bytearray(LD)
prec[secondo:secondo + 4] = (12345).to_bytes(4, "little")
f4 = leggi_ld(bytes(prec))
test("M21 puntatore «precedente» incoerente → avvertenza, file comunque letto",
     len(f4.canali) == 3 and any("precedente" in a for a in f4.avvertenze), str(f4.avvertenze))

data_rotta = bytearray(LD)
data_rotta[94:110] = b"ieri".ljust(16, b"\0")
f5 = leggi_ld(bytes(data_rotta))
test("M22 data illeggibile → None e avvertenza", f5.data_ora is None and f5.avvertenze, str(f5.avvertenze))
test("M23 intestazione di 1762 byte e metadati di 124 (come nei file veri)",
     (DIMENSIONE_INTESTAZIONE, DIMENSIONE_CANALE) == (1762, 124))

# ---------------------------------------------------------------------------
print("\n─── .ldx: i giri dai beacon ───")
# ---------------------------------------------------------------------------
monza = leggi_ldx(scrivi_ldx([0.024, 110.006], tempo_migliore="1:49.982"))
test("M24 beacon in microsecondi → secondi", monza.beacon_s == [0.024, 110.006], str(monza.beacon_s))
test("M25 due beacon = un giro, uguale al «Fastest Time» dei file veri (Monza)",
     len(monza.tempi_giro_s) == 1 and abs(monza.tempi_giro_s[0] - 109.982) < 1e-6
     and monza.avvertenze == [], f"{monza.tempi_giro_s} {monza.avvertenze}")
tratti = monza.tratti(110.01)
test("M26 uscita e rientro parziali, il giro in mezzo completo",
     [t.parziale for t in tratti] == [True, False, True] and abs(tratti[1].durata_s - 109.982) < 1e-6)
stint = leggi_ldx(scrivi_ldx([5.0, 105.0, 204.5, 305.25]))
test("M27 più giri: tempi nell'ordine", np.allclose(stint.tempi_giro_s, [100.0, 99.5, 100.75]),
     str(stint.tempi_giro_s))
bugia = leggi_ldx(scrivi_ldx([0.0, 100.0], tempo_migliore="1:30.000"))
test("M28 «Fastest Time» diverso dai beacon → avvertenza", any("dichiarato" in a for a in bugia.avvertenze),
     str(bugia.avvertenze))
conta = leggi_ldx(scrivi_ldx([0.0, 100.0], giri_totali=7))
test("M29 «Total Laps» incoerente con i beacon → avvertenza", any("Total Laps" in a for a in conta.avvertenze))
ok_err, msg = alza(LdxNonValido, leggi_ldx, b"<LDXFile><Layers>")
test("M30 XML rotto → errore dichiarato", ok_err, msg)
ok_err, msg = alza(LdxNonValido, leggi_ldx,
                   b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><LDXFile/>')
test("M31 DTD/entità rifiutate (niente espansioni)", ok_err and "DTD" in msg, msg)
ok_err, msg = alza(LdxNonValido, leggi_ldx, b"<Altro/>")
test("M32 radice diversa da LDXFile → errore", ok_err, msg)
test("M33 tempi in testo: «1:49.982», «48.711», spazzatura",
     (tempo_in_secondi("1:49.982"), tempo_in_secondi("48.711"), tempo_in_secondi("x"))
     == (109.982, 48.711, None))

# ---------------------------------------------------------------------------
print("\n─── Nome del file ───")
# ---------------------------------------------------------------------------
n = leggi_nome_file("Zolder-bmw_m4_gt3-5-2023.11.11-22.59.45.ld")
test("M34 pista, slug della vettura, numero e data dal nome",
     n is not None and (n.pista, n.vettura, n.numero, n.data_ora.isoformat())
     == ("Zolder", "bmw_m4_gt3", 5, "2023-11-11T22:59:45"), str(n))
n2 = leggi_nome_file("mount_panorama-mclaren_720s_gt3_evo-4-2023.11.25-10.21.46.ld")
test("M35 pista con trattino basso e vettura lunga",
     n2 is not None and (n2.pista, n2.vettura) == ("mount_panorama", "mclaren_720s_gt3_evo"), str(n2))
test("M36 nome non di ACC → None", leggi_nome_file("giro_veloce.ld") is None)

# ---------------------------------------------------------------------------
print("\n─── Registrazione completa (.ld + .ldx) ───")
# ---------------------------------------------------------------------------
cartella = pathlib.Path(tempfile.mkdtemp(prefix="pitwall_motec_"))
try:
    # Il nome finisce in «.06»: `with_suffix` lo mangerebbe, quindi si compone a mano.
    ld_path = cartella / "monza-bmw_m4_gt3-9-2023.11.28-09.57.06.ld"
    ldx_path = cartella / "monza-bmw_m4_gt3-9-2023.11.28-09.57.06.ldx"
    ld_path.write_bytes(LD)
    ldx_path.write_bytes(scrivi_ldx([0.5, 9.5]))
    r = leggi_registrazione(ld_path)
    test("M37 durata = canale più corto, giro completo dai beacon",
         abs(r.durata_s - DURATA) < 1e-9 and len(r.giri_completi) == 1
         and abs(r.giri_completi[0].durata_s - 9.0) < 1e-9, f"{r.durata_s} {r.giri_completi}")
    test("M38 slug della vettura dal nome del file", r.nome_file and r.nome_file.vettura == "bmw_m4_gt3")
    test("M39 registrazione coerente: nessuna avvertenza", r.avvertenze == [], str(r.avvertenze))

    ldx_path.write_bytes(scrivi_ldx([0.5, 9.5, 42.0]))
    r2 = leggi_registrazione(ld_path)
    test("M40 beacon oltre la fine dei canali → scartato e dichiarato",
         r2.ldx.beacon_s == [0.5, 9.5] and any("oltre la fine" in a for a in r2.avvertenze),
         f"{r2.ldx.beacon_s} {r2.avvertenze}")

    ldx_path.unlink()
    r3 = leggi_registrazione(ld_path)
    test("M41 senza .ldx: nessun giro inventato, e lo si dice",
         r3.giri_completi == [] and any("manca il .ldx" in a for a in r3.avvertenze), str(r3.avvertenze))

    corto = [CanaleFinto("SPEED", "m/s", 60, velocita),
             CanaleFinto("BRAKE", "%", 20, freno[:100])]
    ld_path.write_bytes(scrivi_ld(corto))
    r4 = leggi_registrazione(ld_path)
    test("M42 canali di durata diversa → avvertenza, durata = la più corta",
         abs(r4.durata_s - 5.0) < 1e-9 and any("durate diverse" in a for a in r4.avvertenze),
         f"{r4.durata_s} {r4.avvertenze}")
finally:
    shutil.rmtree(cartella, ignore_errors=True)

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Lettura dei file MoTeC conforme")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
