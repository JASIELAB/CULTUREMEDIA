import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date
import os
from PIL import Image, ImageDraw, ImageFont

# --- Configuración de página y estilos ---
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")
PRIMARY_COLOR = "#D32F2F"
ACCENT_COLOR = "#FFFFFF"
BG_COLOR = "#FFEBEE"
TEXT_COLOR = "#000000"
st.markdown(f"""
<style>
    .stApp {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; }}
    div.stButton>button, div.stDownloadButton>button {{ background-color: {PRIMARY_COLOR}; color: {ACCENT_COLOR}; }}
</style>
""", unsafe_allow_html=True)

# --- Rutas de archivos ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

# --- Carga inicial de datos ---
inv_cols = ["Código","Año","Receta","Solución","Semana","Día","Preparación","Frascos","pH_Ajustado","pH_Final","CE_Final","Fecha"]
if os.path.exists(INV_FILE):
    inv_df = pd.read_csv(INV_FILE)
    inv_df = inv_df.reindex(columns=inv_cols)
else:
    inv_df = pd.DataFrame(columns=inv_cols)

sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
if os.path.exists(SOL_FILE):
    sol_df = pd.read_csv(SOL_FILE)
    sol_df = sol_df.reindex(columns=sol_cols)
else:
    sol_df = pd.DataFrame(columns=sol_cols)

# --- Carga de recetas ---
recipes = {}
if os.path.exists(REC_FILE):
    xls = pd.ExcelFile(REC_FILE)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        if df.shape[0] > 9:
            sub = df.iloc[9:, :3].dropna(how='all').copy()
            sub.columns = ["Componente","Fórmula","Concentración"]
            recipes[sheet] = sub

# --- Funciones auxiliares ---
def make_qr(text: str) -> bytes:
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

def make_label(info: list, qr_bytes: bytes, size=(400,130)) -> Image.Image:
    label = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(label)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    y = 10
    for line in info:
        draw.text((10, y), line, fill="black", font=font)
        y += 18
    qr_img = Image.open(BytesIO(qr_bytes)).resize((80, 80))
    label.paste(qr_img, (size[0]-90, 10))
    return label

# --- Menú lateral ---
st.sidebar.title("🧭 Menú")
choice = st.sidebar.radio("Selecciona una sección:", [
    "Registrar Lote",
    "Consultar Stock",
    "Inventario",
    "Historial",
    "Soluciones Stock",
    "Recetas de Medios",
    "Imprimir Etiquetas"
])

# --- Cabecera ---
col1, col2 = st.columns([1,8])
col1.image("logo_blackberry.png", width=60)
col2.markdown("<h1 style='text-align:center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Secciones ---
if choice == "Registrar Lote":
    st.subheader("📝 Registrar Lote")
    año = st.text_input("Año (ej. 2025)")
    receta = st.selectbox("Receta", list(recipes.keys()))
    solucion = st.text_input("Solución stock")
    semana = st.number_input("Semana", min_value=1, max_value=52, step=1)
    dia = st.number_input("Día", min_value=1, max_value=7, step=1)
    prep = st.text_input("Número de preparación")
    frascos = st.number_input("Cantidad de frascos", min_value=1, max_value=500, step=1)
    ph_aj = st.number_input("pH ajustado", step=0.1, format="%.1f")
    ph_fin = st.number_input("pH final", step=0.1, format="%.1f")
    ce = st.number_input("CE final", step=0.01, format="%.2f")
    if st.button("Registrar lote"):
        code = f"{año}{receta}{solucion}{semana}{dia}{prep}"
        fecha = date.today().isoformat()
        row = {"Código":code, "Año":año, "Receta":receta, "Solución":solucion,
               "Semana":semana, "Día":dia, "Preparación":prep, "Frascos":frascos,
               "pH_Ajustado":ph_aj, "pH_Final":ph_fin, "CE_Final":ce, "Fecha":fecha}
        inv_df.loc[len(inv_df)] = row
        inv_df.to_csv(INV_FILE, index=False)
        st.success("Lote registrado.")
        info = [f"Código: {code}", f"Año: {año}", f"Receta: {receta}", f"Frascos: {frascos}",
                f"pH ajustado: {ph_aj}", f"pH final: {ph_fin}", f"CE: {ce}"]
        qr = make_qr(code)
        label = make_label(info, qr)
        st.image(label)
        buf = BytesIO()
        label.save(buf, format="PNG")
        st.download_button("📥 Descargar etiqueta", buf.getvalue(), file_name=f"etiqueta_{code}.png")

elif choice == "Consultar Stock":
    st.subheader("🔍 Consultar Stock")
    st.dataframe(inv_df)

elif choice == "Inventario":
    st.subheader("📋 Inventario Actual")
    st.dataframe(inv_df)

elif choice == "Historial":
    st.subheader("📜 Historial de Lotes")
    st.dataframe(inv_df)

elif choice == "Soluciones Stock":
    st.subheader("🧪 Registro de Soluciones Stock")
    fecha = st.date_input("Fecha", date.today())
    cantidad = st.text_input("Cantidad pesada")
    cod_s = st.text_input("Código solución stock")
    responsable = st.text_input("Responsable")
    regulador = st.text_input("Tipo de regulador de crecimiento")
    obs = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        row = {"Fecha": fecha, "Cantidad": cantidad, "Código_Solución": cod_s,
               "Responsable": responsable, "Regulador": regulador, "Observaciones": obs}
        sol_df.loc[len(sol_df)] = row
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Solución registrada.")
        info = [f"Código: {cod_s}", f"Fecha: {fecha.isoformat()}", f"Cantidad: {cantidad}",
                f"Responsable: {responsable}", f"Regulador: {regulador}"]
        qr2 = make_qr(cod_s)
        label2 = make_label(info, qr2)
        st.image(label2)
        buf2 = BytesIO()
        label2.save(buf2, format="PNG")
        st.download_button("📥 Descargar etiqueta Stock", buf2.getvalue(), file_name=f"etq_stock_{cod_s}.png")

elif choice == "Recetas de Medios":
    st.subheader("📖 Recetas de Medios de Cultivo")
    receta = st.selectbox("Selecciona receta", list(recipes.keys()))
    if receta:
        st.dataframe(recipes[receta])

elif choice == "Imprimir Etiquetas":
    st.subheader("🖨️ Imprimir Etiquetas")
    codes = inv_df["Código"].tolist()
    sel = st.multiselect("Selecciona lotes para imprimir", codes)
    if st.button("Generar PDF etiquetas"):
        st.warning("Función PDF no implementada aún.")

else:
    st.write("Sección no implementada.")

# --- Botón Descarga Inventario y Soluciones ---
st.sidebar.markdown("---")
st.sidebar.download_button("📥 Descargar Inventario Excel", to_excel_bytes(inv_df), file_name="inventario.xlsx")
st.sidebar.download_button("📥 Descargar Soluciones Excel", to_excel_bytes(sol_df), file_name="soluciones.xlsx")
