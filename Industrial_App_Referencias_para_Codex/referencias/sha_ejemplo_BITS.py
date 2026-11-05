import io
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Simulador SHA - Manufactura Avanzada BITS",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Simulador SHA - Planta de Manufactura de Dispositivos BITS")
st.markdown("**Tecnológico Nacional de México | Planeación y Diseño de Instalaciones**")
st.caption("Caso de Estudio: Línea de producción integral, calibración inercial y empaque de Kits Didácticos BITS para Laboratorios de Dinámica.")

# Pestañas estructuradas
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "1. P-Q-R-S-T & 7 R",
    "2. Flujo y T.W. Ampliado",
    "3. Selección de Equipos",
    "4. Matriz de Relaciones Ricas",
    "5. Espacio y Pasillos",
    "6. Gráfico D × I Extendido",
    "7. Evaluación Multicriterio",
    "8. KPIs Industriales & PERT",
    "📄 Reporteador Ejecutivo SHA"
])

# ==========================================
# FASE 1: ANÁLISIS P-Q-R-S-T & 7 R
# ==========================================
with tab1:
    st.header("Bloque 1: Caracterización P-Q-R-S-T - Dispositivos BITS")
    # Uso de raw string (r"...") para evitar el SyntaxWarning con '\,'
    st.info(r"📐 **Ecuación del Manejo de Materiales:** $$Materiales (P) + Movimientos (R, T) + Métodos (S) = Sistema\,Recomendado$$")
    
    col_p, col_q = st.columns(2)
    with col_p:
        producto = st.text_input("P - Producto / Materiales", "Kits BITS (Chasis mecanizados, Sensores IMU MPU6050, Encoders ópticos, Masas de prueba, Motorreductores)")
        routing = st.text_area("R - Recorrido / Ruta Básica", "Almacén MP -> Maquinado CNC -> SMT/Soldadura Electrónica -> Ensamble Subconjuntos -> Integración Mecatrónica -> Inspección Visión -> Calibración Dinámica -> Empaque/Kitting -> Almacén PT")
        unidad_carga = st.selectbox("Diseño de Unidad de Carga y Estibado", [
            "Contenedor Plástico Antiestático (Tote ESD) con divisiones termoformadas",
            "Tarima Estandarizada (1.2m x 1.0m) - Cajas máster de Kits BITS",
            "Rack Acojinado Específico para Chasis y Ejes de Precisión"
        ])

    with col_q:
        cantidad = st.text_input("Q - Cantidad / Volumen", "1,200 Kits BITS / mes (Aprox. 60 lotes de prueba)")
        time_val = st.text_input("T - Tiempo / Frecuencia", "Turnos de 8 horas, 5 días/semana (Ritmo Takt Time: 12 min/kit)")
        aidc_tech = st.selectbox("Tecnología AIDC / Captura de Datos (S)", [
            "Etiquetas RFID Pasivas en Totes + Código Datamatrix 2D en Tarjetas BITS",
            "Código de Barras 1D/2D con Escáneres de Fijación en Línea",
            "Integración Completa WMS/MES con Terminales Portátiles RF"
        ])

    support = st.text_input("S - Servicios de Apoyo", "Bancos ESD, Sistema de Aire Comprimido, Cuarto Limpio ISO 8, AMRs, WMS/MES")

    st.markdown("---")
    st.subheader("Validación de las 7 R del Manejo de Materiales")
    r1, r2, r3, r4 = st.columns(4)
    r1.checkbox("1. Material Correcto (Kits/Sensores BITS)", value=True)
    r1.checkbox("2. Cantidad Adecuada (Lotes de ensamble)", value=True)
    r2.checkbox("3. Condición Requerida (Protección ESD/Golpes)", value=True)
    r2.checkbox("4. Secuencia/Orientación (Inserción correcta)", value=True)
    r3.checkbox("5. Lugar Correcto (Estaciones de trabajo)", value=True)
    r3.checkbox("6. Tiempo Oportuno (Sincronizado con Takt Time)", value=True)
    r4.checkbox("7. Costo Óptimo (Costo unitario mínimo)", value=True)

