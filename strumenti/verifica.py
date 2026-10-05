"""strumenti/verifica.py — la verifica di PitWall in un comando solo: verde o rosso.

Dalla radice del repository:

    python strumenti/verifica.py                    tutto
    python strumenti/verifica.py --veloce           senza browser: test, tipi, documenti
    python strumenti/verifica.py --accetta-catture  le catture di ora diventano il paragone

Che cosa controlla, in ordine:

  1. i test del backend (tutti i `backend/app/tests/test_*.py`, senza rete e senza spesa)
  2. i tipi del frontend (`tsc --noEmit`)
  3. i numeri scritti nei documenti (`numeri_documenti.py`): se sono rimasti indietro è rosso
  4. le pagine: rispondono 200?                              } solo con i server accesi
  5. i cinque percorsi automatici nel browser                } (`strumenti/server.ps1 avvia`)
  6. le catture su tre formati, con l'elenco delle pagine cambiate

Esce con 0 se non c'è niente di rosso. Un passo saltato (server spenti, immagini non
scaricate) è giallo: lo dice, non lo nasconde e non lo conta come passato.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

RADICE = Path(__file__).resolve().parents[1]
BACKEND = RADICE / "backend"
FRONTEND = RADICE / "frontend"
NUMERI = Path(__file__).resolve().parent / "numeri.json"
CATTURE = FRONTEND / "e2e" / "catture"

PAGINE = ["/", "/login", "/console", "/telemetry", "/setup", "/sessioni", "/tracciati", "/lezioni", "/crediti"]
# Test che leggono le immagini scaricate (fuori dal repository): senza, si saltano dicendolo.
SERVONO_IMMAGINI = {"test_tracciati.py"}
MANIFEST = FRONTEND / "public" / "assets" / "manifest.json"

VERDE, ROSSO, GIALLO = "VERDE", "ROSSO", "SALTATO"
SIMBOLO = {VERDE: "✅", ROSSO: "❌", GIALLO: "⏭ "}
esiti: list[tuple[str, str, str]] = []


def segna(nome: str, stato: str, dettaglio: str = "") -> None:
    esiti.append((nome, stato, dettaglio))
    print(f"{SIMBOLO[stato]} {nome}" + (f" — {dettaglio}" if dettaglio else ""), flush=True)


def python_del_backend() -> str:
    for candidato in (BACKEND / ".venv" / "Scripts" / "python.exe", BACKEND / ".venv" / "bin" / "python"):
        if candidato.exists():
            return str(candidato)
    return sys.executable


def npx() -> str:
    return shutil.which("npx.cmd") or shutil.which("npx") or "npx"


def risponde(url: str) -> int | None:
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, OSError):
        return None


# ── 1 · test del backend ────────────────────────────────────────────────────
def un_test(python: str, file: Path) -> tuple[str, int, int, str]:
    ambiente = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([python, str(file)], cwd=BACKEND, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=ambiente)
    trovato = re.findall(r"RISULTATI: (\d+)/(\d+)", p.stdout)
    if not trovato:
        return file.name, 0, 0, (p.stderr or p.stdout).strip().splitlines()[-1][:200] if (p.stderr or p.stdout).strip() else "nessun esito"
    passati, totali = map(int, trovato[-1])
    falliti = [r.strip() for r in p.stdout.splitlines() if "FAIL" in r][:3]
    return file.name, passati, totali, " · ".join(falliti)


def test_backend() -> dict[str, int]:
    python = python_del_backend()
    file = sorted((BACKEND / "app" / "tests").glob("test_*.py"))
    saltati = [f.name for f in file if f.name in SERVONO_IMMAGINI and not MANIFEST.exists()]
    da_fare = [f for f in file if f.name not in saltati]
    conti: dict[str, int] = {}
    rossi: list[str] = []
    # I test che aprono la memoria condivisa di ACC (finta) usano gli stessi nomi di mappa:
    # insieme si pestano i piedi, quindi vanno in fila. Gli altri girano a quattro per volta.
    in_fila = [f for f in da_fare if re.search(r"mmap|acpmf", f.read_text(encoding="utf-8"))]
    insieme = [f for f in da_fare if f not in in_fila]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        risultati = list(pool.map(lambda f: un_test(python, f), insieme))
    risultati += [un_test(python, f) for f in in_fila]
    for nome, passati, totali, nota in risultati:
        conti[nome] = totali
        if totali == 0 or passati != totali:
            rossi.append(f"{nome} {passati}/{totali}" + (f" ({nota})" if nota else ""))
    totale = sum(conti.values())
    if rossi:
        segna("Test del backend", ROSSO, "; ".join(rossi))
    else:
        segna("Test del backend", VERDE, f"{totale} test in {len(da_fare)} file")
    for nome in saltati:
        segna(f"  {nome}", GIALLO, "servono le immagini scaricate (apply_photos.py, apply_maps.py)")
    return conti if not rossi and not saltati else {}


# ── 2 · tipi ────────────────────────────────────────────────────────────────
def tipi() -> None:
    p = subprocess.run([npx(), "tsc", "--noEmit"], cwd=FRONTEND, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    errori = [r for r in (p.stdout + p.stderr).splitlines() if "error TS" in r]
    if p.returncode == 0:
        segna("Tipi del frontend", VERDE, "0 errori")
    else:
        segna("Tipi del frontend", ROSSO, f"{len(errori)} errori; il primo: {errori[0][:160] if errori else p.stderr.strip()[:160]}")


# ── 3 · numeri dei documenti ────────────────────────────────────────────────
def documenti() -> None:
    p = subprocess.run([sys.executable, str(Path(__file__).with_name("numeri_documenti.py")), "--controlla"],
                       cwd=RADICE, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    ultima = (p.stdout.strip().splitlines() or [""])[-1]
    segna("Numeri nei documenti", VERDE if p.returncode == 0 else ROSSO, ultima[:240])


# ── 4-6 · pagine, percorsi, catture ─────────────────────────────────────────
def pagine() -> bool:
    if risponde("http://localhost:8000/") != 200 or risponde("http://localhost:3000/login") is None:
        segna("Pagine, percorsi e catture", GIALLO, "server spenti: accendili con strumenti/server.ps1 avvia")
        return False
    rotte = {p: risponde(f"http://localhost:3000{p}") for p in PAGINE}
    rotte_rosse = [f"{p} → {s}" for p, s in rotte.items() if s != 200]
    segna("Pagine", ROSSO if rotte_rosse else VERDE, "; ".join(rotte_rosse) or f"{len(PAGINE)} pagine rispondono 200")
    return True


def browser() -> None:
    p = subprocess.run([npx(), "playwright", "test"], cwd=FRONTEND, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    righe = (p.stdout + p.stderr).splitlines()
    falliti = [r.strip() for r in righe if re.match(r"\s*(✘|x|\d+\)) ", r) and "percorsi.spec" in r]
    passati = len([r for r in righe if re.match(r"\s*(✓|ok) ", r) and "percorsi.spec" in r])
    if p.returncode != 0:
        segna("Percorsi nel browser", ROSSO, (falliti[0] if falliti else righe[-1] if righe else "errore")[:200])
    else:
        segna("Percorsi nel browser", VERDE, f"{passati} percorsi arrivano in fondo")
    esito = CATTURE / "esito.json"
    if not esito.exists():
        segna("Catture", ROSSO, "nessun esito scritto")
        return
    voci = json.loads(esito.read_text(encoding="utf-8"))
    cambiate = [v["file"] for v in voci if v["stato"] == "cambiata"]
    nuove = [v for v in voci if v["stato"] == "nuova"]
    larghe = [v["file"] for v in voci if v["scorre"]]
    if larghe:
        segna("Catture", ROSSO, f"scorrono in orizzontale: {', '.join(larghe)}")
    elif cambiate:
        # Una pagina cambiata non è un errore: è una cosa da guardare.
        segna("Catture", VERDE, f"{len(voci)} catture · DA GUARDARE, cambiate: {', '.join(cambiate)}")
    else:
        segna("Catture", VERDE, f"{len(voci)} catture, " + ("tutte nuove (primo giro)" if len(nuove) == len(voci) else "nessuna pagina cambiata"))


def accetta_catture() -> None:
    ora, prima = CATTURE / "ora", CATTURE / "prima"
    if not ora.exists():
        print("Nessuna cattura da accettare: lancia prima la verifica con i server accesi.")
        raise SystemExit(1)
    shutil.rmtree(prima, ignore_errors=True)
    shutil.copytree(ora, prima)
    print(f"Le {len(list(prima.glob('*.png')))} catture di ora sono il nuovo termine di paragone.")


def main() -> int:
    parser = argparse.ArgumentParser(description="La verifica di PitWall in un comando solo.")
    parser.add_argument("--veloce", action="store_true", help="senza browser: test, tipi, documenti")
    parser.add_argument("--accetta-catture", action="store_true", help="le catture di ora diventano il paragone")
    opzioni = parser.parse_args()
    if opzioni.accetta_catture:
        accetta_catture()
        return 0

    inizio = time.perf_counter()
    conti = test_backend()
    if conti:
        nuovo = {"file": len(conti), "test": sum(conti.values()), "per_file": dict(sorted(conti.items()))}
        vecchio = json.loads(NUMERI.read_text(encoding="utf-8")) if NUMERI.exists() else None
        if nuovo != vecchio:
            NUMERI.write_text(json.dumps(nuovo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"   (aggiornato strumenti/numeri.json: {nuovo['test']} test in {nuovo['file']} file)")
    tipi()
    documenti()
    if not opzioni.veloce and pagine():
        browser()

    rossi = [n for n, s, _ in esiti if s == ROSSO]
    gialli = [n for n, s, _ in esiti if s == GIALLO]
    print("─" * 60)
    if rossi:
        print(f"❌ ROSSO — {len(rossi)} da sistemare: {', '.join(rossi)}")
    elif gialli:
        print(f"✅ VERDE su quello che è stato controllato — saltati: {', '.join(g.strip() for g in gialli)}")
    else:
        print("✅ VERDE su tutto")
    print(f"   {time.perf_counter() - inizio:.0f} s")
    return 1 if rossi else 0


if __name__ == "__main__":
    raise SystemExit(main())
