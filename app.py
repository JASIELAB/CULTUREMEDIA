import streamlit as st

# Configuración general de la app
st.set_page_config(
    page_title="Trazabilidad de Medios",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Menú lateral
with st.sidebar:
    st.title("🧭 Menú")
    st.markdown("- Página principal")
    st.markdown("- Registro de lotes")
    st.markdown("- Etiquetas")
    st.markdown("- Trazabilidad")
    st.markdown("- Configuración")

# Logotipos pequeños en los extremos
col1, col2, col3 = st.columns([1, 6, 1])

with col1:
    st.image("logo_blackberry.png", width=60)

with col2:
    st.markdown("<h1 style='text-align: center;'>🧪 Sistema de Trazabilidad de Medios</h1>", unsafe_allow_html=True)

with col3:
    st.image("logo_planasa.png", width=100)

# Línea divisoria
st.markdown("---")

# Contenido inicial
st.write("Bienvenido al sistema. Aquí podrás registrar, visualizar y gestionar lotes de medios de cultivo in vitro.")
