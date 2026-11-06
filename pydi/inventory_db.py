"""SQLite local, migraciones aditivas y catálogo PYDI sin existencias ficticias."""

import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

SCHEMA_VERSION = 1
CATEGORIES = ("Producto terminado", "Materia prima", "Maquinaria")


def database_path() -> Path:
    override = os.environ.get("INDUSTRIAL_APP_DB_PATH")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        local = os.environ.get("LOCALAPPDATA")
        root = Path(local) if local else Path.home() / "AppData" / "Local"
    return root / "IndustrialApp" / "data" / "industrial_app.db"


def _backup(connection: sqlite3.Connection, path: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    target = path.with_name(f"{path.stem}.{stamp}.bak.db")
    with sqlite3.connect(target) as destination:
        connection.backup(destination)
    return target


def backup_database(path: Path | None = None) -> Path:
    resolved = Path(path or database_path())
    with connect(resolved) as connection:
        return _backup(connection, resolved)


def _seed_catalog(connection: sqlite3.Connection) -> None:
    now = datetime.now(UTC).isoformat()
    rows = [("PT-PYDI", CATEGORIES[0], "Polvo de avena con soya", "PT-PYDI", "unidad", "Word PYDI")]
    rows += [(f"MP-{sku}", CATEGORIES[1], name, f"MP-{sku}", "g", "Word PYDI") for sku, name in (
        ("AVENA", "Avena"), ("SOYA", "Soya"), ("CACAHUATE", "Cacahuate"), ("CANELA", "Canela"),
    )]
    rows += [(f"MQ-{sku}", CATEGORIES[2], name, sku, "unidad", "Word PYDI; propuesta sin adquirir") for sku, name in (
        ("TOS-01", "Tostador 01"), ("TOS-02", "Tostador 02"), ("MOL-01", "Molino"),
        ("BAS-01", "Báscula 01"), ("BAS-02", "Báscula 02"), ("SEL-01", "Selladora"),
    )]
    connection.executemany(
        "INSERT OR IGNORE INTO catalog_items(id,category,name,sku,unit,source,created_at) VALUES(?,?,?,?,?,?,?)",
        [(item_id, category, name, sku, unit, source, now) for item_id, category, name, sku, unit, source in rows],
    )
    connection.executemany(
        "INSERT OR IGNORE INTO presentations(id,product_catalog_id,label,grams,sku,price_cents,source) VALUES(?,?,?,?,?,?,?)",
        [("PYDI-250", "PT-PYDI", "Bolsa 250 g", 250, "PYDI-250G", 3500, "Word PYDI §4"),
         ("PYDI-500", "PT-PYDI", "Bolsa 500 g", 500, "PYDI-500G", None, "Word PYDI §2; precio pendiente")],
    )


def initialize(connection: sqlite3.Connection, path: Path) -> Path | None:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA_VERSION:
        raise RuntimeError(f"La base usa versión {version}, superior a la app {SCHEMA_VERSION}.")
    if version == SCHEMA_VERSION:
        return None
    existing = path.exists() and path.stat().st_size > 0
    backup = _backup(connection, path) if existing else None
    try:
        connection.executescript("""
        BEGIN IMMEDIATE;
        CREATE TABLE IF NOT EXISTS catalog_items (
          id TEXT PRIMARY KEY, category TEXT NOT NULL CHECK(category IN ('Producto terminado','Materia prima','Maquinaria')),
          name TEXT NOT NULL, sku TEXT NOT NULL UNIQUE, unit TEXT NOT NULL,
          default_price_cents INTEGER CHECK(default_price_cents >= 0), enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
          source TEXT NOT NULL, metadata_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS presentations (
          id TEXT PRIMARY KEY, product_catalog_id TEXT NOT NULL REFERENCES catalog_items(id),
          label TEXT NOT NULL, grams INTEGER NOT NULL CHECK(grams > 0), sku TEXT NOT NULL UNIQUE,
          price_cents INTEGER CHECK(price_cents >= 0), source TEXT NOT NULL,
          enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
          UNIQUE(product_catalog_id,grams)
        );
        CREATE TABLE IF NOT EXISTS traceable_items (
          id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, catalog_item_id TEXT NOT NULL REFERENCES catalog_items(id),
          presentation_id TEXT REFERENCES presentations(id), lot_code TEXT, quantity_initial TEXT NOT NULL,
          quantity_available TEXT NOT NULL, measure_unit TEXT NOT NULL, status TEXT NOT NULL,
          location TEXT NOT NULL, supplier TEXT, acquired_at TEXT, expiry_at TEXT,
          model TEXT, serial TEXT, maintenance TEXT, acquisition_status TEXT NOT NULL DEFAULT 'REAL',
          version INTEGER NOT NULL DEFAULT 1, created_at_utc TEXT NOT NULL,
          CHECK(length(code) = 23)
        );
        CREATE INDEX IF NOT EXISTS idx_trace_status ON traceable_items(status,presentation_id);
        CREATE INDEX IF NOT EXISTS idx_trace_lot ON traceable_items(lot_code);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_machine_serial ON traceable_items(serial) WHERE serial IS NOT NULL AND serial <> '';
        CREATE TABLE IF NOT EXISTS stock_movements (
          id INTEGER PRIMARY KEY, traceable_item_id INTEGER NOT NULL REFERENCES traceable_items(id),
          movement_type TEXT NOT NULL, quantity TEXT NOT NULL, unit TEXT NOT NULL,
          reason TEXT NOT NULL, created_at_utc TEXT NOT NULL, reference TEXT,
          correlation_id TEXT UNIQUE
        );
        CREATE INDEX IF NOT EXISTS idx_movement_item ON stock_movements(traceable_item_id,id);
        CREATE TABLE IF NOT EXISTS sales (
          id INTEGER PRIMARY KEY, operation_id TEXT NOT NULL UNIQUE, created_at_utc TEXT NOT NULL,
          total_cents INTEGER NOT NULL CHECK(total_cents >= 0), notes TEXT, status TEXT NOT NULL DEFAULT 'CONFIRMADA'
        );
        CREATE TABLE IF NOT EXISTS sale_lines (
          id INTEGER PRIMARY KEY, sale_id INTEGER NOT NULL REFERENCES sales(id),
          traceable_item_id INTEGER NOT NULL UNIQUE REFERENCES traceable_items(id),
          unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents >= 0)
        );
        CREATE TABLE IF NOT EXISTS audit_events (
          id INTEGER PRIMARY KEY, entity TEXT NOT NULL, entity_id TEXT NOT NULL,
          action TEXT NOT NULL, before_json TEXT, after_json TEXT, created_at_utc TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS schema_migrations (
          version INTEGER PRIMARY KEY, applied_at_utc TEXT NOT NULL, backup_path TEXT
        );
        CREATE TRIGGER IF NOT EXISTS stock_movements_no_update BEFORE UPDATE ON stock_movements
          BEGIN SELECT RAISE(ABORT, 'stock_movements is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS stock_movements_no_delete BEFORE DELETE ON stock_movements
          BEGIN SELECT RAISE(ABORT, 'stock_movements is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS audit_events_no_update BEFORE UPDATE ON audit_events
          BEGIN SELECT RAISE(ABORT, 'audit_events is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS audit_events_no_delete BEFORE DELETE ON audit_events
          BEGIN SELECT RAISE(ABORT, 'audit_events is append-only'); END;
        """)
        _seed_catalog(connection)
        connection.execute("INSERT INTO schema_migrations VALUES(?,?,?)", (1, datetime.now(UTC).isoformat(), str(backup) if backup else None))
        connection.execute("PRAGMA user_version=1")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return backup


@contextmanager
def connect(path: Path | None = None):
    resolved = Path(path or database_path()).expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(resolved, timeout=10, isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA journal_mode=WAL")
        initialize(connection, resolved)
        yield connection
    finally:
        connection.close()
