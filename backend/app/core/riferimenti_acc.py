"""core/riferimenti_acc.py — tabelle di riferimento per vettura, dal documento Kunos

Sorgente: `data/acc_riferimenti_vetture.json`, generato da
`scripts/estrai_appendici_acc.py` dalle appendici 2-7 del documento ufficiale
«ACC Shared Memory Documentation v1.8.12». **Non e' un file protetto**, ma e' una
fonte di verita': si aggiorna rigenerandolo, non a mano.

A cosa serve, in concreto:

* `vettura_da_car_model_id()` — i file di risultati scritti dai **server** ACC
  identificano la vettura con un numero (`carModel: 30`), non con lo slug. Senza
  questa tabella, l'import di L1 sa solo dire «vettura 30».
* `riferimenti()` — offset del brake bias, coefficienti della pressione freni,
  angolo di sterzo massimo, giri massimi: i numeri che servono per trasformare i
  canali grezzi in qualcosa di leggibile.

**Nessuna conversione viene applicata qui.** Il documento pubblica le tabelle ma non
l'aritmetica esatta per arrivare al valore mostrato sul cruscotto: finche' non e'
verificata in gioco, PitWall conserva il grezzo e dichiara la conversione come «da
verificare» (decisione 7 del rework dati). Questo modulo espone i numeri e il loro
stato, e lascia decidere a chi legge.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PERCORSO = Path(__file__).resolve().parent / "data" / "acc_riferimenti_vetture.json"
_PERCORSO_LISTA = Path(__file__).resolve().parent / "data" / "acc_lista_vetture_handbook.json"

_CACHE: dict[str, Any] | None = None
_CACHE_LISTA: dict[str, Any] | None = None


def _documento() -> dict[str, Any]:
    global _CACHE
    if _CACHE is None:
        _CACHE = json.loads(_PERCORSO.read_text(encoding="utf-8"))
    return _CACHE


def _lista_completa() -> dict[str, Any]:
    """La tabella `carModelId` -> vettura dell'ACC Server Admin Handbook v1.10.2.

    Copre **tutte** le vetture, comprese le GT3 del 2023-24 e la classe GT2, che il
    documento della shared memory (fermo alla 1.8.12) non conosce. Le appendici
    restano la fonte migliore dove ci sono, perche' portano anche le tabelle di
    conversione: questa lista serve a non restare senza nome sulle altre.
    """
    global _CACHE_LISTA
    if _CACHE_LISTA is None:
        _CACHE_LISTA = json.loads(_PERCORSO_LISTA.read_text(encoding="utf-8"))
    return _CACHE_LISTA


def fonte() -> str:
    """Da dove vengono questi numeri: va citato ovunque li si mostri."""
    return str(_documento()["fonte"])


def tutte() -> list[dict[str, Any]]:
    return list(_documento()["vetture"])


def riferimenti(acc_car_id: str) -> dict[str, Any] | None:
    """I riferimenti di una vettura, o None se il documento non la copre.

    None non e' un errore: il documento si ferma alla 1.8.12 e le vetture uscite
    dopo (Ferrari 296, Mustang GT3, 720S Evo, Huracan Evo2, 992 GT3 R) non ci sono.
    Chi chiama deve dirlo, non tirare a indovinare.
    """
    if not acc_car_id:
        return None
    cercato = acc_car_id.strip().lower()
    for vettura in _documento()["vetture"]:
        if vettura["acc_car_id"] == cercato:
            return dict(vettura)
    return None


def vettura_da_car_model_id(car_model_id: int) -> dict[str, Any] | None:
    """Dal numero che scrivono i server ACC alla vettura. None se sconosciuto.

    Prima le appendici (che portano anche le tabelle di conversione), poi la lista
    completa dell'handbook: cosi' una vettura del 2023 ha almeno nome e slug, e chi
    legge vede da `riferimenti_completi` se puo' aspettarsi anche i numeri.
    """
    for vettura in _documento()["vetture"]:
        if vettura["car_model_id"] == car_model_id:
            return dict(vettura, riferimenti_completi=True,
                        fonte=_documento()["fonte"])
    for vettura in _lista_completa()["vetture"]:
        if vettura["car_model_id"] == car_model_id:
            return dict(vettura, riferimenti_completi=False,
                        fonte=_lista_completa()["fonte"])
    return None


def lista_completa() -> list[dict[str, Any]]:
    """Tutte le vetture che ACC conosce (54), con il loro carModelId ufficiale."""
    return list(_lista_completa()["vetture"])


def vetture_senza_riferimenti() -> list[str]:
    """Le vetture del catalogo PitWall che il documento non copre, dichiarate."""
    return list(_documento()["vetture_del_catalogo_senza_riferimenti"])


def stato_conversioni() -> dict[str, Any]:
    """Quali conversioni sono verificate e quali no. Si mostra, non si nasconde."""
    return dict(_documento()["conversioni"])
