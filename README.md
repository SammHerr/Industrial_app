# Industrial App V3 para estudio SHA y trazabilidad PYDI

Aplicación Streamlit con los **39 apartados V2** del proyecto PYDI/SHA, más el módulo V3 **Códigos e inventario**. V2 conserva sus cálculos, gráficas y exportaciones. V3 registra unidades físicas y lotes reales en SQLite, produce QR/Code 128 y PDF A4, consulta trazabilidad y registra ventas internas.

## Inicio en Windows PowerShell

Desde `C:\Users\herre\OneDrive\Documentos\10mo\denise`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m streamlit run sha.py
```

Abra `http://localhost:8501`. Si `.venv` ya existe, omita su creación y repita la instalación cuando cambien los requisitos. No hace falta activar el entorno. Para el MVP anterior, ejecute `.\.venv\Scripts\python.exe -m streamlit run sha_mvp.py`.

## Datos persistentes V3

La base predeterminada es `%LOCALAPPDATA%\IndustrialApp\data\industrial_app.db` (en este equipo, `C:\Users\herre\AppData\Local\IndustrialApp\data\industrial_app.db`). Está fuera de OneDrive. Para elegir otra ruta, configure `INDUSTRIAL_APP_DB_PATH` antes de iniciar Streamlit. La pestaña **Configuración/catálogos** muestra la ruta efectiva y crea un respaldo SQLite bajo demanda. La primera inicialización crea el esquema y los catálogos; no crea existencias vendibles. Antes de migrar una base existente se genera una copia `.bak.db` en el mismo directorio. Los archivos `.db`, WAL/SHM, respaldos, PDF y exportaciones están ignorados por Git.

En **Generar**, confirme el alta física de una de las tres categorías: producto terminado (cada bolsa tiene ID), materia prima (cada lote/contenedor tiene saldo en gramos) o maquinaria adquirida (cada activo tiene ID). El catálogo PYDI incluye bolsas de 250 g y 500 g; solo la de 250 g tiene precio documental de $35 MXN. Cree una tercera presentación con nombre, gramos, SKU y precio propios en Configuración. No se presupone su tamaño ni precio. Los equipos propuestos aparecen solo en el catálogo hasta que se confirme adquisición física.

Los lectores USB tipo teclado introducen el ID en **Consultar** o **Punto de venta**; también puede pegarlo manualmente. QR y Code 128 contienen el mismo ID opaco `PT-`, `MP-` o `MQ-`. Code 128 es **trazabilidad interna**, no un GTIN, EAN o código GS1 asignado. El PDF A4 ordena hasta 200 etiquetas existentes por categoría, producto, lote y código; la reimpresión no crea registros. Vender requiere una bolsa DISPONIBLE con precio. La venta guarda precio en centavos, folio, líneas, salida de stock y auditoría en una transacción. Una bolsa vendida sale del inventario activo y sigue en Consulta e Historial. Este registro de venta **no cobra, factura ni emite CFDI**.

Los botones globales V2 de cargar ejemplo y limpiar solo alteran formularios y filtros de sesión; nunca borran ni recrean códigos, inventario o ventas. El respaldo de Configuración copia la base sin borrar la original. Para restaurarlo, cierre la app y siga un procedimiento administrativo de recuperación de SQLite; no se ofrece sustitución automática ni anulación de ventas desde la interfaz.

SQLite local es adecuado para uso en una máquina o concurrencia ligera. Mantenga la base fuera de carpetas sincronizadas y controle quién puede acceder al archivo. Para un despliegue multiusuario con cuentas, permisos y mayor concurrencia, migre a PostgreSQL con autenticación y roles; esta versión no implementa ese servidor.

## Uso

- **Cargar datos de ejemplo (Proyecto PYDI):** reconstruye la semilla completa `PYDI-V2-2026-11-05` desde `pydi/data/word_tables.json` y los parámetros documentales. Algunas coordenadas, ventanas y formularios llevan `[M]` ilustrativo, sin atribución al Word.
- **Limpiar todos los datos / Empezar desde cero:** vacía todas las entradas y resultados. **Deshacer limpieza** recupera el estado previo. **Desactivar valores ilustrativos [M]** retira plantillas/posiciones y deja los datos documentales.
- **Escenario:** Documento carga de nuevo la semilla; Resultado calculado conserva las entradas actuales y muestra sus resultados; Nuevo estudio limpia. Cambiar a Documento reemplaza las ediciones actuales, por lo que se recomienda descargar el XLSX antes.
- **Editar:** los editores de cada grupo cambian el estado de la sesión. `kg_lote_equiv × lotes/día` alimenta intensidad de rutas salvo un override manual explícito. La receta alimenta P-Q para ingredientes. Los resultados se recalculan en cada interacción.
- **Exportar:** el XLSX incluye todas las entradas, parámetros, origen, ediciones, fórmulas, alertas y resultados disponibles. Cada tabla de entrada y cada resultado calculado ofrece CSV. La sesión no persiste al cerrar el navegador: descargue sus datos antes.

## Organización

```text
sha.py                         Entrada V3; conserva grupos V2
sha_mvp.py                     MVP anterior conservado
pydi/inventory_db.py           SQLite, catálogo y migración v1
pydi/inventory_service.py      Altas, consumos, consultas y exportación
pydi/sales_service.py          Ventas atómicas e idempotentes
pydi/code_generator.py         IDs, QR y Code 128
pydi/labels_pdf.py             Etiquetas A4 desde registros existentes
pydi/v3_ui.py                  Interfaz persistente V3
pydi/v2_model.py               Escenario canónico, semilla y escenario vacío
pydi/data/word_tables.json     Celdas fuente seleccionadas del Word canónico
pydi/calculations/             Funciones puras y validaciones
pydi/v2_results.py             Snapshot derivado y alertas
pydi/v2_charts.py              Gráficas dinámicas Plotly
pydi/v2_reports.py             XLSX integral
pydi/v2_ui.py                  Interfaz de 14 grupos
pydi/datos.py, calculos.py...  MVP conservado
scripts/                       Inspección y extracción reproducible del Word
tests/                         Pruebas V3, V2 y de regresión MVP
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

La validación V3 y sus límites están en [docs/VALIDACION_V3.md](docs/VALIDACION_V3.md). El esquema y las reglas transaccionales están en [docs/ARQUITECTURA_V3.md](docs/ARQUITECTURA_V3.md). La comprobación V2 anterior permanece en [docs/VALIDACION_V2.md](docs/VALIDACION_V2.md).
