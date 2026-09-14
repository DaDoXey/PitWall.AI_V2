"""
test_adattatori.py — dai file di ACC al bundle (L1 · Fasi 2–3, Entry #032)

Controlla che gli adattatori leggano i file veri di ACC e che, davanti a un file
storto, dicano cosa non va invece di produrre un bundle a metà. Le fixture in
`fixtures/` hanno la struttura verificata su file reali il 14/09/2026 (valori
nostri), comprese le codifiche: ACC scrive i setup in UTF-8 e i risultati in
**UTF-16 LE senza BOM**.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_adattatori.py

Non richiede pytest, né rete, né chiave.
"""

import json
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))  # -> backend/

from app.bundle.adapters import (  # noqa: E402
    ResultsAccError,
    SetupAccError,
    decodifica,
    elenca_partecipanti,
    leggi_results_acc,
    leggi_setup_acc,
)
from app.bundle.schema import Fonte, Meta, SessionBundle, TipoSessione  # noqa: E402

FIX = pathlib.Path(__file__).parent / "fixtures"

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
    except (ValueError, OSError) as e:
        return str(e)
    return None


print("\n" + "═" * 60)
print("TEST — adattatori dei file di ACC")
print("═" * 60 + "\n")

# ---------------------------------------------------------------------------
# 1. Codifiche: il pezzo che fa fallire i parser scritti in fretta
# ---------------------------------------------------------------------------
test("A01 UTF-8 semplice", decodifica('{"a": 1}'.encode("utf-8")) == '{"a": 1}')
test("A02 UTF-8 con BOM", decodifica('{"a": 1}'.encode("utf-8-sig")) == '{"a": 1}')
test("A03 UTF-16 LE **senza BOM** (come i risultati di ACC)",
     decodifica('{"a": 1}'.encode("utf-16-le")) == '{"a": 1}')
test("A04 UTF-16 con BOM", decodifica('{"a": 1}'.encode("utf-16")) == '{"a": 1}')
test("A05 accenti e simboli restano intatti",
     decodifica("Nürburgring · 25.7 psi".encode("utf-16-le")) == "Nürburgring · 25.7 psi")

msg = errore(lambda: decodifica(b"\xff\xfe\xff\xff\x00"))
test("A06 byte non decodificabili danno un errore parlante", msg is not None)

# ---------------------------------------------------------------------------
# 2. Setup di ACC → bundle
# ---------------------------------------------------------------------------
s = leggi_setup_acc(FIX / "acc_setup_gt3.json")

test("A07 legge tutti e 49 i parametri del setup", len(s.valori) == 49, f"{len(s.valori)}")
test("A08 riconosce la vettura come slug del catalogo", s.car == "bmw_m4_gt3", str(s.car))
test("A09 il nome del setup viene dal nome del file", s.nome == "acc_setup_gt3", str(s.nome))

test("A10 le pressioni restano in click, senza inventare psi",
     s.valori["tire_press_fl"].raw == 54
     and s.valori["tire_press_fl"].reale is None
     and s.valori["tire_press_fl"].unita == "click")

c = s.valori["camber_fl"]
test("A11 il camber è in gradi perché li scrive ACC, ed è marcato verificato",
     c.reale == -4.23 and c.unita == "°" and c.verificato is True,
     f"{c.reale} {c.unita} {c.verificato}")
test("A12 anche il camber conserva il float grezzo di ACC",
     abs(float(c.raw) + 4.232851028442383) < 1e-9)
test("A13 il posteriore prende il suo valore, non quello anteriore",
     s.valori["camber_rl"].reale == -1.9, str(s.valori["camber_rl"].reale))

test("A14 quattro parametri su 49 sono in unità reali (i camber)",
     s.quanti_verificati() == (4, 49), str(s.quanti_verificati()))

test("A15 gli ammortizzatori vanno alla ruota giusta (FL/FR/RL/RR)",
     (s.valori["bump_fl"].raw, s.valori["bump_rl"].raw) == (15, 18))
test("A16 lento e veloce non si confondono",
     (s.valori["bump_fl"].raw, s.valori["fast_bump_fl"].raw) == (15, 20))
