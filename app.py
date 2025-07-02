import streamlit as st
from datetime import datetime

# Configuración inicial de la app
st.set_page_config(
    page_title="Medios de Cultivo InVitro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Menú lateral
with st.sidebar:
    st.title("🧭 Menú")
    st.markdown("- Registrar Lote")
    st.markdown("- Consultar Stock")
    st.markdown("- Imprimir Etiquetas")
    st.markdown("- Configuración")

# Cabecera con logotipos
col1, col2, col3 = st.columns([1, 6, 1])

with col1:
    st.image("logo_blackberry.png", width=60)

with col2:
    st.markdown("<h1 style='text-align: center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)

with col3:
    st.image("logo_planasa.png", width=80)

st.markdown("---")

# Formulario de registro
st.subheader("📋 Registrar nuevo lote")
medio = st.selectbox("Tipo de medio", ["MS", "½MS", "B5"])
hormonas = st.text_input("Hormonas (ej. BAP 1, ANA 0.1)")
volumen = st.number_input("Volumen total (mL)", min_value=100, max_value=5000, step=100)

# --- Fin de tu sección actual ---
st.markdown("---")
st.subheader("📦 Stock simulado")
st.table([
    {"Lote": "MS-BAP1ANA0.1-250625-LT01", "Frascos": 40, "Restantes": 35},
    {"Lote": "½MS-KIN0.5AIA0.05-010725-LT02", "Frascos": 30, "Restantes": 28},
])

# 👇 PEGA AQUÍ EL BLOQUE DE RECETAS
import pandas as pd

# Leer Excel y procesar recetas
def extraer_receta(df):
    df_clean = df.iloc[9:, [0, 1, 2]].copy()
    df_clean.columns = ["Componente", "Fórmula", "Concentración"]
    df_clean = df_clean.dropna(subset=["Componente", "Concentración"], how="all")
    df_clean.reset_index(drop=True, inplace=True)
    return df_clean

excel_data = pd.ExcelFile("RECETAS MEDIOS ACTUAL JUNIO251.xlsx")
sheets_content = {sheet: excel_data.parse(sheet) for sheet in excel_data.sheet_names}

recetas = {
    nombre: extraer_receta(sheets_content[nombre])
    for nombre in sheets_content
    if not sheets_content[nombre].empty
}

# Mostrar módulo de recetas
st.markdown("---")
st.subheader("📖 Recetas de Medios de Cultivo")

seleccion = st.selectbox("Selecciona una receta:", list(recetas.keys()))
st.write(f"**Receta para el medio `{seleccion}`:**")
st.dataframe(recetas[seleccion], use_container_width=True)