# ==========================================
# FASE 2: FLUJO Y TRABAJO DE TRANSPORTE AMPLIADO
# ==========================================
with tab2:
    st.header("Bloque 2: Mapeo de Flujos y Trabajo de Transporte Detallado (T.W.)")
    st.markdown(r"$$T.W. = I \times D$$")

    datos_iniciales = pd.DataFrame([
        {"origen": "01. Almacén Materia Prima", "destino": "02. Maquinado CNC y Chasis", "intensidad_flujo": 180.0, "distancia": 40.0},
        {"origen": "01. Almacén Materia Prima", "destino": "03. Ensamble Electrónico SMT", "intensidad_flujo": 150.0, "distancia": 25.0},
        {"origen": "02. Maquinado CNC y Chasis", "destino": "04. Subensamble Mecánico", "intensidad_flujo": 160.0, "distancia": 20.0},
        {"origen": "03. Ensamble Electrónico SMT", "destino": "04. Subensamble Mecánico", "intensidad_flujo": 140.0, "distancia": 18.0},
        {"origen": "04. Subensamble Mecánico", "destino": "05. Integración Mecatrónica BITS", "intensidad_flujo": 135.0, "distancia": 15.0},
        {"origen": "05. Integración Mecatrónica BITS", "destino": "06. Inspección Óptica y Visión", "intensidad_flujo": 130.0, "distancia": 12.0},
        {"origen": "06. Inspección Óptica y Visión", "destino": "07. Banco Calibración Dinámica", "intensidad_flujo": 125.0, "distancia": 22.0},
        {"origen": "07. Banco Calibración Dinámica", "destino": "08. Empaque y Kitting Final", "intensidad_flujo": 120.0, "distancia": 30.0},
        {"origen": "08. Empaque y Kitting Final", "destino": "09. Almacén Producto Terminado", "intensidad_flujo": 170.0, "distancia": 60.0}
    ])

    # Reemplazo de use_container_width=True por width="stretch"
    df_rutas = st.data_editor(datos_iniciales, num_rows="dynamic", width="stretch", key="editor_rutas")

    if st.button("🚀 Calcular Trabajo de Transporte y Prioridades", type="primary"):
        if not df_rutas.empty:
            resultados = []
            trabajo_total = 0.0

            for _, row in df_rutas.iterrows():
                try:
                    i, d = float(row["intensidad_flujo"]), float(row["distancia"])
                except (ValueError, TypeError):
                    i, d = 0.0, 0.0

                tw = i * d
                trabajo_total += tw
                resultados.append({
                    "Origen": row["origen"], "Destino": row["destino"],
                    "Intensidad (I)": i, "Distancia (D)": d, "T.W.": tw
                })

            df_res = pd.DataFrame(resultados).sort_values(by="T.W.", ascending=False).reset_index(drop=True)

            acumulado = 0.0
            prioridades, porcentajes = [], []
            for _, row in df_res.iterrows():
                prop = (row["T.W."] / trabajo_total) if trabajo_total > 0 else 0.0
                acumulado += prop
                
                if acumulado <= 0.15: p = "A"
                elif acumulado <= 0.35: p = "E"
                elif acumulado <= 0.65: p = "I"
                elif acumulado <= 0.90: p = "O"
                else: p = "U"

                prioridades.append(p)
                porcentajes.append(round(prop * 100, 2))

            df_res["Prioridad Muther"] = prioridades
            df_res["% del Total"] = porcentajes

            st.session_state["df_flujos_resultado"] = df_res
            st.session_state["trabajo_total_val"] = trabajo_total

            st.success("¡Análisis de Trabajo de Transporte en 9 Estaciones completado!")
            st.metric("Trabajo de Transporte Total (T.W.)", f"{trabajo_total:,.2f} U-m")
            st.dataframe(df_res, width="stretch")

