#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_dir"

python="$project_dir/.venv/bin/python"
if [ ! -x "$python" ]; then
    printf '%s\n' "Error: falta el entorno virtual de macOS en $project_dir/.venv." >&2
    printf '%s\n' "Créelo con: python3.12 -m venv .venv" >&2
    exit 1
fi

if ! "$python" -c 'import streamlit' >/dev/null 2>&1; then
    printf '%s\n' "Error: Streamlit no está instalado en .venv." >&2
    printf '%s\n' "Instálelo con: ./.venv/bin/python -m pip install -r requirements.txt" >&2
    exit 1
fi

port=$("$python" - <<'PY'
import socket

for candidate in range(8501, 8511):
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", candidate))
        except OSError:
            continue
    print(candidate)
    break
PY
)

if [ -z "$port" ]; then
    printf '%s\n' 'Error: no hay un puerto local libre entre 8501 y 8510.' >&2
    exit 1
fi
if [ "$port" != 8501 ]; then
    printf '%s\n' "El puerto 8501 está ocupado; proceso detectado:" >&2
    lsof -nP -iTCP:8501 -sTCP:LISTEN >&2 || true
fi

printf '%s\n' "Industrial App V3: http://127.0.0.1:$port (Ctrl+C para detener)"
exec "$python" -m streamlit run sha.py --server.address 127.0.0.1 --server.port "$port"
