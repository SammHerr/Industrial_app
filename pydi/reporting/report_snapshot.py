"""Captura independiente y estable del escenario utilizado por un PDF."""

import pickle
from dataclasses import dataclass
from datetime import UTC, datetime

from pydi.reporting.validation import case_fingerprint
from pydi.v2_model import Case
from pydi.v2_results import Snapshot, compute_case


@dataclass(frozen=True)
class ReportSnapshot:
    mode: str
    fingerprint: str
    case_version: str
    generated_at: datetime
    _case_bytes: bytes
    _result_bytes: bytes

    @classmethod
    def capture(cls, case: Case, mode: str) -> "ReportSnapshot":
        selected = case.copy()
        result = compute_case(selected)
        return cls(mode, case_fingerprint(selected), str(selected.version),
                   datetime.now(UTC), pickle.dumps(selected), pickle.dumps(result))

    def materialize(self) -> tuple[Case, Snapshot]:
        """Devuelve copias; ningún renderizador puede alterar la captura."""
        return pickle.loads(self._case_bytes), pickle.loads(self._result_bytes)