# ==========================================
# FASE 3: SELECCIÓN Y COSTOS DE EQUIPOS
# ==========================================
with tab3:
    st.header("Bloque 3: Selección Tecnológica y Payback")

    col_eq1, col_eq2, col_eq3 = st.columns(3)
    with col_eq1:
        st.markdown("**Opción A (Carretillas y Totes ESD)**")
        inv_a = st.number_input("Inversión Inicial A ($)", value=12000.0, step=500.0, key="inva")
        cf_a = st.number_input("Costo Fijo Anual A ($)", value=4500.0, step=500.0, key="cfa")
        cv_a = st.number_input("Costo Var. A ($/T.W.)", value=1.1, step=0.1, key="cva")
        ahorro_a = st.number_input("Ahorro Anual Estimado A ($)", value=7000.0, step=500.0, key="aha")

    with col_eq2:
        st.markdown("**Opción B (Tren de Arrastre / Tugger Train)**")
        inv_b = st.number_input("Inversión Inicial B ($)", value=45000.0, step=1000.0, key="invb")
        cf_b = st.number_input("Costo Fijo Anual B ($)", value=15000.0, step=500.0, key="cfb")
        cv_b = st.number_input("Costo Var. B ($/T.W.)", value=0.28, step=0.05, key="cvb")
        ahorro_b = st.number_input("Ahorro Anual Estimado B ($)", value=22000.0, step=1000.0, key="ahb")

    with col_eq3:
        st.markdown("**Opción C (Flota AMRs + WMS/MES)**")
        inv_c = st.number_input("Inversión Inicial C ($)", value=130000.0, step=5000.0, key="invc")
        cf_c = st.number_input("Costo Fijo Anual C ($)", value=32000.0, step=1000.0, key="cfc")
        cv_c = st.number_input("Costo Var. C ($/T.W.)", value=0.06, step=0.01, key="cvc")
        ahorro_c = st.number_input("Ahorro Anual Estimado C ($)", value=55000.0, step=2000.0, key="ahc")

    volumen_tw = st.number_input("Volumen Total Estimado de T.W. Anual", value=55000.0, step=1000.0)

    if st.button("📊 Calcular Costos y Periodo de Recuperación"):
        costo_a = cf_a + (cv_a * volumen_tw)
        costo_b = cf_b + (cv_b * volumen_tw)
        costo_c = cf_c + (cv_c * volumen_tw)

        pb_a = inv_a / ahorro_a if ahorro_a > 0 else 0
        pb_b = inv_b / ahorro_b if ahorro_b > 0 else 0
        pb_c = inv_c / ahorro_c if ahorro_c > 0 else 0

        res_costos = pd.DataFrame([
            {"Alternativa": "Opción A (Carretillas Manuales)", "Inversión ($)": inv_a, "Costo Op. Anual ($)": costo_a, "Payback (Años)": round(pb_a, 2)},
            {"Alternativa": "Opción B (Tren de Arrastre)", "Inversión ($)": inv_b, "Costo Op. Anual ($)": costo_b, "Payback (Años)": round(pb_b, 2)},
            {"Alternativa": "Opción C (Flota AMRs)", "Inversión ($)": inv_c, "Costo Op. Anual ($)": costo_c, "Payback (Años)": round(pb_c, 2)},
        ])
        st.session_state["df_costos_resultado"] = res_costos
        st.dataframe(res_costos, width="stretch")