test("A17 rebound letto dalla sua chiave",
     (s.valori["rebound_rl"].raw, s.valori["fast_rebound_rl"].raw) == (24, 30))
test("A18 ala, splitter e condotti freni",
     (s.valori["wing"].raw, s.valori["splitter"].raw,
      s.valori["brake_duct_front"].raw, s.valori["brake_duct_rear"].raw) == (1, 0, 3, 2))
test("A19 preload dalla sezione drivetrain (minuscola nei file veri)",
     s.valori["preload"].raw == 10)
test("A20 barre antirollio anteriore e posteriore distinte",
     (s.valori["arb_front"].raw, s.valori["arb_rear"].raw) == (4, 1))
test("A21 elettronica: TC1, TC2, ABS, mappa motore",
     (s.valori["tc1"].raw, s.valori["tc2"].raw, s.valori["abs"].raw,
      s.valori["ecu_map"].raw) == (4, 0, 3, 0))
test("A22 il toe resta in click (toeOutLinear non è in gradi e non viene spacciato)",
     s.valori["toe_rl"].raw == 8 and s.valori["toe_rl"].verificato is False)

test("A23 il JSON originale resta intero dentro il bundle",
     s.raw["basicSetup"]["strategy"]["fuelPerLap"] > 3.5
     and s.raw["advancedSetup"]["mechanicalBalance"]["bumpStopRateDn"] == [0, 0, 10, 10])

# ---------------------------------------------------------------------------
# 3. Le assunzioni si dichiarano, non si nascondono
# ---------------------------------------------------------------------------
test("A24 l'ordine dell'array rideHeight è dichiarato come assunzione",
     any("rideHeight" in a for a in s.assunzioni), str(s.assunzioni))
test("A25 l'uso di bumpStopRateUp è dichiarato",
     any("bumpStopRateUp" in a for a in s.assunzioni))
test("A26 con casterLF ≠ casterRF lo dice (23 e 22 nella fixture)",
     any("caster" in a for a in s.assunzioni))
test("A27 le assunzioni sono tre, non una lista che cresce a caso",
     len(s.assunzioni) == 3, str(len(s.assunzioni)))

# ---------------------------------------------------------------------------
# 4. File storti: errore chiaro, mai un bundle a metà
# ---------------------------------------------------------------------------
s16 = leggi_setup_acc(FIX / "acc_setup_gt3_utf16.json")
test("A28 lo stesso setup in UTF-16 dà lo stesso risultato",
     s16.valori["tire_press_fl"].raw == 54 and len(s16.valori) == 49)

msg = errore(lambda: leggi_setup_acc(FIX / "non_un_setup.json"))
test("A29 un JSON che non è un setup viene rifiutato con il motivo",
     msg is not None and "basicSetup" in msg, msg or "nessun errore")

msg = errore(lambda: leggi_setup_acc(FIX / "setup_rotto.json"))
test("A30 un file troncato viene rifiutato come JSON non valido",
     msg is not None and "JSON" in msg, msg or "nessun errore")

msg = errore(lambda: leggi_setup_acc(FIX / "manca_del_tutto.json"))
test("A31 un file inesistente dà un errore leggibile, non un traceback",
     msg is not None and "non leggibile" in msg, msg or "nessun errore")

msg = errore(lambda: leggi_setup_acc(b"   "))
test("A32 un file vuoto viene rifiutato", msg is not None and "vuoto" in msg,
     msg or "nessun errore")

parziale = leggi_setup_acc(FIX / "acc_setup_solo_base.json")
test("A33 un setup con la sola sezione base viene letto per quel che c'è",
     0 < len(parziale.valori) < 49 and parziale.car == "porsche_991ii_gt3_r",
     f"{len(parziale.valori)} parametri")
test("A34 i parametri assenti non vengono inventati a zero",
     "preload" not in parziale.valori and "wing" not in parziale.valori)

