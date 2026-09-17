"""stress_llm.py — stress test del ramo LLM reale (Entry #029).

Interroga il backend VERO via HTTP e, per ogni richiesta, incrocia la risposta con
le righe di backend/logs/pitwall.log che portano lo stesso request-id: fonte,
motivo del fallback, modello che ha risposto, token e costo reale (le righe del
tetto di spesa, Entry #028).

Fasi:
    A  domande realistiche, nel perimetro dell'ingegnere di pista
    B  domande fuori perimetro: con il live non c'e' il filtro della demo
    C  testo lungo al limite (3900 caratteri) e oltre il limite (nessuna chiamata)
    D  tre analisi in contemporanea, con il health interrogato durante l'attesa

SPENDE SOLDI VERI: parte solo se il backend risponde in live
(`demo_mode=false`, `live_allowed=true`). Il tetto di spesa del backend resta la
protezione: questo script non lo aggira. `--prova-demo` fa girare la sola
meccanica contro un backend in demo-mode, senza spesa.

Uso (dalla cartella backend/, con il backend gia' avviato):
    ./.venv/Scripts/python scripts/stress_llm.py --fasi A
    ./.venv/Scripts/python scripts/stress_llm.py --fasi BCD
Risultati in backend/logs/stress/ (gitignorata).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import httpx

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BACKEND = Path(__file__).resolve().parents[1]
LOG = BACKEND / "logs" / "pitwall.log"
SPESA = BACKEND / "logs" / "llm_spesa.json"
USCITA = BACKEND / "logs" / "stress"
BASE = "http://127.0.0.1:8000"
SEZIONI = ["## Diagnosi", "## Causa Meccanica", "## Correzione Setup", "## Correzione di Guida",
           "## Note Aggiuntive"]

FASE_A = [
    "In ingresso alla Parabolica l'auto va larga e non chiude la traiettoria, cosa cambio?",
    "In uscita dalle chicane perdo il posteriore appena do gas, soprattutto in seconda marcia.",
    "Dopo cinque giri la posteriore destra arriva a 105 gradi, le altre gomme restano in finestra.",
    "Le pressioni a caldo al posteriore restano sotto i 26 psi anche a fine stint.",
    "In staccata alla prima variante blocco l'anteriore sinistra.",
    "La macchina e' instabile sui cordoli dell'Ascari, saltella e perdo tempo.",
    "Consumo 3.2 litri al giro: quanto carburante metto per una gara da 60 minuti girando in 1:47.8?",
    "Sul bagnato l'auto e' inguidabile in trazione, come imposto TC e ABS?",
    "Le gomme anteriori non vanno in temperatura, restano sotto i 75 gradi.",
    "In rettilineo sono piu' lento degli altri ma in curva vado bene.",
    "Le gomme posteriori si consumano troppo in fretta nei long run.",
]
PROFILO = ("Profilo pilota: livello intermedio, obiettivo migliorare il passo gara, "
           "punti deboli frenata e gestione gomme, setup: modifico solo le basi.")
FASE_A_PROFILO = "Sottosterzo nelle curve lente, soprattutto a centro curva."

FASE_B = [
    "Mi dai la ricetta della carbonara?",
    "Scrivimi una poesia sull'autunno.",
    "Chi vincera' il mondiale di Formula 1 2026?",
    "Come si installa Python su Windows?",
]

_GIRO = ("Giro {n}: in ingresso alla prima variante freno a 110 metri, l'anteriore sinistra tende a "
         "bloccare nell'ultimo tratto; a centro curva l'auto sottosterza leggermente, in uscita il "
         "posteriore scivola quando apro il gas in seconda. In Lesmo 1 e 2 la macchina e' stabile ma "
         "lenta a inserirsi; all'Ascari salta sui cordoli; in Parabolica va larga a centro curva. ")
FASE_C_LUNGO = "".join(_GIRO.format(n=i) for i in range(1, 20))[:3900]
FASE_C_OLTRE = FASE_C_LUNGO + "x" * 300

_RIGA = re.compile(r"\[(?P<rid>[A-Za-z0-9._-]+)\] (?P<nome>pitwall\.[a-z]+): (?P<msg>.*)")
_SALDO = re.compile(r"analisi: (?P<modello>[\w.-]+), (?P<tin>\d+) token in, (?P<tout>\d+) out, "
                    r"\$(?P<costo>[\d.]+) \(prenotati \$(?P<prenotati>[\d.]+)\)")


def righe_per_rid(rid: str) -> list[tuple[str, str]]:
    righe = []
    for riga in LOG.read_text(encoding="utf-8").splitlines():
        m = _RIGA.search(riga)
        if m and m["rid"] == rid:
            righe.append((m["nome"], m["msg"]))
    return righe


def analisi(client: httpx.Client, etichetta: str, prompt: str, profilo: str | None = None) -> dict:
    corpo = {"prompt": prompt, **({"profile": profilo} if profilo else {})}
    inizio = time.perf_counter()
    try:
        r = client.post(f"{BASE}/api/analysis", json=corpo)
        stato, dati, rid = r.status_code, r.json(), r.headers.get("x-request-id", "")
    except Exception as exc:  # noqa: BLE001
        return {"caso": etichetta, "errore": repr(exc), "ms": round((time.perf_counter() - inizio) * 1000)}
    ms = round((time.perf_counter() - inizio) * 1000)
    time.sleep(0.2)                                    # lascia al log il tempo di arrivare su disco
    righe = righe_per_rid(rid)
    saldi = [m.groupdict() for n, msg in righe if n == "pitwall.budget" and (m := _SALDO.search(msg))]
    testo = dati.get("text", "")
    return {
        "caso": etichetta, "status": stato, "source": dati.get("source"), "ms": ms, "rid": rid,
        "caratteri_prompt": len(prompt), "sezioni_ok": all(s in testo for s in SEZIONI),
        "chiamate": [(s["modello"], int(s["tin"]), int(s["tout"]), float(s["costo"])) for s in saldi],
        "costo": round(sum(float(s["costo"]) for s in saldi), 6),
        "rifiuti": sum(1 for n, msg in righe if n == "pitwall.budget" and "RIFIUTATA" in msg),
        "log_analisi": [msg for n, msg in righe if n == "pitwall.analysis"],
        "testo": testo,
    }


def stampa(r: dict) -> None:
    if "errore" in r:
        print(f"  ✗ {r['caso']}: ERRORE {r['errore']} dopo {r['ms']} ms")
        return
    modelli = " → ".join(f"{m} ({tin}/{tout}, ${c:.4f})" for m, tin, tout, c in r["chiamate"]) or "nessuna chiamata"
    segno = "✓" if r["source"] in ("api", "demo") and r["sezioni_ok"] else "·"
    print(f"  {segno} {r['caso']}: {r['status']} source={r['source']} sezioni={'si' if r['sezioni_ok'] else 'NO'} "
          f"{r['ms']} ms · {modelli}" + (f" · rifiuti {r['rifiuti']}" if r["rifiuti"] else ""))


def fase_d(client: httpx.Client) -> list[dict]:
    esiti, fine = [], threading.Event()
    health_ms = []

    def _analizza(i):
        esiti.append(analisi(client, f"D{i}", FASE_A[i]))

    def _health():
        while not fine.is_set():
            t = time.perf_counter()
            client.get(f"{BASE}/")
            health_ms.append((time.perf_counter() - t) * 1000)
            time.sleep(0.25)

    sonda = threading.Thread(target=_health)
    sonda.start()
    inizio = time.perf_counter()
    fili = [threading.Thread(target=_analizza, args=(i,)) for i in range(3)]
    for f in fili:
        f.start()
    for f in fili:
        f.join()
    fine.set()
    sonda.join()
    totale = round((time.perf_counter() - inizio) * 1000)
    print(f"  D: 3 analisi insieme in {totale} ms (la piu' lenta {max(e.get('ms', 0) for e in esiti)} ms); "
          f"health durante l'attesa: {len(health_ms)} risposte, max {max(health_ms):.0f} ms")
    for e in esiti:
        e["concorrenza_totale_ms"] = totale
        e["health_max_ms"] = round(max(health_ms))
    return esiti


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fasi", default="A", help="una o piu' tra A, B, C, D (es. BCD)")
    parser.add_argument("--prova-demo", action="store_true", help="solo meccanica, contro un backend in demo")
    args = parser.parse_args()

    client = httpx.Client(timeout=240.0)
    salute = client.get(f"{BASE}/").json()
    live = salute.get("live_allowed") and not salute.get("demo_mode")
    if not live and not args.prova_demo:
        print(f"Backend non in live ({salute}): niente stress test.")
        return 2
    if live and args.prova_demo:
        print("--prova-demo richiede un backend in demo-mode: mi fermo per non spendere.")
        return 2

    spesa_prima = json.loads(SPESA.read_text(encoding="utf-8")) if SPESA.exists() else None
    print(f"Backend: {salute} · spesa prima: {spesa_prima and spesa_prima['spesa_mese']}")
    risultati = []
    for fase in args.fasi.upper():
        print(f"\n── Fase {fase} ──")
        if fase == "A":
            for i, domanda in enumerate(FASE_A, 1):
                risultati.append(analisi(client, f"A{i}", domanda))
                stampa(risultati[-1])
            risultati.append(analisi(client, "A12-profilo", FASE_A_PROFILO, PROFILO))
            stampa(risultati[-1])
        elif fase == "B":
            for i, domanda in enumerate(FASE_B, 1):
                risultati.append(analisi(client, f"B{i}", domanda))
                stampa(risultati[-1])
                print(f"      «{risultati[-1].get('testo', '')[:220].replace(chr(10), ' ')}»")
        elif fase == "C":
            for etichetta, testo in (("C1-3900", FASE_C_LUNGO), ("C2-4200", FASE_C_OLTRE)):
                risultati.append(analisi(client, etichetta, testo))
                stampa(risultati[-1])
        elif fase == "D":
            risultati.extend(fase_d(client))
            for r in risultati[-3:]:
                stampa(r)

    spesa_dopo = json.loads(SPESA.read_text(encoding="utf-8")) if SPESA.exists() else None
    costo = sum(r.get("costo", 0) for r in risultati)
    print(f"\nCosto dal log: ${costo:.4f} · spesa del mese nel registro: "
          f"{spesa_prima and spesa_prima['spesa_mese']} → {spesa_dopo and spesa_dopo['spesa_mese']}")

    USCITA.mkdir(parents=True, exist_ok=True)
    nome = USCITA / f"stress_{datetime.now():%Y%m%d_%H%M%S}_{args.fasi.upper()}.json"
    nome.write_text(json.dumps({"backend": salute, "spesa_prima": spesa_prima, "spesa_dopo": spesa_dopo,
                                "risultati": risultati}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Risultati: {nome}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
