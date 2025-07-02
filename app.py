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
fras
