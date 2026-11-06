# Matriz de trazabilidad de los 39 apartados PYDI

Fuente principal: `Proyecto PYDI (1)(1).docx`; páginas **físicas** según el mapa V2. Las imágenes del índice muestran en algunos casos páginas impresas distintas. `[D]` declarado, `[S]` supuesto del Word, `[C]` derivado, `[M]` complemento metodológico, `[U]` editado. Una pantalla de captura cubre funcionalmente el apartado, pero los resultados que requieren mediciones o cotizaciones siguen pendientes.

| Nº | Apartado / pantalla | Método, variables y unidad | Fuente/página y tipo | Función Python | Verificación |
|---:|---|---|---|---|---|
| 1 | Producto · Producto y proceso | Receta `kg/lote`, `MXN/kg`; masa entrada | §1 pp.6–8 [D] | `ingredients` | `test_seed_coverage_and_capacity` |
| 2 | Proceso · Producto y proceso | `T_disp`, ciclo, lotes/turno, bolsas/mes | §2 pp.9–15 OMML [D/C] | `capacity`, `production` | `test_seed_coverage_and_capacity` |
| 3 | Localización · Localización | `Σw_i s_ij`, puntos; terrenos MXN y emergencias estimadas | §3 pp.16–23 [D/S] | `location_scores` | `test_location_weights_and_scores` |
| 4 | Costos · Costos y equilibrio | `CF/(P−CVU)`, bolsas 250 g/mes; ingresos/CT MXN | §4 pp.23–27 OMML [D/C] | `fixed_costs`, `break_even` | `test_equilibrium_and_word_discrepancy` |
| 5 | Elementos · Elementos, 7R y P-Q | 42 códigos ASO, unidad, lote, ubicación, inventario sin medición | §5 pp.28–31 tabla 17 [D/S] | `make_example_case` | `test_seed_coverage_and_capacity` |
| 6 | 7 R · Elementos, 7R y P-Q | 7 estados y evidencias, conteos | §6 pp.31–33 tabla 18 [D] | `seven_r` | `test_pareto_7r_5s_missing_and_complete` |
| 7 | P-Q · Elementos, 7R y P-Q | kg/lote×lotes/día×días/mes; %, ABC configurable | §7 pp.33–34 tabla 19 [D/C/M] | `pq` | `test_production_pq_and_reactivity` |
| 8 | Fichas · Elementos, 7R y P-Q | Especificación y faltantes por ingrediente/equipo | §8 p.34; título y datos §1/20 [D/M] | `make_example_case` | Inspección UI |
| 9 | Carga unitaria · Cargas y estiba | CU-1…CU-7, kg, dimensiones, equipo | §9 pp.34–36 tabla 20 [D/S] | `make_example_case` | Inspección UI |
| 10 | Contenedores · Cargas y estiba | cm, kg, capacidad, cantidad | §10 pp.36–38 tabla 21 [D/S] | `make_example_case` | Inspección UI |
| 11 | Estiba · Cargas y estiba | rejilla cajas/cama, camas, carga nominal pendiente | §11 pp.38–39 [D/M/C] | `pallet_geometry` | `test_storage_picking_docks_boundaries` |
| 12 | T.W. · Transporte y plano | `I×d`, `n×d`, `n(2d/v+t_c)`; kg·m, m, s por día | §12 pp.40–43 tablas 22–24 [D/S/C] | `routes`, `route_summary` | `test_transport_totals_classification_and_override` |
| 13 | Hilos y D-I · Transporte y plano | x distancia m, y intensidad kg/día; plano conceptual | §13 pp.44–45 [D/M] | `di_chart`, `layout_chart` | Inspección UI |
| 14 | Desperdicios · Mejora y causas | 7 evidencias y acciones, implantación [U] | §14 pp.45–46 tabla 26 [D/S] | `make_example_case` | Inspección UI |
| 15 | Plan mejora · Mejora y causas | comparativa narrativa; reducción solo §12 calculable | §15 pp.46–47 tabla 27 [D/C] | `route_summary` | `test_transport_totals_classification_and_override` |
| 16 | Pareto · Mejora y causas | min/día, %, acumulado | §16 pp.47–48 tabla 28 [D/C] | `pareto` | `test_pareto_7r_5s_missing_and_complete` |
| 17 | Ishikawa · Mejora y causas | 6M y relaciones editables; sin frecuencia inventada | §17 pp.48–49 [D/M] | `ishikawa_chart` | Inspección UI |
| 18 | 5S · Calidad y equipos | 20×0/1/2, puntos/40×100, % solo completo | §18 pp.49–51 tabla 29 [D/C/U] | `five_s` | `test_pareto_7r_5s_missing_and_complete` |
| 19 | CIC-MHE · Calidad y equipos | 10 principios, estado/evidencia/acción | §19 pp.51–53 tabla 30 [D/S/U] | `make_example_case` | Inspección UI |
| 20 | Equipos · Calidad y equipos | fichas, capacidades, costos pendientes MXN | §20 pp.53–55 tablas 31–32 [D/S/U] | `make_example_case` | Inspección UI |
| 21 | Dedicado · Almacén y logística | posiciones ocupadas/totales %, alérgenos, PEPS | §21 p.55 solo título [M/U] | `occupancy` | `test_storage_picking_docks_boundaries` |
| 22 | Aleatorio · Almacén y logística | ubicaciones/lotes/fechas, rotación | §22 p.55 solo título [M/U] | editor de `aleatorio` | Inspección UI |
| 23 | Estructuras · Almacén y logística | m, kg nominal vs previsto, seguridad pendiente | §23 p.55 solo título [M/U] | editor de `estructuras` | Inspección UI |
| 24 | Picking · Almacén y logística | `ceil(bolsas/24 o 12)`, cajas; recorrido capturado m | §24 p.55; caja §9 [D/M] | `picking` | `test_storage_picking_docks_boundaries` |
| 25 | Identificación · Almacén y logística | código/lote/ubicación, etiqueta SVG demostrativa | §25 p.55, Code 128 propuesto [D/M] | `code128_svg`, editor de `identificaciones` | `test_code128_layout_and_pqrst_export` |
| 26 | Sistemas · Almacén y logística | bitácora local de eventos, sin WMS/ERP | §26 p.55 solo título [M/U] | editor de `eventos` | Inspección UI |
| 27 | Muelles · Almacén y logística | `floor(T_operativo/T_vehículo)×posiciones`, vehículos/turno | §27 p.55 solo título [M/U] | `dock_capacity` | `test_storage_picking_docks_boundaries` |
| 28 | Auxiliar · Almacén y logística | equipo/capacidad/mantenimiento/costo | §28 p.55; equipos §20 [D/M] | editor de `auxiliar` | Inspección UI |
| 29 | Estrategia · Plan SHA | roles, secuencia, PEPS/FEFO, riesgos | §29 p.55 solo título [M/U] | editor de `operacion` | Inspección UI |
| 30 | Consolidación · Plan SHA | P/Q/R/S/T sincronizado y exportable, planes A/B/C | §30 p.56 solo título [M/C] | `compute_case`, editor de `planes` | `test_code128_layout_and_pqrst_export` |
| 31 | Clasificación · Transporte y plano | ≤15 m y <1000 kg/día manejo simple; retorno vacío aparte | §31 pp.56–57 tabla 33 [D/C] | `routes` | `test_transport_totals_classification_and_override` |
| 32 | Métodos y equipo · Plan SHA | capacidad/higiene/ergonomía/costo por ruta | §32 p.57 solo título [M/U] | editor de `metodos` | Inspección UI |
| 33 | Plano · Transporte y plano | áreas 30×20 m; posiciones [M] editables | §33 p.57; áreas §13 [D/M] | `layout_chart` | `test_code128_layout_and_pqrst_export` |
| 34 | LCC · Economía y selección | LCC nominal/descontado MXN, años/tasa y sensibilidad editable | §34 p.57; cifras §19/37 [D/M] | `life_cycle` | `test_finance_requires_inputs_and_separates_discounting` |
| 35 | Inversión y payback · Economía | ahorro neto, VPN MXN, payback años | §35 p.57; cifra §37 [D/M] | `payback`, `npv` | `test_finance_requires_inputs_and_separates_discounting` |
| 36 | Evaluación cualitativa · Economía | `Σpeso×calificación`, puntos | §36 p.57 solo título [M/U] | `multicriteria` | `test_multicriteria_and_cpm_cycles` |
| 37 | Selección · Economía | B documental; decisión dinámica solo con LCC y puntuación | §37 pp.57–58 [D/M/C] | `_economics` | Inspección UI |
| 38 | Cronograma · Cronograma y auditoría | 12 semanas referencia; ES/EF/LS/LF si red válida | §38 p.58 figura [D/M] | `cpm`, `gantt_chart` | `test_multicriteria_and_cpm_cycles` |
| 39 | Auditoría · Cronograma y auditoría | 10 KPIs, metas, medición [U], semáforo y PDCA | §39 pp.59–61 tabla 34 [D/M/U] | `audit_measurements` | `test_auditoria_only_user_measurements` |

Las 39 pantallas o registros están implementados. Los apartados 8, 21–30, 32–36 y la red CPM del 38 tienen cobertura de captura o complemento [M] porque el Word no aporta todos los datos necesarios. La matriz no declara esos cálculos como validados por PYDI.