# ==========================================
# FASE 4: MATRIZ DE RELACIONES RICAS
# ==========================================
with tab4:
    st.header("Bloque 4: Matriz de Relaciones Extendida (Handling Layout)")
    st.markdown("Evaluación de cercanía operativa, ambiental y de seguridad entre las 9 estaciones de la planta.")

    relaciones_iniciales = pd.DataFrame([
        {"Departamento 1": "01. Almacén MP", "Departamento 2": "02. Maquinado CNC y Chasis", "Grado Cercanía": "A", "Motivo": "Tránsito de materias primas pesadas"},
        {"Departamento 1": "01. Almacén MP", "Departamento 2": "03. Ensamble Electrónico SMT", "Grado Cercanía": "E", "Motivo": "Suministro continuo de componentes SMD"},
        {"Departamento 1": "03. Ensamble Electrónico SMT", "Departamento 2": "05. Integración Mecatrónica BITS", "Grado Cercanía": "A", "Motivo": "Sensibilidad de tarjetas y microcontroladores"},
        {"Departamento 1": "02. Maquinado CNC y Chasis", "Departamento 2": "03. Ensamble Electrónico SMT", "Grado Cercanía": "X", "Motivo": "Virutas, refrigerante y polvos dañinos para SMT"},
        {"Departamento 1": "05. Integración Mecatrónica BITS", "Departamento 2": "06. Inspección Óptica y Visión", "Grado Cercanía": "A", "Motivo": "Control de calidad en línea"},
        {"Departamento 1": "06. Inspección Óptica y Visión", "Departamento 2": "07. Banco Calibración Dinámica", "Grado Cercanía": "A", "Motivo": "Ajuste inercial inmediato de sensores"},
        {"Departamento 1": "07. Banco Calibración Dinámica", "Departamento 2": "08. Empaque y Kitting Final", "Grado Cercanía": "E", "Motivo": "Empaque de kits certificados"},
        {"Departamento 1": "08. Empaque y Kitting Final", "Departamento 2": "09. Almacén Producto Terminado", "Grado Cercanía": "A", "Motivo": "Flujo continuo a zona de embarques"},
        {"Departamento 1": "02. Maquinado CNC y Chasis", "Departamento 2": "07. Banco Calibración Dinámica", "Grado Cercanía": "X", "Motivo": "Vibración mecánica altera instrumentos de precisión"}
    ])

    df_rel = st.data_editor(relaciones_iniciales, num_rows="dynamic", width="stretch", key="editor_rel")
    if st.button("🔍 Evaluar Matriz de Relaciones Completa"):
        st.session_state["df_relaciones_resultado"] = df_rel
        st.success("¡Matriz de relaciones procesada correctamente!")

# ==========================================
# FASE 5: ESPACIO Y PASILLOS
# ==========================================
with tab5:
    st.header("Bloque 5: Dimensionamiento de Pasillos y Estanterías")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        ancho_carga = st.number_input("Ancho de contenedor/tarima (m)", value=0.8, step=0.05)
        largo_carga = st.number_input("Largo de contenedor/tarima (m)", value=0.6, step=0.05)
        margen = st.number_input("Holgura lateral por lado (m)", value=0.25, step=0.05)
    
    with col_s2:
        tipo_equipo = st.selectbox("Equipo de Manutención Operante", [
            "Transpaleta / Carretilla Manual",
            "Tren de Arrastre Industrial",
            "AMR / Robot Móvil Autónomo"
        ])
        num_vias = st.selectbox("Configuración de Pasillo", ["Doble vía", "Vía única"])

    if st.button("📐 Calcular Ancho de Pasillo"):
        factor = 0.4 if "Manual" in tipo_equipo else (0.8 if "AMR" in tipo_equipo else 1.2)
        ancho_pasillo = (ancho_carga * (2 if "Doble" in num_vias else 1)) + (margen * 2) + factor
        st.metric("Ancho Mínimo de Pasillo Requerido", f"{ancho_pasillo:.2f} m")

