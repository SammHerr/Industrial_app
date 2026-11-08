# Reporte técnico integral V4 en PDF

## Uso en Windows

Desde la raíz del proyecto:

```powershell
.\.venv-win\Scripts\python.exe -m streamlit run sha.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --server.fileWatcherType none --browser.gatherUsageStats false
```

Abra `http://127.0.0.1:8501`, seleccione **Reporte técnico integral PDF** en la barra lateral, elija **Datos base PYDI** o **Datos personalizados actuales**, pulse **Generar reporte PDF** y descargue el archivo. La modalidad base toma una semilla nueva; la personalizada copia el estado actual, recalcula y conserva las celdas vacías. Un cambio posterior de modalidad, caso o portada invalida la descarga anterior hasta regenerar. El PDF se arma en memoria y no consulta SQLite; la exportación de etiquetas QR/Code 128 de V3 sigue separada.

## Contenido y procedencia

El documento contiene portada con modalidad y huella del caso, índice con páginas reales, resumen ejecutivo, 39 apartados numerados, conclusiones, glosario y bibliografía. Cada apartado declara objetivo, método, referencias, fórmulas pertinentes, parámetros, tablas técnicas, resultados calculables, figuras originales cuando hay datos y faltantes específicos. Las tablas tienen encabezados repetidos y bandas para columnas extensas. Las figuras se generan desde el mismo escenario y motor que la interfaz.

La fuente documental principal es `Industrial_App_Referencias_para_Codex/referencias/Proyecto PYDI (1).docx`. Los valores se encuentran en `pydi/data/word_tables.json` y `pydi/v2_model.py`; los resultados provienen de `pydi/v2_results.py` y `pydi/calculations/`. El `ReportSnapshot` conserva una copia independiente de entradas, resultados, alertas, versión, fecha y huella. `[D]`: documental; `[S]`: supuesto del documento; `[C]`: calculado; `[M]`: complemento metodológico; `[U]`: editado por el usuario.

Las nuevas salidas incluyen secuencia de proceso, hoja P-Q-R-S-T, rutas T.W. por fila, matriz desde-hacia, dispersión distancia–intensidad, red topológica **sin escala**, Pareto con acumulado 80 %, Ishikawa solo con causas capturadas, matriz triangular SLP A/E/I/O/U y curva financiera solo con flujos completos. Las figuras del motor V2 (P-Q, equilibrio, estiba, producción, localización, LCC, sensibilidad, Gantt, auditoría) se conservan cuando su representación es válida. La matriz SLP es una sugerencia por intensidad relativa y no afirma incompatibilidades `X` no documentadas.

El reporte conserva las discrepancias del caso: receta de 11.75 kg frente a lote objetivo de 10 kg, tiempos Pareto de 165.1/165.2 min, redondeos de transporte y equilibrio, y cifras financieras del Word sin flujos verificables. No rellena un campo personalizado vacío con el valor base. No genera un plano a escala, Ishikawa vacío, Gantt sin duraciones, VPN/TIR ni recomendación económica cuando falta sustento.

Consulte [la matriz de los 39 apartados](MATRIZ_COBERTURA_REPORTE_39.md), [las referencias](REDISENO_REPORTE_REFERENCIAS.md) y [la auditoría visual](QA_VISUAL_REPORTE.md).

## Dependencias y QA

Las dependencias de ejecución están en `requirements.txt`. Pytest, Ruff, pypdf y PyMuPDF se instalaron en `.venv-win` para pruebas y revisión; PyMuPDF se usa solo en el script de inspección. El PDF se genera con ReportLab y PNG locales de Matplotlib, sin Chrome ni conexión de red.

```powershell
.\.venv-win\Scripts\python.exe -m scripts.generate_report_v4_qa --output C:\ruta\temporal\qa_v4
.\.venv-win\Scripts\python.exe -m scripts.inspect_report_v4_qa --input C:\ruta\temporal\qa_v4 --output C:\ruta\temporal\qa_v4\contactos
.\.venv-win\Scripts\python.exe -m pytest -q
.\.venv-win\Scripts\python.exe -m ruff check .
.\.venv-win\Scripts\python.exe -m compileall -q sha.py pydi
.\.venv-win\Scripts\python.exe -m pip check
```

Los scripts de QA no abren la base operativa. Para la verificación de inventario/ventas se usa una base de prueba aislada; jamás se limpia la DB mediante los botones globales del caso.
