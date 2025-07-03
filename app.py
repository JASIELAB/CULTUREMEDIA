import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date
import os
from PIL import Image, ImageDraw, ImageFont

# --- Configuración de página y estilos ---
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")
PRIMARY_COLOR = "#007ACC"
ACCENT_COLOR = "#2ECC71"
BG_COLOR = "#F5F9FC"
TEXT_COLOR = "#1C2833"
st.markdown(f"""
<style>
    .stApp {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; }}
    div.stButton>button {{ background-color: {PRIMARY_COLOR}; color: white; }}
    div.stDownloadButton>button {{ background-color: {ACCENT_COLOR}; color: white; }}
</style>
""", unsafe_allow_html=True)

# --- Archivos ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

# --- Inicializar o cargar DataFrames ---
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

# --- Cargar recetas ---
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

def make_label(info: list, qr_bytes: bytes) -> bytes:
    # Crear imagen de etiqueta (300x150 px)
    label = Image.new("RGB", (300, 150), "white")
    draw = ImageDraw.Draw(label)
    font = ImageFont.load_default()
    y = 10
    for line in info:
        draw.text((10, y), line, fill="black", font=font)
        y += 18
    qr_img = Image.open(BytesIO(qr_bytes)).resize((80, 80))
    label.paste(qr_img, (300 - 90, 10))
    buf = BytesIO()
    label.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return buf.getvalue()

# --- Sidebar ---
with st.sidebar:
    st.title("🗭 Menú")
    choice = st.radio("Selecciona sección:", [
        "Registrar Lote",
        "Consultar Stock",
        "Inventario",
        "Historial",
        "Soluciones Stock",
        "Recetas",
        "Bajas Inventario"
    ])

# --- Encabezado ---
col1, col2 = st.columns([1, 8])
col1.image("logo_blackberry.png", width=60)
col2.markdown("<h1 style='text-align:center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Sección Soluciones Stock (solo registro y vista) ---
elif choice == "Soluciones Stock":
    st.subheader("🧪 Registro de soluciones stock")
    fdate = st.date_input("Fecha preparación", value=date.today())
    qty = st.text_input("Cantidad (g/mL)")
    code_s = st.text_input("Código solución")
    who = st.text_input("Responsable")
    regulador = st.text_input("Regulador crecimiento")
    obs2 = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [fdate.isoformat(), qty, code_s, who, regulador, obs2]
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Solución registrada.")
        info2 = [
            f"Código: {code_s}", f"Fecha: {fdate.isoformat()}",
            f"Cantidad: {qty}", f"Responsable: {who}", f"Regulador: {regulador}", f"Obs: {obs2}"
        ]
        qr2 = make_qr("\n".join(info2))
        label2 = make_label(info2, qr2)
        st.image(label2, width=300)
        st.download_button("⬇️ Descargar etiqueta PNG", data=label2, file_name=f"sol_{code_s}.png", mime="image/png")
    st.markdown("---")
    st.subheader("📋 Lista de soluciones stock")
    st.dataframe(sol_df)
    st.download_button(
        "⬇️ Descargar Soluciones Excel",
        data=to_excel_bytes(sol_df),
        file_name="soluciones.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
