import streamlit as st
import pandas as pd
import qrcode
import os
import json
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Sistema InVitRo", layout="wide")

def safe_int(val, default=0):
    try: return int(float(val)) if not pd.isna(val) else default
    except: return default

def safe_float(val, default=0.0):
    try: return float(val) if not pd.isna(val) else default
    except: return default

# --- 2. PERSISTENCIA DE DATOS ---
INV_FILE = "inventario_medios.csv"
RECETAS_JSON = "recetas_config.json"

def load_recipes():
    default_recipes = {
        "AR-6": {"WPM": 2.41, "Zeatina": 1.0, "AIA": 0.1, "Sacarosa": 25.0, "Agar PTC": 7.0, "pH": 5.2},
        "SGN 3": {"WPM": 2.46, "KNO3": 500.0, "NH4NO3": 400.0, "Zeatina": 1.0, "Sacarosa": 30.0, "Agar PTC": 6.5, "pH": 5.0},
        "Zr-0": {"MS": 4.4, "PVP": 1.0, "Sacarosa": 30.0, "Agar PTC": 7.0, "pH": 5.7}
    }
    if os.path.exists(RECETAS_JSON):
        with open(RECETAS_JSON, "r") as f: return json.load(f)
    return default_recipes

if 'recipes_db' not in st.session_state:
    st.session_state.recipes_db = load_recipes()

def load_inv():
    if os.path.exists(INV_FILE):
        df = pd.read_csv(INV_FILE, dtype=str)
        df['frascos'] = pd.to_numeric(df['frascos'], errors='coerce').fillna(0).astype(int)
        return df
    return pd.DataFrame(columns=["Código", "Año", "Receta", "Equipo", "Semana", "Día", "Preparación", "frascos", "Fecha_Prep"])

inv_df = load_inv()

# --- 3. MENÚ PRINCIPAL ---
st.title("🧪 Control de Medios InVitRo")

menu_items = [
    ("Registrar Lote","📋"), ("Consultar Stock","📦"), ("Incubación","🌡️"), 
    ("Recetas","📖"), ("Baja Inventario","⚠️"), ("Etiquetas","🖨"),
    ("Gestión de Consumibles", "🛸"), ("Pesaje", "⚖️"), ("Planificación", "🗓️")
]

if 'choice' not in st.session_state:
    st.session_state.choice = "Registrar Lote"

c_menu = st.columns(len(menu_items))
for i, (lbl, icn) in enumerate(menu_items):
    if c_menu[i].button(f"{icn}\n{lbl}"):
        st.session_state.choice = lbl
        st.rerun()

st.divider()

# --- SECCIÓN 1: REGISTRAR ---
if st.session_state.choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    with st.form("reg"):
        c1, c2 = st.columns(2)
        f_prep = c1.date_input("Fecha", date.today())
        receta = c2.selectbox("Receta", list(st.session_state.recipes_db.keys()))
        cant = st.number_input("Frascos", 1, 1000, 100)
        if st.form_submit_button("Guardar"):
            st.success("Lote guardado localmente (Simulación)")

# --- SECCIÓN 2: STOCK ---
elif st.session_state.choice == "Consultar Stock":
    st.header("📦 Inventario de Medios")
    st.dataframe(inv_df, use_container_width=True) #

# --- SECCIÓN 5: BAJA INVENTARIO ---
elif st.session_state.choice == "Baja Inventario":
    st.header("⚠️ Registro de Bajas") #
    if not inv_df.empty:
        lote_sel = st.selectbox("Lote:", inv_df['Código'])
        tipo_b = st.selectbox("Tipo:", ["Consumo", "Merma"]) #
        cant_b = st.number_input("Cantidad:", 1, 1000, 1)
        if st.button("Confirmar Baja"):
            st.success(f"Baja de {cant_b} por {tipo_b} registrada.")

# --- SECCIÓN 7: CONSUMIBLES (POWER BI) ---
elif st.session_state.choice == "Gestión de Consumibles":
    st.header("🛸 Gestión de Consumibles")
    url_pbi = "https://app.powerbi.com/reportEmbed?reportId=41f6b205-e480-4402-82f3-58eb7346fb52&autoAuth=true&ctid=1d8e7719-b" #
    st.link_button("🚀 Abrir Power BI en pestaña nueva", url_pbi, type="primary")
    st.info("Haz clic arriba para ver el stock en tiempo real.")

# --- SECCIÓN 8: PESAJE INDIVIDUAL ---
elif st.session_state.choice == "Pesaje":
    st.header("⚖️ Cálculo de Pesaje")
    rec_p = st.selectbox("Receta para pesar:", list(st.session_state.recipes_db.keys()))
    litros = st.number_input("Litros a preparar:", 0.1, 500.0, 1.0)
    if rec_p:
        f = st.session_state.recipes_db[rec_p]
        res = [{"Insumo": k, "Total": round(v*litros, 3)} for k, v in f.items() if k != "pH"]
        st.table(pd.DataFrame(res))

# --- SECCIÓN 9: PLANIFICACIÓN SEMANAL ---
elif st.session_state.choice == "Planificación":
    st.header("🗓️ Planificación de Producción Semanal")
    
    if 'df_plan_9' not in st.session_state:
        # Datos iniciales basados en tu imagen
        data_p = {
            'Variedad // Destino': ['Madeira', 'Zarzamora 17.55R', 'YOSEMITE', 'SNG3'],
            'RECETA': ['AR-6', 'Zr-0', 'Zr-3', 'SGN 3'],
            'CAMPAÑA': ['PLA MEX ARANDANO', 'PLA MEX MORA', 'PLA MEX MORA', 'PLA MEX ARANDANO'],
            'W11': [10, 4, 4, 0], 'W12': [6, 9, 0, 0], 'W13': [6, 0, 0, 12]
        }
        st.session_state.df_plan_9 = pd.DataFrame(data_p)

    # Matriz editable
    df_ed = st.data_editor(st.session_state.df_plan_9, num_rows="dynamic", use_container_width=True)
    st.session_state.df_plan_9 = df_ed

    # Cálculo de litros (Cargas * 54L)
    semanas = [c for c in df_ed.columns if c.startswith('W')]
    L_CARGA = 54.0
    
    st.subheader("📊 Totales Semanales (Litros)")
    totales = {s: [pd.to_numeric(df_ed[s], errors='coerce').sum() * L_CARGA] for s in semanas}
    df_tot = pd.DataFrame(totales)
    st.dataframe(df_tot.style.background_gradient(cmap='Greens', axis=1), hide_index=True)

    # Cálculo de Insumos por Semana Seleccionada
    st.divider()
    sem_sel = st.selectbox("Calcular insumos para:", semanas)
    insumos_acu = {}
    for _, r in df_ed.iterrows():
        l_fila = (pd.to_numeric(r[sem_sel], errors='coerce') or 0) * L_CARGA
        if l_fila > 0 and r['RECETA'] in st.session_state.recipes_db:
            for ing, dosis in st.session_state.recipes_db[r['RECETA']].items():
                if ing != "pH":
                    insumos_acu[ing] = insumos_acu.get(ing, 0) + (dosis * l_fila)
    
    if insumos_acu:
        st.table(pd.DataFrame([{"Insumo": k, "Cantidad": round(v, 2)} for k, v in insumos_acu.items()]))
