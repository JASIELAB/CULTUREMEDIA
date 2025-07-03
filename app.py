import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
import os
from PIL import Image, ImageDraw, ImageFont

# --- Configuración de página y estilos ---
st.set_page_config(page_title="Medios de Cultivo InVitro", layout="wide")
# Paleta rojo y blanco
PRIMARY_COLOR = "#D32F2F"
ACCENT_COLOR = "#FFFFFF"
BG_COLOR = "#FFEBEE"
TEXT_COLOR = "#000000"
st.markdown(f"""
<style>
    .stApp {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; }}
    .stButton>button, .stDownloadButton>button {{ background-color: {PRIMARY_COLOR}; color: {ACCENT_COLOR}; }}
</style>
""", unsafe_allow_html=True)

# --- Archivos y DataFrames ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

inv_cols = ["Código","Año","Receta","Solución","Semana","Día","Preparación","Frascos","pH_Ajustado","pH_Final","CE_Final","Fecha"]
if os.path.exists(INV_FILE):
    inv_df = pd.read_csv(INV_FILE)[inv_cols]
else:
    inv_df = pd.DataFrame(columns=inv_cols)

sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
if os.path.exists(SOL_FILE):
    sol_df = pd.read_csv(SOL_FILE)[sol_cols]
else:
    sol_df = pd.DataFrame(columns=sol_cols)

# --- Recetas ---
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

def make_label(info: list, qr_bytes: bytes) -> Image.Image:
    label = Image.new("RGB", (400, 130), "white")
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
    label.paste(qr_img, (310, 10))
    return label

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return buf.getvalue()

# --- Menú lateral ---
with st.sidebar:
    st.title("🗭 Menú")
    choice = st.radio("Selecciona sección:", [
        "Registrar Lote","Consultar Stock","Inventario","Historial",
        "Soluciones Stock","Recetas","Incubación","Bajas Inventario","Imprimir Etiquetas"
    ])

# --- Cabecera ---
col1, col2 = st.columns([1, 8])
col1.image("logo_blackberry.png", width=60)
col2.markdown("<h1 style='text-align:center;'>🌱 Control de Medios de Cultivo InVitro</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- Secciones ---
def section_registrar_lote():
    st.subheader("📋 Registrar Nuevo Lote")
    año = st.text_input("Año (ej. 2025)")
    receta = st.selectbox("Receta", ["Selecciona"] + list(recipes.keys()))
    solucion = st.selectbox("Solución stock", ["Selecciona"] + sol_df['Código_Solución'].fillna("").tolist())
    semana = st.text_input("Semana")
    dia = st.text_input("Día")
    prep = st.text_input("Número de preparación")
    frascos = st.number_input("Cantidad de frascos", min_value=1, max_value=999, value=1)
    ph_aj = st.number_input("pH ajustado", value=5.8, format="%.2f")
    ph_fin = st.number_input("pH final", value=5.8, format="%.2f")
    ce = st.number_input("CE final (mS/cm)", value=1.0, format="%.2f")
    if st.button("Registrar lote"):
        cod_base = f"{año}-{receta}-{solucion}-{semana}-{dia}-{prep}".replace(' ','')
        fecha = date.today().isoformat()
        inv_df.loc[len(inv_df)] = [cod_base, año, receta, solucion, semana, dia, prep, frascos, ph_aj, ph_fin, ce, fecha]
        inv_df.to_csv(INV_FILE, index=False)
        st.success("Lote registrado exitosamente.")
    st.markdown("---")
    st.subheader("🔬 Inventario de Soluciones Stock")
    st.dataframe(sol_df)


def section_consultar_stock():
    st.subheader("🔍 Consultar Stock")
    st.dataframe(inv_df)


def section_inventario():
    st.subheader("📦 Inventario Completo")
    st.dataframe(inv_df)


def section_historial():
    st.subheader("📜 Historial de Lotes")
    start = st.date_input("Desde", inv_df['Fecha'].min() if not inv_df.empty else date.today())
    end = st.date_input("Hasta", date.today())
    mask = (pd.to_datetime(inv_df['Fecha']) >= pd.to_datetime(start)) & (pd.to_datetime(inv_df['Fecha']) <= pd.to_datetime(end))
    st.dataframe(inv_df[mask])


def section_soluciones_stock():
    st.subheader("📊 Registro de Soluciones Stock")
    fecha = st.date_input("Fecha")
    cantidad = st.text_input("Cantidad (ej. 1 g)")
    cod = st.text_input("Código de solución")
    resp = st.text_input("Responsable")
    reg = st.text_input("Regulador")
    obs = st.text_area("Observaciones")
    if st.button("Registrar solución"):
        sol_df.loc[len(sol_df)] = [fecha.isoformat(), cantidad, cod, resp, reg, obs]
        sol_df.to_csv(SOL_FILE, index=False)
        st.success("Solución registrada.")
    st.markdown("---")
    st.subheader("🗒 Inventario de Soluciones Stock")
    st.dataframe(sol_df)


def section_recetas():
    st.subheader("📖 Recetas de Medios")
    opc = st.selectbox("Selecciona una receta:", list(recipes.keys()))
    st.dataframe(recipes[opc])


def section_incubacion():
    st.subheader("⏳ Incubación de Lotes")
    df = inv_df.copy()
    df['Días'] = (pd.to_datetime(date.today()) - pd.to_datetime(df['Fecha'])).dt.days
    def color_row(days):
        if days > 30:
            return ['background-color: #EF9A9A']*len(df.columns)
        elif days < 7:
            return ['background-color: #A5D6A7']*len(df.columns)
        else:
            return ['background-color: #FFF59D']*len(df.columns)
    st.dataframe(df.style.apply(lambda x: color_row(x['Días']), axis=1))


def section_bajas_inventario():
    st.subheader("⚠️ Bajas de Inventario")
    code = st.selectbox("Selecciona lote:", inv_df['Código'].tolist())
    qty = st.number_input("Cantidad a dar de baja", min_value=1, max_value=999)
    motivo = st.text_input("Motivo consumo/merma")
    if st.button("Aplicar baja"):
        idx = inv_df[inv_df['Código']==code].index[0]
        inv_df.at[idx,'Frascos'] = max(inv_df.at[idx,'Frascos'] - qty, 0)
        inv_df.to_csv(INV_FILE, index=False)
        st.success("Stock actualizado.")
    st.markdown("---")
    st.dataframe(inv_df)


def section_imprimir_etiquetas():
    st.subheader("🖨️ Imprimir Etiquetas")
    sel = st.multiselect("Selecciona lotes:", inv_df['Código'].tolist())
    if st.button("Generar PDF etiquetas"):
        labels=[]
