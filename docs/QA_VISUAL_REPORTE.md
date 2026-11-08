# QA visual y numérica del reporte V4

## Inspección anterior y resultado

El diagnóstico previo está en `docs/AUDITORIA_REPORTE_ANTES_DESPUES.md`. Los PDF V3 existentes tenían 62 páginas (base) y 61 (personalizado). Se renderizaron **todas** sus páginas: tablas genéricas repetidas, layout con coordenadas ilustrativas que parecía medido, Ishikawa vacío, Gantt sin duraciones, ausencia de matriz desde-hacia y una página final casi vacía. El diseño V4 sustituye esas representaciones por salidas derivadas del escenario o por un aviso concreto de datos faltantes.

| Escenario de QA | Antes | V4 | Resultado |
|---|---:|---:|---|
| Datos base PYDI | 62 | 48 | 39 apartados, sin Ishikawa/Gantt/finanzas no verificables; SHA y SLP originales. |
| Datos personalizados sintéticos | 61 | 53 | Causas, 5S, LCC, flujos, VPN, CPM y Gantt aparecen al completar entradas. |

Archivos temporales fuera del árbol versionado: `C:\Users\herre\.codex\visualizations\2026\11\05\01a1adda-7b7f-7173-be75-d705357be2bd\qa_v4\Industrial_App_V4_Base.pdf` y `Industrial_App_V4_Personalizado.pdf` en esa misma carpeta. `scripts/generate_report_v4_qa.py` reproduce el par sin abrir SQLite; `scripts/inspect_report_v4_qa.py` produce hojas de contacto y comprueba estructura/márgenes.

## Revisión de todas las páginas

Se revisaron visualmente las 4 hojas de contacto finales de base (págs. 1–48) y las 5 de personalizado (págs. 1–53), además de detalles a 2× para SHA/base p.21, SLP/base p.41, Ishikawa/personalizado p.26 y flujos/personalizado p.46. El índice paginado y encabezados corresponden a la modalidad. Las tablas anchas se separan en bandas con clave repetida, las largas conservan cabecera, las figuras tienen título/leyenda/fuente, y no se observaron etiquetas cortadas ni símbolos Unicode sustituidos. La última página base reúne conclusiones y bibliografía; la personalizada termina con ese material, sin página en blanco accidental.

La inspección programática abrió ambos PDF con PyMuPDF: A4, 39 títulos presentes, índice y bibliografía extraíbles, al menos 410 caracteres por página base y 420 por página personalizada, y todas las cajas de texto dentro de los márgenes. Los contenidos no son imágenes de página completa. Los PNG son figuras incrustadas con texto tabular recuperable.

## Concordancia con Industrial App

Las cifras de PDF proceden de `compute_case`, sin fórmulas industriales paralelas. La prueba V4 verifica cada fila T.W. = intensidad × distancia, la suma base/propuesta, Pareto decreciente y acumulado al 100 %, la relación SLP con el flujo capturado, y la ausencia de Ishikawa/finanzas sin entradas. En el escenario personalizado se comprueban salidas condicionales y que los vacíos nunca se rellenan con la semilla. Comparación de resultados del motor con las tablas/figuras revisadas:

| Magnitud | Base | Personalizado sintético | Tratamiento |
|---|---:|---:|---|
| Masa ingredientes, kg/lote | 11.75 | 12.05 | Advertencia frente a objetivo documental 10 kg. |
| Equilibrio 250 g, bolsas continuas / enteras | 8,056.7316 / 8,057 | 7,929.1667 / 7,930 | Redondeo y precio/CVU visibles. |
| T.W. base, kg·m/día | 8,417.435 | 8,876.960 | Suma de rutas I×D. |
| T.W. propuesto, kg·m/día | 5,048.215 | 5,117.0632 aprox. | Igual horizonte y unidad. |
| Pareto, min/día | 165.1 | 152.1 | Se conserva aviso de 165.2 textual en Word base. |
| 5S, puntos/40 | Pendiente | 40/40 | Figura solo con 20 puntajes válidos. |
| LCC nominal A/B/C, MXN | Pendiente | 386,000 / 338,000 / 362,500 | Caso sintético de prueba; no se atribuye al Word. |
| Recuperación B/A, años; VPN, MXN | Pendiente | 1.5; 45,815.7354 | VPN descontado al 10 %; curva acumulada nominal. |

Las pruebas existentes también cubren XLSX/CSV, QR, Code 128, PDF de etiquetas, unicidad de códigos, inventario y venta única con entorno de prueba. La exportación integral se ensayó en navegador local: se descargó un PDF base de 48 páginas y uno de **datos personalizados actuales** de 48 páginas (esa sesión mantenía los valores base), y al cambiar modalidad se invalidó la descarga anterior. El personalizado sintético de 53 páginas prueba las diferencias cuantitativas y gráficas que la sesión local no había capturado.

## Base operativa

Antes y después se abrió `C:\Users\herre\AppData\Local\IndustrialApp\data\industrial_app.db` **solo en lectura**. SHA-256 idéntico: `11F805DAEF026046B0417941C0977CA449D617FFA78594C513A1B91CCF87CB60`; 98,304 bytes; `integrity_check=ok`. Conteos idénticos: `catalog_items=11`, `presentations=2`, `traceable_items=2`, `sales=1`, `sale_lines=1`, `stock_movements=3`, `audit_events=4`. La prueba de navegador usó `INDUSTRIAL_APP_DB_PATH` apuntando a una DB aislada en la carpeta temporal de QA.

## Límites de la evidencia

Los PDF de los ocho libros R1–R8 no estaban en las carpetas locales inspeccionadas. Se siguieron las páginas y convenciones declaradas en `Guia_Referencias_Visuales_PYDI_39_Apartados.md`; no se afirma cotejo directo de sus láminas. El Word PYDI sí estaba disponible. Coordenadas de planta, causas base, especificaciones de proveedor, flujos económicos originales, duraciones base y mediciones de auditoría continúan pendientes donde el proyecto no ofrece datos verificables.
