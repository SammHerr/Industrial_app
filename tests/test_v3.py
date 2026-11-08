"""Integración V3 con SQLite temporal; nunca usa la base real del usuario."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo

import pandas as pd
import pytest
from PIL import Image
from pypdf import PdfReader

from pydi import code_generator
from pydi.code_generator import code128_png, normalize_code, qr_png
from pydi.inventory_db import backup_database, connect
from pydi.inventory_service import (
    InventoryError,
    add_catalog_item,
    add_presentation,
    catalog,
    consume_raw,
    get_record,
    inventory_xlsx,
    movements,
    presentations,
    records,
    register_machine,
    register_products,
    register_raw,
    set_machine_status,
    set_presentation,
)
from pydi.labels_pdf import labels_pdf
from pydi.sales_service import list_sales, sell
from pydi.v2_model import make_empty_case, make_example_case
from pydi.v3_ui import clear_transient_state


def test_bootstrap_catalog_and_no_physical_stock(tmp_path):
    db = tmp_path / "industrial.db"
    items = catalog(path=db)
    assert len(items) == 11
    assert {row["name"] for row in items if row["category"] == "Materia prima"} == {"Avena", "Soya", "Cacahuate", "Canela"}
    seeded = presentations(db)
    assert [(row["grams"], row["price_cents"]) for row in seeded] == [(250, 3500), (500, None)]
    assert records(active_only=True, path=db) == []
    with connect(db) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert records(path=db) == []


def test_new_presentation_price_and_unique_sku(tmp_path):
    db = tmp_path / "industrial.db"
    with pytest.raises(InventoryError):
        add_presentation("Nueva", None, "NEW", path=db)
    third = add_presentation("Edición café con acentos", 330, "PYDI-330G", path=db)
    assert third["grams"] == 330 and third["price_cents"] is None
    set_presentation(third["id"], label="Edición café", grams_value=335, sku="PYDI-335G", path=db)
    assert next(p for p in presentations(db) if p["id"] == third["id"])["grams"] == 335
    with pytest.raises(InventoryError):
        add_presentation("Duplicada", 335, "OTHER", path=db)
    with pytest.raises(InventoryError):
        add_presentation("Duplicada", 400, "PYDI-335G", path=db)
    code = register_products(third["id"], 1, "LOT-330", "APT", path=db)[0]
    with pytest.raises(InventoryError, match="bloqueada"):
        set_presentation(third["id"], grams_value=340, path=db)
    with pytest.raises(InventoryError, match="precio"):
        sell([code], "op-no-price", path=db)
    set_presentation(third["id"], price_mxn="42.50", path=db)
    assert sell([code], "op-price", path=db)["total_cents"] == 4250
    set_presentation(third["id"], enabled=False, path=db)
    with pytest.raises(InventoryError):
        register_products(third["id"], 1, "L", "APT", path=db)


def test_codes_unique_persistent_and_sql_unique(tmp_path):
    db = tmp_path / "industrial.db"
    codes = register_products("PYDI-250", 500, "LOTE-A", "APT-1", path=db)
    raw = register_raw("MP-AVENA", "R-1", "1.25", "kg", "AMP", "2026-11-06", path=db)
    machine = register_machine("MQ-TOS-01", "Producción", serial="SER-001", path=db)
    assert len({*codes, raw, machine}) == 502
    assert all(len(code) == 23 for code in [*codes, raw, machine])
    assert all(normalize_code(f" {code.lower()}\n") == code for code in (codes[0], raw, machine))
    assert qr_png(codes[0]).startswith(b"\x89PNG")
    assert code128_png(codes[0]).startswith(b"\x89PNG")
    with connect(db) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute("UPDATE traceable_items SET code=? WHERE code=?", (codes[0], codes[1]))
    assert len(records(path=db)) == 502
    assert len(records(path=db)) == 502  # nueva conexión, misma fuente persistente
    with pytest.raises(InventoryError):
        register_products("PYDI-250", 501, "L", "APT", path=db)


def test_pdf_reprint_a4_same_codes_no_db_write(tmp_path):
    db = tmp_path / "industrial.db"
    codes = register_products("PYDI-250", 11, "L-Á", "Área PT", path=db)
    with connect(db) as connection:
        before = tuple(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("traceable_items", "stock_movements", "audit_events"))
    pdf = labels_pdf(codes, path=db)
    assert pdf.startswith(b"%PDF")
    reader = PdfReader(BytesIO(pdf))
    assert len(reader.pages) == 2
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert all(code in text for code in codes)
    assert "Polvo de avena con soya" in text
    assert "L-Á" in text
    assert b"/Image" in pdf or b"/Subtype /Image" in pdf
    assert labels_pdf(codes, path=db) != b""
    with connect(db) as connection:
        after = tuple(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("traceable_items", "stock_movements", "audit_events"))
    assert before == after


def test_sale_idempotent_double_sale_and_active_filter(tmp_path):
    db = tmp_path / "industrial.db"
    first, second = register_products("PYDI-250", 2, "L-1", "APT", path=db)
    sale = sell([first], "op-1", path=db)
    assert sale["total_cents"] == 3500 and len(sale["lines"]) == 1
    assert sell([first], "op-1", path=db)["id"] == sale["id"]
    assert get_record(first, db)["status"] == "VENDIDO"
    assert get_record(first, db)["sale_id"] == sale["id"]
    assert [row["code"] for row in records(active_only=True, path=db)] == [second]
    with pytest.raises(InventoryError, match="no disponible"):
        sell([first], "op-2", path=db)
    with pytest.raises(InventoryError, match="carrito distinto"):
        sell([second], "op-1", path=db)
    assert len(list_sales(db)) == 1
    local_day = datetime.now(ZoneInfo("America/Mexico_City")).date().isoformat()
    assert len(list_sales(db, from_date=local_day, to_date=local_day)) == 1
    assert list_sales(db, from_date="2000-01-01", to_date="2000-01-01") == []
    assert [row["movement_type"] for row in movements(first, db)] == ["VENTA", "ALTA"]


def test_multiline_sale_rollback_and_two_connections(tmp_path):
    db = tmp_path / "industrial.db"
    first, second, third = register_products("PYDI-250", 3, "L", "APT", path=db)
    sell([third], "prior", path=db)
    with pytest.raises(InventoryError):
        sell([first, third], "atomic", path=db)
    assert get_record(first, db)["status"] == "DISPONIBLE"
    assert len(list_sales(db)) == 1
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda op: _try_sale(first, op, db), ("race-1", "race-2")))
    assert sorted(outcomes) == ["error", "ok"]
    assert get_record(first, db)["status"] == "VENDIDO"
    assert len(list_sales(db)) == 2
    assert get_record(second, db)["status"] == "DISPONIBLE"


def _try_sale(code, operation, db):
    try:
        sell([code], operation, path=db)
        return "ok"
    except InventoryError:
        return "error"


def test_raw_kardex_exhaustion_and_machine_audit(tmp_path):
    db = tmp_path / "industrial.db"
    raw = register_raw("MP-SOYA", "LOTE-2", "2.5", "kg", "AMP", "2026-11-06", path=db)
    assert consume_raw(raw, 500, "g", "Producción", path=db) == 2000
    with pytest.raises(InventoryError, match="Saldo insuficiente"):
        consume_raw(raw, 2.001, "kg", "Error", path=db)
    assert consume_raw(raw, 2, "kg", "Producción", path=db) == 0
    assert get_record(raw, db)["status"] == "AGOTADO"
    assert [row["movement_type"] for row in movements(raw, db)] == ["CONSUMO", "CONSUMO", "ALTA"]
    equipment = add_catalog_item("Maquinaria", "Molino de prueba", "MOL-TEST", path=db)
    machine = register_machine(equipment["id"], "Sala A", serial="S-002", path=db)
    set_machine_status(machine, "EN_MANTENIMIENTO", "Revisión", path=db)
    assert get_record(machine, db)["status"] == "EN_MANTENIMIENTO"
    assert machine not in [row["code"] for row in records(active_only=True, path=db)]
    with pytest.raises(InventoryError, match="solo se venden"):
        sell([machine], "not-sellable", path=db)


def test_v2_state_buttons_independent_and_exports(tmp_path):
    db = tmp_path / "industrial.db"
    code = register_products("PYDI-250", 1, "L", "APT", path=db)[0]
    sell([code], "sale", path=db)
    before = (get_record(code, db)["status"], len(list_sales(db)))
    assert make_empty_case().tables["ingredientes"].empty
    assert not make_example_case().tables["ingredientes"].empty
    state = {"case": make_example_case(), "v3_lookup": code, "v3_cart": [code], "v3_revision": 2}
    clear_transient_state(state)
    assert state["v3_revision"] == 3 and "v3_lookup" not in state and "v3_cart" not in state
    assert (get_record(code, db)["status"], len(list_sales(db))) == before
    workbook = pd.ExcelFile(BytesIO(inventory_xlsx(db)))
    assert workbook.sheet_names == ["Producto terminado", "Materia prima", "Maquinaria"]
    assert pd.read_excel(BytesIO(inventory_xlsx(db)), sheet_name="Producto terminado").empty
    assert pd.DataFrame(records(active_only=True, path=db)).to_csv(index=False) == "\r\n" or records(active_only=True, path=db) == []
    with pytest.raises(InventoryError):
        labels_pdf([], path=db)


def test_backup_before_migration_and_manual_backup(tmp_path):
    db = tmp_path / "legacy.db"
    with sqlite3.connect(db) as connection:
        connection.execute("CREATE TABLE old_records (value TEXT)")
        connection.execute("INSERT INTO old_records VALUES ('conservar')")
    with connect(db) as connection:
        assert connection.execute("SELECT value FROM old_records").fetchone()[0] == "conservar"
        backup = connection.execute("SELECT backup_path FROM schema_migrations WHERE version=1").fetchone()[0]
    assert backup and pd.notna(backup)
    with sqlite3.connect(backup) as connection:
        assert connection.execute("SELECT value FROM old_records").fetchone()[0] == "conservar"
    manual = backup_database(db)
    assert manual.exists() and manual != db


def test_collision_retry_and_append_only_movements(tmp_path, monkeypatch):
    db = tmp_path / "industrial.db"
    first = register_products("PYDI-250", 1, "L", "APT", path=db)[0]
    alternate = "PT-" + "A" * 20
    sequence = iter([first, alternate])
    monkeypatch.setattr("pydi.inventory_service.new_code", lambda category: next(sequence))
    assert register_products("PYDI-250", 1, "L", "APT", path=db) == [alternate]
    with connect(db) as connection, pytest.raises(sqlite3.IntegrityError, match="append-only"):
        connection.execute("DELETE FROM stock_movements WHERE id=1")
    with connect(db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM stock_movements").fetchone()[0] == 2


def test_all_v3_code_categories_render_without_inventory_side_effects(tmp_path, monkeypatch):
    db = tmp_path / "labels.db"
    custom = add_presentation("Bolsa 330 g", 330, "PYDI-330G", "40.00", path=db)
    codes = [
        register_products("PYDI-250", 1, "MAC-250", "Almacén", path=db)[0],
        register_products("PYDI-500", 1, "MAC-500", "Almacén", path=db)[0],
        register_products(custom["id"], 1, "MAC-330", "Almacén", path=db)[0],
        register_raw("MP-AVENA", "MAC-MP", 1, "kg", "Almacén", "2026-11-06", path=db),
        register_machine("MQ-TOS-01", "Planta", serial="MAC-MQ-001", path=db),
    ]
    with connect(db) as connection:
        before = tuple(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                       for table in ("traceable_items", "stock_movements", "audit_events", "sales"))

    original_barcode = code_generator.Code128
    original_qr = code_generator.qrcode.make
    barcode_values, qr_values = [], []

    def capture_barcode(value, *, writer):
        barcode_values.append(value)
        return original_barcode(value, writer=writer)

    def capture_qr(value, **kwargs):
        qr_values.append(value)
        return original_qr(value, **kwargs)

    monkeypatch.setattr(code_generator, "Code128", capture_barcode)
    monkeypatch.setattr(code_generator.qrcode, "make", capture_qr)
    for code in codes:
        for data in (code128_png(code), qr_png(code)):
            with Image.open(BytesIO(data)) as image:
                assert image.format == "PNG"
                image.verify()
    assert barcode_values == codes and qr_values == codes

    pdf = labels_pdf(codes, path=db)
    assert pdf.startswith(b"%PDF")
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)
    assert all(code in text for code in codes)
    with connect(db) as connection:
        after = tuple(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                      for table in ("traceable_items", "stock_movements", "audit_events", "sales"))
    assert after == before

    sell([codes[0]], "MAC-REGRESSION", path=db)
    assert get_record(codes[0], db)["status"] == "VENDIDO"
    assert codes[0] not in [row["code"] for row in records(active_only=True, path=db)]
    with pytest.raises(InventoryError, match="no disponible"):
        sell([codes[0]], "MAC-REGRESSION-SECOND", path=db)
