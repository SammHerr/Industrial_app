"""Ventas internas idempotentes y atómicas de bolsas físicas individuales."""

import sqlite3
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from pydi.code_generator import normalize_code
from pydi.inventory_db import connect
from pydi.inventory_service import InventoryError, _audit, _text, now_utc, transaction

LOCAL_ZONE = ZoneInfo("America/Mexico_City")


def _local_day_start(value: str, *, next_day: bool = False) -> str:
    try:
        day = date.fromisoformat(value)
    except ValueError:
        raise InventoryError("Filtro de fecha inválido; use AAAA-MM-DD.") from None
    if next_day:
        day += timedelta(days=1)
    return datetime.combine(day, time.min, LOCAL_ZONE).astimezone(UTC).isoformat()


def get_sale(sale_id: int, path: Path | None = None) -> dict | None:
    with connect(path) as connection:
        sale = connection.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
        if sale is None:
            return None
        lines = connection.execute(
            """SELECT sl.id,t.code,c.name,p.label AS presentation,t.lot_code,sl.unit_price_cents
               FROM sale_lines sl JOIN traceable_items t ON t.id=sl.traceable_item_id
               JOIN catalog_items c ON c.id=t.catalog_item_id
               LEFT JOIN presentations p ON p.id=t.presentation_id
               WHERE sl.sale_id=? ORDER BY sl.id""", (sale_id,),
        ).fetchall()
        return {**dict(sale), "lines": [dict(row) for row in lines]}


def list_sales(path: Path | None = None, *, from_date: str | None = None, to_date: str | None = None,
               code: str | None = None) -> list[dict]:
    sql = "SELECT DISTINCT s.* FROM sales s LEFT JOIN sale_lines sl ON sl.sale_id=s.id LEFT JOIN traceable_items t ON t.id=sl.traceable_item_id WHERE 1=1"
    args = []
    if from_date:
        sql += " AND s.created_at_utc>=?"
        args.append(_local_day_start(from_date))
    if to_date:
        sql += " AND s.created_at_utc<?"
        args.append(_local_day_start(to_date, next_day=True))
    if code:
        sql += " AND t.code=?"
        args.append(normalize_code(code))
    with connect(path) as connection:
        return [dict(row) for row in connection.execute(sql + " ORDER BY s.id DESC LIMIT 2000", args)]


def sell(codes: list[str], operation_id: str, *, notes: str = "", path: Path | None = None) -> dict:
    operation = _text(operation_id, "ID de operación", limit=80)
    if not codes or len(codes) > 500:
        raise InventoryError("Carrito: entre 1 y 500 bolsas.")
    normalized = [normalize_code(code) for code in codes]
    if len(set(normalized)) != len(normalized):
        raise InventoryError("El carrito contiene un código repetido.")
    notes = _text(notes, "Notas", required=False, limit=300)
    try:
        with transaction(path) as connection:
            existing = connection.execute("SELECT id FROM sales WHERE operation_id=?", (operation,)).fetchone()
            if existing:
                prior = [row[0] for row in connection.execute(
                    "SELECT t.code FROM sale_lines sl JOIN traceable_items t ON t.id=sl.traceable_item_id WHERE sl.sale_id=?",
                    (existing["id"],),
                )]
                if set(prior) != set(normalized):
                    raise InventoryError("ID de operación reutilizado para un carrito distinto.")
                sale_id = existing["id"]
            else:
                item_rows = []
                for code in normalized:
                    row = connection.execute(
                        """SELECT t.id,t.status,c.category,p.price_cents FROM traceable_items t
                           JOIN catalog_items c ON c.id=t.catalog_item_id
                           LEFT JOIN presentations p ON p.id=t.presentation_id WHERE t.code=?""", (code,),
                    ).fetchone()
                    if row is None:
                        raise InventoryError(f"Código inexistente: {code}.")
                    if row["category"] != "Producto terminado":
                        raise InventoryError(f"{code}: solo se venden bolsas de producto terminado.")
                    if row["status"] != "DISPONIBLE":
                        raise InventoryError(f"{code}: no disponible ({row['status']}).")
                    if row["price_cents"] is None:
                        raise InventoryError(f"{code}: precio no definido para esta presentación.")
                    item_rows.append((code, row))
                total = sum(row["price_cents"] for _, row in item_rows)
                cursor = connection.execute(
                    "INSERT INTO sales(operation_id,created_at_utc,total_cents,notes) VALUES(?,?,?,?)",
                    (operation, now_utc(), total, notes),
                )
                sale_id = cursor.lastrowid
                for code, row in item_rows:
                    updated = connection.execute(
                        "UPDATE traceable_items SET status='VENDIDO',quantity_available='0',version=version+1 WHERE id=? AND status='DISPONIBLE'",
                        (row["id"],),
                    )
                    if updated.rowcount != 1:
                        raise InventoryError(f"{code}: vendido por otra sesión; venta cancelada íntegramente.")
                    connection.execute("INSERT INTO sale_lines(sale_id,traceable_item_id,unit_price_cents) VALUES(?,?,?)",
                                       (sale_id, row["id"], row["price_cents"]))
                    connection.execute(
                        "INSERT INTO stock_movements(traceable_item_id,movement_type,quantity,unit,reason,created_at_utc,reference) VALUES(?,?,?,?,?,?,?)",
                        (row["id"], "VENTA", "1", "unidad", "Venta confirmada", now_utc(), str(sale_id)),
                    )
                    _audit(connection, "traceable_item", code, "VENDIDO", {"status": "DISPONIBLE"}, {"status": "VENDIDO", "sale_id": sale_id})
                _audit(connection, "sale", str(sale_id), "CONFIRMAR", after={"operation_id": operation, "total_cents": total, "codes": normalized})
    except sqlite3.OperationalError as exc:
        raise InventoryError(f"Base ocupada por otra sesión; intente de nuevo. {exc}") from None
    result = get_sale(sale_id, path)
    if result is None:
        raise RuntimeError("La venta confirmada no pudo recuperarse.")
    return result
