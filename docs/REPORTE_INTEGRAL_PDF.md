# Reporte técnico integral en PDF

## Uso

Inicie Industrial App V3 con `./run_mac.sh` en macOS, o con `python -m streamlit run sha.py` dentro del entorno virtual en Windows. En el último grupo de la barra lateral, abra **Reporte técnico integral PDF**. Seleccione **Datos base PYDI** o **Datos personalizados actuales**, complete los datos opcionales de portada y revise los 39 apartados y las advertencias. Pulse **Generar reporte PDF** y luego **Descargar reporte PDF**. El nombre incorpora fecha y hora. Para imprimir, abra el archivo descargado en un lector PDF y use papel A4 a escala real.

La modalidad base crea una copia nueva de la semilla PYDI. No reemplaza los formularios actuales. La modalidad personalizada toma una copia de las tablas y parámetros de la sesión, recalcula con `compute_case` y conserva las celdas vacías. Si cambia el escenario, la modalidad o los datos de portada después de generar, la descarga anterior se oculta hasta regenerar.

## Contenido y procedencia

El documento incluye portada, índice con páginas reales, resumen ejecutivo, los apartados 1 a 39 en el orden del Word, conclusiones y anexos de fórmulas, advertencias, figuras y tablas. Cada apartado presenta las entradas y parámetros pertinentes, fórmulas documentadas cuando corresponden, resultados calculables, visualizaciones disponibles e interpretación breve. Las tablas largas se dividen entre páginas con encabezados repetidos; las tablas anchas se presentan en bandas con la primera columna repetida.

El Word canónico es `Paquete_Codex_Industrial_App_V2_SHA/referencias_v2/Proyecto PYDI (1)(1).docx`. La semilla se define en `pydi/v2_model.py` y `pydi/data/word_tables.json`. `[D]` indica valor del documento; `[S]`, supuesto documental; `[C]`, resultado calculado; `[M]`, método o dato ilustrativo complementario; `[U]`, edición del usuario. Los cálculos provienen de `pydi/v2_results.py` y `pydi/calculations/`; el PDF no tiene fórmulas industriales independientes. Las figuras parten de los mismos constructores Plotly de `pydi/v2_charts.py` y se dibujan en PNG mediante Matplotlib para incrustarlas sin navegador ni Internet. El Code 128 del apartado 25 usa la misma función de vista previa de la interfaz.

El informe conserva las discrepancias documentales: ingredientes de 11.75 kg frente al lote objetivo de 10 kg, redondeos de transporte y equilibrio, y cifras económicas sin flujos suficientes para verificarlas. Cuando faltan datos, el apartado señala el campo o resultado pendiente; las cifras base no rellenan un campo personalizado vacío. Algunas secciones son formularios documentales y no tienen cálculo o figura propios. Los planos usan coordenadas conceptuales `[M]` y no acreditan distancias medidas. LCC, VPN y recuperación requieren inversión y flujos capturados. El PDF no certifica equipos, operaciones, compras ni mediciones de auditoría ausentes.

## Dependencias y almacenamiento

Instale `requirements.txt` con el entorno virtual. El reporte usa ReportLab, Pillow, Pandas, Plotly y Matplotlib con el backend local Agg; no requiere Chrome, Kaleido ni acceso a Internet. `pypdf` forma parte de `requirements-dev.txt` para las pruebas. La función de generación devuelve bytes en memoria y la interfaz los guarda temporalmente en la sesión hasta la descarga. No consulta ni modifica SQLite; el PDF de etiquetas de inventario es una función separada.

## Validación

Ejecute `./.venv/bin/python -m pytest -q`, `./.venv/bin/python -m ruff check .`, `./.venv/bin/python -m compileall -q sha.py pydi` y `./.venv/bin/python -m pip check`. Las pruebas del reporte comprueban cobertura, escenario personalizado, celdas vacías, tablas extensas, imágenes, extracción de texto y aislamiento del estado. La inspección visual de los dos PDF de ejemplo se realizó sobre todas sus páginas renderizadas.
