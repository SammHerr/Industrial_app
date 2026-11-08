# Industrial App V3 en macOS

## Equipo y requisitos

Instalación comprobada el 6 de noviembre de 2026 en macOS 26.6.2, Apple Silicon (ARM64), con Python 3.12.3 de Python.org. Se requiere Python 3.12, acceso a Internet para instalar paquetes de PyPI y permiso de escritura en `~/Library/Application Support/IndustrialApp/data`. Homebrew no fue necesario. Las herramientas de línea de comandos de Xcode tampoco son necesarias para las dependencias actuales.

La raíz del proyecto es `/Users/miguelalejandrosantiagodeleon/Downloads/denise`. El `.venv` recibido era de Windows y se conservó como `.venv.windows-backup-20261106`; el `.venv` activo es nativo de macOS.

## Instalación y dependencias

Desde la raíz del proyecto:

```sh
python3.12 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip setuptools wheel
./.venv/bin/python -m pip install -r requirements-dev.txt
./.venv/bin/python -m pip check
```

`requirements-dev.txt` incluye `requirements.txt`. Las dependencias directas instaladas son Streamlit 1.67.0, pandas 2.3.3, Plotly 6.9.0, openpyxl 3.1.5, python-barcode 0.16.1, qrcode 8.2, ReportLab 4.5.1, pytest 9.2.0, Ruff 0.17.4, python-docx 1.2.0 y pypdf 6.21.4. Pillow 13.0.0 se instala para imágenes de etiquetas. SQLite forma parte de Python 3.12.

Para reinstalar o actualizar solo las dependencias declaradas en este entorno, ejecute `./.venv/bin/python -m pip install -r requirements-dev.txt`. No use el entorno de Windows ni instale estas bibliotecas globalmente.

## Iniciar y detener

```sh
cd /Users/miguelalejandrosantiagodeleon/Downloads/denise
./run_mac.sh
```

Abra la dirección que imprima el script. Prefiere `http://127.0.0.1:8501`; si ese puerto está ocupado, identifica el proceso y elige el primer puerto local libre hasta 8510. El puerto elegido se fija también en Streamlit, por lo que la dirección anunciada coincide con la real. El servicio usa solo `127.0.0.1` y no se expone a la red. Deténgalo con `Ctrl+C` en la terminal que ejecuta el script. No detenga procesos ajenos.

## Base de datos y respaldos

La base operativa predeterminada en macOS es:

```text
/Users/miguelalejandrosantiagodeleon/Library/Application Support/IndustrialApp/data/industrial_app.db
```

La variable `INDUSTRIAL_APP_DB_PATH` permite elegir otra ruta. Windows conserva `%LOCALAPPDATA%\IndustrialApp\data\industrial_app.db`. No se trasladó la base `v3_browser_smoke.db` recibida en el proyecto: tiene datos de prueba y permanece intacta. La base operativa nueva contiene el catálogo PYDI, sin unidades físicas ni ventas inventadas.

Para respaldar una base en uso, abra **Códigos e inventario V3 → Configuración/catálogos → Crear respaldo no destructivo de SQLite**. La copia se guarda junto a la base con sufijo `.bak.db`. Compruebe que el archivo nuevo existe antes de moverlo a otra ubicación. Para una copia manual, cierre primero la app y copie `industrial_app.db`; con la app abierta podrían existir archivos WAL/SHM pendientes. No sustituya la base operativa con un respaldo mientras la app siga abierta.

## Verificación y solución de problemas

```sh
./.venv/bin/python -m pytest -q
./.venv/bin/python -m ruff check .
./.venv/bin/python -m compileall -q sha.py pydi
./.venv/bin/python -m pip check
```

En esta instalación pasaron 34 pruebas. La suite usa SQLite temporal para comprobar altas, unicidad de IDs, QR, Code 128, PDF A4, inventario, kardex, ventas atómicas, rechazo de ventas duplicadas, persistencia y funciones V2. La página respondió con HTTP 200 y el endpoint de salud respondió `ok`.

Si `./run_mac.sh` indica que falta el entorno, créelo con Python 3.12 e instale los requisitos. Si indica que falta Streamlit, repita la instalación de requisitos. Si macOS bloquea la escritura de la base, conceda acceso a la carpeta de Application Support al usuario que ejecuta la app; no cambie permisos generales del sistema. Streamlit puede sugerir instalar `watchdog` o las herramientas de Xcode para mejorar la recarga; son opcionales y la aplicación funciona sin ellas.