msg = errore(lambda: leggi_setup_acc(json.dumps({"basicSetup": {}}).encode("utf-8")))
test("A35 un setup senza nemmeno un parametro leggibile viene rifiutato",
     msg is not None and "parametro" in msg, msg or "nessun errore")

test("A36 si può leggere anche dai soli byte, senza passare dal disco",
     leggi_setup_acc((FIX / "acc_setup_gt3.json").read_bytes(), nome="da byte").nome == "da byte")

# ---------------------------------------------------------------------------
# 5. Il setup entra in un bundle e ci resta
# ---------------------------------------------------------------------------
b = SessionBundle(meta=Meta(fonte=Fonte.ACC_SETUP, car=s.car, track="monza"), setup=s)
riletto = SessionBundle.from_json(b.to_json())
test("A37 il bundle con il setup sopravvive a salvataggio e rilettura",
     riletto.setup.valori["camber_fl"].reale == -4.23
     and riletto.setup.raw["carName"] == "bmw_m4_gt3")
test("A38 anche le assunzioni sopravvivono al salvataggio",
     len(riletto.setup.assunzioni) == 3)
test("A39 un bundle di solo setup ha dati utili", riletto.ha_dati_utili() is True)

# ---------------------------------------------------------------------------
# 6. Risultati di ACC → bundle (Fase 3)
# ---------------------------------------------------------------------------
b = leggi_results_acc(FIX / "acc_results_gioco_prove.json", track="monza")

test("A40 legge i giri dal file del gioco (UTF-16 senza BOM)", len(b.giri) == 4, f"{len(b.giri)}")
test("A41 i tempi restano in millisecondi", b.giri[1].tempo_ms == 103377)
test("A42 i tre settori arrivano interi", b.giri[1].splits_ms == [26127, 40497, 36753])
test("A43 i giri sono numerati da 1 in ordine di tempo", [g.numero for g in b.giri] == [1, 2, 3, 4])
test("A44 il tipo sessione numerico diventa leggibile (0 = prove)",
     b.meta.tipo_sessione is TipoSessione.PROVE, str(b.meta.tipo_sessione))
test("A45 le condizioni vengono da trackStatus", b.meta.condizioni.grip_linea_ideale == 0.96)
test("A46 la sessione asciutta è dichiarata tale", b.meta.condizioni.pista_bagnata is False)
test("A47 la durata della sessione viene letta", b.meta.durata_s == 1800)
test("A48 il pilota viene dalla classifica", b.meta.pilota == "Edoardo Ferlito", str(b.meta.pilota))
test("A49 il circuito assente nel file lo fornisce chi importa", b.meta.track == "monza")
test("A50 la fonte è dichiarata", b.meta.fonte is Fonte.ACC_RESULTS)

test("A51 il carburante residuo viene letto", b.giri[1].carburante_residuo_l == 80.4)
test("A52 il consumo è la differenza fra due giri consecutivi",
     b.giri[1].carburante_usato_l == 3.6, str(b.giri[1].carburante_usato_l))
test("A53 il primo giro non ha un consumo da calcolare",
     b.giri[0].carburante_usato_l is None)
test("A54 dopo un rifornimento non si inventa un consumo negativo",
     b.giri[3].carburante_usato_l is None)
test("A55 i flags di ACC si conservano senza essere interpretati",
     b.giri[2].flags_acc == 4 and b.giri[2].valido is True)
test("A56 e l'app dichiara di non saper giudicare la validità",
     any("validità" in a for a in b.assunzioni), str(b.assunzioni))

# Gara con più vetture: niente indovinelli
partecipanti = elenca_partecipanti(FIX / "acc_results_gioco_gara.json")
test("A57 elenca tutte le vetture del file", len(partecipanti) == 3, str(len(partecipanti)))
test("A58 di ognuna dà pilota, numero e giri fatti",
     partecipanti[1].pilota == "Mirko Bianchi" and partecipanti[1].giri == 2
     and partecipanti[1].numero == 63)

msg = errore(lambda: leggi_results_acc(FIX / "acc_results_gioco_gara.json"))
test("A59 con più vetture non ne sceglie una a caso: chiede quale",
     msg is not None and "3 vetture" in msg, msg or "nessun errore")

