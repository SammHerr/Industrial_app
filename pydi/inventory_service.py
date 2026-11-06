"""Operaciones transaccionales de catálogo, altas, consulta e inventario."""

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pandas as pd

from pydi.code_generator import new_code, normalize_code
from pydi.inventory_db import CATEGORIES, connect


class InventoryError(ValueError):
    pass


def now_utc() -> str:
    return datetime.now(UTC).isoformat()


def amount(value, name: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise InventoryError(f"{name}: cantidad inválida.") from None
    if not number.is_finite() or number <= 0:
        raise InventoryError(f"{name}: debe ser mayor que cero.")
    if number.as_tuple().exponent < -3:
        raise InventoryError(f"{name}: máximo tres decimales en gramos.")
    return number


def grams(value, unit: str) -> Decimal:
    quantity = amount(value, "Cantidad")
    if unit not in ("kg", "g"):
        raise InventoryError("Materia prima: unidad kg o g requerida.")
    return quantity * (1000 if unit == "kg" else 1)


def money_cents(value, *, required: bool = False) -> int | None:
    if value is None or str(value).strip() == "":
        if required:
            raise InventoryError("Precio en MXN requerido.")
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise InventoryError("Precio inválido.") from None
    if not number.is_finite() or number < 0 or number.as_tuple().exponent < -2:
        raise InventoryError("Precio: MXN no negativo con máximo dos decimales.")
    return int(number * 100)


def _text(value, name: str, *, required: bool = True, limit: int = 120) -> str:
    result = str(value or "").strip()
    if (required and not result) or len(result) > limit:
        raise InventoryError(f"{name}: longitud inválida (máximo {limit}).")
    return result


def _date(value, name: str) -> str | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise InventoryError(f"{name}: fecha ISO AAAA-MM-DD requerida.") from None


@contextmanager
def transaction(path: Path | None = None):
    with connect(path) as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def catalog(category: str | None = None, path: Path | None = None) -> list[dict]:
    with connect(path) as connection:
        sql = "SELECT * FROM catalog_items WHERE enabled=1"
        args = []
        if category:
            if category not in CATEGORIES:
                raise InventoryError("Categoría inválida.")
            sql += " AND category=?"
            args.append(category)
        return [dict(row) for row in connection.execute(sql + " ORDER BY category,name", args)]


def presentations(path: Path | None = None, *, enabled_only: bool = True) -> list[dict]:
    with connect(path) as connection:
        sql = "SELECT * FROM presentations"
        if enabled_only:
            sql += " WHERE enabled=1"
        return [dict(row) for row in connection.execute(sql + " ORDER BY grams,sku")]


def add_catalog_item(category: str, name: str, sku: str, *, path: Path | None = None) -> dict:
    if category not in CATEGORIES:
        raise InventoryError("Categoría inválida.")
    name, sku = _text(name, "Nombre"), _text(sku, "SKU/modelo", limit=40).upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]*", sku):
        raise InventoryError("SKU/modelo: use letras, dígitos, punto, guion o guion bajo.")
    item_id = "CAT-" + uuid4().hex.upper()
    with transaction(path) as connection:
        try:
            connection.execute(
                "INSERT INTO catalog_items(id,category,name,sku,unit,source,created_at) VALUES(?,?,?,?,?,?,?)",
                (item_id, category, name, sku, "g" if category == "Materia prima" else "unidad", "Alta usuario", now_utc()),
            )
        except sqlite3.IntegrityError:
            raise InventoryError("SKU/modelo ya registrado.") from None
    return next(item for item in catalog(category, path) if item["id"] == item_id)


def add_presentation(label: str, grams_value, sku: str, price_mxn=None, *, path: Path | None = None) -> dict:
    label, sku = _text(label, "Presentación"), _text(sku, "SKU", limit=40).upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]*", sku):
        raise InventoryError("SKU inválido.")
    try:
        weight = int(grams_value)
        if Decimal(str(grams_value)) != weight or weight <= 0 or weight > 100000:
            raise ValueError
    except (ValueError, TypeError, InvalidOperation):
        raise InventoryError("Gramos: entero positivo hasta 100,000.") from None
    price = money_cents(price_mxn)
    item_id = "PRES-" + uuid4().hex.upper()
    with transaction(path) as connection:
        try:
            connection.execute(
                "INSERT INTO presentations(id,product_catalog_id,label,grams,sku,price_cents,source) VALUES(?,?,?,?,?,?,?)",
                (item_id, "PT-PYDI", label, weight, sku, price, "Alta usuario"),
            )
        except sqlite3.IntegrityError:
            raise InventoryError("SKU o gramaje de presentación ya registrado.") from None
    return next(item for item in presentations(path) if item["id"] == item_id)


