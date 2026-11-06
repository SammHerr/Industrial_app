"""Sección persistente de códigos, inventario y venta interna para Streamlit."""

from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from pydi.code_generator import code128_png, normalize_code, qr_png
from pydi.inventory_db import CATEGORIES, backup_database, database_path
from pydi.inventory_service import (
    InventoryError,
    add_catalog_item,
    add_presentation,
    audit_events,
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
from pydi.sales_service import get_sale, list_sales, sell

LOCAL_ZONE = ZoneInfo("America/Mexico_City")


def _key(name: str) -> str:
    return f"v3_{st.session_state.get('v3_revision', 0)}_{name}"


def _local(utc_value: str | None) -> str:
    if not utc_value:
        return ""
    return datetime.fromisoformat(utc_value).astimezone(LOCAL_ZONE).strftime("%Y-%m-%d %H:%M:%S")


def _table(rows: list[dict], *, label: str | None = None) -> None:
    if label:
        st.markdown(f"**{label}**")
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.info("Sin registros para este filtro.")


def _label_preview(code: str) -> None:
    st.code(code, language="text")
    left, right = st.columns(2)
    left.image(qr_png(code), caption=f"QR: {code}", width=175)
    right.image(code128_png(code), caption=f"Code 128: {code}", width=340)


def _created_pdf() -> None:
    codes = st.session_state.get("v3_created_codes", [])
    if codes:
        st.success(f"{len(codes)} identificadores físicos registrados. Descargar o reimprimir no crea otros.")
        st.dataframe(pd.DataFrame({"código": codes}), width="stretch", hide_index=True)
        _label_preview(codes[0])
        if len(codes) <= 200:
            st.download_button("Descargar PDF de etiquetas recién creadas", labels_pdf(codes), "etiquetas_recientes.pdf", "application/pdf")
        else:
            st.info("Más de 200 etiquetas: descargue por partes desde la pestaña PDF.")


def _generate() -> None:
    st.subheader("Alta de unidades físicas y códigos")
    st.caption("Tres categorías. El QR y Code 128 codifican exactamente el mismo ID interno; no son GTIN/GS1.")
    category = st.selectbox("Categoría principal", CATEGORIES, key=_key("category"))
    if category == CATEGORIES[0]:
        options = presentations()
        mapping = {f"{row['label']} · {row['sku']} · precio: {row['price_cents']/100:.2f} MXN" if row["price_cents"] is not None else f"{row['label']} · {row['sku']} · precio pendiente": row["id"] for row in options}
        with st.form(_key("product_form")):
            selected = st.selectbox("Presentación", list(mapping))
            lot = st.text_input("Lote de producción", max_chars=64)
            count = st.number_input("Bolsas físicas / etiquetas", min_value=1, max_value=500, value=1, step=1)
            location = st.text_input("Ubicación física", max_chars=100)
            confirm = st.checkbox("Confirmo el alta física; no es la producción teórica del Word")
            large = st.checkbox("Confirmo lote grande (>50 bolsas)") if count > 50 else True
            submitted = st.form_submit_button("Registrar bolsas e IDs")
        if submitted:
            if not confirm or not large:
                st.error("Confirme el alta física y, si aplica, el lote grande.")
            else:
                try:
                    st.session_state.v3_created_codes = register_products(mapping[selected], int(count), lot, location)
                    st.success("Alta confirmada en SQLite.")
                except InventoryError as exc:
                    st.error(str(exc))
    elif category == CATEGORIES[1]:
        options = {f"{row['name']} · {row['sku']}": row["id"] for row in catalog(category)}
        with st.form(_key("raw_form")):
            selected = st.selectbox("Materia prima", list(options))
            lot = st.text_input("Lote / contenedor", max_chars=64)
            amount = st.text_input("Cantidad positiva", value="1")
            unit = st.selectbox("Unidad de captura", ["kg", "g"])
            received = st.date_input("Fecha de recepción", value=datetime.now(LOCAL_ZONE).date())
            expiry = st.date_input("Caducidad opcional", value=None)
            location = st.text_input("Ubicación", max_chars=100)
            supplier = st.text_input("Proveedor opcional", max_chars=120)
            confirm = st.checkbox("Confirmo recepción física del lote/contenedor")
            submitted = st.form_submit_button("Registrar lote de materia prima")
        if submitted:
            if not confirm:
                st.error("Confirme la recepción física.")
            else:
                try:
                    code = register_raw(options[selected], lot, amount, unit, location, str(received),
                                        expiry_at=str(expiry) if expiry else None, supplier=supplier)
                    st.session_state.v3_created_codes = [code]
                except InventoryError as exc:
                    st.error(str(exc))
    else:
        options = {f"{row['name']} · {row['sku']}": row["id"] for row in catalog(category)}
        with st.form(_key("machine_form")):
            selected = st.selectbox("Equipo del catálogo", list(options))
            location = st.text_input("Ubicación del activo", max_chars=100)
            model = st.text_input("Modelo opcional", max_chars=120)
            serial = st.text_input("Serie opcional única", max_chars=80)
            maintenance = st.text_input("Plan/estado de mantenimiento", max_chars=120)
            acquired = st.date_input("Fecha de adquisición opcional", value=None)
            confirm = st.checkbox("Confirmo que el activo físico fue adquirido; no es solo una propuesta PYDI")
            submitted = st.form_submit_button("Registrar activo e ID")
        if submitted:
            if not confirm:
                st.error("Confirme adquisición física del activo.")
            else:
                try:
                    code = register_machine(options[selected], location, model=model, serial=serial,
                                            maintenance=maintenance, acquired_at=str(acquired) if acquired else None)
                    st.session_state.v3_created_codes = [code]
                except InventoryError as exc:
                    st.error(str(exc))
    _created_pdf()


def _pdf() -> None:
    st.subheader("PDF de etiquetas existentes")
    st.caption("Orden: categoría, producto/presentación, lote y código. Máximo 200 por archivo A4.")
    search = st.text_input("Filtrar lote, código o nombre", key=_key("pdf_search"))
    found = records(text=search or None, limit=2000)
    mapping = {f"{r['category']} · {r['name']} · {r['presentation'] or ''} · {r['lot_code'] or ''} · {r['code']}": r["code"] for r in found}
    selected = st.multiselect("Códigos ya registrados", list(mapping), max_selections=200)
    if selected:
        codes = [mapping[label] for label in selected]
        st.download_button("Descargar/reimprimir PDF", labels_pdf(codes), "etiquetas_existentes.pdf", "application/pdf")
        _label_preview(codes[0])
    else:
        st.info("Seleccione al menos un código existente.")


def _consult() -> None:
    st.subheader("Consultar QR, Code 128 e historial")
    scanned = st.text_input("Escanee o pegue el ID completo", key=_key("lookup"))
    if scanned:
        try:
            row = get_record(scanned)
            if row is None:
                st.error("Código inexistente.")
            else:
                detail = dict(row)
                detail["fecha_local"] = _local(detail["created_at_utc"])
                st.json(detail)
                _label_preview(row["code"])
                st.download_button("Reimprimir esta etiqueta PDF", labels_pdf([row["code"]]), "etiqueta_consulta.pdf", "application/pdf")
                _table(movements(row["code"]), label="Kardex cronológico (más reciente primero)")
                if row["sale_id"]:
                    st.info(f"Vendido en folio {row['sale_id']} · {_local(row['sold_at_utc'])}")
        except InventoryError as exc:
            st.error(str(exc))
    c1, c2, c3 = st.columns(3)
    category = c1.selectbox("Categoría", ["Todas", *CATEGORIES], key=_key("filter_cat"))
    status = c2.selectbox("Estado", ["Todos", "DISPONIBLE", "VENDIDO", "AGOTADO", "ACTIVO", "EN_MANTENIMIENTO", "FUERA_DE_SERVICIO"], key=_key("filter_status"))
    lot = c3.text_input("Lote contiene", key=_key("filter_lot"))
    opts = {"Todas": None, **{f"{p['label']} · {p['sku']}": p["id"] for p in presentations(enabled_only=False)}}
    presentation = st.selectbox("Presentación", list(opts), key=_key("filter_presentation"))
    _table(records(category=None if category == "Todas" else category,
                   status=None if status == "Todos" else status, lot=lot or None,
                   presentation_id=opts[presentation], limit=1000), label="Resultados")


def _inventory() -> None:
    st.subheader("Inventario disponible actual")
    active = records(active_only=True, limit=10000)
    finished = [r for r in active if r["category"] == CATEGORIES[0]]
    raw = [r for r in active if r["category"] == CATEGORIES[1]]
    machines = [r for r in active if r["category"] == CATEGORIES[2]]
    c1, c2, c3 = st.columns(3)
    c1.metric("Bolsas vendibles", len(finished))
    c2.metric("Lotes MP con saldo", len(raw))
    c3.metric("Máquinas activas", len(machines))
    if finished:
        summary = pd.DataFrame(finished).groupby(["presentation", "grams"], dropna=False).size().reset_index(name="unidades")
        st.dataframe(summary, width="stretch", hide_index=True)
    tabs = st.tabs(CATEGORIES)
    for tab, category, rows in zip(tabs, CATEGORIES, (finished, raw, machines)):
        with tab:
            _table(rows)
            st.download_button("Descargar CSV de esta categoría", pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"),
                               f"inventario_{category.replace(' ','_')}.csv", "text/csv")
    st.download_button("Descargar inventario actual XLSX", inventory_xlsx(), "inventario_actual.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.caption("VENDIDO y AGOTADO no figuran aquí; se conservan en Consulta e Historial.")
    st.divider()
    st.markdown("**Consumo de materia prima**")
    with st.form(_key("consume_form")):
        code = st.text_input("Código MP")
        quantity = st.text_input("Cantidad a consumir", value="1")
        unit = st.selectbox("Unidad", ["kg", "g"])
        reason = st.text_input("Motivo / orden de producción")
        submitted = st.form_submit_button("Registrar consumo")
    if submitted:
        try:
            remaining = consume_raw(code, quantity, unit, reason)
            st.success(f"Consumo confirmado. Saldo: {remaining} g.")
        except InventoryError as exc:
            st.error(str(exc))
    st.markdown("**Estado de maquinaria**")
    with st.form(_key("machine_status_form")):
        code = st.text_input("Código MQ")
        status = st.selectbox("Nuevo estado", ["ACTIVO", "EN_MANTENIMIENTO", "FUERA_DE_SERVICIO"])
        reason = st.text_input("Motivo de cambio")
        submitted = st.form_submit_button("Registrar cambio de estado")
    if submitted:
        try:
            set_machine_status(code, status, reason)
            st.success("Estado auditado.")
        except InventoryError as exc:
            st.error(str(exc))


def _pos() -> None:
    st.subheader("Punto de venta · registro interno")
    st.caption("Lector USB tipo teclado o entrada manual. Sin cobro electrónico ni CFDI.")
    if "v3_cart" not in st.session_state:
        st.session_state.v3_cart = []
    if "v3_operation" not in st.session_state:
        st.session_state.v3_operation = str(uuid4())
    code = st.text_input("Escanear ID PT", key=_key("sale_scan"))
    if st.button("Añadir bolsa al carrito"):
        try:
            normalized = normalize_code(code)
            row = get_record(normalized)
            if row is None:
                raise InventoryError("Código inexistente.")
            if row["category"] != CATEGORIES[0] or row["status"] != "DISPONIBLE" or row["price_cents"] is None:
                raise InventoryError("Bolsa no vendible: categoría, estado o precio pendientes.")
            if normalized in st.session_state.v3_cart:
                raise InventoryError("Código ya presente en el carrito.")
            st.session_state.v3_cart.append(normalized)
        except InventoryError as exc:
            st.error(str(exc))
    cart = []
    for item_code in st.session_state.v3_cart:
        row = get_record(item_code)
        if row:
            cart.append(row)
    if cart:
        view = [{"código": row["code"], "producto": row["name"], "presentación": row["presentation"],
                 "lote": row["lot_code"], "estado actual": row["status"],
                 "MXN": None if row["price_cents"] is None else row["price_cents"] / 100} for row in cart]
        _table(view, label="Carrito")
        st.metric("Total preliminar", f"${sum(row['price_cents'] or 0 for row in cart)/100:,.2f} MXN")
        if st.button("Vaciar carrito (sin afectar inventario)"):
            st.session_state.v3_cart = []
            st.session_state.v3_operation = str(uuid4())
            st.rerun()
        notes = st.text_input("Nota interna opcional", max_chars=300)
        if st.button("Confirmar venta", type="primary"):
            try:
                result = sell(st.session_state.v3_cart, st.session_state.v3_operation, notes=notes)
                st.session_state.v3_last_sale = result
                st.session_state.v3_cart = []
                st.session_state.v3_operation = str(uuid4())
                st.rerun()
            except InventoryError as exc:
                st.error(str(exc))
    else:
        st.info("Carrito vacío. Escanee una bolsa con precio definido.")
    result = st.session_state.get("v3_last_sale")
    if result:
        st.success(f"Venta confirmada · folio {result['id']} · {_local(result['created_at_utc'])} · ${result['total_cents']/100:,.2f} MXN")
        _table(result["lines"], label="Líneas vendidas")


def _history() -> None:
    st.subheader("Historial permanente")
    c1, c2 = st.columns(2)
    from_filter = c1.date_input("Desde (opcional)", value=None)
    to_filter = c2.date_input("Hasta (opcional)", value=None)
    code = st.text_input("Código exacto (opcional)", key=_key("history_code"))
    try:
        sales = list_sales(from_date=str(from_filter) if from_filter else None,
                           to_date=str(to_filter) if to_filter else None, code=code or None)
        _table([{**sale, "fecha_local": _local(sale["created_at_utc"])} for sale in sales], label="Ventas")
        if sales:
            sale_id = st.selectbox("Folio para ver líneas", [sale["id"] for sale in sales])
            detail = get_sale(sale_id)
            if detail:
                _table(detail["lines"], label="Líneas del folio")
        _table(movements(code or None), label="Movimientos de stock")
        _table(audit_events(), label="Auditoría de eventos")
    except InventoryError as exc:
        st.error(str(exc))
    st.caption("No se ofrece anulación automática. Una corrección requiere procedimiento administrativo y conserva el historial.")


def _settings() -> None:
    st.subheader("Configuración y catálogos")
    st.code(str(database_path()), language="text")
    st.caption("SQLite local fuera de OneDrive por defecto. Use INDUSTRIAL_APP_DB_PATH para una ruta autorizada.")
    if st.button("Crear respaldo no destructivo de SQLite"):
        backup = backup_database()
        st.success(f"Respaldo creado: {backup}")
    st.markdown("**Presentaciones PYDI y personalizadas**")
    _table(presentations(enabled_only=False))
    with st.form(_key("presentation_form")):
        label = st.text_input("Nombre de presentación nueva")
        weight = st.number_input("Gramos", min_value=1, max_value=100000, value=None, step=1,
                                 help="Ingrese el gramaje real de la presentación nueva.")
        sku = st.text_input("SKU nuevo")
        price = st.text_input("Precio MXN opcional; vacío = no vendible")
        confirm = st.checkbox("Confirmo esta presentación nueva y sus datos capturados")
        submitted = st.form_submit_button("Crear presentación")
    if submitted:
        if not confirm:
            st.error("Confirme el alta de presentación.")
        else:
            try:
                created = add_presentation(label, weight, sku, price)
                st.success(f"Presentación creada: {created['label']} ({created['grams']} g).")
            except InventoryError as exc:
                st.error(str(exc))
    existing = presentations(enabled_only=False)
    if existing:
        labels = {f"{p['label']} · {p['sku']}": p for p in existing}
        selected = st.selectbox("Presentación a administrar", list(labels), key=_key("presentation_selected"))
        value = labels[selected]
        with st.form(_key("presentation_edit_" + value["id"])):
            new_label = st.text_input("Nombre editable", value=value["label"])
            new_weight = st.number_input("Gramos editables", min_value=1, max_value=100000, value=value["grams"], step=1)
            new_sku = st.text_input("SKU editable", value=value["sku"])
            new_price = st.text_input("Nuevo precio MXN (vacío conserva el actual)")
            enabled = st.checkbox("Habilitada para nuevas altas", value=bool(value["enabled"]))
            submitted = st.form_submit_button("Guardar presentación")
        if submitted:
            try:
                set_presentation(value["id"], label=new_label, grams_value=new_weight, sku=new_sku,
                                 price_mxn=new_price or None, enabled=enabled)
                st.success("Presentación actualizada; ventas anteriores conservan su precio de línea.")
            except InventoryError as exc:
                st.error(str(exc))
    st.markdown("**Agregar materia prima o equipo al catálogo**")
    with st.form(_key("catalog_form")):
        category = st.selectbox("Categoría nueva", [CATEGORIES[1], CATEGORIES[2]])
        name = st.text_input("Nombre")
        sku = st.text_input("Código de catálogo / modelo")
        submitted = st.form_submit_button("Agregar al catálogo")
    if submitted:
        try:
            item = add_catalog_item(category, name, sku)
            st.success(f"Catálogo actualizado: {item['name']}.")
        except InventoryError as exc:
            st.error(str(exc))
    _table(catalog(), label="Catálogo actual")


def render() -> None:
    st.header("Códigos e inventario · Industrial App V3")
    st.caption("Persistencia SQLite independiente de los botones globales V2. Sin existencias ficticias al iniciar.")
    tabs = st.tabs(["Generar", "PDF etiquetas", "Consultar", "Inventario actual", "Punto de venta", "Historial", "Configuración/catálogos"])
    for tab, handler in zip(tabs, (_generate, _pdf, _consult, _inventory, _pos, _history, _settings)):
        with tab:
            handler()


def clear_transient_state(state=None) -> None:
    """Limpia solo widgets/filtros/carrito V3; no abre ni modifica SQLite."""
    if state is None:
        state = st.session_state
    revision = state.get("v3_revision", 0) + 1
    for key in list(state):
        if key.startswith("v3_"):
            del state[key]
    state["v3_revision"] = revision
