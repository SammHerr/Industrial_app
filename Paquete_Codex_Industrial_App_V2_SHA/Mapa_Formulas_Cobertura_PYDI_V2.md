# Industrial App V2 — Mapa de trazabilidad y cobertura de Proyecto PYDI

**Naturaleza de la referencia.** Extracto de orientación para Codex elaborado a partir de `Proyecto PYDI (1)(1).docx` (63 páginas). El Word completo tiene prioridad sobre este resumen. Las páginas aquí son páginas físicas del documento, no números visualizados en el índice. Nunca convertir un dato declarado/supuesto en un dato experimental o certificado.

## Clasificación de fuentes
- **[D] Declarado**: valor/número expresado en el Word, puede ser una cifra reportada sin fórmula completa.
- **[C] Recomputado**: valor obtenido usando fórmula declarada y entradas reales, mostrar fórmula y unidades.
- **[S] Supuesto Word**: medida, velocidad, tasa o parámetro indicado como estimado o propuesto.
- **[M] Complemento metodológico**: fórmula estándar, formulario o valor de DEMOSTRACIÓN que no aparece como dato/fórmula explícita en el Word. NUNCA afirmar que procede del estudio ni que está validado.
- **[U] Introducido por usuario**: escenario diferente y editable.

## Secciones del índice y pantallas necesarias
| Número del Word | Apartado | Páginas físicas | Tipo de pantalla y cálculo | Evidencia de fuente |
|---|---|---|---|---|
| 1 | Descripción de producto | 6–8 | Ficha, presentaciones, ingredientes, masa, costos | Tabla de ingredientes p.8 |
| 2 | Descripción del proceso | 9–15 | Diagrama flujo, ciclo, capacidad, lotes, bolsas | Ecuaciones OMML de capacidad p.11 |
| 3 | Ubicación geográfica | 16–23 | Ponderación de municipios, terrenos, servicios | Tabla de ponderación pp.18–19 |
| 4 | Costos de producción | 23–27 | CF, CVU, precio, punto de equilibrio y curva | Ecuación OMML Qe pp.25–26 |
| 5 | Registro formal de elementos | 28–31 | 42 registros codificados, inventario editable | Tablas ASO-* |
| 6 | 7 R | 31–33 | Tabla de cumplimiento y mejora | 5 'Parcial', 2 'No cumple' |
| 7 | Producto-cantidad P-Q | 33–34 | Masa mensual, ABC, presentaciones 250/500 | Tabla p.33 |
| 8 | Fichas técnicas | 34 | Pantalla editable y evidencia de faltantes | Título sin fichas completas |
| 9 | Carga unitaria | 34–36 | CU-1...CU-7 | Tabla CU pp.35–36 |
| 10 | Contenedores y palets | 36–38 | Dimensiones, cargas, compatibilidad | Tabla p.36–38 |
| 11 | Estibado e integridad | 38–39 | Capas, cajas, tarimas, dibujo conceptual | Diagrama p.39 |
| 12 | Trabajo de manejo T.W. | 40–43 | 9 rutas base y 9 propuesta; TW, D, T | Tabla 8A/8B y ecuaciones p.41 |
| 13 | Hilos y distancia–intensidad | 44–45 | D-I, layout conceptual 30×20 m, flujo | Áreas y descripción p.44–45 |
| 14 | 7 desperdicios | 45–46 | Tabla Lean, evidencias, acciones | Tabla pp.45–46 |
| 15 | Reducción de transporte/esperas/inventario | 46–47 | Comparativa base/propuesta y escenarios | Tabla pp.46–47 |
| 16 | Pareto | 47–48 | Tiempo por causa, acumulado y gráfico | Tabla pp.47–48 |
| 17 | Ishikawa | 48–49 | 6M, espina de pescado editable | Figura p.49 |
| 18 | Checklist 5S | 49–51 | 20 criterios × 0/1/2; auditoría | Lista pp.49–51 |
| 19 | CIC-MHE 10 principios | 51–53 | Evaluación y observaciones | Tabla pp.52–53 |
| 20 | Equipos y especificaciones | 53–55 | Fichas máquinas y manejo | Tablas pp.53–55 |
| 21 | Almacenamiento dedicado | 55 | Modelo editable de posiciones/reglas | Solo encabezado específico |
| 22 | Almacenamiento aleatorio | 55 | Modelo editable de ubicaciones | Solo encabezado específico |
| 23 | Estructuras de almacenaje | 55 | Dimensiones/capacidad editable | Solo encabezado específico |
| 24 | Picking | 55 | Pedidos y surtido, métodos [M] | Solo encabezado específico |
| 25 | Tecnología de identificación | 55 | Trazabilidad códigos/barras | Solo encabezado específico |
| 26 | Sistemas de información | 55 | Registro de movimientos/CSV | Solo encabezado específico |
| 27 | Área de muelles | 55 | Capacidad/dimensiones [M] | Solo encabezado específico |
| 28 | Equipamiento auxiliar | 55 | Ficha y capacidades | Solo encabezado específico |
| 29 | Estrategia de operación | 55 | Secuencia, roles y planes | Solo encabezado específico |
| 30 | Consolidación SHA | 56 | Formato de informe y registro | Solo encabezado específico |
| 31 | Clasificación de movimientos | 56–57 | D-I, distancia e intensidad por clases | Tabla p.56–57 |
| 32 | Asignación métodos/equipos | 57 | Matriz de selección [M] | Solo encabezado específico |
| 33 | Plano de flujo | 57 | Diagrama editable conceptual | Solo encabezado específico |
| 34 | Costo del ciclo de vida | 57 | LCC/escenarios, formularios [M] | Solo encabezado específico; cifras en p.53 |
| 35 | Inversión/costos/payback | 57 | Recuperación basada en flujos [M] | Solo encabezado específico; 2.43 años p.58 |
| 36 | Evaluación cualitativa | 57 | Matriz multicriterio editable [M] | Solo encabezado específico |
| 37 | Selección sistema | 57–58 | Regla/justificación, B recomendada por Word | Texto pp.57–58 |
| 38 | Cronograma instalación | 58 | Gantt referencia 12 semanas | Figura p.58 |
| 39 | Plan de auditoría continua | 59–61 | 10 indicadores, metas, frecuencia, medidas | Tabla pp.59–60 |

