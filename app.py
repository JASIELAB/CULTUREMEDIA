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

# --- Simulación de inventario (en memoria) ---
inventario = [
    {"Lote": "MS-BAP1ANA0.1-250625-LT01", "Frascos": 40, "Restantes": 35},
    {"Lote": "½MS-KIN0.5AIA0.05-010725-LT02", "Frascos": 30, "Restantes": 28},
]

# --- Secciones ---
if menu == "Registrar Lote":
    st.subheader("📋 Registrar nuevo lote")

    anio = st.text_input("Año (ej. 2025)")
    receta = st.selectbox("Receta", list(recetas.keys()))
    solucion_stock = st.text_input("Solución stock (ej. BAP 1mg/mL)")
    semana = st.text_input("Semana (ej. 27)")
    dia = st.text_input("Día (ej. Lunes)")
    preparacion = st.text_input("Número de preparación (ej. 01)")

    st.write(f"**Receta para `{receta}`:**")
    st.dataframe(recetas[receta], use_container_width=True)

    if st.button("Registrar lote"):
        codigo = f"{anio}-W{semana}-{dia}-R{receta}-P{preparacion}"
        st.success("✅ Lote registrado exitosamente.")
        st.code(f"Código generado: {codigo}")

        qr_info = (
            f"Código: {codigo}\n"
            f"Año: {anio}\nSemana: {semana}\nDía: {dia}\n"
            f"Receta: {receta}\nStock: {solucion_stock}\nPreparación: {preparacion}"
        )
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
    st.table(inventario)

    # Botón para descargar inventario
    df_inventario = pd.DataFrame(inventario)
    st.download_button(
        label="⬇️ Descargar inventario como Excel",
        data=generar_excel(df_inventario),
        file_name="Inventario_medios.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

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
