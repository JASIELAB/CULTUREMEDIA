
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Medios de Cultivo", layout="centered")
st.title("🌱 Control de Medios de Cultivo InVitro")

st.subheader("📋 Registrar nuevo lote")
medio = st.selectbox("Tipo de medio", ["MS", "½MS", "B5"])
hormonas = st.text_input("Hormonas (ej. BAP 1, ANA 0.1)")
volumen = st.number_input("Volumen total (mL)", min_value=100, max_value=5000, step=100)
frascos = st.number_input("Número de frascos", min_value=1, max_value=500, step=1)

if st.button("Registrar lote"):
    codigo = f"{medio}-{hormonas.replace(' ', '')}-{datetime.today().strftime('%d%m%y')}-LT01"
    st.success("✅ Lote registrado exitosamente.")
    st.code(f"Código generado: {codigo}")

st.markdown("---")
st.subheader("📦 Stock simulado")
st.table([
    {"Lote": "MS-BAP1ANA0.1-250625-LT01", "Frascos": 40, "Restantes": 35},
    {"Lote": "½MS-KIN0.5AIA0.05-010725-LT02", "Frascos": 30, "Restantes": 28},
    import streamlit as st

# Mostrar los logotipos
col1, col2 = st.columns([1, 5])

with col1:
    st.image("assets/logo_blackberry.png", width=80)

with col2:
    st.image("assets/logo_planasa.png", use_column_width=True)
])
