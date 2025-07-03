import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date
import os
from PIL import Image, ImageDraw, ImageFont

# --- Helpers ---
def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return buf.getvalue()

# Generate QR bytes from text
def make_qr(text: str) -> bytes:
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

# Create label image (400x130) with text info and QR
def make_label(info: list, qr_bytes: bytes, size=(400, 130)) -> Image.Image:
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
    label.paste(qr_img, (size[0] - 90, 10))
    return label

# --- Page config & styles ---
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

# --- Data files ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

# --- Load or init dataframes ---
inv_cols = ["Código","Año","Receta","Solución","Semana","Día","Preparación","Frascos","pH_Ajustado","pH_Final","CE_Final","Fecha"]
if os.path.exists(INV_FILE):
    inv_df = pd.read_csv(INV_FILE).reindex(columns=inv_cols)
else:
    inv_df = pd.DataFrame(columns=inv_cols)

sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
if os.path.exists(SOL_FILE):
    sol_df = pd.read_csv(SOL_FILE).reindex(columns=sol_cols)
else:
    sol_df = pd.DataFrame(columns=sol_cols)

# --- Load recetas ---
recipes = {}
if os.path.exists(REC_FILE):
    xls = pd.ExcelFile(REC_FILE)
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        if df.shape[0] > 9:
            sub = df.iloc[9:, :3].dropna(how='all').copy()
            sub.columns = ["Componente","Fórmula","Concentración"]
            recipes[sheet] = sub

# --- Sidebar menu ---
st.sidebar.title("🧭 Menú")
choice = st.sidebar.radio("Selecciona una sección:", [
    "Registrar Lote",
    "Consultar Stock",
    "Inventario",
    "Historial",
    "Soluciones Stock",
    "Recetas de Medios",
    "Imprimir Etiquetas",
    "Administrar Sistema"
])

# --- Header ---
col1, col2 = st.columns([1, 8])
col1.image("logo_blackberry.png", width=60)
col2.markdown("<h1 style='text-align:center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Sections ---
if choice == "Registrar Lote":
    st.subheader("📝 Registrar Lote")
    año = st.text_input("Año (ej. 2025)")
    receta = st.selectbox("Receta", ["Selecciona..."] + list(recipes.keys()))
    solucion = st.text_input("Solución stock")
    semana = st.number_input("Semana", 1, 52)
    dia = st.number_input("Día", 1, 7)
    prep = st.text_input("Número de preparación")
    frascos = st.number_input("Cantidad de frascos", min_value=1, max_value=999, step=1)
    ph_aj = st.number_input("pH ajustado", format="%.1f")
    ph_fin = st.number_input("pH final", format="%.1f")
    ce = st.number_input("CE final (mS/cm)", format="%.2f")
    if st.button("Registrar lote"):
        code = f"{año}{receta}{solucion}{semana}{dia}{prep}".replace(' ', '')
        fecha = date.today().isoformat()
        inv_df.loc[len(inv_df)] = [code, año, receta, solucion, semana, dia, prep, frascos, ph_aj, ph_fin, ce, fecha]
        inv_df.to_csv(INV_FILE, index=False)
        st.success("Lote registrado.")

elif choice == "Consultar Stock":
    st.subheader("🔍 Stock Actual de Medios")
    st.dataframe(inv_df)
    st.subheader("🧪 Inventario Soluciones Stock")
    st.dataframe(sol_df)

elif choice == "Inventario":
    st.subheader("📋 Inventario Actual")
    st.dataframe(inv_df)

elif choice == "Historial":
    st.subheader("📜 Historial")
    if inv_df.empty:
        st.info("No hay registros.")
    else:
        start = st.date_input("Desde", value=pd.to_datetime(inv_df['Fecha']).dt.date.min())
        end = st.date_input("Hasta", value=pd.to_datetime(inv_df['Fecha']).dt.date.max())
        df = inv_df.copy()
        df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        filt = df[(df['Fecha'] >= start) & (df['Fecha'] <= end)]
        st.dataframe(filt)

elif choice == "Soluciones Stock":
    st.subheader("🧪 Registro de Soluciones Stock")
    fecha = st.date_input("Fecha preparación", value=date.today())
    cantidad = st.text_input("Cantidad (g/mL)")
    cod_s = st.text_input("Código solución stock")
    responsable = st.text_input("Responsable")
    regulador = st.text_input("Regulador crecimiento")
    obs = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [fecha.isoformat(), cantidad, cod_s, responsable, regulador, obs]
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Solución registrada.")

elif choice == "Recetas de Medios":
    st.subheader("📖 Recetas de Medios de Cultivo")
    medio = st.selectbox("Selecciona receta", list(recipes.keys()))
    if medio:
        st.dataframe(recipes[medio])

elif choice == "Imprimir Etiquetas":
    st.subheader("🖨️ Imprimir Etiquetas")
    if inv_df.empty:
        st.info("No hay lotes.")
    else:
        lote = st.selectbox("Selecciona lote", inv_df['Código'].tolist())
        copies = st.number_input("Cantidad de etiquetas", min_value=1, value=1)
        if st.button("Generar PDF"):
            row = inv_df.loc[inv_df['Código'] == lote].iloc[0]
            images = []
            for i in range(1, copies+1):
                code_i = f"{lote}-{i}"
                info = [
                    f"Código: {code_i}",
                    f"Año: {row['Año']}",
                    f"Receta: {row['Receta']}",
                    f"Frascos: {row['Frascos']}",
                    f"pH ajustado: {row['pH_Ajustado']}",
                    f"pH final: {row['pH_Final']}",
                    f"CE final: {row['CE_Final']}"
                ]
                qr = make_qr(code_i)
                label = make_label(info, qr)
                images.append(label)
            pdf_buf = BytesIO()
            images[0].save(pdf_buf, format='PDF', save_all=True, append_images=images[1:])
            pdf_buf.seek(0)
            st.download_button("⬇️ Descargar etiquetas PDF", data=pdf_buf.getvalue(), file_name=f"etiquetas_{lote}.pdf", mime="application/pdf")

elif choice == "Administrar Sistema":
    st.subheader("⚙️ Administrar Sistema")
    if st.button("Limpiar inventario medios"):
        inv_df.drop(inv_df.index, inplace=True)
        inv_df.to_csv(INV_FILE, index=False)
        st.success("Inventario medios limpiado.")
    if st.button("Limpiar soluciones stock"):
        sol_df.drop(sol_df.index, inplace=True)
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Inventario soluciones limpiado.")

# --- Sidebar downloads ---
st.sidebar.markdown("---")
st.sidebar.download_button("⬇️ Descargar Inventario Medios", data=to_excel_bytes(inv_df), file_name="inventario_medios.xlsx")
st.sidebar.download_button("⬇️ Descargar Soluciones Stock", data=to_excel_bytes(sol_df), file_name="soluciones_stock.xlsx")
