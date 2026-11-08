# Auditoría del reporte integral antes del rediseño V4

Se inspeccionaron los PDF existentes de `output/pdf/` (base: 62 páginas; personalizado: 61 páginas) y el generador de `pydi/reporting/`. La revisión visual se hizo con hojas de contacto de **todas** las páginas de ambos archivos. El Word local `Industrial_App_Referencias_para_Codex/referencias/Proyecto PYDI (1).docx` está disponible; los ocho libros de la guía no se hallaron en las carpetas revisadas. Las referencias metodológicas proceden de la guía, sin afirmar cotejo de páginas originales en esta máquina.

| Prioridad | Página anterior | Defecto comprobado | Componente | Corrección V4 |
|---|---:|---|---|---|
| Alta | 21 (base) | La rejilla de estiba parece un patrón certificado aunque falta capacidad nominal de tarima. | `charts.figures_for_section(11)` | Rotular como cabida geométrica y separar restricciones de carga; no dibujar un alzado sin dimensiones. |
| Alta | 29 y 47 (base) | El plano usa posiciones ilustrativas con ejes en metros y se presenta como layout; puede confundirse con geometría medida. | `v2_charts.layout_chart` invocado desde el reporte | Sustituir en el PDF por una red topológica con flechas y leyenda «ESQUEMA NO A ESCALA». |
| Alta | 33-34 (base) | Ishikawa muestra seis ramas con causas sin capturar. | `charts.figures_for_section(17)` | Suprimir la figura cuando no hay causas concretas; mostrar campos requeridos. |
| Alta | 52-53 (base) | Gantt de ventanas ilustrativas parece cronograma calculado pese a duraciones y precedencias ausentes. | `charts.figures_for_section(38)` | Mostrar tabla de tareas pendientes; graficar solo CPM completo. |
| Alta | 48-51 (base) | Economía se limita a tablas de plantillas vacías, sin ficha clara de datos necesarios ni distinción de LCC, VPN y recuperación. | `pdf_builder` | Incluir matriz CAPEX/OPEX y salidas solo cuando el motor tenga flujos suficientes. |
| Media | 22-28 (base) | SHA repite varias bandas de tablas de rutas; falta matriz desde-hacia y esquema de dirección/intensidad. | `pdf_builder._data_table`, `charts` | Hoja compacta de rutas I × D, matriz desde-hacia y red topológica. |
| Media | 31-33 (base) | Pareto no marca visualmente el umbral 80 %. | `charts.render_figure_png` | Gráfica técnica con barras ordenadas, acumulado y referencia 80 %. |
| Media | 5-55 (base) | Predominan tablas genéricas de campos crudos; apartados documentales no tienen ficha de método/datos requeridos. | `pdf_builder` | Registro de artefactos por apartado, tablas de ingeniería seleccionadas y notas específicas. |
| Media | 58-62 (base), 57-61 (personalizado) | El anexo de listas numeradas ocupa páginas con muy poco contenido; última página casi vacía. | `pdf_builder` | Compactar relación de figuras/tablas y controlar los saltos finales. |

Los valores y fórmulas de PYDI se conservan. La diferencia de 11.75 kg de ingredientes frente al lote nominal de 10 kg, el Pareto de 165.1 frente a 165.2 min/día y el redondeo del equilibrio permanecen advertidos. La validación después del cambio se documenta en `QA_VISUAL_REPORTE.md`.
