import streamlit as st

st.set_page_config(page_title="Trazabilidad", layout="wide")

# Encabezado
st.title("🧪 Sistema de Trazabilidad de Medios")

# Mostrar logotipos
col1, col2 = st.columns([1, 5])

with col1:
    st.image("logo_blackberry.png", width=80)

with col2:
    st.image("logo_planasa.png", use_column_width=True)

st.write("Bienvenido al sistema. Aquí podrás gestionar lotes de medios in vitro.")
