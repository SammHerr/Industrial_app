# Simulador SHA para planta de avena con soya

MVP académico de análisis de manejo de materiales para el caso PYDI. Permite editar el registro de materiales y las 7 R, recalcular P-Q y trabajo de transporte, comparar los métodos base y propuesto, explorar gráficas y descargar el escenario actual en Excel. No representa mediciones de una planta en operación.

## Estructura

```text
sha.py                    Interfaz de seis pestañas
pydi/datos.py             Transcripción inicial del caso
pydi/calculos.py          Validaciones, fórmulas y XLSX
pydi/graficas.py          Gráficas Plotly
tests/test_calculos.py    Pruebas de cálculo y exportación
Industrial_App_Referencias_para_Codex/referencias/  Fuentes locales
```

## Requisitos e instalación en PowerShell

Python 3.12 o superior y Git. Desde la carpeta del proyecto:

```powershell
python -m venv "$env:LOCALAPPDATA\venvs\industrial_app"
& "$env:LOCALAPPDATA\venvs\industrial_app\Scripts\Activate.ps1"
python -m pip install -r requirements-dev.txt
python -m streamlit run sha.py
```

Si la política de PowerShell impide activar el entorno, se puede invocar directamente `& "$env:LOCALAPPDATA\venvs\industrial_app\Scripts\python.exe" -m streamlit run sha.py`.

## Validación

```powershell
python -m compileall sha.py pydi tests
python -m pytest -q
ruff check .
```

Las entradas vacías, duplicadas, negativas, incompletas o no numéricas muestran un error; la exportación se desactiva hasta corregirlas. El estado de edición dura la sesión de Streamlit; no hay base de datos ni autenticación.

## Procedencia y discrepancias

Fuente principal: `Industrial_App_Referencias_para_Codex/referencias/Proyecto PYDI (1).docx`. El archivo `sha_ejemplo_BITS.py` se consultó solo como referencia de controles de Streamlit. Los valores iniciales de rutas, P-Q, 7 R y Pareto provienen del Word; los indicadores, porcentajes y acumulados se calculan en la aplicación. Las ediciones del usuario representan escenarios hipotéticos.

- Los cuatro ingredientes suman **11.75 kg**, mientras que el lote se declara de **10 kg**. Se conservan ambas cifras y la app advierte la diferencia.
- Los costos de los cuatro ingredientes y las bolsas suman **$455.00** por lote.
- Las siete masas P-Q redondeadas suman **2,553.1 kg/mes**. Se calcula el total desde las filas y no se fuerza un total textual discrepante.
- Los tiempos Pareto redondeados suman **165.1 min/día**, frente a **165.2 min/día** indicado en el total textual.
- El documento usa valores de ruta redondeados. Los totales de T.W., distancia y tiempo pueden variar ligeramente respecto de sus referencias narrativas.
- Los **7.75 lotes/día** pertenecen a la propuesta, no al ciclo secuencial base. Los precios y costos de 250 g no se aplican a las bolsas de 500 g.

## Alcance siguiente

Este MVP cubre el registro elemental, 7 R, P-Q, T.W., distancia-intensidad y Pareto. Quedan para futuras iteraciones la matriz cualitativa de cercanía A/E/I/O/U/X, cargas unitarias y estibado, desperdicios e Ishikawa, checklist, equipos, almacenamiento, picking, identificación, muelles, planes SHA completos, evaluación económica, cronograma y auditorías. Ningún umbral de porcentaje T.W. se presenta como prioridad oficial de Muther.
