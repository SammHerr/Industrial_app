# Validación Industrial App V3

Fecha local: 2026-11-06. Rama `feature/pydi-v3-trazabilidad-qr-inventario`. La base real predeterminada `C:\Users\herre\AppData\Local\IndustrialApp\data\industrial_app.db` **no existía** al revisar esta implementación y no se creó durante las pruebas. La prueba de navegador usó la base aislada e ignorada `v3_browser_smoke.db` en el proyecto. Pytest empleó `tmp_path` y nunca apuntó a la base real.

| Comprobación | Resultado |
|---|---|
| `python -m pytest -q` | 34 aprobadas: 24 V2/MVP y 10 V3 |
| `ruff check .` | Sin errores |
| `python -m compileall -q sha.py sha_mvp.py pydi scripts tests` | Correcto |
| Altas, migración y unicidad | 500 bolsas y dos códigos de otras categorías únicos; `UNIQUE` SQLite y reintento de colisión verificados; respaldo previo de DB legado conservó su tabla; kardex append-only |
| PDF | `%PDF`, A4, 11 etiquetas en 2 páginas, IDs en texto, QR raster y barras vectoriales, sin nuevas filas al reimprimir |
| Ventas | Precio de línea en centavos, segunda venta rechazada, reintento idempotente, rollback multiartículo y carrera de dos conexiones |
| Materia prima y maquinaria | Conversión kg/g exacta, consumos y agotamiento sin saldo negativo; estado de máquina auditado y fuera de POS |
| Exportación | XLSX con tres hojas actuales, sin artículos vendidos en inventario activo; CSV vacío sin error |

En el navegador local se registró una bolsa física de 250 g del lote `SMOKE-2026`, con QR y Code 128 mostrando el mismo ID. Consulta la encontró; el POS registró folio 1 por **$35 MXN**; el inventario activo pasó de 1 a 0 bolsas. Tras reiniciar Streamlit, el código seguía `VENDIDO`, con folio y reimpresión PDF disponible. La limpieza global V2 vació filtros de consulta sin borrar el registro; recargar el ejemplo V2 tampoco alteró la DB. La prueba usó código y venta de ensayo, no inventario del usuario.

Se renderizó una etiqueta de prueba con Poppler a PNG y se inspeccionó visualmente: QR, barras, lote, producto e ID legibles y dentro del borde, sin recortes. El PDF de validación se conserva en `output/pdf/` y está ignorado por Git. No se ensayó lectura con un escáner USB físico, impresora térmica o integración fiscal: la app solo registra ventas internas.
