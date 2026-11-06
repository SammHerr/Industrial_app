# Inventario de fórmulas y límites documentales PYDI V2

Fuente canónica: `Paquete_Codex_Industrial_App_V2_SHA/referencias_v2/Proyecto PYDI (1)(1).docx`. Se inspeccionaron 366 párrafos, 36 tablas y 19 ecuaciones OMML con `scripts/inspect_word.py`. Las imágenes del índice confirmaron la numeración 1–39. Las páginas citadas abajo son físicas según el mapa V2; los números impresos en el índice del Word difieren en algunos apartados.

## Fórmulas explícitas o aritmética directa del Word

| Apartado | Fórmula | Unidades y condiciones | Evidencia |
|---|---|---|---|
| 2 | `T_disp = T_turno - T_preparación - T_comida` | s/turno; debe ser >0 | OMML 0, p.11 |
| 2 | `Lotes_base = T_disp / T_ciclo` | lotes/turno; ciclo >0. Continuo y entero se muestran por separado | OMML 1–2, p.11 |
| 2 | `kg_base = lotes_base × kg_objetivo_lote` | kg/turno; resultado continuo | OMML 2, p.11 |
| 3 | `P_j = Σ(w_i × s_ij)` | puntos; Σ pesos =1 | OMML 3–9, pp.18–19; tabla 8 |
| 4 | `Qe = CF/(P-CVU)` | bolsas 250 g/mes; `P>CVU` | OMML 14–16, pp.25–26 |
| 4 | `Ingreso = P×Q`, `CT = CF+CVU×Q` | MXN/mes; derivación algebraica de Qe | OMML 17–18 y tabla de costos |
| 7 | `M_i = q_i/lote × lotes/día × días/mes` | kg/mes; insumos empaques usan factor equivalente derivado de tabla redondeada | §7 p.33, tabla 19 |
| 7,16 | `%_i = valor_i/Σvalor×100`; acumulado = Σ% | %; total >0 | Tablas 19 y 28, álgebra directa |
| 12 | `TW_i=I_i×d_i` | kg·m/día; intensidad kg/día | §12 p.41, tablas 22–23 |
| 12 | `D_i=n_i×d_i` | m/día con carga | §12 p.41, tablas 22–23 |
| 12 | `T_i=n_i×(2d_i/v+t_c)` | s/día; v>0, `t_c` 30 s base y 45 s propuesta [S] | §12 p.41, tablas 22–23 |
| 12,15 | `Reducción=(base-propuesto)/base×100` | %; sin cálculo si base=0 | Tabla 24, derivación algebraica |
| 18 | `5S=puntos/(20×2)×100` | %; exige 20 respuestas 0/1/2 | §18 pp.49–51, tabla 29 |
| 39 | Razones y conteos de los 10 indicadores | %, s/lote, m/día o conteo según indicador; divisor >0 | §39 pp.59–61, tabla 34 |

El valor del Word `Qe=8,055` no coincide con `190300/(35-11.38)=8056.73158`, que exige **8,057 bolsas enteras**. El Word declara 10 kg/lote aunque la receta suma 11.75 kg. Las filas P-Q suman 2,553.1 kg/mes frente a 2,553.0 textual; Pareto suma 165.1 frente a 165.2 min/día. Las rutas están redondeadas y sus totales recalculados varían décimas. La app conserva ambas cifras y alerta.

## Complementos metodológicos [M]

Estas ecuaciones **no aparecen como fórmula explícita en PYDI**. Son operativas únicamente con entradas suficientes del usuario.

| Apartado | Método y supuestos | Dimensión / límite |
|---|---|---|
| 7 | ABC con umbrales configurables A/B sobre porcentaje acumulado | %; no es cercanía Muther |
| 11 | Rejilla rectangular de cajas: máximo entre orientaciones ortogonales | cajas/cama; no certifica carga, estabilidad ni inocuidad |
| 21–23 | Ocupación `ocupadas/totales×100`, comparación carga prevista con nominal | %, kg; requiere inventario/ficha de proveedor |
| 24 | `ceil(bolsas_250/24)`, `ceil(bolsas_500/12)` | cajas enteras; capacidades Word §9 |
| 27 | `floor(t_operativo/t_vehículo)×posiciones` | vehículos/turno; no modela cola ni variabilidad |
| 34 | `LCC_nominal=I0+n(O+M)+R−Vres+Cdisp` | MXN nominal; reinversión agregada al final por simplificación |
| 34 | `LCC_desc=I0+Σ[(O+M)/(1+r)^t]+(R+Cdisp−Vres)/(1+r)^n` | MXN presentes; requiere tasa y flujos; reinversión al final |
| 34 | Sensibilidad del LCC descontado en 11 tasas uniformes entre límites editables | MXN presentes por tasa; no estima probabilidades ni sustituye cotizaciones |
| 35 | `VPN=−I_adicional+Σ[flujo_t/(1+r)^t]`; payback simple `I_adicional/ahorro_neto` | MXN presentes/años; ahorro constante positivo para payback |
| 36 | `Σ(peso×calificación)` | puntos, pesos Σ=1, escala 0–100 |
| 38 | CPM ES/EF/LS/LF en red acíclica | semanas; duración y predecesoras completas |

No hay datos suficientes en el Word para recalcular LCC $424,267/$289,135, VPN $135,132 o payback 2.43 años. Se muestran como referencias [D], nunca como resultados verificados. El cronograma de 12 semanas es referencia [D]; las ventanas de la semilla son [M] ilustrativas y no habilitan CPM sin duraciones/dependencias.

## Reproducción de la extracción

```powershell
.\.venv\Scripts\python.exe scripts\inspect_word.py
.\.venv\Scripts\python.exe scripts\inspect_word.py --equations
.\.venv\Scripts\python.exe scripts\inspect_word.py --table 17
```

`scripts/build_word_seed.py` extrae de forma determinista 25 tablas seleccionadas a `pydi/data/word_tables.json`. Ese JSON conserva celdas originales; las conversiones numéricas y su validación están en `pydi/v2_model.py` y `pydi/calculations/`.