def set_presentation(presentation_id: str, *, label: str | None = None, grams_value=None,
                     sku: str | None = None, price_mxn=None, enabled: bool | None = None,
                     path: Path | None = None) -> None:
    with transaction(path) as connection:
        old = connection.execute("SELECT * FROM presentations WHERE id=?", (presentation_id,)).fetchone()
        if old is None:
            raise InventoryError("Presentación inexistente.")
        new_label = old["label"] if label is None else _text(label, "Presentación")
        new_sku = old["sku"] if sku is None else _text(sku, "SKU", limit=40).upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]*", new_sku):
            raise InventoryError("SKU inválido.")
        if grams_value is None:
            new_weight = old["grams"]
        else:
            try:
                new_weight = int(grams_value)
                if Decimal(str(grams_value)) != new_weight or not 1 <= new_weight <= 100000:
                    raise ValueError
            except (ValueError, TypeError, InvalidOperation):
                raise InventoryError("Gramos: entero positivo hasta 100,000.") from None
        if (new_label, new_sku, new_weight) != (old["label"], old["sku"], old["grams"]):
            count = connection.execute("SELECT COUNT(*) FROM traceable_items WHERE presentation_id=?", (presentation_id,)).fetchone()[0]
            if count:
                raise InventoryError("Identidad de presentación bloqueada: ya existen bolsas físicas; precio y estado sí se pueden cambiar.")
        price = old["price_cents"] if price_mxn is None else money_cents(price_mxn)
        active = old["enabled"] if enabled is None else int(enabled)
        try:
            connection.execute("UPDATE presentations SET label=?,grams=?,sku=?,price_cents=?,enabled=? WHERE id=?",
                               (new_label, new_weight, new_sku, price, active, presentation_id))
        except sqlite3.IntegrityError:
            raise InventoryError("SKU o gramaje de presentación ya registrado.") from None
        _audit(connection, "presentation", presentation_id, "ACTUALIZAR", dict(old),
               {"label": new_label, "grams": new_weight, "sku": new_sku, "price_cents": price, "enabled": active})


def _audit(connection, entity: str, entity_id: str, action: str, before=None, after=None) -> None:
    connection.execute(
        "INSERT INTO audit_events(entity,entity_id,action,before_json,after_json,created_at_utc) VALUES(?,?,?,?,?,?)",
        (entity, str(entity_id), action, json.dumps(before, ensure_ascii=False, default=str) if before is not None else None,
         json.dumps(after, ensure_ascii=False, default=str) if after is not None else None, now_utc()),
    )


