#!/usr/bin/env python3
"""
apply_anchors.py — porta a disco le ancore CONFERMATE nel provino

Gemello di apply_maps.py: `build_anchors_proof.py` genera il provino, Edoardo
conferma curva per curva posizione sul giro e punto sulla mappa, l'export e'
`anchors_choice_<id>.json`. Questo script lo controlla con lo stesso validatore
di `check_track_knowledge.py` e lo scrive in
`backend/app/core/data/tracks_anchors/<id>.json`. Se il controllo trova anche un
solo errore non scrive niente: un'ancora sbagliata punterebbe lo zoom e il testo
della guida sulla curva sbagliata, ed e' peggio di nessuna ancora.

Uso (dalla radice del repo):
    backend/.venv/Scripts/python backend/scripts/apply_anchors.py ~/Downloads/anchors_choice_monza.json
    backend/.venv/Scripts/python backend/scripts/apply_anchors.py <file> --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "backend"))

from app.core import ancore, catalog as cat  # noqa: E402


def costruisci(scelta: dict) -> dict:
    """Dall'export del provino al file delle ancore (schema, data, campi in ordine)."""
    return {
        "id": scelta["id"],
        "schema": ancore.SCHEMA,
        "sessione_origine": scelta.get("sessione_origine"),
        "vettura": scelta.get("vettura"),
        "giro": scelta.get("giro"),
        "tempo_giro_ms": scelta.get("tempo_giro_ms"),
        "mappa_commons": scelta.get("mappa_commons"),
        "creato_il": date.today().isoformat(),
        "nota": ("Per ogni curva: inizio (punto di frenata, o inserimento se in pieno), apice e "
                 "uscita sul giro (0-1, come graphics.normalizedCarPosition), e il punto sulla "
                 "mappa verificata (frazioni di larghezza e altezza). Confermati a occhio nel "
                 "provino delle ancore. G_LAT < 0 = curva a destra."),
        "ancore": [
            {"n": a.get("n"), "nome": a.get("nome"),
             "inizio": a.get("inizio"), "metodo_inizio": a.get("metodo_inizio"),
             "apice": a.get("apice"), "metodo_apice": a.get("metodo_apice"),
             "uscita": a.get("uscita"), "metodo_uscita": a.get("metodo_uscita"),
             "g_lat": a.get("g_lat"), "mappa": a.get("mappa")}
            for a in scelta.get("ancore") or []
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Applica l'export del provino delle ancore")
    ap.add_argument("scelte", type=Path, help="anchors_choice_<id>.json esportato dal provino")
    ap.add_argument("--dry-run", action="store_true", help="controlla e basta, non scrive")
    args = ap.parse_args()

    scelta = json.loads(args.scelte.expanduser().read_text(encoding="utf-8"))
    if (scelta.get("_meta") or {}).get("bozza"):
        sys.exit("questa e' una BOZZA del provino (lavoro non finito): si applica solo "
                 "l'export completo, «Esporta ancore»")
    pista = scelta.get("id")
    track = next((t for t in cat.all_tracks() if t.get("id") == pista), None)
    if track is None:
        sys.exit(f"pista sconosciuta: {pista!r}")

    dati = costruisci(scelta)
    errori = ancore.valida_ancore(dati, cat.track_guide(pista),
                                  (track.get("assets") or {}).get("map"), atteso_id=pista)
    if errori:
        print(f"{pista}: {len(errori)} errori, non scrivo niente:")
        for e in errori:
            print(f"  · {e}")
        sys.exit(1)

    uscita = ancore.percorso(pista)
    if args.dry_run:
        print(f"{pista}: {len(dati['ancore'])} ancore conformi — scriverei {uscita.relative_to(_ROOT)}")
        return
    uscita.parent.mkdir(parents=True, exist_ok=True)
    uscita.write_text(json.dumps(dati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{pista}: {len(dati['ancore'])} ancore scritte in {uscita.relative_to(_ROOT)}")


if __name__ == "__main__":
    main()
