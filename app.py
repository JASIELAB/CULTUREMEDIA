import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import qrcode
from PIL import Image

# --- Configuración inicial ---
st.set_page_config(
    page_title="Medios de Cultivo InVitro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Menú lateral ---
with st.sidebar:
    st.title("🧭 Menú")
    st.markdown("- Registrar Lote")
    st.markdown("- Consultar Stock")
    st.markdown("- Recetas de medios")
    st.markdown("- Imprimir Etiquetas")

# --- Cabecera con logotipos ---
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.image("logo_blackberry.png", width=60)
with col2:
    st.markdown("<h1 style='text-align: center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
with col3:
    st.image("logo_planasa.png", width=80)

st.markdown("---")

# --- Formulario de registro ---
st.subheader("📋 Registrar nuevo lote")
medio = st.selectbox("Tipo de medio", ["MS", "½MS", "B5"])
hormonas = st.text_input("Hormonas (ej. BAP 1, ANA 0.1)")
volumen = st.number_input("Volumen total (mL)", min_value=100, max_value=5000, step=100)
frascos = st.number_input("Número de frascos", min_value=1, max_value=500, step=1)

if st.button("Registrar lote"):
    codigo = f"{medio}-{hormonas.replace(' ', '').upper()}-{datetime.today().strftime('%d%m%y')}-LT01"
    st.success("✅ Lote registrado exitosamente.")
    st.code(f"Código generado: {codigo}")

    # Generar QR
    qr_info = f"Lote: {codigo}\nVolumen: {volumen} mL\nFrascos: {frascos}"
    qr = qrcode.make(qr_info)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    st.image(qr, caption="Código QR del lote")

    st.download_button(
        label="⬇️ Descargar QR",
        data=buffer,
        file_name=f"{codigo}_QR.png",
        mime="image/png"
    )

# --- Stock simulado ---
st.markdown("---")
st.subheader("📦 Stock simulado")
st.table([
    {"Lote": "MS-BAP1ANA0.1-250625-LT01", "Frascos": 40, "Restantes": 35},
    {"Lote": "½MS-KIN0.5AIA0.05-010725-LT02", "Frascos": 30, "Restantes": 28},
])

# --- Recetas de Medios desde Excel ---
st.markdown("---")
st.subheader("📖 Recetas de Medios de Cultivo")

# Cargar archivo Excel
excel_file = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"
excel_data = pd.ExcelFile(excel_file)

# Función para limpiar cada hoja
def extraer_receta(df):
    df_clean = df.iloc[9:, [0, 1, 2]].copy()
    df_clean.columns = ["Componente", "Fórmula", "Concentración"]
