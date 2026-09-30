"""scripts/riconverti_setup.py — il setup delle sessioni in archivio, riletto con la tabella di oggi (Entry #057).

Perché esiste:
    il setup di una sessione si converte una volta sola, all'import, e nel bundle
    finisce il risultato. Quando `car_setup_ranges.json` cambia (una vettura nuova, un
    parametro visto in gioco) o cambia l'adattatore, le sessioni già salvate restano
    con la conversione vecchia. Questo script rilegge il JSON originale di ACC, che il
    bundle conserva intatto in `setup.raw`, e rifà la conversione.

Regole:
    * si tocca solo `bundle.setup`: telemetria, giri, analisi, racconto restano;
    * una sessione senza il JSON originale (setup inserito a mano) si salta;
    * la demo si salta: si rigenera da sola quando cambia VERSIONE_GENERATORE;
    * prima di riscrivere un file se ne fa una copia in `_backup_riconversione/`,
      accanto all'archivio.

Uso (dalla cartella backend/):
    ./.venv/Scripts/python scripts/riconverti_setup.py --prova  # dice cosa cambierebbe
    ./.venv/Scripts/python scripts/riconverti_setup.py          # riconverte
"""

from __future__ import annotations

import json
import pathlib
import shutil
import sys
from datetime import datetime

BACKEND = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")  # PITWALL_SESSIONS_DIR: l'archivio sta fuori dal repo

from app.bundle import store  # noqa: E402
from app.bundle.adapters.acc_setup import SetupAccError, leggi_setup_acc  # noqa: E402
from app.bundle.demo import e_demo  # noqa: E402


def _come_si_legge(valore) -> str:
    if valore.verificato and valore.reale is not None:
        return f"{valore.reale:g} {valore.unita}".strip()
    return f"{valore.raw} click"


def differenze(vecchio, nuovo) -> list[str]:
    righe = []
    for chiave in sorted(set(vecchio.valori) | set(nuovo.valori)):
        prima, dopo = vecchio.valori.get(chiave), nuovo.valori.get(chiave)
        a = _come_si_legge(prima) if prima else "—"
        b = _come_si_legge(dopo) if dopo else "—"
        if a != b or (prima and dopo and prima.fonte != dopo.fonte):
            righe.append(f"{chiave}: {a} → {b}")
    if vecchio.assunzioni != nuovo.assunzioni:
        righe.append(f"assunzioni: {len(vecchio.assunzioni)} → {len(nuovo.assunzioni)}")
    return righe


def main(prova: bool) -> int:
    backup = store.cartella() / "_backup_riconversione" / datetime.now().strftime("%Y%m%d-%H%M%S")
    cambiate = 0
    for riassunto in store.elenca():
        id_sessione = riassunto.id
        if e_demo(id_sessione):
            continue
        bundle = store.leggi(id_sessione)
        if not bundle.setup or not bundle.setup.raw:
            continue
        try:
            nuovo = leggi_setup_acc(json.dumps(bundle.setup.raw).encode("utf-8"),
                                    nome=bundle.setup.nome)
        except SetupAccError as e:
            print(f"! {id_sessione}: setup non rileggibile ({e}), lasciato com'è")
            continue
        righe = differenze(bundle.setup, nuovo)
        if not righe:
            continue
        cambiate += 1
        print(f"{id_sessione} · {nuovo.car} · {len(righe)} differenze")
        for riga in righe:
            print(f"    {riga}")
        if not prova:
            backup.mkdir(parents=True, exist_ok=True)
            percorso = store._percorso(id_sessione)
            shutil.copy2(percorso, backup / percorso.name)
            bundle.setup = nuovo
            store.salva(bundle, id_sessione)
    if not cambiate:
        print("nessuna sessione da riconvertire")
    elif prova:
        print(f"\n{cambiate} sessioni cambierebbero (prova: nessun file scritto)")
    else:
        print(f"\n{cambiate} sessioni riconvertite · copie in {backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main(prova="--prova" in sys.argv[1:]))