## Ecuaciones encontradas en Word, parámetros y controles de exactitud

### 2. Producción/capacidad
- `T_disp = 30600 s - 600 s - 1800 s = 28200 s`.
- `Capacidad_lotes = T_disp / T_ciclo` con `T_ciclo = 10200 s/lote` => `2.76470588 lotes/turno` (no confundir con número entero de lotes terminados).
- Masa objetivo del producto: `10 kg/lote`. Dos combinaciones documentales: `32×250g + 4×500g = 10kg`, y el modelo alternativo de `40×250g=10kg` usado en CVU. Mantener escenarios diferenciados.
- Diseño industrial en unidad 2: `7.75 lotes/día`, mes de `26 días` = `201.5 lotes teóricos/mes`; `6448 bolsas/mes (250g)`, `806 bolsas/mes (500g)`, `7254 unidades/mes`.
- Formulación de ingredientes: `3.5 + 6 + 2 + 0.25 = 11.75kg/kit`, no 10kg. No corregir receta automáticamente.

### 3. Ponderación de localizaciones
- `P_j = Σ w_i*s_ij` con `w = [0.15,0.20,0.30,0.20,0.15]`.
- Resultados documentados: Unión Juárez 54.75, Cacahoatán 70, Tapachula 86.
- Terrenos declarados: 1,150,000 / 12,000,000 / 14,000,000 MXN. Área común declarada 10,000 m², verificar fuente/estado.

### 4. Costos/equilibrio
- Costos mensuales: renta 30000, electricidad 10000, agua 1000, publicidad 4000, limpieza 1500, papelería 800, mano de obra directa 114000, indirecta 29000. TOTAL = 190300 MXN/mes.
- Ingredientes/lote de tabla: avena $87.50, soya $240, cacahuate $90, canela $7.50, bolsas $30: total $455/lote.
- CVU de 250 g en Word = $11.38 (valores redondeados 2.19+6+2.25+0.19+0.75). Precio 250 g = $35.
- Ecuación OMML: `Qe = CF / (P-CVU)`. Recalculado `190300/(35-11.38)=8056.731583... bolsas`; `ceil` para unidades vendidas = `8057`. El Word dice **8055**, discrepancia a mostrar. En Word, ventas con Qe reportado = `8055*35 = $281925`.
- Variables faltantes de 500 g: costo/precio detallados. No asumir mismos márgenes ni validación de equilibrio para mezcla.

### 7. P-Q
- Fórmula declarada masa mensual = cantidad/lote × 7.75 lotes/día × 26 días/mes.
- Valores tabulares (kg/mes) en Word: Soya 1209.0; Avena 705.3; Cacahuate 403.0; Cajas 143.1; Canela 50.4; Bolsas 38.7; Etiquetas 3.6.
- Sumatoria de valores redondeados 2553.1 kg vs total reportado **2553.0 kg**. Conservar ambas cifras y advertir.

