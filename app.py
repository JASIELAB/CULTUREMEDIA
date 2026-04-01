import streamlit as st
import pandas as pd
import qrcode
import os
import json
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Sistema InVitRo", layout="wide")

# --- FUNCIONES DE SEGURIDAD ---
def safe_int(val, default=0):
    try:
        if pd.isna(val) or str(val).strip() == "": return default
        return int(float(val))
    except: return default

def safe_float(val, default=0.0):
    try:
        if pd.isna(val) or str(val).strip() == "": return default
        return float(val)
    except: return default

# --- GESTIÓN DE RECETAS ---
RECETAS_JSON = "recetas_config.json"

def load_recipes():
    # Base de datos inicial según tabla proporcionada
    default_recipes = {
        "AR-6": {"WPM": 2.41, "Zeatina": 1.0, "AIA": 0.1, "FeNA-EDDHA": 50.0, "Sacarosa": 25.0, "Agar PTC": 7.0, "pH": 5.2},
        "SGN 3": {"WPM": 2.46, "KNO3": 500.0, "NH4NO3": 400.0, "Zeatina": 1.0, "L-Glutamina": 1.178, "Sacarosa": 30.0, "Agar PTC": 6.5, "pH": 5.0},
        "Zr-0": {"MS": 4.4, "PVP": 1.0, "Sacarosa": 30.0, "Agar PTC": 7.0, "pH": 5.7},
        "Zr-1": {"MS": 4.4, "BAP": 0.4, "PVP": 1.0, "Sacarosa": 30.0, "Agar PTC": 7.0, "pH": 5.7},
        "Zr-3": {"MS": 4.4, "BAP": 0.05, "PVP": 1.0, "Sacarosa": 30.0, "Agar PTC": 7.0, "pH": 5.7}
    }
    if os.path.exists(RECETAS_JSON):
        with open(RECETAS_JSON, "r") as f:
            return json.load(f)
    return default_recipes

def save_recipes(data):
    with open(RECETAS_JSON, "w") as f:
        json.dump(data, f, indent=4)

if 'recipes_db' not in st.session_state:
    st.session_state.recipes_db = load_recipes()

# --- PERSISTENCIA DE INVENTARIO ---
INV_FILE = "inventario_medios.csv"
inv_cols = [
    "Código", "Año", "Receta", "Equipo", "Semana", "Día", "Preparación", 
    "frascos", "Fecha_Prep", "pH_Inicial", "pH_Ajustado", "pH_Final", 
    "CE_Inicial", "CE_Final", "Solucion_1", "Solucion_2", "Solucion_3"
]

