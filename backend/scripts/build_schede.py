#!/usr/bin/env python3
"""Genera SCHEDE.md da cars.json e tracks.json. Fonte unica: i JSON."""

from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict

ORDINE_CLASSI = ["GT3", "GT2", "GT4", "GTC", "TCX"]


def fmt(v, suffisso=""):
    if v is None or v == "":
        return "_da verificare_"
    return f"{v}{suffisso}"


def scheda_auto(c: dict) -> list[str]:
    s = c.get("specs", {})
    r = [f"### {c['brand']} {c['model']} ({c['year']})", ""]
    dlc = f"DLC — {c['dlc_pack']}" if c.get("dlc") else "Contenuto base"
    r += [
        f"- **id:** `{c['id']}` · **acc_car_id:** `{c.get('acc_car_id', '—')}`",
        f"- **Disponibilita':** {dlc}",
        f"- **Motore:** {fmt(s.get('engine'))}",
        f"- **Potenza:** {fmt(s.get('power_hp'), ' CV')} · **Peso:** {fmt(s.get('weight_kg'), ' kg')}"
        + ("  _(valori di omologazione, variabili per BoP)_" if s.get("bop_variable") else ""),
        f"- **Trazione:** {fmt(s.get('drivetrain'))} · **Cambio:** {fmt(s.get('gearbox'))}",
        f"- **Aiuti:** TC {'si' if c.get('has_tc') else 'NO'} · ABS {'si' if c.get('has_abs') else 'NO'}",
        f"- **Affidabilita' specifiche:** {s.get('confidence', 'n.d.')}",
    ]
    if c.get("specs_note"):
        r.append(f"- ⚠️ {c['specs_note']}")
    if c.get("dlc_note"):
        r.append(f"- ⚠️ {c['dlc_note']}")
    r += ["", f"> {c['caption_it']}", "", "**Asset da risolvere:**", ""]
    for ruolo, a in c.get("assets", {}).items():
        r.append(f"- `{ruolo}` — query: _{a.get('commons_query')}_ · "
                 f"categoria: `{a.get('commons_category') or 'nessuna'}` · "
                 f"formato: {a.get('preferred_format')} · licenza attesa: {a.get('license_expected')}")
    r.append("")
    return r


def scheda_pista(t: dict) -> list[str]:
    r = [f"### {t['name']}" + (f" — *{t['nick']}*" if t.get("nick") else ""), ""]
    dlc = f"DLC — {t['dlc_pack']}" if t.get("dlc") else "Contenuto base"
    r += [
        f"- **id:** `{t['id']}` · **acc_track_id:** `{t.get('acc_track_id', '—')}`",
        f"- **Paese:** {t['country']} · **Disponibilita':** {dlc}",
        f"- **Lunghezza:** {fmt(t.get('length_km'), ' km')} · **Curve:** {fmt(t.get('corners'))}"
        f"  _(affidabilita': {t.get('corners_confidence', 'n.d.')})_",
        f"- **Griglia:** {fmt(t.get('grid_size'))} · **Lato pole:** {fmt(t.get('pole_side'))}",
        f"- **Record reale:** {fmt(t.get('lap_record_real'))}",
        f"- **Rif. GT3 in ACC:** {fmt(t.get('gt3_ref_lap_time'))} · "
        f"**Consumo/giro GT3:** {fmt(t.get('gt3_fuel_per_lap_l'), ' L')} "
        f"({t.get('fuel_status', 'n.d.')})",
        f"- **Deportanza:** {fmt(t.get('downforce_level'))}",
    ]
    for k in ("corners_note", "lap_record_note"):
        if t.get(k):
            r.append(f"- ⚠️ {t[k]}")
    r += ["", f"> {t['description_it']}", "",
          f"**Focus setup:** {t.get('setup_focus_it', '—')}", "",
          "**Asset da risolvere:**", ""]
    for ruolo, a in t.get("assets", {}).items():
        r.append(f"- `{ruolo}` — query: _{a.get('commons_query')}_ · "
                 f"categoria: `{a.get('commons_category') or 'nessuna'}` · "
                 f"formato: {a.get('preferred_format')} · licenza attesa: {a.get('license_expected')}")
    r.append("")
    return r


def main() -> None:
    cars = json.loads(Path("cars.json").read_text(encoding="utf-8"))
    tracks = json.loads(Path("tracks.json").read_text(encoding="utf-8"))

    per_classe = defaultdict(list)
    for c in cars:
        per_classe[c["category"]].append(c)

    out = [
        "# PitWall.AI — Schede vetture e circuiti ACC",
        "",
        "Documento generato da `build_schede.py`. **Non modificare a mano**: correggi",
        "`cars.json` / `tracks.json` e rigenera, altrimenti i due divergono.",
        "",
        "## Conteggio consegnato",
        "",
        "| Classe | Schede |",
        "|---|---|",
    ]
    for cl in ORDINE_CLASSI:
        if per_classe.get(cl):
            out.append(f"| {cl} | {len(per_classe[cl])} |")
    out += [f"| **Circuiti** | **{len(tracks)}** |", "",
            "---", "", "# Vetture", ""]

    for cl in ORDINE_CLASSI:
        if not per_classe.get(cl):
            continue
        out += [f"## Classe {cl}", ""]
        for c in sorted(per_classe[cl], key=lambda x: (x["brand"], x["year"])):
            out += scheda_auto(c)

    out += ["---", "", "# Circuiti", ""]
    for t in sorted(tracks, key=lambda x: x["name"]):
        out += scheda_pista(t)

    Path("SCHEDE.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"SCHEDE.md scritto: {len(cars)} vetture, {len(tracks)} circuiti")


if __name__ == "__main__":
    main()