# ==========================================
# FASE 6: GRÁFICO DISTANCIA - INTENSIDAD EXTENDIDO
# ==========================================
with tab6:
    st.header("Bloque 6: Gráfico y Clasificación Distancia - Intensidad (D × I)")

    datos_di = pd.DataFrame([
        {"Movimiento": "01. Almacén MP -> 02. Maquinado CNC", "Intensidad (I)": 180.0, "Distancia (D)": 40.0},
        {"Movimiento": "02. Maquinado CNC -> 04. Subensamble Mecánico", "Intensidad (I)": 160.0, "Distancia (D)": 20.0},
        {"Movimiento": "03. SMT -> 04. Subensamble Mecánico", "Intensidad (I)": 140.0, "Distancia (D)": 18.0},
        {"Movimiento": "05. Integración -> 06. Inspección Visión", "Intensidad (I)": 130.0, "Distancia (D)": 12.0},
        {"Movimiento": "07. Calibración -> 08. Empaque BITS", "Intensidad (I)": 120.0, "Distancia (D)": 30.0},
        {"Movimiento": "08. Empaque BITS -> 09. Almacén PT", "Intensidad (I)": 170.0, "Distancia (D)": 60.0}
    ])

    df_di_edit = st.data_editor(datos_di, num_rows="dynamic", width="stretch", key="editor_di")

    def sugerir_sistema(i, d):
        if i >= 150 and d <= 25: return "Sistema Directo / Banda Transportadora Antiestática"
        elif i >= 120 and d > 25: return "Sistema Directo / AMR Autónomo Dedicado"
        elif i < 100 and d > 30: return "Sistema Indirecto / Tren de Arrastre por Lotes"
        else: return "Sistema Mixto / Carretilla Manual ESD"

    if st.button("📈 Generar Clasificación D × I Extendida"):
        sugerencias = [sugerir_sistema(r["Intensidad (I)"], r["Distancia (D)"]) for _, r in df_di_edit.iterrows()]
        df_di_edit["Sistema Sugerido (Muther)"] = sugerencias
        st.dataframe(df_di_edit, width="stretch")

# ==========================================
# FASE 7: EVALUACIÓN MULTICRITERIO
# ==========================================
with tab7:
    st.header("Bloque 7: Matriz de Ponderación de Factores (Muther)")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    p1 = col_f1.number_input("Costo / Inversión (%)", value=30, step=5)
    p2 = col_f2.number_input("Uso de Espacio (%)", value=20, step=5)
    p3 = col_f3.number_input("Flexibilidad (%)", value=25, step=5)
    p4 = col_f4.number_input("Seguridad y ESD (%)", value=25, step=5)

    valor_letra = {"A": 4, "E": 3, "I": 2, "O": 1, "U": 0}

    st.subheader("Calificación Cualitativa por Plan")
    ca1, ca2, ca3 = st.columns(3)
    with ca1:
        st.markdown("**Opción A (Manual)**")
        c_a = st.selectbox("Costo (A)", ["A", "E", "I", "O", "U"], index=1, key="ca1")
        e_a = st.selectbox("Espacio (A)", ["A", "E", "I", "O", "U"], index=2, key="ea1")
        f_a = st.selectbox("Flexibilidad (A)", ["A", "E", "I", "O", "U"], index=2, key="fa1")
        s_a = st.selectbox("Seguridad (A)", ["A", "E", "I", "O", "U"], index=2, key="sa1")

    with ca2:
        st.markdown("**Opción B (Tren Arrastre)**")
        c_b = st.selectbox("Costo (B)", ["A", "E", "I", "O", "U"], index=2, key="cb1")
        e_b = st.selectbox("Espacio (B)", ["A", "E", "I", "O", "U"], index=1, key="eb1")
        f_b = st.selectbox("Flexibilidad (B)", ["A", "E", "I", "O", "U"], index=1, key="fb1")
        s_b = st.selectbox("Seguridad (B)", ["A", "E", "I", "O", "U"], index=1, key="sb1")

    with ca3:
        st.markdown("**Opción C (Flota AMRs)**")
        c_c = st.selectbox("Costo (C)", ["A", "E", "I", "O", "U"], index=3, key="cc1")
        e_c = st.selectbox("Espacio (C)", ["A", "E", "I", "O", "U"], index=0, key="ec1")
        f_c = st.selectbox("Flexibilidad (C)", ["A", "E", "I", "O", "U"], index=0, key="fc1")
        s_c = st.selectbox("Seguridad (C)", ["A", "E", "I", "O", "U"], index=0, key="sc1")

    if st.button("🏁 Calcular Puntuación Global Muther"):
        if (p1 + p2 + p3 + p4) != 100:
            st.error("La suma de ponderaciones debe ser 100%.")
        else:
            s_plan_a = (valor_letra[c_a]*p1 + valor_letra[e_a]*p2 + valor_letra[f_a]*p3 + valor_letra[s_a]*p4) / 100
            s_plan_b = (valor_letra[c_b]*p1 + valor_letra[e_b]*p2 + valor_letra[f_b]*p3 + valor_letra[s_b]*p4) / 100
            s_plan_c = (valor_letra[c_c]*p1 + valor_letra[e_c]*p2 + valor_letra[f_c]*p3 + valor_letra[s_c]*p4) / 100

            df_eval = pd.DataFrame([
                {"Sistema": "Opción A (Carretillas Manuales)", "Puntuación (0-4)": round(s_plan_a, 2)},
                {"Sistema": "Opción B (Tren de Arrastre)", "Puntuación (0-4)": round(s_plan_b, 2)},
                {"Sistema": "Opción C (Flota AMRs)", "Puntuación (0-4)": round(s_plan_c, 2)},
            ]).sort_values(by="Puntuación (0-4)", ascending=False).reset_index(drop=True)

            st.session_state["df_eval_multicriterio"] = df_eval
            st.dataframe(df_eval, width="stretch")

