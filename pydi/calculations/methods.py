"""Evaluación mínima compartida de candidatos de manejo."""

import pandas as pd


def method_assessment(capacity_kg: object, hygiene_verified: object, ergonomics_verified: object) -> str:
    complete = pd.notna(capacity_kg) and pd.notna(hygiene_verified) and pd.notna(ergonomics_verified)
    adequate = complete and hygiene_verified == True and ergonomics_verified == True
    return "Apto según campos capturados [M]" if adequate else "No evaluable / restricción pendiente"
