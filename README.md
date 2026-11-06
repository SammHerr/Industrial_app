# Industrial App V2 para estudio SHA de planta de avena con soya

Aplicación académica Streamlit para recorrer los **39 apartados** del proyecto PYDI/SHA en 14 grupos de navegación. Combina datos editables del Word, cálculos trazables, avisos de inconsistencias, gráficas dinámicas y exportación XLSX/CSV. No sustituye una medición de planta, cotización, verificación estructural o certificación sanitaria.

## Inicio en Windows PowerShell

Desde `C:\Users\herre\OneDrive\Documentos\10mo\denise`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m streamlit run sha.py
```

Abra `http://localhost:8501`. Si `.venv` ya existe, omita su creación y repita la instalación cuando cambien los requisitos. No hace falta activar el entorno. Para el MVP anterior, ejecute `python -m streamlit run sha_mvp.py` desde el entorno correspondiente.

## Uso

- **Cargar datos de ejemplo (Proyecto PYDI):** reconstruye la semilla completa `PYDI-V2-2026-11-05` desde `pydi/data/word_tables.json` y los parámetros documentales. Algunas coordenadas, ventanas y formularios llevan `[M]` ilustrativo, sin atribución al Word.
- **Limpiar todos los datos / Empezar desde cero:** vacía todas las entradas y resultados. **Deshacer limpieza** recupera el estado previo. **Desactivar valores ilustrativos [M]** retira plantillas/posiciones y deja los datos documentales.
- **Escenario:** Documento carga de nuevo la semilla; Resultado calculado conserva las entradas actuales y muestra sus resultados; Nuevo estudio limpia. Cambiar a Documento reemplaza las ediciones actuales, por lo que se recomienda descargar el XLSX antes.
- **Editar:** los editores de cada grupo cambian el estado de la sesión. `kg_lote_equiv × lotes/día` alimenta intensidad de rutas salvo un override manual explícito. La receta alimenta P-Q para ingredientes. Los resultados se recalculan en cada interacción.
- **Exportar:** el XLSX incluye todas las entradas, parámetros, origen, ediciones, fórmulas, alertas y resultados disponibles. Cada tabla de entrada y cada resultado calculado ofrece CSV. La sesión no persiste al cerrar el navegador: descargue sus datos antes.

## Organización

```text
sha.py                         Entrada V2
sha_mvp.py                     MVP anterior conservado
pydi/v2_model.py               Escenario canónico, semilla y escenario vacío
pydi/data/word_tables.json     Celdas fuente seleccionadas del Word canónico
pydi/calculations/             Funciones puras y validaciones
pydi/v2_results.py             Snapshot derivado y alertas
pydi/v2_charts.py              Gráficas dinámicas Plotly
pydi/v2_reports.py             XLSX integral
pydi/v2_ui.py                  Interfaz de 14 grupos
pydi/datos.py, calculos.py...  MVP conservado
scripts/                       Inspección y extracción reproducible del Word
tests/                         Pruebas V2 y de regresión MVP
docs/                          Inventario, matriz de trazabilidad y validación
```

## Procedencia y límites

El Word canónico es `Paquete_Codex_Industrial_App_V2_SHA/referencias_v2/Proyecto PYDI (1)(1).docx`. Se revisaron sus tablas y ecuaciones OMML; las imágenes `indice_PYDI_parte_1.png` y `indice_PYDI_parte_2.png` corroboran el índice 1–39. La copia anterior `Industrial_App_Referencias_para_Codex/referencias/Proyecto PYDI (1).docx` y el ejemplo BITS se conservan; BITS no aporta datos al modelo.

`[D]` es declarado en el Word, `[S]` supuesto allí expresado, `[C]` cálculo, `[M]` método o ejemplo complementario y `[U]` edición del usuario. Las páginas físicas están en [docs/MATRIZ_TRAZABILIDAD.md](docs/MATRIZ_TRAZABILIDAD.md). Las fórmulas y sus condiciones están en [docs/INVENTARIO_FORMULAS_PYDI.md](docs/INVENTARIO_FORMULAS_PYDI.md). El Word y las imágenes del índice quedan locales y excluidos de Git.

Discrepancias conservadas: receta **11.75 kg** vs lote objetivo **10 kg**; punto de equilibrio Word **8,055** vs recomputado **8,056.7316 / 8,057** bolsas enteras; P-Q **2,553.1** kg sumados vs **2,553.0** textual; Pareto **165.1** vs **165.2** min/día. Las rutas están redondeadas. El precio/CVU de 500 g no están documentados y no se extrapolan de 250 g.

Los apartados 8, 21–30, 32–36 y parte de 38 son formularios o complementos porque el Word carece de insumos completos. LCC, VPN y payback del Word figuran como referencias, sin recomputarse a partir de flujos inventados; el análisis de sensibilidad LCC usa límites de tasa editables y requiere costos capturados. El diagrama de planta usa posiciones ilustrativas `[M]`; no cambia las distancias documentales. Las 12 semanas del cronograma son referencia `[D]`; CPM solo aparece al capturar una red completa y acíclica.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m compileall -q sha.py pydi scripts tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
```

La aplicación también se comprobó en navegador: edición de lotes/día, recalculado mensual, limpieza y recarga, navegación de los 14 grupos y exportación disponible. Los resultados de la última validación están en [docs/VALIDACION_V2.md](docs/VALIDACION_V2.md).
