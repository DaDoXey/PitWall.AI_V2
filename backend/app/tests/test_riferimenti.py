"""
test_riferimenti.py — le tabelle per vettura estratte dal documento Kunos (L3)

Questi numeri non si possono «provare» contro il gioco (ACC non c'è su questo PC):
si può però provare che l'estrazione dal PDF non ha sbagliato a incolonnare, che è
il rischio vero di una tabella copiata da un documento. Quindi:

* valori attesi scritti a mano per un campione di vetture, presi rileggendo il PDF;
* coerenza interna (id unici, slug unici, nessun valore fuori scala);
* la promessa che le conversioni non verificate restino marcate tali;
* e che ogni vettura del catalogo o abbia riferimenti, o sia dichiarata scoperta.

Eseguire con (dalla cartella backend/):
    ./.venv/Scripts/python app/tests/test_riferimenti.py
"""

import json
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from app.core import riferimenti_acc as rif  # noqa: E402

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


tutte = rif.tutte()

print("\n─── Il file c'è ed è coerente ───")
test("R01 il documento contiene 43 vetture", len(tutte) == 43, f"{len(tutte)}")
test("R02 la fonte è dichiarata", "v1.8.12" in rif.fonte(), rif.fonte())
test("R03 ogni vettura ha uno slug non vuoto",
     all(v["acc_car_id"] for v in tutte))
test("R04 gli slug sono unici",
     len({v["acc_car_id"] for v in tutte}) == len(tutte))
test("R05 i carModelId sono unici",
     len({v["car_model_id"] for v in tutte}) == len(tutte))
test("R06 ogni vettura ha tutti e sei i riferimenti",
     all(all(k in v for k in ("car_model_id", "brake_bias_offset",
                              "brake_pressure_coeff_front",
                              "brake_pressure_coeff_rear",
                              "max_steering_angle_deg", "max_rpm"))
         for v in tutte))

print("\n─── Valori ricontrollati sul documento ───")
# Campione riletto a mano dalle appendici: se l'estrazione sballa di una riga,
# questi cadono tutti insieme.
attesi = {
    "porsche_991_gt3_r": dict(car_model_id=0, brake_bias_offset=-21,
                              max_steering_angle_deg=400, max_rpm=9250,
                              brake_pressure_coeff_front=7.1497,
                              brake_pressure_coeff_rear=6.7715),
    "mercedes_amg_gt3": dict(car_model_id=1, brake_bias_offset=-14,
                             max_steering_angle_deg=320, max_rpm=7900,
                             brake_pressure_coeff_front=7.9585,
                             brake_pressure_coeff_rear=7.9585),
    "bmw_m4_gt3": dict(car_model_id=30, brake_bias_offset=-14,
                       max_steering_angle_deg=270, max_rpm=7000,
                       brake_pressure_coeff_front=7.9585,
                       brake_pressure_coeff_rear=7.9585),
    "ferrari_488_gt3_evo": dict(car_model_id=24, brake_bias_offset=-17,
                                max_steering_angle_deg=240, max_rpm=7600,
                                brake_pressure_coeff_front=7.598,
                                brake_pressure_coeff_rear=7.4855),
    "maserati_mc_gt4": dict(car_model_id=58, brake_bias_offset=-15,
                            max_steering_angle_deg=450, max_rpm=7000,
                            brake_pressure_coeff_front=7.7768,
                            brake_pressure_coeff_rear=7.6142),
    "bmw_m2_cs_racing": dict(car_model_id=27, brake_bias_offset=-17,
                             max_steering_angle_deg=180, max_rpm=7520,
                             brake_pressure_coeff_front=7.2886,
                             brake_pressure_coeff_rear=10.0),
}
for slug, valori in attesi.items():
    trovata = rif.riferimenti(slug)
    if trovata is None:
        test(f"R07.{slug} presente nel documento", False, "non trovata")
        continue
    for chiave, atteso in valori.items():
        test(f"R07.{slug}.{chiave} = {atteso}", trovata[chiave] == atteso,
             f"trovato {trovata[chiave]}")

print("\n─── Ricerca per numero: il pezzo che mancava a L1 ───")
test("R08 carModelId 30 è la BMW M4 GT3",
     (rif.vettura_da_car_model_id(30) or {}).get("acc_car_id") == "bmw_m4_gt3")
test("R09 carModelId 0 è la Porsche 991 GT3 R",
     (rif.vettura_da_car_model_id(0) or {}).get("acc_car_id") == "porsche_991_gt3_r")
test("R10 un carModelId sconosciuto dà None, non una vettura a caso",
     rif.vettura_da_car_model_id(9999) is None)

print("\n─── Lista completa (handbook v1.10.2): anche le vetture del 2023-24 ───")
lista = rif.lista_completa()
test("R08b la lista ufficiale ha 54 vetture", len(lista) == 54, f"{len(lista)}")
test("R08c i carModelId della lista sono unici",
     len({v["car_model_id"] for v in lista}) == len(lista))
# Le cinque GT3 nuove: il documento della shared memory non le conosce, l'handbook sì.
nuove = {32: "ferrari_296_gt3", 33: "lamborghini_huracan_gt3_evo2",
         34: "porsche_992_gt3_r", 35: "mclaren_720s_gt3_evo", 36: "ford_mustang_gt3"}
