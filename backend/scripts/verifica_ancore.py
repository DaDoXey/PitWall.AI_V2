#!/usr/bin/env python3
"""
verifica_ancore.py — le ancore di una pista reggono sulle ALTRE sessioni?

Decisione 5 del 25/09, nella forma corretta del 28/09: l'apice di ogni ancora presa
sul giro di origine si riporta sul giro migliore di ogni altra sessione della stessa
pista, e si controlla che

  (a) li' ci sia un punto riconoscibile (minimo di velocita' o picco di
      accelerazione laterale dello stesso senso) entro ±1% di giro. Decide lui se
      l'ancora regge. Tolleranza decisa da Edoardo il 28/09: lo stesso punto si
      sposta di ~0,6% di giro da una sessione all'altra, e a ±0,5% le ancore giuste
      fallivano per uno o due millesimi;
  (b) SOLO INFORMATIVO (decisione del 28/09): cade nello stesso tratto del motore,
      riconosciuto dal suo apice e non dal suo numero. Su un giro solo il motore
      divide alcune curve in modo diverso da una sessione all'altra (a Zandvoort la
      Gerlach e la Hans Ernst), quindi questo controllo fallisce anche con ancore
      perfette: si stampa, non blocca.

Uso (dalla radice del repo):
    backend/.venv/Scripts/python backend/scripts/verifica_ancore.py monza
    backend/.venv/Scripts/python backend/scripts/verifica_ancore.py zandvoort --scelte ~/Downloads/anchors_choice_zandvoort.json

Senza `--scelte` legge il file gia' applicato in data/tracks_anchors/. Esce con 1
se anche una sola ancora non trova il suo punto (a).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_anchors_proof import sessioni_di  # noqa: E402  (carica anche il .env)

from app.analisi.eventi_curva import TOLLERANZA, giro_migliore, profilo, verifica  # noqa: E402
from app.analisi.curve import CurveNonCalcolabili  # noqa: E402
from app.core import ancore, catalog as cat  # noqa: E402
from app.telemetria.registratore import leggi_canali  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Verifica le ancore sulle altre sessioni")
    ap.add_argument("pista")
    ap.add_argument("--scelte", type=Path, help="export del provino invece del file applicato")
    ap.add_argument("--tolleranza", type=float, default=TOLLERANZA,
                    help=f"quota di giro ammessa (default {TOLLERANZA}, decisa il 28/09)")
    args = ap.parse_args()

    if args.scelte:
        dati = json.loads(args.scelte.expanduser().read_text(encoding="utf-8"))
    else:
        dati = ancore.carica(args.pista)
    if not dati:
        sys.exit(f"nessuna ancora per {args.pista}")

    sensi = {c.get("n"): c.get("direzione")
             for c in (cat.track_guide(args.pista) or {}).get("curve") or []}
    voci = [{**a, "direzione": sensi.get(a["n"])} for a in dati["ancore"]]

    cartelle = {c.name: c for c in sessioni_di(args.pista)}
    if dati["sessione_origine"] not in cartelle:
        sys.exit(f"la sessione di origine {dati['sessione_origine']} non e' nell'archivio")

    def prof(nome: str) -> dict:
        canali = leggi_canali(cartelle[nome])
        return profilo(canali, giro_migliore(canali))

    origine = prof(dati["sessione_origine"])
    altre = [n for n in cartelle if n != dati["sessione_origine"]]
    if not altre:
        print(f"{args.pista}: una sola sessione in archivio, niente su cui verificare")
        return

    tutto_ok = True
    print(f"{args.pista}: origine {dati['sessione_origine']} "
          f"({len(origine['curve_motore'])} curve del motore), tolleranza ±{args.tolleranza:.1%} di giro\n")
    for nome in altre:
        try:
            altra = prof(nome)
        except CurveNonCalcolabili as e:
            print(f"  {nome}: scartata ({e})")
            continue
        esiti = verifica(voci, origine, altra, args.tolleranza)
        ok = sum(1 for e in esiti if e["punto_ok"])
        print(f"  {nome} ({len(altra['curve_motore'])} curve del motore): {ok}/{len(esiti)} ancore reggono")
        for e in esiti:
            if not e["punto_ok"]:
                tutto_ok = False
                print(f"     NON REGGE  T{e['n']} {e['nome'] or ''} apice @ {e['apice']}: "
                      f"nessun punto riconoscibile entro ±{args.tolleranza:.1%}")
            if not e["tratto_ok"]:
                dettaglio = (f"apici a {e['scarto_apice']} di giro" if e["scarto_apice"] is not None
                             else "nessun tratto del motore")
                print(f"     info       T{e['n']} {e['nome'] or ''}: tratto del motore diverso ({dettaglio})")
    sys.exit(0 if tutto_ok else 1)


if __name__ == "__main__":
    main()