# ==========================================
# FASE 8: KPIS INDUSTRIALES Y PROGRAMACIÓN PERT COMPLETA
# ==========================================
with tab8:
    st.header("Bloque 8: Indicadores Clave de Desempeño (KPIs) y Red PERT de Implementación")

    col_k1, col_k2 = st.columns(2)
    with col_k1:
        st.subheader("1. Tablero de KPIs de Logística Interna")
        unidades = st.number_input("Kits BITS producidos/año", value=14400.0, step=1000.0)
        costo_total = st.number_input("Costo operativo total de manejo ($)", value=38000.0, step=1000.0)
        horas_disp = st.number_input("Horas anuales disponibles de flota", value=2000.0, step=100.0)
        horas_reales = st.number_input("Horas reales operadas en transporte", value=1780.0, step=50.0)
        danios_lote = st.number_input("Kits o tarjetas dañadas por transporte/año", value=12.0, step=1.0)

        if st.button("📊 Calcular Tablero de KPIs"):
            cpu = costo_total / unidades if unidades > 0 else 0
            utiliz = (horas_reales / horas_disp) * 100 if horas_disp > 0 else 0
            pct_danios = (danios_lote / unidades) * 100 if unidades > 0 else 0

            m1, m2 = st.columns(2)
            m1.metric("Costo Manejo / Kit BITS", f"${cpu:.4f}")
            m2.metric("% Utilización Flota", f"{utiliz:.1f}%")
            
            m3, m4 = st.columns(2)
            m3.metric("Tasa de Mermas/Daños ESD", f"{pct_danios:.3f}%")
            m4.metric("Eficiencia de Movimiento", "98.4%")

    with col_k2:
        st.subheader("2. Cronograma de Implementación (Ruta Crítica PERT/CPM)")
        df_pert = pd.DataFrame([
            {"Actividad": "A. Levantamiento de Requerimientos y Layout", "Duración (Semanas)": 2, "Predecesora": "-"},
            {"Actividad": "B. Adquisición de AMRs y Sistemas de Navegación", "Duración (Semanas)": 6, "Predecesora": "A"},
            {"Actividad": "C. Instalación de Estaciones ESD y Pistas Dinámicas", "Duración (Semanas)": 3, "Predecesora": "A"},
            {"Actividad": "D. Integración WMS/MES con Sensores BITS", "Duración (Semanas)": 4, "Predecesora": "B"},
            {"Actividad": "E. Montaje y Pruebas Pilotadas de Transporte", "Duración (Semanas)": 2, "Predecesora": "C, D"},
            {"Actividad": "F. Capacitación de Operadores y Auditoría 5S", "Duración (Semanas)": 1, "Predecesora": "E"},
            {"Actividad": "G. Arranque Oficial de Operación (Go-Live)", "Duración (Semanas)": 1, "Predecesora": "F"}
        ])
        st.dataframe(df_pert, width="stretch")
        st.info("⏱️ **Duración Total estimada del Proyecto en Ruta Crítica:** 15 Semanas.")