def _insert_traceable(connection, *, category: str, catalog_item_id: str, presentation_id=None,
                      lot_code=None, quantity="1", unit="unidad", location="", supplier=None,
                      acquired_at=None, expiry_at=None, model=None, serial=None, maintenance=None,
                      status="DISPONIBLE") -> str:
    for _ in range(12):
        code = new_code(category)
        try:
            cursor = connection.execute(
                """INSERT INTO traceable_items
                (code,catalog_item_id,presentation_id,lot_code,quantity_initial,quantity_available,measure_unit,status,
                 location,supplier,acquired_at,expiry_at,model,serial,maintenance,created_at_utc)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (code, catalog_item_id, presentation_id, lot_code, str(quantity), str(quantity), unit, status,
                 location, supplier, acquired_at, expiry_at, model, serial, maintenance, now_utc()),
            )
        except sqlite3.IntegrityError as exc:
            if "traceable_items.code" in str(exc):
                continue
            raise InventoryError(f"Alta rechazada: {exc}") from None
        connection.execute(
            "INSERT INTO stock_movements(traceable_item_id,movement_type,quantity,unit,reason,created_at_utc) VALUES(?,?,?,?,?,?)",
            (cursor.lastrowid, "ALTA", str(quantity), unit, "Alta confirmada", now_utc()),
        )
        _audit(connection, "traceable_item", code, "ALTA", after={"category": category, "status": status, "quantity": str(quantity)})
        return code
    raise InventoryError("Colisiones repetidas de código; intente nuevamente.")


def register_products(presentation_id: str, count: int, lot_code: str, location: str,
                      *, path: Path | None = None) -> list[str]:
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 500:
        raise InventoryError("Número de bolsas: entero entre 1 y 500 por operación.")
    lot, location = _text(lot_code, "Lote", limit=64), _text(location, "Ubicación", limit=100)
    with transaction(path) as connection:
        presentation = connection.execute("SELECT * FROM presentations WHERE id=? AND enabled=1", (presentation_id,)).fetchone()
        if presentation is None:
            raise InventoryError("Presentación inexistente o desactivada.")
        return [_insert_traceable(connection, category=CATEGORIES[0], catalog_item_id=presentation["product_catalog_id"],
                                  presentation_id=presentation_id, lot_code=lot, location=location) for _ in range(count)]


def register_raw(catalog_item_id: str, lot_code: str, quantity, unit: str, location: str,
                 received_at: str, *, expiry_at: str | None = None, supplier: str | None = None,
                 path: Path | None = None) -> str:
    lot, location = _text(lot_code, "Lote", limit=64), _text(location, "Ubicación", limit=100)
    received, expiry = _date(received_at, "Recepción"), _date(expiry_at, "Caducidad")
    if not received:
        raise InventoryError("Fecha de recepción requerida.")
    if expiry and expiry < received:
        raise InventoryError("La caducidad precede a la recepción.")
    qty = grams(quantity, unit)
    with transaction(path) as connection:
        item = connection.execute("SELECT category FROM catalog_items WHERE id=? AND enabled=1", (catalog_item_id,)).fetchone()
        if item is None or item["category"] != CATEGORIES[1]:
            raise InventoryError("Materia prima no registrada o desactivada.")
        return _insert_traceable(connection, category=CATEGORIES[1], catalog_item_id=catalog_item_id,
                                 lot_code=lot, quantity=qty, unit="g", location=location,
                                 supplier=_text(supplier, "Proveedor", required=False), acquired_at=received, expiry_at=expiry)


def register_machine(catalog_item_id: str, location: str, *, model: str = "", serial: str = "",
                     maintenance: str = "", acquired_at: str | None = None,
                     path: Path | None = None) -> str:
    location = _text(location, "Ubicación", limit=100)
    acquired = _date(acquired_at, "Adquisición")
    with transaction(path) as connection:
        item = connection.execute("SELECT category FROM catalog_items WHERE id=? AND enabled=1", (catalog_item_id,)).fetchone()
        if item is None or item["category"] != CATEGORIES[2]:
            raise InventoryError("Equipo no registrado o desactivado.")
        return _insert_traceable(connection, category=CATEGORIES[2], catalog_item_id=catalog_item_id,
                                 location=location, model=_text(model, "Modelo", required=False),
                                 serial=_text(serial, "Serie", required=False, limit=80) or None,
                                 maintenance=_text(maintenance, "Mantenimiento", required=False),
                                 acquired_at=acquired, status="ACTIVO")


def consume_raw(code: str, quantity, unit: str, reason: str, *, path: Path | None = None) -> Decimal:
    normalized = normalize_code(code)
    qty = grams(quantity, unit)
    reason = _text(reason, "Motivo", limit=200)
    with transaction(path) as connection:
        row = connection.execute("SELECT t.*,c.category FROM traceable_items t JOIN catalog_items c ON c.id=t.catalog_item_id WHERE t.code=?", (normalized,)).fetchone()
        if row is None or row["category"] != CATEGORIES[1]:
            raise InventoryError("Lote de materia prima inexistente.")
        available = Decimal(row["quantity_available"])
        if qty > available or available <= 0:
            raise InventoryError("Saldo insuficiente; no se permite inventario negativo.")
        remainder = available - qty
        status = "AGOTADO" if remainder == 0 else "DISPONIBLE"
        connection.execute("UPDATE traceable_items SET quantity_available=?, status=?, version=version+1 WHERE id=?",
                           (str(remainder), status, row["id"]))
        connection.execute("INSERT INTO stock_movements(traceable_item_id,movement_type,quantity,unit,reason,created_at_utc) VALUES(?,?,?,?,?,?)",
                           (row["id"], "CONSUMO", str(qty), "g", reason, now_utc()))
        _audit(connection, "traceable_item", normalized, "CONSUMO", {"quantity": str(available)}, {"quantity": str(remainder)})
    return remainder


def set_machine_status(code: str, status: str, reason: str, *, path: Path | None = None) -> None:
    normalized = normalize_code(code)
    if status not in ("ACTIVO", "EN_MANTENIMIENTO", "FUERA_DE_SERVICIO"):
        raise InventoryError("Estado de maquinaria inválido.")
    reason = _text(reason, "Motivo", limit=200)
    with transaction(path) as connection:
        row = connection.execute("SELECT t.*,c.category FROM traceable_items t JOIN catalog_items c ON c.id=t.catalog_item_id WHERE t.code=?", (normalized,)).fetchone()
        if row is None or row["category"] != CATEGORIES[2]:
            raise InventoryError("Activo físico de maquinaria inexistente.")
        if row["status"] == status:
            raise InventoryError("El activo ya tiene ese estado.")
        connection.execute("UPDATE traceable_items SET status=?, maintenance=?, version=version+1 WHERE id=?", (status, reason, row["id"]))
        _audit(connection, "traceable_item", normalized, "ESTADO_MAQUINARIA", {"status": row["status"]}, {"status": status, "reason": reason})


RECORD_SELECT = """SELECT t.*,c.category,c.name,c.sku,p.label AS presentation,p.grams,p.price_cents,
  s.id AS sale_id,s.created_at_utc AS sold_at_utc
  FROM traceable_items t JOIN catalog_items c ON c.id=t.catalog_item_id
  LEFT JOIN presentations p ON p.id=t.presentation_id
  LEFT JOIN sale_lines sl ON sl.traceable_item_id=t.id LEFT JOIN sales s ON s.id=sl.sale_id"""


def get_record(code: str, path: Path | None = None) -> dict | None:
    normalized = normalize_code(code)
    with connect(path) as connection:
        row = connection.execute(RECORD_SELECT + " WHERE t.code=?", (normalized,)).fetchone()
        return dict(row) if row else None


def records(*, category: str | None = None, status: str | None = None, lot: str | None = None,
            presentation_id: str | None = None, text: str | None = None, active_only: bool = False,
            limit: int = 1000, path: Path | None = None) -> list[dict]:
    clauses, args = [], []
    if category:
        if category not in CATEGORIES:
            raise InventoryError("Categoría inválida.")
        clauses.append("c.category=?")
        args.append(category)
    if status:
        clauses.append("t.status=?")
        args.append(status)
    if lot:
        clauses.append("t.lot_code LIKE ?")
        args.append(f"%{lot}%")
    if presentation_id:
        clauses.append("t.presentation_id=?")
        args.append(presentation_id)
    if text:
        clauses.append("(t.code LIKE ? OR c.name LIKE ? OR t.lot_code LIKE ?)")
        args += [f"%{text}%"] * 3
    if active_only:
        clauses.append("((c.category='Producto terminado' AND t.status='DISPONIBLE') OR (c.category='Materia prima' AND t.status='DISPONIBLE') OR (c.category='Maquinaria' AND t.status='ACTIVO'))")
    sql = RECORD_SELECT + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY c.category,c.name,p.grams,t.lot_code,t.code LIMIT ?"
    args.append(min(max(int(limit), 1), 10000))
    with connect(path) as connection:
        return [dict(row) for row in connection.execute(sql, args)]


def movements(code: str | None = None, path: Path | None = None) -> list[dict]:
    sql = "SELECT m.*,t.code FROM stock_movements m JOIN traceable_items t ON t.id=m.traceable_item_id"
    args = []
    if code:
        sql += " WHERE t.code=?"
        args.append(normalize_code(code))
    with connect(path) as connection:
        return [dict(row) for row in connection.execute(sql + " ORDER BY m.id DESC LIMIT 2000", args)]


def audit_events(path: Path | None = None) -> list[dict]:
    with connect(path) as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT 2000")]


def inventory_xlsx(path: Path | None = None) -> bytes:
    output = BytesIO()
    active = records(active_only=True, path=path, limit=10000)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for category, sheet in ((CATEGORIES[0], "Producto terminado"), (CATEGORIES[1], "Materia prima"), (CATEGORIES[2], "Maquinaria")):
            pd.DataFrame([row for row in active if row["category"] == category]).to_excel(writer, sheet_name=sheet, index=False)
    return output.getvalue()
