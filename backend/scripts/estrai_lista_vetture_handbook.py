#!/usr/bin/env python3
"""
estrai_lista_vetture_handbook.py — la lista ufficiale COMPLETA dei carModelId

Perche' esiste:
    Il documento della shared memory si ferma alla v1.8.12 e conosce 43 vetture: le
    cinque GT3 uscite dopo (Ferrari 296, Huracan Evo2, Porsche 992 GT3 R, McLaren
    720S Evo, Ford Mustang) e tutta la classe GT2 non ci sono. L'**ACC Server Admin
    Handbook** di Kunos (v1.10.2) ha invece la tabella completa `carModel` -> nome:
    e' la lista con cui i server scrivono i risultati, cioe' esattamente il numero
    che PitWall deve saper tradurre.

    Questo script la estrae e la aggancia al catalogo di PitWall (`cars.json`),
    dicendo a voce alta che cosa non e' riuscito ad agganciare.

Come si usa:
    ./.venv/Scripts/python scripts/estrai_lista_vetture_handbook.py <ServerAdminHandbook.pdf>

    Il PDF e' pubblicato da Kunos e distribuito con il server dedicato.

Scrive `app/core/data/acc_lista_vetture_handbook.json`.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from scripts.estrai_appendici_acc import testo_del_pdf  # noqa: E402

USCITA = BACKEND / "app" / "core" / "data" / "acc_lista_vetture_handbook.json"
CATALOGO = BACKEND / "app" / "core" / "data" / "cars.json"
FONTE = "ACC Server Admin Handbook v1.10.2 — Kunos Simulazioni, appendice IX.3"

MARKER = re.compile(r"(?:en-US|en-GB|de-DE)")

# Il nome dell'handbook e quello del catalogo non coincidono sempre. Qui SOLO i casi
# che restano dopo l'aggancio per carModelId (che copre le 43 vetture delle appendici)
# e dopo il confronto per nome: ognuno verificato a mano contro l'id ufficiale.
ALIAS_NOME = {
    "lamborghinihuracanevo2": "lamborghini_huracan_gt3_evo2",   # id 33
    "porsche992gt3r": "porsche_992_gt3_r",                      # id 34
}

APPENDICI = BACKEND / "app" / "core" / "data" / "acc_riferimenti_vetture.json"


def normalizza(testo: str) -> str:
    testo = unicodedata.normalize("NFKD", testo).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", testo.lower())


def lista_vetture(testo: str) -> list[tuple[int, str]]:
    # `rfind`, non `find`: il titolo compare anche nell'indice a inizio documento, e
    # lì sotto non c'è nessuna vettura — solo puntini e un numero di pagina.
    inizio = testo.rfind("IX.3 Car model list")
    if inizio < 0:
        sys.exit("sezione «IX.3 Car model list» non trovata nel PDF")
    fine = testo.find("IX.4", inizio)
    pezzo = testo[inizio:fine if fine > 0 else len(testo)]

    celle = [" ".join(c.split()) for c in MARKER.split(pezzo)]
    celle = [c for c in celle if c and c.lower() not in ("value", "car model")]

    fuori: list[tuple[int, str]] = []
    id_corrente: int | None = None
    pezzi_nome: list[str] = []
    for cella in celle:
        if re.fullmatch(r"\d{1,3}", cella):
            if id_corrente is not None and pezzi_nome:
                fuori.append((id_corrente, _ricomponi(pezzi_nome)))
            id_corrente = int(cella)
            pezzi_nome = []
        elif id_corrente is not None:
            pezzi_nome.append(cella)
    if id_corrente is not None and pezzi_nome:
        fuori.append((id_corrente, _ricomponi(pezzi_nome)))
    return fuori


def _ricomponi(pezzi: list[str]) -> str:
    """«Nissan GT» + «-» + «R Nismo GT3 2018» -> «Nissan GT-R Nismo GT3 2018»."""
    testo = " ".join(pezzi)
    testo = re.sub(r"\s*-\s*", "-", testo) if " - " in testo else testo
    testo = unicodedata.normalize("NFKD", testo).encode("ascii", "ignore").decode()
    return " ".join(testo.split())


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Manca il percorso del PDF dell'handbook.")
    pdf = Path(sys.argv[1])
    if not pdf.exists():
        sys.exit(f"PDF non trovato: {pdf}")

    vetture = lista_vetture(testo_del_pdf(pdf))
    print(f"  lista ufficiale: {len(vetture)} vetture")

    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    appendici = json.loads(APPENDICI.read_text(encoding="utf-8"))
    # Prima fonte, e la migliore: le appendici danno gia' id -> slug per 43 vetture.
    slug_per_id = {v["car_model_id"]: v["acc_car_id"] for v in appendici["vetture"]}
    per_nome = {normalizza(f"{c['brand']}{c['model']}{c['year']}"): c for c in catalogo}
    per_nome_senza_anno = {normalizza(f"{c['brand']}{c['model']}"): c for c in catalogo}
    per_slug = {c["acc_car_id"]: c for c in catalogo}

    righe = []
    non_agganciate = []
    for car_model_id, nome in vetture:
        slug = slug_per_id.get(car_model_id)
        fonte_slug = "appendice 2 del documento shared memory" if slug else None
        if slug is None:
            chiave = normalizza(nome)
            slug = ALIAS_NOME.get(chiave)
            if slug:
                fonte_slug = "alias verificato a mano sul carModelId"
            else:
                vettura = per_nome.get(chiave) or per_nome_senza_anno.get(chiave)
                if vettura:
                    slug = vettura["acc_car_id"]
                    fonte_slug = "confronto per nome col catalogo PitWall"
        vettura = per_slug.get(slug) if slug else None
        if slug is None:
            non_agganciate.append((car_model_id, nome))
        righe.append({
            "car_model_id": car_model_id,
            "nome_handbook": nome,
            "acc_car_id": slug,
            "fonte_slug": fonte_slug,
            "id_catalogo": vettura["id"] if vettura else None,
            "nel_catalogo_pitwall": vettura is not None,
        })

    documento = {
        "fonte": FONTE,
        "estratto_il": date.today().isoformat(),
        "estratto_da": "backend/scripts/estrai_lista_vetture_handbook.py",
        "nota": (
            "Tabella COMPLETA carModelId -> vettura, comprese le GT3 uscite dopo il "
            "documento della shared memory e l'intera classe GT2. Gli slug "
            "(`acc_car_id`) vengono dal catalogo di PitWall, agganciato per nome: le "
            "vetture senza slug sono quelle che il catalogo ancora non copre (Lotto 2)."
        ),
        "vetture": righe,
    }
    USCITA.write_text(
        json.dumps(documento, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    con_slug = sum(1 for r in righe if r["acc_car_id"])
    nel_catalogo = sum(1 for r in righe if r["nel_catalogo_pitwall"])
    print(f"  con slug ACC: {con_slug}/{len(righe)} · nel catalogo PitWall: {nel_catalogo}")
    if non_agganciate:
        print("  senza slug (vetture che nessuna delle due fonti copre):")
        for car_model_id, nome in non_agganciate:
            print(f"    {car_model_id:3}  {nome}")
    print(f"\n  scritto {USCITA.relative_to(BACKEND)}")


if __name__ == "__main__":
    main()