def load_df(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
        if 'frascos' in df.columns:
            df['frascos'] = pd.to_numeric(df['frascos'], errors='coerce').fillna(0).astype(int)
        for c in cols:
            if c not in df.columns: df[c] = ""
        return df[cols]
    return pd.DataFrame(columns=cols)

def save_df(path, df):
    df.to_csv(path, index=False)

inv_df = load_df(INV_FILE, inv_cols)

# --- INTERFAZ PRINCIPAL ---
st.title("🧪 Control de Medios de Cultivo")

# Asegúrate de que "Gestión de Consumibles" esté en esta lista
menu = [
    ("Registrar Lote","📋"), 
    ("Consultar Stock","📦"), 
    ("Incubación","🌡️"), 
    ("Recetas","📖"), 
    ("Baja Inventario","⚠️"), 
    ("Etiquetas","🖨"),
    ("Gestión de Consumibles", "🫙"),
    ("Pesaje", "⚖️"),
    ("Planificación de Producción Semanal","🗓️")
]

if 'choice' not in st.session_state: 
    st.session_state.choice = "Registrar Lote"

# Generación de botones
c_menu = st.columns(len(menu))
for i, (lbl, icn) in enumerate(menu):
    if c_menu[i].button(f"{icn} {lbl}"):
        st.session_state.choice = lbl
        st.rerun() # Forzamos el refresco al hacer clic

st.divider()

# --- 1. REGISTRAR LOTE ---
if st.session_state.choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    with st.form("reg_lote"):
        c1, c2, c3 = st.columns(3)
        fecha_prep = c1.date_input("Fecha de Preparación", date.today())
        year = fecha_prep.year 
        receta = c2.selectbox("Receta", list(st.session_state.recipes_db.keys()))
        prep_num = c3.number_input("Preparación #", 1, 100, 1)
        
        c4, c5 = st.columns(2)
        frascos = c4.number_input("Cantidad Frascos", 0, 999, 1)
        equipo = c5.selectbox("Equipo", ["Alpha", "Beta", "Gamma"])
        
        st.markdown("#### 🧪 Parámetros Químicos")
        cp1, cp2, cp3 = st.columns(3)
        ph_ini = cp1.number_input("pH Inicial", 0.0, 14.0, 0.0, format="%.2f")
        ph_aju = cp2.number_input("pH Ajustado", 0.0, 14.0, 0.0, format="%.2f")
        ph_fin = cp3.number_input("pH Final", 0.0, 14.0, 5.7, format="%.2f")
        
        ce1, ce2 = st.columns(2)
        ce_ini = ce1.number_input("CE Inicial (mS/cm)", 0.0, 20.0, 0.0, format="%.2f")
        ce_fin = ce2.number_input("CE Final (mS/cm)", 0.0, 20.0, 0.0, format="%.2f")
        
        st.markdown("#### 🧬 Soluciones Madre")
        cs1, cs2, cs3 = st.columns(3)
        sol_1 = cs1.text_input("Solución Madre 1 (#)")
        sol_2 = cs2.text_input("Solución Madre 2 (#)")
        sol_3 = cs3.text_input("Solución Madre 3 (#)")
        
        if st.form_submit_button("💾 Guardar Lote"):
            sem = fecha_prep.strftime('%U')
            dia_sem = fecha_prep.isoweekday()
            code = f"{str(year)[2:]}{receta[:2]}Z{sem}{dia_sem}-{prep_num}"
            new_row = [code, year, receta, equipo, sem, dia_sem, prep_num, frascos, fecha_prep.isoformat(), ph_ini, ph_aju, ph_fin, ce_ini, ce_fin, sol_1, sol_2, sol_3]
            inv_df.loc[len(inv_df)] = new_row
            save_df(INV_FILE, inv_df)
            st.success(f"✅ Lote {code} registrado correctamente.")

# --- 2. CONSULTAR STOCK ---
elif st.session_state.choice == "Consultar Stock":
    st.header("📦 Inventario de Medios")
    if not inv_df.empty:
        st.subheader("📊 Resumen de Stock por Receta")
        resumen = inv_df.groupby("Receta").agg(Total_Frascos=("frascos", "sum"), Numero_Lotes=("Código", "count")).reset_index()
        st.dataframe(resumen, hide_index=True, use_container_width=True)
        
        st.divider()
        st.subheader("📝 Detalle de Lotes")
        st.dataframe(inv_df, use_container_width=True)
        
        st.subheader("✏️ Edición de Lote")
        sel_lote = st.selectbox("Selecciona lote para editar", [""] + list(inv_df['Código']))
        if sel_lote:
            idx = inv_df[inv_df['Código'] == sel_lote].index[0]
            v_frascos = st.number_input("Cantidad de Frascos", 0, 999, value=safe_int(inv_df.at[idx, 'frascos']))
            if st.button("Actualizar Lote"):
                inv_df.at[idx, 'frascos'] = v_frascos
                save_df(INV_FILE, inv_df)
                st.success("Cambios guardados.")
                st.rerun()
    else:
        st.info("No hay datos en el inventario.")

# --- 3. INCUBACIÓN ---
elif st.session_state.choice == "Incubación":
    st.header("🌡️ Monitoreo de Incubación")
    if not inv_df.empty:
        temp_df = inv_df.copy()
        temp_df['Fecha_Prep'] = pd.to_datetime(temp_df['Fecha_Prep'])
        temp_df['Días'] = (pd.Timestamp(date.today()) - temp_df['Fecha_Prep']).dt.days
        
        def color_incubacion(row):
            d = row['Días']
            if d < 7: color = 'background-color: #ffff99' # Amarillo
            elif 7 <= d <= 28: color = 'background-color: #c2f0c2' # Verde
            else: color = 'background-color: #ff9999' # Rojo
            return [color] * len(row)

        st.dataframe(temp_df[['Código', 'Receta', 'Fecha_Prep', 'Días', 'frascos']].style.apply(color_incubacion, axis=1), use_container_width=True)
    else:
        st.info("No hay lotes registrados.")

# --- 4. RECETAS ---
elif st.session_state.choice == "Recetas":
    st.header("📖 Editor de Recetas")
    rec_name = st.selectbox("Seleccionar Receta:", list(st.session_state.recipes_db.keys()))
    ingredientes = ["WPM", "MS", "KNO3", "NH4NO3", "CaCl2", "Ca(NO3)2-4H2O", "MgSO4 7H2O", "KH2PO4", "MnSO4 H2O", "ZnSO4 7H2O", "BAP", "Zeatina", "AIA", "FeNA-EDDHA", "PVP", "L-Glutamina", "Sacarosa", "Agar PTC", "pH"]
    
    with st.form("edit_rec_form"):
        c = st.columns(3)
        updates = {}
        for i, ing in enumerate(ingredientes):
            val = safe_float(st.session_state.recipes_db[rec_name].get(ing, 0.0))
            updates[ing] = c[i % 3].number_input(ing, value=val, format="%.3f")
        if st.form_submit_button("💾 Guardar Receta"):
            st.session_state.recipes_db[rec_name] = {k: v for k, v in updates.items() if v != 0 or k == "pH"}
            save_recipes(st.session_state.recipes_db)
            st.success("Receta actualizada.")

# --- 5. BAJA INVENTARIO ---

elif st.session_state.choice == "Baja Inventario":
    st.header("⚠️ Registro de Bajas")
    
    if not inv_df.empty:
        # Contenedor para organizar mejor el formulario
        with st.container(border=True):
            col1, col2 = st.columns(2)
            
            with col1:
                sel_b = st.selectbox("Lote a descontar:", inv_df['Código'], help="Selecciona el código del lote")
                
                # Obtener stock actual para validación visual
                idx = inv_df[inv_df['Código'] == sel_b].index[0]
                actual = safe_int(inv_df.at[idx, 'frascos'])
                st.info(f"Stock disponible: **{actual}** frascos")

            with col2:
                # Nuevo: Selección de tipo de baja
                tipo_baja = st.selectbox("Tipo de baja:", ["Consumo", "Merma"], 
                                         help="Consumo: uso regular en lab. Merma: pérdida por contaminación o error.")
                
                cant_b = st.number_input("Cantidad a retirar:", 1, actual if actual > 0 else 1, 1)

            # Opcional: Motivo o comentarios
            comentario = st.text_input("Comentario o motivo (opcional):")

            if st.button("Confirmar Movimiento", use_container_width=True):
                if actual >= cant_b:
                    # Actualizar el DataFrame
                    inv_df.at[idx, 'frascos'] = actual - cant_b
                    save_df(INV_FILE, inv_df)
                    
                    # Mensaje de éxito detallado
                    st.success(f"✅ Baja aplicada: {cant_b} frascos retirados por **{tipo_baja}** del lote {sel_b}.")
                    
                    # Aquí podrías opcionalmente guardar esto en un archivo 'historial_bajas.csv' 
                    # si deseas llevar una estadística de consumo vs merma.
                    
                    st.rerun()
                else:
                    st.error("❌ Stock insuficiente para realizar esta operación.")
    else:
        st.info("No hay lotes disponibles en el inventario para dar de baja.")

# --- 6. ETIQUETAS (2.5cm x 1cm) ---
elif st.session_state.choice == "Etiquetas":
    st.header("🖨 Generador de Etiquetas")
    if not inv_df.empty:
        sel_e = st.selectbox("Lote para generar QR:", inv_df['Código'])
        lote_info = inv_df[inv_df['Código'] == sel_e].iloc[0]
        
        if st.button("Generar Etiqueta"):
            # Medidas 2.5cm x 1cm (300 DPI aprox)
            width, height = 413, 236
            img = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            
            qr = qrcode.QRCode(box_size=4, border=1)
            qr.add_data(sel_e)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").resize((180, 180))
            img.paste(qr_img, (10, 28))
            
            try:
                f_bold = ImageFont.truetype("arialbd.ttf", 22)
                f_reg = ImageFont.truetype("arial.ttf", 16)
            except:
                f_bold = ImageFont.load_default()
                f_reg = ImageFont.load_default()
            
            tx = 200
            draw.text((tx, 30), "RECETA:", fill="black", font=f_reg)
            draw.text((tx, 52), lote_info['Receta'], fill="black", font=f_bold)
            draw.text((tx, 90), "FECHA:", fill="black", font=f_reg)
            draw.text((tx, 112), lote_info['Fecha_Prep'], fill="black", font=f_bold)
            draw.text((tx, 150), "LOTE:", fill="black", font=f_reg)
            draw.text((tx, 172), sel_e, fill="black", font=f_bold)

            st.image(img, caption="Vista previa (2.5x2 cm)")
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.download_button("📥 Descargar Etiqueta", buf.getvalue(), f"QR_{sel_e}.png", "image/png")

# --- 7. GESTIÓN DE CONSUMIBLES ---
elif st.session_state.choice == "Gestión de Consumibles":
    st.header("🫙 Gestión de Consumibles")
    
    # URL de tu reporte (la de tu imagen)
    url_powerbi = "https://app.powerbi.com/reportEmbed?reportId=41f6b205-e480-4402-82f3-58eb7346fb52&autoAuth=true&ctid=1d8e7719-b6f7-4b7e-a7b1-9b9975295122"
    
    with st.container(border=True):
        st.subheader("📊 Inventario Externo (Power BI)")
        st.write("Haz clic en el botón de abajo para abrir el reporte de stock de insumos en una pestaña nueva.")
        
        # Botón principal resaltado
        st.link_button("📂 Abrir Reporte de Stock", url_powerbi, type="primary", use_container_width=True)
        
    st.divider()
    
# --- 8. PESAJE ---
elif st.session_state.choice == "Pesaje":
    st.header("⚖️ PESAJE")
    st.write("Calcula los insumos necesarios según el volumen de producción.")

    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            receta_sel = st.selectbox("Selecciona la Receta:", list(st.session_state.recipes_db.keys()))
        with c2:
            volumen = st.number_input("Litros a preparar:", min_value=0.1, value=1.0, step=0.5)

    if receta_sel:
        st.subheader(f"🧪 Formulación para {volumen} L de {receta_sel}")
        
        # Obtener los datos de la receta seleccionada
        datos_receta = st.session_state.recipes_db[receta_sel]
        
        # Crear tabla de cálculos
        items_plan = []
        for insumo, concentracion in datos_receta.items():
            if insumo != "pH": # El pH no se multiplica
                cantidad_total = round(concentracion * volumen, 3)
                # Determinar unidad (puedes ajustar esto según tu unidad base)
                unidad = "g" if insumo in ["Sacarosa", "Agar PTC", "MS", "WPM"] else "mg"
                items_plan.append({"Insumo": insumo, "Dosis unitaria": concentracion, "Total a pesar": cantidad_total, "Unidad": unidad})
        
        df_plan = pd.DataFrame(items_plan)
        
        if not df_plan.empty:
            st.table(df_plan)
            
            # Resumen de pH
            st.info(f"📌 **Recordatorio:** Ajustar pH final a **{datos_receta.get('pH', 'No definido')}**")
            
            # Botón para exportar planificación
            csv = df_plan.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Descargar Plan de Pesaje (CSV)",
                csv,
                f"Plan_{receta_sel}_{date.today()}.csv",
                "text/csv",
                key='download-csv'
            )
        else:
            st.warning("Esta receta no tiene insumos registrados.")
            
