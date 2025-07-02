import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import qrcode
from PIL import Image

# --- Configuración general ---
st.set_page_config(
    page_title="Medios de Cultivo InVitro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Menú lateral ---
with st.sidebar:
    st.title("🗭 Menú")
    menu = st.radio("Selecciona una sección:", [
        "Registrar Lote",
        "Consultar Stock",
        "Recetas de medios"
    ])

# --- Cabecera con logotipos ---
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.image("logo_blackberry.png", width=60)
with col2:
    st.markdown("<h1 style='text-align: center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
with col3:
    st.empty()  # logo de planasa eliminado

st.markdown("---")

# --- Funciones ---
def generar_qr(texto):
    qr = qrcode.make(texto)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def extraer_receta(df):
    df_clean = df.iloc[9:, [0, 1, 2]].copy()
    df_clean.columns = ["Componente", "Fórmula", "Concentración"]
    df_clean = df_clean.dropna(subset=["Componente", "Concentración"], how="all")
    df_clean.reset_index(drop=True, inplace=True)
    return df_clean

def generar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Receta")
    output.seek(0)
    return output

# --- Recetas desde Excel (carga anticipada) ---
excel_file = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"
excel_data = pd.ExcelFile(excel_file)
recetas = {
    hoja: extraer_receta(excel_data.parse(hoja))
    for hoja in excel_data.sheet_names
    if not excel_data.parse(hoja).empty
}

# --- Secciones ---
if menu == "Registrar Lote":
    st.subheader("📋 Registrar nuevo lote")
    medio = st.selectbox("Tipo de medio", list(recetas.keys()))
    st.write(f"**Receta para el medio `{medio}`:**")
    st.dataframe(recetas[medio], use_container_width=True)

    hormonas = st.text_input("Hormonas (ej. BAP 1, ANA 0.1)")
    volumen = st.number_input("Volumen total (mL)", min_value=100, max_value=5000, step=100)
    frascos = st.number_input("Número de frascos", min_value=1, max_value=500, step=1)

    if st.button("Registrar lote"):
        codigo = f"{medio}-{hormonas.replace(' ', '').upper()}-{datetime.today().strftime('%d%m%y')}-LT01"
        st.success("✅ Lote registrado exitosamente.")
        st.code(f"Código generado: {codigo}")

        qr_info = f"Lote: {codigo}\nMedio: {medio}\nHormonas: {hormonas}\nVolumen: {volumen} mL\nFrascos: {frascos}"
        buffer = generar_qr(qr_info)

        st.image(buffer, caption="Código QR del lote")
        st.download_button(
            label="⬇️ Descargar QR",
            data=buffer,
            file_name=f"{codigo}_QR.png",
            mime="image/png"
        )

elif menu == "Consultar Stock":
    st.subheader("📦 Stock simulado")
    st.table([
        {"Lote": "MS-BAP1ANA0.1-250625-LT01", "Frascos": 40, "Restantes": 35},
        {"Lote": "½MS-KIN0.5AIA0.05-010725-LT02", "Frascos": 30, "Restantes": 28},
    ])

elif menu == "Recetas de medios":
    st.subheader("📖 Consulta de recetas")
    seleccion = st.selectbox("Selecciona una receta:", list(recetas.keys()), key="receta_selector")
    st.write(f"**Receta para el medio `{seleccion}`:**")
    st.dataframe(recetas[seleccion], use_container_width=True)

    st.download_button(
        label="⬇️ Descargar receta como Excel",
        data=generar_excel(recetas[seleccion]),
        file_name=f"Receta_{seleccion}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
