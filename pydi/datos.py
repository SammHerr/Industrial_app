"""Cifras iniciales transcritas del Proyecto PYDI (1).docx.

Las cantidades de rutas están redondeadas en el documento. Las tablas son copias
iniciales editables; los cálculos no dependen de constantes ocultas.
"""

import pandas as pd

PRODUCTO = "Polvo de avena con soya para bebida refrescante"
FUENTE = "Proyecto PYDI (1).docx, archivo local de referencias"
LOTE_DECLARADO_KG = 10.0
BOLSAS_POR_LOTE = {"250 g": 32, "500 g": 4}
LOTES_PROPUESTOS_DIA = 7.75
DIAS_MES = 26
COSTO_FIJO_MENSUAL = 190_300.0
COSTO_VARIABLE_250 = 11.38
PRECIO_250 = 35.0
COSTO_LOTE_REPORTADO = 455.0
TOTAL_PQ_TEXTUAL = None  # El total de la tabla debe derivarse de sus filas.


def materiales_iniciales() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("MAT-01", "Avena", "Materia prima", "kg", 3.5, 87.5),
            ("MAT-02", "Soya", "Materia prima", "kg", 6.0, 240.0),
            ("MAT-03", "Cacahuate", "Materia prima", "kg", 2.0, 90.0),
            ("MAT-04", "Canela", "Materia prima", "kg", 0.25, 7.5),
            ("EMP-01", "Bolsas", "Empaque", "pieza", 36.0, 30.0),
        ],
        columns=["codigo", "nombre", "tipo", "unidad", "consumo_por_lote", "costo_por_lote"],
    )


def siete_r_iniciales() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("Material correcto", "Parcial"),
            ("Cantidad correcta", "No cumple"),
            ("Condición correcta", "Parcial"),
            ("Lugar correcto", "No cumple"),
            ("Tiempo correcto", "Parcial"),
            ("Posición/secuencia correctas", "Parcial"),
            ("Costo correcto", "Parcial"),
        ],
        columns=["criterio", "estado"],
    ).assign(notas="")


def pq_inicial() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("Soya", 1209.0),
            ("Avena", 705.3),
            ("Cacahuate", 403.0),
            ("Cajas de cartón", 143.1),
            ("Canela", 50.4),
            ("Bolsas de empaque", 38.7),
            ("Etiquetas", 3.6),
        ],
        columns=["material", "kg_mes"],
    )


def produccion_inicial() -> pd.DataFrame:
    return pd.DataFrame(
        [("250 g", 6448), ("500 g", 806)],
        columns=["presentacion", "bolsas_mes"],
    )


_RUTAS = [
    ("B1", "Descarga camión", "Recepción", 91.06, 1.82, 6.5),
    ("B2", "Recepción", "Almacén MP", 91.06, 1.82, 5.5),
    ("B3", "Almacén MP", "Báscula de empaque", 91.06, 31.0, 31.0),
    ("B4", "Báscula de empaque", "Tostado", 91.06, 31.0, 23.0),
    ("B5", "Tostado", "Molino", 81.38, 38.75, 7.5),
    ("B6", "Molino", "Empaque", 77.50, 15.50, 6.5),
    ("B7", "Insumos de empaque", "Empaque", 7.13, 7.75, 15.5),
    ("B8", "Empaque", "Almacén PT", 84.49, 12.92, 8.5),
    ("B9", "Almacén PT", "Embarque", 84.49, 12.92, 5.5),
    ("P1", "Descarga camión", "Recepción", 91.06, 1.82, 6.5),
    ("P2", "Recepción", "Almacén MP", 91.06, 0.67, 5.5),
    ("P3", "Almacén MP", "Preparación", 91.06, 2.0, 8.5),
    ("P4", "Preparación", "Tostado", 91.06, 7.75, 8.5),
    ("P5", "Tostado", "Molino", 81.38, 7.75, 7.5),
    ("P6", "Molino", "Empaque", 77.50, 7.75, 6.5),
    ("P7", "Insumos de empaque", "Kit diario", 7.13, 1.0, 15.5),
    ("P8", "Empaque", "Almacén PT", 84.49, 2.0, 8.5),
    ("P9", "Almacén PT", "Embarque", 84.49, 2.0, 5.5),
]


def rutas_iniciales(metodo: str) -> pd.DataFrame:
    prefijo = "B" if metodo == "Base" else "P"
    return pd.DataFrame(
        [fila for fila in _RUTAS if fila[0].startswith(prefijo)],
        columns=["id", "origen", "destino", "intensidad_kg_dia", "viajes_dia", "distancia_m"],
    )


def pareto_inicial() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("Dosificación sin báscula en preparación", 93.0),
            ("Charolas calientes una por una", 30.1),
            ("Recipientes de polvo no estandarizados", 11.5),
            ("PT caja por caja", 10.5),
            ("Surtido embarque caja por caja", 9.1),
            ("Insumos empaque por lote", 8.3),
            ("Recepción sin carga unitaria", 2.6),
        ],
        columns=["causa", "min_dia"],
    )
