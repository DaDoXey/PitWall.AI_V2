#!/usr/bin/env python3
"""
lotto_2_vetture.py — le 23 vetture non GT3 di ACC nel catalogo (Lotto 2, Entry #064)

Perché esiste:
    Il Lotto 1 ha portato in `cars.json` le 31 GT3. Restavano le altre 23 vetture del
    gioco: 11 GT4, 6 GT2, 5 monomarca (GTC) e la BMW M2 CS Racing (TCX). La ricerca
    è stata fatta l'01/10/2026 (scelta di Edoardo: «falla te la ricerca») e sta tutta
    qui sotto, con le fonti accanto a ogni vettura: lo script è la consegna.

Cosa fa:
    * aggiunge le 23 voci in coda a `app/core/data/cars.json` (stesso schema delle GT3);
    * aggancia le 23 righe di `acc_lista_vetture_handbook.json` al catalogo (slug e id);
    * dichiara le 6 GT2 fra le vetture senza riferimenti in `acc_riferimenti_vetture.json`
      (il documento della shared memory si ferma alla 1.8.12: mancanti, mai stimate).

Regole dei dati:
    * gli slug `acc_car_id` sono i carName di ACC, da Race Element
      (`Race_Element.Data.ACC/SetupParser/ConversionFactory.cs`);
    * potenza e peso sono quelli dichiarati dal costruttore o dalla fonte indicata; dove
      la fonte dà una forbice (BoP) c'è il valore più alto e la forbice sta in `nota`;
    * un dato senza fonte resta `null` e la vettura è `confidence: "da_verificare"`;
    * `has_tc` / `has_abs` sono `null` quando nessuna fonte dice com'è la vettura in ACC;
    * le didascalie riportano tratti di guida solo dove una fonte li descrive
      (`caption_fonte`); altrimenti dicono com'è fatta la vettura, e basta.

Uso (dalla cartella backend/):
    ./.venv/Scripts/python scripts/consegne/lotto_2_vetture.py --prova   # non scrive
    ./.venv/Scripts/python scripts/consegne/lotto_2_vetture.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = Path(__file__).resolve().parents[2]
CATALOGO = BACKEND / "app" / "core" / "data" / "cars.json"
HANDBOOK = BACKEND / "app" / "core" / "data" / "acc_lista_vetture_handbook.json"
RIFERIMENTI = BACKEND / "app" / "core" / "data" / "acc_riferimenti_vetture.json"

CDA_GT4 = "https://coachdaveacademy.com/tutorials/what-is-the-fastest-gt4-car-in-acc/"
CDA_MONO = "https://coachdaveacademy.com/tutorials/the-ultimate-guide-to-acc-single-make-cars/"
CDA_CHALL = "https://coachdaveacademy.com/tutorials/acc-challengers-pack"
CDA_GT2 = "https://coachdaveacademy.com/announcements/everything-you-need-to-know-about-the-acc-gt2-pack-dlc/"
SOLO_DATI = "dai dati tecnici: nessuna fonte letta descrive come si guida in ACC"

GT4, CHALL, GT2P = "GT4 Pack", "Challengers Pack", "GT2 Pack"

# (id, acc_car_id, car_model_id, brand, model, anno, classe, dlc_pack,
#  motore, cv, kg, cambio, confidence, nota, tc, abs, didascalia, fonte_didascalia, fonti, commons)
VETTURE = [
    # ───────────── GT4 (GT4 Pack, 15/07/2020) ─────────────
    ("alpine_a110_gt4", "alpine_a110_gt4", 50, "Alpine", "A110 GT4", 2018, "GT4", GT4,
     "1.8L 4 cilindri turbo", 400, 1080, "6 marce sequenziale", "media",
     "potenza 350–400 CV a seconda del BoP; peso dichiarato per la A110 GT4+", None, None,
     "Motore centrale, quattro cilindri 1.8 turbo e poco più di mille chili: è fra le più leggere della classe "
     "e fra le meno potenti. Sulla carta paga in rettilineo contro le V8 e rende dove conta il peso.",
     SOLO_DATI, ["https://www.alpine-cars.co.uk/competition/a110-gt4.html"], "Alpine A110 GT4"),
    ("aston_martin_vantage_gt4", "amr_v8_vantage_gt4", 51, "Aston Martin", "V8 Vantage GT4", 2018, "GT4", GT4,
     "4.0L V8 biturbo", None, None, None, "da_verificare",
     "potenza, peso e cambio della versione GT4 non trovati in una fonte del costruttore (omologata a marzo 2019)",
     None, None,
     "V8 4.0 biturbo davanti e trazione dietro. È la più stabile della classe in quasi ogni situazione e ha "
     "una delle frenate migliori del gruppo.",
     CDA_GT4, [CDA_GT4, "https://www.motorauthority.com/news/1117230_aston-martin-vantage-gt3-and-gt4-customer-race-cars-revealed"],
     "Aston Martin Vantage GT4"),
    ("audi_r8_lms_gt4", "audi_r8_gt4", 52, "Audi", "R8 LMS GT4", 2018, "GT4", GT4,
     "5.2L V10 aspirato", 495, 1460, "7 marce doppia frizione (S tronic)", "media",
     "fino a 495 CV a seconda del BoP; 1460 kg è il peso di omologazione", None, None,
     "V10 aspirato 5.2 in posizione centrale, trazione posteriore e cambio a doppia frizione di serie. "
     "È la GT4 più pesante fra quelle con il peso dichiarato: 1460 kg di omologazione.",
     SOLO_DATI, ["https://www.audi.com/en/sport/motorsport/audi-sport-customer-racing/r8-lms-gt4.html"], "Audi R8 LMS GT4"),
    ("bmw_m4_gt4", "bmw_m4_gt4", 53, "BMW", "M4 GT4", 2018, "GT4", GT4,
     "3.0L 6 cilindri in linea biturbo", 431, 1430, "7 marce doppia frizione", "media",
     "«più di 431 CV» secondo BMW; il valore in gara dipende dal BoP", None, None,
     "Sei cilindri in linea biturbo davanti, come la sorella GT3, e gli stessi punti di forza: forte sui "
     "cordoli e ben bilanciata. Le manca un po' di finezza rispetto alla Porsche 718 Cayman.",
     "https://coachdaveacademy.com/tutorials/under-the-hood-tips-and-tricks-to-driving-bmw-m4-gt4/",
     ["https://www.goodingco.com/lot/2018-bmw-m4-gt4", "https://coachdaveacademy.com/tutorials/under-the-hood-tips-and-tricks-to-driving-bmw-m4-gt4/"],
     "BMW M4 GT4"),
    ("chevrolet_camaro_gt4r", "chevrolet_camaro_gt4r", 55, "Chevrolet", "Camaro GT4.R", 2017, "GT4", GT4,
     "6.2L V8 aspirato", 480, 1429, "6 marce sequenziale", "media",
     "le fonti danno fra 420 e 480 CV; peso 3150 libbre", None, None,
     "V8 aspirato 6.2 di grande cilindrata davanti, costruita da Pratt & Miller, la stessa officina delle "
     "Corvette da corsa. Cambio sequenziale Xtrac a sei marce.",
     SOLO_DATI, ["https://www.topgear.com/car-news/motorsport/gt4r-racecar-ps190k-chevrolet-camaro",
                 "https://www.digitaltrends.com/cars/chevrolet-camaro-gt4r/"], "Chevrolet Camaro GT4.R"),
    ("ginetta_g55_gt4", "ginetta_g55_gt4", 56, "Ginetta", "G55 GT4", 2012, "GT4", GT4,
     "3.7L V6 aspirato", 370, 1085, "6 marce sequenziale", "media",
     "370 CV secondo Wikipedia, 385 secondo altre fonti", None, None,
     "La più anziana della classe: V6 Ford 3.7 aspirato e 1085 kg, con un cambio Hewland sequenziale. "
     "Leggera quanto l'Alpine, ma con il motore davanti.",
     SOLO_DATI, ["https://en.wikipedia.org/wiki/Ginetta_G55"], "Ginetta G55"),
    ("ktm_xbow_gt4", "ktm_xbow_gt4", 57, "KTM", "X-Bow GT4", 2016, "GT4", GT4,
     "2.0L 4 cilindri turbo", 360, 999, "6 marce sequenziale", "media",
     "320 CV al debutto, 360 nelle versioni successive", None, None,
     "Monoscocca in carbonio, quattro cilindri 2.0 turbo di origine Audi dietro il pilota e 999 kg: è la "
     "più leggera della classe. Sviluppata da KTM con Reiter Engineering.",
     SOLO_DATI, ["https://en.wikipedia.org/wiki/KTM_X-Bow",
                 "https://autoindustriya.com/racing-news/ktm-x-bow-gt4-fitted-with-320-ps-2-liter-tfsi-engine.html"], "KTM X-Bow GT4"),
    ("maserati_granturismo_mc_gt4", "maserati_mc_gt4", 58, "Maserati", "GranTurismo MC GT4", 2016, "GT4", GT4,
     "4.7L V8 aspirato", 430, 1410, "6 marce a comando elettroidraulico", "media",
     "430 CV con la strozzatura GT4 (488 senza)", None, None,
     "Gran turismo a motore anteriore: V8 aspirato 4.7 e cambio al retrotreno, in schema transaxle. "
     "È fra le più pesanti della classe.",
     SOLO_DATI, ["https://racer.com/2015/12/09/maserati-reveals-gt4-granturismo-mc/"], "Maserati GranTurismo MC GT4"),
    ("mclaren_570s_gt4", "mclaren_570s_gt4", 59, "McLaren", "570S GT4", 2016, "GT4", GT4,
     "3.8L V8 biturbo", None, None, "7 marce doppia frizione", "da_verificare",
     "potenza e peso in assetto GT4 non trovati in una fonte del costruttore (le fonti lette riportano i dati stradali)",
     None, None,
     "Monoscocca in carbonio e V8 3.8 biturbo in posizione centrale, con il cambio a sette marce della "
     "versione stradale.",
     SOLO_DATI, ["https://cars.mclaren.com/customer-racing/models/570s-gt4"], "McLaren 570S GT4"),
    ("mercedes_amg_gt4", "mercedes_amg_gt4", 60, "Mercedes-AMG", "AMG GT4", 2016, "GT4", GT4,
     "4.0L V8 biturbo", 476, 1390, "6 marce sequenziale", "media",
     "fino a 476 CV al lancio (350 kW); le versioni successive arrivano a 510", None, None,
     "V8 4.0 biturbo davanti e cambio sequenziale al retrotreno. Dà il meglio sulle piste veloci come Monza "
     "e Indianapolis: ottima velocità in rettilineo e buona stabilità.",
     "https://coachdaveacademy.com/tutorials/under-the-hood-tips-and-tricks-to-driving-the-mercedes-amg-gt4/",
     ["https://justcars.com.au/news-and-reviews/mercedes-amg-gt4-revealed/13832",
      "https://coachdaveacademy.com/tutorials/under-the-hood-tips-and-tricks-to-driving-the-mercedes-amg-gt4/"], "Mercedes-AMG GT4"),
    ("porsche_718_cayman_gt4_clubsport", "porsche_718_cayman_gt4_mr", 61, "Porsche", "718 Cayman GT4 Clubsport", 2019, "GT4", GT4,
     "3.8L 6 cilindri boxer aspirato", 425, 1320, "6 marce doppia frizione (PDK)", "alta",
     None, None, None,
     "Il riferimento della classe: sei cilindri boxer aspirato in posizione centrale. Consuma poco le gomme "
     "e ha un telaio che lascia ruotare la vettura in inserimento con fiducia: i suoi stint sono fra i più lunghi.",
     CDA_GT4, ["https://motorsports.porsche.com/usa/en/category/cars/718-cayman-gt4-clubsport", CDA_GT4],
     "Porsche 718 Cayman GT4 Clubsport"),

    # ───────────── Monomarca (GTC) ─────────────
    ("porsche_911_gt3_cup_991", "porsche_991ii_gt3_cup", 9, "Porsche", "911 GT3 Cup (991.2)", 2017, "GTC", None,
     "4.0L 6 cilindri boxer aspirato", 485, 1200, "6 marce sequenziale", "media",
     None, False, False,
     "La 911 della Carrera Cup: sei cilindri boxer 4.0 aspirato a sbalzo dietro, senza controllo di trazione "
     "e senza ABS. È molto difficile da tenere: gas e freno vanno dosati dal pilota, senza rete.",
     CDA_CHALL, ["https://www.goodingco.com/lot/2017-porsche-991-gt3-cup", CDA_CHALL, CDA_MONO], "Porsche 911 GT3 Cup 991"),
    ("porsche_911_gt3_cup_992", "porsche_992_gt3_cup", 28, "Porsche", "911 GT3 Cup (992)", 2021, "GTC", CHALL,
     "4.0L 6 cilindri boxer aspirato", 510, 1260, "6 marce sequenziale", "alta",
     None, False, True,
     "La Cup della generazione 992: 510 CV, niente controllo di trazione e, per la prima volta su una Cup, "
     "l'ABS. Poca aerodinamica: il gas va aperto con dolcezza, ed è un po' più gentile della 991.2.",
     CDA_MONO, ["https://download.newsroom.porsche.com/dam/jcr:584909f3-fb23-4181-b134-ab56d3ba3153/PI20201212e_TechSpecs_Porsche%20911%20GT3%20Cup.pdf",
                CDA_MONO, CDA_CHALL], "Porsche 911 GT3 Cup 992"),
    ("lamborghini_huracan_super_trofeo", "lamborghini_huracan_st", 18, "Lamborghini", "Huracán Super Trofeo", 2015, "GTC", None,
     "5.2L V10 aspirato", 620, 1270, "6 marce sequenziale", "media",
     "1270 kg è il peso a secco", None, None,
     "La Huracán del monomarca Lamborghini: V10 aspirato 5.2 da 620 CV e sola trazione posteriore. "
     "Peso a secco 1270 kg, con il 58% sul retrotreno.",
     SOLO_DATI, ["https://www.supercars.net/blog/2015-lamborghini-huracan-lp-620-2-super-trofeo/"], "Lamborghini Huracán Super Trofeo"),
    ("lamborghini_huracan_super_trofeo_evo2", "lamborghini_huracan_st_evo2", 29, "Lamborghini", "Huracán Super Trofeo EVO2", 2021, "GTC", CHALL,
     "5.2L V10 aspirato", 620, None, "6 marce sequenziale", "media",
     "peso della EVO2 non dichiarato nelle fonti lette", None, None,
     "Più facile della Porsche Cup e più veloce sul giro. Ha meno aderenza di una GT3 in curva ma è molto più "
     "rapida in rettilineo; tende al sovrasterzo in inserimento e a centro curva.",
     CDA_MONO, ["https://www.goodingco.com/lot/2021-lamborghini-huracan-super-trofeo-evo2", CDA_MONO, CDA_CHALL],
     "Lamborghini Huracán Super Trofeo EVO2"),
    ("ferrari_488_challenge_evo", "ferrari_488_challenge_evo", 26, "Ferrari", "488 Challenge Evo", 2020, "GTC", CHALL,
     "3.9L V8 biturbo", 670, 1280, "7 marce doppia frizione", "media",
     None, None, None,
     "La 488 del Ferrari Challenge: 670 CV e meno carico di una GT3. Nelle curve medie e veloci va alzato il "
     "piede, ma in rettilineo è 10–15 km/h più veloce della GT3; sul giro sta fra le GT3 e le Super Trofeo.",
     CDA_MONO, ["https://www.conceptcarz.com/s30204/ferrari-488-challenge-evo.aspx", CDA_MONO, CDA_CHALL], "Ferrari 488 Challenge Evo"),

    # ───────────── TCX ─────────────
    ("bmw_m2_cs_racing", "bmw_m2_cs_racing", 27, "BMW", "M2 CS Racing", 2020, "TCX", CHALL,
     "3.0L 6 cilindri in linea biturbo", 365, 1544, "7 marce doppia frizione", "media",
     "280–365 CV a seconda del BoP; peso 3405 libbre secondo Coach Dave Academy", None, True,
     "La più lenta e la più prevedibile del gioco, quindi la più adatta a chi comincia. Ha meno carico "
     "aerodinamico di ogni altra vettura di ACC e tende al sovrasterzo in accelerazione.",
     CDA_MONO, ["https://www.bmwblog.com/2019/12/11/bmw-m2-cs-racing-all-the-technical-specs/", CDA_MONO, CDA_CHALL], "BMW M2 CS Racing"),

    # ───────────── GT2 (GT2 Pack, 24/01/2024) ─────────────
    ("audi_r8_lms_gt2", "audi_r8_lms_gt2", 80, "Audi", "R8 LMS GT2", 2021, "GT2", GT2P,
     "5.2L V10 aspirato", 640, 1350, None, "media",
     "cambio non indicato nelle fonti lette", True, True,
     "V10 aspirato da 640 CV. Brilla per prontezza e per il rendimento nelle curve lente, e si guida in modo "
     "simile alle altre Audi di ACC.",
     CDA_GT2, ["https://www.audi.com/en/audi-r8-lms-gt2-2020-12841/technical-data-audi-r8-lms-gt2-12845", CDA_GT2], "Audi R8 LMS GT2"),
    ("ktm_xbow_gt2", "ktm_xbow_gt2", 82, "KTM", "X-Bow GT2", 2021, "GT2", GT2P,
     "2.5L 5 cilindri turbo", 600, 1048, "6 marce sequenziale", "alta",
     "1048 kg senza carburante", True, True,
     "La leggera della classe: cinque cilindri 2.5 turbo di origine Audi da 600 CV su poco più di mille chili. "
     "Agile ed estremamente efficace in frenata.",
     CDA_GT2, ["https://www.ktm.com/en-th/models/x-bow/x-bow-gt2-2020/technical-specifications.html", CDA_GT2], "KTM X-Bow GT2"),
    ("maserati_mc20_gt2", "maserati_mc20_gt2", 83, "Maserati", "MC20 GT2", 2023, "GT2", GT2P,
     "3.0L V6 biturbo", 621, None, "6 marce sequenziale", "media",
     "peso a secco non dichiarato: lo fissa il BoP", True, True,
     "V6 Nettuno 3.0 biturbo da 621 CV su monoscocca in carbonio. Ruota con facilità in inserimento: è "
     "agile, e proprio per questo va gestita con attenzione.",
     CDA_GT2, ["https://www.motor1.com/news/674564/maserati-gt2-debut-specs/", CDA_GT2], "Maserati MC20 GT2"),
    ("mercedes_amg_gt2", "mercedes_amg_gt2", 84, "Mercedes-AMG", "AMG GT2", 2023, "GT2", GT2P,
     "4.0L V8 biturbo", 707, 1400, "6 marce sequenziale", "media",
     "meno di 1400 kg", True, True,
     "La più potente: V8 4.0 biturbo da 707 CV davanti. Ha il vantaggio in rettilineo e paga in "
     "maneggevolezza, per via del motore anteriore.",
     CDA_GT2, ["https://www.motor1.com/news/625616/mercedes-amg-gt2-race-car/", CDA_GT2], "Mercedes-AMG GT2"),
    ("porsche_911_gt2_rs_clubsport_evo", "porsche_991_gt2_rs_mr", 85, "Porsche", "911 GT2 RS Clubsport Evo", 2023, "GT2", GT2P,
     "3.8L 6 cilindri boxer biturbo", 700, 1390, "7 marce doppia frizione (PDK)", "media",
     "dati della 911 GT2 RS Clubsport, su cui la Evo si basa", True, True,
     "Sei cilindri boxer 3.8 biturbo da 700 CV: una delle GT2 più veloci in rettilineo. Pacchetto equilibrato, "
     "con il carattere tipico della 911.",
     CDA_GT2, ["https://motorsports.porsche.com/international/en/category/cars/911-gt2-rs-clubsport", CDA_GT2], "Porsche 911 GT2 RS Clubsport"),
    ("porsche_935", "porsche_935", 86, "Porsche", "935", 2019, "GT2", GT2P,
     "3.8L 6 cilindri boxer biturbo", 700, 1380, "7 marce doppia frizione (PDK)", "alta",
     None, True, True,
     "L'omaggio alla 935/78 «Moby Dick», costruito in 77 esemplari sulla base della 911 GT2 RS: 700 CV e "
     "1380 kg. Resta veloce nonostante l'età e si guida in modo simile alla GT2 RS Clubsport.",
     CDA_GT2, ["https://newsroom.porsche.com/en_AU/motorsports/media-guide/race-cars/porsche-935-2019.html", CDA_GT2], "Porsche 935 (2019)"),
]

LOGHI = {
    "Alpine": "Category:Alpine (automobile) logos", "Aston Martin": "Category:Aston Martin logos",
    "Audi": "Category:Audi logos", "BMW": "Category:BMW logos", "Chevrolet": "Category:Chevrolet logos",
    "Ginetta": "Category:Ginetta", "KTM": "Category:KTM logos", "Maserati": "Category:Maserati logos",
    "McLaren": "Category:McLaren logos", "Mercedes-AMG": "Category:Mercedes-AMG logos",
    "Porsche": "Category:Porsche logos", "Lamborghini": "Category:Lamborghini logos",
    "Ferrari": "Category:Ferrari logos",
}


def voce(v) -> dict:
    (id_, acc, _cmid, brand, model, anno, classe, pack, motore, cv, kg, cambio, conf, nota,
     tc, abs_, didascalia, fonte_did, fonti, commons) = v
    specs = {"engine": motore, "power_hp": cv, "weight_kg": kg, "drivetrain": "RWD", "gearbox": cambio,
             "bop_variable": True, "confidence": conf}
    if nota:
        specs["nota"] = nota
    return {
        "id": id_, "acc_car_id": acc, "brand": brand, "model": model, "year": anno,
        "category": classe, "gt3_generation": None,
        "dlc": pack is not None, "dlc_pack": pack,
        "specs": specs,
        "has_tc": tc, "has_abs": abs_,
        "setup_ranges_ref": id_,
        "caption_it": didascalia,
        "caption_fonte": fonte_did,
        "fonti": fonti,
        "assets": {
            "logo": {"commons_query": f"{brand} logo", "commons_category": LOGHI[brand],
                     "preferred_format": "svg", "license_expected": "PD-textlogo o marchio registrato",
                     "status": "da_risolvere"},
            "photo": {"commons_query": commons, "commons_category": f"Category:{commons}",
                      "preferred_format": "jpg", "license_expected": "CC BY-SA (da confermare)",
                      "status": "da_risolvere"},
        },
    }


def riscrivi(percorso: Path, dati, originale: str) -> str:
    testo = json.dumps(dati, ensure_ascii=False, indent=2) + ("\n" if originale.endswith("\n") else "")
    return testo.replace("\n", "\r\n") if "\r\n" in originale else testo


def main() -> int:
    prova = "--prova" in sys.argv
    grezzo_cat = open(CATALOGO, encoding="utf-8", newline="").read()
    catalogo = json.loads(grezzo_cat)
    grezzo_hb = open(HANDBOOK, encoding="utf-8", newline="").read()
    handbook = json.loads(grezzo_hb)

    # I due file devono riscriversi identici prima di toccarli: il diff sarà solo l'aggiunta.
    for nome, dati, grezzo in (("cars.json", catalogo, grezzo_cat), ("handbook", handbook, grezzo_hb)):
        if riscrivi(Path(), dati, grezzo) != grezzo:
            print(f"{nome}: il formato non si riproduce identico, mi fermo")
            return 1

    # Le GT2 non sono nelle appendici della shared memory: vanno dichiarate scoperte.
    grezzo_rif = open(RIFERIMENTI, encoding="utf-8", newline="").read()
    riferimenti = json.loads(grezzo_rif)
    if riscrivi(Path(), riferimenti, grezzo_rif) != grezzo_rif:
        print("riferimenti: il formato non si riproduce identico, mi fermo")
        return 1
    coperte = {v["acc_car_id"] for v in riferimenti["vetture"]}
    scoperte = riferimenti["vetture_del_catalogo_senza_riferimenti"]
    da_dichiarare = [v[1] for v in VETTURE if v[1] not in coperte and v[1] not in scoperte]
    if da_dichiarare:
        riferimenti["vetture_del_catalogo_senza_riferimenti"] = sorted(scoperte + da_dichiarare)
        print("dichiarate senza riferimenti:", da_dichiarare)
        if not prova:
            open(RIFERIMENTI, "w", encoding="utf-8", newline="").write(riscrivi(Path(), riferimenti, grezzo_rif))

    presenti = {c["id"] for c in catalogo} | {c["acc_car_id"] for c in catalogo}
    nuove = [voce(v) for v in VETTURE]
    assert len(nuove) == 23 and len({n["id"] for n in nuove}) == 23
    doppie = [n["id"] for n in nuove if n["id"] in presenti or n["acc_car_id"] in presenti]
    if doppie:
        print("già nel catalogo, niente da fare:", doppie)
        return 0

    per_modello = {v[2]: v for v in VETTURE}
    agganciate = 0
    for riga in handbook["vetture"]:
        v = per_modello.get(riga["car_model_id"])
        if not v:
            continue
        if riga.get("acc_car_id") not in (None, v[1]):
            print(f"slug diverso per carModelId {riga['car_model_id']}: {riga['acc_car_id']} / {v[1]}")
            return 1
        if riga.get("acc_car_id") is None:
            riga["acc_car_id"] = v[1]
            riga["fonte_slug"] = "Race Element, ConversionFactory.cs (carName dei setup di ACC)"
        riga["id_catalogo"] = v[0]
        riga["nel_catalogo_pitwall"] = True
        agganciate += 1
    assert agganciate == 23, agganciate
    handbook["nota"] = handbook["nota"].replace(
        "le vetture senza slug sono quelle che il catalogo ancora non copre (Lotto 2).",
        "dal Lotto 2 (Entry #064) il catalogo copre tutte le 54 vetture; gli slug delle GT2 vengono "
        "da Race Element (ConversionFactory.cs).")

    catalogo.extend(nuove)
    classi: dict[str, int] = {}
    for c in catalogo:
        classi[c["category"]] = classi.get(c["category"], 0) + 1
    print(f"catalogo: {len(catalogo)} vetture {classi} · handbook agganciate: {agganciate}")
    print("da verificare:", [n["id"] for n in nuove if n["specs"]["confidence"] == "da_verificare"])
    if prova:
        print("prova: nessun file scritto")
        return 0
    open(CATALOGO, "w", encoding="utf-8", newline="").write(riscrivi(CATALOGO, catalogo, grezzo_cat))
    open(HANDBOOK, "w", encoding="utf-8", newline="").write(riscrivi(HANDBOOK, handbook, grezzo_hb))
    print("scritto")
    return 0


if __name__ == "__main__":
    sys.exit(main())
