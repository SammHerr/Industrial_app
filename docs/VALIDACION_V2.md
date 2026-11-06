# Validación de Industrial App V2

Fecha local: 2026-11-06. Rama: `feature/pydi-sha-completo-v2`. Fuente principal: `Paquete_Codex_Industrial_App_V2_SHA/referencias_v2/Proyecto PYDI (1)(1).docx` y las dos imágenes del índice; archivos de referencia conservados localmente y excluidos de Git.

## Controles ejecutados

| Comprobación | Resultado |
|---|---|
| `python -m compileall -q sha.py sha_mvp.py pydi scripts tests` | Correcto |
| `python -m pytest -q` | 24 pruebas aprobadas, incluidas 11 del MVP |
| `ruff check .` | Sin hallazgos |
| Exportación desde ejemplo PYDI | XLSX válido de 53 hojas: 38 entradas, 9 resultados y 6 hojas de estado/procedencia |
| Escenario nuevo | 38 tablas vacías, todos los parámetros nulos, sin indicadores ni resultados residuales |
| Interfaz Streamlit en navegador | Navegación de 14 grupos y 39 títulos, limpieza, recarga, cambio de lotes/día 7.75→8 y actualización mensual 6,448/806→6,656/832 bolsas; sin excepción observada |

La etiqueta SVG Code 128, el consolidado PQRST exportado, el plano con rutas y la sensibilidad LCC se verificaron con pruebas unitarias tras el recorrido del navegador. El servidor local se lanzó con `python -m streamlit run sha.py`.

## Valores de control del ejemplo

| Control | Valor recalculado | Comparación documental |
|---|---:|---|
| Disponibilidad | 28,200 s/turno | Word §2 |
| Capacidad base | 2.7647 lotes/turno, 2 completos | Word §2 |
| Masa de receta | 11.75 kg/lote | Objetivo declarado: 10 kg/lote |
| Costo ingredientes + empaque | $425 + $30 = $455 MXN/lote | Word §1 |
| Producción propuesta | 201.5 lotes/mes; 6,448 bolsas de 250 g; 806 de 500 g | Word §2/12 |
| Equilibrio 250 g | 8,056.7316; 8,057 bolsas enteras | Word reporta 8,055 |
| P-Q sumado | 2,553.1 kg/mes | Word reporta 2,553.0 |
| Pareto sumado | 165.1 min/día | Word reporta 165.2 |

Los resultados económicos del Word (LCC, VPN, payback) se muestran como referencias sin validación numérica porque faltan flujos. La auditoría mantiene las metas sin inventar mediciones; el CPM solo se calcula tras capturar dependencias y duraciones. Las coordenadas del plano y los límites de sensibilidad del ejemplo llevan `[M]`.
