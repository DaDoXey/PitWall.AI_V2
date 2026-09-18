"""GET /api/catalog — anagrafica vetture e circuiti ACC (Lotto 1).

Serve il catalogo di `core/catalog.py`: liste compatte per i selettori e schede
complete per la singola vettura/circuito. Nessun dato di sessione qui (quelli
stanno su /api/sessions): questa è l'anagrafica statica.
"""

from fastapi import APIRouter, HTTPException

from app.core import catalog as cat

router = APIRouter()


@router.get("/catalog")
def get_catalog():
    """Indice completo: liste compatte di auto e circuiti + conteggi."""
    return cat.catalog_index()


@router.get("/catalog/car/{car_id}")
def get_car(car_id: str):
    """Scheda completa di una vettura. Accetta slug, acc_car_id, nome di
    display o alias storico (es. 'BMW M4 GT3')."""
    car = cat.resolve_car(car_id)
    if not car:
        raise HTTPException(status_code=404, detail=f"Vettura non trovata: {car_id}")
    names = cat.display_names_by_id()
    return {**car, "display_name": names.get(car["id"], cat.display_name_car(car))}


@router.get("/catalog/track/{track_id}")
def get_track(track_id: str):
    """Scheda completa di un circuito. Accetta slug, acc_track_id, nome
    ufficiale, soprannome o alias storico (es. 'Monza')."""
    track = cat.resolve_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Circuito non trovato: {track_id}")
    # short_name non è nel JSON (è derivato): va aggiunto anche qui, non solo
    # nell'indice, altrimenti il client lo riceve solo a volte. Stesso motivo
    # per le due bandierine: la scheda deve poter dire da sola se esiste una
    # guida e se il layout è stato verificato, senza che il client indovini.
    return {
        **track,
        "short_name": cat.short_name_track(track),
        "ha_guida": cat.has_guide(track),
        "mappa_verificata": cat.map_verified(track),
    }


@router.get("/catalog/track/{track_id}/guida")
def get_track_guide(track_id: str):
    """La guida di un circuito: settori, curva per curva, pit, meteo, chicche.

    Rotta separata dalla scheda perché una guida pesa 15-29 KB e serve solo a
    chi apre davvero il circuito. 404 quando la guida non c'è ancora: sono 4
    su 25, e il client mostra la scheda senza inventare niente.
    """
    track = cat.resolve_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Circuito non trovato: {track_id}")
    guida = cat.track_guide(track.get("id"))
    if guida is None:
        raise HTTPException(
            status_code=404,
            detail=f"Guida non disponibile per il circuito: {track.get('id')}",
        )
    return guida
