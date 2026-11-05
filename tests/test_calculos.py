from io import BytesIO

import pandas as pd
import pytest

from pydi import datos
from pydi.calculos import (
    calcular_pareto,
    calcular_pq,
    calcular_rutas,
    exportar_xlsx,
    resumir_7r,
    totales_rutas,
    validar_materiales,
    validar_produccion,
)


def escenario():
    materiales = datos.materiales_iniciales()
    siete_r = datos.siete_r_iniciales()
    pq = calcular_pq(datos.pq_inicial())
    produccion = datos.produccion_inicial()
    base = calcular_rutas(datos.rutas_iniciales("Base"), 0.9, 30)
    propuesta = calcular_rutas(datos.rutas_iniciales("Propuesto"), 0.9, 45)
    tb, tp = totales_rutas(base), totales_rutas(propuesta)
    resumen = pd.DataFrame(
        [("T.W.", tb["tw_kg_m_dia"], tp["tw_kg_m_dia"])],
        columns=["indicador", "Base", "Propuesto"],
    )
    pareto = calcular_pareto(datos.pareto_inicial())
    return materiales, siete_r, pq, produccion, base, propuesta, resumen, pareto


def test_trabajo_distancia_y_tiempo_por_ruta():
    ruta = pd.DataFrame([("R1", "A", "B", 10, 3, 8)], columns=datos.rutas_iniciales("Base").columns)
    calculada = calcular_rutas(ruta, 2, 4).iloc[0]
    assert calculada["tw_kg_m_dia"] == 80
    assert calculada["distancia_con_carga_m_dia"] == 24
    assert calculada["tiempo_manejo_min_dia"] == pytest.approx(0.6)


def test_totales_de_rutas_del_word():
    _, _, _, _, base, propuesta, _, _ = escenario()
    tb, tp = totales_rutas(base), totales_rutas(propuesta)
    assert tb["tw_kg_m_dia"] == pytest.approx(8417.6, abs=2)
    assert tp["tw_kg_m_dia"] == pytest.approx(5048.3, abs=2)
    assert tb["distancia_con_carga_m_dia"] == pytest.approx(2388.2, abs=2)
    assert tp["distancia_con_carga_m_dia"] == pytest.approx(250.4, abs=2)
    assert tb["tiempo_manejo_min_dia"] == pytest.approx(165.2, abs=2)
    assert tp["tiempo_manejo_min_dia"] == pytest.approx(33.8, abs=2)


def test_pq_recalcula_porcentaje_y_acumulado():
    tabla = calcular_pq(pd.DataFrame({"material": ["A", "B"], "kg_mes": [30, 10]}))
    assert tabla["porcentaje"].tolist() == [75, 25]
    assert tabla["acumulado_pct"].tolist() == [75, 100]
    assert calcular_pq(datos.pq_inicial())["kg_mes"].sum() == pytest.approx(2553.1)


def test_siete_r_no_asume_cumplimiento():
    _, resumen = resumir_7r(datos.siete_r_iniciales())
    cantidades = dict(zip(resumen["estado"], resumen["cantidad"]))
    assert cantidades == {"Cumple": 0, "Parcial": 5, "No cumple": 2, "No evaluado": 0}


def test_pareto_recalcula_100_por_ciento():
    tabla = calcular_pareto(datos.pareto_inicial())
    assert tabla["min_dia"].sum() == pytest.approx(165.1)
    assert tabla["acumulado_pct"].iloc[-1] == pytest.approx(100)


@pytest.mark.parametrize(
    "funcion,tabla",
    [
        (calcular_pq, pd.DataFrame({"material": ["A"], "kg_mes": [0]})),
        (calcular_pareto, pd.DataFrame({"causa": ["A"], "min_dia": [-1]})),
        (validar_materiales, pd.DataFrame()),
        (validar_produccion, pd.DataFrame({"presentacion": ["A", "A"], "bolsas_mes": [1, 2]})),
    ],
)
def test_entradas_invalidas_visibles(funcion, tabla):
    with pytest.raises(ValueError):
        funcion(tabla)


def test_rutas_rechaza_filas_incompletas_duplicados_y_velocidad_cero():
    rutas = datos.rutas_iniciales("Base")
    with pytest.raises(ValueError, match="velocidad"):
        calcular_rutas(rutas, 0, 30)
    rutas.loc[0, "distancia_m"] = None
    with pytest.raises(ValueError, match="distancia_m"):
        calcular_rutas(rutas, 0.9, 30)
    rutas = datos.rutas_iniciales("Base")
    rutas.loc[1, "id"] = rutas.loc[0, "id"]
    with pytest.raises(ValueError, match="duplicados"):
        calcular_rutas(rutas, 0.9, 30)


def test_exportacion_refleja_edicion_actual():
    materiales, siete_r, pq, produccion, base, propuesta, resumen, pareto = escenario()
    original = exportar_xlsx(
        {"velocidad": 0.9}, materiales, siete_r, pq, produccion, base, propuesta, resumen, pareto
    )
    editado = pq[["material", "kg_mes"]].copy()
    editado.loc[editado["material"] == "Soya", "kg_mes"] = 1500
    nuevo = exportar_xlsx(
        {"velocidad": 0.9}, materiales, siete_r, editado, produccion, base, propuesta, resumen, pareto
    )
    assert original != nuevo
    libro = pd.ExcelFile(BytesIO(nuevo))
    assert {"Parámetros", "Materiales", "7R", "P-Q", "Producción", "Rutas base", "Rutas propuestas", "Resumen", "Pareto"} <= set(libro.sheet_names)
    tabla = pd.read_excel(BytesIO(nuevo), sheet_name="P-Q")
    assert tabla.loc[tabla["material"] == "Soya", "kg_mes"].iloc[0] == 1500
    assert tabla.loc[tabla["material"] == "Soya", "porcentaje"].iloc[0] == pytest.approx(1500 / (2553.1 - 1209 + 1500) * 100)
