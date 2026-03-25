import streamlit as st
import pandas as pd
import qrcode
import os
import json
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Gestión Medios InVitRo", layout="wide")

# --- FUNCIONES DE SEGURIDAD Y CARGA ---
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
    # Datos iniciales basados en tu tabla si el archivo no existe
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

def load_df(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
        for c in cols:
            if c not in df.columns: df[c] = ""
        return df
    return pd.DataFrame(columns=cols)

def save_df(path, df):
    df.to_csv(path, index=False)

inv_cols = ["Código", "Año", "Receta", "Solución", "Equipo", "Semana", "Día", "Preparación", "frascos", "pH_Final", "Fecha"]
inv_df = load_df(INV_FILE, inv_cols)
mov_df = load_df(HIST_FILE, ["Timestamp", "Tipo", "Código", "Cantidad", "Detalles"])

# --- HELPERS GRÁFICOS ---
def make_qr(text):
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf

# --- INTERFAZ PRINCIPAL ---
st.title("🔬 Sistema Control de Medios")

menu = [
    ("Registrar Lote","📋"), ("Consultar Stock","📦"), ("Recetas","📖"), 
    ("Baja Inventario","⚠️"), ("Etiquetas","🖨")
]

if 'choice' not in st.session_state: st.session_state.choice = "Registrar Lote"

c_menu = st.columns(len(menu))
for i, (lbl, icn) in enumerate(menu):
    if c_menu[i].button(f"{icn} {lbl}"):
        st.session_state.choice = lbl

st.divider()

# --- LÓGICA DE NAVEGACIÓN ---

if st.session_state.choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    with st.form("reg_lote"):
        c1, c2, c3 = st.columns(3)
        year = c1.number_input("Año", 2000, 2100, 2026)
        receta = c2.selectbox("Receta", list(st.session_state.recipes_db.keys()))
        prep = c3.number_input("Preparación #", 1, 100, 1)
        
        c4, c5 = st.columns(2)
        frascos = c4.number_input("Cantidad Frascos", 0, 999, 1)
        equipo = c5.selectbox("Equipo", ["Alpha", "Beta","Gamma"])
        
        if st.form_submit_button("Guardar Lote"):
            sem = datetime.today().strftime('%U')
            dia = datetime.today().isoweekday()
            code = f"{str(year)[2:]}{receta[:2]}Z{sem}{dia}-{prep}"
            
            new_data = [code, year, receta, "", equipo, sem, dia, prep, frascos, 5.7, date.today().isoformat()]
            inv_df.loc[len(inv_df)] = new_data
            save_df(INV_FILE, inv_df)
            st.success(f"Lote {code} registrado con éxito.")

elif st.session_state.choice == "Consultar Stock":
    st.header("📦 Stock e Inventario")
    st.dataframe(inv_df, use_container_width=True)
    
    st.subheader("✏️ Edición Rápida")
    sel_lote = st.selectbox("Selecciona lote para editar", [""] + list(inv_df['Código']))
    if sel_lote:
        idx = inv_df[inv_df['Código'] == sel_lote].index[0]
        col1, col2 = st.columns(2)
        # CORRECCIÓN: Mínimo 0 para evitar el error de la imagen
        new_f = col1.number_input("Frascos actuales", 0, 999, value=safe_int(inv_df.at[idx, 'frascos']))
        new_ph = col2.number_input("Ajuste pH Final", 0.0, 14.0, value=safe_float(inv_df.at[idx, 'pH_Final']))
        
        if st.button("Guardar Cambios"):
            inv_df.at[idx, 'frascos'] = new_f
            inv_df.at[idx, 'pH_Final'] = new_ph
            save_df(INV_FILE, inv_df)
            st.success("Inventario actualizado.")
            st.rerun()

elif st.session_state.choice == "Recetas":
    st.header("📖 Editor de Recetas (Sin Excel)")
    
    col_a, col_b = st.columns([2,1])
    rec_name = col_a.selectbox("Editar Receta:", list(st.session_state.recipes_db.keys()))
    new_name = col_b.text_input("Nueva Receta (Nombre):")
    if col_b.button("➕ Crear"):
        if new_name and new_name not in st.session_state.recipes_db:
            st.session_state.recipes_db[new_name] = {"pH": 5.7}
            save_recipes(st.session_state.recipes_db)
            st.rerun()

    st.divider()
    
    # Listado de ingredientes basado en tu tabla
    ingredientes = [
        "WPM", "MS", "KNO3", "NH4NO3", "CaCl2", "Ca(NO3)2-4H2O", "MgSO4 7H2O", "KH2PO4",
        "MnSO4 H2O", "ZnSO4 7H2O", "BAP", "Zeatina", "AIA", "FeNA-EDDHA", "PVP", 
        "L-Glutamina", "Sacarosa", "Agar PTC", "pH"
    ]
    
    rec_data = st.session_state.recipes_db[rec_name]
    
    with st.form("edit_receta"):
        st.subheader(f"Componentes de {rec_name}")
        c = st.columns(3)
        updated_values = {}
        for i, ing in enumerate(ingredientes):
            val_actual = safe_float(rec_data.get(ing, 0.0))
            updated_values[ing] = c[i % 3].number_input(ing, value=val_actual, format="%.3f")
        
        if st.form_submit_button("💾 Guardar Receta"):
            # Guardamos solo valores distintos de 0 (excepto pH)
            st.session_state.recipes_db[rec_name] = {k: v for k, v in updated_values.items() if v != 0 or k == "pH"}
            save_recipes(st.session_state.recipes_db)
            st.success("Cambios guardados en el sistema.")

    st.divider()
    st.subheader("📊 Matriz Comparativa")
    st.dataframe(pd.DataFrame(st.session_state.recipes_db).fillna(0), use_container_width=True)

elif st.session_state.choice == "Baja Inventario":
    st.header("⚠️ Registrar Salida / Baja")
    sel = st.selectbox("Lote", inv_df['Código'])
    cant = st.number_input("Cantidad a descontar", 1, 100)
    motivo = st.selectbox("Motivo", ["Consumo Producción", "Contaminación", "Merma"])
    
    if st.button("Ejecutar Baja"):
        idx = inv_df[inv_df['Código'] == sel].index[0]
        curr = safe_int(inv_df.at[idx, 'frascos'])
        if curr >= cant:
            inv_df.at[idx, 'frascos'] = curr - cant
            save_df(INV_FILE, inv_df)
            st.warning(f"Baja realizada. Stock restante de {sel}: {curr - cant}")
        else:
            st.error("No hay suficiente stock para esa cantidad.")

elif st.session_state.choice == "Etiquetas":
    st.header("🖨 Generador de Etiquetas")
    sel_et = st.selectbox("Lote:", inv_df['Código'])
    if st.button("Generar Vista Previa"):
        row = inv_df[inv_df['Código'] == sel_et].iloc[0]
        st.write(f"**Lote:** {row['Código']} | **Receta:** {row['Receta']} | **Fecha:** {row['Fecha']}")
        qr = make_qr(sel_et)
        st.image(qr, width=200)
