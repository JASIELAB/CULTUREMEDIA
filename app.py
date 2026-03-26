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

# --- GESTIÓN DE RECETAS (JSON PERSISTENTE) ---
RECETAS_JSON = "recetas_config.json"

def load_recipes():
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
HIST_FILE = "movimientos.csv"

# Definición de columnas completa (17 campos)
inv_cols = [
    "Código", "Año", "Receta", "Equipo", "Semana", "Día", "Preparación", 
    "frascos", "Fecha_Prep", "pH_Inicial", "pH_Ajustado", "pH_Final", 
    "CE_Inicial", "CE_Final", "Solucion_1", "Solucion_2", "Solucion_3"
]

def load_df(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
        for c in cols:
            if c not in df.columns: df[c] = ""
        return df[cols]
    return pd.DataFrame(columns=cols)

def save_df(path, df):
    df.to_csv(path, index=False)

inv_df = load_df(INV_FILE, inv_cols)
mov_df = load_df(HIST_FILE, ["Timestamp", "Tipo", "Código", "Cantidad", "Detalles"])

# --- INTERFAZ PRINCIPAL ---
st.title("🧪 Control de Medios InVitRo")

menu = [
    ("Registrar Lote","📋"), ("Consultar Stock","📦"), 
    ("Recetas","📖"), ("Baja Inventario","⚠️"), ("Etiquetas","🖨")
]

if 'choice' not in st.session_state: st.session_state.choice = "Registrar Lote"

c_menu = st.columns(len(menu))
for i, (lbl, icn) in enumerate(menu):
    if c_menu[i].button(f"{icn} {lbl}"):
        st.session_state.choice = lbl

st.divider()

# --- 1. REGISTRAR LOTE ---
if st.session_state.choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    with st.form("reg_lote"):
        # Fila 1: Tiempos y Receta
        c1, c2, c3 = st.columns(3)
        fecha_prep = c1.date_input("Fecha de Preparación", date.today())
        year = fecha_prep.year 
        receta = c2.selectbox("Receta", list(st.session_state.recipes_db.keys()))
        prep_num = c3.number_input("Preparación #", 1, 100, 1)
        
        # Fila 2: Logística
        c4, c5 = st.columns(2)
        frascos = c4.number_input("Cantidad Frascos", 0, 999, 1)
        equipo = c5.selectbox("Equipo", ["Preparadora Alpha", "Preparadora Beta"])
        
        st.markdown("#### 🧪 Parámetros Químicos")
        # Fila 3: pH
        cp1, cp2, cp3 = st.columns(3)
        ph_ini = cp1.number_input("pH Inicial", 0.0, 14.0, 0.0, format="%.2f")
        ph_aju = cp2.number_input("pH Ajustado", 0.0, 14.0, 0.0, format="%.2f")
        ph_fin = cp3.number_input("pH Final", 0.0, 14.0, 5.7, format="%.2f")
        
        # Fila 4: CE
        ce1, ce2 = st.columns(2)
        ce_ini = ce1.number_input("CE Inicial (mS/cm)", 0.0, 20.0, 0.0, format="%.2f")
        ce_fin = ce2.number_input("CE Final (mS/cm)", 0.0, 20.0, 0.0, format="%.2f")
        
        st.markdown("#### 🧬 Soluciones Madre")
        # Fila 5: Soluciones
        cs1, cs2, cs3 = st.columns(3)
        sol_1 = cs1.text_input("Solución Madre 1 (#)")
        sol_2 = cs2.text_input("Solución Madre 2 (#)")
        sol_3 = cs3.text_input("Solución Madre 3 (#)")
        
        if st.form_submit_button("💾 Guardar Lote"):
            sem = fecha_prep.strftime('%U')
            dia_sem = fecha_prep.isoweekday()
            # Generación automática de código
            code = f"{str(year)[2:]}{receta[:2]}Z{sem}{dia_sem}-{prep_num}"
            
            new_row = [
                code, year, receta, equipo, sem, dia_sem, prep_num, frascos, 
                fecha_prep.isoformat(), ph_ini, ph_aju, ph_fin, 
                ce_ini, ce_fin, sol_1, sol_2, sol_3
            ]
            
            inv_df.loc[len(inv_df)] = new_row
            save_df(INV_FILE, inv_df)
            st.success(f"✅ Lote {code} registrado correctamente.")

# --- 2. CONSULTAR STOCK (CON EDICIÓN CORREGIDA) ---
elif st.session_state.choice == "Consultar Stock":
    st.header("📦 Inventario de Medios")
    st.dataframe(inv_df, use_container_width=True)
    
    st.subheader("✏️ Editar Parámetros de Lote")
    sel_lote = st.selectbox("Selecciona lote para modificar", [""] + list(inv_df['Código']))
    
    if sel_lote:
        idx = inv_df[inv_df['Código'] == sel_lote].index[0]
        with st.expander("Panel de Edición", expanded=True):
            e_col1, e_col2, e_col3 = st.columns(3)
            # CORRECCIÓN DE ERROR: Mínimo 0 para frascos
            v_frascos = e_col1.number_input("Frascos", 0, 999, value=safe_int(inv_df.at[idx, 'frascos']))
            v_ph_f = e_col2.number_input("pH Final", 0.0, 14.0, value=safe_float(inv_df.at[idx, 'pH_Final']))
            v_ce_f = e_col3.number_input("CE Final", 0.0, 20.0, value=safe_float(inv_df.at[idx, 'CE_Final']))
            
            if st.button("Actualizar Lote"):
                inv_df.at[idx, 'frascos'] = v_frascos
                inv_df.at[idx, 'pH_Final'] = v_ph_f
                inv_df.at[idx, 'CE_Final'] = v_ce_f
                save_df(INV_FILE, inv_df)
                st.success("Cambios guardados.")
                st.rerun()

# --- 3. RECETAS ---
elif st.session_state.choice == "Recetas":
    st.header("📖 Editor de Recetas") # Sin la leyenda "Sin Excel"
    
    col_a, col_b = st.columns([2,1])
    rec_name = col_a.selectbox("Seleccionar Receta:", list(st.session_state.recipes_db.keys()))
    new_rec_name = col_b.text_input("Nombre Nueva Receta:")
    if col_b.button("➕ Crear Nueva"):
        if new_rec_name and new_rec_name not in st.session_state.recipes_db:
            st.session_state.recipes_db[new_rec_name] = {"pH": 5.7}
            save_recipes(st.session_state.recipes_db)
            st.rerun()

    st.divider()
    
    ingredientes = [
        "WPM", "MS", "KNO3", "NH4NO3", "CaCl2", "Ca(NO3)2-4H2O", "MgSO4 7H2O", "KH2PO4",
        "MnSO4 H2O", "ZnSO4 7H2O", "BAP", "Zeatina", "AIA", "FeNA-EDDHA", "PVP", 
        "L-Glutamina", "Sacarosa", "Agar PTC", "pH"
    ]
    
    with st.form("edit_receta_form"):
        st.subheader(f"Ingredientes: {rec_name}")
        c = st.columns(3)
        updated_vals = {}
        curr_data = st.session_state.recipes_db[rec_name]
        
        for i, ing in enumerate(ingredientes):
            val = safe_float(curr_data.get(ing, 0.0))
            updated_vals[ing] = c[i % 3].number_input(ing, value=val, format="%.3f")
        
        if st.form_submit_button("💾 Guardar Cambios en Receta"):
            st.session_state.recipes_db[rec_name] = {k: v for k, v in updated_vals.items() if v != 0 or k == "pH"}
            save_recipes(st.session_state.recipes_db)
            st.success("Receta actualizada.")

# --- 4. BAJA INVENTARIO ---
elif st.session_state.choice == "Baja Inventario":
    st.header("⚠️ Salida de Inventario")
    if not inv_df.empty:
        sel_baja = st.selectbox("Lote a descontar:", inv_df['Código'])
        cant_baja = st.number_input("Cantidad a retirar:", 1, 500)
        
        if st.button("Confirmar Baja"):
            idx = inv_df[inv_df['Código'] == sel_baja].index[0]
            stock_actual = safe_int(inv_df.at[idx, 'frascos'])
            if stock_actual >= cant_baja:
                inv_df.at[idx, 'frascos'] = stock_actual - cant_baja
                save_df(INV_FILE, inv_df)
                st.warning(f"Baja aplicada. Stock restante de {sel_baja}: {stock_actual - cant_baja}")
            else:
                st.error("Error: No hay suficiente stock.")
    else:
        st.info("No hay lotes registrados.")

# --- 5. ETIQUETAS ---
elif st.session_state.choice == "Etiquetas":
    st.header("🖨 Impresión")
    if not inv_df.empty:
        sel_et = st.selectbox("Lote para etiqueta:", inv_df['Código'])
        if st.button("Generar QR"):
            img_qr = qrcode.make(sel_et)
            st.image(img_qr.get_image(), width=200)
            st.write(f"Código: {sel_et}")
    else:
        st.info("No hay lotes registrados.")
