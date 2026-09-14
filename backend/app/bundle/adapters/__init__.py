"""app.bundle.adapters — leggono i file delle fonti e producono pezzi di bundle."""

from app.bundle.adapters.acc_results import (  # noqa: F401
    Partecipante,
    ResultsAccError,
    elenca_partecipanti,
    leggi_results_acc,
)
from app.bundle.adapters.acc_setup import SetupAccError, leggi_setup_acc  # noqa: F401
from app.bundle.adapters.lettura import FileAccIllegibile, carica_json, decodifica  # noqa: F401
