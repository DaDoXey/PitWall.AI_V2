"""GET /api/setup-params — le 5 sezioni × 49 parametri ACC, con la regola della vettura.

Dalla Entry #058 ogni parametro porta `regola`: come il click del file di ACC diventa il
valore che il gioco mostra per quella vettura (`car` = carName di ACC, es.
«bmw_m4_gt3»), oppure `null` se non c'è una regola usabile (vettura senza tabella, o
parametro ancora DA_VERIFICARE). I min/max/default generici restano nella risposta per
compatibilità, ma la pagina Setup lavora in click e non li usa.
"""

from fastapi import APIRouter

from app.core.setup_params import get_params_for_car, regole_vettura

router = APIRouter()


@router.get("/setup-params")
def get_setup_params(car: str | None = None, track: str | None = None):
    sezioni = get_params_for_car(car, track)
    regole = regole_vettura(car)
    for sezione in sezioni.values():
        for chiave, parametro in sezione["params"].items():
            parametro["regola"] = regole.get(chiave)
    return sezioni
