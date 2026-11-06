"""CPM [M] solo para una red acíclica y completamente capturada."""

import pandas as pd

from .common import frame, number, unique_text


def cpm(df: pd.DataFrame) -> pd.DataFrame:
    data = frame(df, ("id", "actividad", "duracion_semanas", "predecesoras"), "Cronograma")
    unique_text(data, "id", "Cronograma")
    ids = set(data["id"].astype(str))
    durations = {str(r.id): number(r.duracion_semanas, f"Duración {r.id}", positive=True) for r in data.itertuples()}
    pred = {}
    for row in data.itertuples():
        names = [x.strip() for x in str(row.predecesoras or "").split(",") if x.strip()]
        if any(x not in ids or x == str(row.id) for x in names):
            raise ValueError(f"Cronograma: predecesora inválida de {row.id}.")
        pred[str(row.id)] = names
    pending = set(ids)
    order = []
    while pending:
        ready = sorted(node for node in pending if set(pred[node]) <= set(order))
        if not ready:
            raise ValueError("Cronograma: dependencias cíclicas.")
        order.extend(ready)
        pending.difference_update(ready)
    early_start = {}
    early_finish = {}
    for node in order:
        early_start[node] = max((early_finish[p] for p in pred[node]), default=0.0)
        early_finish[node] = early_start[node] + durations[node]
    project = max(early_finish.values())
    successors = {node: [other for other in ids if node in pred[other]] for node in ids}
    late_finish, late_start = {}, {}
    for node in reversed(order):
        late_finish[node] = min((late_start[s] for s in successors[node]), default=project)
        late_start[node] = late_finish[node] - durations[node]
    data["ES"] = data["id"].map(early_start)
    data["EF"] = data["id"].map(early_finish)
    data["LS"] = data["id"].map(late_start)
    data["LF"] = data["id"].map(late_finish)
    data["holgura_semanas"] = data["LS"] - data["ES"]
    data["critica"] = data["holgura_semanas"].abs() < 1e-9
    return data
