"""
csv_parser.py — PitWall.AI MVP
Modulo di parsing e validazione schema CSV sessione ACC.

Responsabilità:
  - Validare schema e tipi CSV
  - Estrarre medie e statistica dai dati numerici
  - Restituire un dict strutturato o sollevare CSVParseError

NON fa:
  - Chiamate LLM
  - Logica di dominio ACC avanzata
"""

import pandas as pd
from io import BytesIO, StringIO
from typing import Dict, List, Union


class CSVParseError(Exception):
    """Eccezione sollevata per problemi di parsing/validazione CSV."""
    pass


REQUIRED_COLUMNS = {"lap", "fuel_cons"}
OPTIONAL_COLUMNS = {
    "tire_press_fl", "tire_press_fr", "tire_press_rl", "tire_press_rr",
    "tire_temp_fl", "tire_temp_fr", "tire_temp_rl", "tire_temp_rr",
}
ALL_KNOWN_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS

VALUE_RANGES = {
    "lap": (1, 200),
    "fuel_cons": (0.5, 8.0),
    "tire_press_fl": (24.0, 30.0),
    "tire_press_fr": (24.0, 30.0),
    "tire_press_rl": (24.0, 30.0),
    "tire_press_rr": (24.0, 30.0),
    "tire_temp_fl": (20.0, 130.0),
    "tire_temp_fr": (20.0, 130.0),
    "tire_temp_rl": (20.0, 130.0),
    "tire_temp_rr": (20.0, 130.0),
}

EXPECTED_TYPES = {
    "lap": "int",
    "fuel_cons": "float",
    "tire_press_fl": "float",
    "tire_press_fr": "float",
    "tire_press_rl": "float",
    "tire_press_rr": "float",
    "tire_temp_fl": "float",
    "tire_temp_fr": "float",
    "tire_temp_rl": "float",
    "tire_temp_rr": "float",
}


def parse_session_csv(file_input: Union[str, BytesIO, StringIO]) -> Dict:
    """Legge, valida e normalizza un CSV di sessione ACC."""
    df = _read_csv_safe(file_input)
    df = _normalize_columns(df)

    schema_errors = validate_schema(df)
    if schema_errors:
        raise CSVParseError(
            "File CSV non valido per ACC. "
            f"Errori di schema: {', '.join(schema_errors)}"
        )

    df = _cast_types(df)
    _validate_value_ranges(df)

    if df.empty:
        raise CSVParseError(
            "Il file non contiene righe valide dopo la conversione dei tipi."
        )

    averages = extract_averages(df)

    return {
        "laps_count": int(df["lap"].count()),
        "lap": df["lap"].astype(int).tolist(),
        "fuel_cons_avg": float(df["fuel_cons"].mean()),
        "fuel_cons_per_lap": df["fuel_cons"].astype(float).tolist(),
        "pressures": _build_stat_block(df, "tire_press_"),
        "temperatures": _build_stat_block(df, "tire_temp_"),
        "temperature_series": _build_series_block(df, "tire_temp_"),
        "has_pressure_data": any(col in df.columns for col in OPTIONAL_COLUMNS if "press" in col),
        "has_temp_data": any(col in df.columns for col in OPTIONAL_COLUMNS if "temp" in col),
        "averages": averages,
        "raw_df_summary": _summarize_df(df),
        "validation_errors": schema_errors,
        "warnings": df.attrs.get("range_violations", []),
    }


def _summarize_df(df: pd.DataFrame) -> str:
    return df.head(5).to_string(index=False)


def validate_schema(df: pd.DataFrame) -> List[str]:
    """Verifica che il DataFrame segua lo schema ACC atteso."""
    errors: List[str] = []
    columns = {col.strip().lower() for col in df.columns}

    missing_required = REQUIRED_COLUMNS - columns
    if missing_required:
        errors.append(
            f"Mancano colonne obbligatorie: {', '.join(sorted(missing_required))}"
        )

    unknown_columns = columns - ALL_KNOWN_COLUMNS
    if unknown_columns:
        errors.append(
            f"Colonne non riconosciute: {', '.join(sorted(unknown_columns))}"
        )

    return errors


def extract_averages(df: pd.DataFrame) -> Dict[str, float]:
    """Restituisce le medie delle colonne numeriche note presenti nel DataFrame."""
    averages: Dict[str, float] = {}
    for col in sorted(df.columns):
        if col in EXPECTED_TYPES and pd.api.types.is_numeric_dtype(df[col]):
            averages[col] = float(df[col].mean())
    return averages


def _read_csv_safe(file_input: Union[str, BytesIO, StringIO]) -> pd.DataFrame:
    try:
        if isinstance(file_input, str):
            df = pd.read_csv(file_input)
        else:
            df = pd.read_csv(file_input)
    except Exception as exc:
        raise CSVParseError(
            "Il file non è un CSV valido di ACC. Verifica il formato."
        ) from exc

    if df.empty:
        raise CSVParseError(
            "Il file non è un CSV valido di ACC. Verifica il formato. "
            "(Il file è vuoto.)"
        )
    return df


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [col.strip().lower() for col in df.columns]
    return df


def _cast_types(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        expected = EXPECTED_TYPES.get(col)
        if not expected:
            continue
        if expected == "int":
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.dropna(subset=[col])
            df[col] = df[col].astype(int)
        elif expected == "float":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=list(REQUIRED_COLUMNS))
    return df


def _validate_value_ranges(df: pd.DataFrame) -> None:
    violations: List[str] = []
    for col, (low, high) in VALUE_RANGES.items():
        if col not in df.columns:
            continue
        out_of_range = df[(df[col].notna()) & ((df[col] < low) | (df[col] > high))]
        if not out_of_range.empty:
            if col in REQUIRED_COLUMNS and len(out_of_range) == len(df):
                raise CSVParseError(
                    "Il file non è un CSV valido di ACC. Verifica il formato. "
                    f"(Tutti i valori della colonna '{col}' sono fuori dal range "
                    f"atteso [{low}–{high}].)"
                )
            violations.append(
                f"{col}: {len(out_of_range)} righe fuori range [{low}–{high}]"
            )
    df.attrs["range_violations"] = violations


def _build_stat_block(df: pd.DataFrame, prefix: str) -> Dict[str, Dict[str, float]] | None:
    stats: Dict[str, Dict[str, float]] = {}
    for position in ["fl", "fr", "rl", "rr"]:
        col = f"{prefix}{position}"
        if col in df.columns:
            values = df[col].dropna().astype(float)
            if not values.empty:
                stats[position] = {
                    "avg": float(values.mean()),
                    "min": float(values.min()),
                    "max": float(values.max()),
                }
    return stats if stats else None


def _build_series_block(df: pd.DataFrame, prefix: str) -> Dict[str, list] | None:
    stats: Dict[str, list] = {}
    for position in ["fl", "fr", "rl", "rr"]:
        col = f"{prefix}{position}"
        if col in df.columns:
            values = df[col].dropna().astype(float).tolist()
            if values:
                stats[position] = values
    return stats if stats else None