for numero, slug in nuove.items():
    trovata = rif.vettura_da_car_model_id(numero) or {}
    test(f"R08d.{slug} carModelId {numero} → {slug}",
         trovata.get("acc_car_id") == slug, f"{trovata.get('acc_car_id')}")
    test(f"R08e.{slug} …dichiarata senza tabelle di conversione",
         trovata.get("riferimenti_completi") is False)
test("R08f le vetture delle appendici restano complete",
     (rif.vettura_da_car_model_id(30) or {}).get("riferimenti_completi") is True)
test("R08g la classe GT2 è nella lista, senza slug (catalogo non ancora esteso)",
     (rif.vettura_da_car_model_id(86) or {}).get("acc_car_id") is None
     and "935" in (rif.vettura_da_car_model_id(86) or {}).get("nome_handbook", ""))
test("R08h le stranezze di Kunos sono quelle attese",
     (rif.vettura_da_car_model_id(10) or {}).get("acc_car_id") == "nissan_gt_r_gt3_2017"
     and (rif.vettura_da_car_model_id(11) or {}).get("acc_car_id")
     == "bentley_continental_gt3_2016")

print("\n─── Il catalogo è allineato agli identificativi ufficiali ───")
catalogo_slug = {
    c["acc_car_id"]
    for c in json.loads(
        (BACKEND / "app" / "core" / "data" / "cars.json").read_text(encoding="utf-8")
    )
}
slug_ufficiali = {v["acc_car_id"] for v in lista if v["acc_car_id"]}
fuori_lista = sorted(catalogo_slug - slug_ufficiali)
test("R08i ogni vettura del catalogo usa uno slug ACC ufficiale",
     not fuori_lista, f"slug non ufficiali: {fuori_lista}")
test("R08j …e ognuna ha un carModelId",
     all(any(v["acc_car_id"] == s for v in lista) for s in catalogo_slug))
test("R11 uno slug sconosciuto dà None", rif.riferimenti("ferrari_296_gt3") is None)
test("R12 slug vuoto dà None", rif.riferimenti("") is None)
test("R13 la ricerca per slug non è sensibile alle maiuscole",
     (rif.riferimenti("BMW_M4_GT3") or {}).get("car_model_id") == 30)

print("\n─── Niente numeri fuori scala ───")
test("R14 gli offset del bias sono negativi e plausibili",
     all(-25 <= v["brake_bias_offset"] <= 0 for v in tutte))
test("R15 gli angoli di sterzo stanno fra 180 e 450 gradi",
     all(180 <= v["max_steering_angle_deg"] <= 450 for v in tutte))
test("R16 i giri massimi stanno fra 6000 e 9500",
     all(6000 <= v["max_rpm"] <= 9500 for v in tutte))
test("R17 i coefficienti dei freni stanno fra 6 e 10",
     all(6.0 <= v["brake_pressure_coeff_front"] <= 10.0
         and 6.0 <= v["brake_pressure_coeff_rear"] <= 10.0 for v in tutte))

print("\n─── Onestà dichiarata ───")
stato = rif.stato_conversioni()
test("R18 bias, pressione freni e sterzo sono marcati da verificare",
     all(stato[k]["stato"] == "da_verificare_in_gioco"
         for k in ("brake_bias", "brake_pressure", "steer_angle")), f"{stato}")
test("R19 i giri massimi sono l'unico valore diretto",
     stato["max_rpm"]["stato"] == "verificato_nel_documento")

catalogo = json.loads(
    (BACKEND / "app" / "core" / "data" / "cars.json").read_text(encoding="utf-8")
)
coperte = {v["acc_car_id"] for v in tutte}
dichiarate_scoperte = set(rif.vetture_senza_riferimenti())
non_dichiarate = [
    c["acc_car_id"] for c in catalogo
    if c["acc_car_id"] not in coperte and c["acc_car_id"] not in dichiarate_scoperte
]
test("R20 ogni vettura del catalogo è coperta o dichiarata scoperta",
     not non_dichiarate, f"né coperte né dichiarate: {non_dichiarate}")
test("R21 le vetture uscite dopo la 1.8.12 sono fra quelle dichiarate scoperte",
     {"ferrari_296_gt3", "ford_mustang_gt3", "porsche_992_gt3_r",
      "mclaren_720s_gt3_evo", "lamborghini_huracan_gt3_evo2"} <= dichiarate_scoperte,
     f"{sorted(dichiarate_scoperte)}")

# ---------------------------------------------------------------------------
# Riepilogo
# ---------------------------------------------------------------------------
passed = sum(1 for _, ok in results if ok)
total = len(results)
failed = [name for name, ok in results if not ok]

print("\n" + "═" * 60)
print(f"RISULTATI: {passed}/{total} test superati")
if not failed:
    print("✅ Riferimenti per vettura conformi")
else:
    print(f"❌ Test falliti ({len(failed)}):")
    for name in failed:
        print(f"   - {name}")
print("═" * 60)
sys.exit(1 if failed else 0)