### 12. T.W. y 13. D-I
- `TW_i = I_i × d_i` (kg/día × m = kg·m/día).
- `D_i = n_i × d_i` (viajes/día × m = m/día).
- `T_i = n_i × (2×d_i / v + t_c)` (seg/día); v = 0.9m/s, t_c base 30seg/viaje, propuesto 45seg/viaje; son supuestos marcados en Word.
- `Δ% = (valor_base - valor_propuesto)/valor_base * 100` como derivación explícita para comparativa.
- Base Word: TW=8417.6 kg·m/día, D=2388.2m/día, T=9911.4s/día (165.2 min/día), viajes=153.48/día.
- Propuesta Word: TW=5048.3 kg·m/día, D=250.4m/día, T=2029.6s/día (33.8 min/día), viajes=32.74/día.
- Retorno de vacíos por separado: `2 viajes × 31.5m = 63m/día` no integrado al TW de producto.
- Clasificación del punto 31: manejo simple distancia ≤15m e intensidad <1000kg/día; transporte simple distancia >15m e intensidad <1000kg/día; rangos adicionales no especificados y requieren criterio [M].

### 16. Pareto
- Causas/tipo con tiempos redondeados: B3+B4 93.0; B5 30.1; B6 11.5; B8 10.5; B9 9.1; B7 8.3; B1+B2 2.6 minutos/día.
- Sumados: **165.1 min/día**, Word dice **165.2**. Usar recalculado como denominador gráfico e indicar comparativa reportada; no ajustar una causa ficticiamente.

### 18. 5S
- 20 criterios reales en Word, 4 por cada categoría Seiri, Seiton, Seiso, Seiketsu, Shitsuke; escala 2=Sí, 1=Parcial, 0=No, máximo 40 puntos, porcentaje de cumplimiento = (puntos/40)×100 cuando está completo. Blanco ≠ 0.

### 19–20, 34–37
- Diez principios CIC-MHE y lista de equipos tienen información descriptiva.
- Reportes económicos del texto: LCC 8 años base $424,267, alternativa propuesta $289,135; VPN de mejora $135,132 y payback 2.43 años. No hay serie de flujos/inversión suficiente para auditar: mostrar 'referencia del Word, no recalculada'. LCC, VPN y payback complementarios [M] requieren tasa y flujos ingresados. Alternativa B recomendada en texto; nuevo cálculo puede cambiar decisión si usuario aporta datos.

### 38–39
- Gantt declarado 12 semanas, ruta crítica narrativa y figura. No adoptar la tabla PERT de 15 semanas del caso BITS.
- 10 KPIs: exactitud inventario (≥98%), PEPS/FEFO (100%), tiempo manejo/lote (≤262 s), distancia carga (≤250m/día según meta del Word), merma manejo (≤0.3%), lotes fuera fórmula (0/mes), 5S (≥80%), incidentes (0), mantenimiento (≥95%), ocupación de almacenes (≤85%).
- Frecuencias diario/semanal/mensual/trimestral/anual y seguimiento PDCA.

## Complementos metodológicos permitidos [M]
Solo si la sección carece de fórmula e insumos:
- Capacidad/ocupación almacenamiento: ocupadas/total ×100.
- Picking: `cajas_250 = ceil(bolsas_250/24)`, `cajas_500 = ceil(bolsas_500/12)` bajo mezcla y lotes; valores del Word son 24 y 12 unidades por caja. Cargas y seguridad requieren medidas verificadas.
- Muelles: capacidad por turno = (tiempo operativo/tiempo por vehículo) × posiciones, condicionado por inputs suficientes y cola no modelada.
- Coste ciclo de vida nominal = I0 + ∑(O_t+M_t+R_t) - V_residual + C_disposición; descontado = I0 + ∑[(O_t+M_t+R_t)/(1+r)^t] + [(C_disposición-V_residual)/(1+r)^N]; NO mezclar las dos variantes.
- VPN incremental de mejora = -I_adicional + ∑(ahorro_neto_t/(1+r)^t), tasa y flujos solicitados; payback simple = I_adicional/ahorro_neto anual si este es constante positivo, o por acumulado si es variable.
- CPM: adelante/atrás sobre grafo acíclico, ES/EF/LS/LF, holgura, ruta crítica; solo con duraciones y predecesoras reales.
- Cualquier ejemplo de costos/tiempos sin fuente debe marcarse “ILUSTRATIVO [M], no validado por PYDI”.

## Comprobaciones finales
1. Todos los puntos 1–39 deben aparecer en cobertura, aunque algunos sean plantillas editables por falta de datos originales.
2. Botones de ejemplo/limpiar deben restaurar TODOS los registros y evitar resultados obsoletos.
3. Sin datos no debe mostrarse Qe, VPN, LCC, payback ni auditoría como valores válidos.
4. Un cambio de inputs afecta exportación y todas las gráficas ligadas.
5. No borrar `sha.py` original sin refactor seguro, ni introducir datos BITS, ni publicar automáticamente al remoto.
