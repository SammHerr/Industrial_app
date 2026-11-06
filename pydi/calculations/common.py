"""Validaciones compartidas: nunca convertir ausencias en observaciones cero."""

import math

import pandas as pd


def number(value, label: str, *, positive: bool = False) -> float:
    if value is None or (isinstance(value, str) and value.strip() == "") or pd.isna(value):
        raise ValueError(f"{label}: falta el dato.")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: se requiere un número.") from exc
    if not math.isfinite(result) or result < 0 or (positive and result == 0):
        bound = "mayor que cero" if positive else "no negativo"
        raise ValueError(f"{label}: se requiere un valor finito {bound}.")
    return result


def frame(df: pd.DataFrame, fields: tuple[str, ...], label: str, *, allow_empty: bool = False) -> pd.DataFrame:
    if df is None or (df.empty and not allow_empty):
        raise ValueError(f"{label}: sin datos.")
    missing = set(fields) - set(df.columns)
    if missing:
        raise ValueError(f"{label}: columnas faltantes {', '.join(sorted(missing))}.")
    return df.copy().reset_index(drop=True)


def unique_text(df: pd.DataFrame, field: str, label: str) -> None:
    if df[field].isna().any() or df[field].astype(str).str.strip().eq("").any():
        raise ValueError(f"{label}: {field} vacío.")
    if df[field].astype(str).str.strip().str.casefold().duplicated().any():
        raise ValueError(f"{label}: {field} duplicado.")


def reduction(base: float, proposed: float) -> float | None:
    return None if base <= 0 else (base - proposed) / base * 100
