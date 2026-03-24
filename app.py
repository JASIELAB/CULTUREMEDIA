import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont
import os

# --- Configuración de página ---
st.set_page_config(page_title="Medios Cultivo", layout="wide")

# --- FUNCIONES SEGURAS ---
def safe_int(value, default=1):
    try:
        if pd.isna(value) or value == '':
            return default
        return max(default, int(float(value)))
    except:
        return default

def safe_float(value, default=0.0):
    try:
        if pd.isna(value) or value == '':
            return default
        return float(value)
    except:
        return default

# --- Logo en esquina ---
logo_path = "plablue.png"
if os.path.isfile(logo_path):
    try:
        logo = Image.open(logo_path)
        st.image(logo, width=120)
    except Exception as e:
        st.warning(f"Error al cargar logo: {e}")

# --- Helpers de QR y Etiquetas ---
def make_qr(text: str) -> BytesIO:
    img = qrcode.make(text)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def make_label(info_lines, qr_buf, size=(250, 120)):
    w, h = size
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    y = 5
    for line in info_lines:
        draw.text((5, y), line, fill="black", font=font)
        y += 15
    qr_img = Image.open(qr_buf).resize((80, 80))
    img.paste(qr_img, (w - qr_img.width - 5, (h - qr_img.height) // 2))
    return img

# --- Archivos de datos ---
INV_FILE = "inventario_medios.csv"
SOL_FILE = "soluciones_stock.csv"
HIST_FILE = "movimientos.csv"
REC_FILE = "RECETAS MEDIOS ACTUAL JUNIO251.xlsx"

# --- Columnas ---
inv_cols = [
    "Código","Año","Receta","Solución","Equipo","Semana","Día","Preparación",
    "frascos","pH_Ajustado","pH_Final","CE_Final",
    "Litros_preparar","Dosificar_por_frasco","Fecha"
]
sol_cols = ["Fecha","Cantidad","Código_Solución","Responsable","Regulador","Observaciones"]
hist_cols = ["Timestamp","Tipo","Código","Cantidad","Detalles"]

# --- Funciones de carga / guardado ---
def load_df(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ''
    return df[cols]

def save_df(path, df):
    df.to_csv(path, index=False)

# --- Carga inicial de datos ---
inv_df = load_df(INV_FILE, inv_cols)
sol_df = load_df(SOL_FILE, sol_cols)
mov_df = load_df(HIST_FILE, hist_cols)

# --- UI Principal ---
st.title("Control de Medios de Cultivo InVitRo")
st.markdown("---")

menu = ["Registrar Lote","Consultar Stock","Baja Inventario"]
choice = st.selectbox("Menú", menu)

# --- Registrar Lote ---
if choice == "Registrar Lote":
    year = st.number_input("Año",2000,2100,value=date.today().year)
    receta = st.text_input("Receta")
    frascos = st.number_input("Frascos",1,999,value=1)

    if st.button("Registrar"):
        code = f"{year}-{receta}"
        inv_df.loc[len(inv_df)] = [
            code,year,receta,"","","","",1,
            frascos,0,0,0,0,0,date.today()
        ]
        save_df(INV_FILE,inv_df)
        st.success("Registrado")

# --- Consultar y Editar ---
elif choice == "Consultar Stock":

    if inv_df.empty:
        st.warning("No hay datos")
        st.stop()

    sel = st.selectbox("Selecciona lote",inv_df['Código'])
    idx = inv_df[inv_df['Código']==sel].index[0]

    e_fras = st.number_input(
        "Frascos",
        1,
        999,
        value=safe_int(inv_df.at[idx,'frascos'],1)
    )

    if st.button("Guardar"):
        inv_df.at[idx,'frascos'] = e_fras
        save_df(INV_FILE,inv_df)
        st.success("Actualizado")

# --- Baja Inventario ---
elif choice == "Baja Inventario":

    if inv_df.empty:
        st.warning("No hay datos")
        st.stop()

    sel = st.selectbox("Selecciona código",inv_df['Código'])
    cantidad = st.number_input("Cantidad",1,999,value=1)

    if st.button("Aplicar baja"):
        idx = inv_df[inv_df['Código']==sel].index[0]

        actual = safe_int(inv_df.at[idx,'frascos'],0)

        inv_df.at[idx,'frascos'] = max(0, actual - cantidad)

        save_df(INV_FILE,inv_df)

        st.success("Baja aplicada")