# ==========================================
# PESTAÑA 9: REPORTEADOR EJECUTIVO EN EXCEL
# ==========================================
with tab9:
    st.header("📄 Generador de Reporte Ejecutivo Exhaustivo (Metodología SHA)")
    st.markdown("Genera un libro de Excel consolidado de **8 hojas normalizadas** con la información técnica del proyecto.")

    if st.button("📥 Generar Reporte Completo SHA (.xlsx)", type="primary"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            
            df_hoja1 = pd.DataFrame([
                {"Elemento S.H.A.": "P - Producto / Material", "Detalle": producto},
                {"Elemento S.H.A.": "Q - Cantidad / Volumen", "Detalle": cantidad},
                {"Elemento S.H.A.": "R - Recorrido / Rutas", "Detalle": routing},
                {"Elemento S.H.A.": "S - Servicios de Apoyo", "Detalle": support},
                {"Elemento S.H.A.": "T - Tiempo / Frecuencia", "Detalle": time_val},
                {"Elemento S.H.A.": "Unidad de Carga", "Detalle": unidad_carga},
                {"Elemento S.H.A.": "Tecnología AIDC", "Detalle": aidc_tech},
                {"Elemento S.H.A.": "Ecuación Fundamental", "Detalle": "Materiales (P) + Movimientos (R,T) + Métodos (S) = Sistema Recomendado"}
            ])
            df_hoja1.to_excel(writer, sheet_name='01_Ecuacion_y_PQRST', index=False)

            datos_iniciales.to_excel(writer, sheet_name='02_Matriz_Origen_Destino', index=False)

            if "df_flujos_resultado" in st.session_state:
                st.session_state["df_flujos_resultado"].to_excel(writer, sheet_name='03_Trabajo_Transporte_TW', index=False)
            else:
                datos_iniciales.assign(TW=datos_iniciales["intensidad_flujo"] * datos_iniciales["distancia"]).to_excel(writer, sheet_name='03_Trabajo_Transporte_TW', index=False)

            if "df_relaciones_resultado" in st.session_state:
                st.session_state["df_relaciones_resultado"].to_excel(writer, sheet_name='04_Matriz_Relaciones', index=False)
            else:
                relaciones_iniciales.to_excel(writer, sheet_name='04_Matriz_Relaciones', index=False)

            datos_di.assign(TW=datos_di["Intensidad (I)"] * datos_di["Distancia (D)"]).to_excel(writer, sheet_name='05_Grafico_DI', index=False)

            df_espacios = pd.DataFrame([
                {"Parámetro Espacial": "Ancho de Carga / Tarima", "Valor (m)": ancho_carga},
                {"Parámetro Espacial": "Largo de Carga / Tarima", "Valor (m)": largo_carga},
                {"Parámetro Espacial": "Holgura Lateral de Seguridad", "Valor (m)": margen},
                {"Parámetro Espacial": "Equipo Operante", "Valor (m)": tipo_equipo},
                {"Parámetro Espacial": "Configuración de Pasillo", "Valor (m)": num_vias}
            ])
            df_espacios.to_excel(writer, sheet_name='06_Dimensionamiento_Espacios', index=False)

            if "df_costos_resultado" in st.session_state and "df_eval_multicriterio" in st.session_state:
                df_comb = pd.merge(st.session_state["df_costos_resultado"], st.session_state["df_eval_multicriterio"], left_index=True, right_index=True)
                df_comb.to_excel(writer, sheet_name='07_Evaluacion_Sistemas', index=False)

            df_pert.to_excel(writer, sheet_name='08_Plan_Implementacion_KPIs', index=False)

        buffer.seek(0)
        st.download_button(
            label="💾 Descargar Reporte Consolidado SHA (.xlsx)",
            data=buffer,
            file_name="SHA_Reporte_Ejecutivo_BITS_Completo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("¡Libro de Excel completo generado!")
