"""strumenti/guardiano.py — quello che un commit di PitWall non deve mai contenere.

Gira da solo prima di ogni commit (hook `strumenti/hooks/pre-commit`, da installare una
volta con `python strumenti/guardiano.py --installa`). Rifiuta il commit se fra i file in
stage c'è:

  1. un **file protetto** (logica e numeri che si toccano solo con l'«ok procedi» di
     Edoardo). Per farlo passare dopo un «ok procedi»:  PITWALL_OK_PROCEDI=1 git commit …
  2. un **file che Git dovrebbe ignorare**: `.env`, report, strumenti locali, documenti
     del corso. Succede quando il `.gitignore` si rompe (05/10/2026: fine riga doppi, e
     `backend/.env` era tornato visibile).
  3. una **chiave**: il testo aggiunto contiene qualcosa che somiglia a una chiave API.

    python strumenti/guardiano.py             controlla i file in stage
    python strumenti/guardiano.py --installa  attiva l'hook in questo clone
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

RADICE = Path(__file__).resolve().parents[1]

PROTETTI = (
    "backend/app/core/agent.py",
    "backend/app/core/setup_params.py",
    "backend/app/core/data/car_setup_ranges.json",
    "backend/app/core/vision_parser.py",
    "backend/app/core/prompts/*",
    "backend/app/bundle/demo.py",
    "backend/app/bundle/demo_precedente.py",
    "backend/app/core/demo_responses.py",
)

# Mai nel repository, qualunque cosa dica il .gitignore in quel momento.
MAI = (
    ".env", ".env.*", "*/.env", "*/.env.*", "CLAUDE.md", ".claude/*", "*/.claude/*",
    "*_REPORT.md", "*_PitWall.md", "frontend/public/assets/*", "backend/logs/*",
    "backend/sessions/*", "*/node_modules/*", "*.ld", "*.ldx",
)
CONSENTITI = ("backend/.env.example", "frontend/.env.local.example")

CHIAVI = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


def git(*argomenti: str) -> str:
    return subprocess.run(["git", *argomenti], cwd=RADICE, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def combacia(percorso: str, modelli: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(percorso, m) for m in modelli)


def controlla() -> int:
    in_stage = [r for r in git("diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines() if r]
    problemi: list[str] = []

    protetti = [f for f in in_stage if combacia(f, PROTETTI)]
    if protetti and os.environ.get("PITWALL_OK_PROCEDI") != "1":
        problemi.append("file protetti (serve l'«ok procedi» di Edoardo, poi PITWALL_OK_PROCEDI=1): " + ", ".join(protetti))

    vietati = [f for f in in_stage if combacia(f, MAI) and f not in CONSENTITI]
    if vietati:
        problemi.append("file che non devono entrare nel repository: " + ", ".join(vietati))

    aggiunte = [r[1:] for r in git("diff", "--cached", "-U0").splitlines() if r.startswith("+") and not r.startswith("+++")]
    if any(c.search(riga) for riga in aggiunte for c in CHIAVI):
        problemi.append("nel testo aggiunto c'è qualcosa che somiglia a una chiave API o privata")

    if problemi:
        print("✋ Commit fermato dal guardiano di PitWall:")
        for p in problemi:
            print("   -", p)
        return 1
    return 0


def installa() -> int:
    subprocess.run(["git", "config", "core.hooksPath", "strumenti/hooks"], cwd=RADICE, check=True)
    print("Guardiano attivo: Git userà gli hook in strumenti/hooks per questo clone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(installa() if "--installa" in sys.argv else controlla())
