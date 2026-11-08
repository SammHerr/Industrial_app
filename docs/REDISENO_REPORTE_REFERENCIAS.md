# Referencias y criterio de rediseño del reporte V4

La fuente de valores es el caso PYDI de `Industrial_App_Referencias_para_Codex/referencias/Proyecto PYDI (1).docx`, la semilla `pydi/data/word_tables.json` y el motor `compute_case`. La guía `Guia_Referencias_Visuales_PYDI_39_Apartados.md` aporta las convenciones y las páginas PDF siguientes. **Los PDF bibliográficos R1–R8 no estaban disponibles en este equipo durante la implementación**, por lo que esas páginas no se cotejaron directamente ni se copiaron figuras. Las referencias de página son las declaradas en la guía, con portada = página PDF 1. Editorial, año e ISBN no se completaron sin ejemplares verificables.

| Ref. | Obra declarada en la guía | Páginas PDF indicadas | Aplicación original en V4 |
|---|---|---|---|
| R1 | Muther y Haganas, *Systematic Handling Analysis* | 2, 54, 60, 64, 70 | Hoja P-Q-R-S-T, T.W. por ruta, matriz desde-hacia y red topológica; §§5, 12, 13, 30–33. |
| R2 | Muther y Hales, *Systematic Layout Planning*, 4.ª ed. | 2, 72, 80, 93, 104, 127, 146 | Matriz triangular de cercanía derivada de intensidad, motivos y limitaciones de espacio; §§3, 7, 13, 30, 33, 36–38. |
| R3 | Muther, *Planificación y proyección de la empresa industrial* | 38, 52, 60, 70, 78, 107, 117, 160 | Convención de secuencia productiva y tabla de comparación de alternativas; §§2, 7, 34. |
| R4 | Heragu, *Facilities Design*, 4.ª ed. | 65, 69, 74, 80, 90, 102, 145 | Fichas de producto, proceso, ubicación y equipos; §§1–3, 8, 10, 20. |
| R5 | Tompkins et al., *Facilities Planning*, 4.ª ed. | 103, 219, 247; caps. 5, 7, 11 | Cargas, almacenes, picking, equipos y política de operación; §§1, 6, 8–11, 19–24, 27–29, 32, 39. |
| R6 | García-Díaz y Smith, *Facilities Planning and Design* | 4, 225, 275; caps. 8–9 | Matriz de flujo, información y capacidad logística; §§12, 19–22, 24–26, 33. |
| R7 | Niebel y Freivalds, *Ingeniería industrial: métodos, estándares y diseño del trabajo*, 12.ª ed. | 4, 55, 113 | Secuencia, desperdicios, Pareto, Ishikawa, 5S, cronograma y auditoría; §§2, 14–18, 38–39. |
| R8 | Sapag Chain y Sapag Chain, *Preparación y evaluación de proyectos*, 5.ª ed. | 150, 313, 345; caps. 6, 14–15 | Costos, punto de equilibrio, LCC, flujos, VPN y recuperación; §§3–4, 34–36. |

## Reglas aplicadas

- Ninguna lámina de libros, captura, logotipo ni diagrama calcado se incorpora al PDF. Las figuras se generan con tablas y parámetros del escenario.
- `[D]` significa dato declarado en PYDI, `[S]` supuesto documental, `[C]` resultado del motor, `[M]` complemento metodológico y `[U]` edición del usuario.
- La matriz SLP propone A/E/I/O/U según intensidad **relativa**; `X` solo podría venir de una incompatibilidad documentada. La red de rutas es un **esquema sin escala**, porque el caso no aporta coordenadas físicas verificadas.
- El flujo lógico V3 ilustra la arquitectura de registro y consulta; no lee ni representa registros de inventario o ventas.
- Sin causas, medidas, costos o fechas suficientes se muestra el faltante específico. No se fabrican resultados para llenar una figura.
