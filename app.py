import streamlit as st
import pandas as pd
import qrcode
import os
import json
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Sistema InVitRo", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

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

# --- GESTIÓN DE RECETAS (JSON Local) ---
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
        with open(RECETAS_JSON, "r") as f: return json.load(f)
    return default_recipes

if 'recipes_db' not in st.session_state:
    st.session_state.recipes_db = load_recipes()

# --- CARGA DINÁMICA DE INVENTARIO DESDE LA NUBE ---
try:
    # ttl=0 para que siempre traiga datos frescos al refrescar la página
    inv_df = conn.read(worksheet="Inventario", ttl=0)
    # Asegurar que frascos sea numérico
    inv_df['frascos'] = pd.to_numeric(inv_df['frascos'], errors='coerce').fillna(0).astype(int)
except Exception as e:
    st.error(f"Error conectando a Google Sheets: {e}")
    inv_df = pd.DataFrame(columns=["Código", "Año", "Receta", "Equipo", "Semana", "Día", "Preparación", "frascos", "Fecha_Prep", "pH_Inicial", "pH_Ajustado", "pH_Final", "CE_Inicial", "CE_Final", "Solucion_1", "Solucion_2", "Solucion_3"])

# --- INTERFAZ PRINCIPAL ---
st.title("🧪 Sistema InVitRo: Gestión de Medios")

menu = [
    ("Registrar Lote","📋"), ("Consultar Stock","📦"), ("Incubación","🌡️"), 
    ("Recetas","📖"), ("Baja Inventario","⚠️"), ("Etiquetas","🖨"),
    ("Gestión de Consumibles", "🫙"), ("Pesaje", "⚖️"), ("Planificación", "🗓️")
]

if 'choice' not in st.session_state: st.session_state.choice = "Registrar Lote"

c_menu = st.columns(len(menu))
for i, (lbl, icn) in enumerate(menu):
    if c_menu[i].button(f"{icn} {lbl}"):
        st.session_state.choice = lbl
        st.rerun()

st.divider()

# --- 1. REGISTRAR LOTE ---
if st.session_state.choice == "Registrar Lote":
    st.header("📋 Registrar nuevo lote")
    with st.form("reg_lote"):
        c1, c2, c3 = st.columns(3)
        fecha_prep = c1.date_input("Fecha de Preparación", date.today())
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
        
        if st.form_submit_button("💾 Guardar Lote en la Nube"):
            year = fecha_prep.year
            sem = fecha_prep.strftime('%U')
            dia_sem = fecha_prep.isoweekday()
            code = f"{str(year)[2:]}{receta[:2]}Z{sem}{dia_sem}-{prep_num}"
            
            new_row = pd.DataFrame([{
                "Código": code, "Año": year, "Receta": receta, "Equipo": equipo,
                "Semana": sem, "Día": dia_sem, "Preparación": prep_num,
                "frascos": frascos, "Fecha_Prep": str(fecha_prep),
                "pH_Inicial": ph_ini, "pH_Ajustado": ph_aju, "pH_Final": ph_fin
            }])
            
            df_updated = pd.concat([inv_df, new_row], ignore_index=True)
            conn.update(worksheet="Inventario", data=df_updated)
            st.success(f"✅ Lote {code} guardado en Google Sheets.")
            st.rerun()

# --- 2. CONSULTAR STOCK ---
elif st.session_state.choice == "Consultar Stock":
    st.header("📦 Inventario de Medios")
    if not inv_df.empty:
        st.subheader("📊 Resumen por Receta")
        resumen = inv_df.groupby("Receta").agg(Total_Frascos=("frascos", "sum"), Numero_Lotes=("Código", "count")).reset_index()
        st.dataframe(resumen, hide_index=True, use_container_width=True)
        
        st.subheader("📝 Detalle de Lotes")
        st.dataframe(inv_df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos en la nube.")

# --- 5. BAJA INVENTARIO ---
elif st.session_state.choice == "Baja Inventario":
    st.header("⚠️ Registro de Bajas")
    if not inv_df.empty:
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                sel_b = st.selectbox("Lote a descontar:", inv_df['Código'])
                idx = inv_df[inv_df['Código'] == sel_b].index[0]
                actual = safe_int(inv_df.at[idx, 'frascos'])
                st.info(f"Stock disponible: **{actual}** frascos")
            with col2:
                tipo_baja = st.selectbox("Tipo de baja:", ["Consumo", "Merma"])
                cant_b = st.number_input("Cantidad a retirar:", 1, actual if actual > 0 else 1, 1)

            if st.button("Confirmar Movimiento", use_container_width=True):
                if actual >= cant_b:
                    inv_df.at[idx, 'frascos'] = actual - cant_b
                    conn.update(worksheet="Inventario", data=inv_df)
                    st.success("✅ Baja sincronizada con Google Sheets.")
                    st.rerun()
    else:
        st.info("Inventario vacío.")

# --- 7. GESTIÓN DE CONSUMIBLES ---
elif st.session_state.choice == "Gestión de Consumibles":
    st.header("🫙 Gestión de Consumibles")
    url_powerbi = "https://app.powerbi.com/reportEmbed?reportId=41f6b205-e480-4402-82f3-58eb7346fb52&autoAuth=true&ctid=1d8e7719-b6f7-4b7e-a7b1-9b9975295122"
    
    st.link_button("📂 Abrir Reporte de Stock Externo", url_powerbi, type="primary", use_container_width=True)
    st.divider()
    
    # Vista rápida de stock actual de medios (leído de la Sheet)
    st.subheader("📈 Disponibilidad de Medios (Google Sheets)")
    if not inv_df.empty:
        resumen_medios = inv_df.groupby("Receta")["frascos"].sum().reset_index()
        st.bar_chart(resumen_medios, x="Receta", y="frascos")
        st.table(resumen_medios)

# --- 8. PESAJE ---
elif st.session_state.choice == "Pesaje":
    st.header("⚖️ PESAJE")
    c1, c2 = st.columns(2)
    receta_sel = c1.selectbox("Selecciona la Receta:", list(st.session_state.recipes_db.keys()))
    volumen = c2.number_input("Litros a preparar:", min_value=0.1, value=1.0)

    if receta_sel:
        datos_receta = st.session_state.recipes_db[receta_sel]
        items_plan = []
        for insumo, concentracion in datos_receta.items():
            if insumo != "pH":
                cant = round(concentracion * volumen, 3)
                unid = "g" if insumo in ["Sacarosa", "Agar PTC", "MS", "WPM"] else "mg"
                items_plan.append({"Insumo": insumo, "Dosis": concentracion, "Total": cant, "Unidad": unid})
        st.table(pd.DataFrame(items_plan))
        st.info(f"📌 Ajustar pH a: {datos_receta.get('pH', '5.7')}")