# --- 9. PLANIFICACIÓN SEMANAL DE CARGAS ---
elif st.session_state.choice == "Planificación":
    st.header("🗓️ Planificación de Producción Semanal")
    st.write("Gestión de cargas de preparadora por variedad y campaña (Factor: 54L/Carga).")

    # Inicialización del DataFrame en el estado de la sesión para que no se borre al editar
    if 'df_semanal_9' not in st.session_state:
        # Datos basados en tu imagen de Planasa
        data_plan = {
            'Variedad // Destino': [
                'Madeira', 'Zarzamora 17.55R', 'YOSEMITE', 'SNG3 (1545 & 1542)', 
                'RUBUS Establecimiento', 'Fresa Multiplicacion', 'ZARZAMORA I+D'
            ],
            'RECETA': ['AR-6', 'Zr-0', 'Zr-3', 'SGN 3', 'Zr-0', 'Zr-1', 'Zr-3'],
            'CAMPAÑA': [
                'PLA MEX ARANDANO LAB T09', 'PLA MEX MORA LAB T00', 'PLA MEX MORA LAB T00', 
                'PLA MEX ARANDANO LAB T09', 'I+D / ROOTBLOK', 'I+D FRESA', 'I+D MORA'
            ],
            'W9': [11, 0, 2, 3, 0, 0, 0], 'W10': [10, 0, 5, 2, 0, 0, 0],
            'W11': [10, 4, 4, 0, 0, 0, 0], 'W12': [6, 9, 0, 0, 0, 0, 0],
            'W13': [6, 0, 0, 12, 1, 0, 1], 'W14': [8, 0, 0, 2, 0, 2, 0],
            'W15': [14, 0, 0, 3, 0, 0, 0], 'W16': [14, 0, 0, 6, 0, 0, 0],
            'W17': [16, 0, 0, 4, 0, 0, 0], 'W18': [0, 0, 0, 0, 0, 0, 0],
            'W19': [0, 0, 0, 0, 0, 0, 0], 'W20': [0, 0, 0, 0, 0, 0, 0]
        }
        st.session_state.df_semanal_9 = pd.DataFrame(data_plan)

    # Definición de semanas
    cols_semanas = [f'W{i}' for i in range(9, 21)]
    LITROS_POR_CARGA = 54.0

    # --- TABLA EDITABLE ---
    st.subheader("📝 Matriz de Cargas Semanales")
    # El editor de datos permite modificar, añadir y borrar filas como en Excel
    df_editado_9 = st.data_editor(
        st.session_state.df_semanal_9,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_seccion_9"
    )
    
    # Guardamos los cambios para que persistan
    st.session_state.df_semanal_9 = df_editado_9

    # --- CÁLCULO DE TOTALES (Fila de Litros) ---
    st.divider()
    st.subheader("📊 Resumen de Volumen Total")
    
    # Calculamos la suma de cargas por columna y multiplicamos por 54L
    totales_litros = []
    for sem in cols_semanas:
        # Aseguramos que los datos sean números para sumar
        cargas_num = pd.to_numeric(df_editado_9[sem], errors='coerce').fillna(0)
        totales_litros.append(cargas_num.sum() * LITROS_POR_CARGA)

    # Crear una tabla pequeña para los totales de litros
    df_totales = pd.DataFrame([totales_litros], columns=cols_semanas)
    df_totales.insert(0, "Concepto", "TOTAL LITROS SEMANA")
    
    # Aplicar un estilo para resaltar la fila de totales (color verde similar a tu imagen)
    st.dataframe(df_totales.style.format(precision=1).background_gradient(cmap='Greens', axis=1), 
                 hide_index=True, use_container_width=True)

    # --- CÁLCULO DE INSUMOS AUTOMÁTICO ---
    st.divider()
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("🧪 Requerimiento de Insumos")
        semana_target = st.selectbox("Ver insumos para la semana:", cols_semanas)
        
    # Lógica para cruzar con la base de datos de recetas (st.session_state.recipes_db)
    dict_insumos_semana = {}
    
    for _, fila in df_editado_9.iterrows():
        nombre_receta = fila['RECETA']
        cargas_plan = pd.to_numeric(fila[semana_target], errors='coerce') or 0
        litros_totales_fila = cargas_plan * LITROS_POR_CARGA
        
        # Si hay litros y la receta existe en tu base de datos de la Sección 4
        if litros_totales_fila > 0 and nombre_receta in st.session_state.recipes_db:
            receta_info = st.session_state.recipes_db[nombre_receta]
            for ingrediente, dosis in receta_info.items():
                if ingrediente != "pH":
                    total_mg_g = dosis * litros_totales_fila
                    dict_insumos_semana[ingrediente] = dict_insumos_semana.get(ingrediente, 0) + total_mg_g

    with c2:
        if dict_insumos_semana:
            # Convertir a tabla para mostrar
            resumen_final = []
            for ing, cant in dict_insumos_semana.items():
                unidad = "g" if ing in ["Sacarosa", "Agar PTC", "MS", "WPM"] else "mg"
                resumen_final.append({"Insumo": ing, "Cantidad": round(cant, 3), "Unidad": unidad})
            
            st.table(pd.DataFrame(resumen_final))
        else:
            st.info(f"No hay cargas planificadas o recetas validas para la {semana_target}.")