g = leggi_results_acc(FIX / "acc_results_gioco_gara.json", car_id=3)
test("A60 scelta per car_id: prende solo i giri di quella vettura", len(g.giri) == 2)
test("A61 e la sua vettura numerica", g.meta.car_model_id == 4, str(g.meta.car_model_id))

g = leggi_results_acc(FIX / "acc_results_gioco_gara.json", player_id="S300")
test("A62 scelta per player_id: trova la vettura del pilota",
     g.meta.pilota == "Luca Verdi" and len(g.giri) == 1, str(g.meta.pilota))

msg = errore(lambda: leggi_results_acc(FIX / "acc_results_gioco_gara.json", car_id=99))
test("A63 un car_id inesistente elenca quelli disponibili",
     msg is not None and "non presente" in msg, msg or "nessun errore")

msg = errore(lambda: leggi_results_acc(FIX / "acc_results_gioco_gara.json", player_id="nessuno"))
test("A64 un player_id inesistente lo dice", msg is not None, "nessun errore")

test("A65 col carburante costante non calcola consumi e lo dichiara",
     all(gi.carburante_usato_l is None for gi in g.giri)
     and any("carburante" in a for a in g.assunzioni))
test("A66 il tipo gara (10) viene riconosciuto", g.meta.tipo_sessione is TipoSessione.GARA)
test("A67 senza circuito indicato lo dichiara mancante invece di inventarlo",
     g.meta.track is None and any("circuito" in a for a in g.assunzioni))

# File del server dedicato: schema diverso, stesso bundle
srv = leggi_results_acc(FIX / "acc_results_server.json")
test("A68 legge anche il formato del server dedicato", len(srv.giri) == 2)
test("A69 dal server il circuito c'è davvero", srv.meta.track == "brands_hatch")
test("A70 il tipo sessione testuale ('R') diventa gara",
     srv.meta.tipo_sessione is TipoSessione.GARA)
test("A71 usa isValidForBest quando c'è: il giro tagliato è invalido",
     srv.giri[0].valido is False and srv.giri[1].valido is True)
test("A72 quindi i giri validi sono uno solo", len(srv.giri_validi) == 1)
test("A73 la sessione bagnata del server viene letta",
     srv.meta.condizioni.pista_bagnata is True)
test("A74 senza carburante nel file non si inventa nulla",
     all(gi.carburante_residuo_l is None for gi in srv.giri))

# I server numerano le sessioni ripetute: "Q2" è pur sempre una qualifica
# (trovato su un file reale di simresults il 14/09).
from app.bundle.adapters.acc_results import _tipo_sessione  # noqa: E402

test("A74b 'Q2' resta una qualifica, non una sessione sconosciuta",
     _tipo_sessione({"sessionType": "Q2"}, False) is TipoSessione.QUALIFICA)
test("A74c 'FP1' resta prove libere",
     _tipo_sessione({"sessionType": "FP1"}, False) is TipoSessione.PROVE)
test("A74d una sigla davvero ignota resta sconosciuta, non viene forzata",
     _tipo_sessione({"sessionType": "XYZ"}, False) is TipoSessione.SCONOSCIUTO)

# File storti
msg = errore(lambda: leggi_results_acc(FIX / "acc_results_senza_giri.json"))
test("A75 un file senza giri viene rifiutato", msg is not None, "nessun errore")

msg = errore(lambda: leggi_results_acc(FIX / "acc_setup_gt3.json"))
test("A76 un setup dato per errore all'import dei risultati viene rifiutato",
     msg is not None and "risultati" in msg, msg or "nessun errore")

msg = errore(lambda: leggi_results_acc(FIX / "setup_rotto.json"))
test("A77 un file troncato viene rifiutato", msg is not None)

riletto = SessionBundle.from_json(b.to_json())
test("A78 il bundle dei risultati sopravvive a salvataggio e rilettura",
     riletto.giri[1].tempo_ms == 103377 and len(riletto.assunzioni) == len(b.assunzioni))

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Adattatori conformi")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
