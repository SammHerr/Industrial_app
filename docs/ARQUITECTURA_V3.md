# Industrial App V3: persistencia y reglas

## Esquema SQLite

La versión de esquema es `PRAGMA user_version=1` y queda anotada en `schema_migrations`. La inicialización es idempotente. Si un archivo de base ya existe con una versión anterior, `sqlite3.Connection.backup()` crea una copia con marca UTC `.bak.db` **antes** de aplicar la migración. No hay borrados de tablas ni registros. Una versión futura desconocida detiene la app. Se activan claves foráneas y WAL en cada conexión.

| Tabla | Propósito y restricciones principales |
|---|---|
| `catalog_items` | Tres categorías principales, SKU único, origen PYDI o alta de usuario. Incluye equipos propuestos, sin declarar activos físicos. |
| `presentations` | 250 g y 500 g del Word; `UNIQUE(sku)` y `UNIQUE(product_catalog_id, grams)`. Precio en centavos, nullable. |
| `traceable_items` | Unidad física PT/MQ o lote/contenedor MP. ID interno `code UNIQUE`, 80 bits aleatorios efectivos y prefijo; estado, ubicación, lote, cantidad, versión. Serie de maquinaria única si se informa. |
| `stock_movements` | Kardex de alta, consumo y venta. Triggers impiden `UPDATE` y `DELETE`; siempre se agrega un movimiento. |
| `sales` | `operation_id UNIQUE`, folio, fecha UTC y total entero en centavos. |
| `sale_lines` | Precio histórico de cada bolsa; `traceable_item_id UNIQUE` impide doble venta física. |
| `audit_events` | Cambios de estado/alta/venta; triggers de solo inserción. |
| `schema_migrations` | Versión aplicada y ruta de respaldo previo. |

El producto terminado usa cantidad `1 unidad` por código. La materia prima se convierte explícitamente de `kg` o `g` a gramos y se guarda como cadena decimal exacta para evitar redondeos binarios. El precio se valida con `Decimal` y se almacena en centavos enteros. Los timestamps se guardan en UTC y la UI los presenta en `America/Mexico_City`. No se registra información personal del cliente.

## Transacciones y estados

Las altas y consumos usan `BEGIN IMMEDIATE`. El alta masiva está limitada a 500 bolsas por operación y genera un ID aleatorio individual por bolsa; un índice `UNIQUE` rechaza colisiones y el servicio reintenta hasta 12 veces. El PDF solo lee registros existentes y acepta 1–200 códigos por descarga. QR y Code 128 codifican literalmente el mismo ID normalizado; no dependen de localhost ni pretenden ser GS1.

La venta acepta solo producto terminado `DISPONIBLE` con precio. Valida carrito y precios, crea venta y líneas, actualiza cada bolsa con `UPDATE ... WHERE status='DISPONIBLE'`, exige `rowcount=1`, agrega kardex y auditoría y confirma una sola transacción. Cualquier error revierte el conjunto. Repetir `operation_id` con el mismo carrito devuelve la venta original; reutilizarlo para otro carrito falla. La restricción única de `sale_lines.traceable_item_id` ofrece una segunda defensa. El producto pasa a `VENDIDO` y saldo cero; conserva su folio y fecha en Consulta/Historial. La interfaz no anula ventas automáticamente: una corrección requiere procedimiento administrativo que mantenga evidencia.

La materia prima pasa de `DISPONIBLE` a `AGOTADO` al consumir el saldo exacto; se rechaza cualquier consumo superior. La maquinaria dada de alta pasa por `ACTIVO`, `EN_MANTENIMIENTO` o `FUERA_DE_SERVICIO`, con cambio auditado. Ninguna máquina se ofrece al punto de venta. El inventario activo filtra solo bolsas disponibles, MP con saldo y máquinas activas.

## Separación V2/V3

`pydi.v2_model.Case` permanece como estado de simulación SHA. Los controles globales de ejemplo/limpieza reconstruyen ese estado y, al limpiar, reinician widgets V3 transitorios con una revisión de clave. No acceden a SQLite. La fuente de verdad de existencias, ventas y códigos es la DB. El arranque solo precarga catálogos documentales; no convierte las 6,448/806 bolsas teóricas de V2 en stock real.

## Operación y límites

Ruta predeterminada: `%LOCALAPPDATA%\IndustrialApp\data\industrial_app.db`; variable `INDUSTRIAL_APP_DB_PATH` para pruebas o ubicación personalizada. Mantenga el archivo fuera de OneDrive. La pestaña Configuración muestra la ruta y crea un respaldo no destructivo. Los archivos de DB, WAL/SHM, respaldos, PDF y exportaciones se excluyen de Git. SQLite con WAL tolera varias lecturas y escritores breves, pero no sustituye un servidor multiusuario con autenticación, roles, respaldo centralizado y observabilidad. Si esa necesidad aparece, PostgreSQL es la siguiente arquitectura, con migración controlada de IDs y movimientos.
